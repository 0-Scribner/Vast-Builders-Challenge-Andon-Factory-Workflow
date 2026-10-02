# Handoff: ingest LEGO kit clips into team VSS

Give this file to the workshop-VM Cursor agent. It uploads Bryce's kit footage so Scribner can scan it. Clips never go in git.

## Receiver

Workshop VM Cursor agent. CWD = this Scribner repo (`AGENTS.md` at root). All commands run in the **browser VM terminal**, not Bryce's laptop. Skills from the VAST challenge repo may also be present at `~/vast-builders-challenge`; prefer this repo's `tools/scribner` for prompts and the challenge `ingest/upload-video` skill for the HTTP shape.

## Done when

- [ ] Every `kit-<kit_id>_unit-<nnn>.mp4` under the clips dir has been `POST /api/v1/videos/upload`'d once with `custom_prompt` from `prompt_for_kit(kit_id)`, tags `kit:<kit_id>,unit:<nnn>,scribner`, `camera_id=kit-station-1`, `capture_type=general`, `location=kit-bench`, `is_public=true`.
- [ ] Each prompt used is ≤800 characters.
- [ ] Explore (`GET /api/v1/videos/explore?scope=mine`) lists those filenames as fully indexed parents (usually 1 segment).
- [ ] At least one indexed caption contains the literals `PRESENT:` and `COMPLETE:`.
- [ ] A filled Report back block is shown to Bryce.
- Out of scope: running the Scribner gate, reviewing units, retraining, deploying `/app`, committing video files.

## Context

Scribner parses Cosmos captions with `tools/scribner/inspection.py`. That parser only works if ingest used the BOM custom prompt from `tools/scribner/kits.py` (`prompt_for_kit`). Default `scenario=general` produces unusable captions. Known `kit_id`s: `race-car`, `front-loader`. Pipeline: upload → segmenter (~5s) → YOLO → Cosmos Reason → Embed1 → VastDB. YOLO has no LEGO classes; do not mention detections as brick ID.

## Never

- Do not ingest YouTube or other internet video.
- Do not `git add` clips, zips, or anything under `~/kit-clips`.
- Do not print `/config` values, JWTs, passwords, or `Bearer` tokens. `env | cut -d= -f1 | sort` only.
- Do not send `scenario` on the same request as `custom_prompt`. Custom prompt wins only if scenario is omitted.
- Do not guess `kit_id`. Read it from the filename `kit-<kit_id>_unit-<nnn>.mp4` or from tags. If the id is not in `kits.py`, stop (see Stop and escalate).
- Do not search the archive and claim success before Explore shows the parent fully indexed.
- Do not have a second teammate upload the same files. One uploader.
- Do not rebuild DataEngine or use Docker.

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Team config | exactly one `/config/*.config` | yes |
| Clip directory | `$KIT_CLIPS_DIR` or `~/kit-clips` | yes |
| Files | `kit-<kit_id>_unit-<nnn>.mp4` (also `.mov`/`.webm`/`.mkv` if that is what the phone wrote) | yes |
| BOM prompts | `from tools.scribner.kits import prompt_for_kit` | yes |
| Live size limit | `GET $BACKEND/api/v1/config` → `app.max_upload_size_mb` (often 25) | yes |

If clips are still on the laptop: tell Bryce to put a zip on Drive and `curl -L -o /tmp/kits.zip '<url>' && mkdir -p ~/kit-clips && unzip -o /tmp/kits.zip -d ~/kit-clips`. Do not wait on a second channel if the dir already has mp4s.

## Procedure

1. **Confirm environment.**

```sh
mapfile -t TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
(( ${#TEAM_CONFIGS[@]} == 1 )) || { echo "BLOCKED: expected exactly one /config/*.config"; exit 1; }
set -a && source "${TEAM_CONFIGS[0]}" && set +a
BACKEND="$INGRESS_URL"
CLIPS="${KIT_CLIPS_DIR:-$HOME/kit-clips}"
test -d "$CLIPS" || { echo "BLOCKED: no clip dir at $CLIPS"; exit 1; }
```

2. **Login.** Do not echo `$TOKEN`.

```sh
TOKEN=$(curl -s -X POST "$BACKEND/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
test -n "$TOKEN" || { echo "BLOCKED: login failed"; exit 1; }
```

3. **Read live upload limits.** Skip files over `max_upload_size_mb` or with a disallowed extension; list them in Report back as skipped.

```sh
curl -s "$BACKEND/api/v1/config" -H "Authorization: Bearer $TOKEN"
```

4. **For each clip**, parse `kit_id` and `unit` from the filename. If `kit_id` is unknown, stop that file and escalate. Build the prompt in Python (do not hand-type it). Confirm `len(prompt) <= 800`. Upload **one file per request**. Omit `scenario`.

