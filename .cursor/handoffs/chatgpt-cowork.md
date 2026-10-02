# Handoff: close Scribner engineering for ChatGPT Cowork

You are a coding agent (ChatGPT Cowork). Execute this handoff to completion with no back-and-forth. Do not ask Josh to write code, design UX, or choose libraries. After you finish, the only human job left is: **film LEGO kits and drop the clips in a folder**. An **operator** (not an engineer) then uses a web UI to say whether the QC gate was right.

Copy this entire file into Cowork. Repo on disk is Scribner. Current engineering branch: `cursor/lego-kit-qc-gate-72e3`. Origin (Cursor): `https://origin.cursor.com/git/bryce-mcg/Scribner.git`. Public GitHub must exist and stay in sync with origin on every push.

## Receiver

ChatGPT Cowork on Josh’s machine (or any machine with git, Python 3.12, ffmpeg). CWD = Scribner repo root (`AGENTS.md` present). You may clone if missing. You will edit code, run tests, commit, push **origin and GitHub**, and leave mock UI + ingest path ready. Workshop VM / K8s deploy is documented, not required for this handoff to complete.

## Done when

- [ ] `PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v` is all OK.
- [ ] `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` serves an **Operator** UI at `http://127.0.0.1:8080`: video + gate decision + BOM fields; operator keys **A** = gate was right, **O** = gate was wrong (then COMPLETE/INCOMPLETE + reason). HOLD items require a verdict. No engineer copy on that screen.
- [ ] Live scan path uses the full allowed stack (or degrades in logs, never crashes): VSS upload/explore/metadata/detections/search, Cosmos Reason captions (BOM prompt), YOLO detections as occlusion, Cosmos Embed1 vectors as features/precedents, W&B Inference prior when `WANDB_API_KEY` is set, W&B run on retrain. Do not call Canary (kits are silent). Do not rebuild DataEngine. Do not Docker.
- [ ] Dual remotes: `origin` = Origin, `github` = `https://github.com/<owner>/Scribner.git` (public). Every commit is pushed to **both**. `scripts/push_both.sh` exists and is used.
- [ ] README / AGENTS.md state: remaining human work is film (`docs/FILM_THE_KITS.md`) → drop files in `~/kit-clips` named `kit-<kit_id>_unit-<nnn>.mp4` → VM agent runs `.cursor/handoffs/ingest-kits.md`. Operator only opens `/app` (or mock localhost) to approve the gate.
- Out of scope: filming, YouTube, changing BOM unless a new kit appears in filenames, attending the hackathon, `docker`, DataEngine function edits, native apps.

## Context

Scribner is a LEGO kit completeness QC gate on the VAST Builders Challenge stack. `tools/scribner/kits.py` is the BOM. Cosmos captions must stay labeled prose (`PRESENT:` …) because VSS strips JSON; custom_prompt ≤800 chars. Learning is numpy logistic regression in `learn.py` anchored to `prior_logit` (`w0[1]=1`). App is flat imports under `tools/scribner/` for ConfigMap deploy at Ingress **`/app`**. Current UI labels COMPLETE/INCOMPLETE directly; you must change it so the **operator judges the gate**, not “is this a car.” YOLO has no LEGO classes. Own footage only.

## Never

- Do not ingest internet/YouTube video.
- Do not print `/config`, JWTs, passwords, `WANDB_API_KEY`, or GitHub tokens.
- Do not `git add` mp4/zip/clips.
- Do not add sklearn/scipy/torch/node_modules; ConfigMap ≲ 1 MiB.
- Do not ship localhost as the judged **event** demo (mock localhost is OK for this closeout). Event deliverable remains K8s `/app`.
- Do not push only to origin. If GitHub push fails, status=`blocked`, do not pretend it is on github.com.
- Do not ask Josh which button labels to use. Use the Operator spec below.
- Do not rebuild VSS / DataEngine.

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Repo | this tree or clone Origin branch `cursor/lego-kit-qc-gate-72e3` | yes |
| Origin remote | `origin` → Origin Scribner | yes |
| GitHub remote | `github` URL; create public `Scribner` under Josh’s GitHub user/org if missing (`gh repo create` or API). If `GITHUB_REPO` env is set, use that. | yes |
| Auth | `gh auth status` or `git` HTTPS/SSH to github.com | yes to finish GitHub |
| Python | 3.12 + pip: fastapi uvicorn requests numpy pydantic openai | yes |
| Footage | not required for this handoff | no |

## Procedure

1. **Checkout and remotes.**

```sh
git fetch origin cursor/lego-kit-qc-gate-72e3
git checkout cursor/lego-kit-qc-gate-72e3
git pull origin cursor/lego-kit-qc-gate-72e3
git remote -v
```

If `github` remote is missing: resolve owner from `gh api user --jq .login` or `GITHUB_REPO`. Create public repo if 404. `git remote add github https://github.com/<owner>/Scribner.git`. Push branch and `main`.

2. **Add `scripts/push_both.sh`** (executable). It must: `git push origin HEAD` then `git push github HEAD` (create `-u` as needed). Fail the script if either push fails. Use this after every commit in this handoff.

