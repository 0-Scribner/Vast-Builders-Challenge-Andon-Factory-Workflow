# Handoff: full Scribner Primary on Bryce's laptop (ChatGPT Cowork)

You are ChatGPT Cowork on **Bryce's personal computer**. Bryce is already logged into the services this job needs. **Use those sessions and CLIs now.** Do not wait for Cursor Cloud. Do not wait for the workshop VM to “be ready.” Do the remaining laptop work here.

After you finish, Bryce only **re-ingests Pack C** on the workshop VM (or sits as Operator on mock). You do not film. You do not re-upload the corpus.

Primary = warehouse near-miss / path-clear gate on official Pack C. Plan B (LEGO completeness, branch `cursor/plan-b-lego-completeness-72e3`) is backup — **do not check it out or merge it.**

## Receiver

ChatGPT Cowork, Bryce's laptop. CWD = Scribner repo (`AGENTS.md` at root when done). Browser exists. Use `gh`, `git`, `wandb`, Python, `ffmpeg`, and live HTTP to VSS / GPU / W&B Inference whenever credentials are present.

## External tools you MUST use (attempt all; degrade, don't skip)

| Tool | How you use it | Required to finish |
|------|----------------|-------------------|
| **GitHub CLI `gh`** | `gh auth status`, `gh api user`, `gh repo create/view`, public mirror | **yes** — GitHub push is a hard Done-when |
| **git remotes** | `origin` (Origin/Cursor) + `github` (github.com). `./scripts/push_both.sh` after every commit | origin: use if present; github: **yes** |
| **Official stack clone** | `git clone https://github.com/vast-data/vast-builders-challenge` → `$BUILDERS_CHALLENGE_DIR` | **yes** — adversarial vs this clone |
| **W&B Inference** | `https://api.inference.wandb.ai/v1` with `WANDB_API_KEY` (BUILD_DAY.md). `openai` client. Optional `wandb` CLI | attempt if key/login; no crash if missing |
| **W&B Weave / wandb SDK** | `wandb status`; one `wandb.init` smoke if logged in; app `tracking.py` on retrain | attempt if present |
| **VSS (VAST Video Search)** | `INGRESS_URL` or `VSS_URL` + `USERNAME`/`PASSWORD` (or `VSS_*`). Official routes only | attempt if URL set; 401 = report fail, continue mock |
| **NVIDIA Cosmos Reason NIM** | `$COSMOS3_REASON_URL` `GET /v1/models` or `/v1/health/ready` | attempt if URL set |
| **YOLO11 NIM** | `$YOLO_URL` `GET /healthz` | attempt if URL set |
| **Cosmos Embed1 NIM** | `$COSMOS_EMBED1_URL` `GET /v1/models` or `/v1/health/ready` (256-d) | attempt if URL set |
| **Optional `GPU_BEARER_TOKEN`** | `Authorization: Bearer` only when set. Do not print it | if set |
| **ffmpeg** | mock `/clip` mp4 | preferred; empty clip OK |
| **Python 3.12** | fastapi uvicorn requests numpy pydantic openai | **yes** |

Do **not** call `$CANARY_1B_URL` or `/v1/audio/transcriptions`. Do **not** Docker. Do **not** invent VSS routes.

VSS routes you MAY call: `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/config`, `/api/v1/metadata/ingest-config`, `/api/v1/search`, `/api/v1/videos/explore`, `/api/v1/tools/explore`, `/api/v1/tools/detections`, `/api/v1/videos/stream`. Forbidden: `/reports`, `/alerts`, `/analytics`, `/videos/ask`, `/tags`, `/locations`, `/extra-metadata`.

## Done when

- [ ] Laptop repo is Origin branch `cursor/warehouse-primary-72e3` (or GitHub mirror of that branch). Operator UI **A/O + C/U**. Mock 40 Pack C units.
- [ ] `export BUILDERS_CHALLENGE_DIR=$HOME/vast-builders-challenge && ./scripts/run_adversarial.sh` all OK.
- [ ] `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` → `http://127.0.0.1:8080` subtitle **Pack C aisle gate · person close to a moving vehicle**; A/C = CLEAR; O/U = UNSAFE; red-line banner; footer `VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor`.
- [ ] `curl -sS http://127.0.0.1:8080/health` contains `vast-builders-challenge`, `"canary_wired": false`, `"product":"warehouse-near-miss"`, `"line":"primary"`, `"corpus":"provided"`, `person close to a moving vehicle`.
- [ ] **Every logged-in tool was attempted** (Procedure step 7). GitHub push succeeded. W&B / VSS / GPU: `ok` or `skipped (<reason>)` — never silent skip.
- [ ] Public GitHub `HEAD` equals local `HEAD`. Origin pushed if that remote works. `./scripts/push_both.sh` after every commit.
- [ ] `.cursor/adversarial/YYYYMMDD-cowork.md` Attack / Expected / Result: pass for Procedure step 8.
- Out of scope: filming, YouTube, docker, DataEngine rebuild, workshop re-ingest of Pack C, merging Plan B, deploying `/app` (event VM).

