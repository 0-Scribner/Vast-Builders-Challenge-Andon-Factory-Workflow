# Scribner

Scribner is a **LEGO kit completeness quality gate** for the [VAST Builders Challenge](https://github.com/vast-data/vast-builders-challenge). Each clip is one kit. Cosmos Reason describes it against a bill of materials. A tiny logistic model, anchored to that prior, auto-passes, auto-fails, or holds for a human. Reviewer labels retrain the model so coverage rises while subtle misses stay in HOLD.

**Pitch (38 words):** Scribner turns a phone clip of a LEGO kit into a pass/fail completeness check. It reads a bill-of-materials caption, holds uncertain units for a human, and learns from those decisions so the next shift needs fewer reviews.

Agents: read **[AGENTS.md](AGENTS.md)** first, then `.cursor/skills/`.

## Why this, on this stack

The challenge thesis is *the ingest prompt decides what is searchable*. Scribner makes that prompt a **bill of materials**. YOLO has no LEGO classes (occlusion only). Learning is a prior-anchored logistic regression, not a new detector.

Own footage is allowed; internet video is not. Shoot 4.0–4.8 s clips, kit filling the frame, white background, no hands. See `.cursor/skills/ingest-kits`.

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

1. Film kits (`race-car`, `front-loader` — parts in `tools/scribner/kits.py`).
2. Upload with the BOM prompt (skill `ingest-kits`).
3. Deploy at `/app` (skill `deploy-scribner`, [deploy/DEPLOY.md](deploy/DEPLOY.md)).
4. Review HOLD units, hit Retrain, show coverage.

Do not rebuild DataEngine. Do not Docker. Do not demo localhost.

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Operating manual for Cursor / Josh |
| `tools/scribner/` | App (flat imports — this dir is the ConfigMap) |
| `tools/scribner/kits.py` | Bills of materials (source of truth) |
| `prompts/kit_completeness_v1.txt` | Generated ingest prompts (≤800 chars) |
| `.cursor/skills/` | run-mock, ingest-kits, review-retrain, deploy-scribner |
| `deploy/DEPLOY.md` | kubectl for `/app` |

## Stack named in the demo

VAST S3 + DataEngine + VastDB · NVIDIA Cosmos Reason (captions) · Cosmos Embed1 (index) · YOLO11 (hands/occlusion only) · W&B Inference (optional prior) · Cursor skills · this gate (`numpy` logistic regression).

## 2-minute demo

1. Problem: kit completeness is still a human looking at a tray.
2. Show a COMPLETE caption vs MISSING: 4 black wheels (prompt = schema).
3. Cold start: those auto-decide; UNCLEAR / far-side HOLDs.
4. Label ~15 HOLDs. Retrain. HOLD band narrows; coverage up.
5. A hidden-door clip still HOLDs — that is the point of HITL.
6. Name the stack. Open the markdown report.

## Constraints we will not violate

- Cosmos captions are plain prose (JSON is stripped). Parser expects `PRESENT:` / `MISSING:` / `UNCLEAR:` / `COMPLETE:` / `CONFIDENCE:`.
- Custom prompt ≤800 characters.
- ConfigMap ≲ 1 MiB, no JS build, no sklearn.
- Ingress path `/app` only.
