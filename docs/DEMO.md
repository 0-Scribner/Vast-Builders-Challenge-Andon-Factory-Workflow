# Judge demo (2 minutes)

Pick the mode before the judges arrive.

| Mode | Start | Open |
|------|-------|------|
| Local mock | `SCRIBNER_MOCK=1 ./scripts/run_mock.sh` | `http://127.0.0.1:8080` |
| Team Ingress | `bash workshop/07_deploy_scribner.sh` on the workshop VM, in advance | the `/app` URL that the script prints |

The header chip reads `MOCK` or `LIVE`. Mock clips are generated warehouse stand-ins; say so out loud in mock mode. The team Ingress path needs the workshop VM and the team config, and it has not run yet. Until it has, demo the local mock.

Before the clock starts: load the page and open the 現場 Queue tab. If the queue is empty, click **Scan / reload**.

Keys: `A` or `C` marks CLEAR (正常). `O` or `U` marks UNSAFE (異常, pulls the andon cord). `N` moves to the next queued unit.

## Script

**0:00 to 0:15. Problem.**
"A person close to a moving vehicle is a near-miss. Today a human scrubs camera footage to find it. Scribner puts an andon over the official Pack C warehouse video instead."

**0:15 to 0:35. The board.**
Point at the three line lamps: 正常 CLEAR (green, run), 呼び出し HOLD (yellow, call a human), 停止 ALERT (red, stop). "The line lamps track the worst open ticket. The station tower beside the clip tracks this clip."

**0:35 to 0:55. The prompt is the schema.**
Open a unit with `PATH_CLEAR: YES`, then one with `NEAR_MISS: YES`, in the schema panel. "The ingest prompt asks Cosmos Reason for these fields, so the caption is the inspection record. A near-miss clip is a red lamp, not a search hit."

**0:55 to 1:25. Review.**
Label about eight queued units: `A` for a clear aisle, `O` for a near-miss (the andon cord), `N` to move on. Point at the hint under the buttons: changing an AUTO_ALERT to CLEAR needs a confirm. "Red never goes green without a person."

**1:25 to 1:40. Retrain.**
Click **Retrain**. "The labels refit a small logistic regression anchored to the Cosmos caption prior, then re-derive the CLEAR and ALERT thresholds." Read the KPI row as it stands after the refit. A clip with an UNCLEAR field never auto-clears.

**1:40 to 1:50. Shift report.**
Open the **Shift report** tab: units, decisions, labels, current metrics and the stack line for the shift.

**1:50 to 2:00. Stack line.**
Point at the footer: VAST, NVIDIA Cosmos, CoreWeave and W&B, Cursor, and the payoff query *person close to a moving vehicle*. "Camera `sdg_warehouse_cam-2`, provided Pack C footage, official Builders Challenge stack only." `/health` returns the same stack line.

## Recovery

- Port 8080 busy: run `PORT=8081 ./scripts/run_mock.sh` and open `http://127.0.0.1:8081`.
- Empty queue: click **Scan / reload**.
- Live clip does not play under `/app`: switch to the local mock and say it is the mock.
