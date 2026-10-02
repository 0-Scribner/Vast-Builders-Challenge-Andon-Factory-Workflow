# Adversarial review — andon + footage follow-up 2026-10-02

Follow-up on Japanese QC 安灯 + warehouse near-miss. Official clone: `/tmp/vast-builders-challenge` @ 4987d8e. Mock server `SCRIBNER_MOCK=1` on `:8080`. **Live Pack C VSS skipped** (`INGRESS_URL`/`VSS_URL` unset). Footage proven is mock andon-tinted aisle (`sdg_warehouse_cam-2` overlay, 緑/黄/赤), not a grey rectangle. `canary_called=no`.

HEAD at review: `ae80e58` then this file.

| Attack | Expected | Result | Evidence |
|--------|----------|--------|----------|
| PATH_CLEAR YES + NEAR_MISS YES | not AUTO_CLEAR; AUTO_ALERT / 赤 | pass | `test_inconsistent_caption_never_auto_clear`; `test_inconsistent_never_auto_clear` |
| Pack C forklift-near-person caption | AUTO_ALERT, never AUTO_CLEAR | pass | `test_pack_c_near_miss_caption_never_auto_clear` |
| LOW confidence PATH_CLEAR YES | HOLD / 黄 | pass | `test_low_confidence_never_auto_clear` |
| UNCLEAR nonempty | not AUTO_CLEAR | pass | `test_unclear_never_auto_clear` |
| view_blocked / occlusion | HOLD | pass | `test_occlusion_never_auto_clear` |
| YOLO person+vehicle without HIGH PATH_CLEAR | not AUTO_CLEAR | pass | `test_yolo_person_vehicle_never_sole_source_clear`; `test_yolo_both_without_high_clear_never_auto_clear` |
| YOLO `hand`/`person` as Pack C occlusion | not HOLD-every-person | pass | `test_pack_c_person_forklift_hand_is_not_occlusion`; `scan._occlusion` always False |
| W&B PASS on NEAR_MISS p_fail < 0.8 | clamp ≥ 0.8, proposed FAIL | pass | `test_wandb_pass_cannot_undercut_near_miss` |
| W&B PASS on LOW/UNCLEAR | stay HOLD band | pass | `test_wandb_pass_cannot_undercut_low_confidence` |
| `gate_ok=true` on HOLD | HTTP 400 | pass | `test_http_gate_ok_on_hold_is_400`; curl POST mock → `400` |
| AUTO_ALERT→CLEAR without `confirm_escape` | HTTP 400 | pass | `test_http_auto_alert_clear_without_confirm_is_400`; curl → `400` |
| override reason=agree | HTTP 400 | pass | `test_http_override_reason_agree_is_400`; curl → `400` |
| YouTube / http / random.mp4 / spaceship / 801-char prompt | IngestRejected | pass | IngestPokaYokeTests |
| `/api/v1/reports` wired as a client call | fail | pass | listed only in `forbidden_vss_paths`; `scan_scribner_violations()==[]` |
| GPU host `166.19.38.112` | not in runtime | pass | `test_gpu_client_module_does_not_reference_canary_url`; health blob has no host |
| Canary transcriptions | not wired | pass | `gpu.canary` false; `canary_wired` false; `canary_called=no` |
| `/health` missing official source / warehouse-near-miss / andon | fail the pin | pass | `test_http_health_pins_stack_andon_no_canary`; curl `/health` |
| UI missing 安灯 / ANDON / 呼び出し / 停止 / `/api/andon` / payoff / AUTO_CLEAR / UNSAFE | fail | pass | `test_ui_is_warehouse_operator`; curl `/` greps |
| `/api/andon` not Pack C 現場 | fail | pass | `camera_id=sdg_warehouse_cam-2`, `board=andon`, rule 赤灯 |
| AUTO_ALERT `station_lamp` not red | fail | pass | `GET /api/andon?unit_id=wh-017` → `station_lamp` red / 停止 |
| empty queue `line_lamp` not green | fail | pass | `test_line_lamp_red_beats_yellow`; `line_lamp([])==green` |
| HOLD+ALERT `line_lamp` not red | fail | pass | mock line `停止` / red; synthetic HOLD+ALERT → red |
| Report LINE ≠ `/api/andon` `line_ja` | fail | pass | report `- 安灯 ANDON line: **停止**`; `test_http_report_line_matches_andon` |
| mock `/clip?unit_id=` grey / empty | fail | pass | AUTO_ALERT clip 14767 B, RGB 45.5/19.5/17.6 spread 27.9; `test_http_clip_alert_is_andon_tinted_mp4_not_grey`; `test_warehouse_clips_are_andon_tinted_not_grey` |
| live `/clip` empty source | fall back to unit.source | pass | `test_clip_source_falls_back_to_unit` |
| unittest discover | ~52+ OK | pass | **64 OK** in 1.632s via `./scripts/run_adversarial.sh` |
| Browser UI plays clip with lamps | not grey rectangle | pass | DISPLAY=:1 Chrome `http://127.0.0.1:8080/` MOCK; line 赤 停止; station 黄 呼び出し; aisle clip `sdg_warehouse_cam-2` / 呼び出し HOLD. Artifacts: `/opt/cursor/artifacts/andon_operator_ui_loaded.png`, `andon_operator_report_tight.png`, `andon_aisle_{green,yellow,red}.png`, `andon_operator_mock_pack_c_lamps_and_aisle_clip.mp4` |
| Live Pack C `sdg_warehouse_cam-2` VSS stream | play real segment | skipped | `footage_live=skipped (no INGRESS_URL/VSS_URL)` — do not claim live Pack C |

Fixes this pass (attacks that were open or leftover):

- W&B prior could return PASS / p=0.05 on NEAR_MISS → `merge_wandb_prior` clamps.
- Pack C YOLO `hand` treated as occlusion (LEGO leftover) → `_occlusion` is False.
- Live `/clip` ignored `unit_id` when `source` empty → `clip_source()`.
- Empty ffmpeg fallback wrote 0-byte clip → simpler tinted aisle instead.
- Cowork handoff missing live-vs-mock footage, HTTP 400 curls, not-grey RGB, browser verify.

Red never auto-greens. 赤灯は人なしで緑にしない.
