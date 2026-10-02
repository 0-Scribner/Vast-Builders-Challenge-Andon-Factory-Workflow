"""Optional W&B Inference prior. Falls back to inspection.heuristic_prior.

Agent note: never fail the gate because W&B is missing. Credits and
network are flaky on a hackathon day. Cache by caption hash so a retrain
does not re-spend tokens.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

import config
from inspection import heuristic_prior

_CACHE: Dict[str, Dict[str, Any]] = {}


def prior_for(inspection: Dict[str, Any], kit_id: str) -> Dict[str, Any]:
    key = hashlib.sha256(
        (kit_id + "|" + (inspection.get("raw") or "")).encode("utf-8")
    ).hexdigest()
    if key in _CACHE:
        return _CACHE[key]
    heuristic = heuristic_prior(inspection)
    result = heuristic
    if config.WANDB_API_KEY:
        try:
            wandb = _wandb_prior(inspection, kit_id)
            result = merge_wandb_prior(heuristic, wandb, inspection)
        except Exception as exc:  # noqa: BLE001 — demo must not crash
            result = {**heuristic, "wandb_error": type(exc).__name__}
    _CACHE[key] = result
    return result


def merge_wandb_prior(
    heuristic: Dict[str, Any],
    wandb: Optional[Dict[str, Any]],
    inspection: Dict[str, Any],
) -> Dict[str, Any]:
    """W&B may corroborate. It must not green-light a fail-closed heuristic.

    False CLEAR is the red line: a NEAR_MISS / blocked-path prior stays ≥ 0.8
    even if the LLM replies PASS. LOW / UNCLEAR stays in the HOLD band.
    """
    if not wandb:
        return heuristic
    p_h = float(heuristic.get("p_fail_prior") or 0.5)
    try:
        p_w = float(wandb.get("p_fail_prior") or 0.5)
    except (TypeError, ValueError):
        p_w = p_h
    p_w = min(max(p_w, 0.02), 0.98)
    fail_closed = bool(
        inspection.get("near_miss")
        or inspection.get("inconsistent")
        or inspection.get("path_clear") is False
        or (inspection.get("hazards") or inspection.get("missing"))
    )
    hold_closed = bool(
        inspection.get("confidence") == "low"
        or inspection.get("unclear")
        or inspection.get("complete") is None
    )
    proposed = str(wandb.get("proposed") or "")
    if fail_closed:
        p_w = max(p_w, p_h, 0.8)
        proposed = "FAIL"
    elif hold_closed and p_w < 0.45:
        p_w = 0.45
        if proposed == "PASS":
            proposed = "HOLD"
    elif p_h >= 0.6:
        p_w = max(p_w, p_h)
        if proposed == "PASS":
            proposed = heuristic.get("proposed") or "FAIL"
    out = dict(wandb)
    out["p_fail_prior"] = p_w
    out["proposed"] = proposed or wandb.get("proposed") or heuristic.get("proposed")
    out["heuristic_p_fail_prior"] = p_h
    out["source"] = wandb.get("source") or "wandb"
    return out


def _wandb_prior(inspection: Dict[str, Any], kit_id: str) -> Optional[Dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI(
        base_url=config.WANDB_INFERENCE_URL,
        api_key=config.WANDB_API_KEY,
        project=f"{config.WANDB_TEAM}/{config.WANDB_PROJECT}"
        if config.WANDB_TEAM and config.WANDB_PROJECT
        else None,
    )
    payload = {
        "scene_id": kit_id,
        "path_clear": inspection.get("path_clear"),
        "near_miss": inspection.get("near_miss"),
        "hazards": inspection.get("hazards") or inspection.get("missing"),
        "unclear": inspection.get("unclear"),
        "person": inspection.get("person"),
        "vehicle_present": inspection.get("vehicle_present"),
        "motion": inspection.get("motion"),
        "distance": inspection.get("distance"),
        "confidence": inspection.get("confidence"),
        "inconsistent": inspection.get("inconsistent"),
        "caption": (inspection.get("raw") or "")[:800],
    }
    resp = client.chat.completions.create(
        model=config.SCRIBNER_MODEL,
        temperature=0,
        max_tokens=200,
        messages=[
            {
                "role": "system",
                "content": (
                    "You verify warehouse path safety from a parsed caption. "
                    "Reply with ONLY JSON: "
                    '{"p_fail_prior": float 0-1, "proposed": "PASS"|"FAIL"|"HOLD", '
                    '"rationale": string ≤140 chars}. '
                    "p_fail_prior is P(the aisle is UNSAFE / a near-miss). "
                    "If NEAR_MISS is YES, PATH_CLEAR is NO, or a named hazard exists, "
                    "p_fail_prior ≥ 0.8. "
                    "If PATH_CLEAR=YES, NEAR_MISS=NO, HIGH confidence, p_fail_prior ≤ 0.15. "
                    "If UNCLEAR or LOW, around 0.5. "
                    "Never propose PASS when a person is close to a moving vehicle."
                ),
            },
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(text)
    p = float(data.get("p_fail_prior", 0.5))
    p = min(max(p, 0.02), 0.98)
    return {
        "p_fail_prior": p,
        "proposed": data.get("proposed") or "HOLD",
        "rationale": str(data.get("rationale") or "")[:200],
        "source": "wandb",
    }
