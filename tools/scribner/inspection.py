"""Parse Cosmos Reason captions into a warehouse / near-miss record.

Contract with ``kits.prompt_for_scene``: PERSON, VEHICLE, MOTION,
DISTANCE, PATH_CLEAR, NEAR_MISS, HAZARD, UNCLEAR, CONFIDENCE.
False CLEAR is the red line: PATH_CLEAR YES + NEAR_MISS YES is inconsistent.

``complete=True`` means the path is CLEAR (safe). ``complete=False`` means UNSAFE.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from kits import SCENES, hazards_for

_FIELD_RE = re.compile(
    r"(PERSON|VEHICLE|MOTION|DISTANCE|PATH_CLEAR|NEAR_MISS|HAZARD|UNCLEAR|CONFIDENCE)\s*:\s*",
    re.IGNORECASE,
)
_NONE_RE = re.compile(r"^\s*(none|n/?a|no|nothing|-)\s*\.?$", re.IGNORECASE)
_VEHICLE_WORDS = (
    "forklift",
    "truck",
    "car",
    "bus",
    "van",
    "pallet-jack",
    "pallet jack",
    "tugger",
    "vehicle",
)


def parse_caption(text: str, kit_id: Optional[str] = None) -> Dict[str, Any]:
    raw = (text or "").strip()
    spans = _split_fields(raw)
    person = _yes_no_unclear(spans.get("PERSON", ""))
    vehicle_raw = (spans.get("VEHICLE") or "").strip()
    vehicle_tokens = _token_list(vehicle_raw)
    vehicle_present = _vehicle_present(vehicle_raw, vehicle_tokens)
    motion = _motion(spans.get("MOTION", ""))
    distance = _distance(spans.get("DISTANCE", ""))
    path_clear = _yes_no(spans.get("PATH_CLEAR", ""))
    near_miss = _yes_no(spans.get("NEAR_MISS", ""))
    hazards = _token_list(spans.get("HAZARD", ""))
    unclear = _token_list(spans.get("UNCLEAR", ""))
    confidence = _confidence(spans.get("CONFIDENCE", ""))

    matched_hazards: List[str] = []
    if kit_id and kit_id in SCENES:
        for hz in hazards_for(kit_id):
            label = hz["label"].lower()
            hid = hz["id"]
            if any(_part_mentioned(label, tok) for tok in hazards):
                matched_hazards.append(hid)

    parsed = bool(spans)
    inconsistent = bool(path_clear is True and (near_miss is True or hazards))

    if not parsed:
        complete: Optional[bool] = None
    elif inconsistent:
        complete = False
    elif near_miss is True or path_clear is False or hazards:
        complete = False
    elif path_clear is True and near_miss is False and not hazards:
        complete = True
    else:
        complete = None

    return {
        "raw": raw,
        "parsed": parsed,
        "person": person,
        "vehicle": vehicle_tokens,
        "vehicle_present": vehicle_present,
        "motion": motion,
        "distance": distance,
        "path_clear": path_clear,
        "near_miss": near_miss,
        "hazards": matched_hazards or hazards,
        "missing": matched_hazards or hazards,
        "unclear": unclear,
        "complete": complete,
        "confidence": confidence,
        "part_ids_missing": matched_hazards,
        "part_ids_present": [],
        "kit_id": kit_id,
        "inconsistent": inconsistent,
    }


def heuristic_prior(inspection: Dict[str, Any]) -> Dict[str, Any]:
    """p_fail = P(unsafe). UNCLEAR / LOW → ~0.5 HOLD."""
    complete = inspection.get("complete")
    confidence = inspection.get("confidence") or "medium"
    hazards = inspection.get("hazards") or inspection.get("missing") or []
    unclear = inspection.get("unclear") or []
    parsed = bool(inspection.get("parsed"))
    near_miss = inspection.get("near_miss")
    path_clear = inspection.get("path_clear")

    if not parsed:
        p = 0.50
        rationale = "Caption did not match PATH_CLEAR / NEAR_MISS fields; hold."
    elif unclear or confidence == "low":
        p = 0.50
        rationale = "Unclear fields or low confidence; hold."
    elif inspection.get("inconsistent"):
        p = 0.90
        rationale = "PATH_CLEAR YES conflicts with NEAR_MISS or a named hazard."
    elif (near_miss is True or path_clear is False or hazards) and confidence in {
        "high",
        "medium",
    }:
        p = 0.88 if confidence == "high" else 0.74
        rationale = f"Near-miss or blocked path; hazards={hazards!r}."
    elif complete is True and not hazards and confidence == "high":
        p = 0.10
        rationale = "Path clear at HIGH confidence."
    elif complete is True and not hazards:
        p = 0.22
        rationale = "Path clear at reduced confidence."
    elif complete is False:
        p = 0.62
        rationale = "Unsafe without a clean hazard list."
    else:
        p = 0.48
        rationale = "Ambiguous path safety."

    return {
        "p_fail_prior": float(p),
        "proposed": "FAIL" if p >= 0.6 else ("PASS" if p <= 0.3 else "HOLD"),
        "rationale": rationale,
        "source": "heuristic",
    }


def _split_fields(text: str) -> Dict[str, str]:
    matches = list(_FIELD_RE.finditer(text))
    if not matches:
        return {}
    out: Dict[str, str] = {}
    for i, m in enumerate(matches):
        key = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[key] = text[start:end].strip().rstrip(".;")
    return out


def _token_list(blob: str) -> List[str]:
    blob = (blob or "").strip()
    if not blob or _NONE_RE.match(blob):
        return []
    parts = re.split(r"[,;]|(?:\s+and\s+)", blob)
    cleaned = []
    for p in parts:
        t = re.sub(r"\s+", " ", p).strip(" .")
        if t and not _NONE_RE.match(t):
            cleaned.append(t)
    return cleaned


def _yes_no(blob: str) -> Optional[bool]:
    t = (blob or "").strip().split()[0].upper() if (blob or "").strip() else ""
    if t.startswith("YES") or t in {"Y", "CLEAR", "COMPLETE"}:
        return True
    if t.startswith("NO") or t in {"N", "UNSAFE", "INCOMPLETE"}:
        return False
    return None


def _yes_no_unclear(blob: str) -> Optional[bool]:
    t = (blob or "").strip().upper()
    if t.startswith("UNCLEAR"):
        return None
    return _yes_no(blob)


def _motion(blob: str) -> Optional[str]:
    t = (blob or "").strip().upper()
    if t.startswith("MOV"):
        return "moving"
    if t.startswith("STOP"):
        return "stopped"
    if t.startswith("NONE"):
        return "none"
    return None


def _distance(blob: str) -> Optional[str]:
    t = (blob or "").strip().upper()
    if t.startswith("CLOSE"):
        return "close"
    if t.startswith("FAR"):
        return "far"
    if t.startswith("NONE"):
        return "none"
    return None


def _confidence(blob: str) -> Optional[str]:
    t = (blob or "").strip().upper()
    if t.startswith("HIGH"):
        return "high"
    if t.startswith("MED"):
        return "medium"
    if t.startswith("LOW"):
        return "low"
    return None


def _vehicle_present(raw: str, tokens: List[str]) -> Optional[bool]:
    blob = (raw or "").strip()
    if not blob or _NONE_RE.match(blob):
        return False
    low = blob.lower()
    if any(w in low for w in _VEHICLE_WORDS) or tokens:
        return True
    return None


def _part_mentioned(part_label: str, token: str) -> bool:
    tok = token.lower()
    nouns = [
        w
        for w in re.findall(r"[a-z]+", part_label.lower())
        if w not in {"a", "an", "the", "with", "black", "clear", "red", "yellow", "blue", "gray", "grey"}
    ]
    return any(n in tok for n in nouns if len(n) >= 4) or part_label.lower() in tok
