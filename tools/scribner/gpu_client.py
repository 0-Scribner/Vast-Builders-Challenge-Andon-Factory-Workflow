"""Direct calls to the shared CoreWeave GPU NIMs from the Builders Stack.

URLs come only from config.example / ``/config/<team>.config``:

- ``$COSMOS3_REASON_URL``, ``POST /v1/chat/completions``
- ``$YOLO_URL``, ``GET /healthz``, ``POST /v1/infer``
- ``$COSMOS_EMBED1_URL``, ``POST /v1/embeddings`` (256-d, ``request_type``)

Optional ``$GPU_BEARER_TOKEN`` (gpu skills). config.example says NIMs may
have no auth, send the header only when the token is set.

Never hardcode a GPU host. Never call the optional ASR NIM from this
module; it is not in the default VSS pipeline and warehouse clips have
no speech. YOLO person/vehicle corroborates the caption and must not
sole-source AUTO_CLEAR.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

import config
from builders_stack import EMBED_DIM


class GpuError(RuntimeError):
    pass


def _headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if config.GPU_BEARER_TOKEN:
        h["Authorization"] = f"Bearer {config.GPU_BEARER_TOKEN}"
    return h


def _need(url: str, name: str) -> str:
    if not url:
        raise GpuError(f"{name} is unset; source /config/<team>.config")
    return url.rstrip("/")


def cosmos_reason_complete(prompt: str, *, max_tokens: int = 64) -> str:
    base = _need(config.COSMOS3_REASON_URL, "COSMOS3_REASON_URL")
    model = config.COSMOS3_REASON_MODEL or _first_model_id(base)
    r = requests.post(
        f"{base}/v1/chat/completions",
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0,
        },
        timeout=60,
    )
    r.raise_for_status()
    return ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def yolo_health() -> Dict[str, Any]:
    base = _need(config.YOLO_URL, "YOLO_URL")
    r = requests.get(f"{base}/healthz", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def yolo_infer(video_base64: str, filename: str = "clip.mp4") -> Dict[str, Any]:
    """Person/vehicle corroboration. Never sole-source AUTO_CLEAR from YOLO."""
    base = _need(config.YOLO_URL, "YOLO_URL")
    r = requests.post(
        f"{base}/v1/infer",
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "video_base64": video_base64,
            "filename": filename,
            "include_frames": False,
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


_VEHICLE_CLASSES = ("forklift", "truck", "car", "bus", "van", "vehicle")


def yolo_person_vehicle(payload: Dict[str, Any]) -> Dict[str, bool]:
    """Corroborate person/vehicle. Gate still requires a HIGH PATH_CLEAR caption."""
    classes = str(payload.get("object_classes") or "").lower()
    return {
        "yolo_person": "person" in classes,
        "yolo_vehicle": any(v in classes for v in _VEHICLE_CLASSES),
    }


def occlusion_from_yolo(payload: Dict[str, Any], *, corpus: bool = True) -> bool:
    """YOLO hand/person classes are Pack C subjects, not blocked-view proof."""
    classes = str(payload.get("object_classes") or "").lower()
    if corpus:
        return False
    return "hand" in classes


def embed_text(text: str) -> List[float]:
    base = _need(config.COSMOS_EMBED1_URL, "COSMOS_EMBED1_URL")
    model = config.COSMOS_EMBED1_MODEL or _first_model_id(base)
    r = requests.post(
        f"{base}/v1/embeddings",
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "input": text,
            "model": model,
            "request_type": "query",
            "encoding_format": "float",
        },
        timeout=60,
    )
    r.raise_for_status()
    vec = r.json()["data"][0]["embedding"]
    if len(vec) != EMBED_DIM:
        raise GpuError(f"Embed1 dim {len(vec)} != {EMBED_DIM} (VastDB vectors column)")
    return list(vec)


def _first_model_id(base: str) -> str:
    r = requests.get(f"{base}/v1/models", headers=_headers(), timeout=15)
    r.raise_for_status()
    data = r.json().get("data") or []
    if not data:
        raise GpuError(f"no models at {base}/v1/models")
    return str(data[0]["id"])


def available() -> Dict[str, bool]:
    return {
        "cosmos3_reason": bool(config.COSMOS3_REASON_URL),
        "yolo": bool(config.YOLO_URL),
        "embed1": bool(config.COSMOS_EMBED1_URL),
        "canary": False,
        "gpu_bearer": bool(config.GPU_BEARER_TOKEN),
    }
