# Scribner

Scribner is a **completeness quality gate** for the [VAST Builders Challenge](https://github.com/vast-data/vast-builders-challenge) **provided video packs**. Default live corpus is **Pack C** (`sdg_warehouse_cam-2`, ~178 aisle clips). Cosmos Reason describes each clip against a bill of materials. A tiny logistic model, anchored to that prior, auto-passes, auto-fails, or holds for a human. Reviewer labels retrain the model so coverage rises while unclear distance stays in HOLD.

**Pitch (40 words):** Scribner turns the official warehouse aisle archive into a pass/fail completeness check. It reads a bill-of-materials caption, holds uncertain clips for a human, and learns from those decisions so the next shift reviews fewer aisles.

Agents: read **[AGENTS.md](AGENTS.md)** first, then `.cursor/skills/`.

## Why this, on this stack

The challenge thesis is *the ingest prompt decides what is searchable*. Scribner makes that prompt a **bill of materials** (`PRESENT` / `MISSING` / `COMPLETE`) for the footage organizers already indexed. Re-ingest Pack C; do not film LEGO for the judged demo; do not scrape YouTube. YOLO person/hand is occlusion only on optional own clips; on Pack C, people and forklifts are the subject. Learning is a prior-anchored logistic regression, not a new detector.

The same schema expands to the official cross-pack query *person close to a moving vehicle* (`SCRIBNER_PACK=cross`).

Own `race-car` / `front-loader` clips remain optional extra kits with the same parser.

## Quick start (mock, no VSS)

```bash
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
export SCRIBNER_MOCK=1
./scripts/run_mock.sh
# http://127.0.0.1:8080   keys: C complete · I incomplete · N next
```

Oracle loop:

```bash
PYTHONPATH=tools/scribner python3 scripts/simulate_reviews.py
```

## Live (workshop VM)

1. Re-ingest Pack C with the warehouse-aisle BOM prompt (skill `ingest-kits`). Camera `sdg_warehouse_cam-2`.
2. Deploy at `/app` (skill `deploy-scribner`, [deploy/DEPLOY.md](deploy/DEPLOY.md)).
3. Review HOLD units (`COMPLETE` / `INCOMPLETE`), hit Retrain, show coverage.

Do not rebuild DataEngine. Do not Docker. Do not demo localhost.

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Operating manual for Cursor / Bryce |
| [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md) | Official challenge repo contract |
| `tools/scribner/` | App (flat imports — this dir is the ConfigMap) |
| `tools/scribner/kits.py` | Bills of materials (source of truth) |
| `prompts/kit_completeness_v1.txt` | Generated ingest prompts (≤800 chars) |
| `.cursor/skills/` | run-mock, ingest-kits, review-retrain, deploy-scribner |
| `deploy/DEPLOY.md` | kubectl for `/app` |

## Stack named in the demo

VAST S3 + DataEngine + VastDB · NVIDIA Cosmos Reason (captions) · Cosmos Embed1 (index) · YOLO11 (occlusion on own clips) · W&B Inference (optional prior) · Cursor skills · this gate (`numpy` logistic regression). Bound to the official Builders Challenge repo only.

## 2-minute demo

1. Problem: aisle completeness (path clear, person-vehicle gap, walkway clear) is still a human scrubbing cameras.
2. Show a COMPLETE caption vs MISSING: person-vehicle separation (prompt = schema).
3. Cold start: those auto-decide; UNCLEAR / far-side HOLDs.
4. Label ~15 HOLDs. Retrain. HOLD band narrows; coverage up.
5. An unclear-distance clip still HOLDs — that is the point of HITL.
6. Name Pack C + the stack. Open the markdown report.

## Constraints we will not violate

- Cosmos captions are plain prose (JSON is stripped). Parser expects `PRESENT:` / `MISSING:` / `UNCLEAR:` / `COMPLETE:` / `CONFIDENCE:`.
- Custom prompt ≤800 characters (`GET /api/v1/metadata/ingest-config`).
- ConfigMap ≲ 1 MiB, no JS build, no sklearn.
- Ingress path `/app` only (`deployment/deploy-app-no-registry`).
- Only the official stack: [docs/BUILDERS_STACK.md](docs/BUILDERS_STACK.md). Run `./scripts/run_adversarial.sh`.
- False PASS is illegal. No AUTO_PASS on inconsistent captions, MISSING parts, LOW confidence, UNCLEAR fields, or occlusion.
