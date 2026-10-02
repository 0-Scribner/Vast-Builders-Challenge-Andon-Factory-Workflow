# Handoff: full Scribner Primary build on Bryce's laptop (ChatGPT Cowork)

You are ChatGPT Cowork on **Bryce's personal computer**. Bryce is already logged into the services this job needs (GitHub, W&B, git remotes, browser sessions). Use those sessions. Do not wait for Cursor Cloud or the workshop VM. Do the remaining laptop work here. After you finish, Bryce only re-ingests Pack C on the workshop VM (or sits as Operator on mock).

Primary is the **warehouse near-miss / path-clear gate** on official Pack C. Plan B (LEGO completeness) is a separate branch — do not check it out or merge it into this work.

## Receiver

ChatGPT Cowork, Bryce's laptop. CWD = Scribner repo (`AGENTS.md` at root when done). This machine has a browser; run `gh auth login` / `wandb login` only if status shows logged-out. Official stack clone is public. Workshop `/config` is optional.

## Done when

- [ ] Repo on this laptop is a continuation of Origin branch `cursor/warehouse-primary-72e3` (or a complete scaffold if Origin is unreachable), with Operator UI **A/O + C/U**, `scripts/push_both.sh`, tests, mock 40 Pack C units.
- [ ] `export BUILDERS_CHALLENGE_DIR=/tmp/vast-builders-challenge && ./scripts/run_adversarial.sh` all OK.
- [ ] `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` → `http://127.0.0.1:8080` subtitle **Pack C aisle gate · person close to a moving vehicle**; A/C = CLEAR; O/U = UNSAFE; HOLD cannot `gate_ok`; illegal POST → 400; red-line banner present; footer names VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor.
- [ ] `curl -sS http://127.0.0.1:8080/health` contains `vast-builders-challenge`, `"canary_wired": false`, `"product":"warehouse-near-miss"`, `"line":"primary"`, `"corpus":"provided"`, `person close to a moving vehicle`.
- [ ] Logged-in services used: GitHub push succeeded; W&B prior path works if `WANDB_API_KEY` is set (no crash if unset); VSS `POST /api/v1/auth/login` smoke ran if `INGRESS_URL` is set (do not fail the build on 401).
- [ ] Public GitHub `HEAD` equals local `HEAD`. Origin pushed if that remote works. `./scripts/push_both.sh` after every commit.
- [ ] `.cursor/adversarial/YYYYMMDD-cowork.md` has Attack / Expected / Result: pass for every attack in Procedure step 8.
- Out of scope: filming, YouTube, docker, DataEngine rebuild, native apps, needing the workshop VM to finish, merging Plan B LEGO completeness.

## Context

Warehouse near-miss HITL for the VAST Builders Challenge **provided videos** (Pack C `sdg_warehouse_cam-2`). Clip = one aisle segment. Cosmos Reason captions a PATH_CLEAR / NEAR_MISS prompt; parser + prior-anchored logistic → AUTO_CLEAR / AUTO_ALERT / HOLD. Operator marks CLEAR / UNSAFE. False CLEAR is the red line. YOLO person/vehicle corroborates; it must not sole-source AUTO_CLEAR.
Only allowed stack: https://github.com/vast-data/vast-builders-challenge (`config.example`, `.cursor/skills`). No invented VSS routes. No Canary. Ingress `/app`.
Scenes in `tools/scribner/kits.py`: `warehouse-aisle` (Pack C) and `person-near-vehicle` (cross-pack). Prompt ≤800, labeled prose, no JSON.
ConfigMap ≲1 MiB, numpy only. Origin already has the Primary app; you finish laptop wiring, push GitHub.

## Never

