# T2 heart extrapolation: continuous state temporal flow
Frozen before target evaluation, 2026-10-08. Local predictions are not leaderboard score forecasts.

## Data boundary
Official heart released stages E8.25_late, E8.75, E9.5 only. Development predictor sees E8.25_late and E8.75; E9.5 is opened solely by evaluator after predictions are saved. Final predictor can use all three released stages; no E10.5/E12.5 or disallowed external measurements. Generic sequence-derived GO memberships, if independently audited, may supply functional topology but no experimental response weights or expression data.

## Mechanism and fixed comparisons
The new mechanism is a label-independent continuous temporal vector field. Joint source-only latent microstates are matched by reciprocal, uncertainty-weighted expression neighborhoods. Pooled source PCA and independently defined GO-module coordinates are compared as one predefined method ablation. Low-support correspondences shrink to zero. A smooth velocity field is evaluated on later-stage cells, then advanced according to observed and forecast time intervals. All rows retain their source spatial coordinates; transformed expression is projected back to each source row's implied library. This changes cell-specific trajectories and correlations rather than scanning scalar doses or remapping named cell types.

One fixed 64-component PCA, 128 microstates per observed stage, 8-neighbor smooth prediction, reciprocal correspondence and source-only bandwidth. No parameter grid, no response to hidden targets, no geometry tuning. Baselines: copy last and incumbent recipe (shared-state median difference times 0.9 plus row-library conservation). Preserve a source-only replayable row sample at final generation.

## Validation
Full 500-gene emitted AnnData predictions; official locked veckit full T2 scorer at seeds 20261003, 20261011, 20261019. E9.5 is partitioned once by celltype-stratified split into development and reserve using fixed seed 20261008. Reserve is evaluated once after shortlist decision and cannot trigger parameter changes. Historical reserve identity is absent and therefore this is not a biologically independent or untouched validation set.

Primary local comparison is median neighborhood MMD and global MMD relative to incumbent-recipe control, with DE/direction and variogram reported and guardrails: all finite, nonnegative, exact ordered panel, source coordinates unchanged, row libraries preserved within 1e-4 relative, no >5% worsening both MMD measures, no >10% worsening variogram. Do not rank by old eight-channel composite. A local gain is only method-screening evidence because cross-family proxy validity is weak. If neither new mechanism is credible, report that honestly before recommending one formal attempt. No hidden score can be claimed before portal return.

## Reproducibility
Keep immutable input hashes, model parameters, raw official scorer output, source-row identity ledger, full-model replay comparison, code hash, package versions, topology provenance and disclosure. Final version assigned by coordinator; do not edit shared registry or T1/T3 files.

### Pre-run independent-review clarification (12:07 UTC; no fit/evaluation yet)
Primary transport is restricted to exactly shared celltype strata; unmatched named states remain exactly copied, avoiding the already-failed crosswalk/coverage expansion. Within each shared stratum, continuous microstates replace a single median shift, capturing heterogeneous temporal movement. 128 microstates is a per-stage overall upper target allocated by square-root stratum size, capped by available cells, not 128 per celltype. Reciprocity reliability compares round-trip microstate error to within-stage spacing. Functional modules change matching geometry only; actual velocity always uses released expression. The PCA-only arm is the predefined topology ablation. Neighborhood MMD internally uses seed zero, so three scorer runs are not independent NMMD replicates. Variogram is gene-pair expression structure, not a spatial variogram.
