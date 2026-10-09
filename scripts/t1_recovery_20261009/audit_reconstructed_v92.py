import os
import json, hashlib, platform
from pathlib import Path
import numpy as np, scipy, sklearn, anndata as ad, h5py, pandas as pd
R=Path(os.environ.get('T1_RECOVERY_ROOT', 't1_recovery_run'))
p=R/'submit/T1_val__A_ot_gen_v51_reconstructed.h5ad'
build=json.loads((R/'work/t1r3/A_ot_gen_v51_reconstructed.build.json').read_text())
a=ad.read_h5ad(p);base=np.load(R/'work/repro51/chain/v0051.npy',mmap_mode='r')
h=hashlib.sha256();cb=hashlib.sha256();libs=[];clibs=[];cn=0;changed=0
for lo in range(0,a.n_obs,128):
    z=a.X[lo:lo+128].toarray().astype(np.float32);b=np.asarray(base[lo:lo+128]);h.update(z.tobytes());cb.update(np.ascontiguousarray(b).tobytes());libs.extend(np.expm1(z).sum(1).tolist());clibs.extend(np.expm1(b).sum(1).tolist());cn+=np.count_nonzero(b);changed+=np.count_nonzero(z!=b)
ref='35fae3a797acdf44b4c6d141e1a0db65b44744ea218f96218c7909e34eda5dc1'
obs={'nnz_fraction':float(a.X.nnz/np.prod(a.shape)),'carrier_nnz_fraction':float(cn/np.prod(a.shape)),'pb_shift_l2':build['pb_shift_l2'],'max_abs_pb':build['max_abs_pb'],'median_library':float(np.median(libs)),'carrier_median_library':float(np.median(clibs))}
historical={'nnz_fraction':.13637,'carrier_nnz_fraction':.13645,'pb_shift_l2':5.78,'max_abs_pb':.31,'median_library':10456.,'carrier_median_library':10000.}
out={'status':'RECIPE_RECONSTRUCTION_NOT_EXACT_ORIGINAL','file':str(p),'sha256':build['sha256'],'original_v92_sha256':ref,'original_file_sha_match':build['sha256']==ref,'expression_sha256':h.hexdigest(),'carrier_expression_sha256':cb.hexdigest(),'shape':list(a.shape),'format':build['format'],'changed_entries_from_carrier':int(changed),'observed':obs,'historical_rounded_aggregate':historical,'aggregate_delta_vs_rounded':{k:v-historical[k] for k,v in obs.items()},'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'anndata':ad.__version__,'pandas':pd.__version__,'h5py':h5py.__version__},'limits':['The historical server score58.8865 does not belong to this reconstruction.','Original per-cell labels and original prediction bytes are unavailable; differences cannot be claimed metadata-only.','Historical aggregate values are rounded and cannot establish exact matrix identity.','Both downstream final candidates must use this one same frozen reconstructed baseline. Historical server comparison retains a replay confound.']}
(R/'work/t1r3/RECONSTRUCTED_V92_AUDIT.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
