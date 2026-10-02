---
name: ingest-kits
description: >-
  Upload Bryce's LEGO kit phone clips into the team VSS instance with the
  kit bill-of-materials custom_prompt, tags, and camera metadata. Use when
  the team has filmed race-car or front-loader kits and wants them indexed,
  or says "upload the lego videos", "ingest kits", "custom prompt for kits".
---

# Ingest LEGO kit clips

Own footage is allowed. Internet / YouTube video is **not**.

## Before any upload

1. Confirm with Bryce (or Cosmos) that new uploads are OK if Architecture Reference sounded re-ingest-only.
2. Read live limits: `GET $INGRESS_URL/api/v1/config` (max_upload_size_mb, often 25).
3. Clips must be **4.0–4.8 seconds**, kit filling the frame, white background, **no hands**, 1080p not 4K, `.mp4`.
4. Kit id is `race-car` or `front-loader` (see `tools/scribner/kits.py`). If they filmed a new kit, edit `kits.py` first and regenerate prompts.

## Prompt (must be ≤800 chars)

Generate from code, do not hand-type:

```bash
cd /path/to/Scribner
python3 -c "from kits import prompt_for_kit; import sys; sys.path.insert(0,'tools/scribner')"
PYTHONPATH=tools/scribner python3 -c "from kits import prompt_for_kit; print(prompt_for_kit('race-car')); print(len(prompt_for_kit('race-car')))"
```

Use `front-loader` when the clip is that kit. Never send JSON as the prompt — VSS strips JSON from Cosmos output.

## Metadata for every file

| Field | Value |
|-------|--------|
| `custom_prompt` | `prompt_for_kit(kit_id)` |
| `tags` | `kit:<kit_id>,unit:<id>,variant:<complete\|missing-wheels\|…>` |
| `camera_id` | `kit-station-1` |
| `capture_type` | `general` |
| `location` | `kit-bench` |
| `is_public` | `true` |

Filename: `kit-<kit_id>_unit-<id>.mp4` e.g. `kit-race-car_unit-014.mp4`.

## Upload

On the workshop VM, credentials are already in the environment (`INGRESS_URL`, `USERNAME`, `PASSWORD` from `/config/<team>.config`, names in the official `config.example`). Use the challenge repo's `ingest/upload-video` skill for the HTTP shape. Scribner's `vss_client.upload_video` is a thin wrapper over that same multipart table (`file`, `is_public`, `tags`, `custom_prompt`, `camera_id`, `capture_type`, `location`; omit `scenario` when `custom_prompt` is set).

```bash
PYTHONPATH=tools/scribner python3 - <<'PY'
from pathlib import Path
from kits import CAMERA_ID, CAPTURE_TYPE, LOCATION, prompt_for_kit
from vss_client import VssClient

client = VssClient()
kit_id = "race-car"  # or front-loader
prompt = prompt_for_kit(kit_id)
folder = Path("/path/to/clips")
for i, path in enumerate(sorted(folder.glob("*.mp4")), start=1):
    tags = f"kit:{kit_id},unit:{i:03d},variant:unknown"
    print(path.name, client.upload_video(
        str(path),
        custom_prompt=prompt,
        tags=tags,
        camera_id=CAMERA_ID,
        capture_type=CAPTURE_TYPE,
        location=LOCATION,
    ))
PY
```

One file per request. After each batch, poll dashboard/explore until `fully_indexed`. Do not claim searchability until Explore shows the clips.

## After ingest

In Scribner (live mode, `SCRIBNER_MOCK=0`): `POST /api/scan` then open the review queue.

## Agent rules

- Confirm kit_id with Bryce if the filename does not contain `race-car` or `front-loader`.
- Do not upload if size exceeds `max_upload_size_mb`.
- Do not print JWTs or passwords.
- Designate 1–2 people for bulk upload; do not stampede the shared GPU queue.
