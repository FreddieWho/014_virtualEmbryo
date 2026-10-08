"""Reproduce the frozen v0083-v0085 arrays from explicit local approved inputs.

Requires the project's base commit eb464afa7ee53d5bed7078d65bfed4f03df675b2.
No network, held-out target access, server-score fitting, or input mutation.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[k]='2'
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np,anndata as ad,pandas as pd
from threadpoolctl import threadpool_limits

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',required=True,type=Path)
p.add_argument('--wt',required=True,type=Path)
p.add_argument('--source',required=True,type=Path)
p.add_argument('--go',required=True,type=Path)
p.add_argument('--out',required=True,type=Path)
args=p.parse_args();repo=args.repo.resolve();sys.path[:0]=[str(repo),str(repo/'scripts')]
from scripts.t3_next.five import Hurdle
from scripts.t3_next.five_ops import bounded_add
from t3_autoresearch import retained_model
from t3_six.common import fit_log_multiplier
from t3_six2.deliver import route_emit
threadpool_limits(limits=2)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def dense(x): return np.asarray(x.toarray() if hasattr(x,'toarray') else x,dtype=np.float32)
assert sha(args.wt)=='149ab6df7c99ad85046c8aebebcf0c43689b3720c59ffb7cc550edcf2f13a83c'
assert sha(args.go)=='acdb554d47989a4d8230fb8acc0fc7d20ec40e12086b56ef1715afb8fee11e0d'
args.out.mkdir(parents=True,exist_ok=False)
wt=ad.read_h5ad(args.wt);wx=dense(wt.X);genes=list(wt.var_names);gi=genes.index('Gata4');cols=np.flatnonzero(np.arange(500)!=gi)
assert wx.shape==(24826,500)
rows=np.sort(np.random.default_rng(20260904).choice(len(wx),7449,replace=False));coords=np.asarray(wt.obsm['spatial_3D'])[:,:3].astype(float);types=wt.obs.celltype.astype(str).to_numpy()
m=Hurdle().fit(wx[:,[gi]],coords,types,wx[:,cols],100.)
factual,prob=m.predict(wx[rows][:,[gi]],coords[rows],types[rows]);cf,_=m.predict(np.zeros((len(rows),1),dtype=np.float32),coords[rows],types[rows]);base=wx[rows].copy();base[:,gi]=0;base[:,cols]=bounded_add(base[:,cols],cf-factual,.25)
assert np.count_nonzero(base[:,cols]!=wx[rows][:,cols])==301307
source=ad.read_h5ad(args.source);x=dense(source.X);labels=source.obs.condition.astype(str).to_numpy();assert x.shape==(5454,500) and list(source.var_names)==genes
assert hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()=='6fcbecd0da0974ad57d3f100094df765f08d53b48d9b8fa7c73f4fd0638e2575'
ctrl=x[labels=='ctrl'];assert len(ctrl)==220
split=json.loads((repo/'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text());conditions=split['fixed_training_genes']+split['val']['genes']+split['test']['genes'];assert set(conditions)==set(labels)-{'ctrl'}
emb=np.load(args.go);ei={g:i for i,g in enumerate(emb['genes'])};E=emb['embedding'];Y=np.array([x[labels==g].mean(0)-ctrl.mean(0) for g in conditions])
delta=retained_model.predict({'genes':np.array(conditions),'E':E[[ei[g] for g in conditions]],'Y':Y},{'genes':np.array(['Gata4']),'E':E[[ei['Gata4']]]})[0];beta=fit_log_multiplier(ctrl,delta);sd=np.std(Y,axis=0)
donor=max(conditions,key=lambda g:float(E[ei['Gata4']]@E[ei[g]]));donor_ko=x[labels==donor];sign=(np.sign(donor_ko.mean(0,dtype=float)-ctrl.mean(0,dtype=float))==np.sign(delta)).astype(float)
aux={'hurdle_prob':prob,'hurdle_cols':cols,'ctrl':ctrl,'donor_ko':donor_ko,'sign_gate':sign,'delta4':delta}
expected={'v0083':'938461817b8fe4cc682ff0478a044e168dbd61dc35d85d8c798126cd71399eb1','v0084':'a93f267c18afd2986e359a1d3cc6202ea1b39016cdb16401c28c47bb68e4361e','v0085':'5f83c81fc005c7d8c87132c83151c5d4b5e2fb3b79c053d8ff4cab5f22cfd839'}
result=[]
for cid,lane,params in [('v0083','o3_psb','psb'),('v0084','n1_qtl','q0.25'),('v0085','n2_dsign','g0.5')]:
 pred=route_emit(lane,params,base,beta,sd,aux);pred[:,gi]=0;h=hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()
 assert pred.shape==(7449,500) and np.isfinite(pred).all() and (pred>=0).all()
 # Byte-exact expression reproduction is checked independently of H5AD metadata.
 assert h==expected[cid],f'{cid} array mismatch: {h}; check exact dependencies and BLAS threads'
 obs=wt.obs.iloc[rows].copy();obs.index=pd.Index(np.asarray(obs.index,dtype=object),dtype=object)
 for col in obs:obs[col]=pd.Categorical(np.asarray(obs[col],dtype=object),categories=pd.Index(np.asarray(obs[col].cat.categories,dtype=object),dtype=object))
 a=ad.AnnData(X=pred,obs=obs,var=pd.DataFrame(index=pd.Index(np.asarray(genes,dtype=object),dtype=object)));a.obsm['spatial_3D']=coords[rows].astype(np.float32);a.uns['ve_contract']={'normalization':'log_normalized'};a.uns['reproduction']={'candidate_id':cid,'recipe':lane,'params':params,'donor':donor,'target_truth_used':False,'expression_sha256':h,'note':'Portable replay; metadata differs from submitted immutable artifact'}
 path=args.out/(cid+'.h5ad');a.write_h5ad(path,compression='gzip');result.append({'candidate_id':cid,'filename':path.name,'sha256':sha(path),'expression_sha256':h,'exact_expression_match':True});print(cid,'exact expression match',flush=True)
(args.out/'REPLAY_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
