---
name: ingest-kits
description: >-
  Re-ingest the official provided Pack C warehouse clips
  (sdg_warehouse_cam-2) with the warehouse-aisle path-safety
  custom_prompt. Use when the team says "reingest warehouse",
  "pack C", "provided videos", "ingest kits", "path clear prompt".
---

# Ingest provided Pack C clips

The judged corpus is **already indexed**. Live path is **re-ingest**, not
a bulk re-upload.

## Before any re-ingest

1. Confirm with Bryce which camera. Prefer Pack C `sdg_warehouse_cam-2`.
2. Read live limits: `GET $INGRESS_URL/api/v1/metadata/ingest-config`.
3. Generate the prompt from code (do not hand-type it). Must be ≤800 chars.

```bash
cd /path/to/Scribner
PYTHONPATH=tools/scribner python3 -c "from kits import prompt_for_kit; p=prompt_for_kit('warehouse-aisle'); print(len(p)); print(p)"
```

Never send JSON as the prompt — VSS strips JSON from Cosmos output.

## Metadata for Pack C re-ingest

| Field | Value |
|-------|--------|
| `custom_prompt` | `prompt_for_kit('warehouse-aisle')` |
| `camera_id` | `sdg_warehouse_cam-2` (omit to preserve) |
| `capture_type` | `warehouse` if ingest-config allows it, else omit |
| `location` | `warehouse3` if changing metadata, else omit |

Use the challenge repo's `ingest/reingest-videos` skill for the HTTP shape
(`POST /api/v1/dashboard/reingest`). Scribner's `vss_client.reingest` is a
thin wrapper. Omit `scenario` when `custom_prompt` is set.

Re-ingest **one clip first**, wait until Explore shows `PATH_CLEAR:` in the
caption, then continue. Designate 1–2 people; do not stampede the GPU queue.

## After re-ingest

In Scribner (live mode, `SCRIBNER_MOCK=0`): `POST /api/scan` then open the
review queue. Default filter is `SCRIBNER_CAMERA_ID=sdg_warehouse_cam-2`.
Cross-pack: `SCRIBNER_PACK=cross` (search *person close to a moving vehicle*).

## Agent rules

- Do not guess the target. List Explore rows and match `sdg_warehouse_cam-2`.
- Do not print JWTs or passwords.
- Do not rebuild DataEngine or call Docker.
- Do not fall back to Plan B LEGO prompts on this branch.
