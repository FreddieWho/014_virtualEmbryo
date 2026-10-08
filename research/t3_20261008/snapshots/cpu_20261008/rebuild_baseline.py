"""Rebuild historical algorithm on public WT, without asserting byte identity."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[k]='2'
import sys, json, time, hashlib, pickle
from pathlib import Path
import numpy as np
import anndata as ad
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.t3_next.five import Hurdle, type_baseline
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.common import dense,dump,sha
threadpool_limits(limits=2)
OUT=ROOT/'experiments/cpu_20261008/baseline';OUT.mkdir(exist_ok=True)
a=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E8.75.h5ad')
x=dense(a.X); genes=list(a.var_names);gi=genes.index('Gata4');cols=np.flatnonzero(np.arange(500)!=gi)
rows=np.sort(np.random.default_rng(20260904).choice(a.n_obs,7449,replace=False))
coords=np.asarray(a.obsm['spatial_3D'])[:,:3].astype(float);types=a.obs.celltype.astype(str).to_numpy();act=x[:,[gi]];y=x[:,cols]
blocks=np.searchsorted(np.quantile(coords[:,2],[.25,.5,.75]),coords[:,2],side='right')
report={'source_sha256':sha('/workspace/shared/virtual_embryo_data/E8.75.h5ad'),'row_seed':20260904,'row_indices_sha256':hashlib.sha256(rows.tobytes()).hexdigest(),'rows':len(rows),'full_wt':len(x),'Gata4_positive_rows':int((x[rows,gi]>0).sum()),'n_celltypes':len(set(types)),'algorithm':'v0048 frozen alpha100 strength0.25; rebuilt historical sampler, not asserted artifact byte-identical','folds':[]}
print(json.dumps(report),flush=True)
for fold in sorted(set(blocks)):
 t=time.time(); tr=blocks!=fold;te=~tr
 m=Hurdle().fit(act[tr],coords[tr],types[tr],y[tr],100.)
 pred,p=m.predict(act[te],coords[te],types[te]);b=type_baseline(y,types,tr,te);bp=type_baseline((y>0).astype(float),types,tr,te)
 r={'fold':int(fold),'mse':float(np.mean((pred-y[te])**2)),'type_mean_mse':float(np.mean((b-y[te])**2)),'brier':float(np.mean((p-(y[te]>0))**2)),'type_brier':float(np.mean((bp-(y[te]>0))**2)),'entries':int(y[te].size),'seconds':time.time()-t};report['folds'].append(r);dump(OUT/'report.json',report);print(r,flush=True)
t=time.time();m=Hurdle().fit(act,coords,types,y,100.)
base=x[rows].copy(); zero=base.copy();zero[:,gi]=0
factual,_=m.predict(act[rows],coords[rows],types[rows]);cf,_=m.predict(np.zeros_like(act[rows]),coords[rows],types[rows]);hurdle=zero.copy();hurdle[:,cols]=bounded_add(zero[:,cols],cf-factual,.25)
assert np.array_equal(hurdle[x[rows,gi]==0][:,cols],zero[x[rows,gi]==0][:,cols])
np.save(OUT/'carrier_rows.npy',rows)
with (OUT/'hurdle_model.pkl').open('wb') as f:pickle.dump(m,f,protocol=5)
for name,X in [('wt_identity',base),('genotype_zero',zero),('hurdle_rebuild',hurdle)]:
 b=ad.AnnData(X=np.asarray(X,dtype=np.float32),obs=a.obs.iloc[rows].copy(),var=a.var.copy());b.obsm['spatial_3D']=coords[rows].astype(np.float32);b.uns['ve_contract']={'normalization':'log_normalized'};b.uns['cpu_rebuild']={'source_sha256':report['source_sha256'],'row_seed':20260904,'target_used':False,'method':name}
 p=OUT/(name+'.h5ad');b.write_h5ad(p,compression='gzip');report[name]={'path':str(p),'sha256':sha(p),'changed_entries_vs_zero':int(np.count_nonzero(X!=zero)),'downstream_changed_rows':int(np.any(X[:,cols]!=zero[:,cols],axis=1).sum()),'density':float((X>0).mean())}
report['final_fit_seconds']=time.time()-t;dump(OUT/'report.json',report);print(json.dumps(report),flush=True)
