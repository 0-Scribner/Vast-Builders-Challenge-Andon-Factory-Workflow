#!/usr/bin/env python3
"""Sanitized connection and app checks; no ingest or review writes.

Exit 0: requested checks passed; 1: at least one failed; 2: missing prerequisites.
Connection success is NOT proof of re-ingest, SDK logging, or browser playback.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
from urllib.parse import quote, urlsplit

import requests

CAMERA = "sdg_warehouse_cam-2"
QUERY = "person close to a moving vehicle"


class CheckFailure(Exception):
    """Only fixed, credential-free reason codes may be used here."""


def require(condition, code):
    if not condition:
        raise CheckFailure(code)


def request(method, url, **kwargs):
    parts = urlsplit(url)
    require(parts.scheme in {"http", "https"} and parts.hostname and
            not parts.username and not parts.password, "invalid_service_url")
    r = requests.request(method, url, timeout=(5, 20), allow_redirects=False, **kwargs)
    require(r.status_code == 200, "http_" + str(r.status_code))
    return r


def json_request(method, url, **kwargs):
    return request(method, url, **kwargs).json()


class Results:
    def __init__(self):
        self.rows = []

    def skip(self, name, reason):
        self.rows.append({"check": name, "status": "skipped", "reason": reason})

    def check(self, name, op):
        try:
            value = op()
        except Exception as exc:
            # Never print exception messages from HTTP/SDK clients: they can contain secrets.
            reason = str(exc) if isinstance(exc, CheckFailure) else type(exc).__name__
            self.rows.append({"check": name, "status": "fail", "reason": reason})
            return False, None
        self.rows.append({"check": name, "status": "ok"})
        return True, value

    def exit_code(self):
        if any(r["status"] == "fail" for r in self.rows):
            return 1
        return 2 if any(r["status"] == "skipped" for r in self.rows) else 0


def inventory(fetch):
    """Reject incomplete/unknown pagination rather than claim a full inventory."""
    rows, expected = [], None
    for offset in range(0, 10000, 100):
        page = fetch(offset)
        require(isinstance(page, dict), "explore_schema")
        total = page.get("total")
        require(type(total) is int and total >= 0, "explore_total")
        if expected is None:
            expected = total
        require(total == expected, "explore_changed_during_scan")
        batch = next((page[k] for k in ("items", "results", "videos") if k in page), None)
        require(isinstance(batch, list) and all(isinstance(x, dict) for x in batch),
                "explore_rows")
        rows.extend(batch)
        require(len(rows) <= expected, "explore_count_mismatch")
        if len(rows) == expected:
            # Parent chunks, not segments, are what Explore enumerates.
            ids = [x.get("original_video") or x.get("id") for x in rows]
            require(all(isinstance(x, str) and x for x in ids) and len(set(ids)) == len(ids),
                    "explore_duplicate_or_missing_parent")
            return rows
        require(len(batch) == 100, "explore_incomplete_page")
    raise CheckFailure("explore_inventory_limit")


def pack_c(rows):
    selected = [r for r in rows if r.get("camera_id") == CAMERA]
    require(bool(selected), "pack_c_missing")
    require(all(r.get("location") == "warehouse3" for r in selected), "pack_c_location")
    return selected


def search_hits(payload):
    require(isinstance(payload, dict), "search_schema")
    rows = payload.get("results")
    require(isinstance(rows, list) and bool(rows), "search_no_segments")
    require(all(isinstance(r, dict) and isinstance(r.get("source"), str) and
                r["source"] for r in rows), "search_source_missing")
    return rows


def vss_checks(results, env):
    names = ("vss_login", "vss_me", "vss_config", "vss_ingest_config",
             "vss_explore_pack_c", "vss_payoff_search")
    # Match tools/scribner/config.py so the probe checks the app's actual backend.
    base = (env.get("VSS_URL") or env.get("INGRESS_URL") or "").rstrip("/")
    user = env.get("VSS_USERNAME") or env.get("USERNAME")
    password = env.get("VSS_PASSWORD") or env.get("PASSWORD")
    if not all((base, user, password)):
        for name in names:
            results.skip(name, "missing_VSS_URL_or_credentials")
        return

    def login():
        data = json_request("POST", base + "/api/v1/auth/login",
                            json={"username": user, "password": password})
        require(isinstance(data, dict) and isinstance(data.get("access_token"), str)
                and data["access_token"], "login_token_missing")
        return data["access_token"]

    ok, token = results.check(names[0], login)
    if not ok:
        for name in names[1:]:
            results.skip(name, "login_failed")
        return
    headers = {"Authorization": "Bearer " + token}

    def get(path, **kwargs):
        return json_request("GET", base + "/api/v1/" + path, headers=headers, **kwargs)

    def me():
        data = get("auth/me")
        require(isinstance(data, dict) and data.get("username") == user, "identity_mismatch")

    def config_check(path):
        data = get(path)
        require(isinstance(data, dict) and bool(data), "empty_config")
        return data

    results.check(names[1], me)
    results.check(names[2], lambda: config_check("config"))
    results.check(names[3], lambda: config_check("metadata/ingest-config"))
    ok, parents = results.check(names[4], lambda: pack_c(inventory(
        lambda offset: get("videos/explore", params={"scope": "all", "limit": 100, "offset": offset}))))

    def search():
        rows = search_hits(json_request("POST", base + "/api/v1/search", headers=headers,
            json={"query": QUERY, "top_k": 5, "min_similarity": 0.3,
                  "include_public": True, "metadata_filters": {"camera_id": CAMERA}}))
        require(ok, "pack_c_inventory_unverified")
        sources = set()
        for parent in parents:
            if parent.get("preview_source"):
                sources.add(parent["preview_source"])
            for segment in parent.get("timeline") or []:
                if isinstance(segment, dict) and segment.get("source"):
                    sources.add(segment["source"])
        # A requested filter alone is not evidence of a hit's camera.
        for row in rows:
            camera = row.get("camera_id")
            require(camera == CAMERA or (camera is None and row["source"] in sources),
                    "search_camera_unverified")

    results.check(names[5], search)


def gpu_health(base, model, token):
    # GPU_BEARER_TOKEN is optional; Authorization is sent only when it is set.
    headers = {"Authorization": "Bearer " + token} if token else {}
    if model == "yolo":
        data = json_request("GET", base + "/healthz", headers=headers)
        require(isinstance(data, dict) and data.get("ok") is True and
                data.get("model_loaded") is True, "yolo_not_ready")
        return
    data = json_request("GET", base + "/v1/models", headers=headers)
    require(isinstance(data, dict) and isinstance(data.get("data"), list) and
            data["data"] and all(isinstance(x, dict) and isinstance(x.get("id"), str)
                                  and x["id"] for x in data["data"]), "models_missing")
    for path in ("ready", "live"):
        request("GET", base + "/v1/health/" + path, headers=headers)


def gpu_checks(results, env):
    for name, variable in (("cosmos_reason", "COSMOS3_REASON_URL"),
                           ("yolo", "YOLO_URL"), ("embed1", "COSMOS_EMBED1_URL")):
        if not env.get(variable):
            results.skip(name + "_health", "missing_" + variable)
        else:
            results.check(name + "_health", lambda n=name, v=variable:
                          gpu_health(env[v].rstrip("/"), n, env.get("GPU_BEARER_TOKEN", "")))


def wandb_check(results, env):
    if not all(env.get(k) for k in ("WANDB_API_KEY", "WANDB_TEAM", "WANDB_PROJECT", "SCRIBNER_MODEL")):
        results.skip("wandb_inference", "missing_WANDB_credentials_project_or_verified_SCRIBNER_MODEL")
        return

    def infer():
        from openai import OpenAI
        base = "https://api.inference.wandb.ai/v1"
        require((env.get("WANDB_INFERENCE_URL") or base).rstrip("/") == base,
                "nonworkshop_wandb_endpoint")
        with OpenAI(base_url=base, api_key=env["WANDB_API_KEY"], timeout=20, max_retries=0,
                    project=env["WANDB_TEAM"] + "/" + env["WANDB_PROJECT"]) as client:
            response = client.chat.completions.create(model=env["SCRIBNER_MODEL"],
                max_tokens=16, messages=[{"role": "user", "content": "Reply with PONG."}])
            require(bool(response.choices) and bool(response.choices[0].message.content),
                    "inference_empty")
    results.check("wandb_inference", infer)


def embedding_valid(vector):
    require(isinstance(vector, list) and len(vector) == 256 and
            all(type(x) in (int, float) and math.isfinite(x) for x in vector), "embedding_invalid")


def app_check(base, expected):
    base = base.rstrip("/")
    get = lambda path, **kwargs: json_request("GET", base + path, **kwargs)
    h, board = get("/health"), get("/api/andon")
    require(h.get("mock") is (expected == "mock"), "wrong_app_mode")
    require(h.get("product") == "warehouse-near-miss" and h.get("line") == "primary"
            and h.get("corpus") == "provided", "wrong_product")
    require(h.get("stack", {}).get("canary_wired") is False and
            h.get("stack", {}).get("source") == "https://github.com/vast-data/vast-builders-challenge",
            "wrong_stack")
    require(board.get("board") == "andon" and board.get("name_ja") == "安灯" and
            board.get("gemba") == "現場" and board.get("camera_id") == CAMERA and
            board.get("rule") == "赤灯は人なしで緑にしない", "wrong_board")
    report = request("GET", base + "/api/report").text
    lines = re.findall(r"^- 安灯 ANDON line: \*\*(.*?)\*\*", report, flags=re.M)
    require(lines == [board.get("line_ja")], "report_line_mismatch")
    rows = get("/api/units").get("units")
    require(isinstance(rows, list) and bool(rows), "no_units")
    ids = [u.get("id") for u in rows]
    require(all(isinstance(x, str) and x for x in ids) and len(set(ids)) == len(ids), "duplicate_unit_ids")
    if expected == "mock":
        require(len(rows) == 40, "mock_unit_count")
        require({u.get("decision", {}).get("decision") for u in rows} >=
                {"AUTO_ALERT", "HOLD", "AUTO_CLEAR"}, "mock_lamp_fixture_missing")
    sources = []
    for row in rows:
        detail = get("/api/units/" + quote(row["id"], safe=""))
        require(detail.get("mock") is (expected == "mock"), "unit_mode_mismatch")
        if expected == "live":
            require(detail.get("camera_id") == CAMERA and detail.get("location") == "warehouse3",
                    "unit_camera_mismatch")
            require(isinstance(detail.get("source"), str) and detail["source"], "unit_source_missing")
            sources.append(detail["source"])
        if (row.get("decision") or {}).get("decision") == "AUTO_ALERT":
            lamp = get("/api/andon", params={"unit_id": row["id"]})
            require(lamp.get("station_lamp") == "red", "alert_lamp_not_red")
    require(len(sources) == len(set(sources)), "duplicate_live_sources")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("connections")
    app = sub.add_parser("app")
    app.add_argument("--url", required=True)
    app.add_argument("--expect", choices=("mock", "live"), required=True)
    args = parser.parse_args()
    results = Results()
    if args.command == "connections":
        vss_checks(results, os.environ)
        gpu_checks(results, os.environ)
        wandb_check(results, os.environ)
    else:
        results.check("app_contract_" + args.expect, lambda: app_check(args.url, args.expect))
    print(json.dumps(results.rows, indent=2))
    return results.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
