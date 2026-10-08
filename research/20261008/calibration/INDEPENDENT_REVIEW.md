# Independent calibration review

## Conclusion
No numerical local cutoff currently guarantees a server improvement, and the evidence does not identify a fixed number of server points by which local evaluation underestimates candidates. Local relative raw-metric composite, developmental source metrics, and server calibrated skill are not commensurate. Operational improvement should mean server gain over the current incumbent greater than 0.1, separated from historical gain over a baseline and from an absolute score target.

## Independently checked examples
1. T2 heart extrapolation v0022: recorded local composite -3.182563 versus baseline zero; server 50.74 versus baseline 50.53 (+0.21). The negative local proxy misses a baseline improvement. This is not a 3.39-point error. It uses E9.5 cardiac proxy versus E10.5 server target. Archived local scorer artifacts have not been independently byte-matched.
2. T2 historical set: 16 candidates plus constructed baseline. Local composite >0 retains 8 candidates and only one of the two baseline improvements; >1 retains 5 and neither improvement. Both improvements (+0.11,+0.21) exceed 0.1 relative to historical baseline, not necessarily their contemporaneous incumbent. Five score-only passes of >1 all lose to baseline; local 3.913 yields server50.09. Expanded rank correlation is 0.111588 including baseline or 0.138337 excluding it. These are descriptive counterfactual audits of already-submitted candidates, not population false-negative or success probabilities.
3. T3 WT-development siblings v57/v58/v59: local MSE .15141056/.15456203/.15633981 (lower better), server47.37/47.95/47.93. Local top1 would sacrifice .58 versus cohort best, but best only improves shared parentv48=47.93 by .02, not a meaningful promotion. All were submitted; no historical rejection is proved. Development refits differ from final artifacts.
4. T3 frozen-donor comparison: dsign05 (v85 method) beats qtl025 (v84 method) on all five reported metrics in all six pooled/cross-donor and development/historical aggregates. Server reverses: v84=49.55, v85=47.45. Choosing the proxy-dominant method could lose2.10 points and miss v84's+1.62 over v48. This is a method-level ranking reversal; reconstructed methods and WT versus hurdle carrier mismatch prevent exact artifact calibration. The six aggregates are overlapping slices of one method pair, not six independent experiments.

## Claims to avoid
- A universal '+x points' adjustment or a hard safety margin based on maximum historical error
- Calling 2.10 the amount of local score underestimation; it is an observed server opportunity loss from a hypothetical method choice
- Claiming an empirical local gate's retrospective retention fraction estimates future recall, because submission selection leaves rejected candidates without server labels
- Counting seeds, correlated variants, all pairwise comparisons, or overlapping donor slices as independent families
- Treating an in-sample/row-wise LOOCV regression or row bootstrap as out-of-family validation
- Treating failure of a proxy performance guardrail as equivalent to invalid artifacts, leakage, or a contract violation
- Describing these already-submitted counterexamples as actual unsubmitted missed winners

## Practical decision framework
1. Keep hard validity/leakage/contract checks. Separate these from soft performance evidence.
2. Compare against the correct parent/current incumbent using the same frozen local protocol; record candidate hash, method family, stage/carrier, source scope, seed and exact server outcome.
3. Use local tests to prioritize a diverse representative per mechanism, not automatically delete unseen mechanisms. Positive performance across relevant disjoint tests earns priority, not a guarantee. Reserve a limited exploratory submission opportunity for credible mechanisms whose proxy is negative or out of domain, subject to available authorized budget.
4. Keep expression and geometry diagnostics separate. A source-stage gain is weak evidence when target stage, carrier, or geometry differs.
5. With enough independent prospective families, fit parent-relative server delta from local deltas and assess leave-one-family-out prediction. Reject for predicted weakness only when a defensible upper prediction bound is at or below the promotion threshold; prioritize when a lower bound exceeds it; keep uncertain candidates in an exploration queue. Present bounds as conditional prediction statements, never certainty. Current data do not justify numeric bounds.
6. Freeze proposed gates before the next evaluation cohort and record all local rejects; evaluate a preselected representative subset across accepted/rejected strata when submission budget permits. This audits false negatives without using each server answer to retune and re-score the same validation set.

## Recommended concise Chinese explanation
现在没有“本地达到某个分数，服务器一定会好”的可靠门槛，而且不能统一说本地低估了几分。我们确实查到：T2一个候选本地相对分是-3.18，服务器反而比历史基线高0.21；T3一组方法在本地五项指标都落后，服务器却领先另一方法2.10分。但后者是跨域重建诊断，2.10是选错候选可能损失的服务器分，不是可直接加回本地的修正值。

所以本地更适合决定先试谁，现阶段不能单凭分数淘汰新机制。旧T2门槛“本地>1”在这批16个已提交候选中会放行5个，却漏掉两个超过历史基线的候选。实际做法应是先排除文件/泄漏问题，同机制挑代表，给有依据的新机制留探索机会，再用服务器反馈积累同协议、同父模型的校准数据。

## Additional example audit
- HOLDOUT10 v0030: original reports verify local normalized error0.92868 fails an aspirational0.90 goal, while server51.12 improves historical baseline by0.59 and v0022 by0.38. This is a too-stringent-goal counterexample, not a local-negative/server-positive reversal. Important: the original review says development shifts100%of rows versus32%of rows in the final server artifact, so the pairing is method-level, not identical predictions. Sources: `reports/t2_holdout_setup_20261003/REPORT.md` and `reports/t2_holdout10_score_review_20261003/REPORT.md`.
- Embryo v0001→v0002: do NOT call the reported seven unchanged local metrics plus server+3.45 a whole-score false negative or use it to inflate the maximum missed gain. The original M0 appendix reports coordinates multiplied by1.305. Current `scale_log_ratio=log(RMS_pred/RMS_true)` must consequently change by log(1.305), approximately0.2662, at fixed target. The baseline's server submetrics and complete original local eighth-channel records/version were not recovered. v0002's scale skill is91.9. This establishes a possible omitted-scale/geometry diagnostic blind spot, not that all relevant local channels failed. Sources: `reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md:147`; `third_party/veckit/common/shape_metrics.py:163–174`; server submetric registry.
