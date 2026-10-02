"""VSS retrieval tools behind /api/stack.

Routes and fields follow the challenge skills retrieval/dashboard,
retrieval/suggest-prompts, retrieval/list-metadata and retrieval/agent-qa.
VssClient holds the JWT (retrieval/login). In mock mode no VSS call is made
and every payload carries "mock": true.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import config
from kits import CAMERA_ID, LOCATION, PACK_C_CAPTURE, PAYOFF_QUERY
from vss_client import VssClient, VssError

log = logging.getLogger("scribner.stack_tools")

DASHBOARD_SCOPES = ("all", "mine", "public")
LOGIN_PATH = "/api/v1/auth/login"

MOCK_FIELDS: Dict[str, Dict[str, Any]] = {
    "location": {"label": "Location", "options": [LOCATION]},
    "camera_id": {"label": "Camera ID", "options": [CAMERA_ID]},
    "capture_type": {"label": "Capture type", "options": [PACK_C_CAPTURE]},
}
MOCK_PROMPTS = [
    PAYOFF_QUERY,
    "forklift entering a pedestrian aisle",
    "person walking behind a reversing forklift",
]
MOCK_ANSWER = "Mock mode: the VSS agent was not called, so there is no grounded answer."

_client: Optional[VssClient] = None
_client_lock = threading.Lock()


class AskBody(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    unit_id: Optional[str] = None


def _vss() -> VssClient:
    global _client
    with _client_lock:
        if _client is None:
            _client = VssClient()
        return _client


def failure_reason(route: str, exc: BaseException) -> str:
    """Browser-safe text: never the host, token, password or response body."""
    if isinstance(exc, VssError):
        return f"VSS {route} failed: {exc}"
    if isinstance(exc, requests.HTTPError):
        resp = exc.response
        status = resp.status_code if resp is not None else "unknown"
        url = str(getattr(resp, "url", "") or "").split("?")[0]
        if url.endswith(LOGIN_PATH):
            return f"VSS login failed: HTTP {status}"
        return f"VSS {route} failed: HTTP {status}"
    if isinstance(exc, requests.Timeout):
        return f"VSS {route} timed out"
    if isinstance(exc, requests.ConnectionError):
        return f"VSS {route} connection failed"
    if isinstance(exc, requests.JSONDecodeError):
        return f"VSS {route} returned invalid JSON"
    return f"VSS {route} failed: {type(exc).__name__}"


def _live(route: str, call: Callable[[VssClient], Any]) -> Any:
    try:
        return call(_vss())
    except Exception as exc:
        reason = failure_reason(route, exc)
        log.warning("%s", reason)
        raise HTTPException(503, reason) from exc


def _mock_stats(units: List[Dict[str, Any]]) -> Dict[str, Any]:
    videos = {str(u.get("original_video") or "") for u in units} - {""}
    return {
        "overview": {"segment_rows": len(units), "unique_videos": len(videos)},
        "objects": [
            {"label": "person", "segment_count": sum(1 for u in units if u.get("yolo_person"))},
            {"label": "vehicle", "segment_count": sum(1 for u in units if u.get("yolo_vehicle"))},
        ],
        "recent_videos": [
            {"original_video": u.get("original_video"), "filename": u.get("filename")}
            for u in units[:10]
        ],
    }


def _mock_metadata(field: str, prefix: str, limit: int) -> Dict[str, Any]:
    if not field:
        return {
            "schema": [
                {
                    "name": name,
                    "type": "string",
                    "ui_type": "select",
                    "label": spec["label"],
                    "options": list(spec["options"]),
                }
                for name, spec in MOCK_FIELDS.items()
            ],
            "table": "vss-collection",
        }
    if field not in MOCK_FIELDS:
        raise HTTPException(
            400, f"field {field!r} is not filterable; expected one of {', '.join(MOCK_FIELDS)}"
        )
    values = [v for v in MOCK_FIELDS[field]["options"] if v.startswith(prefix)][:limit]
    return {"field": field, "values": values, "count": len(values)}


def build_router(state: Any) -> APIRouter:
    """``state`` is the app's AppState: unit lookup for /ask, local units for mock stats."""
    router = APIRouter(prefix="/api/stack", tags=["stack"])

    @router.get("/dashboard")
    def stack_dashboard(scope: str = Query("all")) -> Dict[str, Any]:
        if scope not in DASHBOARD_SCOPES:
            raise HTTPException(
                400, f"unknown scope {scope!r}; expected one of {', '.join(DASHBOARD_SCOPES)}"
            )
        if config.MOCK:
            return {"mock": True, "scope": scope, "data": _mock_stats(state.store.load_units())}
        data = _live("/api/v1/dashboard/stats", lambda c: c.dashboard(scope=scope))
        return {"mock": False, "scope": scope, "data": data}

    @router.get("/suggest")
    def stack_suggest() -> Dict[str, Any]:
        if config.MOCK:
            return {"mock": True, "data": {"prompts": list(MOCK_PROMPTS), "key_events": []}}
        return {"mock": False, "data": _live("/api/v1/suggestions", lambda c: c.suggestions())}

    @router.get("/metadata")
    def stack_metadata(
        field: str = Query(""),
        prefix: str = Query(""),
        limit: int = Query(50, ge=1, le=1000),
    ) -> Dict[str, Any]:
        field = field.strip()
        if config.MOCK:
            return {"mock": True, "field": field or None, "data": _mock_metadata(field, prefix, limit)}
        if field:
            data = _live(
                "/api/v1/metadata/values",
                lambda c: c.metadata_values(field, prefix=prefix, limit=limit),
            )
        else:
            data = _live("/api/v1/metadata/schema", lambda c: c.metadata_schema())
        return {"mock": False, "field": field or None, "data": data}

    @router.post("/ask")
    def stack_ask(body: AskBody) -> Dict[str, Any]:
        question = body.question.strip()
        if not question:
            raise HTTPException(400, "question is empty")
        unit_id = (body.unit_id or "").strip() or None
        original_video = ""
        if unit_id:
            unit = state.unit(unit_id)
            if not unit:
                raise HTTPException(404, f"unknown unit {unit_id!r}")
            original_video = str(unit.get("original_video") or "")
            if not original_video:
                raise HTTPException(400, f"unit {unit_id!r} has no original_video")
        target = {"unit_id": unit_id, "original_video": original_video or None}
        if config.MOCK:
            return {
                "mock": True,
                **target,
                "data": {"answer": MOCK_ANSWER, "tool_used": None, "evidence": []},
            }
        data = _live(
            "/api/v1/agent/ask",
            lambda c: c.agent_ask(question, original_video=original_video),
        )
        if not isinstance(data, dict) or "answer" not in data:
            raise HTTPException(503, "VSS /api/v1/agent/ask returned no answer")
        return {"mock": False, **target, "data": data}

    return router
