# Scribner

Scribner is the **Primary** judged product: a warehouse **path-clear / near-miss gate** on the [VAST Builders Challenge](https://github.com/vast-data/vast-builders-challenge) **Pack C** archive (`sdg_warehouse_cam-2`, ~178 aisle clips). Cosmos Reason captions each clip against a PATH_CLEAR / NEAR_MISS schema. A tiny logistic model, anchored to that prior, auto-clears, auto-alerts, or holds for a human. Reviewer labels retrain the model so coverage rises while unclear distance stays in HOLD.

**Pitch (40 words):** Scribner turns the official warehouse aisle archive into an aisle gate. It reads a path-safety caption, holds uncertain clips for a human, and learns from those decisions so the next shift reviews fewer near-misses — without auto-clearing what it cannot see.

Plan B (LEGO completeness) lives on `cursor/plan-b-lego-completeness-72e3`. Agents: read **[AGENTS.md](AGENTS.md)** first, then `.cursor/skills/`. Lines: [docs/PLAN.md](docs/PLAN.md).

## Why this, on this stack

The challenge thesis is *the ingest prompt decides what is searchable*. Scribner makes that prompt a **path-safety schema** (`PERSON` / `VEHICLE` / `MOTION` / `DISTANCE` / `PATH_CLEAR` / `NEAR_MISS`) for footage organizers already indexed. Re-ingest Pack C; do not film LEGO for the judged demo; do not scrape YouTube; do not build a hard-hat detector. YOLO person/vehicle **corroborates** and must **not** sole-source AUTO_CLEAR. Learning is a prior-anchored logistic regression, not a new detector.

The same schema **is** the official Architecture Reference payoff query *person close to a moving vehicle* (`SCRIBNER_PACK=cross`).

## Quick start (mock, no VSS)

```bash
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
export SCRIBNER_MOCK=1
./scripts/run_mock.sh
# http://127.0.0.1:8080   keys: A/C clear · O/U unsafe · N next
```

Oracle loop:

```bash
PYTHONPATH=tools/scribner python3 scripts/simulate_reviews.py
```

## Live (workshop VM)

1. Re-ingest Pack C with the warehouse-aisle prompt (skill `ingest-kits` / `ingest-warehouse`). Camera `sdg_warehouse_cam-2`.
2. Deploy at `/app` (skill `deploy-scribner`, [deploy/DEPLOY.md](deploy/DEPLOY.md)).
3. Review HOLD units (`CLEAR` / `UNSAFE`), hit Retrain, show coverage.

Do not rebuild DataEngine. Do not Docker. Do not demo localhost.

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Operating manual for Cursor / Bryce |
| [docs/PLAN.md](docs/PLAN.md) | Primary vs Plan B |
| [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md) | Official challenge repo contract |
| `tools/scribner/` | App (flat imports — this dir is the ConfigMap) |
| `tools/scribner/kits.py` | Scene schema (source of truth) |
| `prompts/warehouse_near_miss_v1.txt` | Generated ingest prompts (≤800 chars) |
| `.cursor/skills/` | run-mock, ingest-kits, ingest-warehouse, review-retrain, deploy-scribner |
| `deploy/DEPLOY.md` | kubectl for `/app` |

## Stack named in the demo

VAST S3 + DataEngine + VastDB · NVIDIA Cosmos Reason (captions) · Cosmos Embed1 (index) · YOLO11 (person/vehicle corroboration) · W&B Inference (optional prior) · Cursor skills · this gate (`numpy` logistic regression). Bound to the official Builders Challenge repo only. The operator footer and `/health` carry the same line: `VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor`.

## 2-minute demo

1. Problem: a person close to a moving vehicle is still a human scrubbing cameras.
2. Show a PATH_CLEAR YES caption vs NEAR_MISS YES (prompt = schema).
3. Cold start: empty aisles AUTO_CLEAR; forklift-near-person AUTO_ALERT; UNCLEAR / far-side HOLDs.
4. Label ~15 HOLDs. Retrain. HOLD band narrows; coverage up.
5. An unclear-distance clip still HOLDs — that is the point of HITL. False CLEAR is illegal.
6. Name Pack C + the stack. Open the markdown report.

## Constraints we will not violate

- Cosmos captions are plain prose (JSON is stripped). Parser expects `PERSON:` / `VEHICLE:` / `MOTION:` / `DISTANCE:` / `PATH_CLEAR:` / `NEAR_MISS:` / `HAZARD:` / `UNCLEAR:` / `CONFIDENCE:`.
- Custom prompt ≤800 characters (`GET /api/v1/metadata/ingest-config`).
- ConfigMap ≲ 1 MiB, no JS build, no sklearn.
- Ingress path `/app` only (`deployment/deploy-app-no-registry`).
- Only the official stack: [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md). Run `./scripts/run_adversarial.sh`.
- False CLEAR is illegal. No AUTO_CLEAR on inconsistent captions, NEAR_MISS, named hazards, LOW confidence, UNCLEAR fields, view blocked, or YOLO person+vehicle without a HIGH PATH_CLEAR caption.
