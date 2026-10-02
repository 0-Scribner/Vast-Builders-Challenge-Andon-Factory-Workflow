"""Orchestrate scan to score to review to retrain.

Agent note: ``AppState`` is the object ``main.py`` talks to. Keep HTTP
handlers thin; put loop logic here so tests can drive it without Starlette.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import config
from andon import counts as andon_counts, line_lamp
from gate import apply_label_override, decide_all, metrics_bundle, review_queue
from learn import derive_thresholds, fit_logistic
from scan import scan_live, scan_mock
from store import Store
from tracking import log_retrain


class AppState:
    def __init__(self, store: Optional[Store] = None, mock: Optional[bool] = None) -> None:
        self.store = store or Store()
        self.mock = config.MOCK if mock is None else mock
        if not self.store.load_scorer():
            self.store.save_scorer(fit_logistic([], []))

    def scan(self) -> Dict[str, Any]:
        units = scan_mock() if self.mock else scan_live()
        self.store.save_units(units)
        return {"n_units": len(units), "mock": self.mock}

    def run_gate(self) -> Dict[str, Any]:
        units = self.store.load_units()
        if not units:
            self.scan()
            units = self.store.load_units()
        scorer = self.store.load_scorer()
        thresholds = self.store.load_thresholds()
        decisions = decide_all(
            units, scorer, thresholds, audit_fraction=config.AUDIT_FRACTION
        )
        self.store.save_decisions(decisions)
        stats = metrics_bundle(decisions, self.store.load_labels(), thresholds)
        return {"n_units": len(units), "metrics": stats}

    def queue(self) -> List[Dict[str, Any]]:
        return review_queue(
            self.store.load_units(),
            self.store.load_decisions(),
            self.store.load_labels(),
        )

    def review(
        self,
        unit_id: str,
        verdict: str,
        reason: str = "agree",
        notes: str = "",
        *,
        gate_ok: Optional[bool] = None,
        confirm_escape: bool = False,
    ) -> Dict[str, Any]:
        verdict = verdict.upper().strip()
        if verdict in {"PASS", "COMPLETE", "C", "YES", "CLEAR", "A", "ACCEPT"}:
            verdict = "CLEAR"
        elif verdict in {"FAIL", "INCOMPLETE", "I", "NO", "UNSAFE", "U", "O", "OBJECT", "ALERT"}:
            verdict = "UNSAFE"
        else:
            raise ValueError("verdict must be CLEAR or UNSAFE")
        decisions = {d.get("unit_id"): d for d in self.store.load_decisions()}
        drow = decisions.get(unit_id) or {}
        auto = drow.get("decision") or "HOLD"
        if gate_ok is True and auto == "HOLD":
            raise ValueError("cannot mark gate_ok on HOLD; pick CLEAR or UNSAFE")
        if gate_ok is True:
            if auto in {"AUTO_CLEAR", "AUTO_PASS"}:
                verdict = "CLEAR"
            elif auto in {"AUTO_ALERT", "AUTO_FAIL"}:
                verdict = "UNSAFE"
            else:
                raise ValueError("cannot mark gate_ok on HOLD; pick CLEAR or UNSAFE")
        overrode = apply_label_override(drow, verdict)
        if overrode and (reason or "").strip() in {"", "agree"}:
            raise ValueError("override requires a non-agree reason")
        if auto in {"AUTO_FAIL", "AUTO_ALERT"} and verdict == "CLEAR" and not confirm_escape:
            raise ValueError("AUTO_ALERT to CLEAR requires confirm_escape=true")
        label = {
            "unit_id": unit_id,
            "verdict": verdict,
            "reason": reason,
            "notes": notes,
            "overrode": overrode,
            "p_fail_at_review": drow.get("p_fail"),
            "decision_at_review": auto,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self.store.replace_label_for_unit(unit_id, label)
        n = len(self.store.load_labels())
        auto = None
        if n >= 8 and n % config.RETRAIN_EVERY == 0:
            auto = self.retrain()
        return {"label": label, "n_labels": n, "auto_retrain": auto}

    def retrain(self) -> Dict[str, Any]:
        units = self.store.load_units()
        labels = self.store.load_labels()
        scorer = fit_logistic(units, labels)
        self.store.save_scorer(scorer)
        prev = self.store.load_thresholds()
        thresholds = derive_thresholds(
            units,
            labels,
            scorer,
            epsilon=config.EPSILON_ESCAPE,
            delta=config.DELTA_FALSE_REJECT,
            prev=prev,
        )
        self.store.save_thresholds(thresholds)
        decisions = decide_all(units, scorer, thresholds, audit_fraction=config.AUDIT_FRACTION)
        self.store.save_decisions(decisions)
        stats = metrics_bundle(decisions, labels, thresholds)
        q = review_queue(units, decisions, labels)
        tally = andon_counts(decisions)
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "scorer_n": scorer.get("n"),
            "andon_green": float(tally["green"]),
            "andon_yellow": float(tally["yellow"]),
            "andon_red": float(tally["red"]),
            "andon_line": line_lamp(q),
            **stats,
        }
        tracking = log_retrain(row, scorer, labels)
        row["wandb_logged"] = 1.0 if tracking.get("status") == "ok" else 0.0
        self.store.append_metrics(row)
        return {
            "metrics": stats,
            "thresholds": thresholds,
            "scorer_n": scorer.get("n"),
            "wandb_tracking": tracking,
        }

    def metrics(self) -> Dict[str, Any]:
        return {
            "current": metrics_bundle(
                self.store.load_decisions(),
                self.store.load_labels(),
                self.store.load_thresholds(),
            ),
            "history": self.store.load_metrics_log(),
            "store": self.store.state_summary(),
        }

    def unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        for u in self.store.load_units():
            if u.get("id") == unit_id:
                drow = next(
                    (d for d in self.store.load_decisions() if d.get("unit_id") == unit_id),
                    None,
                )
                lab = next(
                    (x for x in self.store.load_labels() if x.get("unit_id") == unit_id),
                    None,
                )
                return {**u, "decision_row": drow, "label": lab}
        return None
