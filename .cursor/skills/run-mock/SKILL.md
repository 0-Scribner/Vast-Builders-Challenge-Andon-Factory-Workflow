---
name: run-mock
description: >-
  Run Scribner locally in mock mode (no VSS, no credentials). Use when
  verifying the kit-completeness gate, UI, tests, or a cold start before
  the workshop VM. Triggers on "run mock", "start scribner locally",
  "prove the loop", "run tests".
---

# Run Scribner in mock mode

Do this **before** touching the live VSS stack. Mock mode loads 40 synthetic
Pack C aisle units (complete, missing person-gap/walkway/lane, hidden-gap,
view-blocked) and runs the same parser → prior → scorer → HOLD queue as live.

## Tests (must pass)

From the repo root:

```bash
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
```

If unittest is not on the path, `cd tools/scribner && python3 -m unittest tests.test_scribner -v`.

## App

```bash
export SCRIBNER_MOCK=1
export SCRIBNER_DATA_DIR=/tmp/scribner-dev
rm -rf "$SCRIBNER_DATA_DIR"
cd tools/scribner
python3 main.py
```

Open `http://127.0.0.1:8080`. Keyboard: `C` complete, `I` incomplete, `N` next.

Health check: `curl -s http://127.0.0.1:8080/health`

## Headless review loop (optional)

```bash
PYTHONPATH=tools/scribner python3 scripts/simulate_reviews.py
```

Expect coverage after oracle labels ≥ coverage at cold start, and
`missing-person-gap` units with `p_fail ≥ 0.55`.

## Agent rules

- Do not require VSS credentials in mock mode.
- Do not start Docker.
- If port 8080 is busy, set `PORT=8081`.
- Data lives in `SCRIBNER_DATA_DIR`; delete it for a true cold start.
