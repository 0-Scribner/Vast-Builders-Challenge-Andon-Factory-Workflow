"""Decide AUTO_CLEAR / AUTO_ALERT / HOLD, with a random audit sample.

False CLEAR (unsafe aisle marked clear) is the red-line failure.
AUTO_PASS / AUTO_FAIL remain aliases in coverage_stats.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence

from learn import coverage_stats, predict_p_fail

DECISION_CLEAR = "AUTO_CLEAR"
DECISION_ALERT = "AUTO_ALERT"
DECISION_HOLD = "HOLD"


def pass_blocked(unit: Dict[str, Any]) -> str:
    """Why AUTO_CLEAR is illegal, or '' if a clear is allowed."""
    insp = unit.get("inspection") or {}
    if insp.get("inconsistent"):
        return "inconsistent_caption"
    if insp.get("near_miss") is True:
        return "near_miss"
    if insp.get("path_clear") is False:
        return "path_not_clear"
    hazards = insp.get("hazards") or insp.get("missing") or []
    if hazards:
        return "hazards"
    if insp.get("complete") is False:
        return "complete_no"
    if insp.get("confidence") == "low":
        return "confidence_low"
    if insp.get("unclear"):
        return "unclear_parts"
    if unit.get("occlusion") or unit.get("view_blocked"):
        return "view_blocked"
    if insp.get("distance") == "close" and insp.get("motion") == "moving":
        if insp.get("person") is True and insp.get("vehicle_present") is True:
            return "close_moving_person_vehicle"
    if unit.get("yolo_person") and unit.get("yolo_vehicle"):
        if insp.get("path_clear") is not True or insp.get("confidence") != "high":
            return "person_and_vehicle_unconfirmed"
        if insp.get("near_miss") is True or insp.get("distance") == "close":
            return "person_vehicle_conflict"
    if insp.get("path_clear") is None and insp.get("complete") is None:
        return "path_unknown"
    if insp.get("complete") is None and insp.get("path_clear") is not True:
        return "complete_unknown"
    return ""


def decide_one(
    unit: Dict[str, Any],
    scorer: Optional[Dict[str, Any]],
    thresholds: Dict[str, float],
    *,
    audit_fraction: float = 0.10,
) -> Dict[str, Any]:
    p = predict_p_fail(unit, scorer)
    t_pass = float(thresholds.get("t_pass", 0.18))
    t_fail = float(thresholds.get("t_fail", 0.82))
    if p <= t_pass:
        decision = DECISION_CLEAR
    elif p >= t_fail:
        decision = DECISION_ALERT
    else:
        decision = DECISION_HOLD

    closed = ""
    if decision == DECISION_CLEAR:
        closed = pass_blocked(unit)
        if closed:
            insp = unit.get("inspection") or {}
            if (
                insp.get("near_miss")
                or insp.get("path_clear") is False
                or insp.get("hazards")
                or insp.get("missing")
                or insp.get("complete") is False
            ):
                decision = DECISION_ALERT
            else:
                decision = DECISION_HOLD

    audit = False
    if decision != DECISION_HOLD and _stable_rand(unit.get("id", "")) < audit_fraction:
        audit = True
    return {
        "unit_id": unit.get("id"),
        "p_fail": round(p, 4),
        "t_pass": t_pass,
        "t_fail": t_fail,
        "decision": decision,
        "audit": audit,
        "kit_id": unit.get("kit_id"),
        "scorer_n": (scorer or {}).get("n", 0),
        "fail_closed": closed or None,
    }


def decide_all(
    units: Sequence[Dict[str, Any]],
    scorer: Optional[Dict[str, Any]],
    thresholds: Dict[str, float],
    *,
    audit_fraction: float = 0.10,
) -> List[Dict[str, Any]]:
    return [decide_one(u, scorer, thresholds, audit_fraction=audit_fraction) for u in units]


def review_queue(
    units: Sequence[Dict[str, Any]],
    decisions: Sequence[Dict[str, Any]],
    labels: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    labeled = {lab.get("unit_id") for lab in labels}
    by_id = {u["id"]: u for u in units}
    items = []
    for d in decisions:
        uid = d.get("unit_id")
        if uid in labeled:
            continue
        if d.get("decision") != DECISION_HOLD and not d.get("audit"):
            continue
        unit = by_id.get(uid) or {}
        items.append({**unit, "decision_row": d})
    items.sort(
        key=lambda u: (
            0 if u.get("decision_row", {}).get("decision") == DECISION_HOLD else 1,
            abs(float(u.get("decision_row", {}).get("p_fail", 0.5)) - 0.5),
        )
    )
    return items


def apply_label_override(decision: Dict[str, Any], verdict: str) -> bool:
    mapping = {
        "AUTO_PASS": "CLEAR",
        "AUTO_CLEAR": "CLEAR",
        "AUTO_FAIL": "UNSAFE",
        "AUTO_ALERT": "UNSAFE",
    }
    auto = mapping.get(decision.get("decision", ""), "")
    return bool(auto) and auto != verdict


def metrics_bundle(
    decisions: Sequence[Dict[str, Any]],
    labels: Sequence[Dict[str, Any]],
    thresholds: Dict[str, float],
) -> Dict[str, Any]:
    stats = coverage_stats(decisions)
    n_override = sum(1 for lab in labels if lab.get("overrode"))
    n_labels = len(labels)
    stats.update(
        {
            "n_labels": float(n_labels),
            "override_rate": (n_override / n_labels) if n_labels else 0.0,
            "t_pass": float(thresholds.get("t_pass", 0.18)),
            "t_fail": float(thresholds.get("t_fail", 0.82)),
            "hold_band": float(thresholds.get("t_fail", 0.82))
            - float(thresholds.get("t_pass", 0.18)),
        }
    )
    return stats


def _stable_rand(key: str) -> float:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF
