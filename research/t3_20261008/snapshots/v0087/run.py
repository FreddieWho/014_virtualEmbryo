import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,hashlib,time
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans
from threadpoolctl import threadpool_limits
threadpool_limits(2)
P=Path(__file__).parent;D=Path('/workspace/shared/virtual_embryo_data');sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit')
from common import core_metrics as cm
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dense(a):return a.toarray().astype('float32') if hasattr(a,'toarray') else np.asarray(a,dtype='float32')
def norm(x,gi):
 c=np.expm1(np.maximum(x,0).astype('float64'));c[:,gi]=0;s=c.sum(1);assert np.all(s>0);return np.log1p(c*(10000/s)[:,None]).astype('float32')
def measure(p,t,r):
 s,r2=cm.severity_slope(p,t,r);dp=p.mean(0,dtype=float)-r.mean(0,dtype=float);dt=t.mean(0,dtype=float)-r.mean(0,dtype=float)
 return dict(de=float(cm.de_score(p,t,r)['score']),direction=float(cm.de_direction(p,t,r)),severity_log=float(s),severity_abs=float(abs(s)),severity_r2=float(r2),slope_all=float(dp@dt/(dt@dt)),mmd=float(cm.mmd_unbiased(p,t,seed=0)),variogram=float(cm.variogram_score(p,t,seed=0)),mse=float(np.mean((p.mean(0,dtype=float)-t.mean(0,dtype=float))**2)),strong_sign=float(np.mean(np.sign(dp[abs(dt)>=.25])==np.sign(dt[abs(dt)>=.25]))))
def sample_states(pool,lab,states,rng,fallback,flab):
 ix=[];out=[]
 for c in states:
  candidates=np.flatnonzero(lab==c)
  if len(candidates)>=20:out.append(pool[rng.choice(candidates)])
  else:out.append(fallback[rng.choice(np.flatnonzero(flab==c))])
 return np.asarray(out)
w=ad.read_h5ad(D/'E9.5.h5ad');k=ad.read_h5ad(D/'E9.5_mab21l2_ko.h5ad');g=ad.read_h5ad(D/'E8.75.h5ad');assert np.array_equal(w.var_names,k.var_names) and np.array_equal(w.var_names,g.var_names)
X,Y,G=map(lambda a:dense(a.X),(w,k,g));gi=list(w.var_names).index('Mab21l2');N=7449
inputs=[D/'E9.5.h5ad',D/'E9.5_mab21l2_ko.h5ad',D/'E8.75.h5ad',Path('/workspace/shared/t3new_20261008/mab_anchored_v2.npy'),Path('/workspace/shared/t3repo/third_party/veckit/common/core_metrics.py'),P/'PROTOCOL.md',Path(__file__)]
(P/'INPUT_HASHES.json').write_text(json.dumps({str(p):sha(p) for p in inputs},indent=2))
def summary(z):
 s=np.expm1(z.astype(float)).sum(1);return dict(shape=list(z.shape),row_expm1_sum_quantiles=np.quantile(s,[0,.01,.5,.99,1]).tolist(),detection=float((z>0).mean()),positive_quantiles=np.quantile(z[z>0],[.01,.5,.99]).tolist())
(P/'OBSERVATION.json').write_text(json.dumps({a:summary(b) for a,b in [('WT',X),('KO',Y),('Gata_WT',G)]},indent=2))
sec=pd.to_numeric(k.obs.section).to_numpy();rng=np.random.default_rng(241);wp=rng.permutation(len(X));gp=rng.permutation(500);genehalves=np.array_split(gp,2);rows=[];alignment=[];checks=[]
for fold in range(2):
 tr=wp[fold::2];te=wp[1-fold::2];kt=np.flatnonzero(sec%2==fold);kv=np.flatnonzero(sec%2!=fold);features=genehalves[fold];evalg=genehalves[1-fold]
 pca=PCA(n_components=12,svd_solver='randomized',random_state=241).fit(X[tr][:,features]);z=pca.transform(X[tr][:,features]);km=MiniBatchKMeans(n_clusters=32,batch_size=1024,n_init=3,random_state=241).fit(z)
 def labels(A):
  zz=pca.transform(A[:,features]);ll=km.predict(zz);dist=np.linalg.norm(zz-km.cluster_centers_[ll],axis=1);return ll,dist
 wl,wd=labels(X[tr]);vl,vd=labels(X[te]);kl,kd=labels(Y[kt]);tl,td=labels(Y[kv]);gl,gd=labels(G)
 threshold=np.quantile(wd,.95);nw=np.bincount(wl,minlength=32);nk=np.bincount(kl,minlength=32);pw=nw/nw.sum();pk=nk/nk.sum();support=(nw>=20)&(nk>=20)
 alignment.append(dict(fold=fold,wt_train=len(tr),wt_test=len(te),ko_train=len(kt),ko_test=len(kv),features=features.tolist(),evaluation_genes=evalg.tolist(),WT_state_counts=nw.tolist(),KO_state_counts=nk.tolist(),distance_threshold=float(threshold),ko_train_outside=float((kd>threshold).mean()),ko_test_outside=float((td>threshold).mean()),Gata_WT_outside=float((gd>threshold).mean()),unsupported_WT_mass=float(pw[~support].sum()),unsupported_KO_mass=float(pk[~support].sum())))
 wm=np.stack([X[tr][wl==c].mean(0) for c in range(32)]);glob=Y[kt].mean(0)-X[tr].mean(0);delta=np.stack([Y[kt][kl==c].mean(0)-wm[c] if support[c] else glob for c in range(32)]);lam=nk/(nk+50);delta=lam[:,None]*delta+(1-lam[:,None])*glob
 rng=np.random.default_rng(900+fold);baseix=rng.choice(te,N,replace=False);base=X[baseix];bl,_=labels(base);states=rng.choice(32,N,p=pk)
 preds={'identity':base.copy(),'global_shift':np.maximum(base+glob,0),'composition':sample_states(X[tr],wl,states,rng,X[tr],wl),'state_shift':np.maximum(base+delta[bl],0),'within_joint':sample_states(Y[kt],kl,bl,rng,X[tr],wl),'combined_joint':sample_states(Y[kt],kl,states,rng,X[tr],wl),'state_gene_shuffle':np.maximum(base+delta[bl][:,rng.permutation(500)],0)}
 # Save learned model and split indices, enabling exact provenance inspection.
 np.savez_compressed(P/f'model_fold{fold}.npz',WT_train=tr,WT_test=te,KO_train=kt,KO_test=kv,features=features,pca_mean=pca.mean_,pca_components=pca.components_,centers=km.cluster_centers_,global_delta=glob,state_delta=delta,WT_proportions=pw,KO_proportions=pk,base_indices=baseix)
 for name,raw in preds.items():
  pred=norm(raw,gi);a=ad.AnnData(pred,obs=pd.DataFrame(index=[f'fold{fold}_{i}' for i in range(N)]),var=w.var.copy());a.obsm['spatial_3D']=np.asarray(w.obsm['spatial_3D'])[baseix].copy();a.uns['scope']='Released Mab21l2 same-perturbation technical holdout. Not a Gata4 candidate.';file=P/f'fold{fold}_{name}.h5ad';a.write_h5ad(file,compression='gzip');r=ad.read_h5ad(file);assert np.array_equal(r.X,pred);assert np.array_equal(r.var_names,w.var_names);assert np.all(np.isfinite(r.X)) and np.all(r.X>=0) and np.all(r.X[:,gi]==0);assert np.max(abs(np.expm1(r.X.astype(float)).sum(1)-10000))<.01
  checks.append(dict(fold=fold,model=name,sha256=sha(file),serialization='PASS',normalization='PASS',zero_to_positive=int(np.sum((base==0)&(pred>0))),positive_to_zero=int(np.sum((base>0)&(pred==0))),**summary(pred)))
  for label,ii in [('full_panel',np.arange(500)),('alignment_heldout_genes',evalg)]:
   row=dict(fold=fold,model=name,metric_panel=label,**measure(pred[:,ii],Y[kv][:,ii],X[te][:,ii]));rows.append(row)
  pd.DataFrame(rows).to_csv(P/'metrics.csv',index=False);print(fold,name,rows[-2],flush=True)
 baseline=np.load('/workspace/shared/t3new_20261008/mab_anchored_v2.npy')
 for label,ii in [('full_panel',np.arange(500)),('alignment_heldout_genes',evalg)]:rows.append(dict(fold=fold,model='historical_adult_anchored',metric_panel=label,**measure(baseline[:,ii],Y[kv][:,ii],X[te][:,ii])))
 (P/'ALIGNMENT.json').write_text(json.dumps(alignment,indent=2));(P/'CHECKS.json').write_text(json.dumps(checks,indent=2));pd.DataFrame(rows).to_csv(P/'metrics.csv',index=False)
print(pd.DataFrame(rows).groupby(['metric_panel','model'])[['de','direction','severity_abs','mmd','variogram','mse']].mean().to_string(),flush=True)
(P/'COMPLETE.json').write_text(json.dumps(dict(status='completed',models=14,folds=2,metrics=len(rows),no_hidden_outcomes=True,no_submission=True,blocks_submission=False),indent=2))
