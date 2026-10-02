"""Official VAST Builders Challenge video corpus.

Source of truth:
https://github.com/vast-data/vast-builders-challenge
``ARCHITECTURE_REFERENCE.md`` § Video corpus (already indexed).
``BUILD_DAY.md`` § What video you have points at that section for
camera IDs, folders, and worked queries.

Do not ingest YouTube or film replacement footage. Re-ingest only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class Camera(TypedDict):
    pack: str
    pack_name: str
    source: str
    location: str
    category: str
    camera_id: str
    scenario: str
    capture_type: str
    indexed: str
    ready: bool
    scene_id: str
    clip_kind: str


# Architecture Reference tables 1–6. Pack E is listed as ingesting soon.
CAMERAS: List[Camera] = [
    {
        "pack": "A",
        "pack_name": "Highway Traffic",
        "source": "I-24 / 3D traffic",
        "location": "nashville",
        "category": "Traffic",
        "camera_id": "i24_cam-1",
        "scenario": "traffic",
        "capture_type": "traffic",
        "indexed": "~51 multi-cam highway clips (scene*_p*c*)",
        "ready": True,
        "scene_id": "person-near-vehicle",
        "clip_kind": "highway",
    },
    {
        "pack": "B",
        "pack_name": "Live Driving",
        "source": "PIE drives",
        "location": "toronto",
        "category": "Streets",
        "camera_id": "pie_cam-3",
        "scenario": "live_driving",
        "capture_type": "streets",
        "indexed": "6 long drive sets (set01 … set06)",
        "ready": True,
        "scene_id": "person-near-vehicle",
        "clip_kind": "dashcam",
    },
    {
        "pack": "C",
        "pack_name": "Warehouse Safety",
        "source": "SDG warehouse RGB",
        "location": "warehouse3",
        "category": "Warehouse",
        "camera_id": "sdg_warehouse_cam-2",
        "scenario": "warehouse",
        "capture_type": "warehouse",
        "indexed": "~178 short ceiling / aisle clips",
        "ready": True,
        "scene_id": "warehouse-aisle",
        "clip_kind": "warehouse",
    },
    {
        "pack": "D",
        "pack_name": "Neighborhood Streets",
        "source": "Neighborhood cars",
        "location": "neighborhood",
        "category": "Streets",
        "camera_id": "neighborhood_cam-1",
        "scenario": "surveillance",
        "capture_type": "streets",
        "indexed": "2 day merges (2026-09-01, 2026-09-02)",
        "ready": True,
        "scene_id": "person-near-vehicle",
        "clip_kind": "street",
    },
    {
        "pack": "E",
        "pack_name": "SF Streets",
        "source": "SF streets",
        "location": "san_francisco",
        "category": "Streets",
        "camera_id": "sf_streets_cam-1",
        "scenario": "surveillance",
        "capture_type": "streets",
        "indexed": "4 street cameras — ingesting soon",
        "ready": False,
        "scene_id": "person-near-vehicle",
        "clip_kind": "street",
    },
    {
        "pack": "F",
        "pack_name": "Indoor Smart Spaces",
        "source": "Smart spaces",
        "location": "indoor",
        "category": "Crowds",
        "camera_id": "smartspace_cam-1",
        "scenario": "surveillance",
        "capture_type": "crowds",
        "indexed": "~102 indoor / facility camera clips",
        "ready": True,
        "scene_id": "warehouse-aisle",
        "clip_kind": "indoor",
    },
]

CAMERA_BY_ID: Dict[str, Camera] = {c["camera_id"]: c for c in CAMERAS}
READY_CAMERAS: List[Camera] = [c for c in CAMERAS if c["ready"]]
READY_CAMERA_IDS: List[str] = [c["camera_id"] for c in READY_CAMERAS]

CAMERA_TO_SCENE: Dict[str, str] = {c["camera_id"]: c["scene_id"] for c in CAMERAS}

# BUILD_DAY.md § What video you have (confirmed on the day).
# Architecture Reference adds Pack C warehouse + Pack F indoor + Pack E (soon).
BUILD_DAY_CAMERAS: List[str] = ["pie_cam-3", "i24_cam-1", "neighborhood_cam-1"]


def camera_row(camera_id: str) -> Optional[Camera]:
    return CAMERA_BY_ID.get((camera_id or "").strip())


def pack_for_camera(camera_id: str) -> str:
    row = camera_row(camera_id)
    return row["pack"] if row else "C"


def location_for_camera(camera_id: str) -> str:
    row = camera_row(camera_id)
    return row["location"] if row else ""


def clip_kind(camera_id: str) -> str:
    row = camera_row(camera_id)
    return row["clip_kind"] if row else "warehouse"


def public_corpus() -> Dict[str, Any]:
    return {
        "source_repo": "https://github.com/vast-data/vast-builders-challenge",
        "section": "ARCHITECTURE_REFERENCE.md#video-corpus-already-indexed",
        "build_day": "BUILD_DAY.md#what-video-you-have",
        "payoff_query": "person close to a moving vehicle",
        "rule": "Re-ingest only. Do not upload YouTube or film replacement footage.",
        "build_day_kinds": [
            "Dashcam driving (PIE / pie_cam-3 / toronto)",
            "Overhead multi-camera highway (I-24 / i24_cam-1 / nashville)",
            "Private neighborhood camera (neighborhood_cam-1)",
        ],
        "cameras": CAMERAS,
        "ready_camera_ids": READY_CAMERA_IDS,
    }
