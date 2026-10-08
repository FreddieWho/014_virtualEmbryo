> Final disposition at10:42UTC: all-supported seven-KO hurdle-v2 is the recommended single experimental candidate if the last upload is used. Source genotype-heldout evidence and custom released-Mab weighted calibration support review; no official Gata4 score or70-point prediction. Both Gata matrices passed independent full structural checks. Detailed final recommendation and limitations are at the end; earlier sections preserve the chronological audit.

# Active T3 transfer-validation audit

2026-10-08. Independent read-only implementation review; this isolated report is the only owned output. No candidate, source admission, portal action, model fit or expression-matrix computation performed.

## Validation hierarchy and minimum useful evidence

1. **Contract/observation check.** Identical ordered 500 genes, finite nonnegative log-expression, legal cell count and required finite spatial columns; serialize/reload actual emitted matrices. Released expm1 row sums of 10,000 are an observation convention and potential model constraint, not automatically a requirement proved by the basic nonnegative-X validator. Report row-closure effects on mean response and all metrics. Full-panel closure must occur before full-panel evaluation.
2. **Same-perturbation sample prediction.** Freeze state representation on discovery WT only; assign discovery/evaluation cells without evaluation-outcome-driven tuning. Fit released Mab response on discovery KO cells and predict disjoint KO-cell distribution. This is legitimate supervised same-Mab technical-sample prediction. A discovery-KO prototype containing every gene does not invalidate that claim, but makes a held-out-response-gene claim false for those measured genes.
3. **Cross-gene representation capacity.** WT state construction, feature scaling and KO assignment/weight fitting use discovery genes only. Held-out WT prototype means may provide the output dictionary, but no held-out KO expression may enter predictions. A discovered KO within-state residual on the held-out genes is direct supervision, even from disjoint KO cells. Report the composition oracle separately from such within-state arms. Full-panel emission cannot mix measured held-out KO genes into normalization and remain gene-held-out.
4. **Unseen perturbation transfer.** Requires withholding the entire perturbation response from every learned statistic, donor choice, uncertainty estimate, embedding trained on outcomes, hyperparameter selection and emitter. Existing 26 approved adult-fibroblast perturbation groups can test this source-domain claim using outer held-out perturbations and inner tuning; group by biological donor or perturbation family where metadata genuinely supports it. Repeatedly used historical test groups are validation, not pristine final tests. No adult-fibroblast result alone establishes embryo transfer.
5. **Embryo unseen-gene evidence.** With only released Mab as matched spatial KO, a clean prospective bridge is to train the genotype-to-response mechanism only on independent approved perturbations and evaluate its frozen Mab prediction without using Mab outcomes for fitting or tuning. It remains one cross-domain perturbation, but is more relevant than reusing Mab as both teacher and validation target. If Mab identity/embedding is absent or source states have no overlap, explicitly report that limitation rather than silently replace the test.

## Required ablations and honest interpretation

Use identity; composition-only; pooled within-state shift; state-specific within-state shift; their combination; an appropriately randomized negative control. Evaluate the same serialized 500-gene emitter for all deployment comparisons. Report raw DES, DCS, severity slope and R²/gate, response MSE and distribution metrics, without converting local ranks to official skill or predicting a leaderboard total. A gene-panel subset score is a diagnostic, not the official full-panel score.

State matching should use untreated information where possible. Shared frozen state IDs avoid comparing incompatible WT22 and KO15 annotations as if biologically homologous. WT-only alignment is still an assumption: a strongly shifted KO cell may be reassigned to the wrong WT state; confidence/support and unassigned fractions should be shown. KO-defined novel templates are legitimate for supervised representation capacity but cannot be assumed available for an unseen gene.

Composition and within-state response are not uniquely causal from the unpaired population. For a fixed state assignment, show the exact additive decomposition, residual error, and shrinkage/control baseline. Report state-specific improvement over pooled response: otherwise the state-specific model may merely repackage the same shared global KO/batch signal. WT-vs-WT cell splits check numerical noise and overfit only. Sections/cell halves are not independent biological replicates, and provided metadata cannot separate Mab treatment from all batch/donor effects.

