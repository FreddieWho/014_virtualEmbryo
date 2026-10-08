import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,time,json
from pathlib import Path
import numpy as np,anndata as ad
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'third_party/veckit')]
from scripts.t3_next.five import Hurdle
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.common import dense,dump,sha
from common import core_metrics as cm
threadpool_limits(limits=2)
OUT=ROOT/'experiments/cpu_20261008/mab_diagnostic';OUT.mkdir(exist_ok=True)
wtpath=Path('/workspace/shared/virtual_embryo_data/E9.5.h5ad');kopath=Path('/workspace/shared/virtual_embryo_data/E9.5_mab21l2_ko.h5ad')
a=ad.read_h5ad(wtpath);x=dense(a.X);genes=list(a.var_names);gi=genes.index('Mab21l2');cols=np.flatnonzero(np.arange(500)!=gi)
act=x[:,[gi]];coords=np.asarray(a.obsm['spatial_3D'])[:,:3].astype(float);types=a.obs.celltype.astype(str).to_numpy()
t=time.time();m=Hurdle().fit(act,coords,types,x[:,cols],100.)
factual,_=m.predict(act,coords,types);cf,_=m.predict(np.zeros_like(act),coords,types)
zero=x.copy();zero[:,gi]=0;pred=zero.copy();pred[:,cols]=bounded_add(zero[:,cols],cf-factual,.25)
# Freeze predictions BEFORE loading permitted KO outcome.
np.save(OUT/'hurdle_full_prediction.npy',pred)
report={'protocol_sha256':sha(ROOT/'experiments/cpu_20261008/PROTOCOL.md'),'wt_sha256':sha(wtpath),'prediction_sha256':sha(OUT/'hurdle_full_prediction.npy'),'fit_seconds':time.time()-t,'fit_rows':len(x),'changed_rows':int(np.any(pred[:,cols]!=x[:,cols],axis=1).sum()),'training_KO_used':False,'outcome_role':'released Mab21l2 only; a single intervention, not independent Gata4 evidence','metrics':[]};dump(OUT/'FROZEN_PREDICTION.json',report)
ko=ad.read_h5ad(kopath);assert list(ko.var_names)==genes;truth=dense(ko.X);report['KO_sha256']=sha(kopath);report['KO_genotypes']=list(ko.obs.genotype.astype(str).unique());report['KO_samples']=ko.obs.sample_id.astype(str).value_counts().to_dict()
rows=np.sort(np.random.default_rng(20260904).choice(len(x),7449,replace=False))
for name,p in [('full_wt_identity',x),('sampled_wt_identity',x[rows]),('gene_zero',zero),('hurdle',pred)]:
 t=time.time();de=cm.de_score(p,truth,x);sev,r2=cm.severity_slope(p,truth,x)
 r={'method':name,'de':de,'direction':cm.de_direction(p,truth,x),'severity':sev,'severity_r2':r2,'mmd':cm.mmd_unbiased(p,truth,seed=0),'variogram':cm.variogram_score(p,truth,seed=0),'response_mse':float(np.mean((p.mean(0,dtype=float)-truth.mean(0,dtype=float))**2)),'density':float((p>0).mean()),'seconds':time.time()-t}
 report['metrics'].append(r);dump(OUT/'RESULT.json',report);print(r,flush=True)
