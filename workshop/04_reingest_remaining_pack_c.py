#!/usr/bin/env python3
"""Sequentially expand Pack C re-ingest after deliverable 3 is verified."""
from __future__ import annotations

import argparse
import time

from _common import PACK_C_CAMERA, complete_parent, exact_pack_c, parent_id, require_live_env, scribner_imports, write_report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verified-one-chunk", action="store_true", help="Required safety acknowledgement")
    ap.add_argument("--yes", action="store_true", help="Required to mutate VSS")
    ap.add_argument("--limit", type=int, default=0, help="Maximum parents this run; 0 means all")
    ap.add_argument("--skip-target", action="append", default=[], help="Exact ID already verified; repeatable")
    args = ap.parse_args()
    if not (args.verified_one_chunk and args.yes):
        raise SystemExit("Refusing bulk re-ingest. Require --verified-one-chunk --yes")

    require_live_env()
    VssClient, prompt_for_kit = scribner_imports()
    client = VssClient()
    client.login()
    parents = [p for p in exact_pack_c(client.explore_all(scope="all")) if complete_parent(p)]
    if not parents:
        raise SystemExit(f"FAIL CLOSED: no exact complete {PACK_C_CAMERA} parents")

    prompt = prompt_for_kit("warehouse-aisle")
    if len(prompt) > client.prompt_max():
        raise SystemExit("Generated prompt exceeds live VSS limit")

    seen = set(args.skip_target)
    targets = []
    for p in parents:
        pid = parent_id(p)
        if not pid or pid in seen:
            continue
        seen.add(pid)
        targets.append(p)
    if args.limit > 0:
        targets = targets[: args.limit]

    report = {"status": "running", "camera_id": PACK_C_CAMERA, "prompt_chars": len(prompt), "jobs": []}
    for idx, p in enumerate(targets, start=1):
        pid = parent_id(p)
        kwargs = {"chunk_count": 1, "custom_prompt": prompt}
        if p.get("original_video"):
            kwargs["original_video"] = str(p["original_video"])
        elif p.get("stream_id"):
            kwargs["stream_id"] = str(p["stream_id"])
        else:
            report["jobs"].append({"target": pid, "status": "skipped_no_stable_id"})
            continue
        print(f"[{idx}/{len(targets)}] start {pid}")
        job = client.reingest(**kwargs)
        job_id = str(job.get("job_id") or "")
        if not job_id:
            raise SystemExit(f"No job_id for {pid}")
        deadline = time.time() + 30 * 60
        final = {}
        while time.time() < deadline:
            final = client.reingest_status(job_id)
            st = str(final.get("status") or "")
            if st == "completed":
                break
            if st in {"failed", "error"}:
                raise SystemExit(f"Job {job_id} failed for {pid}")
            time.sleep(4)
        else:
            raise SystemExit(f"Timed out job {job_id} for {pid}")
        report["jobs"].append(
            {
                "target": pid,
                "job_id": job_id,
                "status": "completed",
                "indexed_segments": final.get("indexed_segments"),
                "total_segments": final.get("total_segments"),
            }
        )

    report["status"] = "ok"
    report["completed_jobs"] = sum(1 for j in report["jobs"] if j.get("status") == "completed")
    write_report("04_reingest_remaining_pack_c.json", report)
    print(f"OK completed sequential jobs={report['completed_jobs']}")


if __name__ == "__main__":
    main()
