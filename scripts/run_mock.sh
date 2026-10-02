#!/usr/bin/env bash
# Local mock server. Agent: prefer the run-mock skill.
set -euo pipefail
export SCRIBNER_MOCK="${SCRIBNER_MOCK:-1}"
export SCRIBNER_DATA_DIR="${SCRIBNER_DATA_DIR:-/tmp/scribner-dev}"
export PORT="${PORT:-8080}"
cd "$(dirname "$0")/../tools/scribner"
exec python3 main.py