## Minimum decision before a Gata4 hypothesis candidate

- Exact source provenance, allowed scope and no forbidden source ingestion
- State/emitter implementation passes independent code inspection and actual matrix checks
- Improvement is named at its actual level (representation capacity, technical prediction, source-domain transfer, or independent cross-domain transfer)
- A predeclared genotype-to-response rule explains how Gata4 differs from Mab; copying Mab fitted proportions/residuals is labelled a biological hypothesis, never validated target transfer
- Candidate changes contain real response evidence beyond observation closure alone, and unknown source support is disclosed
- Last portal attempt stays reserved unless the parent/user elects to spend it on a clearly labelled hypothesis

Scientific uncertainty is blocks_submission: false. These are evidence standards for recommendation, not a ban on legal competition candidate generation and not a demand for unattainable causal proof.

## Pending review

Builder and observation worker have been asked for frozen plans/code and results. Final judgment awaits the actual new prototype; this report is preliminary.

## Implementation review at 10:04 UTC

Read frozen `t3_state_response_20261008/PROTOCOL.md` and `run.py`. The current design correctly names complementary genes as held out from alignment, not from response supervision. WT PCA/k-means fit only discovery WT cells and selected feature genes; KO fitting and evaluation sections are disjoint. No same-Mab held-out-cell outcome leakage identified in the inspected implementation. It produces serialized/reloaded full-panel matrices and computes raw source metrics without skill calibration. This is valid technical generalization of a supervised released-perturbation model, subject to batch confounding and assumptions below.

Requested corrections before interpreting results:

- `identity` zeroes Mab21l2 and recloses panel totals, so it is not literal WT identity. Add unchanged WT baseline; forcing transcript zero is an intervention assumption, not guaranteed by knockout genotype.
- `combined_joint` draws states at discovery-KO proportions and then discovery-KO whole cells in those states. Except fallback/sampling error, that reproduces the training KO empirical distribution. A high holdout score is a technical ceiling and does not establish that state conditioning adds predictive value. An unconditional empirical KO draw makes the ceiling explicit.
- The useful learned comparison is state-specific shift versus pooled global shift under the same emission. Composition-only and within-joint help descriptive decomposition but do not establish causal mechanisms.
- Zero-to-positive/positive-to-zero counts compare unrelated sampled cells to a fixed base array in composition/empirical arms. These are rowwise array differences, not inferred biological transitions.

No instruction to stop the legal experiment; no repository edits or candidate operations performed.

## Observed results and observation-module review at 10:05 UTC

The primary run completed 14 matrices/two technical folds. Reading `metrics.csv` and averaging the full-panel rows gives:

| Model | raw DES | raw DCS | abs severity log | MMD | variogram | response MSE |
|---|---:|---:|---:|---:|---:|---:|
| global shift | .836353 | .935335 | .254368 | .006336 | .045782 | .007760 |
| state shift | .822464 | .890460 | .334701 | .005431 | .037034 | .010584 |
| within-state empirical KO | .836957 | .915959 | .160088 | .002939 | .002911 | .006685 |
| joint empirical KO ceiling | .943237 | .977797 | .015209 | .000215 | .000753 | .001281 |
| composition | .269022 | .295758 | 1.879893 | .010279 | .015419 | .051190 |
| historical adult anchored | .014191 | .121597 | 6.907755 | .023455 | .019551 | .069894 |

State-specific mean shifts do **not** beat pooled mean shifts on the response group; they improve two distribution metrics. Empirical KO resampling preserves covariance and zero patterns unavailable from mean shifts, but is supervised on this same perturbation. Neither result establishes target-gene transfer. Supplementary unchanged-WT/empirical-KO controls remain pending.

