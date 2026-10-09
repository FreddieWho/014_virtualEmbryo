# T1 late-anchor + OT generative round (2026-10-08 / 10-09)

Human Team track. Validation-board work only; no official test-phase portal upload in this publication.

## What this package is

Code and docs for the T1 late-external-anchor route (GSE230531 E8.5 / E14.5 / E16.5 per-sample files only) and the round-3 OT generative displacement experiment. Binaries (`*.h5ad`, GEO MTX, `groups.npz`, label npy) stay local and are gitignored.

| Path | Role |
|---|---|
| [`scripts/vework/`](../../scripts/vework/) | Val/test recipes, local eval, backtest harness, test pipeline |
| [`scripts/vework/t1ext/`](../../scripts/vework/t1ext/) | Late-anchor + OT builders (`build_t1_late_anchor.py`, `build_t1_v51_anchor.py`, `build_t1_A_ot.py`, `otfield.py`, …) |
| [`EXTERNAL_SOURCES_T1.md`](EXTERNAL_SOURCES_T1.md) | Allowed/banned GSM list and processing notes |
| [`PROGRESS_T1_round3.md`](PROGRESS_T1_round3.md) | Round-3 build log and portal score table |
| [`MANIFEST.tsv`](MANIFEST.tsv) | Local submission manifest (paths point at `/workspace/ve/submit/`; SHA-256 of h5ad) |
| [`backtests/`](backtests/) | E8.5→E9.5 anchor/OT JSON + [`FAITHFULNESS.md`](backtests/FAITHFULNESS.md) |
| [`../TEST_PHASE_PLAN.md`](../TEST_PHASE_PLAN.md) | Test-phase #1/#2 recipe plan (opens 2026-10-20) |

## Portal scores (SERVER_SCORED; detail pages observed 2026-10-09 CST)

| version | method | board | de | dir | mmd | vario | vs prior T1 best (v0051 53.92) | verdict |
|---|---|---:|---:|---:|---:|---:|---|---|
| v0063 | late_anchor_x1 (LA1) | 53.14 | — | — | — | — | −0.78 | REJECT (submetrics not re-read) |
| v0064 | late_anchor_x2_comphalf (LA2) | 53.43 | — | — | — | — | −0.49 | REJECT (submetrics not re-read) |
| v0065 | v51_anchor_auto (LA3) | **57.99** | 51.6 | 64.0 | 61.7 | 52.8 | **+4.07** | PROMOTED (then superseded) |
| v0066 | ot_gen_v51 (ot-gen-A) | **58.89** | 49.7 | 65.9 | 65.2 | 52.3 | **+4.97** | **PROMOTED current T1 best** |
| v0067 | v51_anchor_pergroup (B) | 58.22 | 51.4 | 64.2 | 62.4 | 53.0 | +4.30 | scored backup (−0.67 vs A) |

Submission detail IDs (portal): A `39e6870fb90549e09067e7c3cff92333`; B `455eb227ed4a407382c2f18a4d2ab920`. LA1–LA3 submission IDs not re-captured in this write-up.

SHA-256 (local artifacts, see MANIFEST):

- LA1 `f876b1ef0983c635833fe7ca8713034712b777b091413196923fac5282d84282`
- LA2 `7dbc0eb05f5ab578fffe3590158bbb5b33cd1230acb26522759a1db5e217fa09`
- LA3 `79af479a577c53a182b5c74aeba5066c8b9a553e1a9570ccf4b9a15c540052d2`
- A `35fae3a797acdf44b4c6d141e1a0db65b44744ea218f96218c7909e34eda5dc1`
- B `04d73c5d2c9daab7c9fc9db3ba9543c295639f9e4415ca312511c0147adf7fe6`

Registry: [`../SERVER_SCORE_REGISTRY.md`](../SERVER_SCORE_REGISTRY.md)#t1-late-anchor-ot-score-return-20261009 ; INDEX rows in [`../../submissions/INDEX.tsv`](../../submissions/INDEX.tsv).

## External source boundary

GEO **GSE230531** only, per-sample files: GSM7226268/69 (E8.5), GSM7226272/73 (E14.5), GSM7226274/76 (E16.5 warp check). Banned-window E10.5/E12.5 samples never downloaded. See EXTERNAL_SOURCES_T1.md and SHA256SUMS.
