# Scribner workshop execution kit: deliverables 2-8

Prepared against Primary branch `cursor/warehouse-primary-72e3`, public baseline `c9034f52a29da266e5da669ff1e14eb47cde00cf`, and official Builders Challenge commit `4987d8ebd8e5270dccf0864851a16ed42eb8d8e7`.

These scripts contain no credentials. Run them only in the assigned workshop environment after sourcing the single `/config/<team>.config`. Reports default to `/tmp/scribner-live-evidence` so live responses are not committed.

## 2. VSS preflight

```bash
set -a && source /config/<team>.config && set +a
python workshop/02_vss_preflight.py
```

Requires exact camera `sdg_warehouse_cam-2` and location `warehouse3`, validates the Explore inventory, and records the payoff query status. Zero verified payoff hits before re-ingest is reported, not misrepresented as proof.

## 3. Re-ingest one complete Pack C chunk first

```bash
python workshop/03_reingest_one_pack_c.py --list
python workshop/03_reingest_one_pack_c.py --target '<exact ID from list>' --yes
```

Only complete Pack C parents are offered. It generates `warehouse-aisle` from code, checks the live prompt limit, launches exactly one job, waits for completion, then requires `PATH_CLEAR`, `NEAR_MISS`, `UNCLEAR`, and `CONFIDENCE` in refreshed caption evidence.

## 4. Expand sequentially

Only after step 3 passes:

```bash
python workshop/04_reingest_remaining_pack_c.py \
  --verified-one-chunk --yes \
  --skip-target '<target already verified>'
```

Use `--limit N` for a staged run. Jobs are sequential.

## 5. Prove real Pack C in Scribner

Start live mode with a separate local store:

```bash
SCRIBNER_MOCK=0 SCRIBNER_PACK=C SCRIBNER_CAMERA_ID=sdg_warehouse_cam-2 \
SCRIBNER_DATA_DIR=/tmp/scribner-live PORT=8082 ./scripts/run_mock.sh
```

Then:

```bash
python workshop/05_verify_live_scribner.py --app-url http://127.0.0.1:8082
```

The verifier requires exact Pack C provenance, unique segment sources, source/caption schema pairing, `/clip` bytes matching the verified VSS source, valid MP4 decode, correct lamps, and illegal review overrides returning 400. A manual browser check is still required for the LIVE indicator and playback.

## 6. GPU + W&B proof

Set `SCRIBNER_MODEL` explicitly to a model verified available in the assigned W&B account, then:

```bash
python workshop/06_verify_gpu_wandb.py --app-url http://127.0.0.1:8082
```

Requires Cosmos Reason health + nonempty inference, YOLO health + direct inference on a real Pack C clip, Embed1 health + 256 finite values, W&B prior use with near-miss clamp, an online W&B SDK smoke run with remote readback, and an actual Scribner retrain whose remote run contains `andon_line` and numeric andon metrics.

## 7. Deploy at `/app`

```bash
bash workshop/07_deploy_scribner.sh
```

No Docker. Uses `python:3.12-slim`, separate code/static ConfigMaps, includes `builders_stack_lock.json`, uses a Secret for VSS/W&B/GPU settings, creates a 256Mi PVC `scribner-data` mounted at `/data`, sets live Pack C explicitly, and deploys only under the existing team host `/app`.

If the PVC cannot bind, stop and resolve the team-approved StorageClass. Do not fall back to `/tmp` and claim persistence.

Then rerun deliverable 5 against the printed event URL. Restart the deployment once and verify review/model state behaves as claimed. Inspect browser network requests: all Scribner requests must remain under `/app`.

## 8. Finalize submission

The patch corrects the public code URL. After deployment:

```bash
python workshop/08_finalize_submission.py --feedback 'YOUR EVENT FEEDBACK'
```

It fills team identity from `$USERNAME`/`$PIPELINE` and derives the live `/app` URL from `$INGRESS_URL`. Review the final `SUBMISSION.md` and follow the organizers' actual submission workflow.

## Final adverse audit before push

```bash
./scripts/run_adversarial.sh
python -m unittest discover -s tools/scribner/tests -v
git diff --check
```

Do not claim steps 2-8 complete until their real environment evidence passes.
