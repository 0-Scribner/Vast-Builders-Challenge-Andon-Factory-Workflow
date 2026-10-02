"""Environment and paths.

Agent note: credentials come from the process environment (K8s Secret or
``/config/<team>.config`` sourced on the VM). Never interpolate secret
values into logs, HTML, or git.
"""

from __future__ import annotations

import os
from pathlib import Path


def _truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


# Local / tests: no VSS. Workshop pod: leave unset or 0.
MOCK = _truthy("SCRIBNER_MOCK", "0")

# FastAPI bind. Ingress rewrites /app -> / so the app serves at /.
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("SCRIBNER_PORT", "8080")))

# VSS backend. Prefer the names the deploy skill injects.
VSS_URL = (
    os.environ.get("VSS_URL")
    or os.environ.get("INGRESS_URL")
    or ""
).rstrip("/")
VSS_USERNAME = os.environ.get("VSS_USERNAME") or os.environ.get("USERNAME") or ""
VSS_PASSWORD = os.environ.get("VSS_PASSWORD") or os.environ.get("PASSWORD") or ""

# Optional GPU NIMs (embeddings / re-interrogation). Missing is OK.
COSMOS3_REASON_URL = os.environ.get("COSMOS3_REASON_URL", "").rstrip("/")
COSMOS_EMBED1_URL = os.environ.get("COSMOS_EMBED1_URL", "").rstrip("/")
GPU_BEARER_TOKEN = os.environ.get("GPU_BEARER_TOKEN", "")

# W&B serverless inference (optional prior). Missing is OK — heuristic prior kicks in.
WANDB_API_KEY = os.environ.get("WANDB_API_KEY", "")
WANDB_TEAM = os.environ.get("WANDB_TEAM", "")
WANDB_PROJECT = os.environ.get("WANDB_PROJECT", "")
SCRIBNER_MODEL = os.environ.get("SCRIBNER_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
WANDB_INFERENCE_URL = os.environ.get(
    "WANDB_INFERENCE_URL", "https://api.inference.wandb.ai/v1"
)

SCRIBNER_WEBHOOK_URL = os.environ.get("SCRIBNER_WEBHOOK_URL", "")

# Gate knobs. Demo-scale epsilon is looser than production on purpose.
AUDIT_FRACTION = float(os.environ.get("SCRIBNER_AUDIT_FRACTION", "0.10"))
EPSILON_ESCAPE = float(os.environ.get("SCRIBNER_EPSILON", "0.08"))
DELTA_FALSE_REJECT = float(os.environ.get("SCRIBNER_DELTA", "0.12"))
RETRAIN_EVERY = int(os.environ.get("SCRIBNER_RETRAIN_EVERY", "10"))

PKG_DIR = Path(__file__).resolve().parent
STATIC_DIR = PKG_DIR / "static"


def repo_root() -> Path:
    """Walk up until AGENTS.md or prompts/ appears (nested repo vs flat ConfigMap)."""
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "AGENTS.md").exists() or (p / "prompts").is_dir():
            return p
    return here


REPO_ROOT = repo_root()
DATA_DIR = Path(os.environ.get("SCRIBNER_DATA_DIR", "/tmp/scribner"))
