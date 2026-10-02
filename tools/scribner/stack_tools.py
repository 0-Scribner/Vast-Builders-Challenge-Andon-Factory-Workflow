"""VSS retrieval tools behind /api/stack.

Routes and fields follow the challenge skills retrieval/dashboard,
retrieval/suggest-prompts, retrieval/list-metadata and retrieval/agent-qa.
VssClient holds the JWT (retrieval/login). In mock mode no VSS call is made
and every payload carries "mock": true.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlsplit

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import config
from kits import CAMERA_ID, LOCATION, PACK_C_CAPTURE, PAYOFF_QUERY
from vss_client import VssClient, VssError

log = logging.getLogger("scribner.stack_tools")

DASHBOARD_SCOPES = ("all", "mine", "public")
LOGIN_PATH = "/api/v1/auth/login"
_URL_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s'\"<>]+")

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


def _url_parts(url: str) -> List[str]:
    try:
        parts = urlsplit(url)
        return [p for p in (parts.netloc, parts.hostname, parts.password) if p]
    except ValueError:
        return [url.split("://", 1)[-1].split("/", 1)[0]]


def _secrets(client: Any) -> List[str]:
    """VSS base URL, host, password and JWT from config and the live client."""
    raw = [config.VSS_URL, config.VSS_PASSWORD]
    if client is not None:
        raw += [getattr(client, name, "") for name in ("base", "password", "_token")]
    found = set()
    for value in raw:
        value = str(value or "")
        if not value:
            continue
        found.add(value)
        if "://" in value:
            found.update(_url_parts(value))
    return sorted(found, key=len, reverse=True)


def _redact(text: str, client: Any = None) -> str:
    text = _URL_RE.sub("<url>", text)
    for value in _secrets(client):
        text = re.sub(re.escape(value), "<redacted>", text, flags=re.IGNORECASE)
    return text


def _is_login(resp: Any) -> bool:
    return str(getattr(resp, "url", "") or "").split("?")[0].endswith(LOGIN_PATH)


def _route_status(exc: BaseException) -> Optional[int]:
    """HTTP status of the failed route call; None for login and non-HTTP failures."""
    if not isinstance(exc, requests.HTTPError) or exc.response is None:
        return None
    if _is_login(exc.response):
        return None
    return exc.response.status_code


def failure_reason(route: str, exc: BaseException, client: Any = None) -> str:
    """Browser-safe text: never a URL, the host, token, password or response body."""
    if isinstance(exc, VssError):
        reason = f"VSS {route} failed: {str(exc) or type(exc).__name__}"
    elif isinstance(exc, requests.HTTPError):
        resp = exc.response
        status = resp.status_code if resp is not None else "unknown"
        if resp is not None and _is_login(resp):
            reason = f"VSS login failed: HTTP {status}"
        else:
            reason = f"VSS {route} failed: HTTP {status}"
    elif isinstance(exc, requests.Timeout):
        reason = f"VSS {route} timed out"
    elif isinstance(exc, requests.ConnectionError):
        reason = f"VSS {route} connection failed"
    elif isinstance(exc, requests.JSONDecodeError):
        reason = f"VSS {route} returned invalid JSON"
    else:
        reason = f"VSS {route} failed: {type(exc).__name__}"
    return _redact(reason, client)


def _live(route: str, call: Callable[[VssClient], Any], rejected: str = "") -> Any:
    """Run one VSS call. ``rejected`` is the reason returned when VSS answers 400."""
    client: Optional[VssClient] = None
    try:
        client = _vss()
        return call(client)
    except Exception as exc:
        status, reason = 503, failure_reason(route, exc, client)
        if rejected and _route_status(exc) == 400:
            status, reason = 400, _redact(rejected, client)
        log.warning("%s", reason)
        raise HTTPException(status, reason) from exc


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
            # retrieval/list-metadata: non-filterable fields get HTTP 400 from VSS.
            data = _live(
                "/api/v1/metadata/values",
                lambda c: c.metadata_values(field, prefix=prefix, limit=limit),
                rejected=f"field {field!r} is not filterable on VSS: HTTP 400",
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
