import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,hashlib,time
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad,joblib
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from emitter_v88 import emit
sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common import core_metrics as cm
P=Path(__file__).parent;R=Path('/workspace/shared/t3_v87_restored');O=P/'source_evaluation';O.mkdir(exist_ok=True)
GENES=['Dnmt3a','Kmt2a','Kdm2b','Dnmt1','Dnmt3b','Ehmt2','Kmt2b'];ARMS={'baseline':(False,False),'residual':(True,False),'conditional':(False,True),'both':(True,True)};WEIGHTS={'de':.30,'direction':.25,'severity_abs':.25,'mmd':.12,'variogram':.08}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def measure(p,t,c,seed):
 s,r2=cm.severity_slope(p,t,c)
 return dict(de=cm.de_score(p,t,c)['score'],direction=cm.de_direction(p,t,c),severity_abs=abs(s),severity_r2=r2,mmd=cm.mmd_unbiased(p,t,seed=seed),variogram=cm.variogram_score(p,t,seed=seed),mse=float(((p.mean(0,dtype=float)-t.mean(0,dtype=float))**2).mean()))
# All fitting inputs explicit; raw target outcomes never present.
data={g:ad.read_h5ad(P/'source_panel/normalized'/f'{g}_whitelisted_panel10000.h5ad') for g in ['WT']+GENES}
wt=data['WT'].X;wo=data['WT'].obs;model=joblib.load(R/'inference/state_emitter.joblib')
controls={};wrng=np.random.default_rng(711)
for sex in wo.sex.unique():
 blocks=[]
 for e in wo.loc[wo.sex==sex,'embryo'].unique():
  ix=np.flatnonzero((wo.sex==sex)&(wo.embryo==e));blocks.append(wt[wrng.choice(ix,500,replace=len(ix)<500)])
 controls[sex]=np.concatenate(blocks)
cache=O/'embryo_responses.npz';meta=[];parts=[]
cache_inputs={str(g):sha(P/'source_panel/normalized'/f'{g}_whitelisted_panel10000.h5ad') for g in ['WT']+GENES}
cache_inputs.update(model=sha(R/'inference/state_emitter.joblib'),response_code=sha(P/'crossko_hurdle_v2.py'),runner=sha(__file__))
if cache.exists():
 assert json.loads((O/'CACHE_INPUTS.json').read_text())==cache_inputs, 'Stale response cache'
 z=np.load(cache);d=z['delta'];comp=z['composition'];support=z['support'];meta=json.loads((O/'embryo_responses.json').read_text())
else:
 for gene in GENES:
  a=data[gene]
  for e in sorted(a.obs.embryo.unique()):
   mask=np.asarray(a.obs.embryo==e);sex=a.obs.loc[mask,'sex'].iloc[0];r=model.summarize_response(controls[sex],a.X[mask]);parts.append(r);meta.append(dict(gene=gene,embryo=str(e),sex=str(sex)));print('response',gene,e,flush=True)
 d=np.stack([r['delta'] for r in parts]);comp=np.stack([r['composition'] for r in parts]);support=np.stack([r['support'] for r in parts]);np.savez_compressed(cache,delta=d,composition=comp,support=support);(O/'embryo_responses.json').write_text(json.dumps(meta,indent=2))
(O/'CACHE_INPUTS.json').write_text(json.dumps(cache_inputs,indent=2))
gresp={}
for g in GENES:
 ix=[i for i,m in enumerate(meta) if m['gene']==g];gresp[g]=dict(delta=d[ix].mean(0),composition=comp[ix].mean(0),support=support[ix].mean(0))
