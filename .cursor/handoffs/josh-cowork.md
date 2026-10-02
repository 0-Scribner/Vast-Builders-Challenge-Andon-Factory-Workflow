# Handoff: Josh's Cowork — finish Scribner Primary live connections

## Receiver

Josh's Cowork agent on Josh's computer, working in the Scribner repository.
Use Josh's existing authenticated sessions and CLIs. Origin is mandatory and is
the source of truth. GitHub is the public organization mirror.

This is a one-time integration work order. Complete the laptop work locally.
The designated workshop operator handles Pack C re-ingest and event deployment
on the team's existing VM/cluster. If Cowork has that authorized environment
available, execute those steps there; otherwise hand over the concrete commands
and report the outstanding checks. Do not wait for a cloud coding agent.

Read this file completely before making live requests. A successful mock demo
does not establish a successful live integration.

## Done when

- [ ] Origin `bryce-mcg/Scribner`, branch `cursor/warehouse-primary-72e3`, is checked out and is the upstream.
- [ ] Public GitHub mirror is **`0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow`**. Do not create a personal mirror.
- [ ] Local HEAD = Origin Primary = GitHub Primary = GitHub HEAD after each final push.
- [ ] Official challenge clone is present; all adversarial tests pass (67 at this handoff, plus tests for subsequent fixes).
- [ ] The existing mock demo still has 40 units, correct 安灯 lamps, A/C CLEAR, O/U UNSAFE, and playable green/yellow/red aisle MP4s.
- [ ] Every connection is recorded as ok, fail, or skipped with a reason. A configured URL returning 401 is fail.
- [ ] W&B Inference answers a smoke request and supplies a real app prior without weakening the hazard rules.
- [ ] A W&B SDK smoke run succeeds; an actual app retrain produces a run with `andon_line` and numeric andon metrics.
- [ ] VSS login, me, ingest-config, Pack C Explore, and the payoff search succeed with the assigned team's credentials.
- [ ] Cosmos Reason, YOLO11, and Embed1 have separate health results; Embed1 inference returns 256 numbers.
- [ ] Pack C is re-ingested by the designated workshop owner with the generated warehouse prompt; job completion and updated captions are verified.
- [ ] Live scan contains the intended `sdg_warehouse_cam-2` sources. A nonmatching camera or missing target cannot silently become a Pack C unit.
- [ ] A real Pack C segment is streamed through Scribner `/clip` and played in the operator UI with matching station lamps. Mock and live stores are separate.
- [ ] Event `/app` loads its UI, API calls, video, review, report, and retrain correctly through the actual Ingress.
- [ ] Save a new dated adversarial report, connection results, live screenshot, and final commit IDs; push Origin first and the organization mirror second.
- [ ] Out of scope: filming, internet video, corpus re-upload, Plan B merge, Docker, rebuilding VSS/DataEngine, Canary, and new infrastructure unrelated to this app.

## Context

Primary is 安灯 over provided Pack C warehouse footage: `sdg_warehouse_cam-2`, `warehouse3`.
Cosmos captions use PATH_CLEAR / NEAR_MISS; the prior-anchored numpy gate yields AUTO_CLEAR / HOLD / AUTO_ALERT.
The false-CLEAR rule is `赤灯は人なしで緑にしない`.
Bryce's laptop passed 67 tests, real mock HTTP checks, three clip-color checks, browser playback, and A/O controls.
Origin login and dual-remote pushes work; the GitHub organization mirror is public with Primary as its default branch.
No W&B key, VSS URL/credentials, GPU URLs, or GPU bearer were available on Bryce's laptop; live checks were skipped.
Read `.cursor/adversarial/20261002-cowork.md` for evidence and the exact changes already made.
Files owning remaining work: `scan.py`, `vss_client.py`, `gpu_client.py`, `llm.py`, `tracking.py`, `main.py`, `static/index.html`, `deploy/DEPLOY.md`.

## Never

