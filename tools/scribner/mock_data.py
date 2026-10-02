"""Synthetic units from the official Architecture Reference corpus.

Captions match ``inspection.parse_caption``. ``true_unsafe`` (and
``true_incomplete`` alias) is oracle-only — never used by the scorer.

Pack C warehouse units stay first so existing AUTO_ALERT clip tests
keep the red aisle stand-in. Packs A/B/D/F follow (BUILD_DAY + Reference).
"""

from __future__ import annotations

from typing import Any, Dict, List

from corpus import pack_for_camera
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
_HIGHWAY_CLEAR = (
    "PERSON: NO. VEHICLE: truck. MOTION: MOVING. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. Overhead I-24 traffic. Travel lanes are clear of people."
)
_HIGHWAY = (
    "PERSON: YES. VEHICLE: truck. MOTION: MOVING. DISTANCE: CLOSE. "
    "PATH_CLEAR: NO. NEAR_MISS: YES. HAZARD: person-near-vehicle. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A person is close to a moving truck."
)
_DASHCAM_CLEAR = (
    "PERSON: NO. VEHICLE: car. MOTION: MOVING. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. Forward-facing Toronto drive. The travel lane is open."
)
_DASHCAM_PED = (
    "PERSON: YES. VEHICLE: car. MOTION: MOVING. DISTANCE: CLOSE. "
    "PATH_CLEAR: NO. NEAR_MISS: YES. HAZARD: person-near-vehicle. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A pedestrian is close to a moving car at an intersection."
)
_STREET_CLEAR = (
    "PERSON: NO. VEHICLE: car. MOTION: MOVING. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A car passes houses. No person near the vehicle."
)
_STREET_CLOSE = (
    "PERSON: YES. VEHICLE: car. MOTION: MOVING. DISTANCE: CLOSE. "
    "PATH_CLEAR: NO. NEAR_MISS: YES. HAZARD: person-near-vehicle. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A person is close to a moving car on a residential street."
)
_INDOOR_CLEAR = (
    "PERSON: YES. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. A person walks an indoor corridor. No vehicle in frame."
)
_INDOOR_EMPTY = (
    "PERSON: NO. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
    "CONFIDENCE: HIGH. An empty indoor corridor."
)
_UNCLEAR_ROAD = (
    "PERSON: YES. VEHICLE: car. MOTION: MOVING. DISTANCE: UNCLEAR. "
    "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: DISTANCE. "
    "CONFIDENCE: LOW. Distance between the person and the moving vehicle cannot be verified."
)

_PREFIX = {"A": "a", "B": "b", "C": "wh", "D": "nb", "F": "in"}


