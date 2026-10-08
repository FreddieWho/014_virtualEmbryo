"""Path-portable v0036 replay/refit adapter. Frozen implementation is unchanged."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import argparse,hashlib,json,pickle,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'frozen'))
import numpy as np,anndata as ad
import flow,endpoint_flow as ef,endpoint_residual as er
from reproduce import select

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--inputs',type=Path,required=True,help='Official E8.75.h5ad and E9.5.h5ad directory')
 p.add_argument('--endpoint',type=Path,required=True,help='Clean E14.5 H5AD with adjacent T2_DATA_PERMIT.json')
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--model',type=Path,help='Optional trusted local frozen pickle; omitted: rebuild medians and endpoint microstates')
 p.add_argument('--compare',type=Path,help='Optional historical candidate, comparison only, never inference input')
 p.add_argument('--manifest',type=Path,default=HERE.parents[1]/'infra/bioinf-data-index/t2_heart_extra_20261008/PUBLIC_INPUTS.json')
 a=p.parse_args();manifest=json.loads(a.manifest.read_text());flow.PANEL=HERE/'T2__heart__val_extrap.genes.txt';flow.DATA=a.inputs
 for n in ['E8.75','E9.5']:
  assert sha(a.inputs/(n+'.h5ad'))==manifest['original_released_inputs'][n],f'{n} hash mismatch'
 genes=flow.PANEL.read_text().splitlines();late=ad.read_h5ad(a.inputs/'E9.5.h5ad')[:,genes].copy();late.X=flow.dense(late.X);carrier=late[select(late.obs.celltype.astype(str).to_numpy())].copy()
 if a.model:
  assert sha(a.model)==manifest['model_sha'],'Only the recorded trusted model identity is supported'
  m=pickle.loads(a.model.read_bytes())
 else:
  early=ad.read_h5ad(a.inputs/'E8.75.h5ad')[:,genes].copy();early.X=flow.dense(early.X)
  m={'endpoint':ef.fit_endpoint(a.endpoint),'median_deltas':ef.source_model(early,late),'early_time':8.75,'late_time':9.5,'target_time':10.5,'endpoint_time':14.5}
 x,diag=er.predict(carrier,m,False);carrier.X=x;carrier.uns['ve_contract']={'schema':'ve.contract.v1','normalization':'log_normalized'}
 result={'status':'PASS','mode':'replay' if a.model else 'refit','shape':list(x.shape),'diagnostics':diag,'byte_identity_claimed':False}
 if a.compare:
  assert sha(a.compare)==manifest['candidate_sha'],'Candidate identity mismatch'
  original=ad.read_h5ad(a.compare);err=float(np.max(np.abs(flow.dense(original.X)-x)));assert err<=2e-6
  assert original.obs_names.equals(carrier.obs_names) and original.var_names.equals(carrier.var_names)
  assert np.array_equal(original.obsm['spatial_3D'],carrier.obsm['spatial_3D'])
  result.update(exact_X=bool(np.array_equal(flow.dense(original.X),x)),max_abs_X_error=err,coordinate_exact=True,obs_names_exact=True,var_names_exact=True)
 a.out.parent.mkdir(parents=True,exist_ok=True);carrier.write_h5ad(a.out)
 Path(str(a.out)+'.verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
