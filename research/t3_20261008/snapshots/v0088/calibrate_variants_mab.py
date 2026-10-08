import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='2'
import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from threadpoolctl import threadpool_limits
threadpool_limits(2)
sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common import core_metrics as cm
P=Path(__file__).parent;O=P/'deployment';w=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad');k=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5_mab21l2_ko.h5ad');X=w.X.toarray() if hasattr(w.X,'toarray') else w.X;Y=k.X.toarray() if hasattr(k.X,'toarray') else k.X;ix=np.sort(np.random.default_rng(20260904).choice(len(X),7449,replace=False));preds={name:ad.read_h5ad(O/f'mab_{name}.h5ad').X for name in ['baseline','residual','conditional','both']};weights={'de':.30,'direction':.25,'severity_abs':.25,'mmd':.12,'variogram':.08};rows=[];anchors=[]
def measure(p,t,seed):
 s,r2=cm.severity_slope(p,t,X);de=cm.de_score(p,t,X);up,dn,_=cm.de_genes(t,X);ind=np.r_[up,dn].astype(int);dp=cm.pseudobulk(p)-cm.pseudobulk(X);dt=cm.pseudobulk(t)-cm.pseudobulk(X);beta=float(dt[ind]@dp[ind]/(dt[ind]@dt[ind]));return dict(de=de['score'],direction=cm.de_direction(p,t,X),severity_abs=abs(s),severity_log=s,severity_r2=r2,beta_unthresholded=beta,beta_from_score=float(np.exp(s)),n_up=de['n_up'],n_down=de['n_dn'],mmd=cm.mmd_unbiased(p,t,seed=seed),variogram=cm.variogram_score(p,t,seed=seed))
for seed in [0,1,2]:
 perm=np.random.default_rng(seed).permutation(len(Y));h=len(Y)//2;truth=Y[perm[h:]];ceiling=measure(Y[perm[:h]],truth,seed);floor=measure(X,truth,seed);anchors.append(dict(seed=seed,ceiling=ceiling,floor=floor,prediction_rows=h,truth_rows=len(Y)-h,reference_rows=len(X)))
 for name,p in preds.items():
  raw=measure(p,truth,seed);skills={m:cm.skill(raw[m],floor[m],ceiling[m],lower_is_better=m in ['severity_abs','mmd','variogram']) for m in weights};total=100*sum(weights[m]*skills[m] for m in weights);r=dict(seed=seed,model=name,local_total=total,**raw,**{m+'_skill':100*s for m,s in skills.items()});rows.append(r);print(r,flush=True)
 pd.DataFrame(rows).to_csv(O/'MAB_LOCAL_CALIBRATION.csv',index=False);(O/'MAB_LOCAL_CALIBRATION_ANCHORS.json').write_text(json.dumps(anchors,indent=2))
result=dict(scope='Custom public-core local Mab split-half calibration, NOT official score or Gata4 forecast',weights=weights,protocol_sha256=hashlib.sha256((P/'PROTOCOL.md').read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),summary=pd.DataFrame(rows).groupby('model').local_total.agg(['mean','std','min','max']).to_dict('index'),paired_new_minus_old={name:(pd.DataFrame(rows).pivot(index='seed',columns='model',values='local_total')[name]-pd.DataFrame(rows).pivot(index='seed',columns='model',values='local_total').baseline).tolist() for name in ['residual','conditional','both']});(O/'MAB_LOCAL_CALIBRATION_SUMMARY.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
