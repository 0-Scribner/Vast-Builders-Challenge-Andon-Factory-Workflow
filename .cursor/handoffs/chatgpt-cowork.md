# Handoff: close Scribner engineering for ChatGPT Cowork

You are a coding agent (ChatGPT Cowork). Execute this handoff to completion with no back-and-forth. Do not ask Josh to write code, design UX, or choose libraries. After you finish, the only human job left is: **film LEGO kits and drop the clips in a folder**. An **operator** (not an engineer) then uses a web UI to say whether the QC gate was right.

**Poka-yoke** (mistake-proofing) and **adversarial review** are mandatory on every change. A change without both is not done. Prefer making the wrong action *impossible* over adding a warning.

Copy this entire file into Cowork. Repo on disk is Scribner. Current engineering branch: `cursor/lego-kit-qc-gate-72e3`. Origin (Cursor): `https://origin.cursor.com/git/bryce-mcg/Scribner.git`. Public GitHub must exist and stay in sync with origin on every push.

## Receiver

ChatGPT Cowork on Josh’s machine (or any machine with git, Python 3.12, ffmpeg). CWD = Scribner repo root (`AGENTS.md` present). You may clone if missing. You will edit code, run tests, run an adversarial pass on each change, commit, push **origin and GitHub**, and leave mock UI + ingest path ready. Workshop VM / K8s deploy is documented, not required for this handoff to complete.

## Done when

- [ ] `PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v` is all OK, including **poka-yoke and adversarial** tests (false-PASS attacks, inconsistent captions, illegal operator actions, filename/prompt guards).
- [ ] `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` serves an **Operator** UI at `http://127.0.0.1:8080`: video + gate decision + BOM fields; operator keys **A** = gate was right, **O** = gate was wrong (then COMPLETE/INCOMPLETE + reason). HOLD items require a verdict. No engineer copy on that screen. Illegal clicks are **rejected by API and disabled in UI** (poka-yoke), not toasted-and-allowed.
- [ ] Live scan path uses the full allowed stack (or degrades in logs, never crashes): VSS upload/explore/metadata/detections/search, Cosmos Reason captions (BOM prompt), YOLO detections as occlusion, Cosmos Embed1 vectors as features/precedents, W&B Inference prior when `WANDB_API_KEY` is set, W&B run on retrain. Do not call Canary (kits are silent). Do not rebuild DataEngine. Do not Docker.
- [ ] Dual remotes: `origin` = Origin, `github` = `https://github.com/<owner>/Scribner.git` (public). Every commit is pushed to **both**. `scripts/push_both.sh` exists and is used. Push script **fails closed** if either remote fails.
- [ ] README / AGENTS.md state: remaining human work is film (`docs/FILM_THE_KITS.md`) → drop files in `~/kit-clips` named `kit-<kit_id>_unit-<nnn>.mp4` → VM agent runs `.cursor/handoffs/ingest-kits.md`. Operator only opens `/app` (or mock localhost) to approve the gate.
- [ ] Every feature you shipped has a checked **Adversarial review** block in `.cursor/adversarial/YYYYMMDD-cowork.md` (attacks you ran, what broke, the poka-yoke you added). No empty checklists.
- Out of scope: filming, YouTube, changing BOM unless a new kit appears in filenames, attending the hackathon, `docker`, DataEngine function edits, native apps.

## Context

Scribner is a LEGO kit completeness QC gate on the VAST Builders Challenge stack. `tools/scribner/kits.py` is the BOM. Cosmos captions must stay labeled prose (`PRESENT:` …) because VSS strips JSON; custom_prompt ≤800 chars. Learning is numpy logistic regression in `learn.py` anchored to `prior_logit` (`w0[1]=1`). App is flat imports under `tools/scribner/` for ConfigMap deploy at Ingress **`/app`**. Current UI labels COMPLETE/INCOMPLETE directly; you must change it so the **operator judges the gate**. YOLO has no LEGO classes. Own footage only. False PASS (incomplete kit auto-passed) is the failure mode poka-yoke must make hardest.

## Never