## Context

Scribner is an aisle gate on VAST Builders Challenge **provided Pack C** (`sdg_warehouse_cam-2`, warehouse3). Cosmos Reason captions PATH_CLEAR / NEAR_MISS. Parser + prior-anchored logistic → AUTO_CLEAR / AUTO_ALERT / HOLD. Operator CLEAR / UNSAFE. False CLEAR is the red line. YOLO corroborates person/vehicle; it must not sole-source AUTO_CLEAR.

Stack lock: https://github.com/vast-data/vast-builders-challenge (`config.example`, `.cursor/skills`). Ingress `/app` at the event. Prompt ≤800, labeled prose, no JSON. ConfigMap ≲1 MiB, numpy only.

Origin already has Primary. You wire laptop logins, smoke every tool, push GitHub.

## Never

- Do not print tokens, passwords, JWTs, `WANDB_API_KEY`, `GPU_BEARER_TOKEN`, `SECRET_KEY`, `ACCESS_KEY`. Never bare `env`. Names only: `env | cut -d= -f1 | sort`.
- Do not ingest YouTube/internet video. Do not `git add` mp4/zip/real `*.config` / `.env`.
- Do not docker; do not rebuild VSS/DataEngine; do not hardcode GPU host `166.19.38.112`.
- Do not AUTO_CLEAR if inconsistent caption, NEAR_MISS YES, named hazards, LOW, UNCLEAR nonempty, view blocked, or YOLO person+vehicle without HIGH PATH_CLEAR.
- Do not allow `gate_ok=true` on HOLD. Override reason cannot be empty/`agree`. AUTO_ALERT→CLEAR needs `confirm_escape=true`.
- Do not call forbidden VSS paths. Do not wire Canary. Do not send `scenario` with `custom_prompt`.
- Do not skip GitHub push. Do not invent a GitHub URL you did not push.
- Do not check out Plan B. Do not restore COMPLETE/INCOMPLETE as the operator control. Do not build a hard-hat detector.

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Work folder | Cowork workspace | yes |
| Official stack | clone challenge repo → `BUILDERS_CHALLENGE_DIR` | yes |
| Scribner | Origin `bryce-mcg/Scribner` branch `cursor/warehouse-primary-72e3`, else GitHub | yes |
| GitHub | `gh auth status` | yes |
| `.env` | copy `.env.example`; fill from logged-in `wandb` / workshop `/config/<team>.config` if Bryce has it | use if present |
| W&B | `WANDB_API_KEY` `WANDB_TEAM` `WANDB_PROJECT` | use if present |
| VSS | `INGRESS_URL`/`VSS_URL` + user/pass | use if present |
| GPU NIMs | `COSMOS3_REASON_URL` `YOLO_URL` `COSMOS_EMBED1_URL` optional `GPU_BEARER_TOKEN` | use if present |
| Python 3.12 + ffmpeg + git + gh | this laptop | yes |

```sh
test -f .env || cp .env.example .env
set -a && source .env && set +a
# If Bryce has a workshop config on this machine (do not print values):
if test -f /config/*.config 2>/dev/null; then set -a && source /config/*.config && set +a; fi
```

Never commit `.env`.

## Procedure

1. **Login audit (no secrets).** Record only yes/no.

```sh
gh auth status >/dev/null && echo github=yes || { gh auth login; gh auth status >/dev/null && echo github=yes; }
gh api user --jq .login
command -v wandb >/dev/null && wandb status >/dev/null && echo wandb=yes || echo wandb=no
test -n "${WANDB_API_KEY:-}" && echo wandb_key=yes || echo wandb_key=no
test -n "${INGRESS_URL:-}${VSS_URL:-}" && echo vss=yes || echo vss=no
test -n "${COSMOS3_REASON_URL:-}" && echo cosmos=yes || echo cosmos=no
test -n "${YOLO_URL:-}" && echo yolo=yes || echo yolo=no
test -n "${COSMOS_EMBED1_URL:-}" && echo embed1=yes || echo embed1=no
test -n "${GPU_BEARER_TOKEN:-}" && echo gpu_bearer=yes || echo gpu_bearer=no
command -v ffmpeg >/dev/null && echo ffmpeg=yes || echo ffmpeg=no
git remote -v
env | cut -d= -f1 | sort
```

If GitHub is no after one `gh auth login`, stop (blocked). Do not print `gh auth token`.

2. **Official stack clone (required). Read the skills you will call.**

