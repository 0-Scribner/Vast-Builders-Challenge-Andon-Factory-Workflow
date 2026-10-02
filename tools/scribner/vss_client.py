"""VSS HTTP client. Mirrors the workshop retrieval skills.

Agent note: JWT from POST /api/v1/auth/login. Playback endpoints take
``?token=`` because <video> cannot set headers — we still proxy /clip
server-side so the browser never sees the JWT.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

import config


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
            raise VssError("VSS_URL / VSS_USERNAME missing; use SCRIBNER_MOCK=1 locally")
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
    ) -> Dict[str, Any]:
        with open(path, "rb") as f:
            files = {"file": f}
            data = {
                "is_public": "true" if is_public else "false",
                "tags": tags,
                "custom_prompt": custom_prompt,
                "camera_id": camera_id,
                "capture_type": capture_type,
                "location": location,
            }
            r = self._post("/api/v1/videos/upload", files=files, data=data)
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
