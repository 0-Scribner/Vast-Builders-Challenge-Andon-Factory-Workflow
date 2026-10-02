#!/usr/bin/env python3
"""Oracle-label every mock unit and print coverage before vs after retrain.

Agent note: uses ``true_incomplete`` which exists only on mock fixtures.
Never read that field in the scorer or the live UI.
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
    for u in st.store.load_units():
        verdict = "INCOMPLETE" if u["true_incomplete"] else "COMPLETE"
        st.review(u["id"], verdict, reason="agree")
    warm = st.retrain()["metrics"]
    print("cold", json.dumps(cold, indent=2))
    print("warm", json.dumps(warm, indent=2))
    print("data_dir", os.environ["SCRIBNER_DATA_DIR"])


if __name__ == "__main__":
    main()
