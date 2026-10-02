# Handoff: close Scribner engineering for ChatGPT Cowork (Josh’s machine)

You are ChatGPT Cowork **on Josh’s personal computer**, not the VAST workshop VM and not a Cursor cloud agent. Execute this handoff to completion with no back-and-forth. Do not ask Josh to write code, design UX, or choose libraries. After you finish, the only human job left is: **film LEGO kits on this machine and drop the clips in a folder**. An **operator** (Josh or a teammate) then uses a web UI on this machine to say whether the QC gate was right.

**Poka-yoke** (mistake-proofing) and **adversarial review** are mandatory on every change. A change without both is not done. Prefer making the wrong action *impossible* over adding a warning.

Repo name: **Scribner**. Engineering branch: `cursor/lego-kit-qc-gate-72e3`.
- Origin (Cursor forge, may be unreachable from this laptop): `https://origin.cursor.com/git/bryce-mcg/Scribner.git`
- GitHub (you must create or use this from **this machine**): `https://github.com/<owner>/Scribner.git` (`GITHUB_REPO` env wins if set)

If this folder is not already a git clone of Scribner with `AGENTS.md` at the root, clone or copy it first. If Origin auth fails from the laptop, get the tree however Josh already has it (Cursor app folder, zip, existing clone) and make **GitHub** the remote you can push. Still add `origin` if it works. **Every commit: push every remote that exists. GitHub is required before you are done.**

## Receiver

ChatGPT Cowork, Josh’s laptop, CWD = Scribner repo root (`AGENTS.md` present). Python 3.12, pip, ffmpeg, git, `gh` if possible. You will edit code, run tests **locally**, run adversarial attacks locally, commit, push GitHub (and Origin if authenticated), and leave **mock UI** ready on localhost. There is **no** `/config/*.config` on this machine — do not search for it, do not block on it. Workshop VM ingest/deploy is **later**, not this session.

## Done when

- [ ] `PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v` is all OK, including **poka-yoke and adversarial** tests (false-PASS attacks, inconsistent captions, illegal operator actions, filename/prompt guards).
- [ ] `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` serves an **Operator** UI at `http://127.0.0.1:8080` on **this laptop**: video + gate decision + BOM fields; keys **A** = gate was right, **O** = gate was wrong (then COMPLETE/INCOMPLETE + reason). HOLD items require a verdict. No engineer copy on that screen. Illegal clicks are **rejected by API and disabled in UI** (poka-yoke), not toasted-and-allowed.
- [ ] Live-mode **code** is wired for the full allowed stack and **degrades on this laptop** (no VSS): VSS client, Cosmos Reason BOM prompt, YOLO detections as occlusion, Cosmos Embed1 kNN, W&B prior/tracking when keys exist. Do not call Canary. Do not rebuild DataEngine. Do not Docker. Do not require the workshop cluster to finish this handoff.
- [ ] Remote `github` exists and `git ls-remote github HEAD` matches local HEAD. If `origin` works, it matches too. `scripts/push_both.sh` pushes all configured remotes and **fails closed** if any configured remote fails. Prefer: origin then github. If origin is missing, push github only but say so in Report back.
- [ ] README / AGENTS.md: remaining human work on **this machine** is film (`docs/FILM_THE_KITS.md`) → `~/kit-clips` named `kit-<kit_id>_unit-<nnn>.mp4`. Later, on the **workshop VM**, an ingest agent runs `.cursor/handoffs/ingest-kits.md`. Operator on laptop (now) or `/app` (event) only approves the gate.
- [ ] `.cursor/adversarial/YYYYMMDD-cowork.md` has Attack / Expected / Result / Fix with Result: pass on the required attacks. No empty checklists.
- Out of scope this session: filming, YouTube, workshop login, kubectl, attending the hackathon, `docker`, DataEngine edits, native apps, changing BOM unless a new kit appears in filenames.

## Context

