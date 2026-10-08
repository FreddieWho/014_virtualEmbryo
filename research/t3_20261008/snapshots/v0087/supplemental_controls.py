# Audit-added controls, after first-fold result. Not part of model selection.
import os
for x in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[x]='2'
import json,sys
from pathlib import Path
import anndata as ad,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
threadpool_limits(2)
P=Path(__file__).parent;sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common import core_metrics as cm
w=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad');k=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5_mab21l2_ko.h5ad');X=w.X.toarray() if hasattr(w.X,'toarray') else w.X;Y=k.X.toarray() if hasattr(k.X,'toarray') else k.X;gi=list(w.var_names).index('Mab21l2');rows=[]
for fold in range(2):
 z=np.load(P/f'model_fold{fold}.npz');rr=np.random.default_rng(515+fold).choice(z['KO_train'],7449,replace=True);raw=Y[rr].copy();c=np.expm1(raw.astype(float));c[:,gi]=0;closed=np.log1p(c*10000/c.sum(1)[:,None]).astype('float32');preds={'literal_WT':X[z['base_indices']].copy(),'unconditional_KO_ceiling_raw':raw,'unconditional_KO_ceiling_zero_closed':closed}
 for name,p in preds.items():
  a=ad.AnnData(p,var=w.var.copy());a.obsm['spatial_3D']=np.asarray(w.obsm['spatial_3D'])[z['base_indices']];a.uns['scope']='Technical ceiling/control, not deployable Gata4';f=P/f'supp_fold{fold}_{name}.h5ad';a.write_h5ad(f,compression='gzip');p=ad.read_h5ad(f).X;assert np.array_equal(p,preds[name])
  for label,ii in [('full_panel',np.arange(500)),('alignment_heldout_genes',np.setdiff1d(np.arange(500),z['features']))]:
   pp=p[:,ii];t=Y[z['KO_test']][:,ii];r=X[z['WT_test']][:,ii];s,r2=cm.severity_slope(pp,t,r);rows.append(dict(fold=fold,model=name,metric_panel=label,de=cm.de_score(pp,t,r)['score'],direction=cm.de_direction(pp,t,r),severity_abs=abs(s),severity_log=s,severity_r2=r2,mmd=cm.mmd_unbiased(pp,t,seed=0),variogram=cm.variogram_score(pp,t,seed=0),mse=float(np.mean((pp.mean(0,dtype=float)-t.mean(0,dtype=float))**2))))
  pd.DataFrame(rows).to_csv(P/'supplemental_metrics.csv',index=False);print(rows[-2],flush=True)
print('COMPLETE',flush=True)
