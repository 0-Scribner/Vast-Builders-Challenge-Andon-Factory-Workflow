# Handoff: build all of Scribner on Bryce's laptop (ChatGPT Cowork)

You are ChatGPT Cowork on **Bryce's personal computer**. You do the **entire build** on this machine. Do not wait for Cursor Cloud, a workshop VM, or another agent. Do not ask Bryce to write code, design UX, or choose libraries. Do not leave “finish this on the VM” except the later **clip upload** at the event.

After you are done, Bryce's only jobs are: (1) film LEGO kits, (2) put files in `~/kit-clips`, (3) sit as **Operator** in the UI and say whether the QC gate was right.

**Poka-yoke** (make the wrong action impossible) and **adversarial review** (attack every change before commit) are mandatory. False PASS (incomplete kit marked complete) is the red line.

## Receiver

ChatGPT Cowork, Bryce's laptop. CWD = a local folder that will be the Scribner git repo (`AGENTS.md` at root when done). Tools you may install locally: Python 3.12, pip, ffmpeg, git, GitHub CLI. Workshop `/config`, kubectl, DataEngine, and origin.cursor.com are **optional**. GitHub on this machine is **required**. Mock mode is how you develop and demo on this laptop.

## Done when

- [ ] A git repo on this laptop contains the full app under `tools/scribner/` (FastAPI, operator UI, numpy HITL scorer, mock 40 units, tests).
- [ ] `PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v` all OK, including `test_poka_yoke.py`.
- [ ] `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` → `http://127.0.0.1:8080` Operator UI: A = gate was right, O = gate was wrong, HOLD requires a verdict, illegal actions API 400 + UI disabled.
- [ ] Live clients exist in code for the full allowed stack and degrade if env vars are missing (this laptop has no VSS).
- [ ] Public GitHub repo exists; `git ls-remote github HEAD` (or `origin` if that remote IS github.com) matches local HEAD. `scripts/push_both.sh` pushes every configured remote and fails closed. After every commit you push to GitHub from this laptop.
- [ ] `.cursor/adversarial/YYYYMMDD-cowork.md` has real attacks with Result: pass.
- [ ] README: remaining human work is film → `~/kit-clips`. Operator uses localhost now, `/app` at the event.
- Out of scope: filming, YouTube, docker, DataEngine rebuild, native apps, attending the event, needing `/config` to finish.

## Context

Product: LEGO kit completeness QC gate for the VAST Builders Challenge. Each clip = one kit. Cosmos Reason (on the event stack) describes the kit using a bill-of-materials prompt; you parse PRESENT/MISSING/UNCLEAR/COMPLETE/CONFIDENCE. A logistic scorer anchored to that prior AUTO_PASS / AUTO_FAIL / HOLD. The human is an **operator who judges the gate**, not an engineer labeling cars.

BOMs in `tools/scribner/kits.py` only: **race-car** (4 black wheels, 1 clear windshield, 1 red roof, 2 yellow headlights, 1 minifigure with a hat, 1 blue door) and **front-loader** (1 yellow bucket, 4 black wheels, 1 black cabin, 1 gray roll bar, 1 yellow body, 1 minifigure). Custom prompt ≤800 chars, labeled prose, no JSON (VSS strips JSON). YOLO has no LEGO classes (occlusion only). App must stay ConfigMap-small (≲1 MiB, numpy only, no sklearn/torch/node). Event Ingress path `/app`. Own footage only.

If this laptop already has a Scribner clone (from Cursor/Origin branch `cursor/lego-kit-qc-gate-72e3`), **extend that tree**. If the folder is empty, **create the full repo here**. Do not wait for Origin if GitHub works.

## Never

- Do not ingest YouTube/internet video.
- Do not print tokens, passwords, `WANDB_API_KEY`. Never bare `env`.
- Do not `git add` mp4/zip/real `*.config`.
- Do not docker; do not rebuild VSS/DataEngine.
- Do not require the workshop VM to finish the build.
- Do not AUTO_PASS on inconsistent caption, MISSING nonempty, LOW confidence, UNCLEAR nonempty, or occlusion.
- Do not allow “Gate was right” on HOLD, or override with empty/`agree` reason.
- Do not skip adversarial review.
- Do not skip pushing to github.com from this laptop.

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Work folder | Cowork workspace / clone | yes |
| GitHub auth | `gh auth login` or git credentials | yes |
| Python 3.12 + ffmpeg | this laptop | yes |
| Origin remote | only if laptop can reach origin.cursor.com | no |
| Workshop VSS | event only | no |
| Footage | after you finish | no |

## Procedure

1. **Repo on this laptop.** `test -f AGENTS.md && test -d tools/scribner` → continue from that tree. Else scaffold the same layout: `AGENTS.md`, `README.md`, `docs/FILM_THE_KITS.md`, `prompts/`, `tools/scribner/*`, `.cursor/skills`, `.cursor/rules`, `deploy/DEPLOY.md`, `scripts/`. `git init` if needed. Branch `cursor/lego-kit-qc-gate-72e3` or `main` if you create fresh; put GitHub default branch as whatever you push, and tell Report back.

2. **GitHub (required).** `gh api user --jq .login`. Remote `github` = `GITHUB_REPO` or `https://github.com/<login>/Scribner.git`. Create public repo if 404. Push. If Origin also works, keep it and push both.

3. **`scripts/push_both.sh`.** Refuse staged `*.mp4` `*.zip` real `*.config`. Push HEAD to `origin` if present, then `github`. Exit nonzero on any failed push. Use after every commit.

