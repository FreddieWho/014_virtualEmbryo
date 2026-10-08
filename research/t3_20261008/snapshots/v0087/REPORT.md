# State response implementation: measured-Mab control and cross-KO bridge

2026-10-08. This file preserves the initial measured-Mab control. All later seven-KO, hurdle, cross-platform and candidate work is complete in FINAL_REPORT.md. One finalizedv0087 exists; this worker did not submit or publish it. `blocks_submission:false`.

## Concrete result

Implemented WT-only common-state alignment, separate composition/within-state emitters, normalized observation output, and actual serialized/reloaded matrix metrics. Two alternating-section Mab21l2 splits and disjoint WT training/evaluation cells. Fourteen new 7,449×500 H5ADs pass local structure, normalization, split-disjointness and immutable-input hash checks. Six supplementary control matrices were independently serialized/reloaded. These are diagnostic artifacts, not submission candidates.

Raw full-panel averages across two technical folds:

| Emitter | DCS | Absolute log severity | MMD | Variogram | Pseudobulk MSE |
|---|---:|---:|---:|---:|---:|
| Literal unmodified WT | −0.0266 | 6.9078 | .01494 | .01942 | .06467 |
| WT with Mab zero + panel closure | −0.0186 | 5.0787 | .01488 | .01884 | .06270 |
| Global measured mean shift | .9353 | .2544 | .00634 | .04578 | .00776 |
| Composition only | .2958 | 1.8799 | .01028 | .01542 | .05119 |
| State measured mean shift | .8905 | .3347 | .00543 | .03703 | .01058 |
| Within-state empirical KO, WT proportions | .9160 | .1601 | .00294 | .00291 | .00669 |
| Combined empirical KO, KO proportions | .9778 | .0152 | .00021 | .00075 | .00128 |
| Unconditional training-KO resampling | .9748 | .0121 | .00071 | .00090 | .00145 |
| Gene-shuffled state response | .0340 | 2.1387 | .01385 | .08070 | .08310 |
| Historical adult-source anchored emitter | .1216 | 6.9078 | .02346 | .01955 | .06989 |

These are vendored raw metrics, not calibrated leaderboard skills. No portal score is estimated.

The state mean-response model does NOT beat the global mean-response control on response direction/severity/MSE. Its distribution terms improve relative to global shift, but both continuous log shifts distort detection and joint expression compared with empirical KO whole-cell emission. The almost-perfect combined result is the expected same-perturbation empirical technical ceiling: it approximately re-samples the discovery KO distribution. An unconditional discovery-KO resampler does essentially the same. This is not evidence of unseen-gene prediction or a superior state architecture.

The within-joint model versus composition-only confirms that access to measured within-state expression matters for reproducing this observed experiment. It does not establish causal within-state effects: atlas states, residual subtypes, donor/batch, and tissue differences remain confounded.

## Observation and alignment

Official E9.5 WT, released KO and E8.75 WT all have expm1 row totals ~10000. Their respective whole-panel detection fractions are .07796, .09289 and .10498. Every new modeled output closes to panel10000 after setting Mab21l2 to zero; this knockout-transcript assumption is not a guarantee from genotype. The separately retained literal-WT and raw-KO controls quantify that choice. Raw versus zero-closed empirical KO ceilings are nearly equal here.

PCA12/kmeans32 is fitted only on training WT cells and one fixed 250-gene half. KO assignment uses those genes; metrics also report the complementary 250 genes. Response templates for those complementary genes DO use discovery KO cells. Thus the complement tests alignment-held-out genes, not response-supervision-held-out genes. No KO labels or harmonized KO PCA are used. KO duplicate observation names are handled by row position.

WT-training 95th percentile distance thresholds classify about 13.5–19.3% of E8.75 WT as outside E9.5 atlas support, depending on alignment half. This is an untreated-state mismatch warning, not a calibrated uncertainty probability. All 32 states have at least20 training WT and KO cells in these splits. Genes/cells/sections are technical splits; one KO slide/batch is not biological replication.

Per-entry zero-mask differences in CHECKS.json compare output and carrier row positions. For whole-cell resampling/composition, rows are unrelated cells; these numbers are population diagnostics, NOT inferred individual-cell on/off transitions.

## Artifacts and provenance

- Frozen design: PROTOCOL.md, input/code/scorer/protocol SHA256: INPUT_HASHES.json
- Actual implementation: run.py; main raw metrics: metrics.csv
- Audit-added controls: supplemental_controls.py, supplemental_metrics.csv (added after first fold; no model selection)
- Split/model coefficients: model_fold0.npz and model_fold1.npz; alignment/support: ALIGNMENT.json
- Observation units: OBSERVATION.json; serialization hashes: CHECKS.json
- Validation: validate.py, VALIDATION.json, validation.log
- H5AD names fold{0,1}_{model}.h5ad and supp_fold{0,1}_{control}.h5ad

No existing scored artifact was changed. Candidate ID/parent/submission hash: not applicable to these measured-Mab diagnostics. Existing best remains a coordinator decision.

## Ongoing strict cross-KO implementation

crossko.py now exposes WT-only atlas fitting, measured per-sample state response construction, independent gene-prior prediction (fixed ridge / nearest / identity-free mean), composition and within-state marginal-transport ablations, and normalized output. Held-out intervention records are excluded before any donor response/support fitting; equal declared sample units do not become biological replicates without metadata. Missing independent query gene priors stop inference. Stable log-count closure avoids expm1 overflow. Quantile-rank emission can activate zeros but preserves joint dependence only approximately; it is distinct from empirical joint KO resampling above.

Synthetic held-out-KO poisoning leaves fitted parameters and emitted outputs identical; finite/closure/locked-zero checks and missing-prior refusal pass. Synthetic checks establish engineering behavior only. Incoming admitted Dnmt3a/Kmt2a/Kdm2b E8.5 data are being streamed to panel counts; barcoded genotype/cell metadata must identify true cells and outcomes before valid source-domain LOPO. No Gata4 transfer choice can be supported by the single-Mab experiment alone.
