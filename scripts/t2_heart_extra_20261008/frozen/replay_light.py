"""Portable inference replay from frozen model and embedded released-source carrier.
The submitted file retains an untouched layers['log1p'] source input. This script
never uses prediction .X as inference input; it only uses .X for final comparison.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import json,hashlib,pickle,argparse
from pathlib import Path
import numpy as np,anndata as ad
import endpoint_residual as model

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def content(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();r=a.root;receipt=json.loads((r/'INFERENCE_INPUTS.json').read_text());art=r/'candidate/submission.h5ad';mp=r/'model/endpoint_model.pkl';assert sha(art)==receipt['candidate_sha'] and sha(mp)==receipt['model_sha']
 pred=ad.read_h5ad(art);expected=np.asarray(pred.X).copy();carrier=pred.copy();raw=carrier.layers['log1p'];carrier.X=raw.toarray().astype('float32') if hasattr(raw,'toarray')else np.asarray(raw,dtype='float32').copy();assert content(carrier.X)==receipt['source_carrier_X_sha256'];assert content(carrier.obsm['spatial_3D'])==receipt['source_carrier_coordinates_sha256']
 m=pickle.loads(mp.read_bytes());out,diag=model.predict(carrier,m,False);err=float(np.max(np.abs(out-expected)));assert err<=2e-6;result={'status':'PASS','exact_X':bool(np.array_equal(out,expected)),'max_abs_X_error':err,'tolerance':2e-6,'source_input':'Unmodified released E9.5 carrier in candidate.layers[log1p], independently hash-verified; prediction.X used only as output comparator','candidate_sha':sha(art),'model_sha':sha(mp),'diagnostics':diag};(r/'REPLAY_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
