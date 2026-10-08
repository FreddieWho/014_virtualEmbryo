"""Recompute T3 audit from frozen source summaries; no inference or training."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_support import parse_args, logical_source, source_reference, source_sha256
args=parse_args("t3")
import pandas as pd,numpy as np,json,hashlib
O=args.output_dir; O.mkdir(parents=True,exist_ok=True)
E=args.evidence_dir; R=E/'t3repo'; P=E/'t3_delivery/package'; V=E/'t3_v88_optimization_20261008'; W=E/'t3_v87_restored'
sources={}; rows=[]
def sha(p):
 p=Path(p); h=source_sha256(p,E);sources[source_reference(p,E)]=h;return h
idxpath=E/'registries/t3_selected.tsv';sha(idxpath)
idx=pd.read_csv(idxpath,sep='\t');idx=idx[idx.board=='T3:gata4'].set_index('version');idx.to_csv(O/'candidate_inventory.csv')
def add(v,family,protocol,metric,value,reference=None,refvalue=None,parent=None,direction='higher',status='proxy_only',source=None,caveat=''):
 ir=idx.loc[v] if v in idx.index else None; score=float(ir.server_score) if ir is not None and pd.notna(ir.server_score) else None
 ps=float(idx.loc[parent].server_score) if parent in idx.index else None
 rows.append(dict(candidate=v,family=family,protocol=protocol,metric=metric,local_value=value,local_reference=reference,local_reference_value=refvalue,local_improvement=(value-refvalue)*(1 if direction=='higher' else -1) if refvalue is not None else None,better=direction,server_score=score,server_parent=parent,server_parent_score=ps,server_delta=score-ps if score is not None and ps is not None else None,candidate_sha256=ir.sha256 if ir is not None else None,validity=status,absolute_gap_comparable=False,source=source_reference(source,E) if source else None,source_sha256=sha(source) if source else None,caveat=caveat))
# Algorithm-paired source-domain diagnostics with explicit source-carrier mismatch.
f=P/'reports/frozen_donors/SUMMARY.tsv';d=pd.read_csv(f,sep='\t'); proto=P/'reports/frozen_donors/FROZEN_PROTOCOL.json'; ph=sha(proto)
metrics=['de_score','de_direction','severity_abs','mmd_u','variogram','mean_response_mse']
for (scenario,split),g in d.groupby(['scenario','split']):
 g=g.set_index('method')
 for method,v in [('qtl025','v0084'),('dsign05','v0085')]:
  for m in metrics:add(v,'fixed_donor',scenario+'/'+split+'/'+ph[:12],m,g.loc[method,m],'identity',g.loc['identity',m],'v0048','higher' if m in metrics[:2] else 'lower',source=f,caveat='Same frozen emitter/parameters; source WT carrier differs from target hurdle; historical holdouts adaptively reused; reconstructed target hash differs from absent original bytes')
# Historical source ranks; NOT comparable between routes due candidate-set-dependent rank.
for date,mapping in [('20261006',{'o1_dual_form':'v0075','o2_gate_mult':'v0076','o3_shrunk_beta':'v0077','n1_nmf_ablation':'v0078','n2_marker_gate':'v0079','n3_switch_emit':'v0080'}),('20261007',{'o1_hnmf':'v0081','o2_pnmf':'v0082','o3_psb':'v0083','n1_qtl':'v0084','n2_dsign':'v0085','n3_pswap':'unsubmitted_pswap'})]:
 for lane,v in mapping.items():
  f=R/f'reports/t3_six_routes_{date}'/lane/'SELECTION.json';s=json.load(open(f));r=s['mean_weighted_rank'];b=s.get('best_params');b=b if b in r else min(r,key=r.get)
  status='invalid_heldout_leakage' if v in ['v0080','v0083'] else 'proxy_only'
  if lane in ['n1_nmf_ablation','n3_pswap']:status='invalid_sign_interpretation'
  add(v,'historical_source_rank',s.get('design_sha256',date)+'/'+lane,'weighted_rank',r[b],'identity',r.get('identity'),'v0048','lower',status,f,'Lane-specific rank denominator; different emitter/carrier for some routes; do not pool ranks or treat as skill points')
# WT observational developmental proxy, exact source JSON, all submitted and rejected arms.
f=R/'reports/t3_five_select_20260929/DEVELOPMENT.json';j=json.load(open(f));vals=j['weighted_mean_group_mse']
for method,v in [('r2gene','v0057'),('r4spline','v0058'),('r3bag','v0059'),('r1active','unsubmitted_r1active'),('r5local','unsubmitted_r5local')]:add(v,'WT_five_select','WT_train01_dev2_20260929','group_MSE',vals[method],'H',vals['H'],'v0048','lower',source=f,caveat='Single WT specimen; local training blocks differ from final full-WT fit; observational high/low groups are not KO truth')
f=R/'reports/t3_round2_20260928/REPORT.md'
add('v0053','adult_response_MSE','whole_gene_5fold_pooled','MSE',.00505101,'v0046',.00503888,'v0046','lower',source=f)
add('v0052','WT_hurdle','four_spatial_blocks','MSE',1.336405,'v0048',1.285491,'v0048','lower',source=f)
f=R/'reports/t3_five_20260927/REPORT.md'
add('v0044','adult_response_MSE','whole_gene_5fold_pooled','MSE',.00521594,'v0034',.00504725,'v0034','lower',source=f,caveat='Comparator is mean response, not WT carrier v0009; do not mislabel +.52 vs carrier as paired sign reversal')
add('v0046','adult_response_MSE','whole_gene_5fold_pooled','MSE',.00503888,'v0034',.00504725,'v0034','lower',source=f)
add('v0048','WT_hurdle','four_spatial_blocks','MSE',1.285491,'WT_no_Gata_covariate',1.304943,'v0009','lower',source=f)
f=R/'reports/t3_three_20260929/REPORT.md'
for v,val in [('v0054',.185274647),('v0055',.209693894),('v0056',.190587346)]:add(v,'WT_three','WT_fourblocks_14groups_20260929','group_MSE',val,'H',.190683629,'v0048','lower',source=f)
# Current source/Mab totals: same skill function but different outcomes/calibration -> no absolute error.
f=V/'source_evaluation/summary.csv';s=pd.read_csv(f).set_index('model'); baseline=s.loc['baseline','total']
for method,v in [('baseline','v0087'),('conditional','v0088'),('residual','unsubmitted_v88_residual'),('both','unsubmitted_v88_both')]:add(v,'embryo_hurdle','source7_LOKO_seed012','custom_skill_total',s.loc[method,'total'],'baseline',baseline,'v0087','higher','cross_domain_custom_calibration',f,'Equal genotype weights; adaptive 7 KO source validation, not Gata4 target score')
f=V/'deployment/MAB_LOCAL_CALIBRATION.csv';mab=pd.read_csv(f);s=mab.groupby('model').local_total.mean()
for method,v in [('baseline','v0087'),('conditional','v0088'),('residual','unsubmitted_v88_residual'),('both','unsubmitted_v88_both')]:add(v,'embryo_hurdle','Mab_custom_seed012','custom_skill_total',s[method],'baseline',s['baseline'],'v0087','higher','cross_domain_custom_calibration',f,'Released reused Mab different target, full-WT floor / technical split ceilings; seeds not independent candidates')
f=W/'deployment_diagnostics/MAB_LOCAL_CALIBRATION.csv';z=pd.read_csv(f).groupby('model').local_total.mean();add('v0087','embryo_vs_adult','Mab_custom_seed012','custom_skill_total',z['sevenKO_hurdle'],'historical_adult',z['historical_adult'],'v0084','higher','cross_domain_custom_calibration',f,'Historical adult adapter need not be exact v84 recipe; paired method transfer comparison only, not exact artifact delta calibration')
pd.DataFrame(rows).to_csv(O/'paired_local_server.csv',index=False)
# Diagnostic ranking and threshold counterfactuals: do NOT pool different metric protocols.
checks=[]
for (scenario,split),g in d.groupby(['scenario','split']):
 g=g.set_index('method');a=g.loc['qtl025'];b=g.loc['dsign05']; wins=[bool(b[m]>a[m]) if m in metrics[:2] else bool(b[m]<a[m]) for m in metrics[:5]]
 checks.append(dict(cohort='fixed_donor',scenario=scenario,split=split,n_scored=2,source_metrics_favor_v85=sum(wins),top1='v0085' if all(wins) else 'mixed',server_best='v0084',missed_server_points=49.55-47.45,missed_incumbent_gain=49.55-47.93,independent_candidate_pairs=1))
pd.DataFrame(checks).to_csv(O/'dominance_reversals.csv',index=False)
rank=[]
for cohort,ordered,scores,parent in [('WT_five_select',['v0057','v0058','v0059'],[47.37,47.95,47.93],47.93),('fixed_donor',['v0085','v0084'],[47.45,49.55],47.93),('current_source',['v0088','v0087'],[53.69,53.42],53.42)]:
 for k in range(1,len(ordered)+1):
  for threshold in [0,.1,.5,1.0]:
   winners=[v for v,s in zip(ordered,scores) if s-parent>threshold+1e-8]; selected=ordered[:k]; recovered=len(set(winners)&set(selected)); rank.append(dict(cohort=cohort,k=k,server_win_threshold=threshold,scored_winners=len(winners),recalled_winners=recovered,recall=recovered/len(winners) if winners else None,regret=max(scores)-max(scores[:k]),counterfactual_only=True))
pd.DataFrame(rank).to_csv(O/'topk_counterfactual.csv',index=False)
coverage=json.loads((E/'registries/t3_coverage.json').read_text())
summary=dict(n_candidate_inventory=coverage['original_t3_inventory_count'],n_scored_inventory=coverage['original_t3_scored_count'],n_published_inventory=len(idx),n_local_records=len(rows),n_unique_scored_with_local=len({r['candidate'] for r in rows if r['server_score'] is not None}),n_same_target_absolute_score_pairs=0,absolute_underestimation_distribution=None,overall_false_negative_rate=None,max_observed_source_dominance_reversal_server_gap=2.10,source_dominance_reversal_incumbent_gain=1.62,source_strata_favoring_v85_all_five=sum(c['source_metrics_favor_v85']==5 for c in checks),source_strata_count=len(checks),v88_source_delta=float(pd.read_csv(V/'source_evaluation/summary.csv').set_index('model').loc['conditional','total']-baseline),v88_mab_delta=float(s['conditional']-s['baseline']),v88_server_delta=.27,v87_mab_vs_adult_delta=float(z['sevenKO_hurdle']-z['historical_adult']),v87_server_vs_v84_delta=3.87)
(O/'computed_summary.json').write_text(json.dumps(summary,indent=2));(O/'source_hashes.json').write_text(json.dumps(sources,indent=2));print(json.dumps(summary,indent=2))

# Every raw frozen-donor row is public; reaggregate without model/data caches.
raw=pd.read_csv(P/'reports/frozen_donors/METRICS.tsv',sep='\t')
metric_cols=[c for c in d.columns if c not in ['scenario','split','method']]
agg=raw.groupby(['scenario','split','method'])[metric_cols].mean().sort_index()
expected=d.set_index(['scenario','split','method'])[metric_cols].sort_index()
max_error=float(np.max(np.abs(agg.to_numpy()-expected.to_numpy())))
if max_error > 1e-12: raise ValueError(f'Frozen donor summary mismatch: {max_error}')
raw[raw.method.isin(['qtl025','dsign05'])].to_csv(O/'fixed_donor_raw_rows.csv',index=False)
small=[c for c in metric_cols if c != 'severity_r2']
agg.reset_index().query("method in ['qtl025','dsign05']")[['scenario','split','method']+small].to_csv(O/'fixed_donor_summary.csv',index=False)
code=E/'t3cpu/experiments/cpu_20261008/recheck_frozen_donors.py'
code_matches=sha(code)==json.loads(proto.read_text())['code_sha256']
if not code_matches: raise ValueError('Frozen donor original code hash mismatch')
verification=dict(frozen_donor_code_hash_matches=code_matches,summary_recomputed_from_raw_max_abs_error=max_error,raw_source_rows=len(raw),no_training_performed=True)
(O/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
(O/'source_hashes.json').write_text(json.dumps(sources,indent=2)+'\n')