```sh
# example for one file; loop in Python or bash. Build JSON/form with python so the prompt is escaped.
python3 - <<'PY'
import os, re, subprocess, sys
sys.path.insert(0, ".")
from tools.scribner.kits import prompt_for_kit, kit_ids, CAMERA_ID, CAPTURE_TYPE, LOCATION

clips = os.environ.get("KIT_CLIPS_DIR", os.path.expanduser("~/kit-clips"))
backend = os.environ["INGRESS_URL"]
token = os.environ["TOKEN"]
pat = re.compile(r"kit-([a-z0-9-]+)_unit-([0-9]+)\.(mp4|mov|webm|mkv|avi)$", re.I)
ok, skipped, failed = [], [], []
for name in sorted(os.listdir(clips)):
    m = pat.match(name)
    if not m:
        skipped.append((name, "filename"))
        continue
    kit_id, unit, _ = m.group(1).lower(), m.group(2), m.group(3)
    if kit_id not in kit_ids():
        skipped.append((name, f"unknown kit_id={kit_id}"))
        continue
    prompt = prompt_for_kit(kit_id)
    path = os.path.join(clips, name)
    tags = f"kit:{kit_id},unit:{unit},scribner"
    cmd = [
        "curl", "-s", "-X", "POST", f"{backend}/api/v1/videos/upload",
        "-H", f"Authorization: Bearer {token}",
        "-F", f"file=@{path}",
        "-F", "is_public=true",
        "-F", f"tags={tags}",
        "-F", f"custom_prompt={prompt}",
        "-F", f"camera_id={CAMERA_ID}",
        "-F", f"capture_type={CAPTURE_TYPE}",
        "-F", f"location={LOCATION}",
    ]
    out = subprocess.check_output(cmd, text=True)
    print(name, out[:300].replace("\n", " "))
    if '"success": true' in out or '"success":true' in out:
        ok.append(name)
    else:
        failed.append((name, out[:200]))
print(f"OK={len(ok)} SKIP={len(skipped)} FAIL={len(failed)}")
for row in skipped + failed:
    print("ISSUE", row)
PY
```

Export `TOKEN` and `INGRESS_URL` into that Python process via the environment; do not write them to a file.

5. **Poll until indexed.** Re-login if 401. Wait 15s between polls, cap 20 minutes.

```sh
curl -s "$BACKEND/api/v1/dashboard/stats?scope=mine" -H "Authorization: Bearer $TOKEN"
curl -s "$BACKEND/api/v1/videos/explore?scope=mine&limit=100&offset=0" -H "Authorization: Bearer $TOKEN"
```

A parent is ready when its timeline covers segments `1..total_segments` (kit clips: usually 1). Count how many filenames match `kit-`.

6. **Spot-check captions.** Pick one complete-looking clip and one missing-part clip. `GET /api/v1/videos/metadata?source=<preview_source>`. `reasoning_content` must contain `PRESENT:` and `COMPLETE:`. If it is generic prose with no those labels, **do not re-upload the whole set**. Use `ingest/reingest-chunk` on that one `original_video` with the same `custom_prompt`, `chunk_count: 1`.

7. **Stop.** Tell Bryce the units are ready for Scribner scan (`scan_live` / the app). Do not start reviewing.

## Verification

```sh
# after login
python3 - <<'PY'
import os, json, urllib.request
b = os.environ["INGRESS_URL"].rstrip("/")
t = os.environ["TOKEN"]
req = urllib.request.Request(b + "/api/v1/videos/explore?scope=mine&limit=100&offset=0",
                             headers={"Authorization": "Bearer " + t})
data = json.load(urllib.request.urlopen(req))
items = data.get("items") or data.get("videos") or data.get("results") or []
if isinstance(data, list):
    items = data
kit = [x for x in items if "kit-" in str(x.get("filename") or x.get("name") or "")]
print("explore_kit_parents", len(kit))
print("sample_names", [x.get("filename") or x.get("name") for x in kit[:8]])
PY
```

Pass: `explore_kit_parents` equals the number of successfully uploaded clips (or is still climbing but non-zero and dashboard `pending_index` is dropping). Fail: zero kit parents after 10 minutes → Report back `blocked`, include the upload `object_key` count and dashboard `pipeline_alignment` flags, no secret values.

## Report back

```
handoff: ingest-kits
status: done | blocked | partial
checks:
- login: pass | fail
- clips_found: <n>
- uploaded_ok: <n>
- skipped: <n> (<reasons, no paths with secrets>)
- indexed: <n>
- caption_has_PRESENT: pass | fail | not_checked
artifacts:
- object_keys: <count only>
- camera_id: kit-station-1
- tags: kit:<id>,unit:<nnn>,scribner
next: scan_live / open Scribner queue; do not re-upload
```

## Stop and escalate

Write `status: blocked` and stop if: no `/config/*.config`; login fails twice; clip dir empty; a filename's `kit_id` is not in `kits.py`; upload 413/400 on more than two files; Explore still empty of `kit-` after 10 minutes; captions lack `PRESENT:` after one re-ingest of a sample chunk. Do not invent a new prompt. Do not fall back to `scenario=general`.
