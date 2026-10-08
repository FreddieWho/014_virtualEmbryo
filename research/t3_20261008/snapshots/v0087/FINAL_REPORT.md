# T3 strategic reset implemented: seven-KO state-response candidate v0087

2026-10-08. **v0087 scored53.42, +3.87 overv0084=49.55, and is promoted as the new T3 selection.** Submission was performed by the authorized portal worker, not this builder. The two-new-attempt budget is exhausted; no further uploads. Restrictive-lineage alternative remains unsubmitted. `blocks_submission:false`.

Official result: [account-specific link omitted] . Observed2026-10-08T10:48:14Z; UI submissiontime10:47 has no timezone label. Skills: DE41.7, direction51.2, severity75.0, MMD49.7, variogram42.3. Relative tov0084: −5.4,+2.8,+25.0,−5.1,−11.1. Gain is mainly severity; gene ranking and distribution structure worsen. This is not70 and not causal validation. Portal receipt is in v0087/SERVER_RESULT.json.

Timestamped team overview reported by coordinator at10:49:25UTC: Total167.1, Humanrank72 (previous163.2/rank83); rank can change. These are observed portal values, not recomputed totals.

## Artifact and decision

- Candidate: v0087, lane `embhurdle`; selected parent v0084, actual expression carrier official E8.75 WT sampled7449 cells with seed20260904
- File: `v0087/t3_gata4__embhurdle__v0087.h5ad`
- SHA256: `b0cfdf5e870f762185efd9f2bdc803cab26ecb0a54e18a870286d41165ce5fc9`
- Expression-array SHA256: `2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98`
- Single-member upload ZIP: `v0087/sr7__t3__upload__20261008.zip`; exact ZIP hash in ZIP_MANIFEST.json
- Local locked-board contract PASS; selected-parent obs/var/coordinates preserved; serialization and expression equality to pre-calibration frozen output PASS
- Existing scored artifacts unchanged. Final packaging only adds disclosure metadata and inherits the protected parent geometry; expression is byte-identical to the earlier frozen diagnostic. Five ranked expression metrics are unaffected by that geometry copy

This is a **generic developmental-perturbation prior**, not a Gata4-specific causal response model. GO identity models were genuinely tested and did not beat the generic mean. The default all-state choice is supported by actual source validation and a released-Mab objective diagnostic; restricting it to a small lineage gate has no independent outcome validation and reduces response markedly. This is a risk-labelled competition experiment, not a prediction of the Gata4 portal score.

## What changed relative to prior work

1. Replaced adult cardiac-fibroblast signed response with seven admitted E8.5 mouse-embryo interventions: Dnmt1, Dnmt3a, Dnmt3b, Ehmt2/sourceG9a, Kdm2b, Kmt2a, Kmt2b
2. Used original SNP-assigned embryo and barcode metadata to retain real cells. Raw libraries contain up to13.6million droplets; these were streamed rather than mistaken for biological observations
3. Matched the 500-gene observation panel using stable Ensembl IDs, including legacy symbols, and closed count rows to10000 before log1p. Exact unique500 mapping, no missing or duplicate mappings, independently checked
4. Fitted common states on WT only, learned per-embryo state abundance and within-state responses, and evaluated every genotype with ALL its KO records excluded from donor fitting
5. Corrected the observation emitter to separate detection-fraction changes from positive-expression quantiles, allowing measured activation without the artificial low-positive inflation caused by interpolating across zero
6. Compared actual serialized output matrices, not response-vector proxies, on direction, severity, DE, MMD and variogram

## Data and safeguards

Sources are selected GSE137337 E8.5 KO conditions and GSE122187 E8.5 WT, plus published supplementary barcode/embryo annotations. Seven KO identities plus WT span82 embryos. WT whitelist21825/22515 cells matched the deposited archive; the690 missing cells (~3.1%) are absent from the archive itself, not dropped by an expression cutoff. Retention by WT embryo is95.7–98.2%; counts by embryo/sex and published state are saved. All KO whitelist cells match exactly. No heuristic raw-droplet cell calling was used.

KO sex ratios differ markedly from WT8F/2M. Final seven-KO training uses same-sex WT controls with500 cells per WT embryo, equal biological KO-embryo response weighting, and equal500-cell evaluation samples per held-out KO embryo. Published adjusted developmental stage is preserved as metadata but not matched away: it may itself be a perturbation phenotype. WT10xv2 versus severalKOv3, cohort, strain and processing differences remain confounded. Dnmt3b10xv2 and relatively similar sex composition was prespecified as a chemistry-matched diagnostic.

