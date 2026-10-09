> Historical pre-submission report. The experiment has since reached a terminal score; see EMBRYO_SCORE_RETURN.json and REPORT.md for the final outcome. Paths below refer to the original executed run tree.

# Embryo source-library transfer, v0023

Frozen candidate: target/t2_emb_int__e3_libself__v0023.h5ad. Identity and complete local contract are in target/HANDOFF.json.

Parent is byte-exact E3 (SHA e93d56f2130297f7c5b256e3e26fc072b8913766772b3ffcb2634f7a3fdbfdae, historical UI 62.89), not original v0014. Candidate SHA 8c34d6592337df9fa5ccd9d84678831f98bdba9a0aacd654bb2f38cf2a912ce3. Neither v21 copula nor external B is used.

Single change: after the existing C2 shrunk mean bridge, restore each touched row to its own bridge-input XB count-space sum. This is exactly the extrapolation library-preserving rule, applied only to bridge shared-state rows. Orphans, coordinates, row identities/order, labels and expression zero mask match parent. It does not preserve gene marginals, mean bridge target, or frozen classifier type mass. No new endpoint or endpoint quantile target is used.

The bridge input already contains the official prior-stage pseudobulk shift. Restoring raw E7.25 totals would undo a second mechanism; we deliberately do not. Raw source library is ~10000, whereas actual bridge-input library median is 24470.83 (2.447x raw). Candidate library relative error is 4.47e-7 in stored float32 and 1.07e-15 before conversion. 3349 of 5000 rows are eligible; 62.14% expression entries change.

Reproducibility: build.py starts single-thread numerical libraries, calls unchanged source recipe for parent, instruments only source capture and post-shift restoration. Operator-off is exact X. Separate process replay reproduces parent and candidate file hashes. check.py verifies source mapping and invariants. No historic files were edited.

Released-stage local diagnostic E6.75+E8.0→E7.25 uses a plain carrier because exact E3 needs an unavailable fourth earlier released stage. Three-seed local skill medians are recorded below, not official scores or cross-mechanism gates. Within-state shuffled-library control is nearly degenerate on normalized raw holdout source (all ~10000), and must not be interpreted as evidence against row-specific coupling. It is nondegenerate on E3: 61.84% entries differ; median wrong-source library error 21.75%.

- parent: median local TOTAL 51.154639
- source_library: median local TOTAL 50.738275
- within_state_library_shuffle: median local TOTAL 50.738275

The holdout modestly worsens overall while variogram improves; this is a one-switch mechanism probe with no promise of improvement. Full eight metric results are in holdout/LOCAL_SCORES.json. Variogram is gene-pair expression structure, not spatial lag. Scientific mechanism inference is limited; blocks_submission:false.

Run: /workspace/shared/t2venv/bin/python build.py --out NEW_DIRECTORY; add --holdout for local diagnostic. Consumer runtime data path and recipe hash are explicit in handoff. Re-run check.py after target/replay outputs exist. Official released embryo inputs are hash-locked in handoff. No uploads or GitHub push performed.

For relocation, set T2_TRANSFER_REPO to the checked-out source commit and T2_EMBRYO_DATA to the hash-verified released input directory; defaults retain this run paths.