3. **Operator UI (required product change).** Edit `tools/scribner/static/index.html` + `state.py` / `main.py` as needed.

- Screen title: **Operator — kit QC gate**. Subtitle: approve or override the gate. No “reviewer”, no “engineer”.
- Unit card: autoplay clip (`/clip`), kit name, BOM missing/present/unclear, caption, `p_fail`, chip for `AUTO_PASS` / `AUTO_FAIL` / `HOLD`, occlusion flag, prior rationale.
- Precedents: up to 3 nearest labeled units (Embed1 cosine if vectors exist; else caption-tag overlap).
- Actions:
  - **A / “Gate was right”**: if AUTO_PASS → label COMPLETE; AUTO_FAIL → INCOMPLETE; if HOLD, disable and require a verdict.
  - **O / “Gate was wrong”**: operator picks COMPLETE or INCOMPLETE + reason chip (`vlm_missed_part`, `vlm_false_missing`, `hidden_side`, `hands_in_frame`, `wrong_kit`, `other`).
  - HOLD: operator must choose COMPLETE or INCOMPLETE (this is not “agree”).
- Metrics: coverage, HOLD rate, operator agreement (share of non-HOLD labels with `overrode=false`), HOLD band, n_labels.
- Keep audit autos in the queue so the operator can contradict AUTO_*.

`POST /api/review` body may add `gate_ok: true|false`. Persist `overrode` as today. Do not break existing tests; extend them.

4. **Use the entire allowed stack in live mode** (`SCRIBNER_MOCK=0`). Graceful degrade if an endpoint is down.

| Piece | How you must use it |
|-------|---------------------|
| VAST S3 + DataEngine + VastDB | Only via VSS APIs: upload (ingest-kits), explore, metadata, detections, stream, optional `POST /api/v1/search` with `tags`/`camera_id=kit-station-1` |
| Cosmos Reason | BOM `custom_prompt` from `prompt_for_kit`; optional GPU re-ask is extra, not required |
| YOLO11 | `GET /videos/detections`; `occlusion` if person/hand; show class list on the operator card. Never “YOLO found a missing wheel” |
| Cosmos Embed1 | `$COSMOS_EMBED1_URL/v1/embeddings` with bearer if present; 256-d; store on unit; kNN precedents + optional feature dims. If unreachable, skip vectors |
| W&B Inference | existing `llm.py` prior when `WANDB_API_KEY` set |
| W&B tracking | existing `tracking.py` on retrain |
| Cursor/Cowork skills | keep `.cursor/skills/*` accurate after UI rename |
| Canary-1B | do not wire |

5. **Tests.** Update `tools/scribner/tests/test_scribner.py` for parser/scorer/loop plus operator agree/override mapping. Mock coverage after oracle labels must be ≥ cold coverage. Hidden-side / low-confidence must not all AUTO_PASS at cold start.

6. **Docs.** AGENTS.md + README: two roles — **Operator** (UI) vs **Ingest agent** (VM upload). Remaining Josh work = film per `docs/FILM_THE_KITS.md` + copy to `~/kit-clips`. Point VM ingest at `.cursor/handoffs/ingest-kits.md`. Mention dual push.

7. **Commit and dual-push.**

```sh
git add -A
git status   # no mp4, no .config secrets
git commit -m "Make operator QC console the human loop; mirror to GitHub."
./scripts/push_both.sh
```

If you need more commits, push_both after each.

## Verification

```sh
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR=/tmp/scribner-cowork python3 - <<'PY'
from state import AppState
s=AppState(mock=True); s.scan(); m=s.run_gate()["metrics"]
assert m["n"]>=30
q=s.queue(); assert q, "expected HOLD or audit queue"
print("cold_coverage", m["coverage"], "queue", len(q))
PY
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/ || true
# start mock if needed, then:
# curl -s http://127.0.0.1:8080/ | grep -q "Operator"
git remote -v   # must show origin AND github
git status -sb  # must not be ahead of origin after push_both
```

Pass: tests OK; mock queue non-empty; HTML contains Operator + Gate was right; `github` remote exists; `git ls-remote github HEAD` matches local HEAD. Fail: do not mark done; fix or `status: blocked` with the failing command.

## Report back

```
handoff: chatgpt-cowork
status: done | blocked | partial
checks:
- tests: pass | fail
- operator_ui: pass | fail
- stack_wired: pass | fail | partial (<which pieces degraded>)
- origin_push: pass | fail
- github_remote: pass | fail
- github_push: pass | fail
- footage_only_remaining: pass | fail
artifacts:
- branch: cursor/lego-kit-qc-gate-72e3
- origin: origin.cursor.com/git/bryce-mcg/Scribner
- github: https://github.com/<owner>/Scribner
- mock: SCRIBNER_MOCK=1 ./scripts/run_mock.sh → http://127.0.0.1:8080
next: Josh films kits to ~/kit-clips; VM agent runs ingest-kits; operator uses UI
```

## Stop and escalate

Write `status: blocked` and stop if: cannot authenticate to GitHub after one `gh auth login` / token attempt; tests fail after two fix cycles; VSS/DataEngine rewrite seems required (it is not); clip files are the only way to proceed (they are not — mock is enough). Do not invent a GitHub URL you did not push to.
