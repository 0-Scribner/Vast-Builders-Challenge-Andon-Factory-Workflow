#!/usr/bin/env bash
# Local mock server. Agent: prefer the run-mock skill.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON=python3
export SCRIBNER_MOCK="${SCRIBNER_MOCK:-1}"
export SCRIBNER_DATA_DIR="${SCRIBNER_DATA_DIR:-/tmp/scribner-dev}"
export PORT="${PORT:-8080}"
cd "$ROOT/tools/scribner"
exec "$PYTHON" main.py