- Never substitute GitHub for Origin as the upstream. Do not check out or merge Plan B.
- Never print tokens, JWTs, passwords, API keys, raw login JSON, real configuration, or Kubernetes Secret YAML. No bare `env`, shell tracing, or verbose authenticated HTTP.
- Never commit `.env`, credentials, real `*.config`, video, archives, live response dumps, local data, or `.venv`.
- Never call Canary or audio transcription. GPU URLs come from configuration, with separate endpoints per model; never hardcode a host.
- Never invent VSS routes. Read the matching official skill before adding a request. `/reports`, `/alerts`, `/analytics`, `/videos/ask`, `/tags`, `/locations`, and `/extra-metadata` are forbidden.
- Laptop connection smoke uses login, me, config, ingest-config, search, Explore, documented tool retrieval, and stream. Workshop re-ingest routes are used only in the designated re-ingest step after scope is established.
- Never rebuild DataEngine, run Docker, upload the provided corpus again, or ingest YouTube/internet footage.
- Never AUTO_CLEAR inconsistent captions, NEAR_MISS, named hazards, LOW confidence, nonempty UNCLEAR, or blocked views. YOLO person/vehicle needs HIGH PATH_CLEAR corroboration.
- Never treat every warehouse person/hand detection as occlusion. W&B must not reduce a near-miss prior below 0.8.
- Never accept `gate_ok=true` on HOLD, an empty/agree override reason, or AUTO_ALERT→CLEAR without `confirm_escape=true`.
- Never label live units with the mock oracle. A human operator supplies live CLEAR/UNSAFE decisions.
- Never call generated clips live Pack C, or use API availability as proof of a functioning UI/video/retrain integration.
- Never kill Cursor, another user's server, or a workshop service to free a port. Use an explicit local port override.
- Do not create, update, merge, or close PRs from this work order. Existing Origin PR 2 is read-only context.

## Inputs

| Name | Where | Required |
|---|---|---|
| Origin repository | `https://origin.cursor.com/git/bryce-mcg/Scribner.git` | yes |
| Primary branch | `cursor/warehouse-primary-72e3` | yes |
| GitHub mirror | `https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow.git` | yes |
| Existing Origin PR | `https://cursor.com/codebase/bryce-mcg/Scribner/pull/2` | read-only |
| Official stack | `https://github.com/vast-data/vast-builders-challenge`, tested at `4987d8e` | yes |
| Local runtime | Python 3.12, git, gh, Origin CLI, ffmpeg; requirements in `tools/scribner/requirements.txt` | yes |
| Team configuration | existing environment, local ignored `.env`, or the assigned `/config/<team>.config` on the workshop VM | live work |
| W&B | `WANDB_API_KEY`, `WANDB_TEAM`, `WANDB_PROJECT`; optionally configured `SCRIBNER_MODEL` | W&B proof |
| VSS | `INGRESS_URL`, `USERNAME`, `PASSWORD`, or `VSS_URL`, `VSS_USERNAME`, `VSS_PASSWORD` | live Pack C |
| GPU services | `COSMOS3_REASON_URL`, `YOLO_URL`, `COSMOS_EMBED1_URL`; optional `GPU_BEARER_TOKEN` | direct GPU checks |
| Cluster identity | assigned kubeconfig and this team's namespace | event deployment |
| Bryce's current local clone | `/home/mcgrath/.codex/.chatgpt-projects/g-p-6abff2d770f08191b95f214e37af34d8/Scribner-primary` | reference; Josh uses his own path |
| Bryce's verified preview | `http://127.0.0.1:8081`; port 8080 was already a Cursor connection | only on Bryce's machine |

## Procedure

1. **Get the current branch from Origin and establish the exact remotes.**

```bash
set -euo pipefail
command -v origin >/dev/null || {
  curl -fsSL https://downloads.cursor.com/origin/install.sh -o /tmp/scribner-origin-install.sh
  sh /tmp/scribner-origin-install.sh
}
export PATH="$HOME/.local/bin:$PATH"
origin auth status || origin auth login
gh auth status || gh auth login
gh api user --jq .login

export SCRIBNER_DIR="${SCRIBNER_DIR:-$HOME/Scribner}"
if [ ! -d "$SCRIBNER_DIR/.git" ]; then
  git clone --branch cursor/warehouse-primary-72e3 \
    https://origin.cursor.com/git/bryce-mcg/Scribner.git "$SCRIBNER_DIR"
fi
cd "$SCRIBNER_DIR"
cat AGENTS.md
git status --short --branch
```

If the existing checkout has unrelated changes or another active task owns it,
preserve it and use a separate Origin clone. Do not reset/stash/delete someone
else's changes. In a clean task checkout:

