"""Full-panel matched source-reference metrics; never hidden-stage forecasts."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,time,resource,gc
from pathlib import Path
import anndata as ad,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'third_party/veckit/common'))
from core_metrics import mmd_unbiased,variogram_score,energy_distance
from build_cp10k import sha
p=argparse.ArgumentParser();p.add_argument('--arms',required=True);p.add_argument('--reference95',required=True);p.add_argument('--out',required=True);a=p.parse_args()
t=time.time();arms=json.loads(Path(a.arms).read_text());source=ad.read_h5ad(a.reference95,backed='r');ix=np.sort(np.random.default_rng(20261009).choice(source.n_obs,2000,replace=False));ref=source.X[ix].toarray().astype(np.float32);genes=np.asarray(source.var_names);source.file.close()
r={'interpretation':'Same released E9.5 source reference and32,285 genes for every arm; no hidden E10.5 target and no reliable future-score prediction','reference95_sha256':sha(a.reference95),'reference_cells':2000,'full_panel':32285,'arms':{}}
for name,path in arms.items():
 obj=ad.read_h5ad(path);assert np.array_equal(obj.var_names,genes);X=obj.X.toarray().astype(np.float32);del obj
 rows=[]
 for seed in [20261009,20261010,20261011]:
  row={'seed':seed,'mmd_u':mmd_unbiased(X,ref,seed=seed),'variogram':variogram_score(X,ref,seed=seed),'energy_distance':energy_distance(X,ref,seed=seed)};rows.append(row);print(name,row,flush=True)
 r['arms'][name]={'artifact_sha256':sha(path),'metrics':rows};del X;gc.collect();Path(a.out).write_text(json.dumps(r,indent=2))
r.update(wall_seconds=time.time()-t,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);Path(a.out).write_text(json.dumps(r,indent=2));print('DONE',a.out,flush=True)
