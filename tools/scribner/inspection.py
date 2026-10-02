"""Parse Cosmos Reason captions into a kit inspection record.

Contract with ``kits.prompt_for_kit``: captions contain the labeled
fields PRESENT, MISSING, UNCLEAR, COMPLETE, CONFIDENCE in that order.
The VSS reasoner may prefix/suffix extra prose and will truncate at
~1024 characters. This parser is deliberately greedy and case-insensitive.

Agent note: if Bryce changes the prompt field names, update
``_FIELD_ORDER`` and ``tools/scribner/tests/test_inspection.py`` together.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from kits import KITS, parts_for

_FIELD_ORDER = ("PRESENT", "MISSING", "UNCLEAR", "COMPLETE", "CONFIDENCE")
_FIELD_RE = re.compile(
    r"(PRESENT|MISSING|UNCLEAR|COMPLETE|CONFIDENCE)\s*:\s*",
    re.IGNORECASE,
)
_NONE_RE = re.compile(r"^\s*(none|n/?a|no|nothing|-)\s*\.?$", re.IGNORECASE)


def parse_caption(text: str, kit_id: Optional[str] = None) -> Dict[str, Any]:
    """Return a structured inspection from a plain-prose caption.

    Missing fields default to UNCLEAR rather than inventing completeness.
    """
    raw = (text or "").strip()
    spans = _split_fields(raw)
    present = _token_list(spans.get("PRESENT", ""))
    missing = _token_list(spans.get("MISSING", ""))
    unclear = _token_list(spans.get("UNCLEAR", ""))
    complete = _yes_no(spans.get("COMPLETE", ""))
    confidence = _confidence(spans.get("CONFIDENCE", ""))

    matched_missing: List[str] = []
    matched_present: List[str] = []
    if kit_id and kit_id in KITS:
        for part in parts_for(kit_id):
            label = part["label"].lower()
            pid = part["id"]
            if any(_part_mentioned(label, tok) for tok in missing):
                matched_missing.append(pid)
            elif any(_part_mentioned(label, tok) for tok in present):
                matched_present.append(pid)

    parsed = bool(spans)
    inconsistent = bool(complete is True and missing)
    return {
        "raw": raw,
        "parsed": parsed,
        "present": present,
        "missing": missing,
        "unclear": unclear,
        "complete": complete,  # True / False / None
        "confidence": confidence,  # high / medium / low / None
        "part_ids_missing": matched_missing,
        "part_ids_present": matched_present,
        "kit_id": kit_id,
        "inconsistent": inconsistent,
    }


def heuristic_prior(inspection: Dict[str, Any]) -> Dict[str, Any]:
    """Zero-shot p_fail from parsed fields. Used when W&B is absent.

    Salient, high-confidence MISSING → high p_fail (auto-fail territory).
    High-confidence COMPLETE with no missing → low p_fail.
    UNCLEAR / unparsed → ~0.5 so the unit HOLDs for a human.
    """
    complete = inspection.get("complete")
    confidence = inspection.get("confidence") or "medium"
    missing = inspection.get("missing") or []
    unclear = inspection.get("unclear") or []
    parsed = bool(inspection.get("parsed"))

    if not parsed:
        p = 0.50
        rationale = "Caption did not match PRESENT/MISSING/COMPLETE fields; hold for review."
    elif unclear or confidence == "low":
        p = 0.50
        rationale = "Unclear parts or low confidence; hold."
    elif complete is False and missing and confidence in {"high", "medium"}:
        p = 0.88 if confidence == "high" else 0.74
        rationale = f"Model reports incomplete kit; missing={missing!r}."
    elif complete is True and not missing and confidence == "high":
        p = 0.10
        rationale = "Model reports complete kit at HIGH confidence."
    elif complete is True and not missing:
        p = 0.22
        rationale = "Model reports complete kit at reduced confidence."
    elif complete is False:
        p = 0.62
        rationale = "Incomplete without a clean missing list."
    else:
        p = 0.48
        rationale = "Ambiguous completeness."

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
    # Split on commas / semicolons; keep short phrases.
    parts = re.split(r"[,;]|(?:\s+and\s+)", blob)
    cleaned = []
    for p in parts:
        t = re.sub(r"\s+", " ", p).strip(" .")
        if t and not _NONE_RE.match(t):
            cleaned.append(t)
    return cleaned


def _yes_no(blob: str) -> Optional[bool]:
    t = (blob or "").strip().split()[0].upper() if blob.strip() else ""
    if t.startswith("YES") or t == "Y" or t == "COMPLETE":
        return True
    if t.startswith("NO") or t == "N" or t == "INCOMPLETE":
        return False
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


def _part_mentioned(part_label: str, token: str) -> bool:
    tok = token.lower()
    # Match on the distinctive noun in the BOM label ("wheels", "windshield").
    nouns = [w for w in re.findall(r"[a-z]+", part_label.lower()) if w not in {"a", "an", "the", "with", "black", "clear", "red", "yellow", "blue", "gray", "grey"}]
    return any(n in tok for n in nouns if len(n) >= 4) or part_label.lower() in tok
