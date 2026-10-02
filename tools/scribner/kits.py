"""Single source of truth for bills of materials.

The judged corpus is the official provided video packs (Architecture
Reference). Each pack is a kit: Cosmos Reason captions PRESENT / MISSING /
COMPLETE against a completeness checklist. Own LEGO clips remain optional
extra kits with the same parser.

Regenerate prompts::

    PYTHONPATH=tools/scribner python3 -c "from kits import write_prompt_file; write_prompt_file()"

The VSS reasoner **strips JSON** from Cosmos output. Prompts ask for
labeled inline fields that ``inspection.py`` can regex.

Each prompt must stay ≤800 characters (VSS ``custom_prompt`` limit).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

CUSTOM_PROMPT_MAX = 800

# Official provided corpus — Pack C is the default live camera.
PACK_C_CAMERA = "sdg_warehouse_cam-2"
PACK_C_LOCATION = "warehouse3"
PACK_C_CAPTURE = "warehouse"
CROSS_PACK_QUERY = "person close to a moving vehicle"

# Default stamp for live Pack C re-ingest / scan filter.
CAMERA_ID = PACK_C_CAMERA
CAPTURE_TYPE = PACK_C_CAPTURE
LOCATION = PACK_C_LOCATION

# Explore / search camera_id → kit_id.
CAMERA_TO_KIT: Dict[str, str] = {
    "sdg_warehouse_cam-2": "warehouse-aisle",
    "i24_cam-1": "person-near-vehicle",
    "pie_cam-3": "person-near-vehicle",
    "neighborhood_cam-1": "person-near-vehicle",
    "sf_streets_cam-1": "person-near-vehicle",
    "sf_streets_cam-2": "person-near-vehicle",
    "sf_streets_cam-3": "person-near-vehicle",
    "sf_streets_cam-4": "person-near-vehicle",
    "smartspace_cam-1": "warehouse-aisle",
    "kit-station-1": "race-car",
}

Part = Dict[str, str]
Kit = Dict[str, object]

KITS: Dict[str, Kit] = {
    "warehouse-aisle": {
        "name": "Warehouse aisle (Pack C)",
        "corpus": True,
        "camera_id": PACK_C_CAMERA,
        "capture_type": PACK_C_CAPTURE,
        "location": PACK_C_LOCATION,
        "intro": (
            "This clip is official Pack C warehouse footage "
            "(sdg_warehouse_cam-2, warehouse3). "
            "A complete (safe) aisle has: a clear travel lane, "
            "person-vehicle separation, a pallet-free walkway, "
            "an unobstructed aisle path. "
            "Look at the ceiling-camera aisle. "
        ),
        "parts": [
            {"id": "travel-lane", "label": "a clear travel lane"},
            {"id": "person-gap", "label": "person-vehicle separation"},
            {"id": "walkway", "label": "a pallet-free walkway"},
            {"id": "path", "label": "an unobstructed aisle path"},
        ],
    },
    "person-near-vehicle": {
        "name": "Person near a moving vehicle (cross-pack)",
        "corpus": True,
        "camera_id": "",
        "capture_type": "general",
        "location": "",
        "intro": (
            "This clip is official challenge footage "
            "(highway, dashcam, street, or warehouse). "
            "A complete (safe) scene has: person-vehicle separation, "
            "moving-vehicle clearance, an unobstructed travel path. "
            "Look at every person near a vehicle. "
        ),
        "parts": [
            {"id": "person-gap", "label": "person-vehicle separation"},
            {"id": "clearance", "label": "moving-vehicle clearance"},
            {"id": "path", "label": "an unobstructed travel path"},
        ],
    },
    "race-car": {
        "name": "Race Car",
        "corpus": False,
        "camera_id": "kit-station-1",
        "capture_type": "general",
        "location": "kit-bench",
        "parts": [
            {"id": "wheels", "label": "4 black wheels"},
            {"id": "windshield", "label": "1 clear windshield"},
            {"id": "roof", "label": "1 red roof"},
            {"id": "headlights", "label": "2 yellow headlights"},
            {"id": "minifig", "label": "1 minifigure with a hat"},
            {"id": "door", "label": "1 blue door"},
        ],
    },
    "front-loader": {
        "name": "Front Loader",
        "corpus": False,
        "camera_id": "kit-station-1",
        "capture_type": "general",
        "location": "kit-bench",
        "parts": [
            {"id": "bucket", "label": "1 yellow bucket"},
            {"id": "wheels", "label": "4 black wheels"},
            {"id": "cabin", "label": "1 black cabin"},
            {"id": "rollbar", "label": "1 gray roll bar"},
            {"id": "body", "label": "1 yellow body"},
            {"id": "minifig", "label": "1 minifigure"},
        ],
    },
}

REASON_CODES = [
    {"id": "agree", "label": "Model was right"},
    {"id": "vlm_missed_part", "label": "Model missed a missing part"},
    {"id": "vlm_false_missing", "label": "Model claimed a part was missing but it is there"},
    {"id": "hidden_side", "label": "Part was on the far side / occluded"},
    {"id": "hands_in_frame", "label": "Hands or clutter in frame"},
    {"id": "wrong_kit", "label": "Wrong kit / not this corpus"},
    {"id": "other", "label": "Other"},
]


def kit_ids() -> List[str]:
    return list(KITS.keys())


def parts_for(kit_id: str) -> List[Part]:
    kit = KITS[kit_id]
    return list(kit["parts"])  # type: ignore[arg-type]


def bom_line(kit_id: str) -> str:
    return ", ".join(p["label"] for p in parts_for(kit_id))


def is_corpus_kit(kit_id: str) -> bool:
    kit = KITS.get(kit_id) or {}
    return bool(kit.get("corpus"))


def kit_for_camera(camera_id: str) -> str:
    cam = (camera_id or "").strip()
    if cam in CAMERA_TO_KIT:
        return CAMERA_TO_KIT[cam]
    low = cam.lower()
    if "warehouse" in low or cam.startswith("sdg_"):
        return "warehouse-aisle"
    if cam.startswith("kit-") or cam == "kit-station-1":
        return "race-car"
    if cam:
        return "person-near-vehicle"
    return "warehouse-aisle"


def prompt_for_kit(kit_id: str) -> str:
    """Build the ≤800-char Cosmos ingest prompt for one kit type.

    Field order is a contract with ``inspection.parse_caption``.
    Do not reorder PRESENT / MISSING / UNCLEAR / COMPLETE / CONFIDENCE
    without updating the parser tests.
    """
    if kit_id not in KITS:
        raise KeyError(f"unknown kit_id={kit_id!r}; known={kit_ids()}")
    kit = KITS[kit_id]
    intro = kit.get("intro")
    if intro:
        head = str(intro)
    else:
        name = kit["name"]
        head = (
            f"This clip shows a small LEGO build called {kit_id} ({name}). "
            f"A complete build has: {bom_line(kit_id)}. "
            "Look at the build from every visible side. "
        )
    prompt = (
        f"{head}"
        "Write one paragraph in this exact order: "
        "PRESENT: the listed parts you clearly see; "
        "MISSING: the listed parts that are absent, or NONE; "
        "UNCLEAR: parts you cannot verify; "
        "COMPLETE: YES or NO; "
        "CONFIDENCE: HIGH, MEDIUM, or LOW; "
        "then one sentence on where any gap is. "
        "Count only what is clearly visible; never assume a part is present because it should be."
    )
    if len(prompt) > CUSTOM_PROMPT_MAX:
        raise ValueError(
            f"prompt for {kit_id} is {len(prompt)} chars; VSS max is {CUSTOM_PROMPT_MAX}"
        )
    return prompt


def write_prompt_file(path: Optional[Path] = None) -> Path:
    """Write every kit prompt into prompts/kit_completeness_v1.txt."""
    here = Path(__file__).resolve().parent
    root = here
    for p in [here, *here.parents]:
        if (p / "AGENTS.md").exists() or (p / "prompts").is_dir():
            root = p
            break
    out = path or (root / "prompts" / "kit_completeness_v1.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        "# Generated from tools/scribner/kits.py — do not hand-edit.",
        f"# Each CUSTOM PROMPT body is ≤{CUSTOM_PROMPT_MAX} characters.",
        f"# Default provided corpus: Pack C camera_id={PACK_C_CAMERA} "
        f"location={PACK_C_LOCATION} capture_type={PACK_C_CAPTURE}",
        f"# Cross-pack search: {CROSS_PACK_QUERY}",
        "",
    ]
    for kid in kit_ids():
        body = prompt_for_kit(kid)
        blocks.append(f"## kit_id={kid}  chars={len(body)}")
        blocks.append(body)
        blocks.append("")
    out.write_text("\n".join(blocks), encoding="utf-8")
    return out


if __name__ == "__main__":
    p = write_prompt_file()
    for kid in kit_ids():
        print(f"{kid}: {len(prompt_for_kit(kid))} chars")
    print(f"wrote {p}")