def build_mock_units() -> List[Dict[str, Any]]:
    specs = _specs()
    units: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    for spec in specs:
        pack = spec.get("pack") or pack_for_camera(spec.get("camera_id", CAMERA_ID))
        prefix = _PREFIX.get(pack, "u")
        counts[prefix] = counts.get(prefix, 0) + 1
        kit_id = spec["kit_id"]
        caption = spec["caption"]
        inspection = parse_caption(caption, kit_id=kit_id)
        camera_id = spec.get("camera_id", CAMERA_ID)
        unit: Dict[str, Any] = {
            "id": f"{prefix}-{counts[prefix]:03d}",
            "kit_id": kit_id,
            "filename": spec["filename"],
            "camera_id": camera_id,
            "location": spec.get("location", LOCATION),
            "pack": pack,
            "tags": [
                f"scene:{kit_id}",
                f"pack:{pack}",
                f"camera:{camera_id}",
                spec["variant"],
                "line:primary",
            ],
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
        camera_id = extra.get("camera_id", CAMERA_ID)
        row = {
            "kit_id": kit_id,
            "variant": variant,
            "caption": caption,
            "true_unsafe": true_unsafe,
            "filename": f"{kit_id}_{variant}_{n:03d}.mp4",
            "source": f"s3://mock-segments/{camera_id}/{n:03d}.mp4",
            "original_video": f"s3://mock-chunks/{camera_id}/{n:03d}.mp4",
            "pack": extra.get("pack") or pack_for_camera(camera_id),
        }
        row.update(extra)
        out.append(row)

    # Pack C first — existing clip RGB tests pick the first AUTO_ALERT.
    for _ in range(6):
        add("warehouse-aisle", "empty-aisle", _CLEAR, False)
    for _ in range(3):
        add("warehouse-aisle", "forklift-only", _FORKLIFT_ONLY, False, yolo_vehicle=True)
    for _ in range(3):
        add("warehouse-aisle", "person-far", _PERSON_FAR, False, yolo_person=True, yolo_vehicle=True)
    for _ in range(5):
        add(
            "warehouse-aisle",
            "forklift-near-person",
            _NEAR_MISS,
            True,
            yolo_person=True,
            yolo_vehicle=True,
        )
    for _ in range(3):
        add("warehouse-aisle", "pallet-in-walkway", _PALLET, True)
    for _ in range(3):
        add("warehouse-aisle", "unclear-distance", _UNCLEAR, True, yolo_person=True, yolo_vehicle=True)
    add("warehouse-aisle", "view-blocked", _BLOCKED, True, view_blocked=True, occlusion=True)

    # Pack A — I-24 highway (BUILD_DAY + Reference)
    for _ in range(3):
        add(
            "person-near-vehicle",
            "highway-clear",
            _HIGHWAY_CLEAR,
            False,
            camera_id="i24_cam-1",
            location="nashville",
            pack="A",
            yolo_vehicle=True,
        )
    for _ in range(3):
        add(
            "person-near-vehicle",
            "highway-close",
            _HIGHWAY,
            True,
            camera_id="i24_cam-1",
            location="nashville",
            pack="A",
            yolo_person=True,
            yolo_vehicle=True,
        )
    for _ in range(2):
        add(
            "person-near-vehicle",
            "highway-unclear",
            _UNCLEAR_ROAD,
            True,
            camera_id="i24_cam-1",
            location="nashville",
            pack="A",
            yolo_person=True,
            yolo_vehicle=True,
        )

    # Pack B — PIE dashcam / live driving (BUILD_DAY)
    for _ in range(3):
        add(
            "person-near-vehicle",
            "dashcam-clear",
            _DASHCAM_CLEAR,
            False,
            camera_id="pie_cam-3",
            location="toronto",
            pack="B",
            yolo_vehicle=True,
        )
    for _ in range(3):
        add(
            "person-near-vehicle",
            "dashcam-pedestrian",
            _DASHCAM_PED,
            True,
            camera_id="pie_cam-3",
            location="toronto",
            pack="B",
            yolo_person=True,
            yolo_vehicle=True,
        )
    for _ in range(2):
        add(
            "person-near-vehicle",
            "dashcam-unclear",
            _UNCLEAR_ROAD,
            True,
            camera_id="pie_cam-3",
            location="toronto",
            pack="B",
            yolo_person=True,
            yolo_vehicle=True,
        )

    # Pack D — neighborhood street (BUILD_DAY)
    for _ in range(2):
        add(
            "person-near-vehicle",
            "street-clear",
            _STREET_CLEAR,
            False,
            camera_id="neighborhood_cam-1",
            location="neighborhood",
            pack="D",
            yolo_vehicle=True,
        )
    for _ in range(3):
        add(
            "person-near-vehicle",
            "street-close",
            _STREET_CLOSE,
            True,
            camera_id="neighborhood_cam-1",
            location="neighborhood",
            pack="D",
            yolo_person=True,
            yolo_vehicle=True,
        )
    add(
        "person-near-vehicle",
        "street-unclear",
        _UNCLEAR_ROAD,
        True,
        camera_id="neighborhood_cam-1",
        location="neighborhood",
        pack="D",
        yolo_person=True,
        yolo_vehicle=True,
    )

    # Pack F — indoor smart spaces (Architecture Reference)
    for _ in range(2):
        add(
            "warehouse-aisle",
            "indoor-empty",
            _INDOOR_EMPTY,
            False,
            camera_id="smartspace_cam-1",
            location="indoor",
            pack="F",
        )
    for _ in range(2):
        add(
            "warehouse-aisle",
            "indoor-person",
            _INDOOR_CLEAR,
            False,
            camera_id="smartspace_cam-1",
            location="indoor",
            pack="F",
            yolo_person=True,
        )
    return out
