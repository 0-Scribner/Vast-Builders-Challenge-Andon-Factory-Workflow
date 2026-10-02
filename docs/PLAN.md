# Primary vs Plan B

| Line | Branch | Product | Corpus | Operator labels | Gate |
|------|--------|---------|--------|-----------------|------|
| **Primary** (this tree) | `cursor/warehouse-primary-72e3` | `warehouse-near-miss` | Official corpus (I-24, PIE, neighborhood, Pack C warehouse, smart spaces) | CLEAR / UNSAFE (A/O, C/U) | AUTO_CLEAR / AUTO_ALERT / HOLD |
| **Plan B** | `cursor/plan-b-lego-completeness-72e3` | `kit-completeness` | Same Pack C clips parsed as a completeness BOM, plus optional own LEGO | COMPLETE / INCOMPLETE (C/I) | AUTO_PASS / AUTO_FAIL / HOLD |

Do not merge Plan B BOMs (`race-car`, `front-loader`, PRESENT/MISSING) onto Primary. If you need completeness, check out Plan B.

Primary identity (also `/health` and the operator footer):

- payoff query: *person close to a moving vehicle*
- stack line: `VAST · NVIDIA Cosmos · CoreWeave / W&B · Cursor`
- operator surface: 安灯 andon on the official corpus clip (`/api/andon`, `tools/scribner/andon.py`)
- cameras: `i24_cam-1` · `pie_cam-3` · `neighborhood_cam-1` · `sdg_warehouse_cam-2` · `smartspace_cam-1` (`tools/scribner/corpus.py`)
