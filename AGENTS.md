# Scribner — agent operating manual

You are helping Bryce (or any teammate) run a **completeness quality gate** on the VAST Builders Challenge **provided video packs**. Read this file before writing code, calling APIs, or deploying.

When Bryce asks for a **handoff**, write it agent-first using `.cursor/handoffs/TEMPLATE.md` (rule: `.cursor/rules/handoffs.mdc`). Do not write a human narrative. Corpus ingest handoff: `.cursor/handoffs/ingest-kits.md` (skill `ingest-kits`).

Scribner is the app in `tools/scribner/`. The VSS ingest/search stack is **already running** on the workshop VM. Do not rebuild it. Do not redeploy DataEngine functions. Do not call `docker`.

**Stack lock:** https://github.com/vast-data/vast-builders-challenge is the only allowed infrastructure. Env names from that repo's `config.example`. HTTP only against routes in its `.cursor/skills` (`retrieval/*`, `ingest/upload-video`, `ingest/reingest-*`, `gpu/*`, `deployment/deploy-app-no-registry`). Details: `docs/BUILDERS_STACK.md`. After any stack-touching edit: `./scripts/run_adversarial.sh`.

## What this product is

**Pack C** (SDG warehouse, `camera_id=sdg_warehouse_cam-2`, `location=warehouse3`) is already indexed. Re-ingest those clips with a **bill-of-materials prompt**. Cosmos Reason describes each aisle clip. Scribner parses PRESENT / MISSING / COMPLETE, scores `p_fail` (probability the clip is **incomplete**), and decides:

- `AUTO_PASS` — checklist looks complete, confident
- `AUTO_FAIL` — a listed part is missing, confident
- `HOLD` — send to a human

A reviewer marks **COMPLETE** or **INCOMPLETE**. Those labels retrain a tiny logistic regression **anchored to the VLM prior**, then re-derive `T_pass` / `T_fail`. Coverage (share of units decided without a human) should rise. Glare / far-side / low-confidence clips stay in HOLD.

**Red line:** false PASS (an incomplete aisle marked complete). Fail closed.

The same schema expands to the official cross-pack query *person close to a moving vehicle* via `SCRIBNER_PACK=cross`. Optional own `race-car` / `front-loader` clips use the same parser.

Do **not** build a hard-hat detector. PPE is the example the brief says not to treat as the whole product.

## First actions on a new session

1. `SCRIBNER_MOCK=1 python3 tools/scribner/main.py` — prove the loop locally.
2. `BUILDERS_CHALLENGE_DIR=/tmp/vast-builders-challenge ./scripts/run_adversarial.sh` — prove official-stack conformance + poka-yoke.
3. On the workshop VM only: source `/config/<team>.config`, unset mock, **re-ingest Pack C** with skill `ingest-kits`, deploy with `.cursor/skills/deploy-scribner/SKILL.md`.

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
| Operator UI | `tools/scribner/static/index.html` |
| Mock units | `tools/scribner/mock_data.py` |
| Live Explore / search scan | `tools/scribner/scan.py` |
| Persistence | `tools/scribner/store.py` |
| Deploy | `deploy/DEPLOY.md` and skill `deploy-scribner` |

Do not add `sklearn`, `scipy`, `torch`, frontend bundlers, or `node_modules`. The pod is `python:3.12-slim` with code from a ConfigMap (**~1 MiB total**). Keep `tools/scribner/` small.

## Natural-language skills

Skills live in `.cursor/skills/`. Load the matching skill **before** writing curl by hand.

- `run-mock` — local end-to-end without VSS
- `conformance-stack` — clone the official challenge repo and run adversarial tests
- `ingest-kits` — re-ingest Pack C (and optional own clips) with the BOM prompt
- `review-retrain` — drive the HITL loop
- `deploy-scribner` — K8s `/app` (no Docker; `deployment/deploy-app-no-registry`)

## Constraints that fail a demo if ignored

- Ingress path is **`/app`** on the team host. Never `/`, never localhost as the deliverable.
- Cosmos captions are **plain prose**, max ~1024 chars. The pipeline strips JSON. The BOM prompt asks for labeled inline fields (`PRESENT:` …), not JSON.
- Custom ingest prompt max **800 characters**. Count before re-ingesting.
- Pack C clips are already segmented. **Re-ingest**, do not re-upload the corpus. Designate 1–2 people for bulk re-ingest.
- YOLO has **no LEGO classes**. On optional own clips it is occlusion only (person/hand). On Pack C, people and forklifts are expected; do not HOLD every person as occlusion.
- Do not ingest YouTube / internet video. Provided corpus and own files only.

## Demo story (2 minutes)

1. Problem: warehouse aisle completeness is still a human scrubbing cameras.
2. Show a COMPLETE caption vs MISSING: person-vehicle separation (prompt = schema).
3. Gate HOLDs glare/unclear; AUTO_FAIL on a clean near-miss BOM miss; AUTO_PASS on empty aisles.
4. Review ~15 units (keyboard `C` / `I`).
5. Retrain. Coverage rises; salient misses AUTO_FAIL; unclear distance stays HOLD.
6. Name the stack and the official Pack C camera. Optional closer: same schema hits *person close to a moving vehicle* across packs.
