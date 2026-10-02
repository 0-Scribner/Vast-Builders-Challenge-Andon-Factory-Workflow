# Handoff: re-ingest provided Pack C clips

Give this file to the workshop-VM Cursor agent. It re-ingests the official
Pack C warehouse archive so Scribner can scan PATH_CLEAR / NEAR_MISS captions.
Clips never go in git. Do not re-upload the corpus.

## Receiver

Workshop VM Cursor agent. CWD = this Scribner repo (`AGENTS.md` at root). All
commands run in the **browser VM terminal**, not Bryce's laptop. Prefer this
repo's `tools/scribner` for prompts and the challenge `ingest/reingest-videos`
skill for the HTTP shape.

## Done when

- [ ] Pack C (`sdg_warehouse_cam-2`) has been re-ingested with
      `prompt_for_kit('warehouse-aisle')` so captions contain `PATH_CLEAR:` and
      `NEAR_MISS:`.
- [ ] Each prompt used is ≤800 characters. `scenario` omitted.
- [ ] Explore lists warehouse parents; at least one caption has the schema fields.
- [ ] A filled Report back block is shown to Bryce.
- Out of scope: running the Scribner gate, reviewing units, retraining,
  deploying `/app`, committing video files, filming LEGO.

## Context

Scribner parses Cosmos captions with `tools/scribner/inspection.py`. That
parser only works if ingest used the path-safety custom prompt from
`tools/scribner/kits.py` (`prompt_for_kit`). Default `scenario=warehouse`
produces unusable captions. Known corpus scene ids: `warehouse-aisle`,
`person-near-vehicle`. Plan B LEGO kits are **not** on this branch.
Live path: Detector → Reasoner → Embedder → VastDB writer. Segmenter already
ran on the provided packs.

## Never

- Do not ingest YouTube or other internet video.
- Do not `git add` clips, zips, or anything under `~/kit-clips`.
- Do not print `/config` values, JWTs, passwords, or `Bearer` tokens.
  `env | cut -d= -f1 | sort` only.
- Do not send `scenario` on the same request as `custom_prompt`.
- Do not re-upload the provided corpus. Re-ingest existing segments.
- Do not have a second teammate re-ingest the same camera at the same time.
- Do not rebuild DataEngine or use Docker.

## Inputs

| Name | Where | Required |
|------|--------|----------|
| Team config | exactly one `/config/*.config` | yes |
| Path-safety prompt | `prompt_for_kit('warehouse-aisle')` | yes |
| Camera | `sdg_warehouse_cam-2` | yes |

## Procedure

1. **Confirm environment.**

```sh
mapfile -t TEAM_CONFIGS < <(find /config -maxdepth 1 -type f -name '*.config' | sort)
(( ${#TEAM_CONFIGS[@]} == 1 )) || { echo "BLOCKED: expected exactly one /config/*.config"; exit 1; }
set -a && source "${TEAM_CONFIGS[0]}" && set +a
BACKEND="$INGRESS_URL"
```

2. **Login.** Do not echo `$TOKEN`.

```sh
TOKEN=$(curl -s -X POST "$BACKEND/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
test -n "$TOKEN" || { echo "BLOCKED: login failed"; exit 1; }
```

3. **Build the Pack C prompt in Python.** Confirm `len(prompt) <= 800`.

```sh
PYTHONPATH=tools/scribner python3 -c "from kits import prompt_for_kit; p=prompt_for_kit('warehouse-aisle'); print(len(p)); print(p)"
```

4. **Re-ingest one Pack C clip first** via `ingest/reingest-videos` /
   `POST /api/v1/dashboard/reingest` with that `custom_prompt`,
   `camera_id=sdg_warehouse_cam-2`. Wait until Explore shows `PATH_CLEAR:`.
   Then continue the camera. Do not stampede the shared GPU queue.

5. **Spot-check captions.** `GET /api/v1/videos/metadata?source=<preview_source>`.
   `reasoning_content` must contain `PATH_CLEAR:` and `NEAR_MISS:`. If it is
   generic prose, re-ingest that one `original_video` again. Do not fall
   back to `scenario=general`.

6. **Stop.** Tell Bryce the units are ready for Scribner scan. Do not start reviewing.

## Verification

```sh
curl -s "$BACKEND/api/v1/videos/explore?scope=all&limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

Pass: at least one `sdg_warehouse_cam-2` parent with a `PATH_CLEAR:` caption.
Fail: zero warehouse parents after 10 minutes → Report back `blocked`.

## Report back

```
handoff: ingest-kits
status: done | blocked | partial
checks:
- login: pass | fail
- prompt_chars: <n>
- reingest_jobs: <n>
- caption_has_PATH_CLEAR: pass | fail | not_checked
artifacts:
- camera_id: sdg_warehouse_cam-2
- scene_id: warehouse-aisle
next: scan_live / open Scribner queue; do not re-upload the corpus
```

## Stop and escalate

Write `status: blocked` and stop if: no `/config/*.config`; login fails twice;
Explore has no warehouse camera; captions lack `PATH_CLEAR:` after one sample
re-ingest. Do not invent a new prompt. Do not fall back to `scenario=general`.