New source use is hash-bound in task-specific source reviews/permits and recorded by the source worker in the repository data index. GEO permits data use/distribution; this report does not incorrectly claim the numerical matrices have a blanketCC license. The source paper, author attribution and exact accessions are retained. Ontology-only shared features were rebuilt for the expanded genes, never spliced between incompatible SVD bases. The final generic model does not use ontology identity to determine its predicted response.

No Gata4/Ctnnb1 hidden outcomes, same-target KO signatures, comparable alleles, or forbidden phenocopy datasets were used. No score inversion, paid service or GPU was used.

## Experiments and results

### Measured Mab control

The earlier measured-Mab experiment is in REPORT.md. Its main lesson is explicit: empirical whole-KO resampling nearly reaches a technical split ceiling and does not prove unseen-gene prediction. State-mean shifts failed to beat global-mean shifts on direction/severity despite distribution gains. This prevented an oracle result being marketed as a transferable model.

### Strict source leave-intervention-out

WT-only PCA12/kmeans8, min10 state cells per embryo, fixed n/(n+50) shrinkage,21 positive quantiles, fixed ridge alpha10, and seed241. For each query, sorted embryos alternate between discovery and evaluation. ALL query outcomes are excluded from transferable-model fitting; query-discovery outcomes are used only for a separately labelled known-response oracle. The original three-KO and seven-KO protocols remain immutable. This program was adaptively developed, not a pristine independent confirmation set.

Final hurdle-v2 seven-KO averages:

| Model | DE | DCS | Abs log severity | MMD | Variogram | Unranked MSE |
|---|---:|---:|---:|---:|---:|---:|
| WT sampled identity | −.0811 | −.0661 | 6.7469 | .02021 | .01664 | .04857 |
| Generic mean, within | .4782 | .5356 | .8087 | .01530 | .01008 | .02765 |
| **Generic mean, composition+within** | **.4662** | **.5739** | **.5377** | **.01358** | **.01013** | **.02718** |
| GO ridge, composition+within | .4329 | .5221 | .8250 | .01464 | .01129 | .03132 |
| GO nearest, composition+within | .2805 | .3437 | 2.4813 | .02081 | .01721 | .04743 |
| Known-response oracle | .7900 | .8389 | .1090 | .00514 | .00296 | .00727 |

Generic combined improves MSE in6/7 genotypes and severity in7/7. It is source-selected over the identity-specific models. Dnmt3b chemistry-matched result: DCS .5540, severity .4105, MSE .02349 versus WT .03708. This argues against a *purely* v2/v3 explanation, but does not remove cohort confounding.

**Important failure:** Dnmt3a MSE .05222 versus WT .03260 (+60.2% worse), DES−.03125 despite positive DCS .2696. Do not average away this downside. Descriptive genotype-bootstrap DCS improvement vs WT has95% range .522–.758; with only7 adaptively inspected identities this is not an independent embryo-generalization confidence interval.

The original unconditional-quantile emitter had DCS .5762, close to hurdle .5739, but predicted23.8–24.9% detection while actual source KO detection is10.6–14.0%. Hurdle-v2 predictions are12.2–12.8%, retaining response performance while improving variogram from .01692 to .01013. The invalid interim hurdle-v1 smoothed zero-response genes; its files are retained but excluded from final selection. V2 per-gene zero-response and whole-null behavior are explicitly tested.

### Released Mab cross-platform diagnostic

The final source model predicts Mab from official E9.5 WT with no Mab fitting, amplitude choice or gate tuning. Its prediction and both Gata variants were serialized and hashed before loading Mab truth. Mab has been used by historical work, so this is an adaptive external diagnostic, not a novel confirmatory test.

Raw new-Mab versus sampled-WT: DCS .1435 versus .0970; absolute log severity2.0708 versus4.9365; MSE .07907 versus .06290; MMD .01801 versus .01507; variogram .02452 versus .01986. **Response metrics improve modestly while distribution metrics worsen.** Full-truth PSS slope is~.126 with R² .0568: a weak but positive aligned response, still substantially undershooting, not a near-perfect magnitude fit.

Parent requested a competition-weighted calibration because MSE is unranked and response carries80%. Using the public core skill function, full matchedWT floor, three fixed KO split-half ceilings, and weights .30/.25/.25/.12/.08:

- New seven-KO hurdle: **57.25±.28**
- Historical adult emitter: **49.57±.38**
- Sampled7449WT: **53.03±.42**
- Paired new-minus-adult: +7.51 to+7.79 across seeds