```sh
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
test -f "$BUILDERS_CHALLENGE_DIR/config.example" || git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git "$BUILDERS_CHALLENGE_DIR"
test -f "$BUILDERS_CHALLENGE_DIR/config.example"
# Read (do not skip): config.example, BUILD_DAY.md,
# .cursor/skills/ingest/upload-video/SKILL.md,
# .cursor/skills/retrieval/README.md,
# .cursor/skills/retrieval/login/SKILL.md,
# .cursor/skills/retrieval/search/SKILL.md,
# .cursor/skills/gpu/README.md,
# .cursor/skills/deployment/deploy-app-no-registry/SKILL.md
```

3. **Scribner tree.** Prefer Origin branch already pushed.

```sh
if test -f AGENTS.md && test -d tools/scribner; then
  git fetch origin cursor/warehouse-primary-72e3 2>/dev/null || true
  git checkout cursor/warehouse-primary-72e3 2>/dev/null || git checkout -B cursor/warehouse-primary-72e3 origin/cursor/warehouse-primary-72e3 2>/dev/null || true
else
  git clone --branch cursor/warehouse-primary-72e3 https://origin.cursor.com/git/bryce-mcg/Scribner.git Scribner \
    || git clone --branch cursor/warehouse-primary-72e3 origin.cursor.com:git/bryce-mcg/Scribner.git Scribner \
    || git clone --branch cursor/warehouse-primary-72e3 "https://github.com/$(gh api user --jq .login)/Scribner.git" Scribner \
    || true
  cd Scribner 2>/dev/null || true
  test -f AGENTS.md || echo "scaffold from this handoff; do not wait"
fi
```

Extend this tree. Do not start over if `tools/scribner/main.py` exists. Do not merge Plan B.

4. **GitHub remote + `scripts/push_both.sh`.**

```sh
LOGIN="$(gh api user --jq .login)"
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://origin.cursor.com/git/bryce-mcg/Scribner.git"
git remote get-url github 2>/dev/null || git remote add github "https://github.com/${LOGIN}/Scribner.git"
gh repo view "${LOGIN}/Scribner" >/dev/null 2>&1 || gh repo create "${LOGIN}/Scribner" --public --source . --remote github --push
test -x scripts/push_both.sh
./scripts/push_both.sh
```

`push_both.sh` must refuse staged `*.mp4` `*.zip` `.env` real `*.config`, push `origin` if present then `github`, exit nonzero on any failed push. After every later commit, run it.

5. **Python deps (includes W&B Inference client).**

```sh
python3 -m pip install -q fastapi uvicorn requests numpy pydantic openai wandb
command -v ffmpeg >/dev/null || echo "ffmpeg missing — mock clip may be empty; do not block"
```

6. **Keep the Primary warehouse pipeline.** Sibling imports (`cd tools/scribner && python3 main.py`). ConfigMap-small.

- Keep: `kits.py` (Pack C `warehouse-aisle` + `person-near-vehicle`), `inspection.py`, `features.py`/`learn.py` (`w0[1]=1`, FEATURE_VERSION 3), `gate.py` AUTO_CLEAR/AUTO_ALERT/HOLD, `llm.py` (W&B Inference), `vss_client.py`, `gpu_client.py` (no Canary), `builders_stack.py`, `ingest.py`, `mock_data.py` ≥40 units, `scan.py`, `state.py`, `store.py`, `main.py` `/health`.
- UI: A/C CLEAR, O/U UNSAFE, red-line banner, stack footer, payoff query in the subtitle.
- Live degrade: missing W&B/VSS/GPU → heuristic prior + mock. Never crash.

7. **Use every external tool that is logged in.** Never print secrets or response bodies that contain tokens.

