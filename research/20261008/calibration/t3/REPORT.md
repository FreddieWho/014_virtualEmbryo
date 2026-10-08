# T3: local underestimation and missed-winner audit

## Bottom line

There is a concrete **ranking false-negative risk of 2.10 server points** in the available T3 evidence: a local source-dominance gate would select v0085 over v0084, yet v0084 scored49.55 versus v0085's47.45. This would miss a +1.62 promotion over incumbent v0048=47.93. This is **not** a numerical server-minus-local bias, and v0084 was actually submitted. It is a retrospective test of a hypothetical selection rule.

There is **no established local score threshold that guarantees a server improvement**, nor an empirically justified negative margin that safely rejects every candidate. Unsubmitted rejects have unknown server outcomes. No same-target, same-reference calibrated local/official total pairs were recovered, so a point-valued absolute underestimation distribution and an overall false-negative rate cannot be estimated honestly.

## Strongest reversal, independently reproducible

The fixed-donor reevaluation holds the original q0.25/g0.5 parameters fixed, uses original17 training perturbations, excludes the query from training, and selects its donor from training identities. It evaluates development17 and historical9, pooled and both cross-sample directions. All **five actual raw score components favor dsign05 (v0085) over qtl025 (v0084) in all6 strata**. These6 strata are overlapping evaluations of one candidate pair, not6 independent server tests.

Pooled historical9:

| Metric | v0084 qtl025 | v0085 dsign05 | Preferred |
|---|---:|---:|---|
| DE, higher | .089373435 | .231149098 | v0085 |
| Direction, higher | .199536867 | .378775428 | v0085 |
| Absolute log severity error, lower | 3.027770153 | 2.216664625 | v0085 |
| MMD, lower | .053347777 | .050420335 | v0085 |
| Variogram, lower | .005889221 | .005372555 | v0085 |
| Server score | 49.55 | 47.45 | v0084 |

Local pooled historical MSE also favors v0085 (.00673766 versus .00748479); v0084's error is about11.09% higher. All6 separate strata are retained in dominance_reversals.csv and all156 corresponding raw per-perturbation rows in fixed_donor_raw_rows.csv. Source means independently recomputed from390 raw rows match the published summary to8.9e-16. The recovered recheck_frozen_donors.py SHA256 matches the frozen protocol.

Important scope limitations:
- The source evaluation uses WT control as recipient; actual target predictions use the reconstructed hurdle carrier. Identical operator/parameters do not mean identical complete target prediction pipeline
- Source and target also differ in perturbation, stage/context and modality; historical holdouts had already been used adaptively
- Original ignored v83–85 artifacts were unavailable and were reconstructed under the same IDs by explicit instruction. Registered scored v84 SHA is d7af1cef61e032210f9af502684a8b8a95f5a79bef79f79e15634daa556f6230; v85 is8cfbc8950216f8848969f26bb1973c9c52b8efd4c85c49ab15c17c7b16246418. Old hashes are not silently treated as scored bytes
- The original20261007 v84 selection did **not** reject q0.25: its lane-specific weighted rank2.158627 beat identity3.284902. That adaptive four-arm ranking and this later fixed-donor comparison answer different questions

Exact primary sources:
- t3_delivery/package/reports/frozen_donors/{FROZEN_PROTOCOL.json,METRICS.tsv,SUMMARY.tsv}
- t3cpu/experiments/cpu_20261008/recheck_frozen_donors.py and reproduce_backlog.py
- t3registry_v88/submissions/INDEX.tsv and reports/SERVER_SCORE_REGISTRY.md
- Actual submissions: [account-scoped portal link omitted; see authoritative repository registry]; v85 submission ID is in the authoritative registry

## Other quantified selection observations

WT observational five-select cohort: v57/v58/v59 local development group-MSE .151410562/.154562035/.156339810, while server47.37/47.95/47.93. A global local-top1 rule would choose v57 and lose .58 against the cohort best. Top2 recovers the numerical best. But v58 exceeds the actual shared parentv48 by only .02, within the .1 tie band; this is **not a missed promotion**. The real selection rule had family quotas and submitted all3, so there was no historical false rejection. Unsubmitted r1active/r5local cannot be called wins or losses.