```bash
git remote set-url origin https://origin.cursor.com/git/bryce-mcg/Scribner.git
origin auth setup-git --local
git fetch origin cursor/warehouse-primary-72e3
git switch cursor/warehouse-primary-72e3
git merge --ff-only origin/cursor/warehouse-primary-72e3
git branch --set-upstream-to=origin/cursor/warehouse-primary-72e3
if git remote get-url github >/dev/null 2>&1; then
  git remote set-url github https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow.git
else
  git remote add github https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow.git
fi
git config --local credential.https://github.com.helper '!gh auth git-credential'
origin pr list -R bryce-mcg/Scribner --limit 5
origin pr view 2 -R bryce-mcg/Scribner
gh repo view 0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow --json url,visibility,defaultBranchRef
```

2. **Install the runtime, read the contracts, and retain the mock baseline.**

```bash
python3.12 -m venv .venv
export PATH="$PWD/.venv/bin:$PATH"
python -m pip install -r tools/scribner/requirements.txt
export PYTHONPATH="$PWD/tools/scribner"
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
test -f "$BUILDERS_CHALLENGE_DIR/config.example" || \
  git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git "$BUILDERS_CHALLENGE_DIR"
cat .cursor/skills/run-mock/SKILL.md .cursor/skills/conformance-stack/SKILL.md
./scripts/run_adversarial.sh
```

Read official `config.example`, `BUILD_DAY.md`, `.cursor/skills/retrieval/README.md`,
`retrieval/login`, `retrieval/search`, `retrieval/videos`, `gpu/README.md`,
`gpu/model-health`, `gpu/model-smoke-test`, `ingest/reingest-videos`, and
`deployment/deploy-app-no-registry` before their respective steps. User constraints
override examples that hardcode GPU hosts or mention Canary.

Use a free port, keeping existing listeners:

```bash
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR=/tmp/scribner-josh-mock PORT=8081 ./scripts/run_mock.sh
```

This command runs in a dedicated terminal. Keep it available while connecting
services. Do not reuse its store for live footage.

3. **Resolve credentials privately and record every missing dependency.**

```bash
test -f .env || cp .env.example .env
chmod 600 .env
set -a
source .env
set +a
# On the assigned workshop VM only:
if [ -d /config ]; then
  mapfile -t SCRIBNER_TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
  if [ "${#SCRIBNER_TEAM_CONFIGS[@]}" -eq 1 ]; then
    set -a
    source "${SCRIBNER_TEAM_CONFIGS[0]}"
    set +a
  fi
fi
python - <<'PY'
import os
names = ('WANDB_API_KEY','WANDB_TEAM','WANDB_PROJECT','INGRESS_URL','VSS_URL',
         'USERNAME','PASSWORD','VSS_USERNAME','VSS_PASSWORD','COSMOS3_REASON_URL',
         'YOLO_URL','COSMOS_EMBED1_URL','GPU_BEARER_TOKEN')
for name in names:
    print(name + '=' + ('set' if os.environ.get(name) else 'missing'))
PY
wandb status >/dev/null
```

Use existing logins or normal interactive login. Do not ask anyone to paste keys
into chat. If multiple team configs exist, resolve the assigned team before
loading one. Do not search `team-configs/` for other teams' credentials. An
unrelated Cursor/GitHub login does not supply W&B or VSS authentication.

4. **Fix and test the known integration gaps before claiming live readiness.**

These are source observations, not claims of a live failure reproduced on Bryce's machine:

- [ ] **Ingress URL base:** `static/index.html` currently uses root-absolute
  `/api/...`, `/health`, and `/clip` URLs. At `/app`, those requests escape the
  app prefix. Add one consistent base-path helper and use it for every fetch
  and video source. Verify both `/app` and `/app/`, plus localhost `/`.
- [ ] **Camera fail-closed behavior:** `scan_live()` filters only when it finds
  a matching camera; zero matches currently leave all Explore rows in scope.
  Make zero Pack C matches return an explicit unavailable/empty state. Do not
  label other cameras as `sdg_warehouse_cam-2`. Test an archive containing only
  unrelated cameras and an archive with exact Pack C matches.
