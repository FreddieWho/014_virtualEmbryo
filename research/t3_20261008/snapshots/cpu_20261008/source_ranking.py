"""Frozen matched-input signed-rank versus MSE source experiment; no target truth."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,time,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from scipy.stats import rankdata
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'third_party/veckit')]
from t3_next.five_ops import bounded_add
from t3_next.common import dense,dump,sha
from t3_next.source_roles import require_response_role
from t3_autoresearch import retained_model
from common import core_metrics as cm
threadpool_limits(limits=2)
SRC=Path('/workspace/shared/t3source');OUT=ROOT/'experiments/cpu_20261008/source_ranking';OUT.mkdir(exist_ok=True)
manifest=json.loads((SRC/'SOURCE_MANIFEST.json').read_text());require_response_role(manifest,SRC,'SIGNED_RESPONSE')
a=ad.read_h5ad(SRC/'expression.h5ad');x=dense(a.X).astype(float);labels=a.obs.condition.astype(str).to_numpy();samples=a.obs['sample'].astype(str).to_numpy()
emb=np.load(SRC/'GO_EMBEDDING.npz');ei={str(g):i for i,g in enumerate(emb['genes'])}
frozen=json.loads((ROOT/'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text());train_genes=frozen['fixed_training_genes'];held_genes=frozen['val']['genes']+frozen['test']['genes'];genes=train_genes+held_genes
assert set(genes)==set(labels)-{'ctrl'} and len(set(genes))==26
E=np.array([emb['embedding'][ei[g]] for g in genes]);sample_names=sorted(set(samples));rng=np.random.default_rng(20261008)
# Addendum committed before source scoring; original historical split respected.
protocol={'methods':['identity','mean','mse_ridge','signed_rank_ridge','shuffled_mse','shuffled_rank','retained'],'alpha':1.,'rank_target':'sign(Y)*rank(abs(Y))/500, global least-squares magnitude calibration from outer-train only','emitter':'identical bounded_add strength1, +/-log2; no post hoc outcome calibration','development':'LOPO among original17 only','confirmation':'original9 historical holdouts, all predictions fit original17; these were seen in prior project work, not pristine','train_genes':train_genes,'held_genes':held_genes,'scenarios':['pooled','sample0_to_1','sample1_to_0'],'seed':20261008,'source_sha256':sha(SRC/'expression.h5ad'),'embedding_sha256':sha(SRC/'GO_EMBEDDING.npz'),'scorer_sha256':sha(ROOT/'third_party/veckit/common/core_metrics.py'),'code_sha256':sha(__file__),'target_Gata4_labels_used':False}
dump(OUT/'FROZEN_PROTOCOL.json',protocol)

def ridge(train,query,Y,rank=False,shuffle=False,seed=0):
    Y=Y.copy()
    if shuffle:Y=Y[np.random.default_rng(seed).permutation(len(Y))]
    if rank:
        S=np.array([np.sign(y)*rankdata(np.abs(y),method='average')/len(y) for y in Y]);scale=float(np.sum(S*Y)/max(np.sum(S*S),1e-12));Z=S
    else:Z=Y;scale=1.
    mu=Z.mean(0);K=E[train]@E[train].T;k=E[query]@E[train].T
    pred=mu+k@np.linalg.solve(K+np.eye(len(train)),Z-mu)
    return pred*scale

def measure(pred,truth,ctrl):
    de=cm.de_score(pred,truth,ctrl);sev,r2=cm.severity_slope(pred,truth,ctrl)
    return {'de_score':de['score'],'de_direction':cm.de_direction(pred,truth,ctrl),'severity_abs':abs(sev),'severity_r2':r2,'mmd_u':cm.mmd_unbiased(pred,truth,seed=0),'variogram':cm.variogram_score(pred,truth,seed=0),'mse':float(np.mean((pred.mean(0)-truth.mean(0))**2)),'density':float((pred>0).mean()),'n_true_de':de['n_true']}
rows=[];arrays={}
for sn,train_samples,test_samples in [('pooled',sample_names,sample_names),('sample0_to_1',sample_names[:1],sample_names[1:]),('sample1_to_0',sample_names[1:],sample_names[:1])]:
    # Responses are equal-sample pseudobulk, always relative to same-sample NTC.
    Y=np.array([np.mean([x[(labels==g)&(samples==s)].mean(0)-x[(labels=='ctrl')&(samples==s)].mean(0) for s in train_samples],axis=0) for g in genes])
    ctrl=x[(labels=='ctrl')&np.isin(samples,test_samples)]
    for qi,g in enumerate(genes):
        ti=np.array([i for i,h in enumerate(genes[:17]) if h!=g]);stage='development_LOPO17' if qi<17 else 'historical_holdout9'
        assert qi not in ti
        predictions={'identity':np.zeros(500),'mean':Y[ti].mean(0),'mse_ridge':ridge(ti,qi,Y[ti]),'signed_rank_ridge':ridge(ti,qi,Y[ti],rank=True),'shuffled_mse':ridge(ti,qi,Y[ti],shuffle=True,seed=20261008+qi),'shuffled_rank':ridge(ti,qi,Y[ti],rank=True,shuffle=True,seed=20261008+qi),'retained':retained_model.predict({'genes':np.array(genes)[ti],'E':E[ti],'Y':Y[ti]},{'genes':np.array([g]),'E':E[[qi]]})[0]}
        truth=x[(labels==g)&np.isin(samples,test_samples)]
        for name,dg in predictions.items():
            pred=ctrl.copy() if name=='identity' else bounded_add(ctrl,dg,1.).astype(np.float32)
            r={'scenario':sn,'split':stage,'gene':g,'method':name,'train_genes':','.join(np.array(genes)[ti]),**measure(pred,truth,ctrl)};rows.append(r)
            arrays[f'{sn}__{g}__{name}']=dg
        if (qi+1)%5==0:print(sn,qi+1,'/26',flush=True)
    pd.DataFrame(rows).to_csv(OUT/'METRICS.tsv',sep='\t',index=False)
np.savez_compressed(OUT/'PREDICTED_RESPONSES.npz',**arrays)
df=pd.DataFrame(rows);metrics=['de_score','de_direction','severity_abs','mmd_u','variogram','mse','density'];summary=df.groupby(['scenario','split','method'])[metrics].mean();summary.to_csv(OUT/'SUMMARY.tsv',sep='\t');print(summary.to_string(),flush=True)
# Perturbation-level paired bootstrap, never resample cells as biological replicates.
ci=[]
for (sc,sp),group in df.groupby(['scenario','split']):
    for comparator in ['mse_ridge','mean','retained','shuffled_rank']:
        for metric in metrics[:6]:
            p=group.pivot(index='gene',columns='method',values=metric);delta=(p['signed_rank_ridge']-p[comparator]).to_numpy();delta=delta[np.isfinite(delta)];boot=np.mean(delta[rng.integers(len(delta),size=(2000,len(delta)))],axis=1)
            ci.append({'scenario':sc,'split':sp,'comparison':'rank-minus-'+comparator,'metric':metric,'mean_difference':float(np.mean(delta)),'ci_low':float(np.quantile(boot,.025)),'ci_high':float(np.quantile(boot,.975)),'perturbations':len(delta)})
dump(OUT/'BOOTSTRAP.json',ci)
dump(OUT/'COMPLETE.json',{'status':'COMPLETE','rows':len(rows),'protocol_sha256':sha(OUT/'FROZEN_PROTOCOL.json'),'metrics_sha256':sha(OUT/'METRICS.tsv'),'source_role':'SIGNED_RESPONSE','target_outcomes_used':False,'historical_holdout_is_pristine':False})
