"""Source-only per-state row-complexity diagnostic; not a target estimate."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json
from pathlib import Path
import anndata as ad,numpy as np
p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--states',required=True);p.add_argument('--official85',required=True);p.add_argument('--official95',required=True);p.add_argument('--out',required=True);a=p.parse_args()
parent=ad.read_h5ad(a.parent);states=np.load(a.states).astype(str);pc=np.asarray((parent.X>0).sum(1)).ravel();source={}
for stage,path in [('8.5',a.official85),('9.5',a.official95)]:
 obj=ad.read_h5ad(path,backed='r');counts=[]
 for lo in range(0,obj.n_obs,256):counts.extend(np.asarray((obj.X[lo:lo+256]>0).sum(1)).ravel().tolist())
 labels=obj.obs.celltype.astype(str).to_numpy();obj.file.close();source[stage]=(np.asarray(counts),labels)
rows=[]
for state in sorted(set(states)):
 r={'state':state,'prediction_rows':int((states==state).sum()),'prediction_detection_quantiles':np.quantile(pc[states==state],[0,.01,.5,.95,.99,1]).tolist()}
 for stage,(counts,labels) in source.items():
  c=counts[labels==state];r['source'+stage+'_rows']=len(c);r['source'+stage+'_quantiles']=np.quantile(c,[0,.01,.5,.95,.99,1]).tolist() if len(c) else []
  if len(c):r['prediction_above_source'+stage+'_max']=int((pc[states==state]>c.max()).sum())
 rows.append(r)
out={'status':'SOURCE_REFERENCE_ONLY','rows':rows,'future_stage_complexity_not_inferred':True,'description':'The same v94/v96 zero-support pattern; normalization does not change detected-gene counts'}
Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
