"""Recompute T2 audit tables from frozen score receipts; no scorer/model runs."""
import csv,json,re,hashlib,itertools,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_support import parse_args, logical_source
args = parse_args("t2")
R=args.evidence_dir/"t3repo"; O=args.output_dir
O.mkdir(parents=True, exist_ok=True)
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr,pearsonr,kendalltau,binomtest
idx=list(csv.DictReader(open(args.evidence_dir/'registries/t2_heart_extrap.tsv'),delimiter='\t')); idx={r['version']:r for r in idx if r['board']=='T2:heart:val_extrap'}
rows=json.load(open(R/'.auto/calibration/calibration_proxy_validity.json'))['rows']
for r in rows:
 r['version']=re.search(r'v\d{4}',r['label']).group();r['local_source']='.auto/calibration/calibration_proxy_validity.json'; r['precision']='full recorded composite; rounded per-channel gains';r['family']='historical_nonQTE'
maps=list(csv.DictReader(open(R/'.auto/stage_routec/RUN_ID_MAP.tsv'),delimiter='\t'))
for m in maps:
 v=re.search(r'v\d{4}',m['filename']).group();rows.append(dict(version=v,label=idx[v]['method'],composite=float(m['local_composite']),server_board=float(idx[v]['server_score']),guards=v!='v0027',local_source='.auto/stage_routec/RUN_ID_MAP.tsv',precision='composite rounded to 3-4 decimals in immutable manifest',family='QTE'))
for r in rows:
 v=r['version'];r.update(candidate_sha256=idx[v]['sha256'],candidate_path=idx[v]['path'],local_protocol='E9.5 cardiac-subset proxy; final E10.5 prediction scored on observed E9.5, not held-out forecasting',local_seed=20260916,local_metric='100 * mean winsorized relative raw metric gains, 8 channels',local_target='E9.5 cardiac subset',server_target='E10.5 heart',server_metric='official board skill aggregate',identity_quality='historical ID/path linked to current registry SHA; archived raw scorer JSON absent, no new byte audit',reference_version='v0001',reference_sha256=idx['v0001']['sha256'],comparison_kind='baseline-relative comparator; not claiming every baseline is direct parent',local_delta=r['composite'],server_delta=round(r['server_board']-50.53,8),included='rank/threshold diagnostic only; no direct point-scale errors',local_negative=r['composite']<0,server_improves=r['server_board']>50.63,source_ref='5c1bcfb625952db8c773b58ddff40cf966c5e6f9')
