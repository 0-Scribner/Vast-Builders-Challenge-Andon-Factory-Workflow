"""Load units from mock fixtures or from the provided VSS corpus.

Live path for Pack C is **re-ingest** of already-indexed SDG warehouse
clips, then ``scan_live()`` walks Explore (filtered to
``sdg_warehouse_cam-2`` unless ``SCRIBNER_PACK=cross``) and runs the
same PRESENT/MISSING parser as mock mode. Optional own kit uploads still
scan via tags ``kit:race-car`` / filename.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import config
from inspection import parse_caption
from kits import CAMERA_TO_KIT, is_corpus_kit, kit_for_camera, kit_ids
from llm import prior_for
from mock_data import build_mock_units
from vss_client import VssClient

_KIT_TAG = re.compile(r"(?:kit|scene):([a-z0-9-]+)", re.I)


def scan_mock() -> List[Dict[str, Any]]:
    return build_mock_units()


def scan_live(client: Optional[VssClient] = None) -> List[Dict[str, Any]]:
    client = client or VssClient()
    pack = (config.PACK or "C").upper()
    if pack in {"CROSS", "ALL", "X"}:
        parents = _search_hits(client)
        if not parents:
            parents = client.explore_all(scope="all")
    else:
        parents = client.explore_all(scope="all")
        want = config.CAMERA_FILTER
        if want:
            filtered = [
                p
                for p in parents
                if str(p.get("camera_id") or "") == want
                or want in str(p.get("camera_id") or "")
            ]
            if filtered:
                parents = filtered
    units: List[Dict[str, Any]] = []
    for i, parent in enumerate(parents, start=1):
        units.append(_unit_from_parent(client, parent, i))
    return units


def _search_hits(client: VssClient) -> List[Dict[str, Any]]:
    try:
        body = client.search(config.SEARCH_QUERY, top_k=50, llm_top_n=0, min_similarity=0.3)
    except Exception:
        return []
    rows = body.get("results") or body.get("chunk_results") or []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            out.append(row)
    return out


def _unit_from_parent(client: VssClient, parent: Dict[str, Any], i: int) -> Dict[str, Any]:
    filename = parent.get("filename") or parent.get("name") or f"video-{i}"
    tags = _as_tags(parent.get("tags"))
    camera_id = str(parent.get("camera_id") or "")
    kit_id = _kit_from(tags, filename, camera_id)
    source = (
        parent.get("preview_source")
        or parent.get("source")
        or _first_timeline_source(parent)
    )
    caption = parent.get("reasoning_content") or parent.get("caption") or ""
    if source:
        try:
            meta = client.segment_metadata(source)
            caption = (
                meta.get("reasoning_content")
                or meta.get("caption")
                or meta.get("description")
                or caption
            )
        except Exception:
            pass
    occlusion = False
    if source:
        try:
            det = client.detections(source)
            classes = str((det or {}).get("object_classes") or "").lower()
            occlusion = _occlusion(kit_id, classes)
        except Exception:
            occlusion = False
    inspection = parse_caption(caption, kit_id=kit_id)
    unit = {
        "id": _unit_id(parent, i),
        "kit_id": kit_id,
        "filename": filename,
        "camera_id": camera_id,
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
    return unit


def _occlusion(kit_id: str, classes: str) -> bool:
    """Person/forklift are the subject of provided corpus kits, not occlusion."""
    if is_corpus_kit(kit_id):
        return "hand" in classes
    return "person" in classes or "hand" in classes


def _as_tags(raw: Any) -> List[str]:
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str) and raw.strip():
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def _kit_from(tags: List[str], filename: str, camera_id: str = "") -> str:
    known = set(kit_ids())
    for t in tags:
        m = _KIT_TAG.search(t)
        if m and m.group(1) in known:
            return m.group(1)
    low = filename.lower()
    for kid in kit_ids():
        if kid in low:
            return kid
    if camera_id in CAMERA_TO_KIT:
        return CAMERA_TO_KIT[camera_id]
    return kit_for_camera(camera_id)


def _first_timeline_source(parent: Dict[str, Any]) -> str:
    timeline = parent.get("timeline") or []
    if timeline and isinstance(timeline, list):
        first = timeline[0]
        if isinstance(first, dict):
            return first.get("source") or first.get("preview_source") or ""
        return str(first)
    return ""


def _unit_id(parent: Dict[str, Any], i: int) -> str:
    ov = parent.get("original_video") or parent.get("id") or parent.get("source") or str(i)
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(ov))[-48:]
    return f"unit-{slug}"