Read `t3_observation_reset/observation.py`, `recompute_source.py`, `test_observation.py`, and `SUMMARY.json`; independently reran all eight unit tests with one BLAS thread: PASS. Source reprocessing enforces condition allowlist, two specified samples and exact sanitized barcode order; raw-panel normalization is asserted numerically equivalent to reclosure of prior panel expression. Emitter implements stable relative fold-change then panel closure, maintains structural zeros and makes transcript zero-lock optional/explicit. It cannot activate previously zero genes, which is documented.

Important inference restriction: `ResponseObservation.response` support requires treated detection counts, so its support mask is valid for training/source characterization. It must not be reused as held-out-target support in transfer validation. Freeze support from permitted training groups and query WT only.

Mean cross-sample supported rank is .548 for original mean-log responses, .518 after panel closure, .429 for the new CLR-like response. The changed observation scale is correctly named relative panel composition, but these measurements do not show improved response reliability. No independent-animal replication is established. Normalization repairs an intended representation; it is not by itself new biological supervision or evidence of a leaderboard gain.

## Supplement and disposition at 10:08 UTC

Reviewed `supplemental_controls.py` and `supplemental_metrics.csv`. Unconditional raw discovery-KO resampling achieves full-panel mean DCS .974835, versus .977797 for `combined_joint`. This confirms the technical-ceiling interpretation and removes the apparent evidence for state-model sophistication. Unchanged WT DCS is −.02658 with severity sentinel abs 6.9078; gene-zero/closure identity is a distinct intervention assumption, DCS −.01858 and severity abs 5.0787.

**Disposition of the completed Mab prototype:** accepted as a technically valid same-perturbation representation/prediction diagnostic, subject to stated sample/batch limitations. State-specific mean shifts do not improve the response group over global shifts. Empirical KO distributions show the emitter can preserve useful joint behavior when the actual intervention distribution is supplied. These findings do not validate unseen-Gata4 response or warrant a 70-point claim. Recommend preserve final portal budget; blocks_submission:false.

A separate `crossko.py` interface now exists with synthetic held-out-KO poisoning tests. Code inspection confirms held-out records are excluded before response/support fitting. It uses independent identity priors supplied by the caller and offers ridge, nearest and identity-free mean controls. This is implementation readiness only, not new biological validation. Before real runs, advised stable log-count closure instead of unbounded `expm1` on ridge-extrapolated output, and strict panel-unit input checks. Genuine embryo metadata is required to call its weighting equal-embryo; sample-unit weighting can still be performed and explicitly labelled technical when embryo identifiers are absent. Caller must keep the atlas WT-only and identity prior independent of held-out outcomes.

Task: independent active implementation/transfer audit. Candidate ID/parent/artifact/SHA: not applicable; no Gata4 candidate created. Changed path: this isolated audit report only. Observation tests independently rerun: 8 PASS at inspected revision; worker subsequently reports expanded 10 PASS suite. Primary and supplementary model metrics/code read directly. No portal action, forbidden-data access, model fitting or heavy computation. Scientific transfer gap remains; no compliance or authorization blocker found in the inspected bounded work.

# Reopened real-source audit, 10:12 UTC

New evidence changes the feasibility conclusion: GSE137337 selected Dnmt3a/Kmt2a/Kdm2b E8.5 conditions now have published SNP-assigned individual embryo metadata, alongside GSE122187 E8.5 WT. This allows biological-embryo analysis that was impossible for released Mab technical sections. Parent requested continued audit through actual crossKO results and candidate evidence.

Read `t3_developmental_sources/{SOURCE_REVIEW.json,TASK_DATA_PERMIT.json,export_annotations.py}`, selected annotation TSVs, source preprocessing code/receipts and expanded GO provenance. Independently verified source-review hash binding and all four selected annotation TSV hashes. Annotation barcodes are unique within condition; embryo assignments have no sex conflicts. There are WT10, Dnmt3a10, Kmt2a11, Kdm2b10 embryos; identities are condition-prefixed to avoid conflating repeated embryo labels. Library a/b remains technical, not the biological unit.