```sh
export PYTHONPATH=tools/scribner
set -a && test -f .env && source .env && set +a

# --- GitHub ---
gh api user --jq '"github_login=" + .login'
gh repo view "$(gh api user --jq .login)/Scribner" --json url -q .url

# --- W&B Inference (official BUILD_DAY.md host) ---
python3 - <<'PY'
import os, json
from openai import OpenAI
key = os.environ.get("WANDB_API_KEY")
if not key:
    print("wandb_inference=skipped (no WANDB_API_KEY)")
else:
    c = OpenAI(base_url=os.environ.get("WANDB_INFERENCE_URL", "https://api.inference.wandb.ai/v1"), api_key=key)
    try:
        r = c.chat.completions.create(
            model=os.environ.get("SCRIBNER_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
            temperature=0, max_tokens=8,
            messages=[{"role":"user","content":"Reply with the single word PONG."}],
        )
        text = (r.choices[0].message.content or "").strip()
        print("wandb_inference=ok", "pong" if "PONG" in text.upper() else "got_reply")
    except Exception as e:
        print("wandb_inference=fail", type(e).__name__)
PY
command -v wandb >/dev/null && wandb status >/dev/null && echo wandb_cli=ok || echo wandb_cli=skipped

# --- VSS: login + me + ingest-config + explore + official payoff search ---
python3 - <<'PY'
import os, json
from vss_client import VssClient, VssError
url = os.environ.get("INGRESS_URL") or os.environ.get("VSS_URL") or ""
if not url:
    print("vss=skipped (no INGRESS_URL/VSS_URL)")
else:
    try:
        c = VssClient()
        c.login()
        print("vss_login=ok")
        me = c.me()
        print("vss_me=ok", "keys", sorted(me.keys())[:8] if isinstance(me, dict) else type(me).__name__)
        try:
            mx = c.prompt_max()
            print("vss_ingest_config=ok", "custom_prompt_max", mx)
        except Exception as e:
            print("vss_ingest_config=fail", type(e).__name__)
        try:
            rows = c.explore_all(scope="all")
            print("vss_explore=ok", "n", len(rows) if isinstance(rows, list) else "n/a")
        except Exception as e:
            print("vss_explore=fail", type(e).__name__)
        try:
            hits = c.search("person close to a moving vehicle", top_k=5, llm_top_n=0, min_similarity=0.3)
            n = len(hits.get("results") or hits.get("chunk_results") or [])
            print("vss_search=ok", "n", n)
        except Exception as e:
            print("vss_search=fail", type(e).__name__)
    except Exception as e:
        print("vss_login=fail", type(e).__name__)
PY

# --- GPU NIMs: Cosmos Reason, YOLO, Embed1. NEVER Canary. ---
python3 - <<'PY'
import os, requests
from gpu_client import available, _headers

print("gpu_env", available())
h = _headers()

def ping(name, url, path):
    if not url:
        print(f"{name}=skipped")
        return
    try:
        r = requests.get(url.rstrip("/") + path, headers=h, timeout=15)
        print(f"{name}={r.status_code}")
    except Exception as e:
        print(f"{name}=fail", type(e).__name__)

ping("cosmos3_reason", os.environ.get("COSMOS3_REASON_URL",""), "/v1/models")
ping("yolo", os.environ.get("YOLO_URL",""), "/healthz")
ping("embed1", os.environ.get("COSMOS_EMBED1_URL",""), "/v1/models")
print("canary_called=no")
if os.environ.get("CANARY_1B_URL"):
    print("canary_env_present_unused=yes")
PY
```

Do not dump login JSON. Do not curl Canary. 401 on VSS/GPU = `fail` + continue mock.

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
- source contains `/api/v1/reports` or `166.19.38.112` or Canary transcriptions → fail
- `/health` missing `vast-builders-challenge` or `warehouse-near-miss` → fail
- UI missing payoff query or AUTO_CLEAR / UNSAFE → fail

If an attack succeeds, fix before any other feature.

9. **Docs stay Primary.** Remaining human work after you = re-ingest Pack C on the workshop VM. Operator localhost now, `/app` at the event. Do not tell Bryce to film.

10. **Commit (only if you changed files) and push both remotes.**

```sh
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
./scripts/run_adversarial.sh
git add -A && git status
git diff --cached --quiet || git commit -m "Cowork: laptop wiring, GitHub mirror, logged-in stack smoke."
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

Pass: adversarial green; A/O UI; `/health` pins official repo + warehouse-near-miss; GitHub HEAD = local; every tool in the table was attempted; Origin pushed or skipped with reason. Fail: fix or blocked.

## Report back

```
handoff: chatgpt-cowork
status: done | blocked | partial
machine: bryce-laptop
logins:
- github:
- wandb_cli:
- wandb_inference:
- vss_login:
- vss_me:
- vss_search:
- cosmos3_reason:
- yolo:
- embed1:
- canary_called: no
checks:
- tests:
- poka_yoke_tests:
- builders_stack_adversarial:
- adversarial_review:
- operator_ui_AO:
- health_stack_pin:
- github_push:
- origin_push: pass | fail | skipped
- footage_only_remaining: re-ingest Pack C on workshop VM
artifacts:
- github: https://github.com/<login>/Scribner
- mock: http://127.0.0.1:8080
next: Bryce re-ingests Pack C on the workshop VM; operator uses A/O UI
```

## Stop and escalate

Stop `status: blocked` if: GitHub still logged out after one `gh auth login`; tests fail twice; false-CLEAR still reproduces after one fix; you think you need the workshop VM to finish the laptop job (you do not). Missing W&B/VSS/GPU is **not** blocked — record `skipped` and finish GitHub + mock. Do not invent a GitHub URL. Do not print secrets in Report back.