- Do not ingest internet/YouTube video (reject by URL/host check if a path is a URL).
- Do not print `/config`, JWTs, passwords, `WANDB_API_KEY`, or GitHub tokens.
- Do not `git add` mp4/zip/clips (pre-commit / `push_both` must refuse).
- Do not add sklearn/scipy/torch/node_modules; ConfigMap ≲ 1 MiB.
- Do not ship localhost as the judged **event** demo (mock localhost is OK for this closeout). Event deliverable remains K8s `/app`.
- Do not push only to origin. If GitHub push fails, status=`blocked`, do not pretend it is on github.com.
- Do not ask Josh which button labels to use. Use the Operator spec below.
- Do not rebuild VSS / DataEngine.
- Do not AUTO_PASS when caption is inconsistent, confidence is LOW, UNCLEAR is nonempty, or occlusion is true.
- Do not accept operator “Gate was right” on HOLD, or “Gate was wrong” with empty/agree reason.
- Do not skip adversarial review because “the happy path works.”

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

2. **Add `scripts/push_both.sh`** (executable). It must: refuse if staged/working tree contains `*.mp4`, `*.zip`, or files named `*.config` except `*.example`; `git push origin HEAD` then `git push github HEAD` (create `-u` as needed). **Exit non-zero** if either push fails. Use this after every commit in this handoff.

3. **Operator UI (required product change).** Edit `tools/scribner/static/index.html` + `state.py` / `main.py` as needed.

- Screen title: **Operator — kit QC gate**. Subtitle: approve or override the gate. No “reviewer”, no “engineer”.
- Unit card: autoplay clip (`/clip`), kit name, BOM missing/present/unclear, caption, `p_fail`, chip for `AUTO_PASS` / `AUTO_FAIL` / `HOLD`, occlusion flag, prior rationale, **inconsistency flag** if COMPLETE=YES but missing nonempty (or COMPLETE=NO but missing empty and unclear empty).
- Precedents: up to 3 nearest labeled units (Embed1 cosine if vectors exist; else caption-tag overlap).
- Actions (UI disabled + API 400 if violated — poka-yoke):
  - **A / “Gate was right”**: AUTO_PASS → COMPLETE; AUTO_FAIL → INCOMPLETE; **HOLD: button disabled, API rejects**.
  - **O / “Gate was wrong”**: operator must pick COMPLETE or INCOMPLETE **and** a reason chip that is **not** `agree`. Empty reason → reject.
  - HOLD: operator must choose COMPLETE or INCOMPLETE (not agree).
  - Override of AUTO_PASS (claiming the kit is INCOMPLETE) is 1-click. Override of AUTO_FAIL that would mark COMPLETE (possible escaped defect) requires a **second confirm** in UI (`confirm_escape=true` on API). Missing confirm → 400.
- Metrics: coverage, HOLD rate, operator agreement (share of non-HOLD labels with `overrode=false`), HOLD band, n_labels, **false-pass risk** (count of AUTO_PASS with LOW/UNCLEAR/inconsistent — must stay 0).
- Keep audit autos in the queue so the operator can contradict AUTO_*.

`POST /api/review` body may add `gate_ok`, `confirm_escape`. Persist `overrode`. Do not break existing tests; extend them.

4. **Poka-yoke in the gate and ingest (required).** Implement so mistakes bounce, they do not warn-and-continue.

| Mistake to make impossible | Implementation |
|---------------------------|----------------|
| Incomplete kit AUTO_PASS | `gate.py`: if `complete is False` or `part_ids_missing` nonempty → never AUTO_PASS (p_fail floor or decision override). |
| Unclear / LOW / occlusion AUTO_PASS | same; force HOLD or fail-closed, never PASS. |
| COMPLETE=YES and MISSING nonempty | `inspection.py` sets `inconsistent=True`; gate treats as HOLD. |
| Operator agrees on HOLD | API 400; UI disables A. |
| Override with no reason | API 400. |
| Escaping a fail with one misclick | double-confirm on AUTO_FAIL → COMPLETE. |
| Bad clip names / unknown kit | ingest path and any helper: regex `kit-<kit_id>_unit-<nnn>.(mp4\|mov\|webm\|mkv\|avi)`; unknown `kit_id` skip, do not guess. |
| Prompt >800 chars | `prompt_for_kit` already raises; upload helper must refuse if `len(custom_prompt)>800`. |
| YouTube/http(s) as “file” | reject if path/URL contains youtube, youtu.be, or scheme http(s) except the team VSS host. |
| Secrets / clips committed | `push_both.sh` refuse list above. |
| Deploy to `/` | keep Ingress `/app` only in `deploy/DEPLOY.md` / skill. |

5. **Use the entire allowed stack in live mode** (`SCRIBNER_MOCK=0`). Graceful degrade if an endpoint is down.

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

6. **Adversarial review on all development (required, every change).** After each logical change (operator UI, gate poka-yoke, ingest guards, remotes), **before** commit:

a. Write attacks in `.cursor/adversarial/YYYYMMDD-cowork.md` using this shape:

```
## Change: <file or feature>
Attack: <what a rushed operator, bad caption, or hostile filename would do>
Expected poka-yoke: <rejected / HOLD / fail-closed>
Result: pass | fail
Fix: <commit-able change or n/a>
```

Minimum attacks you must actually run (tests or mock API), not just list:

- Caption COMPLETE:YES + MISSING: 4 black wheels → must not AUTO_PASS.
- Caption CONFIDENCE:LOW COMPLETE:YES → must not AUTO_PASS.
- Occlusion true + complete yes → must not AUTO_PASS.
- POST review gate_ok=true on a HOLD unit → 400.
- POST override AUTO_FAIL→COMPLETE without confirm_escape → 400.
- POST override with reason=agree or empty → 400.
- Upload/helper with filename `random.mp4` or kit_id `spaceship` → skip/reject.
- Prompt string of 801 chars → reject.
- Path `https://www.youtube.com/watch?v=…` → reject.
- `git add` simulation of a `.mp4` into push_both dry-run → refuse.

b. Put those cases in `tools/scribner/tests/test_poka_yoke.py` (and HTTP tests if you add a TestClient). A green happy-path suite without these is **not** done.

c. If an attack succeeds (false PASS or illegal label accepted), **fix before any other feature**. Do not push a known bypass.

d. Second pass: re-run the same attacks after the fix. Log Result: pass.

7. **Tests.** Keep `test_scribner.py`. Add poka-yoke tests. Operator agree/override mapping tested. Mock coverage after oracle labels ≥ cold coverage. Hidden-side / low-confidence must not all AUTO_PASS at cold start.

8. **Docs.** AGENTS.md + README: two roles — **Operator** (UI) vs **Ingest agent** (VM upload). Remaining Josh work = film per `docs/FILM_THE_KITS.md` + copy to `~/kit-clips`. Point VM ingest at `.cursor/handoffs/ingest-kits.md`. Mention dual push, poka-yoke (false PASS is the red line), and that every change needs an adversarial note.

9. **Commit and dual-push** (only after adversarial file exists and tests include the attacks).

```sh
git add -A
git status   # no mp4, no .config secrets
git commit -m "Operator QC console, poka-yoke false-PASS, adversarial tests; mirror GitHub."
./scripts/push_both.sh
```

If you need more commits, adversarial delta + tests + push_both after each.

## Verification

```sh
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR=/tmp/scribner-cowork python3 - <<'PY'
from state import AppState
s=AppState(mock=True); s.scan(); m=s.run_gate()["metrics"]
assert m["n"]>=30
q=s.queue(); assert q, "expected HOLD or audit queue"
# false-PASS poka-yoke: no AUTO_PASS with low conf / missing / inconsistent
from gate import decide_all
dec={d["unit_id"]:d for d in s.store.load_decisions()}
for u in s.store.load_units():
    d=dec[u["id"]]
    insp=u.get("inspection") or {}
    if d["decision"]=="AUTO_PASS":
        assert insp.get("complete") is True
        assert not insp.get("missing")
        assert insp.get("confidence")!="low"
        assert not u.get("occlusion")
        assert not insp.get("inconsistent")
print("cold_coverage", m["coverage"], "queue", len(q))
PY
test -f .cursor/adversarial/*cowork.md
git remote -v   # origin AND github
git status -sb
```

Pass: tests OK including poka-yoke; mock AUTO_PASS never on low/missing/inconsistent/occlusion; HTML contains Operator + Gate was right; A disabled on HOLD; adversarial file has Result: pass on the required attacks; `github` remote exists; `git ls-remote github HEAD` matches local HEAD. Fail: do not mark done; fix or `status: blocked` with the failing command.

## Report back

```
handoff: chatgpt-cowork
status: done | blocked | partial
checks:
- tests: pass | fail
- poka_yoke_tests: pass | fail
- adversarial_review: pass | fail
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
- adversarial: .cursor/adversarial/<file>
- mock: SCRIBNER_MOCK=1 ./scripts/run_mock.sh → http://127.0.0.1:8080
next: Josh films kits to ~/kit-clips; VM agent runs ingest-kits; operator uses UI
```

## Stop and escalate

Write `status: blocked` and stop if: cannot authenticate to GitHub after one `gh auth login` / token attempt; tests fail after two fix cycles; an adversarial false-PASS still reproduces after one fix cycle (report the attack, do not ship); VSS/DataEngine rewrite seems required (it is not); clip files are the only way to proceed (they are not — mock is enough). Do not invent a GitHub URL you did not push to.