- [ ] **Segment identity:** Explore returns parent chunks and the scanner
  currently takes a preview/first timeline segment. Check the real response
  schema and inspect all intended segment slots. Ensure each reviewable segment
  has a stable unique ID and correct caption/source pair. Never claim the whole
  Pack C corpus was inspected when only previews were scanned.
- [ ] **Live source truth:** `main.clip()` can generate a mock clip when VSS URL
  is absent even if `state.mock` is false. Make missing live configuration
  explicit, or switch the entire app to a clearly marked mock mode. A LIVE chip
  must never cover generated footage. Missing services must not crash the mock app.
- [ ] **GPU helper:** `gpu_client.occlusion_from_yolo()` still treats `hand` as
  occlusion; the active Pack C scanner already avoids that rule. Correct and
  test the helper before wiring it into any live path.
- [ ] **W&B timeouts and evidence:** the app's optional inference client has no
  short explicit timeout/retry policy and tracking errors are swallowed. Bound
  inference latency and expose sanitized connection/run status if needed. Prove
  remote logging by reading the W&B run, not by assuming a successful local retrain.
- [ ] **Live errors in the UI:** check non-2xx scan/review/retrain responses and
  keep the operator's selected item when a request fails. Do not silently advance
  after a rejected review.
- [ ] **State lifetime:** current deployment stores labels under `/tmp/scribner`.
  Establish whether event restarts must preserve reviews. If so, use the team's
  supported persistence and verify it; never claim durable labels without proof.

Add meaningful regressions for each implemented change. Run the existing
adversarial suite before any feature work after a failing attack. Keep the
ConfigMap below 1 MiB and use numpy only for learning. Do not broaden the
model's AUTO_CLEAR policy to make the live demo appear successful.

5. **Prove W&B Inference and SDK logging separately.**

```bash
python - <<'PY'
import os
from openai import OpenAI
key = os.environ.get('WANDB_API_KEY')
if not key:
    print('wandb_inference=skipped (no WANDB_API_KEY)')
    raise SystemExit(0)
try:
    c = OpenAI(base_url='https://api.inference.wandb.ai/v1', api_key=key,
               timeout=20, max_retries=0)
    r = c.chat.completions.create(
        model=os.environ.get('SCRIBNER_MODEL') or 'meta-llama/Llama-3.1-8B-Instruct',
        temperature=0, max_tokens=8,
        messages=[{'role':'user','content':'Reply with the single word PONG.'}])
    assert r.choices and r.choices[0].message.content
    print('wandb_inference=ok')
except Exception as e:
    print('wandb_inference=fail (' + type(e).__name__ + ')')
PY
```

If the configured model is unavailable, inspect the account's documented model
catalog and select an accessible model; do not guess that authentication failed.
Then make a small `wandb.init` run using the configured team/project, record the
run URL, and finish it. Use an actual app retrain to verify `tracking.py` stores
`andon_line`, `andon_green`, `andon_yellow`, `andon_red`, and label counts remotely.
The existing app uses the W&B SDK; do not report Weave tracing as connected unless
you explicitly add and verify it. Weave is not required for the current app.

6. **Prove VSS access, the Pack C inventory, and the payoff search.**

```bash
python - <<'PY'
import os
from vss_client import VssClient
if not (os.environ.get('INGRESS_URL') or os.environ.get('VSS_URL')):
    print('vss=skipped (no INGRESS_URL/VSS_URL)')
    raise SystemExit(0)
c = VssClient()
try:
    c.login()
    print('vss_login=ok')
except Exception as e:
    print('vss_login=fail (' + type(e).__name__ + ')')
    raise SystemExit(1)
for name, op in [
    ('vss_me', c.me),
    ('vss_ingest_config', c.ingest_config),
    ('vss_explore', lambda: c.explore_all(scope='all')),
    ('vss_search', lambda: c.search('person close to a moving vehicle',
        top_k=5, llm_top_n=0, min_similarity=0.3,
        metadata_filters={'camera_id':'sdg_warehouse_cam-2'})),
]:
    try:
        value = op()
        if name == 'vss_explore':
            rows = [r for r in value if r.get('camera_id') == 'sdg_warehouse_cam-2']
            print(name + '=ok pack_c_parents=' + str(len(rows)))
        elif name == 'vss_search':
            print(name + '=ok hits=' + str(len(value.get('results') or value.get('chunk_results') or [])))
        else:
            print(name + '=ok')
    except Exception as e:
        print(name + '=fail (' + type(e).__name__ + ')')
PY
```

