"""Prior-anchored logistic regression + Beta-smoothed gate thresholds.

numpy only, so the module fits a ConfigMap on the slim image.

Cold start: ``w = w0`` so ``p_fail = sigmoid(prior_logit) = p_fail_prior``.
After labels: minimize log-loss + (λ/2)||w - w0||². Overrides of the
system's proposal get sample weight 2.0 so the humans move the weights.

Thresholds only **narrow** (T_pass can rise, T_fail can fall) so coverage
is monotonic in the demo. Demo-scale epsilon/delta live in ``config.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from features import FEATURE_NAMES, FEATURE_VERSION, prior_anchor, sigmoid, vectorize


def fit_logistic(
    units: Sequence[Dict[str, Any]],
    labels: Sequence[Dict[str, Any]],
    *,
    lam: float = 1.0,
    steps: int = 400,
    lr: float = 0.08,
) -> Dict[str, Any]:
    """Fit w on labeled units. y=1 means UNSAFE (near-miss / blocked path).

    Returns a serializable scorer dict. Empty labels to return the prior anchor.
    """
    w0 = prior_anchor()
    indexed = {u["id"]: u for u in units}
    rows: List[Tuple[np.ndarray, float, float]] = []
    for lab in labels:
        unit = indexed.get(lab.get("unit_id"))
        if not unit:
            continue
        y = 1.0 if lab.get("verdict") in {"INCOMPLETE", "UNSAFE"} else 0.0
        weight = 2.0 if lab.get("overrode") else 1.0
        rows.append((vectorize(unit), y, weight))
    if not rows:
        return _pack(w0, n=0, lam=lam)

    X = np.stack([r[0] for r in rows])
    y = np.array([r[1] for r in rows], dtype=np.float64)
    sw = np.array([r[2] for r in rows], dtype=np.float64)
    w = w0.copy()
    for _ in range(steps):
        z = np.clip(X @ w, -8.0, 8.0)
        p = 1.0 / (1.0 + np.exp(-z))
        grad = X.T @ (sw * (p - y)) / sw.sum() + lam * (w - w0)
        w -= lr * grad
    return _pack(w, n=len(rows), lam=lam)


def predict_p_fail(unit: Dict[str, Any], scorer: Optional[Dict[str, Any]]) -> float:
    w = _unpack(scorer)
    x = vectorize(unit)
    return float(sigmoid(float(x @ w)))


def derive_thresholds(
    units: Sequence[Dict[str, Any]],
    labels: Sequence[Dict[str, Any]],
    scorer: Dict[str, Any],
    *,
    epsilon: float,
    delta: float,
    prev: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Largest T_pass / smallest T_fail that keep Beta-smoothed error <= bounds.

    With few labels the Beta(1,1) prior keeps thresholds conservative
    (wide HOLD band). More labels let them move inward.
    """
    indexed = {u["id"]: u for u in units}
    pairs: List[Tuple[float, int]] = []
    for lab in labels:
        unit = indexed.get(lab.get("unit_id"))
        if not unit:
            continue
        p = predict_p_fail(unit, scorer)
        y = 1 if lab.get("verdict") in {"INCOMPLETE", "UNSAFE"} else 0
        pairs.append((p, y))

    # Cold start / tiny n: keep a wide band so humans see examples.
    t_pass, t_fail = 0.18, 0.82
    if len(pairs) >= 8:
        t_pass = _largest_pass_threshold(pairs, epsilon)
        t_fail = _smallest_fail_threshold(pairs, delta)
        if t_pass >= t_fail:
            mid = 0.5 * (t_pass + t_fail)
            t_pass, t_fail = mid - 0.08, mid + 0.08

    if prev:
        # Monotone narrowing: never widen the HOLD band in a demo.
        t_pass = max(float(prev.get("t_pass", t_pass)), t_pass)
        t_fail = min(float(prev.get("t_fail", t_fail)), t_fail)
        if t_pass >= t_fail:
            t_pass = float(prev.get("t_pass", 0.18))
            t_fail = float(prev.get("t_fail", 0.82))

    t_pass = float(min(max(t_pass, 0.05), 0.45))
    t_fail = float(min(max(t_fail, 0.55), 0.95))
    return {"t_pass": t_pass, "t_fail": t_fail, "n_labels": float(len(pairs))}


def coverage_stats(decisions: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    n = len(decisions) or 1
    auto_ok = {"AUTO_PASS", "AUTO_FAIL", "AUTO_CLEAR", "AUTO_ALERT"}
    auto = sum(1 for d in decisions if d.get("decision") in auto_ok)
    auto_fail = sum(1 for d in decisions if d.get("decision") in {"AUTO_FAIL", "AUTO_ALERT"})
    auto_pass = sum(1 for d in decisions if d.get("decision") in {"AUTO_PASS", "AUTO_CLEAR"})
    hold = sum(1 for d in decisions if d.get("decision") == "HOLD")
    return {
        "n": float(len(decisions)),
        "coverage": auto / n,
        "auto_pass_rate": auto_pass / n,
        "auto_fail_rate": auto_fail / n,
        "auto_clear_rate": auto_pass / n,
        "auto_alert_rate": auto_fail / n,
        "hold_rate": hold / n,
        "alarm_rate": auto_fail / n,
    }


def _largest_pass_threshold(pairs: List[Tuple[float, int]], epsilon: float) -> float:
    """max t s.t. (fails_in_pass + 1) / (n_pass + 2) <= epsilon."""
    ps = sorted({p for p, _ in pairs})
    best = 0.12
    for t in ps:
        n_pass = sum(1 for p, _ in pairs if p <= t)
        n_fail = sum(1 for p, y in pairs if p <= t and y == 1)
        est = (n_fail + 1.0) / (n_pass + 2.0)
        if n_pass >= 2 and est <= epsilon:
            best = t
    return best


def _smallest_fail_threshold(pairs: List[Tuple[float, int]], delta: float) -> float:
    ps = sorted({p for p, _ in pairs}, reverse=True)
    best = 0.88
    for t in ps:
        n_fail_band = sum(1 for p, _ in pairs if p >= t)
        n_pass = sum(1 for p, y in pairs if p >= t and y == 0)
        est = (n_pass + 1.0) / (n_fail_band + 2.0)
        if n_fail_band >= 2 and est <= delta:
            best = t
    return best


def _pack(w: np.ndarray, n: int, lam: float) -> Dict[str, Any]:
    return {
        "feature_version": FEATURE_VERSION,
        "names": list(FEATURE_NAMES),
        "w": [float(v) for v in w.tolist()],
        "n": n,
        "lam": lam,
    }


def _unpack(scorer: Optional[Dict[str, Any]]) -> np.ndarray:
    if not scorer or scorer.get("feature_version") != FEATURE_VERSION:
        return prior_anchor()
    w = np.array(scorer.get("w") or [], dtype=np.float64)
    if w.shape[0] != len(FEATURE_NAMES):
        return prior_anchor()
    return w
