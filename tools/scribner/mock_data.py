"""Forty synthetic Pack C units so the HITL loop runs without VSS.

Captions match ``inspection.parse_caption``. ``true_unsafe`` (and
``true_incomplete`` alias) is oracle-only, never used by the scorer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from inspection import parse_caption
from kits import CAMERA_ID, LOCATION
from llm import prior_for

_CLEAR = (
    "PERSON: NO. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. The aisle is empty and the travel lane is open."
)
_FORKLIFT_ONLY = (
    "PERSON: NO. VEHICLE: forklift. MOTION: MOVING. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A forklift travels an empty aisle."
)
_PERSON_FAR = (
    "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: FAR. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A person stands well clear of a moving forklift."
)
_NEAR_MISS = (
    "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: CLOSE. "
    "PATH_CLEAR: NO. NEAR_MISS: YES. HAZARD: forklift-near-person. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A forklift is moving close to a person in the aisle."
)
_PALLET = (
    "PERSON: NO. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
    "PATH_CLEAR: NO. NEAR_MISS: NO. HAZARD: pallet-in-walkway. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A pallet sits in the pedestrian walkway."
)
_UNCLEAR = (
    "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: UNCLEAR. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: DISTANCE. "
    "CONFIDENCE: LOW. Distance between the person and the forklift cannot be verified."
)
_BLOCKED = (
    "PERSON: NO. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: PATH_CLEAR. "
    "CONFIDENCE: LOW. Glare and a rack hide most of the aisle."
)
_HIGHWAY = (
    "PERSON: YES. VEHICLE: truck. MOTION: MOVING. DISTANCE: CLOSE. "
    "PATH_CLEAR: NO. NEAR_MISS: YES. HAZARD: person-near-vehicle. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A person is close to a moving truck."
)


def build_mock_units() -> List[Dict[str, Any]]:
    specs = _specs()
    units: List[Dict[str, Any]] = []
    for i, spec in enumerate(specs, start=1):
        kit_id = spec["kit_id"]
        caption = spec["caption"]
        inspection = parse_caption(caption, kit_id=kit_id)
        unit: Dict[str, Any] = {
            "id": f"wh-{i:03d}",
            "kit_id": kit_id,
            "filename": spec["filename"],
            "camera_id": spec.get("camera_id", CAMERA_ID),
            "location": spec.get("location", LOCATION),
            "tags": [f"scene:{kit_id}", f"unit:{i:03d}", spec["variant"], "line:primary"],
            "caption": caption,
            "inspection": inspection,
            "source": spec["source"],
            "original_video": spec["original_video"],
            "occlusion": spec.get("occlusion", False),
            "view_blocked": spec.get("view_blocked", False),
            "yolo_person": spec.get("yolo_person", False),
            "yolo_vehicle": spec.get("yolo_vehicle", False),
            "true_unsafe": spec["true_unsafe"],
            "true_incomplete": spec["true_unsafe"],
            "variant": spec["variant"],
            "mock": True,
        }
        unit["prior"] = prior_for(inspection, kit_id)
        units.append(unit)
    return units


def _specs() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def add(
        kit_id: str,
        variant: str,
        caption: str,
        true_unsafe: bool,
        **extra: Any,
    ) -> None:
        n = len(out) + 1
        row = {
            "kit_id": kit_id,
            "variant": variant,
            "caption": caption,
            "true_unsafe": true_unsafe,
            "filename": f"{kit_id}_{variant}_{n:03d}.mp4",
            "source": f"s3://mock-segments/{kit_id}/{n:03d}.mp4",
            "original_video": f"s3://mock-chunks/{kit_id}/{n:03d}.mp4",
        }
        row.update(extra)
        out.append(row)

    for _ in range(8):
        add("warehouse-aisle", "empty-aisle", _CLEAR, False)
    for _ in range(4):
        add("warehouse-aisle", "forklift-only", _FORKLIFT_ONLY, False, yolo_vehicle=True)
    for _ in range(4):
        add("warehouse-aisle", "person-far", _PERSON_FAR, False, yolo_person=True, yolo_vehicle=True)
    for _ in range(8):
        add(
            "warehouse-aisle",
            "forklift-near-person",
            _NEAR_MISS,
            True,
            yolo_person=True,
            yolo_vehicle=True,
        )
    for _ in range(5):
        add("warehouse-aisle", "pallet-in-walkway", _PALLET, True)
    for _ in range(5):
        add("warehouse-aisle", "unclear-distance", _UNCLEAR, True, yolo_person=True, yolo_vehicle=True)
    for _ in range(3):
        add("warehouse-aisle", "view-blocked", _BLOCKED, True, view_blocked=True, occlusion=True)
    for _ in range(3):
        add(
            "person-near-vehicle",
            "highway-close",
            _HIGHWAY,
            True,
            camera_id="i24_cam-1",
            location="nashville",
            yolo_person=True,
            yolo_vehicle=True,
        )
    return out