- Do not print tokens, passwords, JWTs, `WANDB_API_KEY`. Never bare `env`. Names only: `env | cut -d= -f1 | sort`.
- Do not ingest YouTube/internet video. Do not `git add` mp4/zip/real `*.config` / `.env`.
- Do not docker; do not rebuild VSS/DataEngine; do not hardcode GPU host `166.19.38.112`.
- Do not AUTO_CLEAR if inconsistent caption, NEAR_MISS YES, named hazards, LOW, UNCLEAR nonempty, view blocked, or YOLO person+vehicle without HIGH PATH_CLEAR.
- Do not allow A / `gate_ok=true` on HOLD. Override reason cannot be empty/`agree`. AUTO_ALERT→CLEAR needs `confirm_escape=true`.
- Do not call `/api/v1/reports`, `/alerts`, `/analytics`, `/videos/ask`, `/tags`, `/locations`, `/extra-metadata`.
- Do not wire `$CANARY_1B_URL`. Do not send `scenario` with `custom_prompt`.
- Do not skip GitHub push. Do not invent a GitHub URL you did not push. Do not skip adversarial vs the official clone.
- Do not check out `cursor/plan-b-lego-completeness-72e3` into this tree. Do not restore PRESENT/MISSING/COMPLETE as the operator control.
- Do not build a hard-hat / PPE detector.

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Work folder | Cowork workspace | yes |
| Official stack | clone `https://github.com/vast-data/vast-builders-challenge` → `BUILDERS_CHALLENGE_DIR` | yes |
| Scribner origin | `git clone` Origin `bryce-mcg/Scribner` branch `cursor/warehouse-primary-72e3` if reachable; else this folder | yes |
| GitHub | already logged in (`gh auth status`) | yes |
| W&B | already logged in (`wandb login` / `WANDB_*` in `.env`) | use if present |
| VSS | `INGRESS_URL`+`USERNAME`+`PASSWORD` in env or `.env` from `/config/<team>.config` | use if present |
| GPU NIMs | `COSMOS3_REASON_URL`, `YOLO_URL`, `COSMOS_EMBED1_URL`, optional `GPU_BEARER_TOKEN` | use if present |
| Python 3.12 + ffmpeg + git + gh | this laptop | yes |

If `.env` exists, `set -a && source .env && set +a`. Copy `.env.example` if missing. Never commit `.env`.

## Procedure

1. **Login audit (no secrets).** Record only yes/no.

```sh
gh auth status >/dev/null && echo github=yes || { gh auth login; gh auth status >/dev/null && echo github=yes; }
command -v wandb >/dev/null && wandb status >/dev/null && echo wandb=yes || echo wandb=no
test -n "${WANDB_API_KEY:-}" && echo wandb_key=yes || echo wandb_key=no
test -n "${INGRESS_URL:-}${VSS_URL:-}" && echo vss=yes || echo vss=no
test -n "${COSMOS3_REASON_URL:-}" && echo gpu=yes || echo gpu=no
git remote -v
```

If GitHub is no after one `gh auth login`, stop (blocked). Do not print `gh auth token`.

2. **Official stack clone (required).**

```sh
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
test -f "$BUILDERS_CHALLENGE_DIR/config.example" || git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git "$BUILDERS_CHALLENGE_DIR"
test -f "$BUILDERS_CHALLENGE_DIR/config.example"
# Read: config.example, BUILD_DAY.md, .cursor/skills/ingest/upload-video/SKILL.md,
# retrieval/README.md, gpu/README.md, deployment/deploy-app-no-registry/SKILL.md
```

3. **Scribner tree.** Prefer Origin branch already pushed.

```sh
if test -f AGENTS.md && test -d tools/scribner; then
  git fetch origin cursor/warehouse-primary-72e3 2>/dev/null || true
  git checkout cursor/warehouse-primary-72e3 2>/dev/null || true
else
  git clone --branch cursor/warehouse-primary-72e3 origin.cursor.com:git/bryce-mcg/Scribner.git Scribner \
    || git clone --branch cursor/warehouse-primary-72e3 https://github.com/$(gh api user --jq .login)/Scribner.git Scribner \
    || true
  test -f AGENTS.md || echo "scaffold from this handoff file map; do not wait"
fi
```

Extend this tree. Do not start over if `tools/scribner/main.py` exists. Do not merge Plan B.

4. **GitHub remote + `scripts/push_both.sh`.** Login is already done.