The permit is specific to these three zygotic KO conditions, E8.5 WT, and specified WT state metadata, with sample allowlists and hashes. Its review records positive context/phenotype evidence, allowed uses and GEO data-policy basis; no broad approval of other source conditions. Expanded GO528×128 is refitted in one shared outcome-independent basis; query identities may be included because no KO measurements enter this prior. Do not splice these rows into the prior frozen basis.

Early corrections sent before fitting:

- WT preprocessing finds498 panel feature symbols; KO sources find500. Determine missing/duplicate canonical symbols and mask unavailable control features. Otherwise absent assay features become false KO-upregulated responses.
- WT sex mix is2male/8female; Dnmt3a9male/1female, Kmt2a8male/3female, Kdm2b6male/4female. Use sex-matched WT contrasts and equal-embryo reporting, with only two male WT embryos explicitly limiting certainty.
- Published42 states may derive from all-genotype outcomes. Use WT-only frozen state learner for strict heldout-genotype prediction; published labels may describe coverage but not silently supply outcome-trained alignment.
- Published composition-adjusted stage is post-treatment. Kdm2b developmental delay is potentially genuine response and must not be matched away by conditioning on that adjusted stage.

Actual annotated-matrix merge and real heldout-genotype runner/results remain pending.

## Real crossKO results, independently reviewed 10:17 UTC

Read `CROSSKO_PROTOCOL.md`, `run_crossko.py`, revised `crossko.py`, `preprocess_wt_idmatch.py`, and completed `crossko_results/{MERGE_RECEIPT.json,FROZEN.json,metrics.csv,summary.csv,SELECTION.json}`.

The real runner excludes every embryo of the query genotype before response/support fitting. The atlas is WT-only. Expanded GO preprocessing for ridge is training-identity-only after the independently built ontology embedding. Source responses are sex-matched to WT and averaged equally across KO embryos. Chronological E8.5 is retained; adjusted phenotype stage is not used for matching. Evaluator query-KO data enter metrics and an explicitly named separate known-response oracle, not any deployable model. Stable closure and input-unit guards requested earlier are implemented.

Main genotype-heldout results (mean across three queries):

| Route | raw DCS | mean MSE | WT-MSE wins | frozen selection |
|---|---:|---:|---:|---|
| identity-free mean, within | .423949 | .044204 | not selection-eligible | control |
| identity-free mean, combined | .458393 | .046790 | not selection-eligible | control |
| nearest, within | .235508 | .073476 | 1/3 | FAIL |
| nearest, combined | .286410 | .082094 | 1/3 | FAIL |
| ridge, within | .402648 | .049315 | 2/3 | FAIL |
| ridge, combined | .426476 | .052777 | 2/3 | FAIL |
| WT identity | .021157 | .056308 | baseline | baseline |
| known-response discovery-embryo oracle | .851888 | .003518 | supervised ceiling | ineligible |

All identity-conditioned methods fail the predeclared requirement to beat identity-free mean DCS. This is real, useful source-domain heldout-genotype evidence; it does not validate the proposed GO identity mapping. Shared KO-versus-WT cohort differences can contribute to the identity-free response. No Gata4 candidate was built and the frozen criterion must not be loosened after seeing these results.

Independent serialized-output spotchecks: all24 model H5ADs have shape7449×500; first/last20 rows each are finite, nonnegative and expm1-close to10000 within0.01. This is a bounded spotcheck, not independent full-matrix recomputation. Local response-test matrices are not submission artifacts and do not establish the required spatial submission contract.

WT feature mismatch was addressed by exact Ensembl-ID mapping (including renamed symbols); revised receipt reports500 matches. Asked for unique-position completeness and duplicate-map assertions, since raw matched-feature count alone cannot prove500 unique genes. Merge receipts show allKO barcodes matched exactly; WT21825/22515 matched,690 missing (3.06%). Requested WT attrition diagnostics by embryo/sex/published state without using those labels to fit models.

