# Provided videos (Pack C) — no filming required

Scribner’s judged corpus is **Pack C: Warehouse Safety** from the official
[Architecture Reference](https://github.com/vast-data/vast-builders-challenge/blob/main/ARCHITECTURE_REFERENCE.md#video-corpus-already-indexed).

| Field | Value |
|-------|--------|
| Source | SDG warehouse RGB |
| Location | `warehouse3` |
| `camera_id` | `sdg_warehouse_cam-2` |
| Indexed | ~178 short ceiling / aisle clips |
| Kit id | `warehouse-aisle` |
| Example query | *Forklift approaching a person in a warehouse aisle* |

The archive is **pre-ingested**. Live path is **re-ingest** (`ingest/reingest-videos` /
`reingest-chunk`). Do not re-upload the corpus. Do not pull YouTube.

Phone filming is **not** required for the judged product. Optional extra
LEGO kits (`race-car`, `front-loader`) if Bryce later wants them:

- Filename `kit-<kit_id>_unit-<nnn>.mp4`
- 4.0–4.8s, fill the frame, white paper, no hands
- Skill still `ingest-kits` (upload path)

## Completeness checklist (Pack C)

A complete (safe) aisle has:

- a clear travel lane
- person-vehicle separation
- a pallet-free walkway
- an unobstructed aisle path

Salient misses (person-vehicle gap, pallet in walkway, blocked lane) are
what AUTO_FAIL. Unclear distance is what HOLD is for.

## After the corpus is re-ingested

Captions must contain `PRESENT:` and `COMPLETE:`. Then `POST /api/scan`
on the Scribner app.

Skill: `.cursor/skills/ingest-kits/SKILL.md`.
