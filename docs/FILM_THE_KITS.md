# Provided videos (Pack C) — no filming required

Scribner’s judged corpus is **Pack C: Warehouse Safety** from the official
[Architecture Reference](https://github.com/vast-data/vast-builders-challenge/blob/main/ARCHITECTURE_REFERENCE.md#video-corpus-already-indexed).

| Field | Value |
|-------|--------|
| Source | SDG warehouse RGB |
| Location | `warehouse3` |
| `camera_id` | `sdg_warehouse_cam-2` |
| Indexed | ~178 short ceiling / aisle clips |
| Scene id | `warehouse-aisle` |
| Payoff query | *person close to a moving vehicle* |
| Example query | *Forklift approaching a person in a warehouse aisle* |

The archive is **pre-ingested**. Live path is **re-ingest** (`ingest/reingest-videos` /
`reingest-chunk`). Do not re-upload the corpus. Do not pull YouTube.

Phone filming is **not** required for the judged product. LEGO completeness
(`race-car` / `front-loader`) is **Plan B** on branch
`cursor/plan-b-lego-completeness-72e3` — do not mix those BOMs into Primary.

## Path-safety checklist (Pack C)

A CLEAR aisle has:

- PATH_CLEAR YES
- NEAR_MISS NO
- no named hazard (forklift-near-person, pallet-in-walkway, person-in-aisle, blocked-path)
- HIGH confidence, no UNCLEAR fields

Salient UNSAFE (person close to a moving forklift, pallet in walkway) is
what AUTO_ALERT. Unclear distance is what HOLD is for. False CLEAR is illegal.

## After the corpus is re-ingested

Captions must contain `PATH_CLEAR:` and `NEAR_MISS:`. Then `POST /api/scan`
on the Scribner app.

Skill: `.cursor/skills/ingest-kits/SKILL.md` (alias `ingest-warehouse`).
