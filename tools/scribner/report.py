"""Shift report from labeled + gated units.

Agent note: only COMPLETE/INCOMPLETE labels plus AUTO_* decisions go
into the narrative. HOLD units are a backlog, not a verdict.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def render_markdown(units: List[Dict[str, Any]], decisions: List[Dict[str, Any]], labels: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
    by_id = {u["id"]: u for u in units}
    dec = {d.get("unit_id"): d for d in decisions}
    lab = {x.get("unit_id"): x for x in labels}
    failed = []
    passed = []
    for uid, u in by_id.items():
        verdict = (lab.get(uid) or {}).get("verdict")
        decision = (dec.get(uid) or {}).get("decision")
        if verdict == "INCOMPLETE" or (not verdict and decision == "AUTO_FAIL"):
            failed.append(u)
        elif verdict == "COMPLETE" or (not verdict and decision == "AUTO_PASS"):
            passed.append(u)
    kits = Counter((u.get("kit_id") or "?") for u in failed)
    variants = Counter((u.get("variant") or "live") for u in failed)
    lines = [
        "# Scribner kit completeness report",
        "",
        f"- Units scanned: **{len(units)}**",
        f"- Verified complete: **{len(passed)}**",
        f"- Verified incomplete: **{len(failed)}**",
        f"- Coverage (auto decided): **{metrics.get('coverage', 0):.0%}**",
        f"- HOLD rate: **{metrics.get('hold_rate', 0):.0%}**",
        f"- Labels: **{int(metrics.get('n_labels', 0))}**",
        f"- Thresholds: T_pass={metrics.get('t_pass', 0):.2f}  T_fail={metrics.get('t_fail', 0):.2f}",
        "",
        "## Failures by kit",
    ]
    if not kits:
        lines.append("_None yet._")
    else:
        for k, n in kits.most_common():
            lines.append(f"- `{k}`: {n}")
    lines += ["", "## Failures by variant / reason proxy"]
    if not variants:
        lines.append("_None yet._")
    else:
        for k, n in variants.most_common():
            lines.append(f"- `{k}`: {n}")
    lines += ["", "## Incomplete units"]
    for u in failed:
        insp = u.get("inspection") or {}
        missing = ", ".join(insp.get("missing") or []) or "unspecified"
        p = (dec.get(u["id"]) or {}).get("p_fail")
        lines.append(
            f"- `{u.get('id')}`  kit={u.get('kit_id')}  missing={missing}  p_fail={p}"
        )
    lines.append("")
    return "\n".join(lines)
