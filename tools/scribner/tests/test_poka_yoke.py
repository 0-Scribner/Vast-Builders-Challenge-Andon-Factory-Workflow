"""Poka-yoke API tests. False PASS is the red line."""

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


class ApiPokaYokeTests(unittest.TestCase):
    def test_health_pins_builders_stack(self) -> None:
        body = main.health()
        self.assertTrue(body["ok"])
        self.assertEqual(body["stack"]["source"], SOURCE_URL)
        self.assertFalse(body["stack"]["canary_wired"])
        self.assertFalse(body["gpu"]["canary"])

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
                    verdict="COMPLETE",
                    reason="agree",
                    gate_ok=True,
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)
