#!/usr/bin/env python3
"""Prove Scribner is using real Pack C footage and fail closed on provenance."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

from _common import (
    PACK_C_CAMERA,
    exact_pack_c,
    schema_complete,
    scribner_imports,
    timeline_sources,
    write_report,
)


def u(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-url", default="http://127.0.0.1:8082")
    args = ap.parse_args()
    base = args.app_url.rstrip("/")
    s = requests.Session()

    scan = s.post(u(base, "api/scan"), timeout=180)
    scan.raise_for_status()
    health_response = s.get(u(base, "health"), timeout=30)
    health_response.raise_for_status()
    health = health_response.json()
    if health.get("mock") is not False:
        raise SystemExit("FAIL: app reports mock=true")
    if health.get("live_configured") is not True:
        raise SystemExit("FAIL: live app reports VSS configuration unavailable")
    if health.get("camera_id") != PACK_C_CAMERA:
        raise SystemExit(f"FAIL: health camera_id={health.get('camera_id')} != {PACK_C_CAMERA}")

    VssClient, _ = scribner_imports()
    vss = VssClient()
    verified_sources = {
        src
        for p in exact_pack_c(vss.explore_all(scope="all"))
        for src in timeline_sources(p)
    }
    if not verified_sources:
        raise SystemExit("FAIL CLOSED: VSS inventory produced zero exact Pack C segment sources")

    units_response = s.get(u(base, "api/units"), timeout=30)
    units_response.raise_for_status()
    rows = units_response.json().get("units") or []
    if not rows:
        raise SystemExit("FAIL CLOSED: live scan produced zero units")

    details = []
    seen_sources = set()
    for row in rows:
        response = s.get(u(base, f"api/units/{row['id']}"), timeout=30)
        response.raise_for_status()
        d = response.json()
        if d.get("mock") is not False:
            raise SystemExit(f"FAIL: live unit {row['id']} is marked mock")
        if d.get("camera_id") != PACK_C_CAMERA:
            raise SystemExit(f"FAIL: unit {row['id']} camera={d.get('camera_id')}")
        source = str(d.get("source") or "")
        if not source:
            raise SystemExit(f"FAIL: live unit {row['id']} has no segment source")
        if source not in verified_sources:
            raise SystemExit(f"FAIL: unit {row['id']} source is not in verified Pack C inventory")
        if source in seen_sources:
            raise SystemExit(f"FAIL: duplicate live source {source}")
        seen_sources.add(source)
        if not d.get("scan_pairing_complete"):
            raise SystemExit(f"FAIL: source/caption pairing incomplete for {row['id']}")
        if not schema_complete(str(d.get("caption") or "")):
            raise SystemExit(f"FAIL: caption schema incomplete for {row['id']}")
        details.append(d)

    chosen = next(
        (d for d in details if (d.get("decision_row") or {}).get("decision") == "AUTO_ALERT"),
        details[0],
    )
    decision = (chosen.get("decision_row") or {}).get("decision") or "HOLD"
    expected_lamp = "red" if decision in {"AUTO_ALERT", "AUTO_FAIL"} else "green" if decision in {"AUTO_CLEAR", "AUTO_PASS"} else "yellow"
    board_response = s.get(u(base, "api/andon"), params={"unit_id": chosen["id"]}, timeout=30)
    board_response.raise_for_status()
    board = board_response.json()
    if board.get("station_lamp") != expected_lamp:
        raise SystemExit(f"FAIL: station lamp {board.get('station_lamp')} != {expected_lamp}")

    # Empty source query must fall back to unit.source server-side and return the same VSS bytes.
    clip = s.get(u(base, "clip"), params={"unit_id": chosen["id"]}, timeout=180)
    clip.raise_for_status()
    if "video/mp4" not in (clip.headers.get("content-type") or "").lower() or len(clip.content) <= 1024:
        raise SystemExit("FAIL: /clip did not return a nontrivial MP4")
    direct = vss.stream_bytes(str(chosen["source"]))
    same_bytes = hashlib.sha256(clip.content).digest() == hashlib.sha256(direct).digest()
    if not same_bytes:
        raise SystemExit("FAIL: Scribner /clip bytes differ from the verified VSS source")

    decoded = None
    if shutil.which("ffmpeg"):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(clip.content)
            tmp = Path(f.name)
        try:
            p = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(tmp), "-f", "null", "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            decoded = p.returncode == 0
            if not decoded:
                raise SystemExit("FAIL: ffmpeg could not decode live /clip")
        finally:
            tmp.unlink(missing_ok=True)

    checks = {}
    hold = next((d for d in details if (d.get("decision_row") or {}).get("decision") == "HOLD"), None)
    if hold:
        r = s.post(
            u(base, "api/review"),
            json={"unit_id": hold["id"], "verdict": "CLEAR", "reason": "agree", "gate_ok": True},
            timeout=30,
        )
        checks["hold_gate_ok_rejected"] = r.status_code == 400
        if r.status_code != 400:
            raise SystemExit("FAIL: HOLD accepted gate_ok=true")
    alert = next((d for d in details if (d.get("decision_row") or {}).get("decision") == "AUTO_ALERT"), None)
    if alert:
        r = s.post(
            u(base, "api/review"),
            json={"unit_id": alert["id"], "verdict": "CLEAR", "reason": "vlm_false_alert", "confirm_escape": False},
            timeout=30,
        )
        checks["alert_clear_without_confirm_rejected"] = r.status_code == 400
        if r.status_code != 400:
            raise SystemExit("FAIL: AUTO_ALERT -> CLEAR escaped without confirmation")

    report_response = s.get(u(base, "api/report"), timeout=30)
    report_response.raise_for_status()
    report_text = report_response.text
    if str(board.get("line_ja") or "") not in report_text:
        raise SystemExit("FAIL: shift report line lamp disagrees with /api/andon")

    write_report(
        "05_verify_live_scribner.json",
        {
            "status": "ok",
            "app_url": base,
            "unit_count": len(details),
            "unique_sources": len(seen_sources),
            "chosen_unit": chosen["id"],
            "chosen_decision": decision,
            "station_lamp": board.get("station_lamp"),
            "clip_bytes": len(clip.content),
            "clip_matches_vss_bytes": same_bytes,
            "ffmpeg_decode": decoded,
            "camera_id": PACK_C_CAMERA,
            "adversarial": checks,
            "report_line_matches_andon": True,
        },
    )
    print(f"OK live Pack C units={len(details)} clip_bytes={len(clip.content)} lamp={board.get('station_lamp')}")
    print("MANUAL BROWSER CHECK STILL REQUIRED: LIVE indicator, playback, and all requests remain under /app when deployed.")


if __name__ == "__main__":
    main()