4. **Build the app** (implement or finish; files are the contract). Sibling imports so `cd tools/scribner && python3 main.py` works (ConfigMap style).

- `kits.py` — BOMs, `prompt_for_kit`, `CUSTOM_PROMPT_MAX=800`, `CAMERA_ID=kit-station-1`, `LOCATION=kit-bench`, `CAPTURE_TYPE=general`, reason codes.
- `inspection.py` — parse labeled prose; `inconsistent=True` if COMPLETE=YES and missing nonempty.
- `features.py` / `learn.py` — `w0[1]=1` on `prior_logit`; numpy logistic; Beta-smoothed T_pass/T_fail that only narrow.
- `gate.py` — AUTO_PASS/AUTO_FAIL/HOLD + 10% audit; **never AUTO_PASS** if incomplete, missing parts, LOW, UNCLEAR nonempty, occlusion, inconsistent.
- `llm.py` — heuristic prior; W&B if `WANDB_API_KEY`.
- `vss_client.py` — login, explore, metadata, detections, stream, search, upload.
- `mock_data.py` — ≥40 units: complete, missing-wheels/roof/bucket/minifig, hidden-door, hands.
- `scan.py` — mock or live; kit_id from `kit:` tags / filename; YOLO occlusion.
- `state.py` / `store.py` / `report.py` / `tracking.py` / `main.py` FastAPI `/` `/health` `/api/*` `/clip`.
- `static/index.html` Operator UI (below).
- `ingest` helpers: filename regex `kit-<kit_id>_unit-<nnn>.(mp4|mov|webm|mkv|avi)`; unknown kit skip; prompt>800 reject; YouTube/http file reject.

5. **Operator UI** at `/`:

- Title **Operator — kit QC gate**.
- Card: video, BOM, caption, p_fail, decision chip, occlusion, inconsistent, precedents.
- **A** gate was right: AUTO_PASS→COMPLETE, AUTO_FAIL→INCOMPLETE; HOLD disabled + API 400.
- **O** gate was wrong: verdict + reason ≠ agree; empty reason 400.
- HOLD: must pick COMPLETE/INCOMPLETE.
- AUTO_FAIL→COMPLETE: `confirm_escape=true` or 400.
- Metrics: coverage, HOLD rate, agreement, HOLD band, n_labels, false-pass risk = 0.

6. **Stack in code** (degrade on laptop): VSS APIs; Cosmos Reason via BOM prompt; YOLO detections as occlusion; Embed1 256-d kNN if URL set; W&B prior+log if key set; do not wire Canary.

7. **Adversarial review every change** before commit. File `.cursor/adversarial/YYYYMMDD-cowork.md`. Run and test:

- COMPLETE:YES + MISSING: 4 black wheels → not AUTO_PASS
- CONFIDENCE:LOW COMPLETE:YES → not AUTO_PASS
- occlusion + complete yes → not AUTO_PASS
- POST gate_ok=true on HOLD → 400
- AUTO_FAIL→COMPLETE without confirm_escape → 400
- override reason=agree or empty → 400
- `random.mp4` or kit `spaceship` → reject
- 801-char prompt → reject
- `https://www.youtube.com/watch?v=…` → reject
- push_both with staged mp4 → refuse

If an attack succeeds, fix before any other feature.

8. **Docs + film sheet.** Operator vs later VM ingest. `docs/FILM_THE_KITS.md`: 4.0–4.8s, kit fills frame, white paper, no hands, 1080p, names `kit-race-car_unit-001.mp4`. ~40 clips.

9. **Commit from this laptop and push GitHub** (and Origin if present).

```sh
python3 -m pip install -q fastapi uvicorn requests numpy pydantic openai
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
git add -A && git status
git commit -m "Scribner operator QC gate with poka-yoke and adversarial tests."
./scripts/push_both.sh
SCRIBNER_MOCK=1 ./scripts/run_mock.sh
```

## Verification

```sh
PYTHONPATH=tools/scribner python3 -m unittest discover -s tools/scribner/tests -v
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR=/tmp/scribner-cowork python3 - <<'PY'
from state import AppState
s=AppState(mock=True); s.scan(); m=s.run_gate()["metrics"]
assert m["n"]>=30
assert s.queue()
dec={d["unit_id"]:d for d in s.store.load_decisions()}
for u in s.store.load_units():
    d=dec[u["id"]]; insp=u.get("inspection") or {}
    if d["decision"]=="AUTO_PASS":
        assert insp.get("complete") is True and not insp.get("missing")
        assert insp.get("confidence")!="low" and not u.get("occlusion") and not insp.get("inconsistent")
print("ok", m["coverage"])
PY
curl -sS http://127.0.0.1:8080/ | grep -E "Operator|Gate was right"
git ls-remote github HEAD
ls .cursor/adversarial/*cowork.md
```

Pass: tests + poka-yoke green; localhost Operator UI; GitHub HEAD = local; adversarial Results pass. Fail: fix or blocked.

## Report back

```
handoff: chatgpt-cowork
status: done | blocked | partial
machine: bryce-laptop
checks:
- tests:
- poka_yoke_tests:
- adversarial_review:
- operator_ui_localhost:
- github_push:
- origin_push: pass | fail | skipped
- footage_only_remaining:
artifacts:
- github: https://github.com/<owner>/Scribner
- mock: http://127.0.0.1:8080
next: Bryce films to ~/kit-clips; operator uses UI; event VM upload later
```

## Stop and escalate

Blocked if: cannot auth to GitHub after one login attempt; tests fail twice; false-PASS still reproduces after one fix; you think you need the workshop VM to finish (you do not). Do not invent a GitHub URL you did not push.
