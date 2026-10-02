# Scribner — agent operating manual

You are helping Bryce (or any teammate) run the **Primary** warehouse **path-clear / near-miss gate** on the VAST Builders Challenge **provided Pack C videos**. Read this file before writing code, calling APIs, or deploying.

When Bryce asks for a **handoff**, write it agent-first using `.cursor/handoffs/TEMPLATE.md` (rule: `.cursor/rules/handoffs.mdc`). Do not write a human narrative. Corpus ingest handoff: `.cursor/handoffs/ingest-kits.md` (skill `ingest-kits` / `ingest-warehouse`). Cowork laptop: `.cursor/handoffs/chatgpt-cowork.md`.

Scribner is the app in `tools/scribner/`. The VSS ingest/search stack is **already running** on the workshop VM. Do not rebuild it. Do not redeploy DataEngine functions. Do not call `docker`.

**Stack lock:** https://github.com/vast-data/vast-builders-challenge is the only allowed infrastructure. Env names from that repo's `config.example`. HTTP only against routes in its `.cursor/skills` (`retrieval/*`, `ingest/upload-video`, `ingest/reingest-*`, `gpu/*`, `deployment/deploy-app-no-registry`). Details: `docs/BUILDERS_STACK.md`. After any stack-touching edit: `./scripts/run_adversarial.sh`.

**Lines:** Primary = this tree (warehouse near-miss). Plan B = LEGO completeness on `cursor/plan-b-lego-completeness-72e3`. See `docs/PLAN.md`. Do not mix BOMs.

## What this product is

**Pack C** (SDG warehouse, `camera_id=sdg_warehouse_cam-2`, `location=warehouse3`) is already indexed. Re-ingest those clips with a **path-safety prompt**. Cosmos Reason describes each aisle clip. Scribner parses PATH_CLEAR / NEAR_MISS, scores `p_fail` (probability the clip is **UNSAFE**), and decides:

- `AUTO_CLEAR` — 緑 正常, path looks clear, confident
- `AUTO_ALERT` — 赤 停止, near-miss or blocked path, confident
- `HOLD` — 黄 呼び出し, send to a human (andon cord)

The operator UI is an **安灯 andon board** on the Pack C clip (現場 gemba). A reviewer marks **CLEAR** (正常, A/C) or **UNSAFE** (異常 / pull cord, O/U). Those labels retrain a tiny logistic regression **anchored to the VLM prior**, then re-derive `T_pass` / `T_fail`. Coverage should rise. Glare / far-side / low-confidence clips stay 黄 HOLD.

**Red line:** false CLEAR (an unsafe aisle marked clear). 赤灯は人なしで緑にしない.

The same schema **is** the official cross-pack query *person close to a moving vehicle* via `SCRIBNER_PACK=cross`.

Do **not** build a hard-hat detector. PPE is the example the brief says not to treat as the whole product. Do not reskin the VSS Explore UI — this is andon + jidoka, not a search page.

## First actions on a new session

1. `SCRIBNER_MOCK=1 python3 tools/scribner/main.py` — prove the loop locally.
2. `BUILDERS_CHALLENGE_DIR=/tmp/vast-builders-challenge ./scripts/run_adversarial.sh` — prove official-stack conformance + poka-yoke.
3. On the workshop VM only: source `/config/<team>.config`, unset mock, **re-ingest Pack C** with skill `ingest-kits`, deploy with `.cursor/skills/deploy-scribner/SKILL.md`.

Never print, log, or commit values from `/config/*.config`. List env **names** with `env | cut -d= -f1 | sort`. Never run bare `env`.

## File map (edit the smallest file that owns the change)

| Change | File |
|--------|------|
| Scene schema / names / ingest prompt | `tools/scribner/kits.py` then regenerate `prompts/warehouse_near_miss_v1.txt` |
| Caption parser | `tools/scribner/inspection.py` |
| Feature vector or `w0` prior-anchor | `tools/scribner/features.py` |
| Logistic regression / thresholds | `tools/scribner/learn.py` |
| CLEAR/ALERT/HOLD policy, audit % | `tools/scribner/gate.py` |
| VSS HTTP | `tools/scribner/vss_client.py` |
| W&B LLM prior | `tools/scribner/llm.py` |
| Routes | `tools/scribner/main.py` |
| Andon lamps / 現場 mapping | `tools/scribner/andon.py` then `/api/andon` |
| Operator UI (andon + Pack C clip) | `tools/scribner/static/index.html` |
| Mock units | `tools/scribner/mock_data.py` |
| Live Explore / search scan | `tools/scribner/scan.py` |
| Persistence | `tools/scribner/store.py` |
| Deploy | `deploy/DEPLOY.md` and skill `deploy-scribner` |

Do not add `sklearn`, `scipy`, `torch`, frontend bundlers, or `node_modules`. The pod is `python:3.12-slim` with code from a ConfigMap (**~1 MiB total**). Keep `tools/scribner/` small.

## Natural-language skills

Skills live in `.cursor/skills/`. Load the matching skill **before** writing curl by hand.

- `run-mock` — local end-to-end without VSS
- `conformance-stack` — clone the official challenge repo and run adversarial tests
- `ingest-kits` / `ingest-warehouse` — re-ingest Pack C with the path-safety prompt
- `review-retrain` — drive the HITL loop
- `deploy-scribner` — K8s `/app` (no Docker; `deployment/deploy-app-no-registry`)

## Constraints that fail a demo if ignored

- Ingress path is **`/app`** on the team host. Never `/`, never localhost as the deliverable.
- Cosmos captions are **plain prose**, max ~1024 chars. The pipeline strips JSON. The prompt asks for labeled inline fields (`PATH_CLEAR:` …), not JSON.
- Custom ingest prompt max **800 characters**. Count before re-ingesting.
- Pack C clips are already segmented. **Re-ingest**, do not re-upload the corpus. Designate 1–2 people for bulk re-ingest.
- YOLO **corroborates** person/vehicle. It must **not** sole-source AUTO_CLEAR. On Pack C, people and forklifts are expected; do not HOLD every person as occlusion.
- Do not ingest YouTube / internet video. Provided corpus and own files only.

## Demo story (2 minutes)

1. Problem: a person close to a moving vehicle is still a human scrubbing cameras.
2. Andon on the Pack C clip (現場): 緑 AUTO_CLEAR, 黄 HOLD, 赤 AUTO_ALERT. Line lamp = worst open ticket.
3. Show PATH_CLEAR YES vs NEAR_MISS YES (prompt = schema). Red lamp on a near-miss clip.
4. Review ~15 units (keyboard `A` / `O` — O pulls the andon cord).
5. Retrain. Coverage rises; salient near-misses stay 赤; unclear distance stays 黄 HOLD. 赤灯は人なしで緑にしない.
6. Name the stack (footer / `/health`) and `sdg_warehouse_cam-2`. Optional closer: same schema hits *person close to a moving vehicle* across packs.
