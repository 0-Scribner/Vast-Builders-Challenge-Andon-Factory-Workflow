"""Workshop step 9: read-only VastDB evidence against a fake vastdb SDK."""
from __future__ import annotations

import contextlib
import importlib.abc
import importlib.util
import io
import json
import os
import re
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import quote

HERE = Path(__file__).resolve()
SCRIBNER = HERE.parents[1]
ROOT = SCRIBNER.parents[1]
SCRIPT = ROOT / "workshop" / "09_vastdb_read.py"
if str(SCRIBNER) not in sys.path:
    sys.path.insert(0, str(SCRIBNER))

from builders_stack import challenge_dir  # noqa: E402
from kits import PACK_C_CAMERA, PACK_C_LOCATION, prompt_for_kit  # noqa: E402

spec = importlib.util.spec_from_file_location("workshop_09_vastdb_read", SCRIPT)
step9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step9)

ENV_NAMES = ("VDB_ENDPOINT", "S3_ENDPOINT", "ACCESS_KEY", "SECRET_KEY", "VASTDB_BUCKET")
ACCESS = "unit-test-access-4f1c"
SECRET = "unit-test/secret+value=9b2e"
HOST = "VastDB-VIP.invalid"
ENDPOINT = f"http://{HOST}:18080"
BUCKET = "team-x-vss-db"
LIVE_ENV = {"VDB_ENDPOINT": ENDPOINT, "ACCESS_KEY": ACCESS, "SECRET_KEY": SECRET, "VASTDB_BUCKET": BUCKET}
CONFIG_VALUES = (ACCESS, SECRET, quote(SECRET, safe=""), quote(SECRET, safe="").lower(), HOST, HOST.lower(),
                 BUCKET)
COMPLETE = "PERSON: YES; PATH_CLEAR: NO; NEAR_MISS: YES; UNCLEAR: NONE; CONFIDENCE: HIGH"
VECTOR_COLUMNS = ("vectors", "vectors_visual")
TABLE_COLUMNS = ("source", "original_video", "camera_id", "location", "reasoning_content", *VECTOR_COLUMNS)


def row(caption, camera=PACK_C_CAMERA, location=PACK_C_LOCATION):
    return {"source": "s3://segments/clip.mp4", "camera_id": camera, "location": location,
            "reasoning_content": caption}


class FakeVastdb:
    """Only the read calls of the retrieval/vastdb-read skill, each one recorded."""

    def __init__(self, rows=(), columns=TABLE_COLUMNS, error=None):
        self.rows = [dict(r) for r in rows]
        self.columns = list(columns)
        self.error = error
        self.calls = []
        self.module = types.ModuleType("vastdb")
        self.module.connect = self.connect

    def connect(self, access=None, secret=None, endpoint=None, *, ssl_verify=True, timeout=None,
                backoff_config=None):
        self.calls.append(("connect", endpoint, access, secret, ssl_verify))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(transaction=self.transaction)

    @contextlib.contextmanager
    def transaction(self):
        self.calls.append(("transaction",))
        try:
            yield SimpleNamespace(bucket=self.bucket)
        finally:
            self.calls.append(("transaction_closed",))

    def bucket(self, name):
        self.calls.append(("bucket", name))
        return SimpleNamespace(schema=self.schema)

    def schema(self, name):
        self.calls.append(("schema", name))
        return SimpleNamespace(table=self.table)

    def table(self, name):
        self.calls.append(("table", name))
        return SimpleNamespace(columns=self.table_columns, select=self.select)

    def table_columns(self):
        self.calls.append(("columns",))
        return [SimpleNamespace(name=name) for name in self.columns]

    def select(self, columns=None, predicate=None, config=None, *, internal_row_id=False, limit_rows=None):
        columns = list(self.columns if columns is None else columns)
        self.calls.append(("select", columns))
        # The skill warns that projecting the vector columns fails without the pipeline patch.
        bad = [c for c in columns if c not in self.columns or c in VECTOR_COLUMNS]
        if bad:
            raise ValueError(f"cannot project {bad}")
        rows = [{c: r.get(c) for c in columns} for r in self.rows]
        return SimpleNamespace(read_all=lambda: SimpleNamespace(to_pylist=lambda: rows))


