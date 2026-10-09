"""Released-source diagnostics only; never a future-stage score prediction."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,hashlib,gc,time,resource
from pathlib import Path
import numpy as np,anndata as ad
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'third_party/veckit/common'))
from core_metrics import mmd_unbiased,variogram_score,energy_distance
from normalization import restore_cp10k

def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--candidate',required=True);p.add_argument('--official85',required=True);p.add_argument('--official95',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 t=time.time();parent=ad.read_h5ad(a.parent);alt=ad.read_h5ad(a.candidate)
 assert parent.shape==alt.shape==(5118,32285)
 source=ad.read_h5ad(a.official95,backed='r');rng=np.random.default_rng(20261009);ix=np.sort(rng.choice(source.n_obs,2000,replace=False));ref=source.X[ix].toarray().astype(np.float32)
 # All original source cells contribute to the full-panel pseudobulk.
 refsum=np.zeros(source.n_vars);n=source.n_obs
 for lo in range(0,n,256):refsum+=np.asarray(source.X[lo:lo+256].astype(np.float64).sum(0)).ravel()
 source.file.close();refmean=refsum/n
 beforemean=np.asarray(parent.X.astype(np.float64).mean(0)).ravel();aftermean=np.asarray(alt.X.astype(np.float64).mean(0)).ravel()
 d0=beforemean-refmean;d1=aftermean-refmean
 substantial=(np.abs(d0)>=.01)|(np.abs(d1)>=.01)
 out={'interpretation':'Released E9.5 source-reference diagnostic; not hidden E10.5 truth, not forecast accuracy or server-score prediction','full_panel':32285,'source_reference_cells':len(ref),'source_reference_indices_sha256':hashlib.sha256(ix.astype('<i8').tobytes()).hexdigest(),'full_source_pseudobulk_changes':{'substantial_reference_change_genes':int(substantial.sum()),'direction_flips_abs_threshold_0_01':int(((np.sign(d0)!=np.sign(d1))&substantial).sum()),'max_delta_change':float(np.abs(d1-d0).max()),'pseudobulk_l2_shift':float(np.linalg.norm(d1-d0))},'metrics':{},'controls':{}}
 # One matrix dense at a time, and reuse reference.
 for tag,mat in [('exact_v94',parent.X),('cp10k_v96',alt.X)]:
  X=mat.toarray().astype(np.float32);out['metrics'][tag]=[]
  for seed in [20261009,20261010,20261011]:
   r={'seed':seed,'mmd_u':mmd_unbiased(X,ref,seed=seed),'variogram':variogram_score(X,ref,seed=seed),'energy_distance':energy_distance(X,ref,seed=seed)};out['metrics'][tag].append(r);print(tag,r,flush=True)
  del X;gc.collect()
 source=ad.read_h5ad(a.official85,backed='r');control=source.X[:512].tocsr();source.file.close()
 fixed,m=restore_cp10k(control);out['controls']['official85_normalization_max_abs_delta']=float(np.abs(fixed.data-control.data).max())
 # Deterministic range covers the exact parent's empirical row-mass range.
 scales=np.linspace(0.804025,2.349021,512);bad=control.astype(np.float64)
 bad.data=np.expm1(bad.data)*np.repeat(scales,np.diff(bad.indptr));bad.data=np.log1p(bad.data)
 repaired,_=restore_cp10k(bad);out['controls']['synthetic_known_row_scale_repair_max_abs_delta']=float(np.abs(repaired.data-control.data).max())
 assert out['controls']['official85_normalization_max_abs_delta']<1e-6 and out['controls']['synthetic_known_row_scale_repair_max_abs_delta']<1e-6
 out.update(wall_seconds=time.time()-t,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 Path(a.out).write_text(json.dumps(out,indent=2));print('DONE',a.out,flush=True)
if __name__=='__main__':main()
