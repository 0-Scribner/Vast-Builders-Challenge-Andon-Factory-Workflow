# Adversarial log — restore original pipeline on provided Pack C — 2026-10-02

Official clone: https://github.com/vast-data/vast-builders-challenge
Parser/gate restored to PRESENT/MISSING/COMPLETE + AUTO_PASS/AUTO_FAIL/HOLD.
Judged footage is the provided Pack C corpus, not filmed LEGO.

| Attack | Expected | Result | Notes |
|--------|----------|--------|-------|
| Prompt >800 | ValueError / IngestRejected | pass | all kit prompts ≤596 |
| YouTube upload | IngestRejected | pass | ingest.py |
| COMPLETE:YES + MISSING | not AUTO_PASS | pass | gate.pass_blocked |
| Pack C MISSING person-gap | AUTO_FAIL, never AUTO_PASS | pass | test_pack_c_missing_gap_never_auto_pass |
| LOW confidence COMPLETE | HOLD | pass | |
| Person on Pack C as occlusion | not HOLD-all | pass | scan._occlusion corpus kits ignore person |
| Invented VSS routes | none in vss_client | pass | adversarial suite |
| Canary wired | canary_wired false | pass | |
| UI AUTO_CLEAR/UNSAFE | absent | pass | original C/I |
| Hardcoded GPU host | absent | pass | |
