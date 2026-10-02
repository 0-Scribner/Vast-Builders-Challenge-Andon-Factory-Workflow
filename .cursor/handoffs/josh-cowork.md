# Handoff: Josh's Cowork — finish and verify Scribner Primary

## Receiver

Josh's Cowork agent, in a clean Scribner checkout. **Origin is mandatory and is the source of truth.** The public mirror belongs to **0-Scribner**.

This is a one-time integration work order. Finish local code and mock verification on Josh's computer. Run the event integration, re-ingest, and deployment on the assigned workshop VM/cluster with its existing configuration. If that environment is unavailable, finish independent work and report the exact remaining owner actions. Read this entire handoff before live requests.

## Done when

- [ ] Primary is checked out; upstream is Origin; local HEAD, Origin Primary, GitHub Primary, and GitHub HEAD match.
- [ ] All adversarial tests pass, including the handoff checker's negative cases. The earlier application baseline was 67 tests; record the new actual count.
- [ ] A fresh mock store has 40 units, functioning A/C CLEAR and O/U UNSAFE controls, correct 安灯 lamps, and playable green/yellow/red aisle clips.
- [ ] Every required tool and service has an evidence-backed result. Missing inputs are `skipped`; configured failures are `fail`; neither counts as completion.
- [ ] The known live-code gaps in step 4 are fixed and covered by meaningful regressions.
- [ ] VSS identity, configuration, complete Pack C inventory, and payoff search are verified; real captions, detections, and video resolve to the same segments.
- [ ] Cosmos Reason, YOLO11, and Embed1 pass model-specific health and real inference checks; Embed1 produces 256 finite numbers.
- [ ] W&B Inference is used by the app; W&B SDK smoke and a real app retrain have remotely readable runs and expected andon metrics.
- [ ] One designated owner re-ingests the agreed existing Pack C chunks, confirms completion and updated captions, and repeats search → playback → review → retrain.
- [ ] The event app runs on the team's Kubernetes cluster at its existing host's `/app`; browser UI, API, video, review, report, and retrain work there after a clean start.
- [ ] Judges can open the public code; the two-minute demo is rehearsed; the official submission workflow is completed with agreed, factual values.
- [ ] A dated report identifies evidence, remaining work, owner, and final remote commit IDs. Origin is pushed first, then the organization mirror.

## Context

Primary is a warehouse near-miss / path-clear 安灯 board using provided Pack C, `sdg_warehouse_cam-2`, `warehouse3`.
Cosmos captions feed a numpy gate: AUTO_CLEAR / HOLD / AUTO_ALERT; humans supply CLEAR / UNSAFE labels.
The false-CLEAR rule is `赤灯は人なしで緑にしない`.
Bryce verified the mock app, 67 tests, real HTTP guard checks, clip colors, browser playback, and A/O controls.
Origin and public 0-Scribner mirroring worked at application baseline `8505d909d8179f48d05984a946ec7c482645421d`.
No live W&B/VSS/GPU credentials or workshop deployment were available; those integrations are unverified.
The handoff review and checker evidence are in `.cursor/adversarial/20261002-handoff-review.md`.
Runtime owners are `tools/scribner/{scan,vss_client,gpu_client,llm,tracking,main}.py`, `static/index.html`, and `deploy/DEPLOY.md`.

## Never

