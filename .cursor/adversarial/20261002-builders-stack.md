# Adversarial review — official Builders Stack

Date: 2026-10-02
Against: https://github.com/vast-data/vast-builders-challenge @ `4987d8ebd8e5270dccf0864851a16ed42eb8d8e7`
Command: `BUILDERS_CHALLENGE_DIR=/tmp/vast-builders-challenge ./scripts/run_adversarial.sh`
Result: 36 tests OK (then poka-yoke API HOLD case re-run OK).

| Attack | Expected | Result | Fix |
|--------|----------|--------|-----|
| COMPLETE:YES + MISSING: 4 black wheels | not AUTO_PASS | pass | `gate.pass_blocked` + `inspection.inconsistent` |
| CONFIDENCE:LOW COMPLETE:YES | not AUTO_PASS | pass | fail-closed HOLD |
| UNCLEAR nonempty + complete yes | not AUTO_PASS | pass | fail-closed HOLD |
| occlusion + complete yes | not AUTO_PASS | pass | fail-closed HOLD |
| complete=NO with forced low p_fail | AUTO_FAIL not PASS | pass | fail-closed AUTO_FAIL |
| POST gate_ok=true on HOLD | 400 / ValueError | pass | `state.review` |
| AUTO_FAIL→COMPLETE without confirm_escape | 400 | pass | `confirm_escape` |
| override reason=agree | 400 | pass | non-agree required |
| `random.mp4` | reject | pass | `ingest.FILENAME_RE` |
| kit `spaceship` | reject | pass | known kits only |
| 801-char prompt | reject | pass | `CUSTOM_PROMPT_MAX` |
| `https://www.youtube.com/watch?v=…` | reject | pass | `ingest.looks_like_remote` |
| http clip URL | reject | pass | same |
| `scenario` sent with `custom_prompt` | dropped | pass | `filter_upload_fields` |
| Invented `/api/v1/reports` (etc.) in runtime | none | pass | `scan_scribner_violations` |
| VSS paths not in challenge skills | none | pass | subset check vs clone |
| env names not in `config.example` + aliases | none | pass | `ALLOWED_RUNTIME_ENV` |
| Hardcoded GPU host `166.19.38.112` | none | pass | gpu_client uses env URLs |
| Canary ASR wired (`CANARY_1B_URL` / transcriptions) | none in gpu_client | pass | not imported; `gpu.canary=false` |
| config.example env drift vs clone | lock matches | pass | `extract_builders_stack.py` |
| upload-video field contract / 800 cap | present in clone | pass | locked |
| deploy-app-no-registry `/app` + python:3.12-slim + no docker | present | pass | `deploy/DEPLOY.md` |

False PASS remains the red line. Do not weaken these tests to make a demo look better.
