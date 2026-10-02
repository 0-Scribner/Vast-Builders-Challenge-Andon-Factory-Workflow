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
        self.assertNotIn("review('COMPLETE')", html)
        self.assertNotIn("Incomplete", html)