- Never replace Origin with GitHub as upstream, create a personal mirror, check out/merge Plan B, force-push, or alter a PR. Origin PR 2 is read-only context.
- Never print/commit secrets, real configs, JWTs, response dumps, videos, archives, local stores, or `.venv`. No bare `env`, `printenv`, shell tracing, verbose authenticated HTTP, or Secret YAML output. List variable names/presence only.
- Never call Docker, rebuild VSS/DataEngine, invoke the Segmenter, re-upload the corpus, film replacement footage, ingest internet/YouTube video, or write directly to shared S3/VastDB.
- Never call Canary/audio transcription, invent API routes, hardcode GPU hosts, derive one GPU endpoint from another, or edit `/etc/hosts`.
- Never use another team's credentials, namespace, buckets, or index. Do not search `team-configs/` for credentials. Preserve other people's checkouts, listeners, and shared services.
- Never AUTO_CLEAR NEAR_MISS, inconsistent captions, hazards, LOW confidence, nonempty UNCLEAR, or blocked views. Person+vehicle requires HIGH PATH_CLEAR corroboration. A W&B PASS must not reduce near-miss `p_fail` below 0.8.
- Never treat a person/hand detection alone as warehouse occlusion. Never accept `gate_ok=true` on HOLD, an empty/agree override reason, or AUTO_ALERT→CLEAR without `confirm_escape=true`.
- Never use the mock oracle for live labels, call synthetic clips live, or treat health/HTTP 200 as proof of video provenance, playback, inference, logging, or deployment.
- Never claim a physical machine was stopped: this product displays a review/alert decision. Do not invent safety certification or measured accuracy improvements.
- Keep numpy-only learning, small ConfigMaps, and the current simple web app. No sklearn/scipy/torch, frontend bundler, new PPE product, or VSS UI reskin.

## Inputs

| Input | Value or source |
|---|---|
| Origin | `https://origin.cursor.com/git/bryce-mcg/Scribner.git` |
| Primary branch | `cursor/warehouse-primary-72e3` |
| Public mirror | `https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow.git` |
| Origin PR, read-only | `https://cursor.com/codebase/bryce-mcg/Scribner/pull/2` |
| Official challenge | `https://github.com/vast-data/vast-builders-challenge`, reviewed at `4987d8ebd8e5270dccf0864851a16ed42eb8d8e7` |
| Runtime/tools | Python 3.12, git, Origin CLI, gh, ffmpeg, browser, repo requirements; Cursor Agent and kubectl on the workshop VM |
| W&B | `WANDB_API_KEY`, `WANDB_TEAM`, `WANDB_PROJECT`, verified `SCRIBNER_MODEL` |
| VSS | `INGRESS_URL`, `USERNAME`, `PASSWORD`; supported local aliases `VSS_URL`, `VSS_USERNAME`, `VSS_PASSWORD` |
| GPUs | `COSMOS3_REASON_URL`, `YOLO_URL`, `COSMOS_EMBED1_URL`, optional `GPU_BEARER_TOKEN`; model IDs from each service |
| Workshop identity | Existing environment and exactly the assigned `/config/<team>.config`; kubeconfig or its documented team-prefixed alias |
| Existing evidence | `.cursor/adversarial/20261002-cowork.md`, `.cursor/adversarial/20261002-handoff-review.md` |

Official constraints and evidence to produce:

| Requirement / tool | Completion evidence |
|---|---|
| BEFORE_YOU_BUILD + BUILD_DAY | Team of at most four; at most two workshop VMs launched per team; existing Cosmos, Cursor, and W&B access confirmed without collecting personal details |
| Cursor + official skills | Workshop work uses the configured Cursor Agent and matching skills; local Cowork rehearsal follows Bryce's explicit request |
| VAST S3 → DataEngine → VastDB | Existing segments re-ingested through detector → reasoner → embedder → writer; completed job and searchable segment evidence |
| NVIDIA on CoreWeave | Cosmos captions, YOLO detections, Embed1-backed search; separate health/inference results |
| W&B Serverless Inference | Actual app request with a current accessible model, plus gate safety tests |
| W&B experiment tracking | SDK smoke and actual app retrain readable remotely; Weave and ARIA are optional, not claimed unless used |
| Deployment skill | Public image + ConfigMaps + Secret + Deployment/Service/Ingress, team namespace, existing host, `/app`; no Docker build/push |
| Submission skill | Clean-start demo, accessible public code, two-minute explanation, agreed submission fields; actual submission destination confirmed with organizers |

## Procedure

1. **Get a clean Primary checkout from Origin.** Read `AGENTS.md` and `.cursor/rules/handoffs.mdc`. Use normal authenticated login; never paste credentials into chat.

```bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
command -v origin >/dev/null || {
  curl --fail --silent --show-error --max-time 60 https://downloads.cursor.com/origin/install.sh -o /tmp/scribner-origin-install.sh
  sh /tmp/scribner-origin-install.sh
}
origin auth status || origin auth login
gh auth status || gh auth login
export SCRIBNER_DIR="${SCRIBNER_DIR:-$HOME/Scribner}"
# If this path is occupied by unrelated work, choose a separate empty directory.
if [ ! -e "$SCRIBNER_DIR" ]; then
  mkdir -p "$SCRIBNER_DIR"
  git -C "$SCRIBNER_DIR" init
  git -C "$SCRIBNER_DIR" remote add origin https://origin.cursor.com/git/bryce-mcg/Scribner.git
fi
cd "$SCRIBNER_DIR"
git status --short --branch
```

Continue only in the intended clean checkout; preserve existing changes. Do not reset or stash someone else's work.

```bash
test -z "$(git status --porcelain)"
git remote set-url origin https://origin.cursor.com/git/bryce-mcg/Scribner.git
origin auth setup-git --local
git fetch origin cursor/warehouse-primary-72e3
if git show-ref --verify --quiet refs/heads/cursor/warehouse-primary-72e3; then
  git switch cursor/warehouse-primary-72e3
  git merge --ff-only origin/cursor/warehouse-primary-72e3
else
  git switch --track -c cursor/warehouse-primary-72e3 origin/cursor/warehouse-primary-72e3
fi
git branch --set-upstream-to=origin/cursor/warehouse-primary-72e3
if git remote get-url github >/dev/null 2>&1; then
  git remote set-url github https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow.git
else
  git remote add github https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow.git
fi
git config --local credential.https://github.com.helper '!gh auth git-credential'
gh repo view 0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow --json url,visibility,defaultBranchRef
origin pr list -R bryce-mcg/Scribner --limit 5
origin pr view 2 -R bryce-mcg/Scribner
cat AGENTS.md
```

2. **Establish the runtime and official contracts.** Reuse the official clone; inspect its status before updating it. Fetch upstream changes, compare against the reviewed commit, and reconcile changed rules before live work. Do not overwrite local workshop changes.

```bash
python3.12 -m venv .venv
export PATH="$PWD/.venv/bin:$PATH"
python -m pip install -r tools/scribner/requirements.txt
export PYTHONPATH="$PWD/tools/scribner"
export BUILDERS_CHALLENGE_DIR="${BUILDERS_CHALLENGE_DIR:-$HOME/vast-builders-challenge}"
test -f "$BUILDERS_CHALLENGE_DIR/config.example" || \
  git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git "$BUILDERS_CHALLENGE_DIR"
ffmpeg -version >/dev/null
echo ffmpeg=ok
./scripts/run_adversarial.sh
```

Read official `.cursor/rules/build-day.mdc`, `BEFORE_YOU_BUILD.md`, `BUILD_DAY.md`, `ARCHITECTURE_REFERENCE.md`, and `config.example`. Read matching skills before requests: `retrieval/login`, `retrieval/search`, `retrieval/videos`, `retrieval/agent-qa` for tool route shapes, `gpu/model-health`, `gpu/model-smoke-test`, `ingest/reingest-videos` or `reingest-chunk`, `deployment/deploy-app-no-registry`, `submission`, and `ask-cosmos` when blocked. Read the repo's `run-mock`, `conformance-stack`, `ingest-warehouse`/`ingest-kits`, and `deploy-scribner` skills.

The original laptop request permits only these VSS routes: `/api/v1/auth/login`, `/auth/me`, `/config`, `/metadata/ingest-config`, `/search`, `/videos/explore`, `/tools/explore`, `/tools/detections`, `/videos/stream` (all relative suffixes use `/api/v1`). The workshop re-ingest/deploy workflow additionally uses the matching official skill's documented metadata, dashboard, and job-status routes. Scope those calls to that workflow. Forbidden: `/reports`, `/alerts`, `/analytics`, `/videos/ask`, `/tags`, `/locations`, `/extra-metadata`.

3. **Preserve the mock baseline and resolve live configuration privately.** In a dedicated terminal, choose a free port and a fresh private store:

