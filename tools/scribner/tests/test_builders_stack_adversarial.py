"""Adversarial tests vs https://github.com/vast-data/vast-builders-challenge

These attacks should fail closed. If one succeeds, the gate is not using
the official Builders Stack (or it can false-PASS a kit).
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["SCRIBNER_MOCK"] = "1"
os.environ.setdefault("SCRIBNER_DATA_DIR", tempfile.mkdtemp(prefix="scribner-adv-"))

from builders_stack import (  # noqa: E402
    ALLOWED_VSS_PATHS,
    CONFIG_EXAMPLE_ENV,
    CUSTOM_PROMPT_MAX,
    FORBIDDEN_VSS_PATHS,
    SOURCE_URL,
    assert_subset_of_official,
    challenge_dir,
    extract_from_challenge,
    scan_scribner_violations,
    vss_paths_in_scribner,
)
from gate import decide_one, pass_blocked  # noqa: E402
from ingest import IngestRejected, assert_uploadable, filter_upload_fields  # noqa: E402
from inspection import parse_caption  # noqa: E402
from kits import kit_ids, prompt_for_kit  # noqa: E402
from state import AppState  # noqa: E402
from store import Store  # noqa: E402


def _unit(**kwargs):
    insp = kwargs.pop("inspection", None)
    base = {
        "id": kwargs.pop("id", "u-1"),
        "kit_id": "race-car",
        "inspection": insp
        or {
            "complete": True,
            "confidence": "high",
            "missing": [],
            "unclear": [],
            "inconsistent": False,
        },
        "prior": {"p_fail_prior": kwargs.pop("p_fail_prior", 0.05)},
        "occlusion": kwargs.pop("occlusion", False),
    }
    base.update(kwargs)
    return base


class OfficialRepoContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = challenge_dir()
        cls.extracted = extract_from_challenge(cls.repo) if cls.repo else None

    def test_challenge_repo_is_present_for_adversarial(self) -> None:
        self.assertIsNotNone(
            self.repo,
            "clone https://github.com/vast-data/vast-builders-challenge "
            "(or set BUILDERS_CHALLENGE_DIR) before claiming stack conformance",
        )
        self.assertTrue((self.repo / "config.example").is_file())
        self.assertTrue((self.repo / "BUILD_DAY.md").is_file())
        self.assertTrue(
            (self.repo / ".cursor" / "skills" / "ingest" / "upload-video" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (
                self.repo
                / ".cursor"
                / "skills"
                / "deployment"
                / "deploy-app-no-registry"
                / "SKILL.md"
            ).is_file()
        )

    def test_lock_matches_official_config_example(self) -> None:
        if not self.extracted:
            self.skipTest("challenge clone missing")
        official = self.extracted["config_example_env"]
        self.assertEqual(
            official,
            CONFIG_EXAMPLE_ENV,
            "Scribner's config.example env list drifted from the official repo",
        )

    def test_forbidden_routes_are_named_in_retrieval_readme(self) -> None:
        if not self.repo:
            self.skipTest("challenge clone missing")
        text = (self.repo / ".cursor" / "skills" / "retrieval" / "README.md").read_text(
            encoding="utf-8"
        )
        lowered = text.lower().replace("don't", "do not")
        self.assertIn("do not exist", lowered)
        for short in ("/reports", "/alerts", "/analytics", "/videos/ask", "/tags", "/locations", "/extra-metadata"):
            self.assertIn(short, text)

    def test_upload_contract_and_prompt_cap(self) -> None:
        if not self.repo:
            self.skipTest("challenge clone missing")
        text = (
            self.repo / ".cursor" / "skills" / "ingest" / "upload-video" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("POST /api/v1/videos/upload", text)
        for field in (
            "file",
            "is_public",
            "tags",
            "custom_prompt",
            "camera_id",
            "capture_type",
            "location",
            "scenario",
        ):
            self.assertIn(field, text)
        self.assertIn("800", text)
        self.assertEqual(self.extracted["custom_prompt_max"], CUSTOM_PROMPT_MAX)

    def test_gpu_env_names_are_official_and_host_is_not_hardcoded_in_scribner(self) -> None:
        if not self.repo:
            self.skipTest("challenge clone missing")
        cfg = (self.repo / "config.example").read_text(encoding="utf-8")
        for name in ("COSMOS3_REASON_URL", "YOLO_URL", "COSMOS_EMBED1_URL", "CANARY_1B_URL"):
            self.assertIn(name + "=", cfg)
        gpu = (self.repo / ".cursor" / "skills" / "gpu" / "README.md").read_text(encoding="utf-8")
        self.assertIn("GPU_BEARER_TOKEN", gpu)
        self.assertIn("/v1/infer", gpu)
        self.assertIn("/healthz", gpu)
        self.assertIn("/v1/embeddings", gpu)
        problems = assert_subset_of_official(self.extracted)
        self.assertEqual(problems, [])

    def test_deploy_skill_is_configmap_app_on_ingress(self) -> None:
        if not self.repo:
            self.skipTest("challenge clone missing")
        text = (
            self.repo
            / ".cursor"
            / "skills"
            / "deployment"
            / "deploy-app-no-registry"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("python:3.12-slim", text)
        self.assertIn("/app", text)
        self.assertIn("docker build", text.lower())

    def test_scribner_runtime_has_no_stack_violations(self) -> None:
        hits = scan_scribner_violations()
        self.assertEqual(hits, [], msg="\n".join(hits))

    def test_scribner_vss_paths_are_subset_of_official_skills(self) -> None:
        used = vss_paths_in_scribner()
        for path in used:
            self.assertNotIn(path, FORBIDDEN_VSS_PATHS, path)
            self.assertTrue(
                any(path == a or path.startswith(a + "/") for a in ALLOWED_VSS_PATHS),
                f"undocumented VSS path {path}",
            )

    def test_health_names_the_official_source(self) -> None:
        from builders_stack import health_snapshot

        snap = health_snapshot()
        self.assertEqual(snap["source"], SOURCE_URL)
        self.assertFalse(snap["canary_wired"])
        self.assertEqual(snap["deploy_path"], "/app")
        self.assertEqual(snap["custom_prompt_max"], 800)


class GateFailClosedTests(unittest.TestCase):
    def test_inconsistent_caption_never_auto_pass(self) -> None:
        cap = (
            "PRESENT: 1 red roof. MISSING: 4 black wheels. UNCLEAR: NONE. "
            "COMPLETE: YES. CONFIDENCE: HIGH."
        )
        rec = parse_caption(cap, kit_id="race-car")
        self.assertTrue(rec["inconsistent"])
        u = _unit(inspection=rec, p_fail_prior=0.01)
        self.assertTrue(pass_blocked(u))
        d = decide_one(u, None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertNotEqual(d["decision"], "AUTO_PASS")

    def test_missing_parts_never_auto_pass(self) -> None:
        rec = {
            "complete": True,
            "confidence": "high",
            "missing": ["4 black wheels"],
            "unclear": [],
            "inconsistent": True,
        }
        d = decide_one(_unit(inspection=rec, p_fail_prior=0.01), None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertNotEqual(d["decision"], "AUTO_PASS")

    def test_low_confidence_never_auto_pass(self) -> None:
        rec = {
            "complete": True,
            "confidence": "low",
            "missing": [],
            "unclear": [],
            "inconsistent": False,
        }
        d = decide_one(_unit(inspection=rec, p_fail_prior=0.01), None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertEqual(d["decision"], "HOLD")

    def test_unclear_never_auto_pass(self) -> None:
        rec = {
            "complete": True,
            "confidence": "high",
            "missing": [],
            "unclear": ["1 blue door"],
            "inconsistent": False,
        }
        d = decide_one(_unit(inspection=rec, p_fail_prior=0.01), None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertNotEqual(d["decision"], "AUTO_PASS")

    def test_occlusion_never_auto_pass(self) -> None:
        rec = {
            "complete": True,
            "confidence": "high",
            "missing": [],
            "unclear": [],
            "inconsistent": False,
        }
        d = decide_one(
            _unit(inspection=rec, p_fail_prior=0.01, occlusion=True),
            None,
            {"t_pass": 0.5, "t_fail": 0.9},
            audit_fraction=0,
        )
        self.assertEqual(d["decision"], "HOLD")

    def test_complete_no_forced_auto_fail_not_pass(self) -> None:
        rec = {
            "complete": False,
            "confidence": "high",
            "missing": ["4 black wheels"],
            "unclear": [],
            "inconsistent": False,
        }
        d = decide_one(_unit(inspection=rec, p_fail_prior=0.01), None, {"t_pass": 0.5, "t_fail": 0.9}, audit_fraction=0)
        self.assertEqual(d["decision"], "AUTO_FAIL")

    def test_pack_c_missing_gap_never_auto_pass(self) -> None:
        cap = (
            "PRESENT: a pallet-free walkway. MISSING: person-vehicle separation. "
            "UNCLEAR: NONE. COMPLETE: NO. CONFIDENCE: HIGH."
        )
        rec = parse_caption(cap, kit_id="warehouse-aisle")
        d = decide_one(
            _unit(inspection=rec, p_fail_prior=0.01),
            None,
            {"t_pass": 0.5, "t_fail": 0.9},
            audit_fraction=0,
        )
        self.assertNotEqual(d["decision"], "AUTO_PASS")
        self.assertEqual(d["decision"], "AUTO_FAIL")


class IngestPokaYokeTests(unittest.TestCase):
    def test_youtube_rejected(self) -> None:
        with self.assertRaises(IngestRejected):
            assert_uploadable(
                "https://www.youtube.com/watch?v=dQw4w9wgGcQ",
                prompt_for_kit("race-car"),
            )

    def test_http_file_rejected(self) -> None:
        with self.assertRaises(IngestRejected):
            assert_uploadable("https://example.com/kit.mp4", prompt_for_kit("race-car"))

    def test_random_filename_rejected(self) -> None:
        with self.assertRaises(IngestRejected):
            assert_uploadable("/tmp/random.mp4", prompt_for_kit("race-car"))

    def test_unknown_kit_rejected(self) -> None:
        with self.assertRaises(IngestRejected):
            assert_uploadable("/tmp/kit-spaceship_unit-001.mp4", prompt_for_kit("race-car"))

    def test_overlong_prompt_rejected(self) -> None:
        with self.assertRaises(IngestRejected):
            assert_uploadable(
                "/tmp/kit-race-car_unit-001.mp4",
                "x" * (CUSTOM_PROMPT_MAX + 1),
            )

    def test_legal_filename_and_prompt_ok(self) -> None:
        kid = assert_uploadable(
            "/tmp/kit-race-car_unit-014.mp4",
            prompt_for_kit("race-car"),
        )
        self.assertEqual(kid, "race-car")
        self.assertIn("race-car", kit_ids())

    def test_legal_pack_c_filename_ok(self) -> None:
        kid = assert_uploadable(
            "/tmp/kit-warehouse-aisle_unit-014.mp4",
            prompt_for_kit("warehouse-aisle"),
        )
        self.assertEqual(kid, "warehouse-aisle")

    def test_upload_fields_drop_scenario_when_custom_prompt_set(self) -> None:
        out = filter_upload_fields(
            {
                "custom_prompt": "hello",
                "scenario": "general",
                "invented": "nope",
                "tags": "kit:race-car",
                "camera_id": "",
            }
        )
        self.assertNotIn("scenario", out)
        self.assertNotIn("invented", out)
        self.assertNotIn("camera_id", out)
        self.assertEqual(out["custom_prompt"], "hello")


class ReviewPokaYokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="scribner-poka-")
        self.state = AppState(store=Store(self.tmp), mock=True)
        self.state.scan()
        self.state.run_gate()

    def test_gate_ok_on_hold_rejected(self) -> None:
        hold = next(
            d for d in self.state.store.load_decisions() if d["decision"] == "HOLD"
        )
        with self.assertRaises(ValueError):
            self.state.review(hold["unit_id"], "COMPLETE", reason="agree", gate_ok=True)

    def test_override_agree_rejected(self) -> None:
        auto_fail = next(
            (
                d
                for d in self.state.store.load_decisions()
                if d["decision"] == "AUTO_FAIL"
            ),
            None,
        )
        if auto_fail is None:
            self.skipTest("cold start produced no AUTO_FAIL")
        with self.assertRaises(ValueError):
            self.state.review(auto_fail["unit_id"], "COMPLETE", reason="agree")

    def test_auto_fail_to_complete_needs_confirm(self) -> None:
        auto_fail = next(
            (
                d
                for d in self.state.store.load_decisions()
                if d["decision"] == "AUTO_FAIL"
            ),
            None,
        )
        if auto_fail is None:
            self.skipTest("cold start produced no AUTO_FAIL")
        with self.assertRaises(ValueError):
            self.state.review(
                auto_fail["unit_id"],
                "COMPLETE",
                reason="vlm_false_missing",
                confirm_escape=False,
            )
        self.state.review(
            auto_fail["unit_id"],
            "COMPLETE",
            reason="vlm_false_missing",
            confirm_escape=True,
        )


class NoCanaryAndNoInventedClientTests(unittest.TestCase):
    def test_gpu_client_module_does_not_reference_canary_url(self) -> None:
        src = Path(__file__).resolve().parents[1] / "gpu_client.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("CANARY_1B_URL", text)
        self.assertNotIn("/v1/audio/transcriptions", text)
        self.assertNotIn("166.19.38.112", text)
        self.assertIn("YOLO_URL", text)
        self.assertIn("/v1/infer", text)
        self.assertIn("/v1/embeddings", text)

    def test_vss_client_upload_rejects_youtube_before_http(self) -> None:
        from vss_client import VssClient, VssError

        client = VssClient(base="http://127.0.0.1:9", username="x", password="y")
        with mock.patch.object(client, "prompt_max", return_value=800):
            with self.assertRaises(VssError):
                client.upload_video(
                    "https://youtu.be/xxxx",
                    custom_prompt=prompt_for_kit("race-car"),
                    tags="kit:race-car",
                    camera_id="kit-station-1",
                    capture_type="general",
                    location="kit-bench",
                )


if __name__ == "__main__":
    unittest.main()