```sh
LOGIN="$(gh api user --jq .login)"
git remote get-url github 2>/dev/null || git remote add github "https://github.com/${LOGIN}/Scribner.git"
gh repo view "${LOGIN}/Scribner" >/dev/null 2>&1 || gh repo create "${LOGIN}/Scribner" --public --source . --remote github --push
test -x scripts/push_both.sh
./scripts/push_both.sh
```

`push_both.sh` must refuse staged `*.mp4` `*.zip` `.env` real `*.config`, push `origin` if present then `github`, exit nonzero on any failed push. After every later commit, run it.

5. **Python deps.**

```sh
python3 -m pip install -q fastapi uvicorn requests numpy pydantic openai
command -v ffmpeg >/dev/null || echo "ffmpeg missing — mock clip may be empty; do not block"
```

6. **Keep the Primary warehouse pipeline.** Sibling imports (`cd tools/scribner && python3 main.py`). Keep ConfigMap-small.

- Keep: `kits.py` (Pack C `warehouse-aisle` + cross-pack `person-near-vehicle`), `inspection.py` (inconsistent if PATH_CLEAR YES and NEAR_MISS YES), `features.py`/`learn.py` (`w0[1]=1`, FEATURE_VERSION 3), `gate.py` fail-closed AUTO_CLEAR/AUTO_ALERT/HOLD, `llm.py` (W&B if key), `vss_client.py` (official routes only), `gpu_client.py` (env URLs, no Canary, YOLO corroboration), `builders_stack.py`, `ingest.py`, `mock_data.py` ≥40 Pack C units, `scan.py` (Pack C camera filter + yolo flags), `state.py` (poka-yoke review), `store.py`, `main.py` `/health` stack pin.
- **UI** `tools/scribner/static/index.html`: subtitle **Pack C aisle gate · person close to a moving vehicle**. Card: video, PATH_CLEAR / NEAR_MISS strip, caption, p_fail, decision, YOLO flags. **A/C** CLEAR. **O/U** UNSAFE. HOLD: must pick CLEAR/UNSAFE. AUTO_ALERT→CLEAR: `confirm_escape=true`. Metrics: coverage, HOLD rate, auto clear, auto alert, HOLD band, n_labels. Footer: stack line. Banner: False CLEAR is the red line.
- Live degrade: if `WANDB_API_KEY` set, prior may use `https://api.inference.wandb.ai/v1` (no crash on failure). If `INGRESS_URL`/`VSS_URL` set, `VssClient().login()` once; 401 = report `vss=fail` and continue mock. If GPU URLs set, do not call Canary; optional YOLO `/healthz` only.

7. **Logged-in service smoke (optional live, required to attempt).**

```sh
# W&B: names only
python3 - <<'PY'
import os
print("wandb_key", "yes" if os.environ.get("WANDB_API_KEY") else "no")
print("wandb_team", "yes" if os.environ.get("WANDB_TEAM") else "no")
PY
# VSS login if URL present — never print the token
if test -n "${INGRESS_URL:-${VSS_URL:-}}"; then
  PYTHONPATH=tools/scribner python3 - <<'PY'
from vss_client import VssClient, VssError
try:
    VssClient().login()
    print("vss_login=ok")
except Exception as e:
    print("vss_login=fail", type(e).__name__)
PY
fi
```

Do not dump JSON from login.

8. **Adversarial every change** before commit. Write `.cursor/adversarial/YYYYMMDD-cowork.md`. Run `./scripts/run_adversarial.sh`. Also attack:

- PATH_CLEAR:YES + NEAR_MISS:YES → not AUTO_CLEAR (AUTO_ALERT)
- CONFIDENCE:LOW PATH_CLEAR:YES → not AUTO_CLEAR
- occlusion / view_blocked + path clear yes → not AUTO_CLEAR
- YOLO person+vehicle without HIGH PATH_CLEAR → not AUTO_CLEAR
- POST `gate_ok=true` on HOLD → 400
- AUTO_ALERT→CLEAR without `confirm_escape` → 400
- override reason=agree or empty → 400
- `random.mp4` / kit `spaceship` / 801-char prompt / YouTube URL → reject
- `push_both` with staged mp4 → refuse
- source contains `/api/v1/reports` or hardcoded `166.19.38.112` or Canary transcriptions → fail
- `/health` missing `vast-builders-challenge` or `warehouse-near-miss` → fail
- UI missing payoff query or AUTO_CLEAR / UNSAFE → fail