```bash
export SCRIBNER_MOCK_STORE="$(mktemp -d /tmp/scribner-josh-mock.XXXXXX)"
SCRIBNER_MOCK=1 SCRIBNER_DATA_DIR="$SCRIBNER_MOCK_STORE" PORT=8081 ./scripts/run_mock.sh
```

Verify 40 units and A/O controls in the browser. Keep live and mock stores separate. Use existing environment first; inspect only names/presence. An ignored `.env` may be used on the laptop, with mode 600; load only a trusted file and preserve already configured credentials. On the workshop VM:

```bash
mapfile -t SCRIBNER_TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
if [ "${#SCRIBNER_TEAM_CONFIGS[@]}" -ne 1 ]; then
  echo 'Team config unresolved; pause dependent live work.'
else
  set -a
  source "${SCRIBNER_TEAM_CONFIGS[0]}"
  set +a
fi
if wandb status >/dev/null 2>&1; then
  echo 'wandb_cli=ok (command only; authentication still requires remote proof)'
else
  echo 'wandb_cli=fail'
fi
```

Multiple configs require resolving the assigned file before any live action; do not choose by filename order. Missing credentials on the laptop are expected skips, not permission to invent endpoints. On the assigned VM, report missing configuration to the operator. Official `config.example` says GPUs may be unauthenticated, while model-health/smoke skills require a bearer. Bryce explicitly made `GPU_BEARER_TOKEN` optional: attempt every configured GPU URL, send Authorization only when a token is set, and record 401/403 as fail. Resolve the assigned bearer through normal configuration if needed. Never use hardcoded-host or Canary examples.

4. **Fix these source-observed integration gaps before claiming live readiness.** They are open work, not completed fixes:

- [ ] `static/index.html`: centralize the app base path for every fetch and video URL. Root-absolute `/api`, `/health`, `/clip` currently escape `/app`. Test `/`, `/app`, and `/app/`.
- [ ] `scan.py`: exact camera equality; zero Pack C matches must produce an explicit unavailable/empty state. Current filtering can retain unrelated cameras and accepts substring matches.
- [ ] `vss_client.py`: validate actual Explore schema, pagination, counts, duplicate/repeated pages, and malformed responses. Current list handling calls `.get()` before checking the type and can truncate silently.
- [ ] `scan.py`: inspect the agreed segment scope, not just preview/first timeline entries. Stable unique segment IDs must preserve source/caption/detection pairing. Record inspected/available counts; never claim complete coverage from previews.
- [ ] Laptop live scanning currently calls `/videos/metadata` and `/videos/detections`, outside the narrower laptop allowlist. Use allowed documented search/Explore and tool retrieval where sufficient, or do this scan on the workshop VM under its documented route scope. Do not quietly broaden laptop permissions.
- [ ] `main.py`: missing VSS configuration must not generate a clip under a LIVE indicator. Missing source/configuration returns an explicit error or switches the entire app to visibly mock mode. Test empty `source` falling back to the selected unit's real source.
- [ ] `gpu_client.py`: remove the remaining helper rule that treats every `hand` as occlusion before using it in live code. The active Pack C scanner already avoids it.
- [ ] `llm.py`/`tracking.py`: bound inference timeout/retries, expose sanitized fallback/logging status, and verify W&B remotely. A local retrain currently can hide a logging failure. Resolve a current accessible model; the hardcoded default is not verified.
- [ ] UI: failed scan/review/retrain requests must show a useful error and preserve the selected review item. Do not advance after non-2xx responses.
- [ ] Deployment: include code, static assets, and `builders_stack_lock.json`; configure W&B Secret values as well as VSS. Decide and verify review-state persistence across restart; `/tmp` alone is ephemeral.

Keep the mock usable when a live service fails. Add regressions for each fix. After a successful attack, fix and rerun adversarial checks before feature work.

5. **Run strict connection checks and real model operations.** Set `SCRIBNER_MODEL` from the assigned W&B account's available models; do not guess from the old default. The checker makes a small inference request but does not create runs, ingest, review, or deploy:

```bash
if python scripts/handoff_checks.py connections; then
  echo 'connection_checks=ok; end-to-end proofs still required'
else
  SCRIBNER_CHECK_RC=$?
  echo "connection_checks=incomplete exit=$SCRIBNER_CHECK_RC"
fi
```