Do not mistake zero hits for successful footage verification. Resolve a real
Pack C parent/segment from Explore. Keep any response cache outside git with
owner-only permissions. Use `ingest_config()` for the smoke: `prompt_max()` has
a fallback and cannot by itself prove that the live request succeeded.
For read-only segment details, prefer the explicitly allowed documented tool
retrieval endpoints and verify their request shapes in the official clone.

7. **Prove the three GPU services without Canary.**

```bash
python - <<'PY'
import os, requests
headers = {}
if os.environ.get('GPU_BEARER_TOKEN'):
    headers['Authorization'] = 'Bearer ' + os.environ['GPU_BEARER_TOKEN']
for name, key, path in [
    ('cosmos3_reason','COSMOS3_REASON_URL','/v1/models'),
    ('yolo','YOLO_URL','/healthz'),
    ('embed1','COSMOS_EMBED1_URL','/v1/models'),
]:
    url = os.environ.get(key)
    if not url:
        print(name + '=skipped (no ' + key + ')')
        continue
    try:
        r = requests.get(url.rstrip('/') + path, headers=headers, timeout=15)
        print(name + '=' + ('ok' if r.ok else 'fail') + ' HTTP=' + str(r.status_code))
        if r.ok and name == 'yolo':
            print('yolo_model_loaded=' + str(bool(r.json().get('model_loaded'))))
    except Exception as e:
        print(name + '=fail (' + type(e).__name__ + ')')
print('canary_called=no')
PY
```

Next, use `gpu_client.cosmos_reason_complete()` for one minimal PONG request,
`gpu_client.embed_text()` for the payoff query (assert dimension 256), and
`gpu_client.yolo_infer()` on one already retrieved Pack C segment. Do not print
base64, headers, tokens, or full responses. If model IDs fail, discover them
from that model's `/v1/models`, update the appropriate environment variable,
and restart the process so `config.py` rereads it. YOLO uses `/healthz`.

These direct smokes demonstrate endpoint access. The production video pipeline
already invokes these models through VSS/DataEngine; do not rebuild it or add
unnecessary duplicate inference to every app request.

8. **Workshop owner: re-ingest the existing Pack C footage.**

Read `.cursor/skills/ingest-warehouse/SKILL.md`,
`.cursor/skills/ingest-kits/SKILL.md`, and the official
`ingest/reingest-videos/SKILL.md`. Pack C camera and the warehouse prompt are
already chosen. Discover the exact stream/video IDs and complete chunk counts;
do not ask the user to repeat the known camera choice.

```bash
PYTHONPATH=tools/scribner python - <<'PY'
from kits import prompt_for_kit
p = prompt_for_kit('warehouse-aisle')
assert len(p) <= 800
print('prompt_chars=' + str(len(p)))
print(p)
PY
```

Prepare the exact target, one complete chunk for the first run, expected segment
count, and generated prompt. Preserve camera/location metadata unless correction
is needed. Never send `scenario` together with `custom_prompt`. If the target or
chunk scope is unresolved, obtain that choice and the concrete job confirmation
required by the official re-ingest skill; do not invent IDs or launch an
unbounded bulk job. Coordinate one designated owner to prevent duplicate jobs.

Use the official `POST /api/v1/dashboard/reingest` and documented status route
on the workshop VM. Save job ID and selected/copied/indexed counts, then wait
for completion. Verify `PATH_CLEAR:`, `NEAR_MISS:`, `UNCLEAR:`, and `CONFIDENCE:`
in the new captions. Re-run the payoff search and inspect a near-miss and a clear
clip before expanding to the agreed remaining chunks. Re-ingest replaces slots;
do not infer success from a growing row count.

9. **Run live mode with a separate store and prove real video in the browser.**

Only start this after the live-source and camera fixes/checks in step 4:

```bash
# Dedicated terminal; credentials must be loaded before starting Python.
SCRIBNER_MOCK=0 SCRIBNER_PACK=C SCRIBNER_CAMERA_ID=sdg_warehouse_cam-2 \
  SCRIBNER_DATA_DIR=/tmp/scribner-josh-live PORT=8082 ./scripts/run_mock.sh
# The script name is historical; it preserves an explicit SCRIBNER_MOCK=0.
```