class MissingDependency(importlib.abc.MetaPathFinder):
    """Fails `import vastdb` the way an install without one of its dependencies does."""

    def __init__(self, dependency):
        self.dependency = dependency

    def find_spec(self, fullname, path, target=None):
        if fullname == "vastdb":
            raise ModuleNotFoundError(f"No module named '{self.dependency}'", name=self.dependency)
        return None


class VastdbReadTests(unittest.TestCase):
    def run_step9(self, env, sdk=None, modules=None, finder=None, evidence_dir=None, entry_point=False):
        tmp = tempfile.TemporaryDirectory(prefix="scribner-step9-")
        self.addCleanup(tmp.cleanup)
        evidence = Path(evidence_dir) if evidence_dir is not None else Path(tmp.name)
        if sdk is not None:
            modules = {"vastdb": sdk.module}
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ))
            stack.enter_context(patch.dict(sys.modules, modules or {}))
            for name in ENV_NAMES:
                os.environ.pop(name, None)
            os.environ.update(env)
            os.environ["SCRIBNER_EVIDENCE_DIR"] = str(evidence)
            if finder is not None:
                sys.modules.pop("vastdb", None)
                stack.enter_context(patch.object(sys, "meta_path", [finder, *sys.meta_path]))
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            if entry_point:
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(str(SCRIPT), run_name="__main__")
                code = raised.exception.code
            else:
                code = step9.main()
        path = evidence / step9.REPORT_NAME
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        result = SimpleNamespace(code=code, text=text, report=json.loads(text) if text else None,
                                 stdout=out.getvalue(), stderr=err.getvalue())
        for value in CONFIG_VALUES:
            for name in ("text", "stdout", "stderr"):
                self.assertNotIn(value, getattr(result, name), f"{name} carries a config value")
        return result

    def test_only_exact_camera_and_location_count(self):
        near = [
            row(COMPLETE, camera=PACK_C_CAMERA + "0"),
            row(COMPLETE, location=PACK_C_LOCATION + "0"),
            row(COMPLETE, camera=PACK_C_CAMERA + "0", location=PACK_C_LOCATION + "0"),
            row(COMPLETE, camera="x" + PACK_C_CAMERA),
            row(COMPLETE, location=None),
            row(COMPLETE, camera=None),
        ]
        self.assertEqual(near[0]["camera_id"], "sdg_warehouse_cam-20")
        self.assertEqual(near[1]["location"], "warehouse30")

        result = self.run_step9(LIVE_ENV, FakeVastdb(near))
        self.assertEqual((result.code, result.report["status"]), (1, "FAIL"))
        self.assertEqual(result.report["total_rows"], len(near))
        self.assertEqual(result.report["pack_c_rows"], 0)
        self.assertFalse(result.report["checks"]["pack_c_rows_present"])

        result = self.run_step9(LIVE_ENV, FakeVastdb(near + [row(COMPLETE), row(COMPLETE)]))
        self.assertEqual((result.code, result.report["status"]), (0, "PASS"))
        self.assertEqual(result.report["total_rows"], len(near) + 2)
        self.assertEqual(result.report["pack_c_rows"], 2)
        self.assertEqual(result.report["pack_c_rows_with_all_fields"], 2)
        self.assertEqual((result.report["pack_c_camera"], result.report["pack_c_location"]),
                         (PACK_C_CAMERA, PACK_C_LOCATION))

    def test_caption_schema_fields_are_counted_per_pack_c_row(self):
        prompt = prompt_for_kit("warehouse-aisle")
        for field in step9.CAPTION_FIELDS:
            self.assertIn(field, prompt)
        rows = [
            row(COMPLETE),
            row(COMPLETE.lower()),
            row("PERSON: UNCLEAR; PATH_CLEAR: YES; NEAR_MISS: NO"),
            row("PATH_CLEAR YES; NEAR_MISS NO; UNCLEAR NONE; CONFIDENCE HIGH"),
            row(None),
            row(COMPLETE, camera=PACK_C_CAMERA + "0"),
        ]
        result = self.run_step9(LIVE_ENV, FakeVastdb(rows))
        self.assertEqual((result.code, result.report["status"]), (0, "PASS"))
        self.assertEqual((result.report["total_rows"], result.report["pack_c_rows"]), (6, 5))
        self.assertEqual(result.report["pack_c_caption_field_counts"],
                         {"PATH_CLEAR:": 3, "NEAR_MISS:": 3, "UNCLEAR:": 2, "CONFIDENCE:": 2})
        self.assertEqual(result.report["pack_c_rows_with_all_fields"], 2)
        self.assertIn("PATH_CLEAR=3 NEAR_MISS=3 UNCLEAR=2 CONFIDENCE=2 all_fields=2", result.stdout)

        partial = [row("PATH_CLEAR: YES; NEAR_MISS: NO; CONFIDENCE: HIGH")] * 2
        result = self.run_step9(LIVE_ENV, FakeVastdb(partial))
        self.assertEqual((result.code, result.report["status"]), (1, "FAIL"))
        self.assertEqual(result.report["checks"],
                         {"pack_c_rows_present": True, "pack_c_caption_with_all_fields": False})
        self.assertEqual(result.report["pack_c_caption_field_counts"]["UNCLEAR:"], 0)
        self.assertIn("FAIL", result.stderr)

    def test_missing_environment_fails_closed_before_the_sdk_is_touched(self):
        cases = {
            "VDB_ENDPOINT or S3_ENDPOINT": "VDB_ENDPOINT",
            "ACCESS_KEY": "ACCESS_KEY",
            "SECRET_KEY": "SECRET_KEY",
            "VASTDB_BUCKET": "VASTDB_BUCKET",
        }
        for missing, dropped in cases.items():
            with self.subTest(missing=missing):
                env = {k: v for k, v in LIVE_ENV.items() if k != dropped}
                sdk = FakeVastdb([row(COMPLETE)])
                result = self.run_step9(env, sdk)
                self.assertEqual((result.code, result.report["status"]), (2, "UNKNOWN"))
                self.assertEqual(result.report["missing_env"], [missing])
                self.assertEqual(result.report["unmeasured"], ["vastdb_rows"])
                self.assertEqual(sdk.calls, [])
                self.assertIn(missing, result.stderr)

        sdk = FakeVastdb([row(COMPLETE)])
        result = self.run_step9({name: "  " for name in ENV_NAMES}, sdk)
        self.assertEqual(result.code, 2)
        self.assertEqual(result.report["missing_env"], list(cases))
        self.assertEqual(sdk.calls, [])

    def test_missing_sdk_package_is_named(self):
        result = self.run_step9(LIVE_ENV, modules={"vastdb": None})
        self.assertEqual((result.code, result.report["status"]), (2, "UNKNOWN"))
        self.assertEqual(result.report["missing_package"], "vastdb")
        self.assertEqual(result.report["unmeasured"], ["vastdb_rows"])
        self.assertIn("Python package vastdb is not importable", result.stderr)
        self.assertIn("pip install vastdb pyarrow", result.stderr)

        result = self.run_step9(LIVE_ENV, finder=MissingDependency("pyarrow"))
        self.assertEqual((result.code, result.report["status"]), (2, "UNKNOWN"))
        self.assertEqual(result.report["missing_package"], "pyarrow")
        self.assertIn("Python package pyarrow is not importable", result.stderr)

    def test_report_and_output_never_carry_config_values(self):
        error = RuntimeError(
            f"403 bucket={BUCKET} access={ACCESS} secret={SECRET} signed={quote(SECRET, safe='')} "
            f"query={quote(SECRET, safe='').lower()} peer={HOST} "
            f"HTTPConnectionPool(host='{HOST.lower()}', port=18080) url={ENDPOINT}/"
        )
        sdk = FakeVastdb([row(COMPLETE)], error=error)
        result = self.run_step9(LIVE_ENV, sdk)
        self.assertEqual(sdk.calls, [("connect", ENDPOINT, ACCESS, SECRET, False)])
        self.assertEqual((result.code, result.report["status"]), (2, "UNKNOWN"))
        self.assertEqual(result.report["error_type"], "RuntimeError")
        self.assertIn("<REDACTED>", result.report["message"])
        self.assertIn("port=18080", result.report["message"])
        self.assertEqual(result.report["hint"], step9.TUNNEL_HINT)

        result = self.run_step9(LIVE_ENV, FakeVastdb([row(COMPLETE)]))
        self.assertEqual((result.code, result.report["status"]), (0, "PASS"))
        self.assertIn("PASS", result.stdout)

    def test_missing_column_is_unknown(self):
        columns = [c for c in TABLE_COLUMNS if c != "location"]
        sdk = FakeVastdb([row(COMPLETE)], columns=columns)
        result = self.run_step9(LIVE_ENV, sdk)
        self.assertEqual((result.code, result.report["status"]), (2, "UNKNOWN"))
        self.assertEqual(result.report["missing_columns"], ["location"])
        self.assertEqual(result.report["available_columns"], sorted(columns))
        self.assertEqual(result.report["unmeasured"], ["vastdb_rows"])
        self.assertNotIn("select", [call[0] for call in sdk.calls])
        self.assertIn("lacks column(s) location", result.stderr)

    def test_sdk_calls_follow_the_skill_and_stay_read_only(self):
        sdk = FakeVastdb([row(COMPLETE)])
        result = self.run_step9(LIVE_ENV, sdk)
        self.assertEqual(result.code, 0)
        self.assertEqual(sdk.calls, [
            ("connect", ENDPOINT, ACCESS, SECRET, False),
            ("transaction",),
            ("bucket", BUCKET),
            ("schema", step9.SCHEMA),
            ("table", step9.TABLE),
            ("columns",),
            ("select", ["camera_id", "location", "reasoning_content"]),
            ("transaction_closed",),
        ])
        self.assertTrue(result.report["read_only"])

    def test_schema_and_table_match_the_official_config_example(self):
        repo = challenge_dir()
        if repo is None:
            self.skipTest("official challenge clone missing; set BUILDERS_CHALLENGE_DIR")
        text = (repo / "config.example").read_text(encoding="utf-8")
        values = {k: v.strip() for k, v in re.findall(r"^([A-Z][A-Z0-9_]*)=(.*)$", text, re.M)}
        self.assertEqual((values["VDB_SCHEMA"], values["VDB_COLLECTION"]), (step9.SCHEMA, step9.TABLE))

    def test_s3_endpoint_fallback_gets_a_scheme(self):
        env = dict(LIVE_ENV, VDB_ENDPOINT="  ", S3_ENDPOINT=f"{HOST}:18080")
        sdk = FakeVastdb([row(COMPLETE)])
        result = self.run_step9(env, sdk)
        self.assertEqual(result.code, 0)
        self.assertEqual(sdk.calls[0], ("connect", f"http://{HOST}:18080", ACCESS, SECRET, False))
        self.assertEqual(result.report["endpoint_env"], "S3_ENDPOINT")
        self.assertTrue(result.report["endpoint_scheme_added"])

    def test_entry_point_exit_codes_match_the_docstring(self):
        self.assertEqual(step9.EXIT_CODES, {"PASS": 0, "FAIL": 1, "UNKNOWN": 2})
        cases = (
            (LIVE_ENV, [row(COMPLETE)], 0, "PASS"),
            (LIVE_ENV, [row(COMPLETE, camera=PACK_C_CAMERA + "0")], 1, "FAIL"),
            ({}, [row(COMPLETE)], 2, "UNKNOWN"),
        )
        for env, rows, code, status in cases:
            with self.subTest(status=status):
                result = self.run_step9(env, FakeVastdb(rows), entry_point=True)
                self.assertEqual((result.code, result.report["status"]), (code, status))

    def test_unwritable_evidence_dir_is_unknown_not_fail(self):
        tmp = tempfile.TemporaryDirectory(prefix="scribner-step9-")
        self.addCleanup(tmp.cleanup)
        blocker = Path(tmp.name) / "not-a-dir"
        blocker.write_text("occupied", encoding="utf-8")
        result = self.run_step9(LIVE_ENV, FakeVastdb([row(COMPLETE)]), evidence_dir=blocker,
                                entry_point=True)
        self.assertEqual(result.code, 2)
        self.assertIsNone(result.report)
        self.assertIn("UNKNOWN", result.stderr)
        self.assertIn("FileExistsError", result.stderr)
        self.assertIn("not-a-dir", result.stderr)


if __name__ == "__main__":
    unittest.main()
