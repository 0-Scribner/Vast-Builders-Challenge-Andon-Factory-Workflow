"""Load units from mock fixtures or from a live VSS explore listing.

Agent note: live ingest is **upload**, not search. After Bryce uploads
kit clips, call ``scan_live()`` which walks Explore, pulls each
segment's ``reasoning_content``, and runs the same parser/prior path
as mock mode. Kit id is read from tags (``kit:race-car``) or filename.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from inspection import parse_caption
from kits import kit_ids
from llm import prior_for
from mock_data import build_mock_units
from vss_client import VssClient

_KIT_TAG = re.compile(r"kit:([a-z0-9-]+)", re.I)


def scan_mock() -> List[Dict[str, Any]]:
    return build_mock_units()


def scan_live(client: Optional[VssClient] = None) -> List[Dict[str, Any]]:
    client = client or VssClient()
    parents = client.explore_all(scope="all")
    units: List[Dict[str, Any]] = []
    for i, parent in enumerate(parents, start=1):
        filename = parent.get("filename") or parent.get("name") or f"video-{i}"
        tags = _as_tags(parent.get("tags"))
        kit_id = _kit_from(tags, filename)
        source = (
            parent.get("preview_source")
            or parent.get("source")
            or _first_timeline_source(parent)
        )
        caption = ""
        if source:
            try:
                meta = client.segment_metadata(source)
                caption = (
                    meta.get("reasoning_content")
                    or meta.get("caption")
                    or meta.get("description")
                    or ""
                )
            except Exception:
                caption = parent.get("reasoning_content") or ""
        else:
            caption = parent.get("reasoning_content") or ""
        occlusion = False
        if source:
            try:
                det = client.detections(source)
                classes = str((det or {}).get("object_classes") or "").lower()
                occlusion = "person" in classes or "hand" in classes
            except Exception:
                occlusion = False
        inspection = parse_caption(caption, kit_id=kit_id)
        unit = {
            "id": _unit_id(parent, i),
            "kit_id": kit_id,
            "filename": filename,
            "camera_id": parent.get("camera_id") or "",
            "location": parent.get("location") or "",
            "tags": tags,
            "caption": caption,
            "inspection": inspection,
            "source": source or parent.get("original_video") or "",
            "original_video": parent.get("original_video") or "",
            "occlusion": occlusion,
            "mock": False,
        }
        unit["prior"] = prior_for(inspection, kit_id or "unknown")
        units.append(unit)
    return units


def _as_tags(raw: Any) -> List[str]:
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str) and raw.strip():
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def _kit_from(tags: List[str], filename: str) -> str:
    for t in tags:
        m = _KIT_TAG.search(t)
        if m and m.group(1) in kit_ids():
            return m.group(1)
    for kid in kit_ids():
        if kid in filename.lower():
            return kid
    return "race-car"


def _first_timeline_source(parent: Dict[str, Any]) -> str:
    timeline = parent.get("timeline") or []
    if timeline and isinstance(timeline, list):
        first = timeline[0]
        if isinstance(first, dict):
            return first.get("source") or first.get("preview_source") or ""
        return str(first)
    return ""


def _unit_id(parent: Dict[str, Any], i: int) -> str:
    ov = parent.get("original_video") or parent.get("id") or str(i)
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(ov))[-48:]
    return f"unit-{slug}"