v53 pooled sourceMSE .00505101 is worse than matched scalar-shrink comparatorv46 .00503888 (+.2407%), while server47.66 versus47.65. That negative-to-positive sign reversal is only+.01, not a promotion. v44 local worse than mean-response baseline is also server worse than the corresponding mean baselinev34 (47.47 versus47.53); its+.52 versus WT carrierv9 is a different comparator and must not be mislabeled a paired reversal.

The threshold/top-K tables calculate strict numerical winners and >.1, >.5 and >1 promotion-like thresholds separately. Recall values apply only to these scored cohorts and hypothetical gates. They do not estimate recall across unsubmitted candidates.

## Latest family: encouraging relative agreement, not guarantee

v88 versusv87: source7-LOKO local custom-skill delta +.325289517, released-Mab custom-skill delta +.226973049, server delta+.27. All7 source identities improve in the primary selection total. This is one matched candidate-parent improvement, not multiple independent validations because of3 seeds/7 genotypes/2local tests. Source residual and both arms remain unsubmitted, so source-top1 global winner recall is unobservable.

v87 custom Mab57.2518 versus server53.42 and v88 Mab57.4788 versus server53.69 are cross-target, differently calibrated totals. They look optimistic numerically, not locally underestimated, but subtracting them does not produce valid absolute forecast residuals. v87's Mab advantage over historical adult is+7.68476 while actual Gata advantage overv84 is+3.87; the adult adapter is not established as an exact v84 reproduction, so even that comparison is family-level rather than exact-artifact calibration.

## Why high local results cannot guarantee a win

Direct matched WT proxy counterexample: v54 local groupMSE .185274647 improves fromH .190683629 (~2.84%), but server47.75 loses .18 againstv48=47.93. Stronger local group fit does not prove intervention prediction.

A locally preferred v57 has better development and audit WT-group MSE thanH, but server loses .56 againstv48. The source-dominance preference v85 has an even more dramatic reversed ordering againstv84, as above.

Historical source metrics are classified rather than pooled: v80 uses held-query observed switches (oracle leakage); v83 outer-fold reliability included held-query responses; program-swap/NMF sign semantics are invalid; several source operators substitute proxies for the actual hurdle carrier/gate. Weighted ranks depend on each lane's candidate set and are not official skill points. Bad local positives are not evidence for a universal negative offset.

## Practical decision guidance

1. Use current-family local validation for **prioritization**, after final emitter/normalization, with the same candidate-parent comparison, all5 weighted score components, held-whole-intervention isolation and stable improvement across contexts
2. Do not reject a structurally new route solely because unrelated sourceMSE, historical donor dominance, WT observational proxy, or a cross-target custom total is lower. Those gates have demonstrated ordering failures
3. Separate hard engineering invalidity from uncertain efficacy. A broken contract or leaked validation invalidates that evidence; it does not establish the unknown server outcome of a valid final artifact
4. Preserve a small explicitly authorized exploration share for genuinely different mechanisms when conserving submissions. The data do not identify its optimal size, and this report does not authorize more submissions
5. A safe numerical no-false-negative rejection cutoff is **not identified**. The observed2.10 regret is a documented lower bound on possible loss from this particular local dominance rule, not an upper bound on future misses

## Coverage and deliverables

The latest local registry snapshot contains87 candidate rows,78 with scores. This audit extracts106 local records covering24 distinct scored candidates plus explicit unsubmitted arms. The publication inventory retains only candidates and parents used in this audit, with original hashes. The 87/78 full historical coverage counts are retained in evidence/registries/t3_coverage.json; uncovered candidates are not counted as failed or passed local tests. This is an evidence extraction from available cached records, not a claim that every historical experiment has a complete metric receipt. No models trained, target truth read, portal queried, or submissions made.

- paired_local_server.csv: metric/protocol/reference/parent/hash/source classifications
- fixed_donor_summary.csv, fixed_donor_raw_rows.csv, dominance_reversals.csv: central reversal proof
- topk_counterfactual.csv: threshold-specific known-cohort regret and recall
- candidate_inventory.csv: focused static candidate/parent projection; full historical coverage metadata in ../evidence/registries/t3_coverage.json
- computed_summary.json, verification.json, source_hashes.json, analyze.py: reproducible calculations
