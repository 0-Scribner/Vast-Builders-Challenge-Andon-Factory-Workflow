"""Scribner FastAPI app, warehouse near-miss / path-clear gate.

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
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

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
from andon import ensure_warehouse_clip, lamp_for_unit, snapshot as andon_snapshot
from gpu_client import available as gpu_available
from llm import status as llm_status
from scan import LiveScanUnavailable
from tracking import status as tracking_status
from kits import (
    CAMERA_ID,
    KITS,
    LINE,
    LOCATION,
    PAYOFF_QUERY,
    PLAN_B_BRANCH,
    PRODUCT,
    REASON_CODES,
    STACK_LINE,
    kit_ids,
    prompt_for_kit,
)
from report import render_markdown
from stack_tools import build_router as build_stack_router
from state import AppState
from vss_client import VssClient, VssError

state = AppState()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if state.mock and not state.store.load_units():
        state.scan()
        state.run_gate()
    yield


app = FastAPI(title="Scribner warehouse andon / near-miss gate", version="2.2.0", lifespan=_lifespan)
app.include_router(build_stack_router(state))

STATIC = config.STATIC_DIR
STATIC.mkdir(parents=True, exist_ok=True)


class ReviewBody(BaseModel):
    unit_id: str
    verdict: str = Field(..., description="CLEAR or UNSAFE (aliases: C/U, A/O, PASS/FAIL)")
    reason: str = "agree"
    notes: str = ""
    gate_ok: bool | None = None
    confirm_escape: bool = False


def _inspection_public(insp: Dict[str, Any]) -> Dict[str, Any]:
    insp = insp or {}
    return {
        "complete": insp.get("complete"),
        "confidence": insp.get("confidence"),
        "path_clear": insp.get("path_clear"),
        "near_miss": insp.get("near_miss"),
        "hazards": insp.get("hazards") or insp.get("missing") or [],
        "missing": insp.get("missing") or insp.get("hazards") or [],
        "unclear": insp.get("unclear"),
        "person": insp.get("person"),
        "vehicle": insp.get("vehicle"),
        "vehicle_present": insp.get("vehicle_present"),
        "motion": insp.get("motion"),
        "distance": insp.get("distance"),
        "inconsistent": insp.get("inconsistent"),
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "mock": state.mock,
        "line": LINE,
        "product": PRODUCT,
        "corpus": "provided",
        "pack": config.PACK,
        "camera_id": CAMERA_ID,
        "payoff_query": PAYOFF_QUERY,
        "stack_line": STACK_LINE,
        "plan_b_branch": PLAN_B_BRANCH,
        "kits": kit_ids(),
        "store": state.store.state_summary(),
        "andon": _andon(),
        "stack": builders_stack.health_snapshot(),
        "gpu": gpu_available(),
        "live_configured": bool(config.VSS_URL and config.VSS_USERNAME and config.VSS_PASSWORD),
        "llm": llm_status(),
        "wandb_tracking": tracking_status(),
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.post("/api/scan")
def api_scan() -> Dict[str, Any]:
    try:
        result = state.scan()
        gated = state.run_gate()
        return {**result, **gated}
    except LiveScanUnavailable as exc:
        raise HTTPException(503, f"live scan unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(503, f"live scan failed: {type(exc).__name__}") from exc


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
                "yolo_person": u.get("yolo_person"),
                "yolo_vehicle": u.get("yolo_vehicle"),
                "inspection": _inspection_public(u.get("inspection") or {}),
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
                "yolo_person": u.get("yolo_person"),
                "yolo_vehicle": u.get("yolo_vehicle"),
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


@app.get("/api/andon")
def api_andon(unit_id: str = "") -> Dict[str, Any]:
    return _andon(unit_id or None)


def _andon(unit_id: Optional[str] = None) -> Dict[str, Any]:
    q = state.queue()
    current = state.unit(unit_id) if unit_id else None
    if current is None:
        current = q[0] if q else None
    return andon_snapshot(
        decisions=state.store.load_decisions(),
        queue=q,
        current=current,
        camera_id=CAMERA_ID,
        location=LOCATION,
        pack=config.PACK,
    )


@app.get("/api/kits")
def api_kits() -> Dict[str, Any]:
    scenes = {
        kid: {
            "name": KITS[kid]["name"],
            "prompt": prompt_for_kit(kid),
            "chars": len(prompt_for_kit(kid)),
        }
        for kid in kit_ids()
    }
    return {
        "kits": scenes,
        "scenes": scenes,
        "reasons": REASON_CODES,
        "camera_id": CAMERA_ID,
        "location": LOCATION,
        "payoff_query": PAYOFF_QUERY,
        "stack_line": STACK_LINE,
        "line": LINE,
        "product": PRODUCT,
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
    """Pack C segment. Mock paints an andon-tinted warehouse aisle for this unit."""
    source = clip_source(source, unit_id)
    if state.mock:
        path = _ensure_mock_clip(unit_id)
        return FileResponse(path, media_type="video/mp4")
    if not config.VSS_URL:
        raise HTTPException(503, "live VSS is not configured")
    if not source:
        raise HTTPException(404, "no VSS source for this live unit")
    try:
        client = VssClient()
        data = client.stream_bytes(source)
        return Response(content=data, media_type="video/mp4")
    except (VssError, Exception) as exc:
        raise HTTPException(502, f"stream failed: {type(exc).__name__}") from exc


def clip_source(source: str = "", unit_id: str = "") -> str:
    """Live /clip must stream the unit's Pack C segment, not an empty source."""
    if source:
        return source
    if not unit_id:
        return ""
    u = state.unit(unit_id)
    if not u:
        return ""
    return str(u.get("source") or u.get("original_video") or "")


def _ensure_mock_clip(unit_id: str = "") -> Path:
    unit = state.unit(unit_id) if unit_id else None
    return ensure_warehouse_clip(lamp_for_unit(unit) if unit else "yellow")


def main() -> None:
    import uvicorn

    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=False)


if __name__ == "__main__":
    main()
