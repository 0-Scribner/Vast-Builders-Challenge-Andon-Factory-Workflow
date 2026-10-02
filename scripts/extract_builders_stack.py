#!/usr/bin/env python3
"""Extract the official stack contract from a vast-builders-challenge clone.

    git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git /tmp/vast-builders-challenge
    BUILDERS_CHALLENGE_DIR=/tmp/vast-builders-challenge python3 scripts/extract_builders_stack.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "scribner"))

from builders_stack import (  # noqa: E402
    SOURCE_URL,
    challenge_dir,
    dump_lock,
    extract_from_challenge,
)


def ensure_clone() -> Path:
    existing = challenge_dir()
    if existing:
        return existing
    dest = Path(os.environ.get("BUILDERS_CHALLENGE_DIR") or "/tmp/vast-builders-challenge")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not (dest / "config.example").is_file():
        subprocess.check_call(
            ["git", "clone", "--depth", "1", SOURCE_URL + ".git", str(dest)]
        )
    return dest


def main() -> int:
    root = ensure_clone()
    data = extract_from_challenge(root)
    sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    data["extracted_commit"] = sha
    out = dump_lock(data)
    print(json.dumps({"wrote": str(out), "commit": sha, "env": data["config_example_env"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
