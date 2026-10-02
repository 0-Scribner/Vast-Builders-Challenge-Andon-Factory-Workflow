"""Scribner FastAPI app.

Agent note
----------
Routes are the contract with ``static/index.html``. Rename a path only
together with the UI fetch() calls.

This file is the K8s entrypoint: ConfigMap mounts this directory at
``/code`` and runs ``python main.py``. Imports are **sibling** modules
(no ``tools.scribner`` package prefix) so that works.

Bind 0.0.0.0:$PORT. Ingress strips ``/app``. ``/health`` is the probe.
"""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# Local default. The K8s Deployment sets SCRIBNER_MOCK=0 explicitly.
os.environ.setdefault("SCRIBNER_MOCK", "1")

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

import builders_stack
import config
from gpu_client import available as gpu_available
from kits import CAMERA_ID, KITS, LOCATION, REASON_CODES, kit_ids, prompt_for_kit
from report import render_markdown
from state import AppState
from vss_client import VssClient, VssError

state = AppState()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if state.mock and not state.store.load_units():
        state.scan()
        state.run_gate()
    yield


app = FastAPI(title="Scribner completeness gate", version="1.1.0", lifespan=_lifespan)

STATIC = config.STATIC_DIR
STATIC.mkdir(parents=True, exist_ok=True)


class ReviewBody(BaseModel):
    unit_id: str
    verdict: str = Field(..., description="COMPLETE or INCOMPLETE (aliases: C/I, PASS/FAIL)")
    reason: str = "agree"
    notes: str = ""
    gate_ok: bool | None = None
    confirm_escape: bool = False


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "mock": state.mock,
        "product": "kit-completeness",
        "corpus": "provided",
        "pack": config.PACK,
        "camera_id": CAMERA_ID,
        "kits": kit_ids(),
        "store": state.store.state_summary(),
        "stack": builders_stack.health_snapshot(),
        "gpu": gpu_available(),
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.post("/api/scan")
def api_scan() -> Dict[str, Any]:
    result = state.scan()
    gated = state.run_gate()
    return {**result, **gated}


@app.post("/api/run")
def api_run() -> Dict[str, Any]:
    return state.run_gate()


@app.get("/api/units")
def api_units() -> Dict[str, Any]:
    units = state.store.load_units()
    decisions = {d.get("unit_id"): d for d in state.store.load_decisions()}
    labels = {x.get("unit_id"): x for x in state.store.load_labels()}
    rows = []
    for u in units:
        uid = u["id"]
        rows.append(
            {
                "id": uid,
                "kit_id": u.get("kit_id"),
                "variant": u.get("variant"),
                "filename": u.get("filename"),
                "decision": decisions.get(uid),
                "label": labels.get(uid),
                "prior": u.get("prior"),
                "inspection": {
                    "complete": (u.get("inspection") or {}).get("complete"),
                    "confidence": (u.get("inspection") or {}).get("confidence"),
                    "missing": (u.get("inspection") or {}).get("missing"),
                    "unclear": (u.get("inspection") or {}).get("unclear"),
                },
            }
        )
    return {"units": rows}


@app.get("/api/units/{unit_id}")
def api_unit(unit_id: str) -> Dict[str, Any]:
    u = state.unit(unit_id)
    if not u:
        raise HTTPException(404, "unknown unit")
    return u


@app.get("/api/queue")
def api_queue() -> Dict[str, Any]:
    q = state.queue()
    slim = []
    for u in q:
        insp = u.get("inspection") or {}
        slim.append(
            {
                "id": u.get("id"),
                "kit_id": u.get("kit_id"),
                "filename": u.get("filename"),
                "variant": u.get("variant"),
                "caption": u.get("caption"),
                "inspection": insp,
                "prior": u.get("prior"),
                "decision_row": u.get("decision_row"),
                "occlusion": u.get("occlusion"),
                "source": u.get("source"),
            }
        )
    return {"queue": slim, "n": len(slim)}


@app.post("/api/review")
def api_review(body: ReviewBody) -> Dict[str, Any]:
    if not state.unit(body.unit_id):
        raise HTTPException(404, "unknown unit")
    try:
        return state.review(
            body.unit_id,
            body.verdict,
            body.reason,
            body.notes,
            gate_ok=body.gate_ok,
            confirm_escape=body.confirm_escape,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/retrain")
def api_retrain() -> Dict[str, Any]:
    return state.retrain()


@app.get("/api/metrics")
def api_metrics() -> Dict[str, Any]:
    return state.metrics()


@app.get("/api/kits")
def api_kits() -> Dict[str, Any]:
    return {
        "kits": {
            kid: {
                "name": KITS[kid]["name"],
                "prompt": prompt_for_kit(kid),
                "chars": len(prompt_for_kit(kid)),
            }
            for kid in kit_ids()
        },
        "reasons": REASON_CODES,
        "camera_id": CAMERA_ID,
        "location": LOCATION,
    }


@app.get("/api/report")
def api_report() -> PlainTextResponse:
    md = render_markdown(
        state.store.load_units(),
        state.store.load_decisions(),
        state.store.load_labels(),
        state.metrics()["current"],
    )
    return PlainTextResponse(md, media_type="text/markdown")


@app.get("/clip")
def clip(source: str = Query(""), unit_id: str = Query("")) -> Response:
    """Proxy a segment. Mock mode serves a generated 4s color clip."""
    if state.mock or not config.VSS_URL:
        path = _ensure_mock_clip()
        return FileResponse(path, media_type="video/mp4")
    try:
        client = VssClient()
        data = client.stream_bytes(source)
        return Response(content=data, media_type="video/mp4")
    except (VssError, Exception) as exc:
        raise HTTPException(502, f"stream failed: {type(exc).__name__}") from exc


def _ensure_mock_clip() -> Path:
    path = Path("/tmp/scribner_mock.mp4")
    if path.exists() and path.stat().st_size > 1000:
        return path
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x1a2332:s=640x360:d=4.2:r=24",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", "4.2",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart",
        str(path),
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not path.exists():
        path.write_bytes(b"")
    return path


def main() -> None:
    import uvicorn

    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=False)


if __name__ == "__main__":
    main()
