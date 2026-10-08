import json,glob
from pathlib import Path
import numpy as np
D=Path('/workspace/shared/t2_heart_extra_20261008/evaluation');out={}
for part in ['dev','reserve']:
 out[part]={}
 for lane in ['copy','incumbent_recipe','pca','go','graph','perm','endpoint','endfree','endperm','endmatched','endmatchedperm']:
  fs=sorted(D.glob(part+'_'+lane+'_s*.json'))
  if not fs:continue
  x=[json.loads(f.read_text())['metrics'] for f in fs];keys=set.intersection(*(set(q) for q in x))
  out[part][lane]={'runs':len(fs),'files':[str(f) for f in fs],'median':{k:float(np.median([q[k] for q in x])) for k in sorted(keys) if all(isinstance(q[k],(int,float)) for q in x)}}
P=Path('/workspace/shared/t2_extra_independent_audit/metric_comparison.json');P.write_text(json.dumps(out,indent=2))
for part,ls in out.items():
 for lane,v in ls.items():print(part,lane,v['runs'],{k:v['median'][k] for k in ['de_score','de_direction','mmd_u','variogram','neighborhood_mmd']})
