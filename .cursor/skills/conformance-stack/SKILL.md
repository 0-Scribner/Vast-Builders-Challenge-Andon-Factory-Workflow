---
name: conformance-stack
description: >-
  Verify Scribner only uses the official VAST Builders Challenge stack
  (https://github.com/vast-data/vast-builders-challenge): env names from
  config.example, retrieval/ingest/gpu/deploy skills, no invented APIs,
  no Canary, no Docker, no YouTube. Use when someone says "conformance",
  "builders stack", "official APIs", "adversarial stack", or "run adversarial".
---

# Conformance to the official Builders Stack

1. Clone or reuse the challenge repo:

```bash
DIR="${BUILDERS_CHALLENGE_DIR:-/tmp/vast-builders-challenge}"
test -f "$DIR/config.example" || git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git "$DIR"
export BUILDERS_CHALLENGE_DIR="$DIR"
```

2. Extract the contract and attack Scribner:

```bash
./scripts/run_adversarial.sh
```

3. If any test fails: fix the product (do not weaken the test). Record attacks in `.cursor/adversarial/YYYYMMDD-*.md`.

4. Allowed resources are listed in `docs/BUILDERS_STACK.md`. Runtime checker: `tools/scribner/builders_stack.scan_scribner_violations()`.

Do not add VSS routes, env vars, or GPU hosts that are not in that clone. Do not call Canary for kit QC.
