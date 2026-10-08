# Audit-requested supplement after frozen primary; not model-selection retuning.
import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='2'
import sys,json
from pathlib import Path
import anndata as ad,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from crossko import CrossKO
sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common import core_metrics as cm
P=Path(__file__).parent;O=P/'crossko_results';rng=np.random.default_rng(411);data={}
for g in ['WT','Dnmt3a','Kmt2a','Kdm2b']:
 a=ad.read_h5ad(O/f'{g}_whitelisted_panel10000.h5ad');data[g]=(a.X,a.obs)
wt,obs=data['WT'];controls={}
for sex in obs.sex.unique():
 blocks=[]
 for e in obs.loc[obs.sex==sex,'embryo'].unique():
  ix=np.flatnonzero((obs.sex==sex)&(obs.embryo==e));blocks.append(wt[rng.choice(ix,500,replace=len(ix)<500)])
 controls[sex]=np.concatenate(blocks)
e=np.load('/workspace/shared/t3_observation_reset/go_expanded/GO_EXPANDED_EMBEDDING.npz');priors=dict(zip(e['genes'].astype(str),e['embedding']));records=[]
for g in ['Dnmt3a','Kmt2a','Kdm2b']:
 x,o=data[g]
 for embryo in o.embryo.unique():
  ix=o.embryo==embryo;sex=o.loc[ix,'sex'].iloc[0];records.append(dict(gene=g,sample_unit=embryo,unit_kind='embryo',control=controls[sex],ko=x[ix]))
rows=[]
for query in ['Dnmt3a','Kmt2a','Kdm2b']:
 x,o=data[query];model=CrossKO(states=8,min_cells=10).fit_atlas(wt).fit_interventions(records,priors,query)
 for embryo in sorted(o.embryo.unique())[1::2]:
  ix=o.embryo==embryo;sex=o.loc[ix,'sex'].iloc[0];ref=controls[sex];base=ref[rng.choice(len(ref),7449,replace=True)];truth=x[ix]
  for method in ['identity','mean','nearest','ridge']:
   pred=base if method=='identity' else model.emit(base,model.predict(query,method),mode='within')[0];s,r2=cm.severity_slope(pred,truth,ref);rows.append(dict(query=query,embryo=embryo,sex=sex,method=method,direction=cm.de_direction(pred,truth,ref),severity_abs=abs(s),mse=float(np.mean((pred.mean(0,dtype=float)-truth.mean(0,dtype=float))**2))))
 pd.DataFrame(rows).to_csv(O/'sex_matched_equalWTembryo_sensitivity.csv',index=False);print(query,'complete',flush=True)
# Retention of the official whitelist by embryo, sex and published cellstate.
w=pd.read_csv('/workspace/shared/t3_developmental_sources/annotations/WT_E8.5_cell_annotations.tsv',sep='\t');w['retained']=w.barcode.isin(obs.index)
for keys in [['embryo','sex'],['cell_state']]:
 r=w.groupby(keys).retained.agg(['count','sum','mean']);r.to_csv(O/('WT_attrition_'+'_'.join(keys)+'.csv'))
print(pd.DataFrame(rows).groupby(['query','method'])[['direction','severity_abs','mse']].mean().to_string());print('COMPLETE')
