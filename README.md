# Scribner

Scribner is the **Primary** judged product: a Japanese-QC **安灯 andon board** on the [VAST Builders Challenge](https://github.com/vast-data/vast-builders-challenge) **Pack C** warehouse archive (`sdg_warehouse_cam-2`). Cosmos Reason captions each aisle clip. The gate is jidoka: 緑 AUTO_CLEAR, 黄 HOLD (呼び出し), 赤 AUTO_ALERT (停止). A human pulls the andon cord (UNSAFE). False CLEAR never auto-greens a red lamp.

**Pitch:** Scribner puts an andon over official warehouse video. Green means the aisle is clear. Yellow calls a human. Red is a near-miss, a person close to a moving vehicle, and the line does not run until someone looks.

Plan B (LEGO completeness) lives on `cursor/plan-b-lego-completeness-72e3`. Agents: read **[AGENTS.md](AGENTS.md)** first, then `.cursor/skills/`. Lines: [docs/PLAN.md](docs/PLAN.md).

## Why this, on this stack

The challenge thesis is *the ingest prompt decides what is searchable*. Scribner makes that prompt a **path-safety schema** (`PERSON` / `VEHICLE` / `MOTION` / `DISTANCE` / `PATH_CLEAR` / `NEAR_MISS`) for footage organizers already indexed. Re-ingest Pack C; do not film LEGO for the judged demo; do not scrape YouTube; do not build a hard-hat detector. YOLO person/vehicle **corroborates** and must **not** sole-source AUTO_CLEAR. Learning is a prior-anchored logistic regression, not a new detector.

The same schema **is** the official Architecture Reference payoff query *person close to a moving vehicle* (`SCRIBNER_PACK=cross`).

## Quick start (mock, no VSS)

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r tools/scribner/requirements.txt
export BUILDERS_CHALLENGE_DIR="$HOME/vast-builders-challenge"
./scripts/run_adversarial.sh
export SCRIBNER_MOCK=1
./scripts/run_mock.sh
# http://127.0.0.1:8080   keys: A/C 正常 CLEAR, O/U 異常 andon cord, N next
```

The scripts use `.venv/bin/python` when present. If port 8080 is occupied,
run `PORT=8081 ./scripts/run_mock.sh` and open `http://127.0.0.1:8081`.
Mock clips are generated warehouse stand-ins; live Pack C playback requires VSS credentials.

Code: [0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow](https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow),
default branch `cursor/warehouse-primary-72e3`.

Oracle loop:

```bash
PYTHONPATH=tools/scribner python3 scripts/simulate_reviews.py
```

## Live (workshop VM)

1. Re-ingest Pack C with the warehouse-aisle prompt (skill `ingest-kits` / `ingest-warehouse`). Camera `sdg_warehouse_cam-2`.
2. Deploy at `/app` (skill `deploy-scribner`, [deploy/DEPLOY.md](deploy/DEPLOY.md)).
3. Review HOLD units (`CLEAR` / `UNSAFE`), hit Retrain, show coverage.

Scripted workshop steps with pass checks: [workshop/README.md](workshop/README.md).

Do not rebuild DataEngine. Do not Docker. Do not demo localhost.

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Operating manual for coding agents |
| [docs/PLAN.md](docs/PLAN.md) | Primary vs Plan B |
| [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md) | Official challenge repo contract |
| [docs/DEMO.md](docs/DEMO.md) | Two-minute judge demo script |
| `tools/scribner/` | App (flat imports; this dir is the ConfigMap) |
| `tools/scribner/kits.py` | Scene schema (source of truth) |
| `prompts/warehouse_near_miss_v1.txt` | Generated ingest prompts (800 chars max) |
| `workshop/` | Numbered workshop VM steps |
| `.cursor/skills/` | run-mock, ingest-kits, ingest-warehouse, review-retrain, deploy-scribner |
| `deploy/DEPLOY.md` | kubectl for `/app` |

## Stack named in the demo

VAST S3, DataEngine and VastDB; NVIDIA Cosmos Reason (captions); Cosmos Embed1 (index); YOLO11 (person/vehicle corroboration); W&B Inference (optional prior); Cursor skills; this gate (`numpy` logistic regression). Bound to the official Builders Challenge repo only. The operator footer and `/health` carry the same stack line.

## Builders Stack usage

Each tool named in the official [BUILD_DAY.md](https://github.com/vast-data/vast-builders-challenge/blob/main/BUILD_DAY.md), and where Scribner uses it. `workshop/NN` is the numbered script in [workshop/](workshop/README.md).

| BUILD_DAY tool | Where Scribner uses it |
|----------------|------------------------|
| VAST S3 | Holds the Pack C clips. Live `/clip` streams them through the VSS stream route (`tools/scribner/vss_client.py`); `workshop/05` checks `/clip` bytes against the VSS source. |
| VAST DataEngine | Runs the Pack C re-ingest jobs that `workshop/03` and `workshop/04` start. Scribner does not rebuild or redeploy it. |
| VAST DataBase (VastDB) | `workshop/09` reads it directly with `vastdb-read`. The app stays on HTTP. |
| Cosmos Reason | Captions each segment from `prompts/warehouse_near_miss_v1.txt`; `tools/scribner/inspection.py` parses the fields; `workshop/06` checks health and a non-empty completion. |
| Cosmos Embed | Indexes the segments that the live scan searches; `workshop/06` checks health and a 256-value embedding. |
| YOLO | Person and vehicle detections corroborate the caption and never sole-source AUTO_CLEAR; `workshop/06` runs inference on a Pack C clip. |
| W&B Serverless Inference | Optional prior in `tools/scribner/llm.py`, clamped on near-miss; retrain runs log through `tools/scribner/tracking.py`; `workshop/06` checks both. |
| Cursor | Coding agent on the VM; Scribner adds its own skills in `.cursor/skills/`. |
| Video Search & Summary UI | Not called by the app; `workshop/02` reads the same Explore inventory through the API. |
| `reingest-chunk` | `workshop/03`: one complete Pack C chunk first, then a caption-field check. |
| `reingest-videos` | `workshop/04`: the remaining Pack C clips, one job at a time. |
| `search` | Live scan in `tools/scribner/scan.py`; `workshop/02` runs the payoff query *person close to a moving vehicle*. |
| `videos` | Explore inventory, segment metadata, detections and clip stream in `tools/scribner/vss_client.py`; `workshop/02`, `03` and `05`. |
| `agent-qa` | `/api/stack/ask` |
| `dashboard` | `/api/stack/dashboard` |
| `suggest-prompts` | `/api/stack/suggest` |
| `list-metadata` | `/api/stack/metadata`; `workshop/02` and `03` read the live prompt limit. |
| `vastdb-read` | `workshop/09` |
| Deploy (`deploy-app-no-registry`) | `workshop/07` deploys under the team Ingress host at `/app`. |
| Health check | `workshop/02` preflight; the app's `/health` returns the stack line. |
| `submission` | `workshop/08` fills `SUBMISSION.md`. |
| `ask-cosmos` | Support snippet when a health check fails; no app dependency. |

Status: rows that touch VAST, the GPUs or W&B need the workshop VM and the team config. No workshop step and no `/api/stack/*` route has run against live VAST yet, so this repo reports no accuracy figures.

## 2-minute demo

1. Problem: a person close to a moving vehicle is still a human scrubbing cameras.
2. Andon on the Pack C clip: 緑 AUTO_CLEAR, 黄 HOLD, 赤 AUTO_ALERT. Station tower tracks this clip; line lamps track the worst open ticket.
3. PATH_CLEAR YES vs NEAR_MISS YES (prompt = schema). A near-miss clip is a red lamp, not a search hit.
4. Label about 15 HOLDs (`A`/`O`; O pulls the cord). Retrain. The thresholds and the coverage KPI update from those labels.
5. Unclear-distance stays 黄. 赤灯は人なしで緑にしない.
6. Name Pack C + the stack. Open the shift report.

Full judge script: [docs/DEMO.md](docs/DEMO.md).

## Constraints we will not violate

- Cosmos captions are plain prose (JSON is stripped). Parser expects `PERSON:` / `VEHICLE:` / `MOTION:` / `DISTANCE:` / `PATH_CLEAR:` / `NEAR_MISS:` / `HAZARD:` / `UNCLEAR:` / `CONFIDENCE:`.
- Custom prompt of 800 characters or fewer (`GET /api/v1/metadata/ingest-config`).
- ConfigMap under 1 MiB, no JS build, no sklearn.
- Ingress path `/app` only (`deployment/deploy-app-no-registry`).
- Only the official stack: [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md). Run `./scripts/run_adversarial.sh`.
- False CLEAR is illegal. No AUTO_CLEAR on inconsistent captions, NEAR_MISS, named hazards, LOW confidence, UNCLEAR fields, view blocked, or YOLO person+vehicle without a HIGH PATH_CLEAR caption.