From a second terminal:

```bash
export APP_URL=http://127.0.0.1:8082
curl --fail --silent --show-error -X POST "$APP_URL/api/scan"
curl --fail --silent --show-error "$APP_URL/health"
curl --fail --silent --show-error "$APP_URL/api/andon"
```

Resolve a unit from the live scan, then its detail via `/api/units/<id>`.
Verify its camera is exactly Pack C, `mock` is false, source is a discovered VSS
segment, and caption corresponds to that source. Request `/clip?unit_id=<id>`
with an empty source query too; it must use `unit.source`. Save the MP4 outside
git, require HTTP 200, video/mp4, size over 1 KB, and successful ffmpeg decoding.
The browser must show LIVE, play the same real segment, and match the station
tower to its decision. Only then record `footage_live=ok`.

Drive operator review and retrain using human-selected CLEAR/UNSAFE labels.
Verify invalid overrides return 400 and that W&B logging actually appears.
Keep the mock demo independently available if a live service fails.

10. **Workshop owner: deploy and verify `/app` through the existing Ingress.**

Read `.cursor/skills/deploy-scribner/SKILL.md`, `deploy/DEPLOY.md`, and the official
deployment skill. Confirm the assigned cluster context/namespace from the team
configuration. Do not apply manifests to an inferred or unrelated namespace.

Use the existing documented Deployment + Service + Ingress workflow after
fixing the prefix issue. Mount separate code and static ConfigMaps; a directory
ConfigMap does not recurse into `static/`. Include `builders_stack_lock.json`
alongside Python/requirements files so its contract is retained in deployment.
Keep credentials in the Secret and never print generated Secret YAML. Check the
`/app(/|$)(.*)` path and `/$2` rewrite against the actual ingress controller.
Preserve the configured URL scheme when deriving the final app URL.

```bash
kubectl -n "$NS" rollout status deployment/scribner --timeout=120s
export APP_URL="${INGRESS_URL%/}/app"
curl --fail --silent --show-error "$APP_URL/health"
curl --fail --silent --show-error "$APP_URL/api/andon"
curl --fail --silent --show-error "$APP_URL/api/report"
```

Open both `$APP_URL` and `$APP_URL/` in the browser. Check the actual request
URLs for scan, queue, review, retrain, report, and clip: all must stay under
`/app`. Verify real clip playback and the LIVE indicator at the event URL.
Use `SCRIBNER_MOCK=1` for a cluster smoke only when it remains clearly labeled;
that is not completion of the live deployment.

11. **Record, commit, push both, and verify remote equality.**

```bash
./scripts/run_adversarial.sh
git diff --check
git status --short
# Add only the reviewed source, tests, and documentation paths you changed.
# Commit only if there are changes, then immediately:
./scripts/push_both.sh
git rev-parse --abbrev-ref '@{upstream}'
git rev-parse HEAD
git ls-remote origin refs/heads/cursor/warehouse-primary-72e3
git ls-remote github refs/heads/cursor/warehouse-primary-72e3 HEAD
```

The upstream must remain `origin/cursor/warehouse-primary-72e3`. Never force push
to resolve new upstream work. Fetch and inspect it, preserve others' changes,
then re-test. Write `.cursor/adversarial/YYYYMMDD-josh-cowork.md` with every
attack, connection result, actual live evidence, and outstanding owner action.

## Verification

Run these with `APP_URL` pointing first at the mock app, then the live app, then
the deployed `/app`. Keep mock-only destructive/test labeling in its own store.

```bash
./scripts/run_adversarial.sh
python - <<'PY'
import os, requests
base = os.environ['APP_URL'].rstrip('/')
def get(path):
    r = requests.get(base + path, timeout=20)
    r.raise_for_status()
    return r
h = get('/health').json()
b = get('/api/andon').json()
assert h['product'] == 'warehouse-near-miss' and h['line'] == 'primary'
assert h['corpus'] == 'provided' and h['stack']['canary_wired'] is False
assert 'vast-builders-challenge' in h['stack']['source']
assert b['board'] == 'andon' and b['name_ja'] == '安灯' and b['gemba'] == '現場'
assert b['camera_id'] == 'sdg_warehouse_cam-2'
assert b['rule'] == '赤灯は人なしで緑にしない'
assert b['line_ja'] in get('/api/report').text
rows = get('/api/units').json()['units']
assert rows, 'No inspected units'
for u in rows:
    if (u.get('decision') or {}).get('decision') == 'AUTO_ALERT':
        r = requests.get(base + '/api/andon', params={'unit_id':u['id']}, timeout=20)
        r.raise_for_status()
        assert r.json()['station_lamp'] == 'red'
print('app_checks=ok mode=' + ('mock' if h['mock'] else 'live') + ' units=' + str(len(rows)))
PY
```

