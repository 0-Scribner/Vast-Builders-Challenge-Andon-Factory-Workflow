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
    result = heuristic_prior(inspection)
    if config.WANDB_API_KEY:
        try:
            result = _wandb_prior(inspection, kit_id) or result
        except Exception as exc:  # noqa: BLE001 — demo must not crash
            result = {**result, "wandb_error": type(exc).__name__}
    _CACHE[key] = result
    return result


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
        "kit_id": kit_id,
        "complete": inspection.get("complete"),
        "confidence": inspection.get("confidence"),
        "missing": inspection.get("missing"),
        "unclear": inspection.get("unclear"),
        "present": inspection.get("present"),
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
                    "You verify LEGO kit completeness from a parsed caption. "
                    "Reply with ONLY JSON: "
                    '{"p_fail_prior": float 0-1, "proposed": "PASS"|"FAIL"|"HOLD", '
                    '"rationale": string ≤140 chars}. '
                    "p_fail_prior is P(kit is incomplete). "
                    "If missing parts are named, p_fail_prior ≥ 0.8. "
                    "If complete=YES and confidence=high, p_fail_prior ≤ 0.15. "
                    "If unclear, around 0.5."
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
