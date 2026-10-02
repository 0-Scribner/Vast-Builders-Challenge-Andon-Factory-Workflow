"""Feature vector for the kit-completeness scorer.

Agent note
----------
``FEATURE_NAMES`` is the contract with ``learn.py``. If you add a feature:

1. Append it here (never insert in the middle — stored ``w`` vectors
   would silently misalign).
2. Set the matching slot in ``prior_anchor()``.
3. Bump ``FEATURE_VERSION`` so old scorers are discarded.

Index 1 is **always** ``prior_logit``. ``w0[1] = 1`` is how cold start
equals the VLM/heuristic prior.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np

FEATURE_VERSION = 1

FEATURE_NAMES: List[str] = [
    "bias",
    "prior_logit",
    "complete_yes",
    "complete_no",
    "complete_unknown",
    "missing_count",
    "unclear_count",
    "conf_high",
    "conf_med",
    "conf_low",
    "occlusion",
    "kit_race_car",
    "kit_front_loader",
    "miss_wheels",
    "miss_roof",
    "miss_minifig",
    "miss_windshield",
    "miss_bucket",
]

# Clip logits so sigmoid/exp is stable.
_LOGIT_CLIP = 8.0


def logit(p: float) -> float:
    p = min(max(float(p), 1e-4), 1.0 - 1e-4)
    return math.log(p / (1.0 - p))


def sigmoid(z: float) -> float:
    z = min(max(float(z), -_LOGIT_CLIP), _LOGIT_CLIP)
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def prior_anchor() -> np.ndarray:
    """w0: identity on prior_logit, zeros elsewhere. Cold start = the prior."""
    w = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    w[1] = 1.0
    return w


def vectorize(unit: Dict[str, Any]) -> np.ndarray:
    """Turn a unit dict (inspection + prior + detections) into x."""
    insp = unit.get("inspection") or {}
    prior = unit.get("prior") or {}
    p = float(prior.get("p_fail_prior", 0.5))
    missing_ids = set(insp.get("part_ids_missing") or [])
    kit_id = unit.get("kit_id") or insp.get("kit_id") or ""
    complete = insp.get("complete")
    conf = insp.get("confidence")
    x = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    x[0] = 1.0
    x[1] = logit(p)
    x[2] = 1.0 if complete is True else 0.0
    x[3] = 1.0 if complete is False else 0.0
    x[4] = 1.0 if complete is None else 0.0
    x[5] = min(len(insp.get("missing") or []) / 5.0, 1.5)
    x[6] = min(len(insp.get("unclear") or []) / 3.0, 1.5)
    x[7] = 1.0 if conf == "high" else 0.0
    x[8] = 1.0 if conf == "medium" else 0.0
    x[9] = 1.0 if conf == "low" else 0.0
    x[10] = 1.0 if unit.get("occlusion") else 0.0
    x[11] = 1.0 if kit_id == "race-car" else 0.0
    x[12] = 1.0 if kit_id == "front-loader" else 0.0
    x[13] = 1.0 if "wheels" in missing_ids else 0.0
    x[14] = 1.0 if "roof" in missing_ids else 0.0
    x[15] = 1.0 if "minifig" in missing_ids else 0.0
    x[16] = 1.0 if "windshield" in missing_ids else 0.0
    x[17] = 1.0 if "bucket" in missing_ids else 0.0
    return x