There are90–91 true DE genes in these splits. Mean PSS beta~.1267, R²~.0579; most calibrated benefit comes from severity. **These are custom local Mab totals, not official scores, not server-parity proof and not a Gata4 forecast.** Full-reference WT floor is exactly50 by construction; sampledWT is a different prediction and scores differently.

## Exact final emission and biological limits

The generic response averages independent-embryo responses within each training genotype and then equally across the7 genotypes. Per-state composition log-ratios resample whole WT carrier observations. The hurdle component changes positive-cell counts using measured detection differences and transfers positive-expression quantiles relative to the targetWT carrier. New positive cells are chosen through deterministic random tie ranking. This is an unpaired sampled population; neither tie assignment nor recipient row is a reconstructed cell fate. Joint dependence is only approximately preserved.

All8 state templates satisfy the training-support gate, so **all7449 Gata rows are active**. The file name `all_supported` means training-supported states, NOT a distance-gated subset. Source-WT95%-distance flags2110 recipient rows (28.33%) as extrapolative; they are included without additional shrinkage or fallback. The threshold is descriptive, not a validated uncertainty probability. After composition resampling,27.33% of actual donor rows are flagged. Donor mappings are independently replayed and saved.

Gata base detection10.499% becomes11.084%; global mean-response L2 is4.246. Comparing matched donor observations rather than unrelated recipient rows,48,980 zero entries become positive and29,411 positives become zero. Raw recipient-row changes are larger because composition resamples whole observations and must not be interpreted as cell-level activation events.

The conservative positive-lineage alternative changes1660 rows (22.29%), detection10.653%, response L2 .872 (20.5% of all-state magnitude). It is unsubmitted. It uses only verified broad cardiac/endothelial labels and explicit CM/SHF metadata; ambiguous CSE/PHM/JCF expansions are not guessed. The final all-state model is an indirect/generic developmental hypothesis, not a claim of cell-autonomous Mesp1 action everywhere. It neither forces Gata4/Gata6 RNA to zero nor sets Gata6 RNA to50%. The actual conditional target genotype and lineage-specific dosage remain incompletely represented.

Original carrier geometry is inherited from selectedv0084 for the final file. Composition donors replace expression in recipient slots; geometry is not ranked by the five-term objective. Source donor IDs/states/OOD flags are retained separately so this assumption is transparent.

## Verification and handoff

- Tests: held-out KO poisoning leaves fit/output unchanged; missing identity-prior rejection; stable closure under extreme finite log-values; whole KO=WT exact null; partial per-gene zero-response invariance up to shared row-closure factor; no unsupported zero activation
- Main and supplementary source matrices are serialized/reloaded before metrics; final candidate expression is identical to frozen pre-Mab-calibration output
- Donor-provenance replay is exact for all3 deployment diagnostics
- Final locked local contract PASS, unique7449 rows, ordered500 panel, finite nonnegative expression, panel10000 withinfloat tolerance, protected parent metadata/coordinates, ZIP CRC/member hash PASS
- Source, annotation, code, protocol and candidate hashes are in source permits, per-run FROZEN.json/MERGE_RECEIPT.json, FINAL_CODE_HASHES.json and v0087 manifests
- Full source metrics: crossko7_results/metrics.csv and crossko7_hurdle_v2_results/metrics.csv; per-query outputs and selection receipts remain available
- Local Mab calibration: deployment_diagnostics/MAB_LOCAL_CALIBRATION*.json/.csv; exact raw metrics retained
- Independent review: /workspace/shared/t3_transfer_validation_audit_20261008.md

Final decision: PROMOTE v0087 after actual53.42 server result. Preservev0084 and all negative controls; both newly authorized attempts are now spent. No more training or uploads after this delivery. Next offline work, if requested, should target response-gene ranking and conditional/platform structural damage rather than another response-dose sweep. Parent owns repository registration and publication; this packet does not claim every source/code file has been pushed. Creation-time manifests remain immutable and may state submitted:false; the later SERVER_RESULT receipt records the terminal result.


## Verified narrow repository registration

Coordinator verified main commit 7b831f65cca75c76620ad2e595897fdc25a0a0dc after scoring: https://github.com/FreddieWho/014_virtualEmbryo/commit/7b831f65cca75c76620ad2e595897fdc25a0a0dc . Only three core registry/status files were included; this does not imply complete experimental code or source data-index publication. The full reproducibility evidence is delivered in this packet. Portal receipt remains the scoring authority.

Portable inference replay passed in the extracted packet: only WT carrier, frozen response and small saved state model are read; expression/donor indices match exactly. See inference/REPLAY_RESULT.json.