Remaining statistical limitations: WT cells are pooled within sex rather than equal-weighted by WT embryo; only2maleWT exist. Per-embryo metric file compares each single embryo to mixed-sex population prediction/reference, so those rows are not clean sex-controlled individual predictions. The pooled primary score is appropriately sex-matched in construction; the per-embryo output must be relabelled or supplemented. Only3 perturbation identities were tested, and the same test results select among methods; no independent confirmatory set or target-domain claim. These issues do not rescue the failed identity criterion and do not imply that novel source acquisition was wasted.

Current recommendation: keep final portal attempt reserved, retain this tested implementation and negative result, and do not call the genotype prior validated. Scientific gap remains blocks_submission:false. Awaiting builder's final mapping/attrition status; no portal or repository mutations.

## Competition-scope clarification, 10:18 UTC

Parent clarified the next adaptive proposal: a generic developmental-KO mean may be a legitimate competition candidate even though identity-conditioned models did not outperform it. The failed3KO frozen selection remains unchanged, but it is not a universal submission prohibition. A separate prospectively declared expanded7KO/balanced-control experiment can test whether this generic response improves actual heldout prediction, with platform support and amplitude checks. Identity-specific improvement is required only for an identity-specific claim. No need for causal proof or method novelty to justify a useful prediction. This adaptive step must be named as such rather than retrospectively presented as an untouched confirmatory test. Review remains active; final portal decision stays with parent/user.

## Seven-KO prospective audit, 10:21 UTC

Read expanded condition review/permit, `CROSSKO7_PROTOCOL.md` and `run_crossko7.py` before seven-KO metrics were available. New scoped additions are Dnmt1, Dnmt3b, Ehmt2/G9a and Kmt2b, with explicit single-gene chronological E8.5 restrictions. The review addresses distinct developmental mechanisms and potential later cardiac phenotypes rather than automatically declaring every related gene a phenocopy. All remain epigenetic regulators, limiting target-functional-class extrapolation.

The adaptive generic-mean eligibility rule is frozen separately: positive median DCS, MSE better than WT on at least4/7 identities, and severity better on at least4/7; select eligible average DCS then MSE. This supports exploratory artifact review only, never a score guarantee or automatic upload. Within-source training and metrics now equal-weight WT embryos within sex. No published all-genotype state labels are used in the learned atlas; adjusted developmental age stays descriptive.

**Prespecified technical diagnostic sent to builder before seven-KO outcome inspection:** Dnmt3b uses10xv2 like WT, with comparable sex composition6F/2M versus8F/2M. Many other source KOs usev3. Report Dnmt3b separately and stratify other results by chemistry; improvement confined tov3 with failure on Dnmt3b would support a technical-shift concern and must not be averaged away. It would not prove chemistry is the only cause, since Dnmt3b is also a different biological intervention.

Resolved initial3KO checks: `FEATURE_MAP_AUDIT.json` reports exactly500 unique panel positions for WT and sharedKO, no missing or duplicate mappings. WT attrition is present across every embryo (retention95.70%–98.20%), rather than total loss of one donor; phenotype/state-specific retention is separately recorded. Added sex-matched equal-WT-embryo sensitivity emits individual embryos from their own sex-matched carriers, replacing the misleading mixed-sex per-embryo interpretation. These are post hoc robustness checks, not retroactively frozen selection data.

## Seven-KO real results, 10:27 UTC

Completed `crossko7_results/{metrics.csv,summary.csv,SELECTION.json,MERGE_RECEIPT.json}` independently read. The adaptive generic developmental-response candidate now has actual genotype-heldout evidence: mean_combined average raw DCS .576175, mean response MSE .026827 versus WT .048570 (44.77% reduction of mean MSE), MSE improvements6/7 and severity improvements7/7. It is the best eligible model under the new frozen criterion. Mean_within, ridge and nearest also meet the permissive eligibility rule but are weaker by selected DCS. Identity-conditioned priors still do not improve on generic mean.

