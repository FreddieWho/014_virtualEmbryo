import json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
R=ROOT/'reports'
evals=[json.loads((R/f'eval_seed{i}.json').read_text()) for i in range(3)]
assert all(e['complete'] for e in evals)
final=json.loads((ROOT/'artifacts/final/BUILD.json').read_text())
dev=json.loads((ROOT/'artifacts/dev/BUILD.json').read_text())
checks=json.loads((ROOT/'artifacts/final/INDEPENDENT_CHECK.json').read_text())
devchecks=json.loads((ROOT/'artifacts/dev/INDEPENDENT_CHECK.json').read_text())
replay=json.loads((ROOT/'artifacts/replay/BUILD.json').read_text())
assert checks['status']=='PASS' and checks['independent_X_exact']
assert final['artifacts']['zp']['sha256']==replay['artifacts']['zp']['sha256']
metrics=['de_score','de_direction','mmd_u','variogram','neighborhood_mmd','variance_ratio']
summary={arm:{'raw_mean':{k:float(np.mean([e['arms'][arm]['raw'][k] for e in evals])) for k in metrics},'local_total_mean':float(np.mean([e['arms'][arm]['local_skills']['TOTAL'] for e in evals])),'local_total_per_seed':[e['arms'][arm]['local_skills']['TOTAL'] for e in evals]} for arm in ['parent','zp','copy_last','geneperm']}
(R/'LOCAL_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
rows=['| Arm | DE ↑ | Direction ↑ | MMD ↓ | Variogram ↓ | Neighborhood MMD ↓ | Variance ratio | Local total |','|---|---:|---:|---:|---:|---:|---:|---:|']
for arm,s in summary.items():rows.append('| '+arm+' | '+' | '.join(f"{s['raw_mean'][k]:.6f}" for k in metrics)+f" | {s['local_total_mean']:.4f} |")
ss=final['artifacts']['zp']['diagnostics'];parent=final['artifacts']['parent']
report=f'''# v0037 x2_zero_preserve: completed single-axis operator transfer

## Result and recommendation

One frozen heart-extrapolation candidate was generated and independently reproduced. Status: **READY_UNSUBMITTED_WITH_CAUTION**. No server submission or score is claimed. This is an explicit H2 detected-entry-allocation transfer onto the exact historical X2 parent. It is not a replay or improvement claim for v0030.

The local evidence is mixed by channel: DE, direction, and variogram improve; distribution and neighborhood errors worsen materially. The gene-permuted negative control improves variogram even more, so variogram improvement does not establish that the temporal gene alignment is useful. Keep the artifact available for the requested server arbitration, with low confidence; do not promote or hard-reject it from the cross-mechanism aggregate alone. The original v0030 incumbent remains untouched. Science caution has blocks_submission: false.

## Identity

- Task: T2:heart:val_extrap, E10.5 target; candidate ID candidate/T2_heart_val_extrap/v0037_x2_zero_preserve
- Candidate: artifacts/final/submission.h5ad
- Candidate SHA256: {final['artifacts']['zp']['sha256']}
- Actual matched parent: artifacts/final/parent_x2_recipe.h5ad
- Parent SHA256: {parent['sha256']}
- The parent hash **exactly matches** historical X2 b884e3b6… in reports/t1_late_anchor_20261008/MANIFEST.tsv. No metadata or parameter search was needed. X2's verified server score is 50.35, below historical incumbent v0030 51.12 and numeric-high v0032 51.1388. Those scores belong to their own artifacts.
- Original v0030 artifact SHA256 71f587ed68177b7cdbea27f27333523caa33668badc08efd782afb3d541d53a3 was not restored. v0032 is t-shrunk and is not this parent. Recipe resemblance is not historical identity.
- Exact final shape: 25,179 × 500; unique source rows; 8,123 eligible rows in NCC, Peri, V-CM, aPHM, pPHM
- Separate-process whole-build replay regenerated **identical parent and candidate HDF5 bytes**, recorded under artifacts/replay

## Sole changed axis

The frozen source-state median drift, scalar 0.9, rows, metadata, gene panel, coordinates, shared-state threshold (30), orphan handling, clipping, and expm1-library rule all stay fixed. The change is only shift allocation: add drift / max(detected fraction, 0.05) to positive **raw source** entries. This includes the existing H2 detection-floor rule. There is no new dose, no endpoint, no external data, no shape change, and no composition change.

This operator preserves source zeros, not an identical zero mask: positive values can clip to zero. In the final artifact, zero→positive entries = 0; positive→zero entries = {ss['positive_to_zero']:,}. All orphan expression is source-exact. Final library max relative error is {ss['max_abs_library_ratio_error']:.9g}; every row passes the declared 1e-6 tolerance. The old parent activates 29,629 source-zero entries and clips 2,380 positives.

Input drift is unchanged, but clipping and library projection can alter final pseudobulk movement. Before clipping, inverse-detection allocation matches the intended state mean drift except where floor 0.05 or complete absence of detection prevents exact allocation (NCC and pPHM final states). We do not claim conservation of the final drift vector.

## Full matched local evaluation

Fit on all 58,716 E8.25_late cells and all 24,826 E8.75 cells, all 500 genes. Generate all 24,826 prediction rows using the same stratified selection code (all rows when n exceeds stage count). All arms were frozen before the evaluator read released E9.5. Target fitting is prohibited: the 53,742-cell E9.5 file is opened only in the evaluator, with the historical 10% target working copy split into truth/ceiling and 10% reference copy. The official checked-in metric implementation is run on all prediction rows and all 500 genes, fixed scorer seeds 0, 1, 2. Any scorer-internal sampling is unchanged. Final target E10.5 and hidden E12.5 were never read.

Three-seed raw means and local calibrated totals follow. The total is a diagnostic, never a server-score prediction.

{chr(10).join(rows)}

Geometry raw channels are exactly identical across all four arms for every seed, as required by the locked coordinates. Copy-last and shuffled-drift controls were actually generated and fully scored for all three seeds. Zero-drift output is bytewise expression-identical to copy-last; its redundant scoring is deduplicated explicitly. Parent-off replay is expression-exact to the unchanged historical parent routine.

## Exposed failure, no silent repair

The development fold has 31 shared states and 24,788 touched rows, whereas the final fold has 5 shared states and 8,123 touched rows. In the dev candidate, exactly **two Unknown-state cells**, source/output rows 4,153 and 23,725, lose all positive values after the stronger detected-only clipping. Their original library sizes are about 10,000; output libraries are zero. The mandated old clip-and-rescale rule cannot recover an all-zero row. The dev library invariant therefore **fails** on these two cells (max relative error 1.0), even though independent replay and format checks pass. The parent and gene-permuted control have no such failures. No fallback, clipping change, parameter adjustment, or post-hoc row deletion was introduced. Final candidate has no such rows.

This failure and the much broader dev state coverage limit transfer confidence independently of the scalar score. Full results remain included. Neighborhood MMD and marginal MMD worsen in all three seeds; DE improvement is not uniform in every seed (seed 0 ties). The strong null variogram result is a warning against attributing covariance gains to correct temporal dynamics.

## Checks and reproducibility

- Exact current official ordered panel: 500 genes; file SHA256 bf40079bfb50c78d9360905156bd7fd8b39e711ad0cc44866e6dac3f7e9999fa. Index digest a9a553108e19acb6 uses newline-joined names without final newline and is consistent
- Final format contract: PASS, 25,179 cells within [1,000, 25,179], finite nonnegative X, unique obs names, finite spatial_3D
- Source hashes and state medians independently recalculated: PASS
- Candidate vs parent obs/var/coordinates exact: PASS; source-row coordinates exact after the historical float32 representation
- Independent scalar-loop final and dev expression replay: exact, max error 0
- Separate-process parent and final-candidate HDF5 byte replay: exact
- Seven synthetic checks: PASS, including explicit all-clipped failure behavior
- Thread budget: one BLAS/OpenMP thread; three local seeds executed serially. No hidden dataset or external endpoint was used
- Full receipts: artifacts/final/BUILD.json, artifacts/final/INDEPENDENT_CHECK.json, artifacts/dev/BUILD.json, artifacts/dev/INDEPENDENT_CHECK.json, reports/eval_seed0.json through eval_seed2.json
- Source-row ledgers and frozen state deltas are included for both folds. Code SHA256 inventory and runtime versions are in reports/CODE_SHA256.tsv and reports/ENVIRONMENT.json

Run: bash code/run.sh OFFICIAL_DATA_DIR NEW_OUTPUT_DIR. Set PYTHON to the desired environment interpreter; package versions are recorded. The data directory must contain index.json, the exact panel file, and E8.25_late.h5ad / E8.75.h5ad / E9.5.h5ad. Completed output directories are never overwritten. The historical untouched recipes and official scorer sources are included under code/.

## Source ledger

Only the three official released heart stages are used. They were supplied by the coordinating task's official download restoration; this worker performed no browser or portal operation.

- E8.25_late.h5ad: d56f94d3e2d719ed3074d86c03eae457ccf90b24145d33300f9958f0e8078593
- E8.75.h5ad: 149ab6df7c99ad85046c8aebebcf0c43689b3720c59ffb7cc550edcf2f13a83c
- E9.5.h5ad: 371ca6530e084de2b6cd6703b49d95f4bb59546c9291659809575382a630ee9a

## Coordinator-only integration notes

Reserve v0037 was confirmed before generation. No shared INDEX, tracking, registry, or source files were edited. Suggested tracking entry: “2026-10-09: v0037 x2_zero_preserve transfers H2 detected-entry shift allocation onto exact X2 parent (b884e3b6…), with old drift/library/rows/geometry preserved. Full 3-seed matched local run and controls complete; channel trade-off and two dev all-clipped rows disclosed. Final contract and independent byte replay PASS; unsubmitted/unscored; no v0030 parity or server improvement claim.”
'''
(R/'REPORT.md').write_text(report)
handoff={'task':'T2:heart:val_extrap','candidate_id':'candidate/T2_heart_val_extrap/v0037_x2_zero_preserve','parent_candidate':'Historical X2 exact-byte reconstruction; not historical v0030','artifact_path':str(ROOT/'artifacts/final/submission.h5ad'),'sha256':final['artifacts']['zp']['sha256'],'parent_artifact_path':str(ROOT/'artifacts/final/parent_x2_recipe.h5ad'),'parent_sha256':parent['sha256'],'parent_historical_hash_match':True,'parent_server_score':50.35,'historical_v30_parity':False,'shape':[25179,500],'contract_result':'PASS','independent_replay':'EXACT_ARRAY_AND_HDF5_BYTE','local_metrics':summary,'library_final_max_relative_error':ss['max_abs_library_ratio_error'],'dev_library_failure_rows':devchecks['library_failure_rows'],'status':'READY_UNSUBMITTED_WITH_CAUTION','recommendation':'Keep available for server arbitration; low confidence, no scalar-only rejection or promotion','blocks_submission':False,'known_risks':['Actual X2 parent is weaker than incumbent v0030','Dev marginal and neighborhood MMD worsen','Two dev cells all-clip and lose library','Gene-permuted control also improves variogram','Released-stage proxy differs in state coverage and timing from final target'],'report':str(R/'REPORT.md'),'source_commit':'9d30857b5e25610e40872e6f2cfce18941678eaa','changed_paths':[str(ROOT)],'portal_or_upload_performed':False}
(R/'HANDOFF.json').write_text(json.dumps(handoff,indent=2)+'\n')
print(json.dumps({'report':str(R/'REPORT.md'),'handoff':str(R/'HANDOFF.json'),'candidate_sha256':handoff['sha256']},indent=2))
