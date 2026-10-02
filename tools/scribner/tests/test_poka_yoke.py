"""Poka-yoke API tests. False CLEAR is the red line."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["SCRIBNER_MOCK"] = "1"
os.environ["SCRIBNER_DATA_DIR"] = tempfile.mkdtemp(prefix="scribner-poka-")

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from builders_stack import SOURCE_URL  # noqa: E402
from kits import PAYOFF_QUERY, PRODUCT, STACK_LINE  # noqa: E402


class ApiPokaYokeTests(unittest.TestCase):
    def setUp(self) -> None:
        if not main.state.store.load_units():
            main.state.scan()
            main.state.run_gate()

    def test_health_pins_builders_stack(self) -> None:
        body = main.health()
        self.assertTrue(body["ok"])
        self.assertEqual(body["stack"]["source"], SOURCE_URL)
        self.assertFalse(body["stack"]["canary_wired"])
        self.assertFalse(body["gpu"]["canary"])
        self.assertEqual(body["product"], PRODUCT)
        self.assertEqual(body["line"], "primary")
        self.assertEqual(body["payoff_query"], PAYOFF_QUERY)
        self.assertEqual(body["stack_line"], STACK_LINE)
        self.assertEqual(body["plan_b_branch"], "cursor/plan-b-lego-completeness-72e3")
        self.assertEqual(body["corpus"], "provided")
        self.assertEqual(body["andon"]["board"], "andon")
        self.assertEqual(body["andon"]["name_ja"], "安灯")
        self.assertIn(body["andon"]["line_lamp"], {"green", "yellow", "red"})
        self.assertTrue(body["andon"]["rule_en"].startswith("False CLEAR"))

    def test_gate_ok_on_hold_is_400(self) -> None:
        q = main.api_queue()["queue"]
        hold = next(
            (u for u in q if (u.get("decision_row") or {}).get("decision") == "HOLD"),
            None,
        )
        if hold is None:
            self.skipTest("no HOLD in queue")
        with self.assertRaises(HTTPException) as ctx:
            main.api_review(
                main.ReviewBody(
                    unit_id=hold["id"],
                    verdict="CLEAR",
                    reason="agree",
                    gate_ok=True,
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_ui_is_warehouse_operator(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("AUTO_CLEAR", html)
        self.assertIn("AUTO_ALERT", html)
        self.assertIn("UNSAFE", html)
        self.assertIn("review('CLEAR')", html)
        self.assertIn("person close to a moving vehicle", html)
        self.assertIn("VAST", html)
        self.assertIn("NVIDIA Cosmos", html)
        self.assertIn("False CLEAR", html)
        self.assertIn("安灯", html)
        self.assertIn("ANDON", html)
        self.assertIn("呼び出し", html)
        self.assertIn("停止", html)
        self.assertIn("正常", html)
        self.assertIn("/api/andon", html)
        self.assertIn("stationTower", html)
        self.assertIn("gemba-frame", html)
        self.assertIn("自働化", html)
        self.assertIn("ポカヨケ", html)
        self.assertIn("/api/andon?unit_id=", html)
        self.assertIn("position: sticky", html)
        self.assertNotIn("review('COMPLETE')", html)
        self.assertNotIn("Incomplete", html)

    def test_andon_api_maps_queue_to_lamps(self) -> None:
        body = main.api_andon()
        self.assertEqual(body["board"], "andon")
        self.assertEqual(body["gemba"], "現場")
        self.assertEqual(body["camera_id"], "sdg_warehouse_cam-2")
        self.assertEqual(body["location"], "warehouse3")
        self.assertEqual(body["payoff_query"], PAYOFF_QUERY)
        self.assertGreaterEqual(body["counts"]["n"], 30)
        self.assertGreater(body["counts"]["red"], 0)
        self.assertGreater(body["counts"]["yellow"], 0)
        self.assertEqual(
            body["counts"]["green"] + body["counts"]["yellow"] + body["counts"]["red"],
            body["counts"]["n"],
        )

    def test_andon_station_follows_alert_unit(self) -> None:
        rows = main.api_units()["units"]
        alert = next(
            (u for u in rows if (u.get("decision") or {}).get("decision") == "AUTO_ALERT"),
            None,
        )
        self.assertIsNotNone(alert)
        body = main.api_andon(unit_id=alert["id"])
        self.assertEqual(body["station_lamp"], "red")
        self.assertEqual(body["station_ja_lamp"], "停止")
        self.assertEqual(body["unit_id"], alert["id"])

    def test_report_names_andon_and_gemba(self) -> None:
        text = main.api_report().body.decode("utf-8")
        self.assertIn("安灯", text)
        self.assertIn("現場", text)
        self.assertIn("sdg_warehouse_cam-2", text)
        board = main.api_andon()
        self.assertIn(board["line_ja"], text)
        self.assertIn(f"**{board['line_ja']}**", text)


def _rgb_mean(mp4: Path):
    import subprocess

    raw = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(mp4),
            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
        ],
        check=True,
        capture_output=True,
    ).stdout
    n = max(len(raw) // 3, 1)
    r = sum(raw[i] for i in range(0, len(raw), 3)) / n
    g = sum(raw[i] for i in range(1, len(raw), 3)) / n
    b = sum(raw[i] for i in range(2, len(raw), 3)) / n
    return r, g, b


class HttpAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not main.state.store.load_units():
            main.state.scan()
            main.state.run_gate()
        cls.client = TestClient(main.app)

    def test_http_health_pins_stack_andon_no_canary(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        blob = r.text
        self.assertIn("vast-builders-challenge", blob)
        self.assertIn("warehouse-near-miss", blob)
        self.assertIn("andon", blob)
        self.assertFalse(body["stack"]["canary_wired"])
        self.assertNotIn("166.19.38.112", blob)
        self.assertIn("/api/v1/reports", body["stack"]["forbidden_vss_paths"])
        from builders_stack import scan_scribner_violations

        self.assertEqual(scan_scribner_violations(), [])

    def test_http_gate_ok_on_hold_is_400(self) -> None:
        q = self.client.get("/api/queue").json()["queue"]
        hold = next(
            (u for u in q if (u.get("decision_row") or {}).get("decision") == "HOLD"),
            None,
        )
        if hold is None:
            self.skipTest("no HOLD in queue")
        r = self.client.post(
            "/api/review",
            json={
                "unit_id": hold["id"],
                "verdict": "CLEAR",
                "reason": "agree",
                "gate_ok": True,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_http_auto_alert_clear_without_confirm_is_400(self) -> None:
        rows = self.client.get("/api/units").json()["units"]
        alert = next(
            (u for u in rows if (u.get("decision") or {}).get("decision") == "AUTO_ALERT"),
            None,
        )
        if alert is None:
            self.skipTest("no AUTO_ALERT")
        r = self.client.post(
            "/api/review",
            json={
                "unit_id": alert["id"],
                "verdict": "CLEAR",
                "reason": "vlm_false_alert",
                "confirm_escape": False,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_http_override_reason_agree_is_400(self) -> None:
        rows = self.client.get("/api/units").json()["units"]
        alert = next(
            (u for u in rows if (u.get("decision") or {}).get("decision") == "AUTO_ALERT"),
            None,
        )
        if alert is None:
            self.skipTest("no AUTO_ALERT")
        r = self.client.post(
            "/api/review",
            json={"unit_id": alert["id"], "verdict": "CLEAR", "reason": "agree"},
        )
        self.assertEqual(r.status_code, 400)

    def test_http_andon_pack_c_and_alert_station_red(self) -> None:
        board = self.client.get("/api/andon").json()
        self.assertEqual(board["board"], "andon")
        self.assertEqual(board["camera_id"], "sdg_warehouse_cam-2")
        self.assertEqual(board["rule"], "赤灯は人なしで緑にしない")
        rows = self.client.get("/api/units").json()["units"]
        alert = next(
            u for u in rows if (u.get("decision") or {}).get("decision") == "AUTO_ALERT"
        )
        station = self.client.get("/api/andon", params={"unit_id": alert["id"]}).json()
        self.assertEqual(station["station_lamp"], "red")
        from andon import line_lamp, snapshot

        self.assertEqual(line_lamp([]), "green")
        mixed = snapshot(
            decisions=[{"decision": "HOLD"}, {"decision": "AUTO_ALERT"}],
            queue=[
                {"decision_row": {"decision": "HOLD"}},
                {"decision_row": {"decision": "AUTO_ALERT"}},
            ],
        )
        self.assertEqual(mixed["line_lamp"], "red")

    def test_http_clip_alert_is_andon_tinted_mp4_not_grey(self) -> None:
        Path("/tmp/scribner_andon_red.mp4").unlink(missing_ok=True)
        rows = self.client.get("/api/units").json()["units"]
        alert = next(
            u for u in rows if (u.get("decision") or {}).get("decision") == "AUTO_ALERT"
        )
        r = self.client.get("/clip", params={"unit_id": alert["id"]})
        self.assertEqual(r.status_code, 200)
        self.assertIn("video/mp4", r.headers.get("content-type", ""))
        self.assertGreater(len(r.content), 1000)
        tmp = Path(tempfile.mkstemp(suffix=".mp4")[1])
        tmp.write_bytes(r.content)
        red, green, blue = _rgb_mean(tmp)
        tmp.unlink(missing_ok=True)
        # Packed red aisle: R leads. A grey rectangle is R≈G≈B.
        self.assertGreater(red, green + 4)
        self.assertGreater(red, blue + 4)
        self.assertGreater(max(abs(red - green), abs(green - blue), abs(red - blue)), 8)

    def test_http_report_line_matches_andon(self) -> None:
        board = self.client.get("/api/andon").json()
        text = self.client.get("/api/report").text
        self.assertIn(board["line_ja"], text)
        self.assertIn("sdg_warehouse_cam-2", text)
        self.assertIn("安灯", text)

    def test_clip_source_falls_back_to_unit(self) -> None:
        rows = main.api_units()["units"]
        u = rows[0]
        full = main.state.unit(u["id"])
        self.assertTrue(full and full.get("source"))
        self.assertEqual(main.clip_source("", u["id"]), full["source"])
        self.assertEqual(main.clip_source("explicit-src", u["id"]), "explicit-src")
        self.assertEqual(main.clip_source("", ""), "")