Repeat the full attack list in `.cursor/adversarial/20261002-cowork.md` and add
zero matching cameras, malformed/live Explore schemas, duplicate segment IDs,
missing live URL, missing source, VSS 401, inference timeout, W&B logging failure,
and `/app` prefix regressions. Check the empty-queue green rule and red-over-yellow
priority in isolated fixtures, without falsely clearing live alerts.

Pass: real service evidence, real Pack C playback, correct UI lamps, real W&B
retrain evidence, working `/app`, all tests passing, and matching Origin/GitHub
commits. Missing live inputs can leave a usable mock, but the full connection
handoff remains partial. Do not convert missing evidence into an ok result.

## Report back

Paste this block, filled with observed facts and no secrets:

```text
handoff: josh-cowork
status: done | blocked | partial
machine: <actual local or workshop environment>
branch: cursor/warehouse-primary-72e3
checks:
- origin_login:
- origin_cli:
- origin_upstream:
- github_org_and_public_visibility:
- official_stack_commit:
- python_and_dependencies:
- unittest_count:
- builders_stack_adversarial:
- mock_40_units:
- mock_three_clips:
- operator_AO_and_lamps:
- camera_filter_fail_closed:
- unique_live_segments:
- mock_live_source_separation:
- ingress_prefix_fix:
- vss_login:
- vss_me:
- vss_ingest_config:
- vss_explore_pack_c:
- vss_payoff_search:
- cosmos_reason_health_and_inference:
- yolo_health_and_inference:
- embed1_health_and_256d:
- wandb_inference:
- wandb_sdk_smoke:
- wandb_actual_retrain_andon_line:
- weave: skipped (not part of current app) | ok (<actual evidence>)
- reingest_job_and_counts:
- caption_schema_after_reingest:
- footage_live:
- live_browser_playback:
- review_HTTP_400_checks:
- report_line_matches_andon:
- event_app_UI_API_video:
- review_state_persistence:
- canary_called: no
- origin_push:
- github_push:
- local_origin_github_HEAD_equal:
artifacts:
- commit:
- origin: https://cursor.com/codebase/bryce-mcg/Scribner
- github: https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow
- local_preview:
- event_app:
- wandb_smoke_run:
- wandb_retrain_run:
- adversarial_report:
- browser_screenshot:
remaining:
- <exact unfinished action, assigned owner, required input, completion check>
next: <one concrete next action, or complete>
```

## Stop and escalate

- Origin or GitHub authentication/access cannot be established through normal login: preserve local work and identify the missing access. Do not create another repository or substitute a different upstream.
- A configured service returns 401/403: record fail with the service name and status; resolve the assigned credentials. Do not print tokens or retry guessed accounts.
- Multiple team configurations, an ambiguous cluster namespace, unresolved re-ingest target/chunk scope, or no designated bulk owner: complete read-only discovery and prepare the exact request; pause that write until scope is resolved.
- Tests fail twice, or false CLEAR remains after one attempted fix: stop feature work and report the reproducer and affected commit.
- `/api/andon` is missing, camera provenance is wrong, a live unit streams generated footage, or the event UI escapes `/app`: do not call live readiness complete; fix and re-test first.
- Missing W&B/VSS/GPU credentials: keep mock operational, finish independent work, and report partial with the missing variable names and owner. Do not block unrelated laptop work or claim full connection success.
- GPU/image/cluster failure outside this app's control: provide sanitized evidence to the workshop owner; do not rebuild shared infrastructure.

Optional housekeeping: Bryce's empty personal `brycehcmcgrath/Scribner` repository
was created before the organization destination was clarified. It has no pushed
code. CLI deletion was denied for missing `delete_repo` scope. Josh does not need
to address it; Bryce may remove it separately. Do not request broader credentials
for this cleanup as part of finishing the application.
