"""VSS HTTP client. Mirrors vast-builders-challenge retrieval/ + ingest/ skills.

JWT from POST /api/v1/auth/login (retrieval/login). Playback endpoints take
``?token=`` because <video> cannot set headers. We still proxy /clip
server-side so the browser never sees the JWT.

Only routes listed in the challenge skills. No /reports, /alerts, /analytics,
/videos/ask, /tags, /locations, or /extra-metadata.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

import config
from builders_stack import CUSTOM_PROMPT_MAX
from ingest import IngestRejected, assert_uploadable, filter_upload_fields


class VssError(RuntimeError):
    pass


class VssClient:
    def __init__(
        self,
        base: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.base = (base or config.VSS_URL).rstrip("/")
        self.username = username if username is not None else config.VSS_USERNAME
        self.password = password if password is not None else config.VSS_PASSWORD
        self._token: Optional[str] = None
        self._token_at = 0.0
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/json"

    def login(self, force: bool = False) -> str:
        if self._token and not force and (time.time() - self._token_at) < 20 * 60:
            return self._token
        if not self.base or not self.username:
            raise VssError("INGRESS_URL / USERNAME missing; use SCRIBNER_MOCK=1 locally")
        r = self.session.post(
            f"{self.base}/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
            timeout=30,
        )
        r.raise_for_status()
        token = r.json().get("access_token")
        if not token:
            raise VssError("login returned no access_token")
        self._token = token
        self._token_at = time.time()
        return token

    def me(self) -> Dict[str, Any]:
        r = self._get("/api/v1/auth/me")
        r.raise_for_status()
        return r.json()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.login()}"}

    def _get(self, path: str, **kwargs: Any) -> requests.Response:
        r = self.session.get(
            f"{self.base}{path}", headers=self._headers(), timeout=60, **kwargs
        )
        if r.status_code == 401:
            self.login(force=True)
            r = self.session.get(
                f"{self.base}{path}", headers=self._headers(), timeout=60, **kwargs
            )
        return r

    def _post(self, path: str, **kwargs: Any) -> requests.Response:
        r = self.session.post(
            f"{self.base}{path}", headers=self._headers(), timeout=120, **kwargs
        )
        if r.status_code == 401:
            self.login(force=True)
            r = self.session.post(
                f"{self.base}{path}", headers=self._headers(), timeout=120, **kwargs
            )
        return r

    def app_config(self) -> Dict[str, Any]:
        r = self._get("/api/v1/config")
        r.raise_for_status()
        return r.json()

    def ingest_config(self) -> Dict[str, Any]:
        # Public per list-metadata skill; still send JWT if we have one.
        r = self.session.get(
            f"{self.base}/api/v1/metadata/ingest-config", timeout=30
        )
        r.raise_for_status()
        return r.json()

    def prompt_max(self) -> int:
        try:
            cfg = self.ingest_config()
            n = int(cfg.get("custom_prompt_max_length") or CUSTOM_PROMPT_MAX)
            return n if n > 0 else CUSTOM_PROMPT_MAX
        except Exception:
            return CUSTOM_PROMPT_MAX

    def metadata_schema(self) -> Dict[str, Any]:
        r = self._get("/api/v1/metadata/schema")
        r.raise_for_status()
        return r.json()

    def metadata_values(self, field: str, prefix: str = "", limit: int = 50) -> Dict[str, Any]:
        params: Dict[str, Any] = {"field": field, "limit": limit}
        if prefix:
            params["prefix"] = prefix
        r = self._get("/api/v1/metadata/values", params=params)
        r.raise_for_status()
        return r.json()

    def explore(self, scope: str = "all", limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        r = self._get(
            "/api/v1/videos/explore",
            params={"scope": scope, "limit": limit, "offset": offset},
        )
        r.raise_for_status()
        return r.json()

    def explore_all(self, scope: str = "mine") -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        offset = 0
        total = None
        while True:
            page = self.explore(scope=scope, limit=100, offset=offset)
            batch = page.get("items") or page.get("results") or page.get("videos") or []
            if isinstance(page, list):
                batch = page
            items.extend(batch)
            total = page.get("total", len(items)) if isinstance(page, dict) else len(items)
            if not batch or len(items) >= int(total or 0):
                break
            offset += 100
            if offset > 5000:
                break
        return items

    def segment_metadata(self, source: str) -> Dict[str, Any]:
        r = self._get("/api/v1/videos/metadata", params={"source": source})
        r.raise_for_status()
        return r.json()

    def detections(self, source: str) -> Optional[Dict[str, Any]]:
        r = self._get("/api/v1/videos/detections", params={"source": source})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def search(self, query: str, **body: Any) -> Dict[str, Any]:
        payload = {"query": query, "top_k": 50, "llm_top_n": 0, "include_public": True}
        payload.update(body)
        r = self._post("/api/v1/search", json=payload)
        r.raise_for_status()
        return r.json()

    def synthesize(self, original_video: str, question: str, max_segments: int = 40) -> Dict[str, Any]:
        r = self._post(
            "/api/v1/videos/synthesize",
            json={
                "original_video": original_video,
                "question": question,
                "max_segments": max_segments,
            },
        )
        r.raise_for_status()
        return r.json()

    def upload_video(
        self,
        path: str,
        *,
        custom_prompt: str,
        tags: str,
        camera_id: str,
        capture_type: str,
        location: str,
        is_public: bool = True,
        allowed_users: str = "",
    ) -> Dict[str, Any]:
        try:
            assert_uploadable(path, custom_prompt, max_prompt=self.prompt_max())
        except IngestRejected as exc:
            raise VssError(str(exc)) from exc
        data = filter_upload_fields(
            {
                "is_public": "true" if is_public else "false",
                "tags": tags,
                "custom_prompt": custom_prompt,
                "camera_id": camera_id,
                "capture_type": capture_type,
                "location": location,
                "allowed_users": allowed_users,
            }
        )
        with open(path, "rb") as f:
            r = self._post("/api/v1/videos/upload", files={"file": f}, data=data)
        r.raise_for_status()
        return r.json()

    def reingest(
        self,
        *,
        original_video: str = "",
        stream_id: str = "",
        chunk_count: int = 1,
        custom_prompt: str = "",
        camera_id: str = "",
        capture_type: str = "",
        location: str = "",
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"chunk_count": chunk_count}
        if stream_id:
            body["stream_id"] = stream_id
        elif original_video:
            body["original_video"] = original_video
        else:
            raise VssError("reingest needs stream_id or original_video")
        if custom_prompt:
            if len(custom_prompt) > self.prompt_max():
                raise VssError("custom_prompt exceeds VSS max")
            body["custom_prompt"] = custom_prompt
        if camera_id:
            body["camera_id"] = camera_id
        if capture_type:
            body["capture_type"] = capture_type
        if location:
            body["location"] = location
        r = self._post("/api/v1/dashboard/reingest", json=body)
        r.raise_for_status()
        return r.json()

    def reingest_status(self, job_id: str) -> Dict[str, Any]:
        r = self._get(f"/api/v1/dashboard/reingest/{job_id}")
        r.raise_for_status()
        return r.json()

    def dashboard(self, scope: str = "mine") -> Dict[str, Any]:
        r = self._get("/api/v1/dashboard/stats", params={"scope": scope})
        r.raise_for_status()
        return r.json()

    def stream_bytes(self, source: str) -> bytes:
        token = self.login()
        r = self.session.get(
            f"{self.base}/api/v1/videos/stream",
            params={"source": source, "token": token},
            timeout=120,
        )
        r.raise_for_status()
        return r.content

    def suggestions(self) -> Any:
        r = self._get("/api/v1/suggestions")
        r.raise_for_status()
        return r.json()

    def agent_ask(self, question: str, original_video: str = "", top_k: int = 10) -> Dict[str, Any]:
        if not 1 <= top_k <= 50:
            raise VssError(f"agent/ask top_k must be 1-50, got {top_k}")
        body: Dict[str, Any] = {"question": question, "top_k": top_k}
        if original_video:
            body["original_video"] = original_video
        r = self._post("/api/v1/agent/ask", json=body)
        r.raise_for_status()
        return r.json()