rows=[];anchors=[];rng=np.random.default_rng(241);crng=np.random.default_rng(9001)
for query in GENES:
 a=data[query];obs=a.obs;all_e=sorted(obs.embryo.unique());evaluation=all_e[1::2];truth=[];ceiling=[];control=[]
 for e in evaluation:
  rr=np.flatnonzero(obs.embryo==e);chosen=rng.choice(rr,500,replace=len(rr)<500);truth.append(a.X[chosen]);left=np.setdiff1d(rr,chosen);assert len(left)>0;ceiling.append(a.X[crng.choice(left,500,replace=len(left)<500)])
  c=controls[obs.iloc[rr[0]].sex];control.append(c[rng.choice(len(c),500,replace=False)])
 truth=np.concatenate(truth);technical_ceiling=np.concatenate(ceiling);reference=np.concatenate(control);base=reference[rng.choice(len(reference),7449,replace=True)].copy()
 train=[g for g in GENES if g!=query];response={k:np.mean([gresp[g][k] for g in train],axis=0) for k in ['delta','composition','support']};response['support']=response['support']>=.5
 preds={};receipts=[]
 for name,(res,cond) in ARMS.items():
  pred,ix=emit(model,base,response,residual=res,conditional=cond);file=O/f'{query}_{name}.h5ad';ad.AnnData(pred,var=a.var.copy()).write_h5ad(file,compression='gzip');pred=ad.read_h5ad(file).X;preds[name]=pred;receipts.append(dict(model=name,sha256=sha(file),detection=float((pred>0).mean()),donor_sha256=hashlib.sha256(ix.tobytes()).hexdigest()));print('emitted',query,name,flush=True)
 (O/f'{query}_FROZEN.json').write_text(json.dumps(dict(training_genes=train,heldout=query,evaluation_embryos=list(map(str,evaluation)),prediction_receipts=receipts,code_sha256=sha(__file__),emitter_sha256=sha(P/'emitter_v88.py'),protocol_sha256=sha(P/'PROTOCOL.md')),indent=2))
 for seed in [0,1,2]:
  floor=measure(reference,truth,reference,seed);ceil=measure(technical_ceiling,truth,reference,seed);anchors.append(dict(query=query,seed=seed,floor=floor,ceiling=ceil))
  for m in WEIGHTS:
   assert np.isfinite(floor[m]) and np.isfinite(ceil[m]), ('Nonfinite anchor',query,seed,m)
   gap=(floor[m]-ceil[m]) if m in ['severity_abs','mmd','variogram'] else (ceil[m]-floor[m])
   assert gap>1e-10, ('Invalid floor/ceiling orientation',query,seed,m,floor[m],ceil[m])
  for name,pred in preds.items():
   raw=measure(pred,truth,reference,seed);skills={m:100*cm.skill(raw[m],floor[m],ceil[m],lower_is_better=m in ['severity_abs','mmd','variogram']) for m in WEIGHTS};total=sum(WEIGHTS[m]*skills[m] for m in WEIGHTS)
   assert all(np.isfinite(raw[m]) and np.isfinite(skills[m]) for m in WEIGHTS) and np.isfinite(total), ('Nonfinite result',query,name,seed)
   row=dict(query=query,seed=seed,model=name,total=total,**raw,**{m+'_skill':v for m,v in skills.items()});rows.append(row);print(row,flush=True)
  pd.DataFrame(rows).to_csv(O/'metrics.csv',index=False);(O/'anchors.json').write_text(json.dumps(anchors,indent=2))
f=pd.DataFrame(rows);summary=f.groupby('model').mean(numeric_only=True);summary.to_csv(O/'summary.csv');q=f.groupby(['query','model']).mean(numeric_only=True);decisions=[]
for name in ['residual','conditional','both']:
 delta=q.xs(name,level='model')-q.xs('baseline',level='model');passed=bool(delta.total.mean()>0 and (delta.total>0).sum()>=4 and all(delta[m+'_skill'].mean()>=-2 for m in ['de','direction','severity_abs']));decisions.append(dict(model=name,passes=passed,mean_gain=float(delta.total.mean()),wins=int((delta.total>0).sum()),component_delta={m:float(delta[m+'_skill'].mean()) for m in WEIGHTS},per_query_gain=delta.total.to_dict()))
eligible=[d for d in decisions if d['passes']];chosen=max(eligible,key=lambda d:d['mean_gain'])['model'] if eligible else None
(O/'SELECTION.json').write_text(json.dumps(dict(chosen=chosen,decisions=decisions,scope='Adaptive source-local calibrated comparison; not official or target forecast'),indent=2));print('SELECTED',chosen,decisions,flush=True)