Exit 0 means those checks passed, 1 means failure, 2 means missing prerequisites. Record every JSON result; continue independent checks. Exceptions are sanitized. The checker rejects redirects/non-200 responses, empty Pack C inventories, unverified search cameras, missing models, and YOLO `model_loaded=false`. If a live schema differs, record unverified, inspect privately, and adapt with tests; do not weaken checks to obtain green output.

Required additional proofs:

- VSS: me matches assigned identity; inspect valid ingest configuration. The payoff query is **person close to a moving vehicle**. Verify each selected Pack C source, caption, and detection. Zero hits requires checking indexing/filter/prompt state, not an `ok` footage result.
- Cosmos Reason/Embed1: `/v1/models`, `/v1/health/ready`, `/v1/health/live` must all return 200. Discover model IDs, then perform a nonempty chat completion and embedding request. Assert 256 finite numeric embedding values, using `scripts/handoff_checks.embedding_valid` if useful.
- YOLO11: `/healthz` must report `ok=true` and `model_loaded=true`; then `/v1/infer` on a small already-retrieved Pack C clip must report successful perception with valid detections. Do not require objects in a truly empty scene; verify the actual response schema. No `/v1/models` call on YOLO.
- W&B: inference smoke alone is insufficient. Prove the app actually receives a W&B prior, and test near-miss clamping. Create and finish a small SDK run with explicit team/project and online mode; read it back remotely. Then retrain through the app on human labels and read back `andon_line`, numeric `andon_green`, `andon_yellow`, `andon_red`, and label counts. Record both run URLs. Local/offline logs do not establish connection.
- Direct GPU smokes are diagnostics requested for this handoff. The production pipeline already invokes the three models; do not add duplicate inference to every app request. Weave/ARIA are optional; Canary remains prohibited.

6. **Workshop owner: prepare and execute the bounded Pack C re-ingest.** Respect the limit of two VM launches per team and designate one bulk-ingest owner. Read the matching official ingest skill. Paginate all accessible parents, resolve the known Pack C camera to an exact stream/video, and count complete chunks. A complete chunk contains segment numbers 1 through `total_segments`; non-stream target uses one chunk; stream limit is 1–100 and no more than available.

Generate the existing warehouse prompt from `kits.py`:

```bash
PYTHONPATH=tools/scribner python - <<'PY'
from kits import prompt_for_kit
p = prompt_for_kit('warehouse-aisle')
assert len(p) <= 800
print('prompt_chars=' + str(len(p)))
print(p)
PY
```

Fetch the live prompt limit successfully, enforce `min(800, live_limit)`, and retain prose rather than JSON instruction blocks. Cosmos captions are truncated around 1,024 characters; put the key schema first. Never use a fallback limit as evidence of a successful request.