Scribner is a LEGO kit completeness QC gate for the VAST Builders Challenge. `tools/scribner/kits.py` is the BOM. Cosmos captions must stay labeled prose (`PRESENT:` …) because VSS strips JSON; custom_prompt ≤800 chars. Learning is numpy logistic regression in `learn.py` anchored to `prior_logit` (`w0[1]=1`). App is flat imports under `tools/scribner/` for later ConfigMap deploy at Ingress **`/app`**. Change the UI so the **operator judges the gate**, not “is this a car.” YOLO has no LEGO classes. Own footage only. False PASS (incomplete kit auto-passed) is the failure poka-yoke must make hardest. This laptop runs **mock** until clips are uploaded on the VM.

## Never

- Do not ingest internet/YouTube video (reject by URL/host check if a path is a URL).
- Do not print `/config`, JWTs, passwords, `WANDB_API_KEY`, or GitHub tokens. Never run bare `env`.
- Do not `git add` mp4/zip/clips (`push_both` must refuse).
- Do not add sklearn/scipy/torch/node_modules; ConfigMap ≲ 1 MiB.
- Do not treat localhost as the **event** deliverable. Event app is K8s `/app`. Localhost is correct for **this laptop closeout**.
- Do not block waiting for workshop `/config` or a VM. Mock is enough.
- Do not skip GitHub because Origin already has the code. Josh’s machine must have a github.com URL.
- Do not ask Josh which button labels to use. Use the Operator spec below.
- Do not rebuild VSS / DataEngine. Do not docker.
- Do not AUTO_PASS when caption is inconsistent, confidence is LOW, UNCLEAR is nonempty, or occlusion is true.
- Do not accept operator “Gate was right” on HOLD, or “Gate was wrong” with empty/agree reason.
- Do not skip adversarial review because “the happy path works.”

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Repo on this laptop | folder with `AGENTS.md`; clone Origin branch `cursor/lego-kit-qc-gate-72e3` if you can, else use Josh’s existing folder | yes |
| GitHub | `gh auth status` or git credentials to github.com; create public repo if 404 | yes |
| Origin | only if this laptop can authenticate to origin.cursor.com | no |
| Python | 3.12 + pip: fastapi uvicorn requests numpy pydantic openai | yes |
| ffmpeg | for mock `/clip` | yes (install if missing) |
| Footage | not required for this session | no |
| Workshop `/config` | does not exist here | n/a |

## Procedure

1. **Orient on this laptop.**

```sh
pwd
test -f AGENTS.md
git status -sb
git remote -v
git branch --show-current
python3 --version
which ffmpeg || echo "INSTALL ffmpeg"
gh auth status || true
```

If not on `cursor/lego-kit-qc-gate-72e3` and the branch exists: checkout and pull. If the folder is empty: clone Origin if auth works; otherwise stop with `blocked: no Scribner tree on this machine` (Josh must open the Cursor/Origin project or paste the folder). Do **not** invent a blank app.

2. **GitHub remote (required on this machine).**

```sh
gh api user --jq .login
```

`GITHUB_REPO` if set, else `https://github.com/<login>/Scribner.git`. Create public repo if 404 (`gh repo create Scribner --public --source=. --remote=github` or `git remote add github …` then `gh repo create`). Push this branch and `main` to `github`.

If Origin works: keep `origin` pointing at origin.cursor.com. Do not delete it.

3. **Add `scripts/push_both.sh`** (executable). Behavior on **this laptop**:

- Refuse if staged/working tree contains `*.mp4`, `*.zip`, or `*.config` except `*.example`.
- Push `HEAD` to every remote in `origin` and `github` that exists.
- If both exist: origin first, then github.
- If only github exists: push github, print `origin skipped`.
- **Exit non-zero** if any attempted push fails.

Use it after every commit.

4. **Operator UI on localhost (required).** Edit `tools/scribner/static/index.html` + `state.py` / `main.py` as needed.