The predeclared chemistry-matched Dnmt3b check is positive: mean_combined DCS .546699, DES .484848, MSE .022356 versus WT .037084 (39.72% reduction), severity abs .401341 versus sentinel6.907755. Therefore results are not solely gains onv3 KOs againstv2 WT. This weakens, without eliminating, the chemistry-only explanation; genotype and experiment remain inseparable in this small source.

Do not hide the failing case: Dnmt3a mean_combined MSE .051105 versus WT .032603, a56.75% worsening; DES−.03125 despite DCS+.277529. Other per-genotype MSE gains: Kmt2a68.83%, Kdm2b59.78%, Dnmt162.84%, Ehmt219.68%, Kmt2b65.17%. Average variogram is slightly worse than WT (.016921 vs .016644), despite improved average MMD (.014665 vs .020215). All raw per-gene results remain saved.

Mean-combined predicted detection is23.8%–24.9% across seven queries, roughly twice sourceWT11.9%; requested comparison to each true sourceKO density and attention to small positive activation masses. This is an emitter magnitude question, not proof of invalidity. Generic quantile means can activate the union of genes shifted in different donors, so detection requires explicit checking before target transfer.

All expandedKO barcode whitelists matched exactly; WT retains the already-disclosed690-cell gap. Independently verified v2 review/parent-permit bindings and selected expanded annotation hashes; no duplicate barcodes or embryo-sex inconsistencies. New source counts provide WT10 plus72KO embryos. Cross-platform support diagnostic remains28.16% targetWT outside source per-state95% distance; this is descriptive, not a probability or automatic exclusion rule.

Updated recommendation: source evidence supports preparing a clearly labelled generic developmental-perturbation hypothesis artifact for review, without claiming gene-specific Gata4 prediction or any leaderboard score. Parent/user decides whether the single remaining upload is worth the known functional-class, conditional-lineage, assay and amplitude risks. Waiting on actual target artifact and exact-emitter audit; no submission authorized or performed.

## Adaptive hurdle-emitter review, 10:29 UTC

Read `HURDLE_PROTOCOL.md`, `crossko_hurdle.py`, and runner diff before the repaired run completed. The change explicitly separates detection-fraction response from positive-expression quantiles, avoiding interpolation through the zero discontinuity. Original7KO outputs remain separate and the adaptation is correctly declared. Same heldout genotypes, sex-balanced WT controls and frozen source hyperparameters remain in force.

Early bug sent to builder: in active states, an exactly zero per-gene response still triggers positive-quantile interpolation/smoothing when another gene has nonzero response. The all-zero global shortcut does not protect these genes. Requested a per-gene zero-response identity rule before common closure and a mixed-response null test. Unsupported source genes set to zero response should not quietly acquire an interpolation transformation. If repaired after execution starts, preserve the old output/provenance and rerun under a distinct frozen revision rather than silently relabel artifacts.

Metric naming reconciliation: authoritative original7KO `summary.csv` remains mean_combined DCS .5761754007 and mean_within .5352361890. A report of approximately.54 should not be attributed to mean_combined. New hurdle results will be identified separately.

## Corrected hurdle and actual deployment, 10:38 UTC

Corrected hurdle-v2 independently reviewed; partial-null test checks a common rowwise closure factor for unchanged genes rather than demanding impossible final-column invariance. Original unconditional7KO remains an immutable baseline; invalid hurdle-v1 is separately retained/ineligible. Hurdle-v2 mean_combined achieves average source DCS .573896, MSE .027175, MSE6/7 and severity7/7; Dnmt3b chemistry-matched DCS .553984, MSE .023492. Compared with original unconditional mean_combined DCS .576175/MSE .026827, response is similar while average MMD improves .014665→.013577 and variogram .016921→.010134. Source truth detection is10.6%–14.0%, confirming original23.8%–24.9% was excessive; hurdle Dnmt3b prediction12.54% matches truth12.51% closely.

