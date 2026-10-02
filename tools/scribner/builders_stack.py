"""Official VAST Builders Challenge stack contract.

Source of truth (not this file):
https://github.com/vast-data/vast-builders-challenge

Scribner may only call the env vars, VSS routes, GPU NIMs, and deploy
pattern documented there. Re-extract with::

    BUILDERS_CHALLENGE_DIR=/path/to/vast-builders-challenge \\
      python3 scripts/extract_builders_stack.py

Agent note: never hardcode GPU hosts from skill examples. Never wire
Canary-1B into the kit gate (kits are silent; Canary is optional ASR).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

SOURCE_URL = "https://github.com/vast-data/vast-builders-challenge"
PINNED_COMMIT = "4987d8ebd8e5270dccf0864851a16ed42eb8d8e7"
CUSTOM_PROMPT_MAX = 800
EMBED_DIM = 256
DEPLOY_IMAGE = "python:3.12-slim"
DEPLOY_INGRESS_PATH = "/app"

# config.example on the challenge repo (the VM exports these).
CONFIG_EXAMPLE_ENV: List[str] = [
    "USERNAME",
    "PASSWORD",
    "S3_ENDPOINT",
    "ACCESS_KEY",
    "SECRET_KEY",
    "S3_CHUNKS_BUCKET",
    "S3_SEGMENTS_BUCKET",
    "VDB_ENDPOINT",
    "VASTDB_BUCKET",
    "VDB_SCHEMA",
    "VDB_COLLECTION",
    "VDB_PROMPTS_COLLECTION",
    "PIPELINE",
    "INGRESS_URL",
    "WANDB_API_KEY",
    "WANDB_TEAM",
    "WANDB_PROJECT",
    "COSMOS3_REASON_URL",
    "YOLO_URL",
    "COSMOS_EMBED1_URL",
    "CANARY_1B_URL",
    "COSMOS3_REASON_MODEL",
    "COSMOS_EMBED1_MODEL",
]

# From .cursor/skills/gpu (not listed in config.example, used by GPU skills).
GPU_SKILL_ENV: List[str] = ["GPU_BEARER_TOKEN"]

# From deployment/deploy-app-no-registry Secret keys (aliases of INGRESS_URL / USERNAME / PASSWORD).
DEPLOY_SECRET_ALIASES: List[str] = ["VSS_URL", "VSS_USERNAME", "VSS_PASSWORD"]

# W&B Inference base URL documented by BUILD_DAY.md → docs.wandb.ai/inference.
# Not a VSS route. Override only if W&B documents a different host.
WANDB_INFERENCE_DEFAULT = "https://api.inference.wandb.ai/v1"

# App-local knobs. Never treat these as VSS credentials.
APP_LOCAL_ENV: List[str] = [
    "HOST",
    "PORT",
    "SCRIBNER_MOCK",
    "SCRIBNER_PORT",
    "SCRIBNER_DATA_DIR",
    "SCRIBNER_AUDIT_FRACTION",
    "SCRIBNER_EPSILON",
    "SCRIBNER_DELTA",
    "SCRIBNER_RETRAIN_EVERY",
    "SCRIBNER_MODEL",
    "WANDB_INFERENCE_URL",
    "BUILDERS_CHALLENGE_DIR",
    "KIT_CLIPS_DIR",
    "KUBECONFIG",
    "PYTHONPATH",
]

ALLOWED_RUNTIME_ENV: Set[str] = set(
    CONFIG_EXAMPLE_ENV + GPU_SKILL_ENV + DEPLOY_SECRET_ALIASES + APP_LOCAL_ENV
)

# retrieval/README.md — routes that do NOT exist.
FORBIDDEN_VSS_PATHS: List[str] = [
    "/api/v1/reports",
    "/api/v1/alerts",
    "/api/v1/analytics",
    "/api/v1/videos/ask",
    "/api/v1/tags",
    "/api/v1/locations",
    "/api/v1/extra-metadata",
]

# Routes named in challenge skills (ingest/ + retrieval/ + gpu is separate).
ALLOWED_VSS_PATHS: List[str] = [
    "/api/v1/auth/login",
    "/api/v1/auth/me",
    "/api/v1/config",
    "/api/v1/search",
    "/api/v1/tools/search",
    "/api/v1/tools/segments",
    "/api/v1/tools/segment",
    "/api/v1/tools/detections",
    "/api/v1/tools/explore",
    "/api/v1/tools/synthesize",
    "/api/v1/agent/ask",
    "/api/v1/agent/search-and-answer",
    "/api/v1/metadata/schema",
    "/api/v1/metadata/values",
    "/api/v1/metadata/ingest-config",
    "/api/v1/dashboard/stats",
    "/api/v1/dashboard/reingest",
    "/api/v1/suggestions",
    "/api/v1/videos/explore",
    "/api/v1/videos/stream",
    "/api/v1/videos/playback-url",
    "/api/v1/videos/detections",
    "/api/v1/videos/metadata",
    "/api/v1/videos/synthesize",
    "/api/v1/videos/upload",
]

UPLOAD_FIELDS: List[str] = [
    "file",
    "is_public",
    "tags",
    "allowed_users",
    "scenario",
    "custom_prompt",
    "camera_id",
    "capture_type",
    "location",
]

GPU_PATHS = {
    "cosmos3_reason": ["/v1/models", "/v1/health/ready", "/v1/health/live", "/v1/chat/completions"],
    "yolo": ["/healthz", "/v1/infer"],
    "embed1": ["/v1/models", "/v1/health/ready", "/v1/health/live", "/v1/embeddings"],
    "canary_unused": ["/v1/health/ready", "/v1/health/live", "/v1/audio/transcriptions"],
}

CHALLENGE_SKILLS = [
    "ingest/upload-video",
    "ingest/reingest-videos",
    "ingest/reingest-chunk",
    "retrieval/login",
    "retrieval/search",
    "retrieval/videos",
    "retrieval/dashboard",
    "retrieval/list-metadata",
    "retrieval/agent-qa",
    "retrieval/suggest-prompts",
    "retrieval/vastdb-read",
    "gpu/model-health",
    "gpu/model-smoke-test",
    "deployment/deploy-app-no-registry",
    "submission",
    "ask-cosmos",
]

_API_RE = re.compile(r"/api/v1/[A-Za-z0-9_./-]+")
_ENV_ASSIGN_RE = re.compile(r"^([A-Z][A-Z0-9_]+)=", re.M)
_OS_ENV_RE = re.compile(r"os\.environ(?:\.get)?\(\s*[\"']([A-Z][A-Z0-9_]+)[\"']")
_DOCKER_RE = re.compile(r"\bdocker\s+(build|push|run)\b", re.I)
_YOUTUBE_RE = re.compile(r"youtube\.com|youtu\.be", re.I)
_GPU_HOST_RE = re.compile(r"166\.19\.38\.112")


def health_snapshot() -> Dict[str, Any]:
    return {
        "source": SOURCE_URL,
        "pinned_commit": PINNED_COMMIT,
        "custom_prompt_max": CUSTOM_PROMPT_MAX,
        "embed_dim": EMBED_DIM,
        "deploy_image": DEPLOY_IMAGE,
        "deploy_path": DEPLOY_INGRESS_PATH,
        "canary_wired": False,
        "forbidden_vss_paths": list(FORBIDDEN_VSS_PATHS),
    }


def lock_path() -> Path:
    return Path(__file__).resolve().parent / "builders_stack_lock.json"


def load_lock() -> Dict[str, Any]:
    path = lock_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dump_lock(data: Dict[str, Any], path: Optional[Path] = None) -> Path:
    out = path or lock_path()
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def challenge_dir() -> Optional[Path]:
    env = os.environ.get("BUILDERS_CHALLENGE_DIR", "").strip()
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(Path("/tmp/vast-builders-challenge"))
    for p in candidates:
        if (p / "config.example").is_file() and (p / "BUILD_DAY.md").is_file():
            return p
    return None


def extract_from_challenge(root: Path) -> Dict[str, Any]:
    """Parse a local clone of vast-builders-challenge into a comparable lock."""
    root = Path(root)
    config_text = (root / "config.example").read_text(encoding="utf-8")
    config_env = _ENV_ASSIGN_RE.findall(config_text)

    skill_files = list((root / ".cursor" / "skills").rglob("*.md"))
    skill_files += list((root / ".cursor" / "rules").rglob("*.mdc"))
    blobs = [p.read_text(encoding="utf-8", errors="replace") for p in skill_files]
    blobs.append((root / "BUILD_DAY.md").read_text(encoding="utf-8", errors="replace"))
    blobs.append((root / "ARCHITECTURE_REFERENCE.md").read_text(encoding="utf-8", errors="replace"))
    joined = "\n".join(blobs)

    api_paths = sorted({_normalize_api(m) for m in _API_RE.findall(joined)})
    gpu_token = "GPU_BEARER_TOKEN" in joined
    no_docker = "docker" in (root / ".cursor" / "skills" / "deployment" / "deploy-app-no-registry" / "SKILL.md").read_text(encoding="utf-8").lower()
    retrieval = (root / ".cursor" / "skills" / "retrieval" / "README.md").read_text(encoding="utf-8")
    forbidden = _forbidden_from_retrieval(retrieval)
    upload_skill = (root / ".cursor" / "skills" / "ingest" / "upload-video" / "SKILL.md").read_text(encoding="utf-8")
    prompt_max = 800
    m = re.search(r"custom_prompt_max_length[^\d]*(\d+)", upload_skill)
    if m:
        prompt_max = int(m.group(1))

    return {
        "source": SOURCE_URL,
        "config_example_env": config_env,
        "gpu_bearer_token_in_skills": gpu_token,
        "vss_paths_in_skills": api_paths,
        "forbidden_vss_paths": forbidden,
        "custom_prompt_max": prompt_max,
        "deploy_app_mentions_no_docker": no_docker,
        "deploy_image": DEPLOY_IMAGE,
        "deploy_path": DEPLOY_INGRESS_PATH,
    }


def _normalize_api(path: str) -> str:
    path = path.split("?")[0].rstrip(".")
    path = re.sub(r"/<[^>]+>", "", path)
    path = re.sub(r"/\{[^}]+\}", "", path)
    # job id suffix in dashboard/reingest/<job_id>
    if path.startswith("/api/v1/dashboard/reingest/") and path != "/api/v1/dashboard/reingest":
        path = "/api/v1/dashboard/reingest"
    return path


def _forbidden_from_retrieval(text: str) -> List[str]:
    found: List[str] = []
    m = re.search(r"No (`[^`]+`(,\s*)?)+", text)
    if not m:
        return list(FORBIDDEN_VSS_PATHS)
    names = re.findall(r"`(/[^`]+)`", m.group(0))
    for n in names:
        if n.startswith("/api/"):
            found.append(n)
        else:
            found.append("/api/v1" + n if n.startswith("/") else n)
    return found or list(FORBIDDEN_VSS_PATHS)


def scribner_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "AGENTS.md").is_file():
            return p
    return here.parents[1]


def iter_scribner_py() -> Iterable[Path]:
    root = scribner_root() / "tools" / "scribner"
    for p in root.rglob("*.py"):
        yield p


def iter_scribner_runtime_py() -> Iterable[Path]:
    for p in iter_scribner_py():
        if "tests" in p.parts:
            continue
        yield p


def vss_paths_in_scribner() -> Set[str]:
    found: Set[str] = set()
    for p in iter_scribner_runtime_py():
        if p.name == "builders_stack.py":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in _API_RE.findall(text):
            found.add(_normalize_api(m))
    return found


def env_names_in_scribner() -> Set[str]:
    found: Set[str] = set()
    for p in iter_scribner_runtime_py():
        text = p.read_text(encoding="utf-8", errors="replace")
        found.update(_OS_ENV_RE.findall(text))
    return found


def scan_scribner_violations() -> List[str]:
    """Return human-readable attacks that currently succeed (should be empty)."""
    hits: List[str] = []
    runtime_py = [
        p for p in iter_scribner_runtime_py() if p.name != "builders_stack.py"
    ]
    for p in runtime_py:
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = str(p.relative_to(scribner_root()))
        for bad in FORBIDDEN_VSS_PATHS:
            if bad in text:
                hits.append(f"{rel} invents forbidden VSS path {bad}")
        if _DOCKER_RE.search(text):
            hits.append(f"{rel} shells out to docker")
        if _GPU_HOST_RE.search(text):
            hits.append(f"{rel} hardcodes GPU_HOST 166.19.38.112 (use $COSMOS3_REASON_URL / $YOLO_URL / $COSMOS_EMBED1_URL)")
        if p.name in {"gpu_client.py", "vss_client.py", "scan.py", "llm.py", "main.py"}:
            if re.search(r"CANARY_1B_URL\s*\)", text) or "CANARY_1B_URL/" in text:
                hits.append(f"{rel} calls Canary-1B (not in the kit gate; optional ASR only)")
            if "/v1/audio/transcriptions" in text:
                hits.append(f"{rel} wires Canary ASR")
    for path in vss_paths_in_scribner():
        if path in FORBIDDEN_VSS_PATHS:
            hits.append(f"Scribner calls forbidden {path}")
        # Allow /api/v1/dashboard/reingest/<id> already normalized.
        allowed_prefixes = tuple(ALLOWED_VSS_PATHS)
        if path.startswith("/api/v1/") and not any(
            path == a or path.startswith(a + "/") for a in allowed_prefixes
        ):
            hits.append(f"Scribner calls undocumented VSS path {path}")
    for name in env_names_in_scribner():
        if name not in ALLOWED_RUNTIME_ENV:
            hits.append(f"Scribner reads non-stack env var {name}")
    return hits


def assert_subset_of_official(extracted: Dict[str, Any]) -> List[str]:
    """Compare this repo's lock/constants against a live challenge clone."""
    problems: List[str] = []
    official_env = set(extracted.get("config_example_env") or [])
    if official_env and set(CONFIG_EXAMPLE_ENV) != official_env:
        problems.append(
            "config.example env drift: "
            f"lock-only={sorted(set(CONFIG_EXAMPLE_ENV) - official_env)} "
            f"repo-only={sorted(official_env - set(CONFIG_EXAMPLE_ENV))}"
        )
    official_forbidden = set(extracted.get("forbidden_vss_paths") or [])
    if official_forbidden and not official_forbidden.issubset(set(FORBIDDEN_VSS_PATHS) | {p.replace("/api/v1", "") for p in FORBIDDEN_VSS_PATHS}):
        # Retrieval README lists short paths (/reports) not /api/v1/reports.
        short = {p.split("/api/v1", 1)[-1] if p.startswith("/api") else p for p in FORBIDDEN_VSS_PATHS}
        official_short = {p if p.startswith("/") else "/" + p for p in official_forbidden}
        if not official_short.issubset(short | set(FORBIDDEN_VSS_PATHS)):
            problems.append(f"forbidden-route drift vs retrieval README: {sorted(official_forbidden)}")
    if int(extracted.get("custom_prompt_max") or 0) not in {0, CUSTOM_PROMPT_MAX}:
        problems.append(f"custom_prompt_max drifted to {extracted.get('custom_prompt_max')}")
    return problems
