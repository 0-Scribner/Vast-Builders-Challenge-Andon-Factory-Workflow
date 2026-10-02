"""Forty synthetic Pack C units so the HITL loop runs without VSS.

Captions **must** match ``inspection.parse_caption`` (PRESENT / MISSING /
COMPLETE). Ground-truth ``true_incomplete`` is what a reviewer would say
— used by ``scripts/simulate_reviews.py`` and tests, never by the scorer.

Salient defects (person-vehicle gap, pallet in walkway, blocked lane)
have clean COMPLETE: NO captions. Subtle defects (unclear distance) are
labeled UNCLEAR / wrong COMPLETE: YES so the gate HOLDs them.
"""

from __future__ import annotations

from typing import Any, Dict, List

from inspection import parse_caption
from kits import CAMERA_ID, LOCATION
from llm import prior_for

_COMPLETE = (
    "PRESENT: a clear travel lane, person-vehicle separation, a pallet-free walkway, "
    "an unobstructed aisle path. MISSING: NONE. UNCLEAR: NONE. COMPLETE: YES. "
    "CONFIDENCE: HIGH. The aisle is open and no person is close to a moving vehicle."
)
_MISSING_GAP = (
    "PRESENT: a pallet-free walkway, an unobstructed aisle path. "
    "MISSING: person-vehicle separation, a clear travel lane. UNCLEAR: NONE. "
    "COMPLETE: NO. CONFIDENCE: HIGH. A forklift is moving close to a person in the aisle."
)
_MISSING_WALKWAY = (
    "PRESENT: a clear travel lane, person-vehicle separation. "
    "MISSING: a pallet-free walkway. UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH. "
    "A pallet sits in the pedestrian walkway."
)
_MISSING_LANE = (
    "PRESENT: person-vehicle separation, a pallet-free walkway. "
    "MISSING: a clear travel lane, an unobstructed aisle path. UNCLEAR: NONE. "
    "COMPLETE: NO. CONFIDENCE: HIGH. Equipment blocks the travel lane."
)
_HIDDEN_GAP = (
    "PRESENT: a pallet-free walkway, an unobstructed aisle path. "
    "MISSING: NONE. UNCLEAR: person-vehicle separation. COMPLETE: YES. "
    "CONFIDENCE: LOW. Distance between the person and the forklift cannot be verified."
)
_VIEW_BLOCKED = (
    "PRESENT: a clear travel lane. MISSING: NONE. "
    "UNCLEAR: person-vehicle separation, a pallet-free walkway, an unobstructed aisle path. "
    "COMPLETE: YES. CONFIDENCE: LOW. Glare and a rack hide most of the aisle."
)


def build_mock_units() -> List[Dict[str, Any]]:
    specs = _specs()
    units: List[Dict[str, Any]] = []
    for i, spec in enumerate(specs, start=1):
        kit_id = spec["kit_id"]
        caption = spec["caption"]
        inspection = parse_caption(caption, kit_id=kit_id)
        unit: Dict[str, Any] = {
            "id": f"packc-{i:03d}",
            "kit_id": kit_id,
            "filename": spec["filename"],
            "camera_id": CAMERA_ID,
            "location": LOCATION,
            "tags": [f"kit:{kit_id}", f"unit:{i:03d}", spec["variant"], "corpus:provided"],
            "caption": caption,
            "inspection": inspection,
            "source": spec["source"],
            "original_video": spec["original_video"],
            "occlusion": spec.get("occlusion", False),
            "true_incomplete": spec["true_incomplete"],
            "variant": spec["variant"],
            "mock": True,
        }
        unit["prior"] = prior_for(inspection, kit_id)
        units.append(unit)
    return units


def _specs() -> List[Dict[str, Any]]:
    """12 complete + 20 salient incomplete + 8 subtle/unclear."""
    out: List[Dict[str, Any]] = []

    def add(
        kit_id: str,
        variant: str,
        caption: str,
        true_incomplete: bool,
        occlusion: bool = False,
    ) -> None:
        n = len(out) + 1
        out.append(
            {
                "kit_id": kit_id,
                "variant": variant,
                "caption": caption,
                "true_incomplete": true_incomplete,
                "occlusion": occlusion,
                "filename": f"{kit_id}_{variant}_{n:03d}.mp4",
                "source": f"s3://mock-segments/{kit_id}/{n:03d}.mp4",
                "original_video": f"s3://mock-chunks/{kit_id}/{n:03d}.mp4",
            }
        )

    for _ in range(12):
        add("warehouse-aisle", "complete", _COMPLETE, False)
    for _ in range(8):
        add("warehouse-aisle", "missing-person-gap", _MISSING_GAP, True)
    for _ in range(5):
        add("warehouse-aisle", "missing-walkway", _MISSING_WALKWAY, True)
    for _ in range(4):
        add("warehouse-aisle", "missing-travel-lane", _MISSING_LANE, True)
    for _ in range(3):
        add("warehouse-aisle", "missing-path", _MISSING_LANE, True)
    for _ in range(5):
        add("warehouse-aisle", "hidden-gap", _HIDDEN_GAP, True)
    for _ in range(3):
        add("warehouse-aisle", "view-blocked", _VIEW_BLOCKED, True, occlusion=True)
    return out
