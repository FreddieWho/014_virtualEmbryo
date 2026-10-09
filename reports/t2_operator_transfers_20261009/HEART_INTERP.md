> Historical pre-submission report. The experiment has since reached a terminal score; see HEART_INTERP_SCORE_RETURN.json and REPORT.md for the final outcome. Paths below refer to the original executed run tree.

# Heart interpolation v0025 handoff

**Decision: ready for the one authorized mechanism test after parent review. Unsubmitted and unscored.**

## Frozen identity

- Candidate: `T2_heart_val_interp/v0025_h_heart_copula`
- File: `/workspace/shared/t2_operator_transfers_20261009/heart_interp/final/t2_hrt_int__heart_copula__v0025.h5ad`
- SHA256: `efb0c7298be54493d3d540257daf1f9c9664d8e64fe14bba8dd349669ea977c2`
- Shape: 5,872 cells × exact 500-gene heart panel; range 1,000–17,616; contract PASS
- Parent: historic H1, portal model `bridgeC2-r2`, submission `d0fd25a74fed4aeabaa4e9fe128bfa74`, confirmed by the parent portal worker
- Exact parent SHA256: `7cc2e31445613a7e9e13525ea3b3ce8bf386855f8df0b70d6ba47f1ae2a23a37`
- Parent identity restoration: current recipe has one later-added `carrier` provenance field. Removing only that field reproduces the entire historical H1 hash. This is an exact-file verification, not a presumed array match
- New version v0025 was absent from the current INDEX/history for this board; coordinator owns final registry integration

## Mechanism and legal input

Reuse the exact embryo-v0021 operator implementation, **never its learned B or embryo expression**. Rank-Gaussian-transform 83,542 released heart cells from E8.25_late and E8.75 on the exact500 panel, then fit LedoitWolf precision. Shrinkage is 0.0013137380209128804. Within each stored parent state, average each gene's original and conditional rank at fixed weight0.5, and assign that gene's original sorted values to the resulting rank order. No parameter search.

Official train files, full hashes, legal stage roles and source snapshots are in `SOURCE_INTAKE.json` and `final/RESULT.json`. E9.5 is used only as a fitting endpoint of the local released-stage fold. No protected E8.5/E10.5/E12.5 data, external measured data, or pretrained coefficients are used.

## Preserved and changed

- Exact: per-state and global per-gene value multiset, every zero/positive value, obs and var metadata/order, all coordinate rows, and stored state-label counts
- Changed: 15.8962% of expression entries, joint dependence, per-cell expression-coordinate associations, per-cell library size, and potentially classifier-derived cell-state mass
- Per-cell panel-library proxy `sum(expm1(X))` changes in every row; median absolute relative change 13.3393%,95th percentile 43.9659%
- Fixed stored cell-type counts do not imply fixed server-inferred composition

The final diagnostic-only classifier reached its300iteration limit. Its soft-mass and hard-label change estimates are approximate diagnostics, not exact mechanism evidence or server predictions. The candidate was frozen before this classifier ran and does not depend on it.

## Full matched local evaluation

Strict fold: build parent and fit B on all released E8.25_late+E9.5; only then expose released E8.75 for evaluation. Full panel and full5,872-cell predictions; all eight public T2 metrics; seeds0/1/2. The parent control is identical apart from the operator. The shuffled control simultaneously permutes B's two gene axes with fixed seed20261009, preserving coefficient values/eigenspectrum while disrupting gene identity.

| Arm | Mean local total | MMD skill | Neighborhood-MMD skill | Variogram skill |
|---|---:|---:|---:|---:|
| parent | 53.2045 | 51.6725 | 53.3423 | 51.5072 |
| heart_copula | 54.4572 | 57.1618 | 55.2230 | 51.0987 |
| gene_shuffle_control | 52.7827 | 51.1504 | 51.9904 | 51.4517 |

Copula total gain: **+1.2527 mean**, with all three seed gains +1.2409 to +1.2594. Raw neighborhood MMD improves6.68–7.21%; shuffled control worsens5.22–5.48%. Variogram is modestly worse. DE/direction and geometry metric values match in this local evaluation; that does not guarantee identical server submetrics.

This is one held-out released stage with a different bracket from E8.5. It supports testing the mechanism, not a claim of server improvement or biological causality. No outcome-driven retuning was performed.

## Engineering checks and reproduction

- Contract: PASS, finite and nonnegative, exact500 gene content/order, unique obs, valid spatial3D, legal cell count
- Full parent and shuffle controls: built and evaluated
- Unit tests:3/3 PASS
- Fresh independent process: refitted B bit-exact, candidate X array-exact, coordinates/obs/var exact, all marginal checks PASS (`REPLAY_AUDIT.json`)
- Numerical libraries: one thread throughout; recorded in `ENVIRONMENT.json` and run JSON
- Scripts: `run_transfer.py`, `replay_audit.py`, `test_transfer.py`; commands in `README.md`
- Whole output matrix and arrays are reproducible in the locked environment. Different numerical reductions can change discrete ranks; no cross-thread or cross-environment identity claim
- No shared repository edits, upload, push, or new server score

Scientific limitation: exploratory local evidence; `blocks_submission: false`. Parent owns candidate registration, the sole official upload, and score recording.
