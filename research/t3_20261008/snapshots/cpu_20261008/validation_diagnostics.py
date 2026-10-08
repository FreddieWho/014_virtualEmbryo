"""Fixed-dose diagnostic of audited bugs; oracle arms are ineligible for delivery."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'third_party/veckit')]
from t3_six.evaluate import route_n3 as switch, nmf_basis
from t3_six2.evaluate import route_n3 as swap, route_o3 as shrink
from t3_six.validation import nearest_training_donor,signed_program_pair,training_response_sd
from t3_six.common import fit_log_multiplier,measure
from t3_autoresearch import retained_model
from t3_next.common import dump,sha,dense
threadpool_limits(limits=2)
OUT=ROOT/'experiments/cpu_20261008/validation_diagnostics';OUT.mkdir(exist_ok=True)
a=ad.read_h5ad('/workspace/shared/t3source/expression.h5ad');x=dense(a.X);labels=a.obs.condition.astype(str).to_numpy();ctrl=x[labels=='ctrl'];density=(ctrl>0).mean(0)
frozen=json.loads((ROOT/'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text());train=frozen['fixed_training_genes'];held=frozen['val']['genes']+frozen['test']['genes'];genes=train+held
emb=np.load('/workspace/shared/t3source/GO_EMBEDDING.npz');E=emb['embedding'];names=emb['genes'].tolist();ei={g:i for i,g in enumerate(names)}
Y={g:x[labels==g].mean(0)-ctrl.mean(0) for g in genes};all_sd=np.std(np.stack(list(Y.values())),axis=0)
W,H=nmf_basis(np.ascontiguousarray(np.expm1(ctrl)),16);rows=[];folds=[]
dump(OUT/'FROZEN_PROTOCOL.json',{'strength':.25,'rank_grid_search':False,'train':train,'held':held,'oracle_arm':'explicitly ineligible for inference, upper-bound diagnostic','program_comparison':'original absolute selection vs signed remove/add; no outcome-dependent choice','source_sha256':sha('/workspace/shared/t3source/expression.h5ad'),'code_sha256':sha(__file__)})
for g in genes:
 tr=[h for h in train if h!=g]
 donor=nearest_training_donor(E,names,tr,g)
 dg=retained_model.predict({'genes':np.array(tr),'E':E[[ei[h] for h in tr]],'Y':np.array([Y[h] for h in tr])},{'genes':np.array([g]),'E':E[[ei[g]]]})[0]
 beta=fit_log_multiplier(ctrl,dg);sd=training_response_sd(Y,tr,g)
 cr=np.array([abs(np.corrcoef(h,dg)[0,1]) if h.std()>0 and dg.std()>0 else 0 for h in H]);old_remove=int(cr.argmax());cr[old_remove]=-1;old_add=int(cr.argmax());remove,add=signed_program_pair(H,dg)
 methods={'identity':ctrl,'switch_oracle_not_deployable':switch(x[labels==g],ctrl)['s0.25'],'switch_training_donor':switch(x[labels==donor],ctrl)['s0.25'],'swap_original_abs':swap(ctrl,W,H,old_remove,old_add)['p0.25'],'swap_signed':swap(ctrl,W,H,remove,add)['p0.25'],'shrink_leaky_all26':shrink(ctrl,dg,beta,all_sd,density)['psb'],'shrink_outer_train':shrink(ctrl,dg,beta,sd,density)['psb']}
 folds.append({'query':g,'train':tr,'donor':donor,'signed_remove':remove,'signed_add':add,'original_remove':old_remove,'original_add':old_add,'sd_max_change':float(np.max(np.abs(sd-all_sd)))})
 for method,p in methods.items():rows.append({'split':'development17' if g in train else 'historical9','gene':g,'method':method,**measure(p,x[labels==g],ctrl)})
 print(g,donor,flush=True)
pd.DataFrame(rows).to_csv(OUT/'METRICS.tsv',sep='\t',index=False);dump(OUT/'OUTER_IDENTITIES.json',folds)
summary=pd.DataFrame(rows).groupby(['split','method'])[['de_score','de_direction','severity_abs','mmd_u','variogram','mean_response_mse','density']].mean();summary.to_csv(OUT/'SUMMARY.tsv',sep='\t');print(summary.to_string(),flush=True)