fields=sorted(set().union(*(r.keys() for r in rows)) - {'gains'})
with open(O/'historical_paired_audit.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in rows)
def stats(rs):
 x=np.array([r['composite'] for r in rs]);y=np.array([r['server_board'] for r in rs]);n=len(x)
 rho=spearmanr(x,y);pear=pearsonr(x,y)
 pairs=[np.sign((x[i]-x[j])*(y[i]-y[j])) for i,j in itertools.combinations(range(n),2) if x[i]!=x[j] and y[i]!=y[j]]
 pred=[];base=[]
 for i in range(n):
  z=np.arange(n)!=i; b=np.polyfit(x[z],y[z],1);pred.append(float(np.polyval(b,x[i])));base.append(float(np.mean(y[z])))
 err=np.array(pred)-y
 rng=np.random.default_rng(args.bootstrap_seed);boots=[]
 for _ in range(args.bootstrap_resamples):
  z=rng.integers(n,size=n)
  if np.std(x[z]) and np.std(y[z]):boots.append(float(spearmanr(x[z],y[z]).statistic))
 return dict(n=n,pearson=float(pear.statistic),spearman=float(rho.statistic),spearman_p=float(rho.pvalue),spearman_bootstrap_ci95=np.quantile(boots,[.025,.975]).tolist(),kendall_tau_b=float(kendalltau(x,y).statistic),pairwise_concordant=sum(p>0 for p in pairs),pairwise_nontied=len(pairs),pairwise_concordance=sum(p>0 for p in pairs)/len(pairs),loocv_linear_mae=float(np.mean(abs(err))),loocv_linear_rmse=float(np.sqrt(np.mean(err**2))),loocv_mean_baseline_mae=float(np.mean(abs(np.array(base)-y))),loocv_mean_baseline_rmse=float(np.sqrt(np.mean((np.array(base)-y)**2))),loocv_positive_residual_max=float(np.max(y-np.array(pred))),loocv_note='fitted predictions in server points, not raw local-minus-server error; exploratory dependent convenience sample',predictions=pred)
s={k:stats(rs) for k,rs in [('all17',rows),('nonbaseline16',rows[1:]),('old12',rows[:12]),('QTE5',rows[12:])]}
nonbase=rows[1:];win=[r for r in nonbase if r['server_improves']]
s['thresholds']=[]
for threshold in [0,1]:
 for guard in [False,True]:
  selected=[r for r in nonbase if r['composite']>threshold and (r['guards'] or not guard)]
  caught=[r for r in win if r in selected];ci=binomtest(len(caught),len(win)).proportion_ci()
  s['thresholds'].append(dict(local_threshold=threshold,require_guards=guard,selected_n=len(selected),winner_n=len(win),retained_winners=len(caught),recall=len(caught)/len(win),nominal_exact_recall_ci95=[ci.low,ci.high],selected_winner_precision=len(caught)/len(selected) if selected else None,missed=[r['version'] for r in win if r not in selected]))
s['false_negative_sign']=[{k:r[k] for k in ['version','composite','server_board','server_delta','guards']} for r in win if r['composite']<0]
s['cautions']=['Bootstrap/binomial intervals nominal only: dependent adaptive selected candidates, not unbiased future population','No same-scale local-to-server MAE/RMSE/bias: raw-relative composite is not server skill points','No universal false-negative rate: unsubmitted local rejects lack server outcomes']
json.dump(s,open(O/'statistics.json','w'),indent=2,default=lambda x:x.item())
# Each submitted extrap candidate accounted for, including exclusions.
with open(O/'all_extrap_inclusion_audit.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=['version','method','sha256','server_score','inclusion','reason']);w.writeheader()
 for v,r in idx.items():
  reason='historical 17 cohort' if any(x['version']==v for x in rows) else ('no server score' if not r['server_score'] else 'different protocol or no paired local values recovered; excluded from historical17')
  if v=='v0036':reason='new earlier-stage model has raw dev/reserve metrics and one server outcome; reconstructed v30 comparator cannot be joined to historical v30'
  w.writerow(dict(version=v,method=r['method'],sha256=r['sha256'],server_score=r['server_score'],inclusion='include_rank_only' if any(x['version']==v for x in rows) else 'exclude_pooled_statistics',reason=reason))
# New run: retain every actual score call as an audit record; seeds are not candidate outcomes.
D=args.evaluation_dir or args.evidence_dir/'t2_heart_extra_20261008/evaluation';new=[]
if len(list(D.glob('*_s*.json'))) != 42: raise ValueError('Expected all 42 frozen T2 score receipts')
for p in sorted(D.glob('*_s*.json')):
 d=json.load(open(p));m=re.match(r'(dev|reserve)_(.*)_s(\d+)\.json',p.name)
 if not m:continue
 for metric,value in d['metrics'].items():
  new.append(dict(partition=m[1],lane=m[2],seed=m[3],metric=metric,value=value,source=logical_source(p,args.evidence_dir),scorer_sha256=d.get('scorer_sha256'),target='E9.5',candidate_mapping='v0036 earlier-stage analog' if m[2]=='endmatched' else 'reconstructed recipe, NOT exact v0030' if m[2]=='incumbent_recipe' else 'unsubmitted control',pooled_inclusion='excluded: raw values vs skill, one server candidate, seed pseudoreplication'))
with open(O/'new_run_raw_audit.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=new[0]);w.writeheader();w.writerows(new)
print(json.dumps(s,indent=2,default=lambda x:x.item()))
