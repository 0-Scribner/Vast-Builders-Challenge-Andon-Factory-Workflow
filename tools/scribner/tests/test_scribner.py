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

from andon import ensure_warehouse_clip, lamp_for_decision, line_lamp, snapshot  # noqa: E402
from corpus import READY_CAMERA_IDS, public_corpus  # noqa: E402
from gate import decide_one, pass_blocked  # noqa: E402
from inspection import heuristic_prior, parse_caption  # noqa: E402
from kits import CUSTOM_PROMPT_MAX, kit_for_camera, kit_ids, prompt_for_kit  # noqa: E402
from learn import derive_thresholds, fit_logistic, predict_p_fail  # noqa: E402
from mock_data import build_mock_units  # noqa: E402
from state import AppState  # noqa: E402
from store import Store  # noqa: E402


class PromptLimitTests(unittest.TestCase):
    def test_prompts_fit_vss(self) -> None:
        for kid in kit_ids():
            p = prompt_for_kit(kid)
            self.assertLessEqual(len(p), CUSTOM_PROMPT_MAX, kid)
            self.assertIn("PATH_CLEAR:", p)
            self.assertIn("NEAR_MISS:", p)
            self.assertIn("PERSON:", p)
            self.assertIn("VEHICLE:", p)
        self.assertEqual(set(kit_ids()), {"warehouse-aisle", "person-near-vehicle"})
        self.assertIn("sdg_warehouse", prompt_for_kit("warehouse-aisle"))
        self.assertIn("person close to a moving vehicle", prompt_for_kit("warehouse-aisle"))
        self.assertEqual(kit_for_camera("sdg_warehouse_cam-2"), "warehouse-aisle")
        self.assertEqual(kit_for_camera("i24_cam-1"), "person-near-vehicle")
        self.assertEqual(kit_for_camera("pie_cam-3"), "person-near-vehicle")
        self.assertEqual(kit_for_camera("neighborhood_cam-1"), "person-near-vehicle")
        self.assertEqual(kit_for_camera("kit-station-1"), "person-near-vehicle")
        self.assertNotIn("race-car", kit_ids())

    def test_official_corpus_cameras(self) -> None:
        body = public_corpus()
        ids = {c["camera_id"] for c in body["cameras"]}
        self.assertEqual(ids, set(READY_CAMERA_IDS) | {"sf_streets_cam-1"})
        for required in ("i24_cam-1", "pie_cam-3", "neighborhood_cam-1", "sdg_warehouse_cam-2"):
            self.assertIn(required, ids)
        units = build_mock_units()
        cams = {u["camera_id"] for u in units}
        for required in ("i24_cam-1", "pie_cam-3", "neighborhood_cam-1", "sdg_warehouse_cam-2", "smartspace_cam-1"):
            self.assertIn(required, cams)
        self.assertGreaterEqual(len(units), 40)


