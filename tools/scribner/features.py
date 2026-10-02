"""Feature vector for the warehouse near-miss scorer.

Index 1 is always prior_logit. w0[1] = 1 so cold start equals the prior.
FEATURE_VERSION 3 discards completeness-era scorers.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np

FEATURE_VERSION = 3

FEATURE_NAMES: List[str] = [
    "bias",
    "prior_logit",
    "complete_yes",
    "complete_no",
    "complete_unknown",
    "hazard_count",
    "unclear_count",
    "conf_high",
    "conf_med",
    "conf_low",
    "view_blocked",
    "path_clear_yes",
    "near_miss_yes",
    "yolo_person",
    "yolo_vehicle",
    "person_yes",
    "vehicle_yes",
    "distance_close",
    "motion_moving",
    "kit_warehouse_aisle",
    "kit_person_near_vehicle",
    "hz_forklift_near_person",
    "hz_pallet_walkway",
    "hz_blocked_path",
]

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
    w = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    w[1] = 1.0
    return w


def vectorize(unit: Dict[str, Any]) -> np.ndarray:
    insp = unit.get("inspection") or {}
    prior = unit.get("prior") or {}
    p = float(prior.get("p_fail_prior", 0.5))
    hz = set(insp.get("part_ids_missing") or insp.get("hazards") or [])
    kit_id = unit.get("kit_id") or insp.get("kit_id") or ""
    complete = insp.get("complete")
    conf = insp.get("confidence")
    x = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    x[0] = 1.0
    x[1] = logit(p)
    x[2] = 1.0 if complete is True else 0.0
    x[3] = 1.0 if complete is False else 0.0
    x[4] = 1.0 if complete is None else 0.0
    x[5] = min(len(insp.get("hazards") or insp.get("missing") or []) / 4.0, 1.5)
    x[6] = min(len(insp.get("unclear") or []) / 3.0, 1.5)
    x[7] = 1.0 if conf == "high" else 0.0
    x[8] = 1.0 if conf == "medium" else 0.0
    x[9] = 1.0 if conf == "low" else 0.0
    x[10] = 1.0 if (unit.get("occlusion") or unit.get("view_blocked")) else 0.0
    x[11] = 1.0 if insp.get("path_clear") is True else 0.0
    x[12] = 1.0 if insp.get("near_miss") is True else 0.0
    x[13] = 1.0 if unit.get("yolo_person") else 0.0
    x[14] = 1.0 if unit.get("yolo_vehicle") else 0.0
    x[15] = 1.0 if insp.get("person") is True else 0.0
    x[16] = 1.0 if insp.get("vehicle_present") is True else 0.0
    x[17] = 1.0 if insp.get("distance") == "close" else 0.0
    x[18] = 1.0 if insp.get("motion") == "moving" else 0.0
    x[19] = 1.0 if kit_id == "warehouse-aisle" else 0.0
    x[20] = 1.0 if kit_id == "person-near-vehicle" else 0.0
    x[21] = 1.0 if "forklift-near-person" in hz else 0.0
    x[22] = 1.0 if "pallet-in-walkway" in hz else 0.0
    x[23] = 1.0 if "blocked-path" in hz else 0.0
    return x
