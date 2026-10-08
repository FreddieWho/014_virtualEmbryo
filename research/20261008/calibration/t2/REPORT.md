# T2 local underestimation audit (2026-10-08)

## Bottom line
There is no demonstrated local-score threshold guaranteeing server improvement. A conservative no-false-negative rejection margin is not identifiable. Use local evaluations to diagnose validity and compare controlled variants, not to eliminate a new method family on a scalar proxy alone.

### Historical heart-extrapolation evidence
The auditable historical set contains 16 alternatives plus one constructed baseline. These are version/path-linked historical local-score records joined to the current authoritative server index at commit `5c1bcfb625952db8c773b58ddff40cf966c5e6f9`. The 12 older local scorer JSONs and original candidate binaries are absent in this checkout; their historical local values are in a recorded calibration summary. Thus this is **not** a newly byte-verified 17-artifact calibration set. Five Route-C records additionally have exact upload-manifest hash matches to the current registry. No reconstruction was substituted for an original historical score.

The local composite is **100 times the mean of eight winsorized (±30%) relative raw-metric gains**, baseline zero. It is neither a rank composite nor a within-stage calibrated skill score nor an estimate of leaderboard points. The final E10.5 prediction was scored against an E9.5 cardiac subset, reference E8.75, scorer seed 20260916. This is a stage-shift proxy, not a genuine held-out temporal prediction. No target E10.5 data was read here.

Observed missed opportunities, relative to the baseline server score 50.53:
- v0022 late-reference: local composite **−3.183**, server **50.74 (+0.21)**. A local-negative veto kills a real better-than-baseline candidate. It also failed a local DE performance guard, demonstrating why these guards must be distinguished from true invalid-file/data-leakage gates. Relative to then-board-best v0011=50.64, its gain was only +0.10, a tie boundary, not an unambiguous incumbent promotion.
- v0011 shrink: local **+0.0297**, server **50.64 (+0.11)**. It survives a sign-only rule but fails the historical **>+1** local selection threshold.

Counterfactual filtering of the 16 submitted alternatives (two beat baseline by >0.1; the same two beat it by >0):
- Require local >0: retain 8, discard 8, retain 1/2 winners, discard 1/2; selected winner precision 1/8
- Require local >+1: retain 5, discard 11, retain 0/2 winners; selected winner precision 0/5
- Adding the recorded performance guards leaves recall unchanged; >0 selection becomes 7 with 1 winner

These are observed retrospective counts, **not** estimates of the fraction of all genuinely good candidates discarded by local research. Unsubmitted local rejects have no server outcomes. Only two observed positives, adaptive designs and shared parents make population rates or guarantees unsupported.

Historical correlation correction: the 12-record Spearman **0.53846** is reproduced. Including the five Route-C records gives tie-aware Spearman **0.11159**, not the repeatedly quoted 0.122; there is a server-score tie at 50.03. The provided historical code uses untied integer ranks, so its general approach is unsafe with ties. The 17-record Pearson is **0.09009**, and pairwise agreement is **75/135=55.6%** after excluding tied server pairs. Excluding the constructed baseline gives Spearman **0.13834**. The underlying conclusions are unchanged.

A univariate linear map from local composite to server points does not rescue calibration: candidate-wise LOOCV MAE **1.53**, RMSE **2.73** server points; leave-one-out mean-only RMSE **2.71**. Its maximum observed positive out-of-fold residual is **1.94 points**, but this is a retrospective fitting error, not an upper bound or usable safe margin. An old12 fit transferred to a different family would be especially optimistic. Row-bootstrap and binomial intervals in the machine-readable statistics are labeled naive descriptive sensitivities, not user-facing calibrated uncertainty: candidates are dependent, selected and not independent families.

High local scores are not sufficient: v0024 **+3.913 local →50.09 server (−0.44 baseline)**; all five >+1 selected historical records lose to baseline. The QTE subgroup can show a positive within-group correlation while containing zero baseline winners. Ranking a bad family is not proving a winner exists.

### Different true-temporal protocol: keep separate
The 2026-10-03 HOLDOUT10 evaluation fit E8.25_late/E8.75 and evaluated released E9.5 rows. Its objective is the median over three seeds of an equal-weight mean of five error ratios versus copy-last: `(1-DE), (1-direction), MMD, variogram, NMMD`. Lower is better; 1=copy-last; 0.90 is an arbitrary 10% improvement goal, not a server boundary.

The historical report records v0030 local **0.92868**, which misses a ≤0.90 requirement, yet server **51.12**, +0.59 versus baseline and +0.38 versus v0022. Thus a stringent progress target would reject a real promoted candidate, even though local direction was favorable. This is a missed-gain threshold example, not a negative-local/server-positive sign inversion and not a same-scale 0.59-point calibration error.

