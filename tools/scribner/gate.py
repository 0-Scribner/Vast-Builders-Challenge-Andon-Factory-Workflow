"""Decide AUTO_PASS / AUTO_FAIL / HOLD, with a random audit sample.

Agent note: keep audit_fraction > 0. The demo story is "we measure
escapes", not "we hope". HOLD is the correct default when unsure.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence

from learn import coverage_stats, predict_p_fail


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
        decision = "AUTO_PASS"
    elif p >= t_fail:
        decision = "AUTO_FAIL"
    else:
        decision = "HOLD"

    audit = False
    if decision != "HOLD" and _stable_rand(unit.get("id", "")) < audit_fraction:
        audit = True
        # Audited autos still keep their decision, but they also appear
        # in the review queue so a human can contradict them.
    return {
        "unit_id": unit.get("id"),
        "p_fail": round(p, 4),
        "t_pass": t_pass,
        "t_fail": t_fail,
        "decision": decision,
        "audit": audit,
        "kit_id": unit.get("kit_id"),
        "scorer_n": (scorer or {}).get("n", 0),
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
    """HOLD first (closest to 0.5), then unaudited-not, then audits still unlabeled."""
    labeled = {lab.get("unit_id") for lab in labels}
    by_id = {u["id"]: u for u in units}
    items = []
    for d in decisions:
        uid = d.get("unit_id")
        if uid in labeled:
            continue
        if d.get("decision") != "HOLD" and not d.get("audit"):
            continue
        unit = by_id.get(uid) or {}
        items.append({**unit, "decision_row": d})
    items.sort(
        key=lambda u: (
            0 if u.get("decision_row", {}).get("decision") == "HOLD" else 1,
            abs(float(u.get("decision_row", {}).get("p_fail", 0.5)) - 0.5),
        )
    )
    return items


def apply_label_override(decision: Dict[str, Any], verdict: str) -> bool:
    """True when the human contradicted an auto decision or the prior proposal."""
    mapping = {"AUTO_PASS": "COMPLETE", "AUTO_FAIL": "INCOMPLETE"}
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
