#!/usr/bin/env python3
"""Read-only VastDB evidence: exact Pack C index rows and their caption schema fields.

Uses only the vastdb SDK reads documented in the retrieval/vastdb-read skill. Never
writes to VastDB or S3 and never prints credential values. Exit 0 PASS, 1 FAIL
(measured, but no Pack C rows or no Pack C caption with every field), 2 UNKNOWN
(could not measure).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlsplit

# Schema and table names are the retrieval/vastdb-read skill defaults.
SCHEMA = "vss-schema"
TABLE = "vss-collection"
COLUMNS = ("camera_id", "location", "reasoning_content")
CAPTION_FIELDS = ("PATH_CLEAR:", "NEAR_MISS:", "UNCLEAR:", "CONFIDENCE:")
REDACTED_ENV = ("ACCESS_KEY", "SECRET_KEY", "VDB_ENDPOINT", "S3_ENDPOINT", "VASTDB_BUCKET")
REPORT_NAME = "09_vastdb_read.json"
EXIT_CODES = {"PASS": 0, "FAIL": 1, "UNKNOWN": 2}
TUNNEL_HINT = (
    "If the VastDB VIP is not routable from this host, open the SSH tunnel from the "
    "retrieval/vastdb-read skill and set VDB_ENDPOINT=http://127.0.0.1:18080."
)


def pack_c_constants() -> Tuple[str, str]:
    scribner_dir = Path(__file__).resolve().parents[1] / "tools" / "scribner"
    if not (scribner_dir / "kits.py").is_file():
        raise LookupError("tools/scribner/kits.py not found; run from a Scribner checkout")
    if str(scribner_dir) not in sys.path:
        sys.path.insert(0, str(scribner_dir))
    from kits import PACK_C_CAMERA, PACK_C_LOCATION

    return PACK_C_CAMERA, PACK_C_LOCATION


def read_env() -> Tuple[Dict[str, str], List[str]]:
    endpoint_env = "VDB_ENDPOINT" if os.environ.get("VDB_ENDPOINT", "").strip() else "S3_ENDPOINT"
    env = {
        "endpoint_env": endpoint_env,
        "endpoint": os.environ.get(endpoint_env, "").strip(),
        "access": os.environ.get("ACCESS_KEY", "").strip(),
        "secret": os.environ.get("SECRET_KEY", "").strip(),
        "bucket": os.environ.get("VASTDB_BUCKET", "").strip(),
    }
    required = (
        ("VDB_ENDPOINT or S3_ENDPOINT", "endpoint"),
        ("ACCESS_KEY", "access"),
        ("SECRET_KEY", "secret"),
        ("VASTDB_BUCKET", "bucket"),
    )
    return env, [name for name, key in required if not env[key]]


def redaction_values() -> List[str]:
    values = {os.environ.get(name, "").strip() for name in REDACTED_ENV}
    # Connection errors print the endpoint host and port, not the configured URL.
    for name in ("VDB_ENDPOINT", "S3_ENDPOINT"):
        raw = os.environ.get(name, "").strip()
        try:
            parts = urlsplit(raw if "://" in raw else "http://" + raw)
        except ValueError:
            continue
        values |= {parts.netloc, parts.hostname or ""}
    values |= {quote(value, safe="") for value in values}
    return sorted((v for v in values if v), key=len, reverse=True)


def redact(text: str) -> str:
    for value in redaction_values():
        text = re.sub(re.escape(value), "<REDACTED>", text, flags=re.IGNORECASE)
    return text[:500]


def write_report(report: Dict[str, Any]) -> Path:
    out = Path(os.environ.get("SCRIBNER_EVIDENCE_DIR") or "/tmp/scribner-live-evidence")
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_NAME
    tmp = out / (REPORT_NAME + ".tmp")
    body = json.dumps({"ts_epoch": int(time.time()), **report}, indent=2, sort_keys=True)
    tmp.write_text(body + "\n", encoding="utf-8")
    os.replace(tmp, path)
    print(f"report={path}")
    return path


def finish(report: Dict[str, Any], status: str, message: str, hint: str = "", **fields: Any) -> int:
    message = redact(message)
    report.update(fields, status=status, message=message)
    if hint:
        report["hint"] = hint
    write_report(report)
    stream = sys.stdout if status == "PASS" else sys.stderr
    print(f"{status} {message}", file=stream)
    if hint:
        print(hint, file=stream)
    return EXIT_CODES[status]


def read_rows(vastdb: Any, env: Dict[str, str]) -> Tuple[List[str], Optional[List[Dict[str, Any]]]]:
    session = vastdb.connect(
        endpoint=env["endpoint"], access=env["access"], secret=env["secret"], ssl_verify=False
    )
    with session.transaction() as tx:
        table = tx.bucket(env["bucket"]).schema(SCHEMA).table(TABLE)
        names = [column.name for column in table.columns()]
        if any(name not in names for name in COLUMNS):
            return names, None
        rows = table.select(columns=list(COLUMNS)).read_all().to_pylist()
    return names, rows


def count_rows(rows: List[Dict[str, Any]], camera: str, location: str) -> Dict[str, Any]:
    pack_c = [r for r in rows if r.get("camera_id") == camera and r.get("location") == location]
    field_counts = {field: 0 for field in CAPTION_FIELDS}
    complete = 0
    for row in pack_c:
        caption = str(row.get("reasoning_content") or "").upper()
        present = [field in caption for field in CAPTION_FIELDS]
        for field, hit in zip(CAPTION_FIELDS, present):
            field_counts[field] += int(hit)
        complete += int(all(present))
    return {
        "total_rows": len(rows),
        "pack_c_rows": len(pack_c),
        "pack_c_caption_field_counts": field_counts,
        "pack_c_rows_with_all_fields": complete,
    }


def main() -> int:
    report: Dict[str, Any] = {
        "script": "09_vastdb_read",
        "read_only": True,
        "schema": SCHEMA,
        "table": TABLE,
        "caption_fields": list(CAPTION_FIELDS),
    }
    try:
        camera, location = pack_c_constants()
    except (LookupError, ImportError) as exc:
        return finish(report, "UNKNOWN", str(exc), unmeasured=["pack_c_constants"])
    report.update(pack_c_camera=camera, pack_c_location=location)

    env, missing = read_env()
    if missing:
        return finish(
            report,
            "UNKNOWN",
            "missing environment "
            + ", ".join(missing)
            + ". On the workshop VM source the single /config/<team>.config first.",
            missing_env=missing,
            unmeasured=["vastdb_rows"],
        )
    scheme_added = not env["endpoint"].startswith(("http://", "https://"))
    if scheme_added:
        env["endpoint"] = "http://" + env["endpoint"]
    report.update(endpoint_env=env["endpoint_env"], endpoint_scheme_added=scheme_added)

    try:
        import vastdb
    except ImportError as exc:
        package = (exc.name or "vastdb").split(".")[0]
        return finish(
            report,
            "UNKNOWN",
            f"Python package {package} is not importable ({exc}). "
            "Install it with: pip install vastdb pyarrow",
            missing_package=package,
            unmeasured=["vastdb_rows"],
        )

    try:
        names, rows = read_rows(vastdb, env)
    except Exception as exc:
        return finish(
            report,
            "UNKNOWN",
            f"VastDB read failed: {type(exc).__name__}: {exc}",
            hint=TUNNEL_HINT,
            error_type=type(exc).__name__,
            unmeasured=["vastdb_rows"],
        )
    if rows is None:
        absent = [name for name in COLUMNS if name not in names]
        return finish(
            report,
            "UNKNOWN",
            f"{TABLE} lacks column(s) {', '.join(absent)}; see available_columns in the report",
            missing_columns=absent,
            available_columns=sorted(names),
            unmeasured=["vastdb_rows"],
        )

    counts = count_rows(rows, camera, location)
    checks = {
        "pack_c_rows_present": counts["pack_c_rows"] > 0,
        "pack_c_caption_with_all_fields": counts["pack_c_rows_with_all_fields"] > 0,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    fields = " ".join(
        f"{name[:-1]}={n}" for name, n in counts["pack_c_caption_field_counts"].items()
    )
    summary = (
        f"total_rows={counts['total_rows']} pack_c_rows={counts['pack_c_rows']} {fields} "
        f"all_fields={counts['pack_c_rows_with_all_fields']}"
    )
    return finish(report, status, summary, checks=checks, unmeasured=[], **counts)


def run() -> int:
    try:
        return main()
    except Exception as exc:
        # Python exits 1 on an uncaught exception, and 1 means a measured FAIL here.
        message = redact(f"unexpected {type(exc).__name__}: {exc}")
        print(f"UNKNOWN {message}", file=sys.stderr)
        return EXIT_CODES["UNKNOWN"]


if __name__ == "__main__":
    raise SystemExit(run())