Three related variants v0032/v0034/v0033 have local error **0.9194/0.9347/0.9376** and server **51.14/51.02/50.89**, a correct ranking on just three dependent recipe variants. All fail ≤0.90 while all beat the older 50.53 baseline. Relative to incumbent v0030, none is a >0.1 promotion. This small post hoc rank agreement cannot certify a future threshold.

### Latest v0036 experiment: 42 calls are not 42 calibration pairs
`new_run_raw_audit.csv` contains every metric from 33 dev plus nine held-row score calls: 11 dev methods×3 seeds and three reserve methods×3 seeds. E9.5 is the evaluation stage in both splits, not an independent embryo. NMMD internally fixes seed 0; its repeated scores are not independent replications.

Only one final candidate was server-scored: v0036 SHA `0b89c69adff3b5cb3d86f0d8b0dbfe667f289343b0d7ac8908ca9c70ed33fc03`, server **50.47**. Its comparator named `incumbent_recipe` is an explicit reconstruction, not the original v0030 SHA `71f587ed68177b7cdbea27f27333523caa33668badc08efd782afb3d541d53a3`. Therefore **do not** join reconstructed local recipe results to historical v0030 server outcomes as a controlled pair.

The small local MMD/NMMD gains versus this reconstruction failed to establish server benefit; the final −0.65 versus historical v0030 is an observed whole-candidate result. It cannot identify the endpoint component's causal contribution, provide a false-negative rate, or estimate raw-metric↔skill numerical error. Direct MAE/RMSE/mean bias between raw local scores and server skills would be a units error.

### Other T2 boards: useful corroboration, no pooled statistics
The historical M0 appendix records embryo v0010 neighborhood-MMD **16.4% worse locally**, yet then-best server **62.29**. It also records an expression-identical coordinate-scale pair v0001→v0002 with no change in the seven tracked local metrics and roughly **+3.4 server points** (later precise v0002 registry score60.15 versus56.70, +3.45). Heart-interpolation v0013 has the worst local shape metric among 12 records yet server62.04. These published historical diagnostic examples demonstrate blind spots, but the original complete paired raw tables were not recovered, so no new per-board false-negative rate/correlation is calculated. Do not pool these protocols with heart extrapolation.

## Recommended policy for saving submissions without silently killing winners

These are recommendations for user review, not an active automatic gate or authorization for future submissions.
1. Hard rejection: invalid schema/nonfinite arrays/forbidden target use or failure to reproduce the claimed method. Separate these from performance heuristics like a DE floor or modest metric deterioration.
2. For a new family, do not reject on one local scalar; report per-channel changes versus the exact frozen parent, raw values, biological-stage shift, sample coverage and geometry separately.
3. Run target-free rolling-origin tasks wherever released stages permit. Freeze panels, row partitions, seed set, scorer revision, error directions, baselines and family selection rule before development; score held rows once after selecting. Repeated cells in one stage are not new biological replicates.
4. For a known family, require effect stability against a byte-verified parent and a negative control; use local ranking as supporting evidence only. Neither >0 nor >+1 nor error≤0.90 is validated as a universal accept/reject cutoff.
5. Future authorized calibration should sample both locally strong and locally rejected borderline representatives, spread over distinct families; otherwise false negatives remain unobservable. Lock the sample before server returns. Evaluate leave-one-family-out or forward-in-time recall and positive predictive value, using exact submission SHA, server total and all skills, local protocol and parent linkage. Do not tune a rejection margin to these same historical outcomes and present it as validated.
6. Until that prospective evidence exists, a high-recall policy is an abstention/secondary review band, not “local score below X is safely bad.” No submissions, model runs or hidden-output access were performed for this audit.

## Reproducible artifacts
- `historical_paired_audit.csv`: 17 recorded identities/local outcomes/server outcomes, provenance and limits
- `all_extrap_inclusion_audit.csv`: every indexed extrapolation candidate, inclusion/exclusion reasons
- `new_run_raw_audit.csv`: all 42 existing raw-score calls expanded by metric
- `statistics.json`, `analyze.py`: programmatic statistics and exact threshold counts
- `../provenance/SOURCE_INVENTORY.json`, `../evidence/registries/`: source hashes and focused static historical registry projections; current authoritative records remain at repository root


## Final independent-review qualifications
- v0030 HOLDOUT10 is a method-level comparison: development shifted100% of rows while the final server artifact shifted32%. Its missed0.90 target remains a useful overly strict goal example, not an exact-artifact local/server calibration pair.
- The embryo v0001→v0002 seven-flat-metrics observation must not be counted as a whole-score false negative or as maximum missed gain. Coordinates×1.305 necessarily change the eighth scale channel by log(1.305)≈0.2662 at a fixed target. Original complete local eighth-channel records/version and baseline server submetrics were not recovered. It supports an omitted-scale diagnostic blind spot only.