`deploy_diagnostics.py` was inspected. It fits all seven permitted KO identities with the source-only selected mean_combined operator, then creates frozen Mab and both Gata variants before loading released Mab outcomes. No target outcome supplies fitting, gating, amplitude or identity features. No forcedGata4/Gata6 transcript zero or allele-dose multiplier. Conservative gate is a positive-support hypothesis, not complete Mesp1 lineage or a recombination probability. Outside gated rows remain exactly WT.

Independently read both Gata H5ADs and checked full7449×500 matrices, official ordered panel, unique row names, all finite/nonnegative values, 10,000 closure (max error .00450/.00311), exact carrier coordinates, frozen SHA256 and outside-gate WT equality: PASS. This is an independent structural check, not running the full official portal validator.

- All-supported: SHA256 d845759d0e04f0ee0db74c2877e4fbf4f6d2889ccad448da518d29392af24a2b;7449 changed rows; detection11.084% versus WT10.499%; mean-responseL2 4.2462
- Positive-lineage: SHA256 14a772953abde3797941869397dfb07342a7e08dddfdbf7828b04c9c79153b8d;1660 changed rows; detection10.653%; mean-responseL2 .87246

Requested donor-index provenance: combined mode resamples donor rows but deployment originally discarded returned donor indices. Existing support/lineage/zero-difference records therefore describe original recipient slots versus emitted population rows, not paired cell trajectories or actual donor identity. Coordinates remain original recipient slots by design; geometry is not ranked in the current task. This does not invalidate expression metrics but must not be called lineage-preserving individual transport.

Released-Mab external diagnostic: new DCS .14354 vs sampledWT .09703 and oldadult .13725; DES .01449 vs−.01449/0; abs severity2.07083 vs4.93653/6.90776. New MSE .07907 vsWT .06290 (+25.7%), MMD .01801 vs .01507, variogram .02452 vs .01986. This is modest ranked-response gain with distribution losses. **MSE is unranked and cannot alone reject the candidate.** Parent requested a bounded local calibration using public skill mapping, matchedWT floor and releasedKO split-half ceiling to assess the actual .30/.25/.25/.12/.08 tradeoff. It will be labelled custom released-data calibration, never official hidden-target score or server parity; signedPSS beta/R² requested. Current inference is a weak/mixed cross-platform result, not proof of no competition value.

## Final weighted-objective audit and recommendation, 10:42 UTC

Reviewed `MAB_LOCAL_CALIBRATION_PROTOCOL.md`, `calibrate_mab.py`, anchors, all nine per-seed scores and summary. Independently recomputed all nine weighted totals from saved raw metrics and public `skill()` mapping: PASS within1e-10. Actual matched reference is the entire releasedE9.5WT; literal reference floor is DES0/DCS0/PSSsentinel. KO random halves give technical ceilings at seeds0/1/2, with finite nondegenerate floor/ceiling separations. There is no missing-metric weight renormalization. This is a custom released-Mab calibration, **not official server parity, biological replication, a Gata4 prediction, or a70-point claim**.

Local weighted results (mean ± technical-seed SD):

- sevenKO hurdle-v2:57.2518 ± .2790; range56.9296–57.4157
- historical adult emitted comparator:49.5670 ± .3850
- sampled7449WT comparator:53.0306 ± .4202
- actual matched-reference WT floor:50 by construction

The new operator's gain is +7.6848 over historical adult and +4.2212 over sampledWT. New-minus-adult component contributions are DES+.1874, DCS+.0472, severity+6.7507, MMD+1.0089, variogram−.3095. Thus the response-weighted task objective supports the new operator despite worse unranked MSE. However, most gain is severity calibration, not strong DE/direction recovery. Mean unthresholded severity beta=.12669, log beta=−2.06608, R²=.05787. It is a small positively aligned response that passes the metric gate, not correct amplitude or high causal fidelity. The old comparator's unthresholded beta is+.00869 but negativeR², so the reported exp(sentinel)=.001 is a floor encoding, not its fitted beta.

