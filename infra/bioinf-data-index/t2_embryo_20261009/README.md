# External data handoff — T2 embryo interpolation — 2026-10-09

## Ready now

GSE65924 (Peng et al., Dev Cell 2016; DOI 10.1016/j.devcel.2016.02.020) supplies three independently processed E7.0 epiblast embryos, 122 laser-microdissected pools (~20 cells/pool), 23,361 genes. It is **not** a 3D single-cell atlas. The readout is FPKM, not counts and not the challenge's expression scale. All spatial labels used are experimental region/serial-section labels rather than learned annotations.

- `EXTERNAL_INPUT_MANIFEST.json`: sources, intake decision, exact hashes, preprocessing and limitations
- `gse65924_e70_pool_fpkm.npz`: X (pools × genes), genes, sample_ids
- `gse65924_e70_pool_metadata.tsv`: observed regions, sections and derived ordinal coding
- `gse65924_e70_gene_spatial_rank_prior.tsv`: independent within-embryo rank correlations with AP category and PD section order; sign consistency and conservative weights
- `prepare_gse65924.py`: reproducible processing from the three downloaded GEO matrices
- `GSM1611141_metadata.txt`: source processing and E7.0 staging evidence
- `GSE65924_series_metadata.txt`: source region definitions, single-stage design and L/R mirror warning
- `GEO_reuse_policy_evidence.md`: source repository's explicit unrestricted data-use policy, verified from primary NCBI search result; direct-page fetch was CAPTCHA-blocked; no special source restriction found. Do not relabel this license CC0/CC-BY. Cite original study + accession + GEO.

AP coding (-1 anterior, +1 posterior, 0 lateral) and normalized PD section index are ordinal region descriptors, **not physical 3D coordinates**. The deposited L/R labels are mirror-inverted; anatomical L/R is explicitly corrected in a separate column. There are no cell-type labels, pretrained embeddings, imputation or cross-stage normalization in this handoff.

The repository's previous heart 500-gene panel has 482 exact symbol matches; this is NOT yet verified to equal the current embryo panel. A panel-specific output is clearly named `gse65924_rank_prior_shared_previous_heart_panel.tsv`. Avoid speculative alias replacement.

## Model use and required controls

Transfer relative spatial-expression dependence only. Build gene programs from genes with consistent AP/PD correlations across the three independent embryos, or fit a low-dimensional region covariance model using within-platform/within-gene ranks. Anchor axes using released official training stages. Restrict transfer to compatible epiblast-like support identified from official training data; do not impose epiblast organization on whole-embryo cells. Preserve official expression marginal distributions and scale.

Two scientifically distinct hypotheses are possible, but both must have independent controls:
1. Add region-program compatibility to endpoint transport cost (geometry–expression coupling).
2. Preserve geometry and expression marginals, changing only which expression vectors occupy compatible local positions (assignment-only coupling test).

A matched zero-external control must use the same base model, seeds and postprocessing. A negative control must shuffle spatial-region assignments (or gene-program weights) while preserving FPKM/gene marginals and solver settings. Validate program reproducibility leave-one-external-embryo-out, and evaluate any possible official training-replicate holdout. Neither local agreement nor a leaderboard score proves external biological information gain. These pools cannot directly justify target surface/volume, target occupancy, true cell count or a precise 3D cavity.

## Current rules audited

https://virtualembryo.ai/challenge/rules §10 and https://virtualembryo.ai/challenge/faq, read live 2026-10-09. For T2 embryo interpolation the explicit prohibited external interval is strictly between E7.25 and E8.0. The endpoints are permitted. The heart interval and extrapolation exclusions are not interchangeable with this embryo setting. Measured protected data are prohibited through pretraining as well; source disclosure is mandatory. Public multi-stage resources require removal before training. No labels/target properties may be recovered from score returns. Later source/model changes require re-review.

The live rules page requires two distinct evidence types including trajectory for Agent Team submissions; FAQ still says one. Apply the rules page rather than the stale FAQ minimum.

## Quarantine / excluded

GSE171588 E6.75_2/E7.0_2/E7.25_2 stage-specific non-log FPKM files were downloaded for intake. They are **REVIEW_HOLD / DO NOT TRAIN**: GSM processing metadata mentions ComBat, with insufficient precision about which exported file and which batches/stages. Their nonnegative unlogged values suggest earlier FPKM output, but that is not proof of no cross-stage processing. No protected-stage file was downloaded.

Harland 2025 E7.25 seqFISH is not cleared: joint atlas embeddings, imputed transcriptomes and annotations involve E7.5, and even segmentation network retraining provenance spans imaged embryos. Do not use a stage-filtered integrated atlas. A raw allowed-stage-only extraction with stage-independent segmentation and verified data license would need separate review.

MOSTA starts much later and would be a poor targeted fix for gastrulation geometry; no protected-stage download was attempted.

## Repository integration

All new data and notes are owned in this independent folder. Before a candidate is delivered, coordinator should integrate this manifest under `infra/bioinf-data-index/`, append the central INDEX/SUMMARY, and disclose exact used files in the submission method summary. Shared coordinator files were deliberately not edited concurrently. No submission or push performed here.

## Complementary single-cell source (ready)

GSE278981 / GSM8559288 is a standalone E7.25 normal ARC mouse 10x Chromium channel: 6,173 cells × 32,285 features. Only the three PE725 filtered feature/barcode matrix files were fetched. The same GEO series contains E7.5, but none of that sample was downloaded. Nonnegative integer counts verified, no learned metadata/embedding/annotation transferred. Source processing cites Aryamanesh2022 rather than naming an exact alignment version; the sample-specific CellRanger filenames and count values are verified, while exact original alignment reproducibility remains limited.

- `GSM8559288_INPUT_MANIFEST.json`: provenance, hashes and usage limits
- `gsm8559288_e725_counts_csr.npz`: scipy.sparse.load_npz, cells × features
- `gsm8559288_e725_features.tsv`: aligned feature IDs, symbols, type
- `gsm8559288_e725_cell_qc.tsv`: aligned barcodes and per-cell count/gene/mitochondrial metrics
- `prepare_gsm8559288.py`: conversion and validation
- `gsm8559288_e725_previous_panel_rank_covariance.npz`: optional reference-panel ranks/covariance; see matching README for exact fixed QC

This source is complementary to the Geo-seq pools: use its cell-state support or rank-covariance to avoid unrealistic expression mixtures under spatial transport. The expression marginals and coordinates should still come from official training endpoints. It cannot independently determine spatial occupancy, and one channel cannot calibrate the target's cell-type proportions. A second candidate could add this covariance/manifold regularizer to the external-spatial candidate, paired with local no-scRNA and shuffled-gene controls; the added effect is then distinguishable from the first spatial prior. If local ablation cannot separate meaningful signal from batch/solver changes, preserve the second external submission rather than force it.
