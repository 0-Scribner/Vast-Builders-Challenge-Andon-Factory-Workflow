#!/usr/bin/env python3
"""Verify Cosmos Reason, YOLO11, Embed1=256d, W&B inference and remote retrain logging."""
from __future__ import annotations

import argparse
import base64
import math
import os
import sys

import requests

from _common import PAYOFF_QUERY, repo_root, write_report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-url", default=os.environ.get("APP_URL", ""), help="Live Scribner URL; required for full W&B/retrain proof")
    args = ap.parse_args()

    mod = repo_root() / "tools" / "scribner"
    sys.path.insert(0, str(mod))
    import config  # type: ignore
    import gpu_client  # type: ignore
    from llm import prior_for, status as llm_status  # type: ignore

    headers = {"Accept": "application/json"}
    if config.GPU_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {config.GPU_BEARER_TOKEN}"

    result = {"status": "ok", "canary_called": False}

    # Cosmos health + real text inference.
    if not config.COSMOS3_REASON_URL:
        raise SystemExit("Missing COSMOS3_REASON_URL")
    cbase = config.COSMOS3_REASON_URL.rstrip("/")
    for p in ("/v1/models", "/v1/health/ready", "/v1/health/live"):
        r = requests.get(cbase + p, headers=headers, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise SystemExit(f"Cosmos health failed {p}: HTTP {r.status_code}")
    pong = gpu_client.cosmos_reason_complete("Reply with the single word: PONG", max_tokens=16).strip()
    if not pong:
        raise SystemExit("Cosmos Reason inference returned empty content")
    result["cosmos_reason"] = {"health": True, "inference_nonempty": True}

    # YOLO health + real inference on a verified live Scribner clip.
    yh = gpu_client.yolo_health()
    if yh.get("ok") is not True or yh.get("model_loaded") is not True:
        raise SystemExit("YOLO /healthz did not report ok=true and model_loaded=true")
    result["yolo"] = {"health": True, "model_loaded": True}
    if not args.app_url:
        raise SystemExit("--app-url is required for direct YOLO inference and W&B retrain proof")
    abase = args.app_url.rstrip("/")
    rows_r = requests.get(abase + "/api/units", timeout=30)
    rows_r.raise_for_status()
    rows = rows_r.json().get("units") or []
    if not rows:
        raise SystemExit("YOLO inference needs a live Scribner unit; run deliverable 5 first")
    detail_r = requests.get(abase + "/api/units/" + rows[0]["id"], timeout=30)
    detail_r.raise_for_status()
    detail = detail_r.json()
    if detail.get("mock") is not False:
        raise SystemExit("Refusing YOLO proof on a mock unit")
    clip = requests.get(abase + "/clip", params={"unit_id": detail["id"]}, timeout=180)
    clip.raise_for_status()
    payload = gpu_client.yolo_infer(base64.b64encode(clip.content).decode("ascii"), filename="pack-c-segment.mp4")
    if not isinstance(payload, dict):
        raise SystemExit("YOLO inference response malformed")
    result["yolo"]["inference"] = True
    result["yolo"]["flags"] = gpu_client.yolo_person_vehicle(payload)

    # Embed1 health + finite 256-dimensional assertion.
    if not config.COSMOS_EMBED1_URL:
        raise SystemExit("Missing COSMOS_EMBED1_URL")
    ebase = config.COSMOS_EMBED1_URL.rstrip("/")
    for p in ("/v1/models", "/v1/health/ready", "/v1/health/live"):
        r = requests.get(ebase + p, headers=headers, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise SystemExit(f"Embed1 health failed {p}: HTTP {r.status_code}")
    vec = gpu_client.embed_text(PAYOFF_QUERY)
    if len(vec) != 256 or any(type(x) not in (int, float) or not math.isfinite(float(x)) for x in vec):
        raise SystemExit("Embed1 did not return 256 finite numeric values")
    result["embed1"] = {"health": True, "dim": 256, "finite": True}

    # W&B must use an explicitly verified model from the assigned account.
    if not config.WANDB_API_KEY or not config.WANDB_TEAM or not config.WANDB_PROJECT:
        raise SystemExit("W&B proof requires WANDB_API_KEY, WANDB_TEAM, WANDB_PROJECT")
    if not os.environ.get("SCRIBNER_MODEL", "").strip():
        raise SystemExit("Set SCRIBNER_MODEL explicitly to a model verified accessible in the assigned W&B account")

    inspection = {
        "raw": "PERSON: YES; VEHICLE: forklift; MOTION: moving; DISTANCE: close; PATH_CLEAR: NO; NEAR_MISS: YES; HAZARD: person close to moving vehicle; UNCLEAR: NONE; CONFIDENCE: HIGH",
        "person": True,
        "vehicle_present": True,
        "motion": "moving",
        "distance": "close",
        "path_clear": False,
        "near_miss": True,
        "hazards": ["person close to moving vehicle"],
        "unclear": [],
        "confidence": "high",
        "inconsistent": False,
        "complete": False,
    }
    prior = prior_for(inspection, "warehouse-aisle")
    if prior.get("wandb_error") or llm_status().get("status") != "ok":
        raise SystemExit(f"W&B app-prior path did not complete: {llm_status().get('status')}")
    if float(prior.get("p_fail_prior") or 0.0) < 0.8:
        raise SystemExit("W&B prior weakened a near-miss below 0.8")
    result["wandb_inference"] = {"ok": True, "fail_closed": True, "source": prior.get("source")}

    import wandb  # type: ignore
    settings = wandb.Settings(init_timeout=20)
    run = wandb.init(
        project=config.WANDB_PROJECT,
        entity=config.WANDB_TEAM,
        job_type="smoke",
        reinit=True,
        mode="online",
        settings=settings,
    )
    wandb.log({"scribner_smoke": 1.0})
    run_id = str(run.id)
    run_path = f"{config.WANDB_TEAM}/{config.WANDB_PROJECT}/{run_id}"
    run.finish()
    api = wandb.Api(timeout=30)
    remote_smoke = api.run(run_path)
    if float((remote_smoke.summary or {}).get("scribner_smoke") or 0.0) != 1.0:
        raise SystemExit("W&B smoke run could not be read back remotely")
    result["wandb_sdk"] = {"ok": True, "run_id": run_id, "remote_readback": True}

    # Actual app retrain must report a successful tracking run, then prove it remotely.
    r = requests.post(abase + "/api/retrain", timeout=90)
    r.raise_for_status()
    retrain = r.json()
    tracking = retrain.get("wandb_tracking") or {}
    if tracking.get("status") != "ok" or not tracking.get("run_id"):
        raise SystemExit(f"App retrain W&B tracking failed: {tracking.get('status')}")
    retrain_path = f"{config.WANDB_TEAM}/{config.WANDB_PROJECT}/{tracking['run_id']}"
    remote = api.run(retrain_path)
    summary = remote.summary or {}
    required_numeric = ("andon_green", "andon_yellow", "andon_red", "n_labels")
    if not summary.get("andon_line") or any(not isinstance(summary.get(k), (int, float)) for k in required_numeric):
        raise SystemExit("Remote app retrain run missing andon_line or numeric andon metrics")
    result["wandb_retrain"] = {
        "ok": True,
        "run_id": tracking["run_id"],
        "andon_line": str(summary.get("andon_line")),
        "numeric_metrics": True,
        "remote_readback": True,
    }

    write_report("06_verify_gpu_wandb.json", result)
    print("OK GPU + W&B inference + remote tracking proof complete")


if __name__ == "__main__":
    main()
