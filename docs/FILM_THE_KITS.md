# How to film the kits

Agent note: give this to Bryce before they pick up a phone. Bad footage
cannot be rescued by a better prompt.

## Kits

Defined in `tools/scribner/kits.py`:

- **race-car** — 4 black wheels, 1 clear windshield, 1 red roof, 2 yellow headlights, 1 minifigure with a hat, 1 blue door
- **front-loader** — 1 yellow bucket, 4 black wheels, 1 black cabin, 1 gray roll bar, 1 yellow body, 1 minifigure

Do not add a third kit unless you also add it to `KITS` and regenerate prompts.

## Shot recipe

- Phone on a book / tripod, not handheld.
- White paper or table, one desk lamp, no mixed window glare.
- Kit **fills the frame**. Cosmos sees a handful of reduced-resolution frames.
- **No hands** in the shot (hands → UNCLEAR + occlusion HOLD).
- **4.0–4.8 seconds** so the 5s segmenter emits exactly one clip.
- 1080p 30fps. Not 4K (upload cap ~25 MB).
- Filename: `kit-<id>_unit-<number>.mp4` e.g. `kit-race-car_unit-007.mp4`.

## Take list (about 40 clips)

Per kit:

| Variant | Count | What to change |
|---------|-------|----------------|
| complete | 8–10 | Every BOM part on, two slight angles |
| missing-wheels | 4 | All wheels off |
| missing-roof or missing-bucket | 3 | The salient large part |
| missing-minifig | 2 | Empty seat |
| hidden-side | 2 | Complete kit, but the distinguishing part faces away |

Salient omissions (wheels, roof, bucket, minifig) are what AUTO_FAIL. Hidden-side is what HOLD is for.

## After filming

AirDrop / drive / USB onto a laptop, then the `ingest-kits` skill on the VM. Do not YouTube them.
