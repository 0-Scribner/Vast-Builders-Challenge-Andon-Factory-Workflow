#!/usr/bin/env bash
# Local server; SCRIBNER_MOCK=0 switches it to live VSS.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON=python3
export SCRIBNER_MOCK="${SCRIBNER_MOCK:-1}"
export SCRIBNER_DATA_DIR="${SCRIBNER_DATA_DIR:-/tmp/scribner-dev}"
export PORT="${PORT:-8080}"
cd "$ROOT/tools/scribner"
exec "$PYTHON" main.py
