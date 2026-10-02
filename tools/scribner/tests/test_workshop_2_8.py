"""Regressions for the Scribner live-readiness/manual workshop package."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve()
SCRIBNER = HERE.parents[1]
ROOT = SCRIBNER.parents[1]
if str(SCRIBNER) not in sys.path:
    sys.path.insert(0, str(SCRIBNER))
os.environ.setdefault("SCRIBNER_MOCK", "1")
os.environ.setdefault("SCRIBNER_DATA_DIR", tempfile.mkdtemp(prefix="scribner-workshop-tests-"))

import config  # noqa: E402
from gpu_client import occlusion_from_yolo  # noqa: E402
from scan import LiveScanUnavailable, scan_live  # noqa: E402
from tracking import log_retrain, status as tracking_status  # noqa: E402
from vss_client import VssClient, VssError  # noqa: E402


class WrongCameraClient:
    def explore_all(self, scope="all"):
        return [
            {"camera_id": "sdg_warehouse_cam-20", "filename": "wrong.mp4"},
            {"camera_id": "other-camera", "filename": "other.mp4"},
        ]


class SegmentClient:
    def explore_all(self, scope="all"):
        return [{
            "camera_id": "sdg_warehouse_cam-2",
            "location": "warehouse3",
            "filename": "parent.mp4",
            "original_video": "s3://chunks/parent.mp4",
            "timeline": [
                {"source": "s3://segments/1.mp4", "reasoning_content": "PATH_CLEAR: YES; NEAR_MISS: NO; UNCLEAR: NONE; CONFIDENCE: HIGH"},
                {"source": "s3://segments/2.mp4", "reasoning_content": "PATH_CLEAR: NO; NEAR_MISS: YES; UNCLEAR: NONE; CONFIDENCE: HIGH"},
            ],
        }]

    def tool_detections(self, source):
        return {"object_classes": ["person", "forklift"]}


class DuplicateSegmentClient(SegmentClient):
    def explore_all(self, scope="all"):
        rows = super().explore_all(scope)
        rows[0]["timeline"][1]["source"] = rows[0]["timeline"][0]["source"]
        return rows


class RepeatedExploreClient(VssClient):
    def __init__(self):
        pass

    def explore(self, scope="all", limit=100, offset=0):
        return {"items": [{"original_video": "same", "filename": "same.mp4"}], "total": 2}


class WorkshopPackageTests(unittest.TestCase):
    def test_pack_c_filter_fails_closed_on_zero_exact_matches(self):
        with patch.object(config, "PACK", "C"), patch.object(config, "CAMERA_FILTER", "sdg_warehouse_cam-2"):
            with self.assertRaises(LiveScanUnavailable):
                scan_live(WrongCameraClient())

    def test_live_scan_inspects_timeline_segments_with_unique_paired_sources(self):
        with patch.object(config, "PACK", "C"), patch.object(config, "CAMERA_FILTER", "sdg_warehouse_cam-2"):
            units = scan_live(SegmentClient())
        self.assertEqual(len(units), 2)
        self.assertEqual(len({u["source"] for u in units}), 2)
        self.assertTrue(all(u["scan_pairing_complete"] for u in units))
        self.assertEqual([u["segment_index"] for u in units], [1, 2])
        self.assertTrue(all(u["segments_available"] == 2 for u in units))

    def test_duplicate_segment_sources_fail_closed(self):
        with patch.object(config, "PACK", "C"), patch.object(config, "CAMERA_FILTER", "sdg_warehouse_cam-2"):
            with self.assertRaises(LiveScanUnavailable):
                scan_live(DuplicateSegmentClient())

    def test_explore_schema_and_repeated_pagination_fail_closed(self):
        for bad in ({}, {"items": "bad", "total": 1}, {"items": [], "total": "x"}):
            with self.subTest(bad=bad), self.assertRaises(VssError):
                VssClient._explore_batch(bad)
        with self.assertRaises(VssError):
            RepeatedExploreClient().explore_all()

    def test_frontend_uses_ingress_prefix_and_non_2xx_guard(self):
        html = (SCRIBNER / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("const APP_BASE", html)
        self.assertIn("async function appFetch", html)
        self.assertIn("if (!response.ok)", html)
        self.assertIn("showError(err)", html)
        self.assertNotIn("fetch('/api/", html)
        self.assertNotIn('fetch("/api/', html)
        self.assertNotIn("src = '/clip", html)
        self.assertIn("appUrl('clip?unit_id=", html)

    def test_live_clip_never_falls_back_to_mock_when_vss_missing(self):
        import main
        with patch.object(main.state, "mock", False), patch.object(config, "VSS_URL", ""):
            with self.assertRaises(main.HTTPException) as cm:
                main.clip(source="s3://segments/1.mp4", unit_id="")
        self.assertEqual(cm.exception.status_code, 503)

    def test_pack_c_hand_is_not_occlusion(self):
        self.assertFalse(occlusion_from_yolo({"object_classes": ["hand", "person"]}, corpus=True))

    def test_wandb_tracking_missing_key_is_explicit_skip(self):
        with patch.object(config, "WANDB_API_KEY", ""):
            out = log_retrain({"coverage": 0.5}, {"n": 1}, [])
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(tracking_status()["status"], "skipped")

    def test_wandb_inference_is_bounded(self):
        src = (SCRIBNER / "llm.py").read_text(encoding="utf-8")
        self.assertIn("timeout=20.0", src)
        self.assertIn("max_retries=0", src)
        self.assertIn("def status()", src)

    def test_deployment_has_stack_lock_persistent_state_and_app_prefix(self):
        doc = (ROOT / "deploy" / "DEPLOY.md").read_text(encoding="utf-8")
        sh = (ROOT / "workshop" / "07_deploy_scribner.sh").read_text(encoding="utf-8")
        for text in (doc, sh):
            self.assertIn("builders_stack_lock.json", text)
            self.assertIn("/app", text)
            self.assertIn("scribner-data", text)
            self.assertIn("/data/scribner", text)
        self.assertNotIn("CANARY_1B_URL", sh)

    def test_workshop_scripts_are_present(self):
        for name in (
            "02_vss_preflight.py", "03_reingest_one_pack_c.py", "04_reingest_remaining_pack_c.py",
            "05_verify_live_scribner.py", "06_verify_gpu_wandb.py", "07_deploy_scribner.sh",
            "08_finalize_submission.py",
        ):
            self.assertTrue((ROOT / "workshop" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
