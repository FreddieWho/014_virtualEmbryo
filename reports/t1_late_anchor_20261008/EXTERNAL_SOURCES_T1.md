# External data used for T1 (late-anchor route) — recorded 2026-10-08

Source: **GEO GSE230531**, "Single-cell RNA sequencing of murine hearts for studying the development of the cardiac
conduction system" (Scientific Data 2023, doi:10.1038/s41597-023-02333-6). 10x Chromium scRNA-seq, CellRanger 3.1
raw (unfiltered) matrices, wild-type C57BL/6J. GEO public data, no use restrictions; article open access.

Downloaded **per-sample files only** (never `GSE230531_RAW.tar`, which also contains banned E10.5/E12.5 samples):

| GSM | GEO title | tissue | stage (GEO "developmental stage") | matrix size | cells kept | use |
|---|---|---|---|---|---|---|
| GSM7226268 | embryo, replicate 1 [E8_5_1] | embryo | E8_5 | 50.4 MB (**truncated gzip at source**, 12.6M of 27.1M entries read; complete barcodes kept) | 2,924 | within-batch early baseline |
| GSM7226269 | embryo, replicate 1 [E8_5_2] | embryo | E8_5 | 110.4 MB | 5,776 | within-batch early baseline |
| GSM7226272 | heart, replicate 4 [E14_5_1] | heart | E14_5 | 85.1 MB | 4,966 | late anchor |
| GSM7226273 | heart, replicate 4 [E14_5_2] | heart | E14_5 | 66.4 MB | 4,358 | late anchor |
| GSM7226274 | heart, replicate 5 [E16_5_1_7] | heart | E16_5 | 97.9 MB | 4,960 | time-warp check only |
| GSM7226276 | heart, replicate 5 [E16_5_2] | heart | E16_5 | 78.4 MB | 4,818 | time-warp check only |

Total downloaded ≈ 0.49 GB (plus ~6 MB of GSE193346 metadata CSVs from earlier scouting, not used in any model).
- **Not downloaded:** GSM7226279/80 (E10.5) and GSM7226270/1 (E12.5) are in the banned window. P3 is not needed.
- No other external data, no pre-trained models.
- The stage metadata was verified from each GSM's GEO record (`ext/meta/GSM*.soft.txt`). sha256 of every file is in `ext/GSE230531/SHA256SUMS`.
- Processing (`vework/t1ext/ext_prep.py`):
  - Cell calling: UMI ≥1500, genes ≥700, mito ≤25%.
  - Normalisation: log1p(CP10k over all features), the same scheme as the released T1 h5ad.
  - Genes: symbol match to the T1 panel (25,943/32,285 present). Absent genes get no anchor.
