"""Parser + scorer + HITL coverage tests.

Run from repo root:
    PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["SCRIBNER_MOCK"] = "1"
os.environ.setdefault("SCRIBNER_DATA_DIR", tempfile.mkdtemp(prefix="scribner-test-"))

from inspection import heuristic_prior, parse_caption  # noqa: E402
from kits import CUSTOM_PROMPT_MAX, kit_ids, prompt_for_kit  # noqa: E402
from learn import derive_thresholds, fit_logistic, predict_p_fail  # noqa: E402
from mock_data import build_mock_units  # noqa: E402
from state import AppState  # noqa: E402
from store import Store  # noqa: E402


class PromptLimitTests(unittest.TestCase):
    def test_prompts_fit_vss(self) -> None:
        for kid in kit_ids():
            p = prompt_for_kit(kid)
            self.assertLessEqual(len(p), CUSTOM_PROMPT_MAX, kid)
            self.assertIn("PRESENT:", p)
            self.assertIn("MISSING:", p)
            self.assertIn("COMPLETE:", p)


class ParserTests(unittest.TestCase):
    def test_complete_race_car(self) -> None:
        cap = (
            "PRESENT: 4 black wheels, 1 clear windshield, 1 red roof, "
            "2 yellow headlights, 1 minifigure with a hat, 1 blue door. "
            "MISSING: NONE. UNCLEAR: NONE. COMPLETE: YES. CONFIDENCE: HIGH. "
            "The car is fully assembled."
        )
        rec = parse_caption(cap, kit_id="race-car")
        self.assertTrue(rec["complete"])
        self.assertEqual(rec["confidence"], "high")
        self.assertEqual(rec["missing"], [])
        self.assertIn("wheels", rec["part_ids_present"])
        prior = heuristic_prior(rec)
        self.assertLess(prior["p_fail_prior"], 0.2)

    def test_missing_wheels(self) -> None:
        cap = (
            "PRESENT: 1 clear windshield, 1 red roof. "
            "MISSING: 4 black wheels. UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH. "
            "Chassis on paper, no wheels."
        )
        rec = parse_caption(cap, kit_id="race-car")
        self.assertFalse(rec["complete"])
        self.assertIn("wheels", rec["part_ids_missing"])
        prior = heuristic_prior(rec)
        self.assertGreater(prior["p_fail_prior"], 0.8)

    def test_unclear_holds(self) -> None:
        cap = (
            "PRESENT: 4 black wheels. MISSING: NONE. UNCLEAR: 1 blue door. "
            "COMPLETE: YES. CONFIDENCE: LOW. Far side not visible."
        )
        rec = parse_caption(cap, kit_id="race-car")
        prior = heuristic_prior(rec)
        self.assertGreaterEqual(prior["p_fail_prior"], 0.4)
        self.assertLessEqual(prior["p_fail_prior"], 0.6)


class LearningTests(unittest.TestCase):
    def test_cold_start_equals_prior(self) -> None:
        units = build_mock_units()
        scorer = fit_logistic(units, [])
        for u in units[:5]:
            p = predict_p_fail(u, scorer)
            self.assertAlmostEqual(p, u["prior"]["p_fail_prior"], places=2)

    def test_labels_move_weights_and_narrow_band(self) -> None:
        units = build_mock_units()
        labels = []
        for u in units:
            labels.append(
                {
                    "unit_id": u["id"],
                    "verdict": "INCOMPLETE" if u["true_incomplete"] else "COMPLETE",
                    "overrode": False,
                }
            )
        scorer = fit_logistic(units, labels)
        # Salient incomplete should score high after fit.
        missing = next(u for u in units if u["variant"] == "missing-wheels")
        complete = next(u for u in units if u["variant"] == "complete")
        self.assertGreater(predict_p_fail(missing, scorer), 0.6)
        self.assertLess(predict_p_fail(complete, scorer), 0.4)
        thr = derive_thresholds(
            units, labels, scorer, epsilon=0.08, delta=0.12, prev=None
        )
        self.assertLess(thr["t_pass"], thr["t_fail"])


class LoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="scribner-loop-")
        self.state = AppState(store=Store(self.tmp), mock=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_gate_review_retrain_coverage(self) -> None:
        scanned = self.state.scan()
        self.assertGreaterEqual(scanned["n_units"], 30)
        gated = self.state.run_gate()
        cold = gated["metrics"]["coverage"]
        # Review every unit with ground truth (oracle human).
        decisions = {d["unit_id"]: d for d in self.state.store.load_decisions()}
        for u in self.state.store.load_units():
            verdict = "INCOMPLETE" if u["true_incomplete"] else "COMPLETE"
            auto = (decisions.get(u["id"]) or {}).get("decision") or "HOLD"
            kwargs: dict = {}
            reason = "agree"
            if auto == "AUTO_PASS" and verdict == "INCOMPLETE":
                reason = "vlm_missed_part"
            elif auto == "AUTO_FAIL" and verdict == "COMPLETE":
                reason = "vlm_false_missing"
                kwargs["confirm_escape"] = True
            self.state.review(u["id"], verdict, reason=reason, **kwargs)
        result = self.state.retrain()
        warm = result["metrics"]["coverage"]
        self.assertGreaterEqual(warm, cold)
        # Salient missing wheels should now be AUTO_FAIL or at least high p.
        units = {u["id"]: u for u in self.state.store.load_units()}
        decisions = {d["unit_id"]: d for d in self.state.store.load_decisions()}
        mw = next(u for u in units.values() if u["variant"] == "missing-wheels")
        self.assertGreaterEqual(decisions[mw["id"]]["p_fail"], 0.55)
        self.assertIn(decisions[mw["id"]]["decision"], {"AUTO_FAIL", "HOLD"})
        complete = next(u for u in units.values() if u["variant"] == "complete")
        self.assertLessEqual(decisions[complete["id"]]["p_fail"], 0.45)
        # Subtle hidden-door should not all be auto-passed (low confidence).
        hidden = [u for u in units.values() if u["variant"] == "hidden-door"]
        hidden_dec = [decisions[u["id"]]["decision"] for u in hidden]
        self.assertTrue(any(d != "AUTO_PASS" for d in hidden_dec))


if __name__ == "__main__":
    unittest.main()
