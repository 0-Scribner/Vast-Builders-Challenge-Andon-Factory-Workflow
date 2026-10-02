"""Shift report from labeled + gated units.

Only CLEAR/UNSAFE labels plus AUTO_CLEAR / AUTO_ALERT decisions go into
the narrative. HOLD units are a backlog, not a verdict.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from andon import snapshot as andon_snapshot
from gate import review_queue
from kits import CAMERA_ID, LOCATION, PAYOFF_QUERY, PRODUCT, STACK_LINE


def render_markdown(
    units: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    labels: List[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> str:
    by_id = {u["id"]: u for u in units}
    dec = {d.get("unit_id"): d for d in decisions}
    lab = {x.get("unit_id"): x for x in labels}
    failed = []
    passed = []
    for uid, u in by_id.items():
        verdict = (lab.get(uid) or {}).get("verdict")
        decision = (dec.get(uid) or {}).get("decision")
        if verdict == "UNSAFE" or (
            not verdict and decision in {"AUTO_ALERT", "AUTO_FAIL"}
        ):
            failed.append(u)
        elif verdict == "CLEAR" or (
            not verdict and decision in {"AUTO_CLEAR", "AUTO_PASS"}
        ):
            passed.append(u)
    kits = Counter((u.get("kit_id") or "?") for u in failed)
    variants = Counter((u.get("variant") or "live") for u in failed)
    board = andon_snapshot(
        decisions=decisions,
        queue=review_queue(units, decisions, labels),
        camera_id=CAMERA_ID,
        location=LOCATION,
    )
    lines = [
        "# Scribner aisle-gate report",
        "",
        f"- Product: **{PRODUCT}**",
        f"- 安灯 ANDON line: **{board['line_ja']}** ({board['line_en']})",
        f"- 現場 gemba: `{board['camera_id']}` / `{board['location']}`",
        f"- Lamps: 緑 {board['counts']['green']} · 黄 {board['counts']['yellow']} · 赤 {board['counts']['red']}",
        f"- Rule: {board['rule']}, {board['rule_en']}",
        f"- Query: *{PAYOFF_QUERY}*",
        f"- Stack: {STACK_LINE}",
        f"- Units scanned: **{len(units)}**",
        f"- Verified CLEAR: **{len(passed)}**",
        f"- Verified UNSAFE: **{len(failed)}**",
        f"- Coverage (auto decided): **{metrics.get('coverage', 0):.0%}**",
        f"- HOLD rate: **{metrics.get('hold_rate', 0):.0%}**",
        f"- Labels: **{int(metrics.get('n_labels', 0))}**",
        f"- Thresholds: T_pass={metrics.get('t_pass', 0):.2f}  T_fail={metrics.get('t_fail', 0):.2f}",
        "",
        "## Alerts by scene",
    ]
    if not kits:
        lines.append("_None yet._")
    else:
        for k, n in kits.most_common():
            lines.append(f"- `{k}`: {n}")
    lines += ["", "## Alerts by variant"]
    if not variants:
        lines.append("_None yet._")
    else:
        for k, n in variants.most_common():
            lines.append(f"- `{k}`: {n}")
    lines += ["", "## Unsafe units"]
    for u in failed:
        insp = u.get("inspection") or {}
        hazards = ", ".join(insp.get("hazards") or insp.get("missing") or []) or "unspecified"
        p = (dec.get(u["id"]) or {}).get("p_fail")
        lines.append(
            f"- `{u.get('id')}`  scene={u.get('kit_id')}  hazard={hazards}  p_fail={p}"
        )
    lines.append("")
    return "\n".join(lines)
