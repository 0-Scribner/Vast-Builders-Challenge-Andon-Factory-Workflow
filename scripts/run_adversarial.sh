#!/usr/bin/env bash
# Attack Scribner against the official Builders Stack clone, then poka-yoke tests.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON=python3
DIR="${BUILDERS_CHALLENGE_DIR:-/tmp/vast-builders-challenge}"
if [[ ! -f "$DIR/config.example" ]]; then
  git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git "$DIR"
fi
export BUILDERS_CHALLENGE_DIR="$DIR"
export PYTHONPATH="$ROOT/tools/scribner"
"$PYTHON" "$ROOT/scripts/extract_builders_stack.py"
"$PYTHON" -m unittest discover -s "$ROOT/tools/scribner/tests" -v