- Title: **Operator — kit QC gate**. Subtitle: approve or override the gate. No “reviewer”, no “engineer”.
- Unit card: autoplay `/clip`, kit name, BOM missing/present/unclear, caption, `p_fail`, chip AUTO_PASS / AUTO_FAIL / HOLD, occlusion, prior rationale, **inconsistent** if COMPLETE=YES and missing nonempty (or COMPLETE=NO and missing empty and unclear empty).
- Precedents: up to 3 nearest labeled units (Embed1 cosine if vectors exist; else caption-tag overlap).
- Actions (UI disabled + API 400 — poka-yoke):
  - **A / “Gate was right”**: AUTO_PASS → COMPLETE; AUTO_FAIL → INCOMPLETE; **HOLD: disabled, API rejects**.
  - **O / “Gate was wrong”**: COMPLETE or INCOMPLETE **and** reason chip **not** `agree`. Empty reason → reject.
  - HOLD: operator must choose COMPLETE or INCOMPLETE.
  - Override AUTO_PASS → INCOMPLETE: 1-click. Override AUTO_FAIL → COMPLETE: second confirm (`confirm_escape=true`). Missing confirm → 400.
- Metrics: coverage, HOLD rate, operator agreement, HOLD band, n_labels, **false-pass risk** (AUTO_PASS with LOW/UNCLEAR/inconsistent must stay 0).
- Audit autos stay in the queue.

`POST /api/review` may add `gate_ok`, `confirm_escape`. Persist `overrode`. Extend tests; do not drop existing ones.

5. **Poka-yoke in gate and ingest (required).** Mistakes bounce; they do not warn-and-continue.

| Mistake to make impossible | Implementation |
|---------------------------|----------------|
| Incomplete kit AUTO_PASS | `gate.py`: `complete is False` or `part_ids_missing` nonempty → never AUTO_PASS |
| Unclear / LOW / occlusion AUTO_PASS | force HOLD or fail-closed, never PASS |
| COMPLETE=YES and MISSING nonempty | `inspection.py` `inconsistent=True`; gate HOLD |
| Operator agrees on HOLD | API 400; UI disables A |
| Override with no reason | API 400 |
| Escaping a fail with one misclick | double-confirm AUTO_FAIL → COMPLETE |
| Bad clip names / unknown kit | regex `kit-<kit_id>_unit-<nnn>.(mp4\|mov\|webm\|mkv\|avi)`; unknown kit_id skip, do not guess |
| Prompt >800 chars | refuse upload if `len(custom_prompt)>800` |
| YouTube/http(s) as “file” | reject youtube, youtu.be, or http(s) except a VSS host |
| Secrets / clips committed | `push_both.sh` refuse |
| Deploy to `/` | Ingress `/app` only in `deploy/DEPLOY.md` / skill (docs only this session) |

6. **Stack wiring in code** (must run without VSS on this laptop). Graceful degrade.

| Piece | How you must use it |
|-------|---------------------|
| VAST S3 + DataEngine + VastDB | VSS APIs in `vss_client.py`; live only when `SCRIBNER_MOCK=0` and `VSS_URL` set |
| Cosmos Reason | BOM `prompt_for_kit`; live captions from metadata |
| YOLO11 | `GET /videos/detections`; occlusion if person/hand; show classes on operator card. Never brick ID |
| Cosmos Embed1 | `$COSMOS_EMBED1_URL/v1/embeddings` + bearer if present; 256-d; kNN; skip if unreachable |
| W&B Inference | `llm.py` when `WANDB_API_KEY` set |
| W&B tracking | `tracking.py` on retrain |
| Skills | keep `.cursor/skills/*` accurate after UI rename |
| Canary-1B | do not wire |

On this laptop, `SCRIBNER_MOCK=1` is the default you demo.

7. **Adversarial review on all development (required, every change).** After each logical change, **before** commit, write `.cursor/adversarial/YYYYMMDD-cowork.md`:

```
## Change: <file or feature>
Attack: <rushed operator, bad caption, hostile filename>
Expected poka-yoke: <rejected / HOLD / fail-closed>
Result: pass | fail
Fix: <change or n/a>
```

Run these for real (tests or mock API), not just list them:

- Caption COMPLETE:YES + MISSING: 4 black wheels → must not AUTO_PASS.
- Caption CONFIDENCE:LOW COMPLETE:YES → must not AUTO_PASS.
- Occlusion true + complete yes → must not AUTO_PASS.
- POST review gate_ok=true on a HOLD unit → 400.
- POST override AUTO_FAIL→COMPLETE without confirm_escape → 400.
- POST override with reason=agree or empty → 400.
- Filename `random.mp4` or kit_id `spaceship` → skip/reject.
- Prompt 801 chars → reject.
- Path `https://www.youtube.com/watch?v=…` → reject.
- `push_both` dry-run with a `.mp4` staged → refuse.

Put cases in `tools/scribner/tests/test_poka_yoke.py`. If an attack succeeds, **fix before any other feature**. Re-run. Log Result: pass.

8. **Tests.** Keep `test_scribner.py`. Add poka-yoke tests. Operator mapping tested. Oracle coverage ≥ cold coverage. Hidden-side / low-confidence must not all AUTO_PASS at cold start.

9. **Docs.** AGENTS.md + README: **Operator** (this laptop UI) vs **Ingest agent** (workshop VM later). Josh remaining: film per `docs/FILM_THE_KITS.md` into `~/kit-clips`. Dual push. False PASS is the red line. Every change needs an adversarial note.

10. **Commit and push from this machine** (only after adversarial file exists and poka-yoke tests exist).

```sh
git add -A
git status   # no mp4, no .config secrets
git commit -m "Operator QC console, poka-yoke false-PASS, adversarial tests; mirror GitHub."
./scripts/push_both.sh
```

Further commits: adversarial delta + tests + push_both each time.

## Verification

```sh
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR=/tmp/scribner-cowork python3 - <<'PY'
from state import AppState
s=AppState(mock=True); s.scan(); m=s.run_gate()["metrics"]
assert m["n"]>=30
q=s.queue(); assert q, "expected HOLD or audit queue"
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
# start ./scripts/run_mock.sh if needed
curl -sS http://127.0.0.1:8080/ | grep -E "Operator|Gate was right"
ls .cursor/adversarial/*cowork.md
git remote -v
git ls-remote github HEAD
```

Pass: tests OK including poka-yoke; no AUTO_PASS on low/missing/inconsistent/occlusion; HTML has Operator + Gate was right; A disabled on HOLD; adversarial Results are pass; github HEAD matches local. Fail: fix or `status: blocked` with the failing command.

## Report back

```
handoff: chatgpt-cowork
status: done | blocked | partial
machine: josh-laptop
checks:
- tests: pass | fail
- poka_yoke_tests: pass | fail
- adversarial_review: pass | fail
- operator_ui_localhost: pass | fail
- stack_wired_in_code: pass | fail | partial
- origin_push: pass | fail | skipped (no origin auth)
- github_remote: pass | fail
- github_push: pass | fail
- footage_only_remaining: pass | fail
artifacts:
- branch: cursor/lego-kit-qc-gate-72e3
- github: https://github.com/<owner>/Scribner
- adversarial: .cursor/adversarial/<file>
- mock: SCRIBNER_MOCK=1 ./scripts/run_mock.sh → http://127.0.0.1:8080
next: Josh films to ~/kit-clips on this laptop; later VM ingest-kits; operator uses UI
```

## Stop and escalate

Write `status: blocked` and stop if: no Scribner tree on this laptop and Origin clone fails; cannot authenticate to GitHub after one `gh auth login` / token attempt; tests fail after two fix cycles; a false-PASS attack still reproduces after one fix cycle; you think you need the workshop VM to finish (you do not — mock is enough). Do not invent a GitHub URL you did not push to.
