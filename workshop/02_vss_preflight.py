#!/usr/bin/env python3
"""Read-only VSS preflight for deliverable 2. Writes sanitized evidence only."""
from __future__ import annotations

from _common import (
    PACK_C_CAMERA,
    PACK_C_LOCATION,
    PAYOFF_QUERY,
    exact_pack_c,
    parent_id,
    require_live_env,
    scribner_imports,
    timeline_sources,
    write_report,
)


def main() -> None:
    require_live_env()
    VssClient, _ = scribner_imports()
    client = VssClient()

    token = client.login()
    if not token:
        raise SystemExit("VSS login returned no token")
    me = client.me()
    cfg = client.app_config()
    ingest_cfg = client.ingest_config()
    parents = client.explore_all(scope="all")
    pack_c = exact_pack_c(parents)
    if not pack_c:
        raise SystemExit(f"FAIL CLOSED: no exact {PACK_C_CAMERA}/{PACK_C_LOCATION} in Explore")

    pack_sources = {s for p in pack_c for s in timeline_sources(p)}
    search = client.search(PAYOFF_QUERY, top_k=50, min_similarity=0.3)
    hits = search.get("results") or search.get("chunk_results") or []
    verified_hits = 0
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        camera = str(hit.get("camera_id") or "")
        source = str(hit.get("source") or hit.get("preview_source") or "")
        if camera == PACK_C_CAMERA or source in pack_sources:
            verified_hits += 1

    sample = [
        {
            "id": parent_id(p),
            "filename": p.get("filename"),
            "camera_id": p.get("camera_id"),
            "location": p.get("location"),
            "stream_id": p.get("stream_id"),
            "segments": len(p.get("timeline") or []),
        }
        for p in pack_c[:20]
    ]
    result = {
        "status": "ok",
        "vss_login": True,
        "vss_me": bool(me),
        "vss_config": bool(cfg),
        "ingest_config": bool(ingest_cfg),
        "custom_prompt_max_length": ingest_cfg.get("custom_prompt_max_length"),
        "pack_c_camera": PACK_C_CAMERA,
        "pack_c_location": PACK_C_LOCATION,
        "pack_c_parent_count": len(pack_c),
        "pack_c_segment_sources": len(pack_sources),
        "pack_c_sample": sample,
        "payoff_query": PAYOFF_QUERY,
        "payoff_result_count": len(hits),
        "payoff_verified_pack_c_hits": verified_hits,
        "payoff_status": "verified_hits" if verified_hits else "no_verified_hits_before_reingest",
    }
    write_report("02_vss_preflight.json", result)
    print(
        f"OK exact Pack C parents={len(pack_c)} segments={len(pack_sources)} "
        f"verified_payoff_hits={verified_hits}"
    )


if __name__ == "__main__":
    main()
