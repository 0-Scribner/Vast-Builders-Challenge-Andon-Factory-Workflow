# Adversarial review — warehouse andon 2026-10-02

Japanese QC 安灯 on Pack C (`sdg_warehouse_cam-2`). Line lamp = worst open queue ticket. Station lamp = clip on screen. Mock `/clip` is an andon-tinted aisle. Official clone: `/tmp/vast-builders-challenge`.

| Attack | Expected | Result | Evidence |
|--------|----------|--------|----------|
| PATH_CLEAR YES + NEAR_MISS YES | not AUTO_CLEAR; AUTO_ALERT / 赤 | pass | `test_inconsistent_caption_never_auto_clear` |
| Pack C forklift-near-person caption | AUTO_ALERT, never AUTO_CLEAR | pass | `test_pack_c_near_miss_caption_never_auto_clear` |
| LOW confidence PATH_CLEAR YES | HOLD / 黄 | pass | `test_low_confidence_never_auto_clear` |
| UNCLEAR nonempty | not AUTO_CLEAR | pass | `test_unclear_never_auto_clear` |
| view_blocked / occlusion | HOLD | pass | `test_occlusion_never_auto_clear` |
| YOLO person+vehicle without HIGH PATH_CLEAR | not AUTO_CLEAR | pass | `test_yolo_person_vehicle_never_sole_source_clear` |
| `gate_ok=true` on HOLD | 400 / ValueError | pass | `test_gate_ok_on_hold_is_400` |
| AUTO_ALERT → CLEAR without confirm_escape | ValueError | pass | `test_auto_alert_to_clear_needs_confirm` |
| override reason=agree | ValueError | pass | `test_override_agree_rejected` |
| YouTube / http / random.mp4 / spaceship / 801-char prompt | IngestRejected | pass | IngestPokaYokeTests |
| `/api/v1/reports` or GPU host `166.19.38.112` or Canary | not in runtime | pass | `scan_scribner_violations` empty |
| `/health` missing official source, warehouse-near-miss, or andon | fail the pin | pass | `test_health_pins_builders_stack` |
| UI missing AUTO_CLEAR / UNSAFE / 安灯 / ANDON / `/api/andon` / payoff | fail operator contract | pass | `test_ui_is_warehouse_operator` |
| `/api/andon` not Pack C 現場 | fail | pass | `test_andon_api_maps_queue_to_lamps` |
| AUTO_ALERT unit `station_lamp` not red | fail | pass | `test_andon_station_follows_alert_unit` |
| empty queue `line_lamp` not green; HOLD+ALERT not red | fail | pass | `test_line_lamp_red_beats_yellow` |
| unittest discover | 52 OK | pass | 0.076s |

Red never auto-greens. Operator O pulls the andon cord.