If an attack succeeds, fix before any other feature.

9. **Docs.** README remaining human work = re-ingest Pack C on the workshop VM. Operator uses localhost now, `/app` at the event. `docs/BUILDERS_STACK.md` names the official GitHub repo. `docs/FILM_THE_KITS.md` is the provided-corpus note (no filming required). `docs/PLAN.md` names Primary vs Plan B.

10. **Commit and push both remotes.**

```sh
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
./scripts/run_adversarial.sh
git add -A && git status
git commit -m "Scribner Primary: warehouse near-miss gate on Pack C."
./scripts/push_both.sh
SCRIBNER_MOCK=1 ./scripts/run_mock.sh
```

## Verification

```sh
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
export PYTHONPATH=tools/scribner
./scripts/run_adversarial.sh
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR=/tmp/scribner-cowork python3 - <<'PY'
from state import AppState
s=AppState(mock=True); s.scan(); m=s.run_gate()["metrics"]
assert m["n"]>=30
assert s.queue()
dec={d["unit_id"]:d for d in s.store.load_decisions()}
for u in s.store.load_units():
    d=dec[u["id"]]; insp=u.get("inspection") or {}
    if d["decision"] in {"AUTO_CLEAR","AUTO_PASS"}:
        assert insp.get("path_clear") is True and not insp.get("near_miss")
        assert not (insp.get("hazards") or insp.get("missing"))
        assert insp.get("confidence")!="low" and not u.get("occlusion") and not insp.get("inconsistent")
        if u.get("yolo_person") and u.get("yolo_vehicle"):
            assert insp.get("confidence")=="high"
print("ok", m["coverage"])
PY
# HOLD + gate_ok must 400
python3 - <<'PY'
from state import AppState
from store import Store
import tempfile
s=AppState(store=Store(tempfile.mkdtemp()), mock=True); s.scan(); s.run_gate()
hold=next(d for d in s.store.load_decisions() if d["decision"]=="HOLD")
try:
    s.review(hold["unit_id"], "CLEAR", reason="agree", gate_ok=True)
    raise SystemExit("HOLD gate_ok should 400")
except ValueError:
    print("hold_poka_yoke=ok")
PY
SCRIBNER_MOCK=1 ./scripts/run_mock.sh & sleep 2
curl -sS http://127.0.0.1:8080/health | grep -E "vast-builders-challenge|warehouse-near-miss"
curl -sS http://127.0.0.1:8080/ | grep -E "AUTO_CLEAR|False CLEAR|person close to a moving vehicle"
git ls-remote github HEAD
git rev-parse HEAD
ls .cursor/adversarial/*cowork.md
```

Pass: adversarial green; A/O UI on Pack C aisle gate; `/health` pins official repo + warehouse-near-miss; GitHub HEAD = local; Origin pushed or explicitly skipped with reason; every attack Result: pass. Fail: fix or blocked. Do not ship COMPLETE/INCOMPLETE as the operator control.

## Report back

```
handoff: chatgpt-cowork
status: done | blocked | partial
machine: bryce-laptop
logins:
- github:
- wandb:
- vss:
- gpu:
checks:
- tests:
- poka_yoke_tests:
- builders_stack_adversarial:
- adversarial_review:
- operator_ui_AO:
- health_stack_pin:
- github_push:
- origin_push: pass | fail | skipped
- footage_only_remaining:
artifacts:
- github: https://github.com/<login>/Scribner
- mock: http://127.0.0.1:8080
next: Bryce re-ingests Pack C on the workshop VM; operator uses A/O UI
```

## Stop and escalate

Stop `status: blocked` if: GitHub still logged out after one `gh auth login`; tests fail twice; false-CLEAR still reproduces after one fix; you think you need the workshop VM to finish (you do not). Do not invent a GitHub URL. Do not print secrets in Report back.