**Recommended single experimental selection: `gata4_all_supported.h5ad`**, if parent/user decides to spend the remaining attempt. Its complete source operator has genotype-heldout source evidence and the frozen externalMab weighted diagnostic. The conservative positive-lineage gate is a useful sensitivity artifact, but changes only1660rows, drops mean-responseL2 from4.246 to.872 and has no independent comparative evidence showing better target prediction. This recommendation is a competition hypothesis, not a guarantee, and does not rely on novelty or an identity-specific learned effect. It remains reasonable to reserve the final upload because all training interventions are epigenetic regulators and assay/conditional-lineage transport is uncertain; the actual upload decision belongs to parent/user.

Donor provenance sidecars are now provided for all three deployment matrices. Existing per-row cell/state comparisons must distinguish original recipient slot from selected donor. No submission artifact was overwritten or uploaded during this audit. Both Gata artifact hashes remain those independently checked above.

Final status: source admissions/mappings/heldout splits/emitter implementation reviewed; actual source and cross-platform outcomes audited; candidate matrices structurally verified; weighted objective reconciled. No compliance blocker identified in the inspected task-scoped sources. Scientific risks explicitly remain blocks_submission:false. This audit is complete for the current frozen prototype and candidate choice; further changes require new provenance and review.

## Final immutable v0087 release check, 10:45 UTC

Parent selected all-supported; builder finalized a single new artifact with protected v0084 metadata/geometry and unchanged frozen expression. Independent audit reloaded final, pre-calibration source and parent; reexecuted the repository's local contract validator: **PASS**. Final expression dtype/content is bit-identical to pre-calibration d845759d... source. Obs identities match the frozen expression carrier; obs/var and spatial coordinates match protected v0084. All7449×500 expression entries, canonical panel order, finite/nonnegative values and10,000 panel closure pass. No model rerun, response refit or new experiment was performed during finalization.

Ready artifact:
`/workspace/shared/t3_state_response_20261008/v0087/t3_gata4__embhurdle__v0087.h5ad`

Final file SHA256:
`b0cfdf5e870f762185efd9f2bdc803cab26ecb0a54e18a870286d41165ce5fc9`

Expression-array SHA256:
`2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98`

Single-candidate ZIP:
`/workspace/shared/t3_state_response_20261008/v0087/sr7__t3__upload__20261008.zip`

ZIP SHA256:
`f071ed337ee47de12f5ee38706bb8e1f2962f8b0904c9317c519ebf01a4704a3`

ZIP has exactly the named H5AD, with matching member hash and CRC PASS. Independently verified27 code, permit, protocol, frozen-prediction/scorer and eight actual model-input hashes against embedded provenance. Source licenses/accessions, all seven source identities,7449 active rows/2110 recipient-slot OOD rows, generic prior and no forced Gata4/Gata6 RNA/dose assumptions are disclosed. Contract metadata change explains the new file hash; expression is unchanged. Source permit/code hashes are not a substitute for organizer endorsement, and no such endorsement is claimed.

Original evidence remains available and distinct:

- Initial3KO negative identity-selection `crossko_results/SELECTION.json`: SHA2561b8e20fd3311cdd6d758dcb3547c79204efdd33e3c22b0f997ca407e442da809
- Original7KO unconditional selection `crossko7_results/SELECTION.json`: SHA256b62f1ed5bf9a09c05916b9fcd69cbf194d2230aeed61a968ce59237d041730da
- Ineligible hurdle-v1 provenance `crossko7_hurdle_results/FROZEN.json`: SHA256db44532c90741444817d7314e2347601d5e7905cac9ccf5395e81b6203a846f7
- Corrected hurdle-v2 provenance `crossko7_hurdle_v2_results/FROZEN.json`: SHA256399d9e881d93c4b3c24e1bdf4054c617ca9c6de6c45e1b42f28a29a12be76c07

**Release disposition: READY for parent-directed handoff; not uploaded, no server score.** Scientific risk statements and custom-calibration limitations above continue to apply. No additional experiments are requested or implied by this final audit.
