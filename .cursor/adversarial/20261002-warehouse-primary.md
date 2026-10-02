# Adversarial review — warehouse Primary 2026-10-02

Parser/gate retooled to PATH_CLEAR / NEAR_MISS + AUTO_CLEAR / AUTO_ALERT / HOLD.
Official clone: `/tmp/vast-builders-challenge` @ 4987d8e.

| Attack | Expected | Result | Evidence |
|--------|----------|--------|----------|
| PATH_CLEAR YES + NEAR_MISS YES | not AUTO_CLEAR; AUTO_ALERT | pass | `test_inconsistent_caption_never_auto_clear` |
| Pack C forklift-near-person caption | AUTO_ALERT, never AUTO_CLEAR | pass | `test_pack_c_near_miss_caption_never_auto_clear` |
| LOW confidence PATH_CLEAR YES | HOLD | pass | `test_low_confidence_never_auto_clear` |
| UNCLEAR nonempty | not AUTO_CLEAR | pass | `test_unclear_never_auto_clear` |
| view_blocked / occlusion | HOLD | pass | `test_occlusion_never_auto_clear` |
| YOLO person+vehicle without HIGH PATH_CLEAR | not AUTO_CLEAR | pass | `test_yolo_person_vehicle_never_sole_source_clear` |
| `gate_ok=true` on HOLD | 400 / ValueError | pass | `test_gate_ok_on_hold_is_400` |
| AUTO_ALERT → CLEAR without confirm_escape | ValueError | pass | `test_auto_alert_to_clear_needs_confirm` |
| override reason=agree | ValueError | pass | `test_override_agree_rejected` |
| YouTube / http / random.mp4 / spaceship / 801-char prompt | IngestRejected | pass | IngestPokaYokeTests |
| `/api/v1/reports` or GPU host `166.19.38.112` or Canary | not in runtime | pass | `scan_scribner_violations` empty |
| `/health` missing official source or warehouse-near-miss | fail the pin | pass | `test_health_pins_builders_stack` |
| UI missing AUTO_CLEAR / UNSAFE / payoff query | fail operator contract | pass | `test_ui_is_warehouse_operator` |
| unittest discover | 45 OK | pass | 0.074s |

Oracle mock: cold coverage 80% HOLD 20%; after labels coverage 100% HOLD band 0.64 → 0.37.
