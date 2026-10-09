"""Additional source-specificity diagnostic; no refit or gate change."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import sys,argparse,json
from pathlib import Path
import numpy as np,anndata as ad
from scipy.special import softmax
from test_affine_assay import moments,GROUPS,COARSE
p=argparse.ArgumentParser();p.add_argument('--fit',required=True);p.add_argument('--source-result',required=True);p.add_argument('--external95',required=True);p.add_argument('--official95',required=True);p.add_argument('--out',required=True);a=p.parse_args()
f=np.load(a.fit);previous=json.loads(Path(a.source_result).read_text());ext=ad.read_h5ad(a.external95);official=ad.read_h5ad(a.official95)
z=(ext.X[:,f['markers']].toarray().astype(float)-f['marker_mean'])/f['marker_sd'];pr=softmax(z@f['classifier_coefficients'].T+f['classifier_intercept'],axis=1);labels=np.where(pr.max(1)>=.8,f['classifier_classes'][pr.argmax(1)],'LOWCONF');ol=np.array([COARSE[x] for x in official.obs.celltype.astype(str)])
rows=[]
for g in GROUPS:
 old=next(x for x in previous['state_results'] if x['group']==g)
 x=moments(ext.X[labels==g]);y=moments(official.X[ol==g]);assert x['n']==old['external95_cells']
 eligible=f[g+'|fit_eligible'];ev=eligible&(x['k']>=10)&(y['k']>=10)
 if ev.sum()<100:continue
 b=f[g+'|slope'];constant=float(np.median(b[eligible]));xs=np.sqrt(x['var'][ev]);ys=np.sqrt(y['var'][ev]);exact=float(np.median(np.abs(np.log((b[ev]*xs+.05)/(ys+.05)))))
 assert abs(exact-old['sd_error_adjusted'])<1e-12
 rows.append({'state':g,'evaluated_genes':int(ev.sum()),'constant_source_fitted_median_slope':constant,'original_gene_specific_error':exact,'state_median_slope_error':float(np.median(np.abs(np.log((constant*xs+.05)/(ys+.05))))),'identity_error':old['sd_error_unadjusted']})
r={'status':'POST_FREEZE_SPECIFICITY_DIAGNOSTIC_ONLY','model_or_gate_changed':False,'rows':rows,'equal_state_mean_gene_specific':float(np.mean([x['original_gene_specific_error'] for x in rows])),'equal_state_mean_state_median':float(np.mean([x['state_median_slope_error'] for x in rows])),'gene_specific_beats_state_median_states':sum(x['original_gene_specific_error']<x['state_median_slope_error'] for x in rows),'total_states':len(rows)}
Path(a.out).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
