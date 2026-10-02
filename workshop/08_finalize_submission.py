#!/usr/bin/env python3
"""Fill only submission fields that can be verified from the current environment."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

CODE_URL = "https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feedback", default="")
    ap.add_argument("--live-app", default="", help="Override verified live URL")
    args = ap.parse_args()

    path = Path("SUBMISSION.md")
    if not path.is_file():
        raise SystemExit("Run from Scribner repo root")
    text = path.read_text(encoding="utf-8")

    team = (os.environ.get("USERNAME") or os.environ.get("PIPELINE") or "").strip()
    if team:
        first, *rest = text.splitlines()
        if first.startswith("# team-pending") or first.startswith("# team-"):
            text = "\n".join([f"# {team}", *rest]) + ("\n" if text.endswith("\n") else "")

    # Code URL is now verified public.
    import re
    text = re.sub(r"\*\*Code:\*\*.*", f"**Code:** {CODE_URL}", text)

    live = args.live_app.strip()
    if not live:
        ingress = (os.environ.get("INGRESS_URL") or "").rstrip("/")
        if ingress:
            live = ingress + "/app"
    if live:
        text = re.sub(r"\*\*Live app:\*\*.*", f"**Live app:** {live}", text)
    if args.feedback.strip():
        text = re.sub(r"## Feedback\n.*?(?=\n<!--|\Z)", "## Feedback\n" + args.feedback.strip() + "\n", text, flags=re.S)

    path.write_text(text, encoding="utf-8")
    missing = []
    if "team-pending" in text:
        missing.append("team number ($USERNAME/$PIPELINE)")
    if "none yet" in text or "<N>" in text:
        missing.append("verified live app")
    if "NOT PROVIDED" in text:
        missing.append("feedback")
    print(f"updated={path}")
    print("remaining=" + (", ".join(sorted(set(missing))) if missing else "none"))


if __name__ == "__main__":
    main()