class ParserTests(unittest.TestCase):
    def test_clear_empty_aisle(self) -> None:
        cap = (
            "PERSON: NO. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
            "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: NONE. "
            "CONFIDENCE: HIGH. The aisle is empty."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        self.assertTrue(rec["complete"])
        self.assertTrue(rec["path_clear"])
        self.assertFalse(rec["near_miss"])
        self.assertEqual(rec["confidence"], "high")
        self.assertEqual(rec["hazards"], [])
        prior = heuristic_prior(rec)
        self.assertLess(prior["p_fail_prior"], 0.2)

    def test_near_miss_forklift(self) -> None:
        cap = (
            "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: CLOSE. "
            "PATH_CLEAR: NO. NEAR_MISS: YES. HAZARD: forklift-near-person. "
            "UNCLEAR: NONE. CONFIDENCE: HIGH. A forklift is moving close to a person."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        self.assertFalse(rec["complete"])
        self.assertTrue(rec["near_miss"])
        self.assertIn("forklift-near-person", rec["part_ids_missing"])
        prior = heuristic_prior(rec)
        self.assertGreater(prior["p_fail_prior"], 0.8)

    def test_unclear_holds(self) -> None:
        cap = (
            "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: UNCLEAR. "
            "PATH_CLEAR: YES. NEAR_MISS: NO. HAZARD: NONE. UNCLEAR: DISTANCE. "
            "CONFIDENCE: LOW. Distance cannot be verified."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        prior = heuristic_prior(rec)
        self.assertGreaterEqual(prior["p_fail_prior"], 0.4)
        self.assertLessEqual(prior["p_fail_prior"], 0.6)

    def test_inconsistent_path_clear_and_near_miss(self) -> None:
        cap = (
            "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: CLOSE. "
            "PATH_CLEAR: YES. NEAR_MISS: YES. HAZARD: NONE. UNCLEAR: NONE. "
            "CONFIDENCE: HIGH. Conflicting fields."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        self.assertTrue(rec["inconsistent"])
        self.assertFalse(rec["complete"])
        self.assertGreater(heuristic_prior(rec)["p_fail_prior"], 0.8)

    def test_pallet_blocks_path(self) -> None:
        cap = (
            "PERSON: NO. VEHICLE: NONE. MOTION: NONE. DISTANCE: NONE. "
            "PATH_CLEAR: NO. NEAR_MISS: NO. HAZARD: pallet-in-walkway. "
            "UNCLEAR: NONE. CONFIDENCE: HIGH. A pallet sits in the walkway."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        self.assertFalse(rec["complete"])
        self.assertIn("pallet-in-walkway", rec["part_ids_missing"])
        self.assertGreater(heuristic_prior(rec)["p_fail_prior"], 0.8)


class GateFailClosedTests(unittest.TestCase):
    def test_yolo_both_without_high_clear_never_auto_clear(self) -> None:
        rec = {
            "complete": None,
            "confidence": "medium",
            "path_clear": None,
            "near_miss": None,
            "missing": [],
            "hazards": [],
            "unclear": [],
            "inconsistent": False,
            "person": True,
            "vehicle_present": True,
        }
        unit = {
            "id": "yolo-only",
            "kit_id": "warehouse-aisle",
            "inspection": rec,
            "prior": {"p_fail_prior": 0.01},
            "yolo_person": True,
            "yolo_vehicle": True,
        }
        self.assertTrue(pass_blocked(unit))
        d = decide_one(unit, None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertNotEqual(d["decision"], "AUTO_CLEAR")
        self.assertNotEqual(d["decision"], "AUTO_PASS")

    def test_inconsistent_never_auto_clear(self) -> None:
        cap = (
            "PERSON: YES. VEHICLE: forklift. MOTION: MOVING. DISTANCE: CLOSE. "
            "PATH_CLEAR: YES. NEAR_MISS: YES. HAZARD: NONE. UNCLEAR: NONE. "
            "CONFIDENCE: HIGH."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        unit = {
            "id": "inc",
            "kit_id": "warehouse-aisle",
            "inspection": rec,
            "prior": {"p_fail_prior": 0.01},
        }
        d = decide_one(unit, None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertNotEqual(d["decision"], "AUTO_CLEAR")
        self.assertEqual(d["decision"], "AUTO_ALERT")


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
                    "verdict": "UNSAFE" if u["true_unsafe"] else "CLEAR",
                    "overrode": False,
                }
            )
        scorer = fit_logistic(units, labels)
        missing = next(u for u in units if u["variant"] == "forklift-near-person")
        complete = next(u for u in units if u["variant"] == "empty-aisle")
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
        decisions = {d["unit_id"]: d for d in self.state.store.load_decisions()}
        for u in self.state.store.load_units():
            verdict = "UNSAFE" if u["true_unsafe"] else "CLEAR"
            auto = (decisions.get(u["id"]) or {}).get("decision") or "HOLD"
            kwargs: dict = {}
            reason = "agree"
            if auto in {"AUTO_CLEAR", "AUTO_PASS"} and verdict == "UNSAFE":
                reason = "vlm_missed_near_miss"
            elif auto in {"AUTO_ALERT", "AUTO_FAIL"} and verdict == "CLEAR":
                reason = "vlm_false_alert"
                kwargs["confirm_escape"] = True
            self.state.review(u["id"], verdict, reason=reason, **kwargs)
        result = self.state.retrain()
        warm = result["metrics"]["coverage"]
        self.assertGreaterEqual(warm, cold)
        units = {u["id"]: u for u in self.state.store.load_units()}
        decisions = {d["unit_id"]: d for d in self.state.store.load_decisions()}
        mw = next(u for u in units.values() if u["variant"] == "forklift-near-person")
        self.assertGreaterEqual(decisions[mw["id"]]["p_fail"], 0.55)
        self.assertIn(decisions[mw["id"]]["decision"], {"AUTO_ALERT", "AUTO_FAIL", "HOLD"})
        complete = next(u for u in units.values() if u["variant"] == "empty-aisle")
        self.assertLessEqual(decisions[complete["id"]]["p_fail"], 0.45)
        hidden = [u for u in units.values() if u["variant"] == "unclear-distance"]
        hidden_dec = [decisions[u["id"]]["decision"] for u in hidden]
        self.assertTrue(any(d not in {"AUTO_CLEAR", "AUTO_PASS"} for d in hidden_dec))

    def test_accept_object_aliases(self) -> None:
        self.state.scan()
        self.state.run_gate()
        hold = next(d for d in self.state.store.load_decisions() if d["decision"] == "HOLD")
        self.state.review(hold["unit_id"], "O", reason="agree")
        lab = next(x for x in self.state.store.load_labels() if x["unit_id"] == hold["unit_id"])
        self.assertEqual(lab["verdict"], "UNSAFE")


class AndonTests(unittest.TestCase):
    def test_alert_is_red_hold_is_yellow_clear_is_green(self) -> None:
        self.assertEqual(lamp_for_decision("AUTO_ALERT"), "red")
        self.assertEqual(lamp_for_decision("AUTO_FAIL"), "red")
        self.assertEqual(lamp_for_decision("UNSAFE"), "red")
        self.assertEqual(lamp_for_decision("HOLD"), "yellow")
        self.assertEqual(lamp_for_decision(""), "yellow")
        self.assertEqual(lamp_for_decision("AUTO_CLEAR"), "green")
        self.assertEqual(lamp_for_decision("CLEAR"), "green")

    def test_line_lamp_red_beats_yellow(self) -> None:
        q = [
            {"decision_row": {"decision": "HOLD"}},
            {"decision_row": {"decision": "AUTO_ALERT"}},
        ]
        self.assertEqual(line_lamp(q), "red")
        self.assertEqual(line_lamp([{"decision_row": {"decision": "HOLD"}}]), "yellow")
        self.assertEqual(line_lamp([]), "green")

    def test_snapshot_pins_pack_c_gemba(self) -> None:
        board = snapshot(
            decisions=[
                {"decision": "AUTO_CLEAR"},
                {"decision": "HOLD"},
                {"decision": "AUTO_ALERT"},
            ],
            queue=[{"id": "wh-021", "kit_id": "warehouse-aisle", "decision_row": {"decision": "AUTO_ALERT"}}],
            current={"id": "wh-021", "kit_id": "warehouse-aisle", "decision_row": {"decision": "AUTO_ALERT"}},
        )
        self.assertEqual(board["board"], "andon")
        self.assertEqual(board["name_ja"], "安灯")
        self.assertEqual(board["gemba"], "現場")
        self.assertEqual(board["jidoka"], "自働化")
        self.assertEqual(board["camera_id"], "sdg_warehouse_cam-2")
        self.assertEqual(board["station_ja"], "倉庫通路")
        self.assertEqual(board["line_lamp"], "red")
        self.assertEqual(board["station_lamp"], "red")
        self.assertEqual(board["rule"], "赤灯は人なしで緑にしない")
        self.assertEqual(board["counts"]["n"], 3)

    def test_warehouse_clip_is_real_mp4(self) -> None:
        path = ensure_warehouse_clip("red")
        self.assertGreater(path.stat().st_size, 1000)
        self.assertTrue(path.name.endswith("red.mp4"))

    def test_warehouse_clips_are_andon_tinted_not_grey(self) -> None:
        import subprocess

        for lamp in ("green", "yellow", "red"):
            p = Path(f"/tmp/scribner_andon_{lamp}.mp4")
            p.unlink(missing_ok=True)
            path = ensure_warehouse_clip(lamp)
            self.assertGreater(path.stat().st_size, 1000)
            raw = subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-i", str(path),
                    "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
                ],
                check=True,
                capture_output=True,
            ).stdout
            n = max(len(raw) // 3, 1)
            r = sum(raw[i] for i in range(0, len(raw), 3)) / n
            g = sum(raw[i] for i in range(1, len(raw), 3)) / n
            b = sum(raw[i] for i in range(2, len(raw), 3)) / n
            spread = max(abs(r - g), abs(g - b), abs(r - b))
            self.assertGreater(spread, 8, msg=f"{lamp} looks grey r={r:.1f} g={g:.1f} b={b:.1f}")
            if lamp == "green":
                self.assertGreater(g, r)
            elif lamp == "red":
                self.assertGreater(r, g)
            else:
                self.assertGreater(r + g, 2 * b)


if __name__ == "__main__":
    unittest.main()
