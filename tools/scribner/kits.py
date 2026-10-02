"""Single source of truth for LEGO kit bills of materials.

Agent note
----------
Edit this file when Bryce changes which kits they filmed or which parts
count as "complete". Then regenerate ``prompts/kit_completeness_v1.txt``::

    python3 -c "from tools.scribner.kits import write_prompt_file; write_prompt_file()"

The VSS reasoner **strips JSON** from Cosmos output and appends a
plain-prose instruction. Prompts here therefore ask for labeled inline
fields (PRESENT: … MISSING: …) that ``inspection.py`` can regex.

Each prompt must stay ≤800 characters (VSS ``custom_prompt`` limit).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

# custom_prompt hard limit from VSS ingest-config / upload-video skill
CUSTOM_PROMPT_MAX = 800

# Capture metadata stamped on every kit upload so search filters work.
CAMERA_ID = "kit-station-1"
CAPTURE_TYPE = "general"
LOCATION = "kit-bench"

Part = Dict[str, str]
Kit = Dict[str, object]

KITS: Dict[str, Kit] = {
    "race-car": {
        "name": "Race Car",
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

# Reason chips shown in the review UI. Keep ids stable — labels.jsonl
# stores them, and the scorer one-hots a subset.
REASON_CODES = [
    {"id": "agree", "label": "Model was right"},
    {"id": "vlm_missed_part", "label": "Model missed a missing part"},
    {"id": "vlm_false_missing", "label": "Model claimed a part was missing but it is there"},
    {"id": "hidden_side", "label": "Part was on the far side / occluded"},
    {"id": "hands_in_frame", "label": "Hands or clutter in frame"},
    {"id": "wrong_kit", "label": "Wrong kit / not a kit"},
    {"id": "other", "label": "Other"},
]


def kit_ids() -> List[str]:
    return list(KITS.keys())


def parts_for(kit_id: str) -> List[Part]:
    kit = KITS[kit_id]
    return list(kit["parts"])  # type: ignore[arg-type]


def bom_line(kit_id: str) -> str:
    return ", ".join(p["label"] for p in parts_for(kit_id))


def prompt_for_kit(kit_id: str) -> str:
    """Build the ≤800-char Cosmos ingest prompt for one kit type.

    The field order is a contract with ``inspection.parse_caption``.
    Do not reorder PRESENT / MISSING / UNCLEAR / COMPLETE / CONFIDENCE
    without updating the parser tests.
    """
    if kit_id not in KITS:
        raise KeyError(f"unknown kit_id={kit_id!r}; known={kit_ids()}")
    name = KITS[kit_id]["name"]
    prompt = (
        f"This clip shows a small LEGO build called {kit_id} ({name}). "
        f"A complete build has: {bom_line(kit_id)}. "
        "Look at the build from every visible side. "
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


def write_prompt_file(path: Path | None = None) -> Path:
    """Write every kit prompt into prompts/kit_completeness_v1.txt for humans and ingest-kits."""
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
