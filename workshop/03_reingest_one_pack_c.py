#!/usr/bin/env python3
"""Safely re-ingest exactly one Pack C parent/chunk with the generated path-safety prompt."""
from __future__ import annotations

import argparse
import time

from _common import (
    PACK_C_CAMERA,
    complete_parent,
    exact_pack_c,
    first_source,
    parent_id,
    require_live_env,
    schema_present,
    scribner_imports,
    write_report,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", help="Exact original_video or stream_id from --list")
    ap.add_argument("--list", action="store_true", help="List exact Pack C candidates and exit")
    ap.add_argument("--yes", action="store_true", help="Required to launch the re-ingest job")
    args = ap.parse_args()

    require_live_env()
    VssClient, prompt_for_kit = scribner_imports()
    client = VssClient()
    client.login()
    parents = [p for p in exact_pack_c(client.explore_all(scope="all")) if complete_parent(p)]
    if not parents:
        raise SystemExit(f"FAIL CLOSED: no exact complete {PACK_C_CAMERA} parents")

    if args.list or not args.target:
        for p in parents:
            print(
                f"{parent_id(p)}\tfile={p.get('filename')}\tstream={p.get('stream_id')}"
                f"\tsegments={len(p.get('timeline') or [])}\tlocation={p.get('location')}"
            )
        if not args.target:
            print("Choose one exact ID, then rerun with --target '<id>' --yes")
            return

    matches = [p for p in parents if args.target in {str(p.get("original_video") or ""), str(p.get("stream_id") or "")}]
    if len(matches) != 1:
        raise SystemExit(f"Target must resolve to exactly one Pack C parent; matches={len(matches)}")
    target = matches[0]
    if not args.yes:
        raise SystemExit("Dry stop: add --yes after reviewing the exact target")

    prompt = prompt_for_kit("warehouse-aisle")
    max_prompt = client.prompt_max()
    if len(prompt) > max_prompt:
        raise SystemExit(f"Generated prompt is {len(prompt)} chars > live max {max_prompt}")

    kwargs = {"chunk_count": 1, "custom_prompt": prompt}
    if target.get("original_video"):
        kwargs["original_video"] = str(target["original_video"])
    elif target.get("stream_id"):
        kwargs["stream_id"] = str(target["stream_id"])
    else:
        raise SystemExit("Target has neither original_video nor stream_id")

    job = client.reingest(**kwargs)
    job_id = str(job.get("job_id") or "")
    if not job_id:
        raise SystemExit("Re-ingest returned no job_id")

    last = {}
    deadline = time.time() + 30 * 60
    while time.time() < deadline:
        last = client.reingest_status(job_id)
        status = str(last.get("status") or "")
        print(
            f"status={status} chunks={last.get('completed_chunks')}/{last.get('total_chunks')} "
            f"clips={last.get('indexed_segments')}/{last.get('total_segments')}"
        )
        if status == "completed":
            break
        if status in {"failed", "error"}:
            raise SystemExit(f"Re-ingest failed: {status}")
        time.sleep(4)
    else:
        raise SystemExit("Timed out waiting for re-ingest")

    refreshed = exact_pack_c(client.explore_all(scope="all"))
    chosen = next((p for p in refreshed if parent_id(p) == parent_id(target)), target)
    src = first_source(chosen)
    meta = client.segment_metadata(src) if src else {}
    caption = str(meta.get("reasoning_content") or meta.get("caption") or meta.get("description") or "")
    fields = schema_present(caption)
    if not all(fields.values()):
        raise SystemExit(f"Completed job but caption schema incomplete: {fields}")

    write_report(
        "03_reingest_one_pack_c.json",
        {
            "status": "ok",
            "target": parent_id(target),
            "job_id": job_id,
            "prompt_chars": len(prompt),
            "selected_chunks": job.get("selected_chunks"),
            "copied_segments": job.get("copied_segments"),
            "final": {
                "completed_chunks": last.get("completed_chunks"),
                "total_chunks": last.get("total_chunks"),
                "indexed_segments": last.get("indexed_segments"),
                "total_segments": last.get("total_segments"),
            },
            "caption_schema": fields,
        },
    )
    print("OK one Pack C target re-ingested and schema verified")


if __name__ == "__main__":
    main()
