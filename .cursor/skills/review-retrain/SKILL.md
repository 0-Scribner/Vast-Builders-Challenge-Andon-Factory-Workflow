---
name: review-retrain
description: >-
  Drive Scribner's human-in-the-loop loop: load the HOLD queue, record
  CLEAR/UNSAFE labels with reason codes, retrain the prior-anchored
  logistic scorer, and report coverage / HOLD-band metrics. Use when the
  team is labeling Pack C clips, hitting Retrain, or asking whether
  coverage moved.
---

# Review and retrain

## What "learned" means

Cold start: `w = w0` so `p_fail` equals the caption prior. Salient
NEAR_MISS+HIGH captions already AUTO_ALERT; PATH_CLEAR+HIGH already
AUTO_CLEAR; UNCLEAR / LOW confidence HOLD.

After labels: `learn.fit_logistic` pulls `w` toward the humans
(overrides weighted 2×). Thresholds only **narrow**. Headline KPI is
**coverage** (share auto-decided) and **HOLD band** (`t_fail - t_pass`).

Never quote an accuracy number with n < 30 labels. Show the coverage curve.

## UI

Keyboard: `A`/`C` CLEAR (accept), `O`/`U` UNSAFE (object), `N` next.
Reason chips must be set when the human disagrees with the caption
(`vlm_missed_near_miss`, `vlm_false_alert`, `far_but_looks_close`, …).
AUTO_ALERT → CLEAR requires `confirm_escape=true`.

## API (same as the UI)

```bash
curl -s -X POST "$APP/api/review" -H 'Content-Type: application/json' \
  -d '{"unit_id":"wh-021","verdict":"UNSAFE","reason":"vlm_missed_near_miss"}'
curl -s -X POST "$APP/api/retrain"
curl -s "$APP/api/metrics"
```

`$APP` is `http://127.0.0.1:8080` locally or `http://video-lab-team-<N>.cosmos.vastdata.com/app` on cluster.

## Oracle simulation (mock only)

```bash
PYTHONPATH=tools/scribner python3 scripts/simulate_reviews.py
```

Uses each mock unit's `true_unsafe` flag — **never** send that field
from the live scorer; it is test-only.

## Agent rules

- Auto-retrain already fires every `SCRIBNER_RETRAIN_EVERY` (default 10) labels; still call `/api/retrain` before a demo so metrics_log has a row.
- Do not lower epsilon/delta during a demo to fake coverage.
- If queue is empty after scan, either every unit was auto-decided (good — check audit samples) or scan found nothing (check `sdg_warehouse_cam-2` on Explore and that captions have `PATH_CLEAR:`).
