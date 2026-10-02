"""Attack the handoff's readiness checks without contacting live services."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("handoff_checks", ROOT / "scripts/handoff_checks.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class HandoffChecksTest(unittest.TestCase):
    def test_handoff_shell_python_and_section_contracts(self):
        doc = (ROOT / ".cursor/handoffs/josh-cowork.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^## (.+)$", doc, re.M), [
            "Receiver", "Done when", "Context", "Never", "Inputs", "Procedure",
            "Verification", "Report back", "Stop and escalate"])
        context = doc.split("## Context\n", 1)[1].split("## Never", 1)[0]
        self.assertLessEqual(len([s for s in context.splitlines() if s.strip()]), 8)
        for block in re.findall(r"```bash\n(.*?)\n```", doc, re.S):
            # Bytes keep LF line endings; text mode writes CRLF on Windows.
            result = subprocess.run(["bash", "-n"], input=block.encode("utf-8"), capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
            for python in re.findall(r"python - <<'PY'\n(.*?)\nPY", block, re.S):
                compile(python, "handoff snippet", "exec")

    def test_http_redirect_and_auth_errors_fail(self):
        for status in (301, 302, 401, 403, 500):
            with self.subTest(status=status), patch.object(checks.requests, "request",
                    return_value=SimpleNamespace(status_code=status)) as request:
                with self.assertRaises(checks.CheckFailure):
                    checks.request("GET", "https://example.invalid/health")
                self.assertFalse(request.call_args.kwargs["allow_redirects"])
                self.assertEqual(request.call_args.kwargs["timeout"], (5, 20))

    def test_exception_secrets_are_not_reported(self):
        results = checks.Results()
        def fail():
            raise RuntimeError("Bearer SECRET token=SECRET password=SECRET")
        results.check("probe", fail)
        self.assertNotIn("SECRET", json.dumps(results.rows))
        self.assertEqual(results.exit_code(), 1)
        self.assertEqual(results.rows[0]["reason"], "RuntimeError")

    def test_missing_services_do_not_pass_or_make_requests(self):
        results = checks.Results()
        with patch.object(checks.requests, "request") as request:
            checks.vss_checks(results, {})
            checks.gpu_checks(results, {})
            checks.wandb_check(results, {})
            request.assert_not_called()
        self.assertEqual(len(results.rows), 10)
        self.assertTrue(all(r["status"] == "skipped" for r in results.rows))
        self.assertEqual(results.exit_code(), 2)

    def test_vss_failure_does_not_silently_drop_dependent_results(self):
        results = checks.Results()
        with patch.object(checks, "json_request", side_effect=checks.CheckFailure("http_401")):
            checks.vss_checks(results, {"INGRESS_URL": "https://example.invalid",
                                      "USERNAME": "team-test", "PASSWORD": "secret"})
        self.assertEqual(results.rows[0]["status"], "fail")
        self.assertEqual(len(results.rows), 6)
        self.assertTrue(all(r["status"] == "skipped" for r in results.rows[1:]))
        checks.gpu_checks(results, {})
        checks.wandb_check(results, {})
        self.assertEqual(len(results.rows), 10)
        self.assertEqual(results.exit_code(), 1)

    def test_vss_alias_precedence_matches_the_app(self):
        env = {"INGRESS_URL": "https://unused.invalid", "USERNAME": "unused", "PASSWORD": "unused",
               "VSS_URL": "https://app.invalid", "VSS_USERNAME": "actual", "VSS_PASSWORD": "secret"}
        with patch.object(checks, "json_request", side_effect=checks.CheckFailure("http_401")) as call:
            checks.vss_checks(checks.Results(), env)
        self.assertEqual(call.call_args.args[1], "https://app.invalid/api/v1/auth/login")
        self.assertEqual(call.call_args.kwargs["json"], {"username": "actual", "password": "secret"})

    def test_camera_missing_substring_wrong_location_rejected(self):
        for rows in ([], [{"camera_id": "other"}],
                     [{"camera_id": checks.CAMERA + "-spoof", "location": "warehouse3"}],
                     [{"camera_id": checks.CAMERA, "location": "wrong"}]):
            with self.subTest(rows=rows), self.assertRaises(checks.CheckFailure):
                checks.pack_c(rows)

    def test_explore_unknown_or_incomplete_schema_rejected(self):
        for page in ([], {}, {"items": [], "total": "1"}, {"items": [], "total": 1},
                     {"items": [{}], "total": 1}, {"items": "invalid", "total": 1}):
            with self.subTest(page=page), self.assertRaises(checks.CheckFailure):
                checks.inventory(lambda offset: page)

    def test_explore_all_pages_and_duplicate_attack(self):
        rows = [{"original_video": str(i)} for i in range(101)]
        offsets = []
        def fetch(offset):
            offsets.append(offset)
            return {"items": rows[offset:offset+100], "total": 101}
        self.assertEqual(checks.inventory(fetch), rows)
        self.assertEqual(offsets, [0, 100])
        rows[-1] = rows[0]
        with self.assertRaises(checks.CheckFailure):
            checks.inventory(fetch)

    def test_empty_or_parent_only_search_is_not_segment_proof(self):
        for payload in ({"results": []}, {"chunk_results": [{"original_video": "x"}]},
                        {"results": [{}]}, {"results": [{"source": ""}]}):
            with self.subTest(payload=payload), self.assertRaises(checks.CheckFailure):
                checks.search_hits(payload)

    def test_requested_camera_filter_does_not_prove_response_camera(self):
        for camera in (None, "other", checks.CAMERA):
            def fake(method, url, **kwargs):
                if url.endswith("auth/login"):
                    return {"access_token": "secret"}
                if url.endswith("auth/me"):
                    return {"username": "team-test"}
                if url.endswith("videos/explore"):
                    return {"total": 1, "items": [{"original_video": "parent", "camera_id": checks.CAMERA,
                        "location": "warehouse3", "preview_source": "known"}]}
                if url.endswith("search"):
                    return {"results": [{"source": "unknown", "camera_id": camera}]}
                return {"setting": True}
            results = checks.Results()
            with patch.object(checks, "json_request", side_effect=fake):
                checks.vss_checks(results, {"INGRESS_URL": "https://example.invalid",
                                          "USERNAME": "team-test", "PASSWORD": "secret"})
            self.assertEqual(results.rows[-1]["status"], "ok" if camera == checks.CAMERA else "fail")

    def test_yolo_200_with_unloaded_model_is_failure(self):
        for payload in ({"ok": True, "model_loaded": False}, {"ok": True},
                        {"ok": "true", "model_loaded": "true"}):
            with patch.object(checks, "json_request", return_value=payload):
                with self.assertRaises(checks.CheckFailure):
                    checks.gpu_health("https://example.invalid", "yolo", "secret")

    def test_configured_gpu_is_attempted_without_optional_bearer(self):
        results = checks.Results()
        with patch.object(checks, "json_request", return_value={"ok": True, "model_loaded": True}) as call:
            checks.gpu_checks(results, {"YOLO_URL": "https://example.invalid"})
        self.assertEqual(call.call_args.kwargs["headers"], {})
        self.assertEqual(next(r["status"] for r in results.rows if r["check"] == "yolo_health"), "ok")

    def test_reason_and_embed_require_models_ready_and_live(self):
        with patch.object(checks, "json_request", return_value={"data": [{"id": "model"}]}), \
             patch.object(checks, "request") as request:
            checks.gpu_health("https://example.invalid", "embed1", "secret")
            self.assertEqual([c.args[1] for c in request.call_args_list],
                             ["https://example.invalid/v1/health/ready", "https://example.invalid/v1/health/live"])
        with patch.object(checks, "json_request", return_value={"data": []}):
            with self.assertRaises(checks.CheckFailure):
                checks.gpu_health("https://example.invalid", "cosmos_reason", "secret")
        with patch.object(checks, "json_request", return_value={"data": [{"id": "model"}]}), \
             patch.object(checks, "request", side_effect=checks.CheckFailure("http_503")):
            with self.assertRaises(checks.CheckFailure):
                checks.gpu_health("https://example.invalid", "cosmos_reason", "secret")

    def test_embedding_dimensions_types_and_finite_values(self):
        checks.embedding_valid([0.0] * 256)
        for vector in ([0.0]*255, [True]*256, ["0"]*256, [float("nan")]*256, [float("inf")]*256):
            with self.subTest(value=type(vector[0]).__name__), self.assertRaises(checks.CheckFailure):
                checks.embedding_valid(vector)

    def test_wandb_empty_completion_and_timeout_are_not_ok(self):
        for empty in (True, False):
            client = Mock()
            client.__enter__ = Mock(return_value=client)
            client.__exit__ = Mock(return_value=False)
            if empty:
                client.chat.completions.create.return_value = SimpleNamespace(choices=[])
            else:
                client.chat.completions.create.side_effect = TimeoutError("secret token")
            constructor = Mock(return_value=client)
            results = checks.Results()
            with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=constructor)}):
                checks.wandb_check(results, {"WANDB_API_KEY": "secret", "SCRIBNER_MODEL": "verified",
                                            "WANDB_TEAM": "team", "WANDB_PROJECT": "project"})
            self.assertEqual(results.exit_code(), 1)
            self.assertNotIn("secret", json.dumps(results.rows))
            self.assertEqual(constructor.call_args.kwargs["timeout"], 20)
            self.assertEqual(constructor.call_args.kwargs["max_retries"], 0)

    def app_fixture(self, mode=True):
        rows = [{"id": str(i), "decision": {"decision": ("AUTO_ALERT", "HOLD", "AUTO_CLEAR")[i % 3]}}
                for i in range(40 if mode else 2)]
        board = {"board": "andon", "name_ja": "安灯", "gemba": "現場", "camera_id": checks.CAMERA,
                 "rule": "赤灯は人なしで緑にしない", "line_ja": "赤 停止", "station_lamp": "red"}
        health = {"mock": mode, "product": "warehouse-near-miss", "line": "primary", "corpus": "provided",
                  "stack": {"canary_wired": False, "source": "https://github.com/vast-data/vast-builders-challenge"}}
        details = {u["id"]: {"mock": mode, "camera_id": checks.CAMERA, "location": "warehouse3",
                              "source": "s3://segment/" + u["id"]} for u in rows}
        paths = []
        def fetch(method, url, **kwargs):
            path = url.removeprefix("https://example.invalid/app")
            paths.append(path)
            if path == "/health": return health
            if path == "/api/andon": return board
            if path == "/api/units": return {"units": rows}
            return details[path.removeprefix("/api/units/")]
        return rows, details, paths, fetch

    def test_mock_cannot_pass_live_check(self):
        rows, details, paths, fetch = self.app_fixture()
        with patch.object(checks, "json_request", side_effect=fetch):
            with self.assertRaisesRegex(checks.CheckFailure, "wrong_app_mode"):
                checks.app_check("https://example.invalid/app", "live")

    def test_app_checks_keep_prefix_and_require_exact_report_line(self):
        rows, details, paths, fetch = self.app_fixture()
        with patch.object(checks, "json_request", side_effect=fetch), \
             patch.object(checks, "request", return_value=SimpleNamespace(text="- 安灯 ANDON line: **赤 停止** (red)")):
            checks.app_check("https://example.invalid/app/", "mock")
        self.assertEqual(len([p for p in paths if p.startswith("/api/units/")]), 40)
        with patch.object(checks, "json_request", side_effect=fetch), \
             patch.object(checks, "request", return_value=SimpleNamespace(text="赤 停止 elsewhere, wrong LINE")):
            with self.assertRaisesRegex(checks.CheckFailure, "report_line_mismatch"):
                checks.app_check("https://example.invalid/app", "mock")

    def test_live_unit_wrong_camera_missing_or_duplicate_source_fails(self):
        for field, value in (("camera_id", "other"), ("source", ""), ("mock", True), ("source", "s3://segment/1")):
            rows, details, paths, fetch = self.app_fixture(False)
            details["0"][field] = value
            with patch.object(checks, "json_request", side_effect=fetch), \
                 patch.object(checks, "request", return_value=SimpleNamespace(text="- 安灯 ANDON line: **赤 停止** (red)")):
                with self.subTest(field=field, value=value), self.assertRaises(checks.CheckFailure):
                    checks.app_check("https://example.invalid/app", "live")

    def test_empty_units_or_missing_mock_lamp_fixture_is_not_pass(self):
        for empty in (True, False):
            rows, details, paths, fetch = self.app_fixture()
            if empty:
                rows.clear()
            else:
                for row in rows:
                    row["decision"]["decision"] = "AUTO_CLEAR"
            with patch.object(checks, "json_request", side_effect=fetch), \
                 patch.object(checks, "request", return_value=SimpleNamespace(text="- 安灯 ANDON line: **赤 停止** (red)")):
                with self.assertRaises(checks.CheckFailure):
                    checks.app_check("https://example.invalid/app", "mock")


if __name__ == "__main__":
    unittest.main()
