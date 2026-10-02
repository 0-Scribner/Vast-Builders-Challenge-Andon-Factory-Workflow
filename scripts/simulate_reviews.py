#!/usr/bin/env python3
"""Oracle-label every mock unit and print coverage before vs after retrain.

Uses ``true_unsafe``, which exists only on mock fixtures; the scorer and
the live UI never read it.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "scribner"))

os.environ["SCRIBNER_MOCK"] = "1"
os.environ["SCRIBNER_DATA_DIR"] = tempfile.mkdtemp(prefix="scribner-sim-")

from state import AppState  # noqa: E402


def main() -> None:
    st = AppState(mock=True)
    st.scan()
    cold = st.run_gate()["metrics"]
    decisions = {d["unit_id"]: d for d in st.store.load_decisions()}
    for u in st.store.load_units():
        verdict = "UNSAFE" if u.get("true_unsafe") or u.get("true_incomplete") else "CLEAR"
        auto = (decisions.get(u["id"]) or {}).get("decision") or "HOLD"
        kwargs = {}
        reason = "agree"
        if auto in {"AUTO_CLEAR", "AUTO_PASS"} and verdict == "UNSAFE":
            reason = "vlm_missed_near_miss"
        elif auto in {"AUTO_ALERT", "AUTO_FAIL"} and verdict == "CLEAR":
            reason = "vlm_false_alert"
            kwargs["confirm_escape"] = True
        st.review(u["id"], verdict, reason=reason, **kwargs)
    warm = st.retrain()["metrics"]
    print("cold", json.dumps(cold, indent=2))
    print("warm", json.dumps(warm, indent=2))
    print("data_dir", os.environ["SCRIBNER_DATA_DIR"])


if __name__ == "__main__":
    main()
