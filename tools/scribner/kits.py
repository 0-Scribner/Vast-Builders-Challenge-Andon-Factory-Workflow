"""Primary product: near-miss / path-clear schema on the official corpus.

The judged demo uses the Architecture Reference video corpus
(I-24, PIE dashcam, neighborhood, Pack C warehouse, smart spaces).
The same prompt-as-schema is the payoff query
*person close to a moving vehicle*.

Plan B (LEGO completeness) lives on branch
``cursor/plan-b-lego-completeness-72e3`` — do not mix those BOMs here.

Regenerate prompts::

    PYTHONPATH=tools/scribner python3 -c "from kits import write_prompt_file; write_prompt_file()"
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from corpus import CAMERA_TO_SCENE as _CORPUS_SCENES

CUSTOM_PROMPT_MAX = 800

LINE = "primary"
PRODUCT = "warehouse-near-miss"
PLAN_B_BRANCH = "cursor/plan-b-lego-completeness-72e3"
PAYOFF_QUERY = "person close to a moving vehicle"
STACK_LINE = "VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor"

PACK_C_CAMERA = "sdg_warehouse_cam-2"
PACK_C_LOCATION = "warehouse3"
PACK_C_CAPTURE = "warehouse"
CROSS_PACK_QUERY = PAYOFF_QUERY

CAMERA_ID = PACK_C_CAMERA
CAPTURE_TYPE = PACK_C_CAPTURE
LOCATION = PACK_C_LOCATION

CAMERA_TO_SCENE: Dict[str, str] = dict(_CORPUS_SCENES)
CAMERA_TO_SCENE.update(
    {
        "sf_streets_cam-2": "person-near-vehicle",
        "sf_streets_cam-3": "person-near-vehicle",
        "sf_streets_cam-4": "person-near-vehicle",
    }
)
CAMERA_TO_KIT = CAMERA_TO_SCENE

Hazard = Dict[str, str]
Scene = Dict[str, object]

SCENES: Dict[str, Scene] = {
    "warehouse-aisle": {
        "name": "Warehouse aisle (Pack C)",
        "corpus": True,
        "camera_id": PACK_C_CAMERA,
        "capture_type": PACK_C_CAPTURE,
        "location": PACK_C_LOCATION,
        "intro": (
            "This clip is official Pack C warehouse footage "
            "(sdg_warehouse_cam-2, warehouse3). "
            "Judge path safety: a person close to a moving vehicle is a near-miss; "
            "a pallet or body in a travel lane is a blocked path. "
        ),
        "hazards": [
            {"id": "forklift-near-person", "label": "forklift-near-person"},
            {"id": "pallet-in-walkway", "label": "pallet-in-walkway"},
            {"id": "person-in-aisle", "label": "person-in-aisle"},
            {"id": "blocked-path", "label": "blocked-path"},
        ],
        "vehicle_examples": "forklift, truck, pallet-jack, other",
    },
    "person-near-vehicle": {
        "name": "Person near a moving vehicle (cross-pack)",
        "corpus": True,
        "camera_id": "",
        "capture_type": "general",
        "location": "",
        "intro": (
            "This clip may be highway, dashcam, street, or warehouse. "
            "Judge whether a person is close to a moving vehicle. "
        ),
        "hazards": [
            {"id": "person-near-vehicle", "label": "person-near-vehicle"},
            {"id": "blocked-path", "label": "blocked-path"},
        ],
        "vehicle_examples": "forklift, truck, car, bus, other",
    },
}

KITS = SCENES

REASON_CODES = [
    {"id": "agree", "label": "Gate / caption was right"},
    {"id": "vlm_missed_near_miss", "label": "Model missed a near-miss"},
    {"id": "vlm_false_alert", "label": "Model alerted but the path was clear"},
    {"id": "far_but_looks_close", "label": "Person and vehicle look close but are not"},
    {"id": "pallet_not_in_path", "label": "Pallet is present but not in the travel path"},
    {"id": "view_blocked", "label": "View too dark / blurry / occluded"},
    {"id": "wrong_camera", "label": "Wrong site / not this gate"},
    {"id": "other", "label": "Other"},
]


def scene_ids() -> List[str]:
    return list(SCENES.keys())


kit_ids = scene_ids


def hazards_for(scene_id: str) -> List[Hazard]:
    scene = SCENES[scene_id]
    return list(scene["hazards"])  # type: ignore[arg-type]


parts_for = hazards_for


def hazard_line(scene_id: str) -> str:
    return ", ".join(h["label"] for h in hazards_for(scene_id))


def is_corpus_kit(kit_id: str) -> bool:
    return kit_id in SCENES


def kit_for_camera(camera_id: str) -> str:
    cam = (camera_id or "").strip()
    if cam in CAMERA_TO_SCENE:
        return CAMERA_TO_SCENE[cam]
    low = cam.lower()
    if "warehouse" in low or cam.startswith("sdg_"):
        return "warehouse-aisle"
    if cam:
        return "person-near-vehicle"
    return "warehouse-aisle"


scene_for_camera = kit_for_camera


def prompt_for_scene(scene_id: str) -> str:
    if scene_id not in SCENES:
        raise KeyError(f"unknown scene_id={scene_id!r}; known={scene_ids()}")
    scene = SCENES[scene_id]
    prompt = (
        f"{scene['intro']}"
        "Write one paragraph in this exact order: "
        "PERSON: YES, NO, or UNCLEAR; "
        f"VEHICLE: {scene['vehicle_examples']}, or NONE; "
        "MOTION: MOVING, STOPPED, or NONE; "
        "DISTANCE: CLOSE, FAR, or NONE; "
        "PATH_CLEAR: YES or NO; "
        "NEAR_MISS: YES or NO; "
        f"HAZARD: {hazard_line(scene_id)}, or NONE; "
        "UNCLEAR: what you cannot verify or NONE; "
        "CONFIDENCE: HIGH, MEDIUM, or LOW; "
        "then one sentence on the closest person-vehicle pair. "
        "Count only what is clearly visible; never assume a path is clear."
    )
    if len(prompt) > CUSTOM_PROMPT_MAX:
        raise ValueError(
            f"prompt for {scene_id} is {len(prompt)} chars; VSS max is {CUSTOM_PROMPT_MAX}"
        )
    return prompt


prompt_for_kit = prompt_for_scene


def write_prompt_file(path: Optional[Path] = None) -> Path:
    here = Path(__file__).resolve().parent
    root = here
    for p in [here, *here.parents]:
        if (p / "AGENTS.md").exists() or (p / "prompts").is_dir():
            root = p
            break
    out = path or (root / "prompts" / "warehouse_near_miss_v1.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        "# Generated from tools/scribner/kits.py — do not hand-edit.",
        f"# Each CUSTOM PROMPT body is ≤{CUSTOM_PROMPT_MAX} characters.",
        f"# Primary line={LINE} product={PRODUCT}",
        f"# Pack C camera_id={PACK_C_CAMERA} location={PACK_C_LOCATION} capture_type={PACK_C_CAPTURE}",
        f"# Cross-pack search: {CROSS_PACK_QUERY}",
        f"# Plan B branch: {PLAN_B_BRANCH}",
        "",
    ]
    for sid in scene_ids():
        body = prompt_for_scene(sid)
        blocks.append(f"## scene_id={sid}  chars={len(body)}")
        blocks.append(body)
        blocks.append("")
    out.write_text("\n".join(blocks), encoding="utf-8")
    return out


if __name__ == "__main__":
    p = write_prompt_file()
    for sid in scene_ids():
        print(f"{sid}: {len(prompt_for_scene(sid))} chars")
    print(f"wrote {p}")
