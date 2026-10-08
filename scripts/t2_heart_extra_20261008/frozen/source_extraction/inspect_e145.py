from pathlib import Path
import h5py,json,numpy as np
from anndata.io import read_elem,sparse_dataset
r=Path('/workspace/shared/t2_external_sources_20261008');p=r/'quarantine/E14.5_E1S3.MOSTA.h5ad'
with h5py.File(p,'r') as f:
 obs=read_elem(f['obs']);var=read_elem(f['var'])
 report={'file':str(p),'shape':[len(obs),len(var)],'obs_columns':list(obs),'var_columns':list(var),'obsm_keys':list(f.get('obsm',{})),'uns_keys':list(f.get('uns',{})),'layers':list(f.get('layers',{})),'obs_categorical':{k:obs[k].astype(str).value_counts().to_dict() for k in obs if obs[k].nunique()<100},'var_names_first':list(var.index[:20]),'matrix_metadata':{}}
 for key in ['X']+['layers/'+k for k in f.get('layers',{})]:
  x=f[key];report['matrix_metadata'][key]={'encoding':str(x.attrs.get('encoding-type','')),'shape':list(x.attrs.get('shape',x.shape if isinstance(x,h5py.Dataset) else [])),'keys':list(x.keys()) if isinstance(x,h5py.Group) else []}
  if isinstance(x,h5py.Group) and 'data' in x:
   v=x['data'][:min(len(x['data']),1000000)];report['matrix_metadata'][key].update(data_dtype=str(x['data'].dtype),nnz=len(x['data']),sample_min=float(v.min()),sample_max=float(v.max()),sample_fraction_noninteger=float(np.mean(v!=np.round(v))))
 (r/'E145_FILE_INSPECTION.json').write_text(json.dumps(report,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else str(x)))
 print(json.dumps(report,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else str(x)))
