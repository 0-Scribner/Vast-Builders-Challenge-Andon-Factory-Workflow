"""Forty synthetic kit units so the HITL loop runs without VSS.

Agent note: captions **must** match ``inspection.parse_caption`` so tests
and the UI stay honest. Ground-truth ``true_incomplete`` is what a
reviewer would say — used by ``scripts/simulate_reviews.py`` and tests,
never by the scorer itself.

Salient defects (wheels, roof, bucket, minifig) have clean COMPLETE: NO
captions. Subtle defects (a far-side door) are labeled UNCLEAR / wrong
COMPLETE: YES so the gate HOLDs them — that is the demo of HITL value.
"""

from __future__ import annotations

from typing import Any, Dict, List

from inspection import parse_caption
from kits import CAMERA_ID, LOCATION
from llm import prior_for


def build_mock_units() -> List[Dict[str, Any]]:
    specs = _specs()
    units: List[Dict[str, Any]] = []
    for i, spec in enumerate(specs, start=1):
        kit_id = spec["kit_id"]
        caption = spec["caption"]
        inspection = parse_caption(caption, kit_id=kit_id)
        unit: Dict[str, Any] = {
            "id": f"kit-{i:03d}",
            "kit_id": kit_id,
            "filename": spec["filename"],
            "camera_id": CAMERA_ID,
            "location": LOCATION,
            "tags": [f"kit:{kit_id}", f"unit:{i:03d}", spec["variant"]],
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
    """20 complete + 14 salient incomplete + 6 subtle/unclear."""
    out: List[Dict[str, Any]] = []

    def add(kit_id: str, variant: str, caption: str, true_incomplete: bool, occlusion: bool = False) -> None:
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

    # --- complete race cars ---
    for _ in range(10):
        add(
            "race-car",
            "complete",
            "PRESENT: 4 black wheels, 1 clear windshield, 1 red roof, 2 yellow headlights, 1 minifigure with a hat, 1 blue door. "
            "MISSING: NONE. UNCLEAR: NONE. COMPLETE: YES. CONFIDENCE: HIGH. "
            "The race car sits on white paper and every listed part is in view.",
            False,
        )
    # --- complete loaders ---
    for _ in range(10):
        add(
            "front-loader",
            "complete",
            "PRESENT: 1 yellow bucket, 4 black wheels, 1 black cabin, 1 gray roll bar, 1 yellow body, 1 minifigure. "
            "MISSING: NONE. UNCLEAR: NONE. COMPLETE: YES. CONFIDENCE: HIGH. "
            "The loader is assembled and the bucket is attached at the front.",
            False,
        )
    # --- salient missing wheels (race car) ---
    for _ in range(5):
        add(
            "race-car",
            "missing-wheels",
            "PRESENT: 1 clear windshield, 1 red roof, 2 yellow headlights, 1 minifigure with a hat, 1 blue door. "
            "MISSING: 4 black wheels. UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH. "
            "The chassis sits flat on the paper with axle holes empty and no wheels attached.",
            True,
        )
    # --- salient missing roof ---
    for _ in range(3):
        add(
            "race-car",
            "missing-roof",
            "PRESENT: 4 black wheels, 1 clear windshield, 2 yellow headlights, 1 minifigure with a hat, 1 blue door. "
            "MISSING: 1 red roof. UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH. "
            "The cabin is open from above; the red roof brick is not on the car.",
            True,
        )
    # --- salient missing bucket ---
    for _ in range(3):
        add(
            "front-loader",
            "missing-bucket",
            "PRESENT: 4 black wheels, 1 black cabin, 1 gray roll bar, 1 yellow body, 1 minifigure. "
            "MISSING: 1 yellow bucket. UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH. "
            "The front arms end in empty pins; the yellow bucket is not attached.",
            True,
        )
    # --- salient missing minifig ---
    for _ in range(3):
        add(
            "race-car",
            "missing-minifig",
            "PRESENT: 4 black wheels, 1 clear windshield, 1 red roof, 2 yellow headlights, 1 blue door. "
            "MISSING: 1 minifigure with a hat. UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH. "
            "The driver's seat is empty; no minifigure is in the cabin.",
            True,
        )
    # --- subtle: far-side door, VLM says complete (human should FAIL) ---
    for _ in range(3):
        add(
            "race-car",
            "hidden-door",
            "PRESENT: 4 black wheels, 1 clear windshield, 1 red roof, 2 yellow headlights, 1 minifigure with a hat. "
            "MISSING: NONE. UNCLEAR: 1 blue door. COMPLETE: YES. CONFIDENCE: LOW. "
            "The far side of the cabin is turned away from the camera so the door cannot be verified.",
            True,
        )
    # --- occlusion: hands in frame ---
    for _ in range(3):
        add(
            "front-loader",
            "hands",
            "PRESENT: 4 black wheels, 1 yellow body. "
            "MISSING: NONE. UNCLEAR: 1 yellow bucket, 1 black cabin, 1 gray roll bar, 1 minifigure. "
            "COMPLETE: YES. CONFIDENCE: LOW. "
            "A person's hands cover the front of the loader so several parts cannot be seen.",
            True,
            occlusion=True,
        )
    return out
