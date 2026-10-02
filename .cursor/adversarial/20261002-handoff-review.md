# Adversarial review of Josh's Cowork handoff — 2026-10-02

## Result and scope

**The complete handoff was reviewed and revised. Live hackathon completion is still partial.**

Reviewed every section, command block, permission boundary, pass condition, and report field in `.cursor/handoffs/josh-cowork.md`. Compared the original laptop request, repository instructions, actual application code, and the official VAST challenge source. Added `scripts/handoff_checks.py` and 20 negative/contract tests to prevent false success in the receiving agent's checks.

This review does not certify live video provenance, service access, production safety, or contest acceptance. No credentials, real Pack C stream, re-ingest job, Kubernetes deployment, or W&B run were available during this review. Those requirements remain explicit work for Josh/the assigned workshop operator. The known runtime gaps were documented as open TODOs; this change does not implement them.

Application baseline: `8505d909d8179f48d05984a946ec7c482645421d` on `cursor/warehouse-primary-72e3`. Origin remains the source of truth; mirror is `0-Scribner/Vast-Builders-Challenge-Andon-Factory-Workflow`.

## Official source checked

Local official clone and upstream HEAD both resolved to `4987d8ebd8e5270dccf0864851a16ed42eb8d8e7` during review. Sources under [the pinned official repository](https://github.com/vast-data/vast-builders-challenge/tree/4987d8ebd8e5270dccf0864851a16ed42eb8d8e7):

- `.cursor/rules/build-day.mdc`, `BEFORE_YOU_BUILD.md`, `BUILD_DAY.md`, `ARCHITECTURE_REFERENCE.md`, `config.example`.
- Retrieval login/search/videos/agent-tool documentation; GPU model-health/model-smoke-test; reingest-videos; deploy-app-no-registry; submission; ask-cosmos.
- Scribner `AGENTS.md`, handoff template/rule, conformance/run-mock skills, current `SUBMISSION.md`, and code owning the known integration gaps.

NVIDIA skill finder/catalog had been consulted during the laptop work. The workshop's supplied API skills remain the applicable endpoint contract. No capability installation, shared-stack deployment, or optional model use was required for this review.

The public W&B documentation URLs redirected to CoreWeave documentation, which the web tool could not fetch. No new model ID or changed inference endpoint was asserted from that failed lookup. The handoff requires a verified model from the assigned account and a real request before reporting W&B ready.

## Findings resolved in the handoff/checker

| Attack or omission | Previous risk | Resolution |
|---|---|---|
| Empty Pack C Explore or zero search hits | Printed `ok` with zero evidence | Required inventory and segment hits; exact camera/location and source checks; no implicit fallback |
| Wrong/substring camera and malformed/paginated Explore | Wrong footage could be treated as Pack C | Exact-match gate; complete pagination and duplicate/unknown schema failures; application fix remains TODO |
| HTTP 200 but unloaded YOLO | Model readiness overstated | Require boolean `ok` and `model_loaded`; Reason/Embed require model list + ready + live |
| Redirect or HTTP error | Broad HTTP success could hide wrong service | Exact 200 and no redirects in connection/app checker |
| W&B exception printed then exit 0 | A failed inference looked successful to shell | Structured per-check results; exit 1 for failures, 2 for missing inputs; bounded inference with no retries |
| Unknown old default model | Authentication failure could be misdiagnosed | Explicit verified `SCRIBNER_MODEL`; account/project required; no fabricated catalog lookup |
| VSS alias/environment mismatch | Smoke could check a backend different from the app | Probe follows the app's VSS alias precedence; covered by regression |
| Mock app accepted as live | Nonempty units were enough to pass | Mandatory expected mode at app and per-unit level; live source/camera/unique-ID checks |
| No AUTO_ALERTs or loose Japanese string match | Station loop vacuously passed; wrong report LINE accepted | Mock requires all three decision fixtures and 40 units; exact report LINE extraction |
| Only API checks | Browser and remote logging could be assumed | Separate real source comparison, decoding/playback, UI controls, and W&B remote readback requirements |
| Re-ingest confirmation only when scope unresolved | Resolved target might skip final confirmation | Prepare exact target/chunks/prompt first; reuse exact prior authorization or obtain final confirmation required by skill |
| Vague laptop route scope | Existing app metadata/detection calls exceeded original laptop list | Exact laptop allowlist; documented workshop-only scope; receiving agent must adapt laptop scan or execute it on VM |
| Deployment undefined namespace / missing mounts | Instructions could deploy incorrectly or omit runtime files | Explicit assigned identity, kubeconfig aliases, static/code/lockfile/Secret requirements, prefix and restart checks |
| No workshop/submission finish | Local demo could be called contest-complete | VM/team limits, Cursor skills, cluster `/app`, clean start, public judge access, two-minute demo, official submission steps |
| Secret-bearing exceptions | Diagnostic output might disclose credentials | Report fixed reason codes or exception class; test hostile secret-containing exception text |
| Comparing displayed SHAs manually | Partial push could be overlooked | Shell equality assertions for local, Origin branch, GitHub branch, and GitHub public HEAD |

## Conflicts resolved explicitly

- The official day guide runs event work on the workshop VM. Bryce explicitly requested a laptop rehearsal; the handoff keeps that rehearsal and still requires the event deliverable on Kubernetes at `/app`.
- Official generic config/reference text says GPU auth may be absent; deployed model-health/smoke skills require `GPU_BEARER_TOKEN`. Bryce's explicit instruction makes the bearer optional and takes precedence: every configured URL is attempted, Authorization is sent only if a bearer exists, and 401/403 is fail. This override has a regression test. Hardcoded-host and Canary examples are not executed.
- The default pipeline uses Cosmos Reason, YOLO11, and Embed1. Canary is optional in the official stack and forbidden by this project. Weave/ARIA are optional; the required app inference/SDK proof is recorded separately.
- Provided video is already segmented. The actual challenge path is re-ingest through detector/reasoner/embedder/writer, with no Segmenter, upload, Docker, or DataEngine redeployment.
- Generic deployment/submission examples do not authorize other teams' resources, invented team identities, or claims of submission. Existing known repository choice is retained; missing team/feedback/event destination remains visible.

## Verification performed

- Full `scripts/run_adversarial.sh`: **87 tests passed** (67 existing + 20 handoff tests).
- All handoff Bash blocks passed `bash -n`; embedded Python compiled; required section order and Context ≤8 nonblank lines passed.
- Test attacks cover secret redaction, HTTP redirect/auth failures, missing services, dependent skips without losing other checks, VSS alias precedence, missing/wrong/substring cameras, incomplete/duplicate inventory, empty/parent-only search, unverified search-camera provenance, unloaded GPU, optional-bearer request behavior, missing model/readiness, invalid/nonfinite embeddings, W&B empty/timeout responses, mock-as-live, report LINE mismatch, duplicate/missing live sources, and missing mock lamp fixtures.
- Real local HTTP: checker against `http://127.0.0.1:8081` with `--expect mock` passed. It inspected 40 units and per-unit details.
- Real local negative HTTP: the same process with `--expect live` failed with `wrong_app_mode`, exit 1.
- Current connection check: all 10 configured-service checks were explicitly skipped for missing live inputs, exit 2. No live inference, re-ingest, SDK run, review mutation, or cluster mutation occurred.
- Prior clip playback/color/A/O and HTTP-400 evidence remains in `.cursor/adversarial/20261002-cowork.md`; these were not represented as new live evidence.
- `git diff --check` passed. Only handoff, checker, checker tests, and this report belong to this change.

Local artifacts: `/tmp/scribner-handoff-review-tests.log`, `/tmp/scribner-handoff-focused.log`, `/tmp/scribner-handoff-review-results.json`. Temporary artifacts are not committed. Tests use fake services or disposable Git fixtures; none contact real GPUs or W&B.

## What remains before hackathon completion

1. Fix the ten runtime integration items in handoff step 4 and verify regressions.
2. Obtain the assigned environment through normal login/configuration, verify VSS/GPU/W&B, and record actual app use and remote W&B runs.
3. Execute the specifically confirmed Pack C re-ingest; prove updated captions, source pairing, real playback, human review, and retrain.
4. Deploy and restart-test the app on this team's cluster at `/app`, including mounts, dependencies, prefix, and label-state behavior.
5. Finish the agreed official `SUBMISSION.md`, clean-start demonstration, public judge access, and actual organizer submission process.

These open items prevent a claim that every live hackathon requirement is already met. The handoff now makes each one an explicit completion condition with an owner and observable proof.
