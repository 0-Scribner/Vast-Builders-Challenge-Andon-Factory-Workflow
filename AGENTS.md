# Scribner — agent operating manual

You are helping Josh (or any teammate) run a **LEGO kit completeness quality gate** on the VAST Builders Challenge stack. Read this file before writing code, calling APIs, or deploying.

When Josh asks for a **handoff**, write it agent-first using `.cursor/handoffs/TEMPLATE.md` (rule: `.cursor/rules/handoffs.mdc`). Do not write a human narrative. Kit ingest handoff: `.cursor/handoffs/ingest-kits.md` (skill `ingest-kits`).

Scribner is the app in `tools/scribner/`. The VSS ingest/search stack is **already running** on the workshop VM. Do not rebuild it. Do not redeploy DataEngine functions. Do not call `docker`.

## What this product is

Each uploaded clip is one kit unit. Cosmos Reason describes the clip using a **bill-of-materials prompt**. Scribner parses that description, scores `p_fail` (probability the kit is incomplete), and decides:

- `AUTO_PASS` — kit looks complete, confident
- `AUTO_FAIL` — kit looks incomplete, confident
- `HOLD` — send to a human

A reviewer marks COMPLETE or INCOMPLETE. Those labels retrain a tiny logistic regression **anchored to the VLM prior**, then re-derive `T_pass` / `T_fail`. Coverage (share of units decided without a human) should rise. Subtle misses stay in HOLD.

## First actions on a new session

1. `SCRIBNER_MOCK=1 python3 tools/scribner/main.py` — prove the loop locally.
2. `python3 -m unittest discover -s tools/scribner/tests -v` — prove parser, scorer, gate.
3. On the workshop VM only: source `/config/<team>.config`, unset mock, deploy with `.cursor/skills/deploy-scribner/SKILL.md`.

Never print, log, or commit values from `/config/*.config`. List env **names** with `env | cut -d= -f1 | sort`. Never run bare `env`.

## File map (edit the smallest file that owns the change)

| Change | File |
|--------|------|
| Kit parts / names / BOM prompt | `tools/scribner/kits.py` then regenerate `prompts/kit_completeness_v1.txt` |
| Caption parser | `tools/scribner/inspection.py` |
| Feature vector or `w0` prior-anchor | `tools/scribner/features.py` |
| Logistic regression / thresholds | `tools/scribner/learn.py` |
| PASS/FAIL/HOLD policy, audit % | `tools/scribner/gate.py` |
| VSS HTTP | `tools/scribner/vss_client.py` |
| W&B LLM prior | `tools/scribner/llm.py` |
| Routes | `tools/scribner/main.py` |
| UI | `tools/scribner/static/index.html` |
| Mock units | `tools/scribner/mock_data.py` |
| Persistence | `tools/scribner/store.py` |
| Deploy | `deploy/DEPLOY.md` and skill `deploy-scribner` |

Do not add `sklearn`, `scipy`, `torch`, frontend bundlers, or `node_modules`. The pod is `python:3.12-slim` with code from a ConfigMap (**~1 MiB total**). Keep `tools/scribner/` small.

## Natural-language skills

Skills live in `.cursor/skills/`. Load the matching skill **before** writing curl by hand.

- `run-mock` — local end-to-end without VSS
- `ingest-kits` — upload phone clips with the BOM prompt
- `review-retrain` — drive the HITL loop
- `deploy-scribner` — K8s `/app` (no Docker)

## Constraints that fail a demo if ignored

- Ingress path is **`/app`** on the team host. Never `/`, never localhost as the deliverable.
- Cosmos captions are **plain prose**, max ~1024 chars. The pipeline strips JSON. The BOM prompt asks for labeled inline fields (`PRESENT:` …), not JSON.
- Custom ingest prompt max **800 characters**. Count before uploading.
- One clip ≈ one 5-second segment. Shoot **4.0–4.8s**, kit filling the frame, white background, no hands.
- YOLO has **no LEGO classes**. Do not claim detector-based brick ID. YOLO is occlusion only (person/hand in frame).
- Do not ingest YouTube / internet video. Own footage and the provided corpus only.

## Demo story (2 minutes)

1. Problem: kit completeness is visual QC humans do by eye.
2. Show a COMPLETE caption vs a MISSING-wheels caption (prompt = schema).
3. Gate HOLDs most units at cold start.
4. Review ~15 units (keyboard `C` / `I`).
5. Retrain. Coverage rises; salient misses AUTO_FAIL; tiny hidden bricks stay HOLD.
6. Name the stack: VAST S3 + DataEngine + VastDB, Cosmos Reason + Embed1, YOLO (occlusion), W&B Inference (optional prior), Cursor, this gate.
