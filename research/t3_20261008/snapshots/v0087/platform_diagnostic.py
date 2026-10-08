import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='2'
import json
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from crossko import CrossKO
P=Path(__file__).parent;w=ad.read_h5ad(P/'crossko_results/WT_whitelisted_panel10000.h5ad');g=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E8.75.h5ad');X=w.X;G=g.X.toarray() if hasattr(g.X,'toarray') else g.X;assert np.array_equal(w.var_names,g.var_names);m=CrossKO(states=8,min_cells=10).fit_atlas(X)
def info(x):
 z=m.pca.transform(x);lab=m.km.predict(z);distance=np.linalg.norm(z-m.km.cluster_centers_[lab],axis=1);return lab,distance
sl,sd=info(X);gl,gd=info(G);threshold=np.array([np.quantile(sd[sl==c],.95) for c in range(8)]);unsupported=gd>threshold[gl];stats=[]
for name,a in [('source_WT10x',X),('target_WT_MERFISH',G)]:stats.append(dict(name=name,cells=len(a),detection=float((a>0).mean()),positive_quantiles=np.quantile(a[a>0],[.01,.5,.99]).tolist(),row_expm1_quantiles=np.quantile(np.expm1(a.astype(float)).sum(1),[0,.5,1]).tolist()))
rows=[]
for c in range(8):
 a=X[sl==c];b=G[gl==c];rows.append(dict(state=c,source_cells=len(a),target_cells=len(b),source_fraction=float(len(a)/len(X)),target_fraction=float(len(b)/len(G)),source_detection=float((a>0).mean()),target_detection=float((b>0).mean()) if len(b) else None,target_outside_fraction=float(unsupported[gl==c].mean()) if len(b) else None,source_distance95=float(threshold[c])))
pd.DataFrame(rows).to_csv(P/'PLATFORM_STATE_SUPPORT.csv',index=False);pd.DataFrame(dict(gene=w.var_names,source_detection=(X>0).mean(0),target_detection=(G>0).mean(0),source_mean=X.mean(0),target_mean=G.mean(0))).to_csv(P/'PLATFORM_GENE_STATS.csv',index=False)
result=dict(scope='Untreated-only source10x versus targetMERFISH technical/state comparison; no heldout outcome',statistics=stats,target_outside95=float(unsupported.mean()),target_celltype_support={str(c):float(1-unsupported[g.obs.celltype.astype(str).to_numpy()==c].mean()) for c in g.obs.celltype.unique()},warning='Same nominal panel closure does not align detection, state resolution or response amplitude; distance thresholds are descriptive, not calibrated probability')
(P/'PLATFORM_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
