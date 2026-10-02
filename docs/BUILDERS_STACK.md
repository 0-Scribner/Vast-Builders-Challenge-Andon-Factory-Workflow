# Official Builders Stack (conformance lock)

Scribner uses **only** the stack in
[vast-data/vast-builders-challenge](https://github.com/vast-data/vast-builders-challenge).
Pinned commit in `tools/scribner/builders_stack.py` (`PINNED_COMMIT`).

Re-extract / attack:

```bash
git clone --depth 1 https://github.com/vast-data/vast-builders-challenge.git /tmp/vast-builders-challenge
export BUILDERS_CHALLENGE_DIR=/tmp/vast-builders-challenge
./scripts/run_adversarial.sh
```

## What we may use

| Piece | Names / routes | Skill |
|-------|----------------|--------|
| Identity + VSS | `USERNAME`, `PASSWORD`, `INGRESS_URL` (pod aliases `VSS_*`) | `retrieval/login` |
| S3 / VastDB | `S3_*`, `ACCESS_KEY`, `SECRET_KEY`, `VDB_*`, `VASTDB_*` | `retrieval/vastdb-read` (debug only; app uses HTTP) |
| Pipeline | `PIPELINE` (UI name, unused by skills) |, |
| W&B Inference | `WANDB_API_KEY`, `WANDB_TEAM`, `WANDB_PROJECT` | BUILD_DAY.md |
| GPU NIMs | `COSMOS3_REASON_URL`, `YOLO_URL`, `COSMOS_EMBED1_URL`, models, optional `GPU_BEARER_TOKEN` | `gpu/*` |
| Upload | `POST /api/v1/videos/upload` fields in upload-video; `custom_prompt` <=800; omit `scenario` when prompt is set | `ingest/upload-video` |
| Re-ingest | `POST /api/v1/dashboard/reingest` | `ingest/reingest-videos` |
| Search / explore / detections / stream / dashboard / metadata | routes in `retrieval/README.md` | `retrieval/*` |
| Deploy | ConfigMap + `python:3.12-slim` + Ingress **`/app`** | `deployment/deploy-app-no-registry` |

## What we must not use

- Invented VSS routes: `/reports`, `/alerts`, `/analytics`, `/videos/ask`, `/tags`, `/locations`, `/extra-metadata`
- YouTube / internet video
- Docker build/push; DataEngine rebuild; native apps
- Hardcoded GPU host `166.19.38.112` (skill example only, use env URLs)
- Canary-1B in the aisle gate (`CANARY_1B_URL` is documented and **unread for inference**)

Machine-readable copy: `tools/scribner/builders_stack.py` + `builders_stack_lock.json`.
