# T1 v0096: restore the observed RNA normalization

Status: submitted and terminal-scored; promoted over v0094. Parent reference is the exact scored v0094 file, not a reconstruction of historical v0092.

## Fixed intervention

For each row, invert log1p in float64, multiply all observed gene values by10000 divided by that row's full-panel sum, take log1p, and cast once to float32. No fitting, clipping, pseudocount, randomization, cell resampling or parameter search. All32,285 official genes are retained.

The complete official E8.5/E9.5 audit covers33,844 rows. All implied RNA library masses equal10,000 within0.000782. The exact v0094 parent instead ranges8,040–23,490. The metric implementation consumes floating log-expression without automatically fixing this scale. This candidate tests measurement consistency; it makes no new biological mechanism claim.

## Checks

- Four unit tests pass
- Independent direct dense-float64 replay checks165,234,630 entries with zero mismatches
- All22,535,804 zero/nonzero positions are unchanged; within-row gene ordering has zero violations
- Every new row mass equals10,000 within0.0006753
- Full-population gene-variance sum is0.930386 times the parent; no zero rows or collapse
- Official E8.5 control normalization and known-scale corruption/repair both have maximum float32 error0.0
- Parent-bound repository validator passes panel order, row identity, normalization marker, finite/nonnegative values, protected metadata and exact serialization roundtrip
- Cross-cell gene ranks and per-gene marginals are deliberately not invariants

Relative to the released E9.5 source,389 of10,333 genes with absolute mean change at least0.01 switch direction. This quantifies a collateral effect; it does not establish which future-stage directions are correct.

## Source-only distribution diagnostic

Across three fixed seeds, MMD to released E9.5 worsens by about10.3%; full-space energy improves by about4%; variogram improves in two seeds and is essentially flat in the third. These comparisons use all32,285 genes but the wrong developmental target for prospective validation. They are a health/context check, not a forecast of the leaderboard or a reason to infer hidden target properties.

## Artifact revision and disclosure

The initially frozen r1 file lacked the project-local normalization marker. It is preserved unchanged and superseded-unsubmitted. r2 supplies that marker and revision provenance; its complete expression is identical to r1. Only r2 is eligible for release. File hashes belong in the canonical submission index; V0096_ARTIFACT_REVISIONS.json records the administrative revision chain.

The new H5AD replaces stale inherited source metadata with an explicit complete ledger: official E8.5/E9.5 inputs; GSE230531 E8.5/E14.5 direct inherited field sources; GSE230531 E16.5 historical temporal-warp/alternative-anchor diagnostics; and GSM5820434 E9.5 historical rejected donor/source-diagnostic use. This correct disclosure applies only to the new artifact. Earlier scored bytes and their unresolved disclosure history are not retroactively changed.

## Reproduce

Use the pinned runtime in configs/t1_quota_20261009/requirements_runtime.txt. Run scripts/t1_quota_20261009/build_cp10k.py with the exact v0094 parent, the official T1 panel, paired v0051 donor-state labels, configs/t1_quota_20261009/cp10k_v0096_r2.json, and a fresh output directory. The builder rejects parent hash drift and any existing destination. Parameter-free expression replay is independent of the donor labels; those labels are used only for statewise diagnostics.

Source-only diagnostic scripts take explicit released official input paths. Never point them at a protected validation/test target.

## Terminal result

The official public API confirms60.7928 and all four ranked components improve. This is a configuration-level result for parameter-free CP10k restoration; it does not identify hidden target properties or validate a new biological mechanism. The full score and submission evidence belong in the canonical registry. [Submission](https://virtualembryo.ai/challenge/account/submissions/24e762950f3a42a89499b59ec02b5f73). The source-reference MMD deterioration did not predict the server outcome, reinforcing the limited role of these source assays.
