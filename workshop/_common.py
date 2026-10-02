#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

PACK_C_CAMERA = "sdg_warehouse_cam-2"
PACK_C_LOCATION = "warehouse3"
PAYOFF_QUERY = "person close to a moving vehicle"
SCHEMA_FIELDS = ("PATH_CLEAR:", "NEAR_MISS:", "UNCLEAR:", "CONFIDENCE:")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        if (p / "tools" / "scribner" / "vss_client.py").is_file():
            return p
    raise SystemExit("Run this from an applied Scribner checkout; tools/scribner/vss_client.py not found")


def scribner_imports():
    root = repo_root()
    mod = root / "tools" / "scribner"
    if str(mod) not in sys.path:
        sys.path.insert(0, str(mod))
    from vss_client import VssClient  # type: ignore
    from kits import prompt_for_kit  # type: ignore
    return VssClient, prompt_for_kit


def report_dir() -> Path:
    out = Path(os.environ.get("SCRIBNER_EVIDENCE_DIR", "/tmp/scribner-live-evidence"))
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_report(name: str, data: Dict[str, Any]) -> Path:
    data = {"ts_epoch": int(time.time()), **data}
    path = report_dir() / name
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"report={path}")
    return path


def exact_pack_c(parents: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in parents
        if str(p.get("camera_id") or "") == PACK_C_CAMERA
        and str(p.get("location") or "") == PACK_C_LOCATION
    ]


def timeline_sources(parent: Dict[str, Any]) -> List[str]:
    timeline = parent.get("timeline") or []
    if not isinstance(timeline, list):
        raise SystemExit("Malformed Explore timeline")
    out = []
    for item in timeline:
        if not isinstance(item, dict):
            raise SystemExit("Malformed Explore timeline entry")
        src = str(item.get("source") or item.get("preview_source") or "")
        if src:
            out.append(src)
    return out


def complete_parent(parent: Dict[str, Any]) -> bool:
    timeline = parent.get("timeline") or []
    if not isinstance(timeline, list) or not timeline:
        return False
    numbers = []
    totals = []
    for item in timeline:
        if not isinstance(item, dict):
            return False
        try:
            if item.get("segment_number") is not None:
                numbers.append(int(item["segment_number"]))
            if item.get("total_segments") is not None:
                totals.append(int(item["total_segments"]))
        except (TypeError, ValueError):
            return False
    if numbers and totals:
        total = max(totals)
        return sorted(set(numbers)) == list(range(1, total + 1))
    # Explore itself only exposes fully-indexed parent chunks in the official skill.
    return bool(timeline_sources(parent))


def first_source(parent: Dict[str, Any]) -> str:
    sources = timeline_sources(parent)
    if sources:
        return sources[0]
    return str(parent.get("preview_source") or parent.get("source") or "")


def parent_id(parent: Dict[str, Any]) -> str:
    return str(parent.get("original_video") or parent.get("stream_id") or parent.get("filename") or "")


def schema_present(text: str) -> Dict[str, bool]:
    upper = (text or "").upper()
    return {field[:-1].lower(): field in upper for field in SCHEMA_FIELDS}


def schema_complete(text: str) -> bool:
    return all(schema_present(text).values())


def require_live_env() -> None:
    needed = [
        bool(os.environ.get("INGRESS_URL") or os.environ.get("VSS_URL")),
        bool(os.environ.get("USERNAME") or os.environ.get("VSS_USERNAME")),
        bool(os.environ.get("PASSWORD") or os.environ.get("VSS_PASSWORD")),
    ]
    if not all(needed):
        raise SystemExit(
            "Missing VSS environment. On workshop VM: source the single /config/<team>.config first. "
            "Never print it."
        )
