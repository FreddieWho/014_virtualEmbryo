# Independent audit of final T3 optimization

2026-10-08. Scope: one newly authorized optimization attempt, no portal or repository mutation. This audit is active; no final candidate has yet been approved.

## Immutable baseline and portable replay

Restored v87 packet at `/workspace/shared/t3_v87_restored` inspected. Independent execution of `inference/replay.py` in the available t3venv passes with exact donor indices and expression SHA256 `2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98`. The 7449 by 500 prediction needs no source KO or hidden target file for replay.

Actual immutable v87 H5AD SHA256: `b0cfdf5e870f762185efd9f2bdc803cab26ecb0a54e18a870286d41165ce5fc9`.
Actual retained v84 H5AD SHA256: `d7af1cef61e032210f9af502684a8b8a95f5a79bef79f79e15634daa556f6230`.

## Early design review

Builder proposes baseline, empirical-positive residual retention, and the same with WT-state-conditioned activation ranks. Three-arm emitter-only family is preferable to adding response-dose or median-response sweeps because it isolates a plausible quantile-emission defect. No performance conclusion yet.

Required checks sent before freezing: specify newly activated/deactivated observations separately from retained positives; preserve exact zero-response behavior; verify rank monotonicity and sparse-gene fallback; fit zero-tie associations on WT only and avoid trivial self-gene PCA reconstruction. New activation association is observational, not causal lineage evidence.

The current model already balances same-sex WT embryos and equally weights KO embryos, so merely adding sex balance is not a new method. Its cv & kv support rule conflates positive-magnitude estimability with detection-change support; this is an identified limitation, not automatically permission to add a fourth family.

## Evaluation requirements

All actual serialized/reloaded matrices must be assessed. Final mean-log X, not latent or count-space means, controls the first three public metrics. Both float64 and scorer-native float32 means matter because tiny ranking ties can shift. Panel closure can alter every gene's final response. CSS is a fractional gene-pair variogram and is not equivalent to covariance matching. Report zeros, full panel expm1 row mass, response amplitude and covariance/variogram changes without guarantees.

Source validation remains adaptively inspected leave-intervention-out data. All seven allowed source inputs and reference/scorer/code hashes must be verified. Any fit including source outcomes must exclude the queried perturbation. Mab is a secondary adaptive cross-platform calibration, not a pristine validation or Gata4 forecast. Target leaderboard observations can guide ordinary candidate selection but must not be inverted to recover hidden outcomes.

Pending: restored source hashes, frozen design, new code review/tests, actual source/Mab results, actual candidate structural audit and independent final portable replay.

## Final independent release audit, 11:54 UTC

**RELEASE PASS for parent-authorized conditional-only v0088.** No portal action performed by this reviewer. This is a completed engineering/scientific-evidence audit of the frozen artifact, not a claim of leaderboard improvement.

### Actual source selection

Independently recomputed every skill and weighted total in all 84 source rows (7 genotypes, 4 arms, 3 metric seeds), then applied the frozen eligibility and ranking rule. Conditional-only is the sole eligible arm: mean local gain +0.3252895167, wins 7/7. Residual-only loses −0.4458131948 with 1/7 wins; combined loses −0.0890986736 with 4/7 wins. No switching to the combined arm despite its slightly better secondary Mab result. All seven baseline seed-0 raw component metrics exactly equal immutable v87 mean_combined records, including unranked MSE.

Conditional source component skill differences: DE 0; direction −0.009395; severity −0.026160; MMD +2.728320; variogram +0.084749. Thus the small source gain is predominantly distributional, not improved response gene ranking. Technical ceilings reuse the held-out evaluation embryos while excluding truth cells from ceiling samples. This is adaptive genotype-heldout source validation, not pristine confirmation or independent embryo-generalization evidence.

Independently checked all 13 restored source files (4,362,519,944 bytes), binding their exact hashes to original immutable source manifests. Checked all 17 rebuilt panel files; all nine raw panels match original frozen hashes, and eight normalized panels preserve the recorded annotated whitelist joins. Source reconstruction retains the known 690 absent WT barcodes. No new source was admitted.

### Actual secondary and target evidence

All 12 Mab calibration rows independently recompute exactly (maximum weighted-total discrepancy 2.85e-14). Conditional Mab mean 57.4787718534 versus v87 57.2517988044, a small +0.2269730490. It remains a secondary, historically adaptive cross-platform diagnostic, not a Gata4 forecast.

Actual selected Gata conditional output: response L2 4.2355872275 versus v87 4.2462046009 (ratio .99749956); mean-log residual L2 .03962938, maximum absolute residual .00714333; response-rank Spearman .99981117. Detection exactly unchanged at .1108427977. Final expm1 row-mass maximum deviation from 10000 is .00382144. Hence approximate amplitude retention is empirically supported; exact pseudobulk/first-three-score invariance is NOT asserted. Substantial joint covariance rearrangement remains an observational WT association hypothesis, not causal transport.

### Exact deliverable checks

Final file: `/workspace/shared/t3_v88_optimization_20261008/v0088/t3_gata4__condhurdle__v0088.h5ad`

H5AD SHA256: `d7944880d8f55974946dad4b2c22879582c03bce547ead312921b0fc39bdddc7`
Expression SHA256: `7cfe4e0cfcfe1a76c003e25eed7d3fab58868f1d6d5dd7cb6b0ab14b3dddf77c`

ZIP: `/workspace/shared/t3_v88_optimization_20261008/v0088/er4__t3__upload__20261008.zip`
ZIP SHA256: `9918ce8b6e80736deb4290523621be13edd97fc62cb87dd96d9d657a023f3635`

Independent full checks PASS: 7449×500 ordered panel; finite nonnegative float32 X; unique row names; exact selected frozen expression; unchanged v87 parent hash; exact parent obs/var/geometry; source permit and protocol/emitter/selection/frozen-prediction hashes; locked local contract; serialization; single ZIP member and matching hash/CRC. Portable inference was independently executed after finalization, exactly reproducing expression and donor indices using only the hash-bound model, prior and untreated carrier, without source or target KO files.

Evidence files in this audit directory: `EMITTER_TESTS.json`, `RESTORED_SOURCE_HASH_AUDIT.json`, `DEPLOYMENT_AUDIT.json`, `MAB_SCORE_AUDIT.json`, `FINAL_ARTIFACT_AUDIT.json`. Independent checker scripts are retained. Source conditional-only choice is final for this small-family experiment; no expanded search is requested or implied. Parent owns the one newly authorized submission and any resulting score adjudication.