Preserve known camera/location metadata. Never send `scenario` with `custom_prompt`. Show the exact target ID, initial one complete chunk, expected clips, generated prompt, and metadata behavior. Reuse any explicit confirmation already covering this exact request. Otherwise obtain final confirmation only after preparing it: the official [reingest-videos skill](https://github.com/vast-data/vast-builders-challenge/blob/4987d8ebd8e5270dccf0864851a16ed42eb8d8e7/.cursor/skills/ingest/reingest-videos/SKILL.md) says, “Start only after explicit confirmation.” The generic instruction to finish connecting is not an exact target/chunk confirmation.

Build JSON safely, start through documented `/api/v1/dashboard/reingest`, and record job ID, selected chunks, copied/indexed segments, and terminal status. Verify PATH_CLEAR, NEAR_MISS, UNCLEAR, CONFIDENCE in updated captions and play clear/near-miss examples before expanding to the agreed remaining scope. Re-ingest replaces slots; rising row counts do not prove success. A lost status record after restart is not permission to launch a duplicate job.

7. **Prove the live app with real footage and human review.** After step 4 fixes, on the authorized environment in a dedicated terminal:

```bash
export SCRIBNER_LIVE_STORE="$(mktemp -d /tmp/scribner-josh-live.XXXXXX)"
SCRIBNER_MOCK=0 SCRIBNER_PACK=C SCRIBNER_CAMERA_ID=sdg_warehouse_cam-2 \
  SCRIBNER_DATA_DIR="$SCRIBNER_LIVE_STORE" PORT=8082 ./scripts/run_mock.sh
```

The script preserves explicit `SCRIBNER_MOCK=0`. From another terminal with the same runtime/configuration:

```bash
export APP_URL=http://127.0.0.1:8082
curl --fail --silent --show-error --max-time 180 -X POST "$APP_URL/api/scan" -o /dev/null
python scripts/handoff_checks.py app --url "$APP_URL" --expect live
```

The app checker validates mode and unit metadata; it cannot independently prove footage provenance. Compare unit sources with the verified VSS inventory. Stream the same source directly and via `/clip?unit_id=<id>&source=` into private temporary files outside git. Require HTTP 200, video/mp4, size >1 KB, ffmpeg decoding, and matching content (hashes when byte-identical; decoded frames/timestamps if the proxy changes packaging). Browser must show LIVE and play that real clip, with its decision's station lamp. Only then set `footage_live=ok`.

Use real human CLEAR/UNSAFE labels, then retrain and verify the remote W&B run. Keep mock-only oracle and invalid-review tests in disposable stores. Do not clear real alerts just to turn the board green.

8. **Workshop owner: deploy at the team's `/app`.** Read the official deployment skill and update `deploy/DEPLOY.md` to include the fixes before executing it. Resolve the existing kubeconfig from `/config/kubeconfig` or this team's documented `<team>-k8s.yaml` alias. Verify context and namespace access privately. Derive `NS` from the assigned team identity, not a guessed name.

```bash
: "${USERNAME:?Assigned team configuration must be loaded}"
: "${INGRESS_URL:?Assigned team configuration must be loaded}"
export NS="$USERNAME"
export APP_URL="${INGRESS_URL%/}/app"
# Continue only after verifying this context and NS belong to the assigned team.
kubectl -n "$NS" auth can-i create deployments.apps
```

Use a public Python 3.12 image, separate code/static ConfigMaps, and a Secret for VSS and W&B values. A directory ConfigMap is not recursive. Include `builders_stack_lock.json`; inspect serialized ConfigMap size below 1 MiB each with headroom. No videos, virtualenv, or credentials in ConfigMaps. Verify dependencies/install permissions and read-only mounts from a clean pod. If showing mock clips in the pod, ffmpeg and suitable fonts must exist there; otherwise do not claim that fallback works.

Use Deployment + Service + Ingress at `/app(/|$)(.*)` with the controller's matching rewrite, preserving the configured HTTP/HTTPS scheme and existing host. Verify regex/controller settings rather than assuming the example works. Keep root `/` for the existing VSS UI. Configure live mode explicitly and verified persistence for labels. Restart the app deployment after updating its ConfigMaps/Secret; verify the mounted revision, not only a successful rollout.

```bash
kubectl -n "$NS" rollout status deployment/scribner --timeout=120s
python scripts/handoff_checks.py app --url "$APP_URL" --expect live
```

Open `/app` and `/app/`; inspect actual browser requests for scan, queue, review, retrain, report, clip. All app requests stay under `/app`. Verify real playback, LIVE indicator, lamps, human review, and remote retrain evidence. Rehearse a clean start/restart and verify the stated data-persistence behavior. Localhost is not the event deliverable.

9. **Finish the official submission workflow.** Read existing `SUBMISSION.md` first. It is currently a draft: team pending, stale code placeholder, no deployed app, and feedback missing. Use the official submission skill on the workshop VM:

- Derive team number from assigned `USERNAME`/`PIPELINE`; never collect member names, emails, ages, or consent details.
- Propose a factual 2–3 sentence description under 40 words and stack based on actual use. Do not claim unverified inference, detection, tracking, or accuracy.
- Use the known public 0-Scribner code URL. Use the verified event app URL; do not invent links or repeat questions already answered.
- Obtain agreement on the description/stack and genuinely missing supplementary/feedback fields, one section at a time. Missing fields remain `NOT PROVIDED` with an explicit incomplete status.
- Keep the official Team heading → Project → Feedback shape; no Members section. Finish the agreed file, rehearse one two-minute demo, and ensure judges can open the code without our login.
- Follow the organizer's actual submission instructions. The reviewed skill does not specify a submission destination or deadline. Preparing `SUBMISSION.md` is not evidence that the entry was submitted.

10. **Record, commit, push Origin then GitHub, and assert equality.** Write `.cursor/adversarial/YYYYMMDD-josh-cowork.md` with actual attacks, tool results, evidence, and owner actions. Review staged content and tracked history for secrets/media; `push_both.sh` only guards staged filenames and is not a full secret scan. Add explicit reviewed paths, commit only changes from this task, and immediately push both.

```bash
./scripts/run_adversarial.sh
git diff --check
git status --short
# Stage explicit reviewed paths and commit the completed change, then:
./scripts/push_both.sh
test "$(git rev-parse --abbrev-ref '@{upstream}')" = origin/cursor/warehouse-primary-72e3
SCRIBNER_HEAD="$(git rev-parse HEAD)"
SCRIBNER_ORIGIN_HEAD="$(git ls-remote origin refs/heads/cursor/warehouse-primary-72e3 | awk '{print $1}')"
SCRIBNER_GITHUB_HEAD="$(git ls-remote github refs/heads/cursor/warehouse-primary-72e3 | awk '{print $1}')"
SCRIBNER_PUBLIC_HEAD="$(git ls-remote github HEAD | awk '{print $1}')"
test "$SCRIBNER_HEAD" = "$SCRIBNER_ORIGIN_HEAD"
test "$SCRIBNER_HEAD" = "$SCRIBNER_GITHUB_HEAD"
test "$SCRIBNER_HEAD" = "$SCRIBNER_PUBLIC_HEAD"
printf 'verified_commit=%s\n' "$SCRIBNER_HEAD"
```

## Verification

Run the full suite after fixes. Then run these against the appropriate active processes:

```bash
./scripts/run_adversarial.sh
python scripts/handoff_checks.py app --url http://127.0.0.1:8081 --expect mock
# After live integration and event deployment:
python scripts/handoff_checks.py app --url http://127.0.0.1:8082 --expect live
python scripts/handoff_checks.py app --url "${INGRESS_URL%/}/app" --expect live
```

Adversarial checklist — reproduce in isolated fixtures/stores, preserve failures as regressions:

- PATH_CLEAR:YES + NEAR_MISS:YES; LOW confidence; blocked view; hazards/UNCLEAR; person+vehicle without HIGH PATH_CLEAR → never AUTO_CLEAR.
- W&B PASS on NEAR_MISS → `p_fail >= 0.8`; person/hand alone → not warehouse occlusion.
- HOLD with `gate_ok=true`; red→CLEAR without confirmation; empty/agree override → actual HTTP 400 and no label mutation.
- Unknown kit `spaceship`, `random.mp4`, 801-character prompt, and YouTube URL → rejected; no upload occurs.
- Staged video/archive/.env/.config → push refused before either remote; failed Origin push → nonzero; successful dual push preserves Origin upstream. Use temporary test repositories.
- Forbidden VSS paths, hardcoded GPU host, Canary transcription, missing official stack/warehouse/andon health fields → conformance fails.
- Missing Japanese/operator/payoff UI content, non-red alert station, empty queue not green, HOLD+ALERT line not red, report LINE mismatch → fail.
- Mock green/yellow/red clips: video/mp4, >1 KB, successful decoding, first-frame RGB spread >8, correct lamp color, browser playing beyond an initial frame.
- Zero/wrong/substring camera, malformed or repeated pagination, preview-only coverage, duplicate unit/source IDs, missing caption/detection/source, mismatched clip → cannot claim complete Pack C inspection or false-clear safety.
- Missing live URL, mock masquerading as live, VSS 401, redirects, malformed 200, unloaded GPU, empty completion, wrong/nonfinite embedding → fail or explicit unavailable; continue independent checks.
- W&B timeout/offline/logging failure → bounded operation, visible sanitized status, no fabricated remote run.
- `/app` and `/app/` prefix, failed review UI state, fresh pod startup, Secret/ConfigMap mounts, dependency installation, restart/persistence → verify through actual Ingress.

Passing the checker is only one layer. Full completion also requires real re-ingest, provenance, browser playback, app W&B use, remote retrain, deployment, and submission evidence. Any missing required proof means `partial` or `blocked`, never `done`.

## Report back

Use `ok | fail | skipped (<reason>)` for every check; no silent omissions. Include no secrets or private response dumps.

```text
handoff: josh-cowork
status: done | partial | blocked
machine: <local and workshop environments used>
branch: cursor/warehouse-primary-72e3
checks:
- origin_cli_login_readonly_PR_context_and_upstream:
- github_cli_org_public_and_default_branch:
- official_stack_commit_and_rule_drift:
- team_access_VM_limits_and_Cursor_Agent:
- python_dependencies_ffmpeg_browser:
- wandb_cli:
- adversarial_test_count_and_results:
- handoff_negative_checks:
- mock_40_units_three_clips_AO_lamps:
- gate_override_HTTP400_and_report_LINE:
- camera_schema_pagination_segment_provenance:
- live_mock_separation_and_UI_error_handling:
- vss_login_me_config_ingest_config:
- vss_complete_pack_c_inventory_and_payoff_search:
- cosmos_reason_health_and_inference:
- yolo_health_and_inference:
- embed1_health_and_256_finite_values:
- GPU_bearer: set | missing (never its value)
- wandb_inference_in_app_and_safety_clamp:
- wandb_sdk_online_smoke_remote_readback:
- wandb_actual_retrain_andon_line_and_metrics:
- weave_ARIA: skipped (optional) | ok (<actual evidence>)
- reingest_owner_confirmed_scope_job_counts_completion:
- updated_caption_schema_and_search:
- real_pack_c_stream_and_browser_playback:
- event_app_UI_API_video_review_report_retrain:
- clean_start_mounted_revision_and_state_persistence:
- code_access_two_minute_demo_SUBMISSION:
- actual_submission: prepared_only | submitted (<evidence>) | incomplete (<missing>)
- canary_called: no
- origin_push:
- github_push:
- local_Origin_GitHub_primary_and_public_HEAD_equal:
artifacts:
- final_commit:
- github: https://github.com/0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow
- origin: https://cursor.com/codebase/bryce-mcg/Scribner
- local_preview:
- event_app:
- wandb_smoke_run:
- wandb_retrain_run:
- adversarial_report:
- connection_results:
- browser_screenshot:
remaining:
- <unfinished action; owner; required input; objective completion check>
next: <one concrete action, or complete>
```

## Stop and escalate

- Missing live inputs: preserve mock, finish independent work, report partial and missing variable names. Do not request secrets in chat.
- Origin/org authentication failure: preserve work; identify the needed access. Do not create another repository or switch upstream.
- Ambiguous team config/namespace or unconfirmed exact re-ingest scope: prepare discovery/request fully; pause only the dependent write.
- Configured 401/403: record fail and resolve the assigned credentials through normal access. Do not guess accounts or print errors containing credentials.
- Tests fail twice, or false CLEAR remains after one attempted fix: stop feature work and report the reproducer and affected commit.
- Unverified provenance, synthetic video under LIVE, unavailable Pack C, escaping `/app`, or missing W&B proof: completion is blocked by that check; fix and rerun rather than relabel it successful.
- Shared GPU/pipeline/cluster trouble: use the official `ask-cosmos` skill to prepare a sanitized support note; do not post/send it. On the laptop, preserve the narrower route scope and mark workshop-only diagnostics not run.
- Missing submission agreement, feedback, or organizer destination: finish technical work and state precisely what remains. Do not fabricate or claim submission.

Optional housekeeping outside this work order: Bryce's empty personal `brycehcmcgrath/Scribner` repo has no pushed code; deletion lacked `delete_repo` permission. It is not the project mirror. Do not broaden credentials for cleanup.
