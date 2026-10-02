# Scribner

Scribner is the **Primary** judged product: a Japanese-QC **安灯 andon board** on the [VAST Builders Challenge](https://github.com/vast-data/vast-builders-challenge) **official video corpus**. Cosmos Reason captions each clip. The gate is jidoka: 緑 AUTO_CLEAR, 黄 HOLD (呼び出し), 赤 AUTO_ALERT (停止). A human pulls the andon cord (UNSAFE). False CLEAR never auto-greens a red lamp.

**Pitch (40 words):** Scribner puts an andon over the official challenge cameras. Green means the path is clear. Yellow calls a human. Red is a near-miss — a person close to a moving vehicle — and the line does not run until someone looks.

## Where the videos come from

The demo site uses **only** the pre-indexed lab corpus in
[ARCHITECTURE_REFERENCE.md § Video corpus](https://github.com/vast-data/vast-builders-challenge/blob/main/ARCHITECTURE_REFERENCE.md#video-corpus-already-indexed).
[BUILD_DAY.md](https://github.com/vast-data/vast-builders-challenge/blob/main/BUILD_DAY.md) names the same sources: dashcam, overhead highway, neighborhood (warehouse and indoor are in the Architecture Reference). Do not film. Do not ingest YouTube. Re-ingest only.

| Pack | Source | Location | `camera_id` | Indexed |
|------|--------|----------|-------------|---------|
| A | I-24 / 3D traffic | nashville | `i24_cam-1` | ~51 highway clips |
| B | PIE drives | toronto | `pie_cam-3` | 6 dashcam sets |
| C | SDG warehouse RGB | warehouse3 | `sdg_warehouse_cam-2` | ~178 aisle clips |
| D | Neighborhood cars | neighborhood | `neighborhood_cam-1` | 2 day merges |
| E | SF streets | san_francisco | `sf_streets_cam-1`…`4` | ingesting soon |
| F | Smart spaces | indoor | `smartspace_cam-1` | ~102 indoor clips |

Payoff query (hits A+B+C+D+E): *person close to a moving vehicle*. Machine-readable copy: `tools/scribner/corpus.py`, `GET /api/corpus`. Live `/clip` streams that camera’s VSS segment. Mock paints a camera-kind stand-in (highway / dashcam / street / warehouse / indoor) tinted to the andon lamp.

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
# http://127.0.0.1:8080   keys: A/C 正常 CLEAR · O/U 異常 andon cord · N next
```

The scripts use `.venv/bin/python` when present. If port 8080 is occupied,
run `PORT=8081 ./scripts/run_mock.sh` and open `http://127.0.0.1:8081`.
Mock clips are camera-kind stand-ins for those official IDs; live playback streams VSS.

Origin is the source of truth: [bryce-mcg/Scribner](https://cursor.com/codebase/bryce-mcg/Scribner),
branch `cursor/warehouse-primary-72e3`. The GitHub mirror is
[0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow](https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow/tree/cursor/warehouse-primary-72e3).
After each commit, run `./scripts/push_both.sh`; it pushes Origin first, then GitHub,
and keeps Origin as the upstream.

For the remaining live connections and event deployment, follow the
[agent-first handoff for Josh's Cowork](.cursor/handoffs/josh-cowork.md).
It includes the unverified services, live camera filtering checks, and the
required `/app` URL fix before deployment.

Oracle loop:

```bash
PYTHONPATH=tools/scribner python3 scripts/simulate_reviews.py
```

## Live (workshop VM)

1. Re-ingest official cameras with the path-safety prompt (skill `ingest-kits` / `ingest-warehouse`). Default `SCRIBNER_PACK=CROSS` searches *person close to a moving vehicle* across I-24, PIE, neighborhood, warehouse. `PACK=C` still pins `sdg_warehouse_cam-2`.
2. Deploy at `/app` (skill `deploy-scribner`, [deploy/DEPLOY.md](deploy/DEPLOY.md)).
3. Review HOLD units (`CLEAR` / `UNSAFE`), hit Retrain, show coverage.

Do not rebuild DataEngine. Do not Docker. Do not demo localhost.

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Operating manual for Cursor / Bryce |
| [docs/PLAN.md](docs/PLAN.md) | Primary vs Plan B |
| [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md) | Official challenge repo contract |
| [docs/Scribner-Andon-Implementation.pdf](docs/Scribner-Andon-Implementation.pdf) | 16:9 slide deck of the andon implementation |
| `docs/deck/build_andon_deck.py` | Regenerates the deck (reportlab, not a ConfigMap dep) |
| `tools/scribner/` | App (flat imports — this dir is the ConfigMap) |
| `tools/scribner/corpus.py` | Official camera IDs / packs from Architecture Reference |
| `tools/scribner/kits.py` | Scene schema (source of truth) |
| `prompts/warehouse_near_miss_v1.txt` | Generated ingest prompts (≤800 chars) |
| `.cursor/skills/` | run-mock, ingest-kits, ingest-warehouse, review-retrain, deploy-scribner |
| `deploy/DEPLOY.md` | kubectl for `/app` |

## Stack named in the demo

VAST S3 + DataEngine + VastDB · NVIDIA Cosmos Reason (captions) · Cosmos Embed1 (index) · YOLO11 (person/vehicle corroboration) · W&B Inference (optional prior) · Cursor skills · this gate (`numpy` logistic regression). Bound to the official Builders Challenge repo only. The operator footer and `/health` carry the same line: `VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor`.

## 2-minute demo

1. Problem: a person close to a moving vehicle is still a human scrubbing cameras.
2. Andon on the official camera clip: 緑 AUTO_CLEAR, 黄 HOLD, 赤 AUTO_ALERT. Station tower tracks this clip; line lamps track the worst open ticket.
3. PATH_CLEAR YES vs NEAR_MISS YES (prompt = schema). A near-miss clip is a red lamp, not a search hit.
4. Label ~15 HOLDs (`A`/`O` — O pulls the cord). Retrain. HOLD band narrows; coverage up.
5. Unclear-distance stays 黄. 赤灯は人なしで緑にしない.
6. Name Pack C + the stack. Open the shift report.

## Constraints we will not violate

- Cosmos captions are plain prose (JSON is stripped). Parser expects `PERSON:` / `VEHICLE:` / `MOTION:` / `DISTANCE:` / `PATH_CLEAR:` / `NEAR_MISS:` / `HAZARD:` / `UNCLEAR:` / `CONFIDENCE:`.
- Custom prompt ≤800 characters (`GET /api/v1/metadata/ingest-config`).
- ConfigMap ≲ 1 MiB, no JS build, no sklearn.
- Ingress path `/app` only (`deployment/deploy-app-no-registry`).
- Only the official stack: [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md). Run `./scripts/run_adversarial.sh`.
- False CLEAR is illegal. No AUTO_CLEAR on inconsistent captions, NEAR_MISS, named hazards, LOW confidence, UNCLEAR fields, view blocked, or YOLO person+vehicle without a HIGH PATH_CLEAR caption.
