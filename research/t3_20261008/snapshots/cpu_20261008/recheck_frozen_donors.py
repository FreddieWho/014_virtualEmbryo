"""Recheck already-frozen q0.25 and g0.5 on strict original17 training splits."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'third_party/veckit')]
from t3_next.common import dump,sha,dense
from t3_next.five_ops import quantile_response
from t3_six.common import fit_log_multiplier,emit_mult,measure
from t3_six.validation import nearest_training_donor
from t3_autoresearch import retained_model
threadpool_limits(limits=2)
OUT=ROOT/'experiments/cpu_20261008/frozen_donors';OUT.mkdir(exist_ok=True)
a=ad.read_h5ad('/workspace/shared/t3source/expression.h5ad');x=dense(a.X);labels=a.obs.condition.astype(str).to_numpy();samples=a.obs['sample'].astype(str).to_numpy();sam=sorted(set(samples))
frozen=json.loads((ROOT/'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text());train=frozen['fixed_training_genes'];held=frozen['val']['genes']+frozen['test']['genes'];genes=train+held
emb=np.load('/workspace/shared/t3source/GO_EMBEDDING.npz');E=emb['embedding'];names=emb['genes'].tolist();ei={g:i for i,g in enumerate(names)}
dump(OUT/'FROZEN_PROTOCOL.json',{'qtl_strength':.25,'dsign_strength':.5,'training_genes':train,'held_genes':held,'origin':'same frozen 2026-10-07 parameters, not retuned','source_sha256':sha('/workspace/shared/t3source/expression.h5ad'),'code_sha256':sha(__file__),'test_emission':'source reference ctrl/donor applied to recipient held-sample WT ctrl, identical target emitter','limitation':'target carrier is hurdle, source carrier here is WT control; no complete carrier-model validation'})
rows=[];folds=[]
for sc,si,ti in [('pooled',sam,sam),('sample0_to_1',sam[:1],sam[1:]),('sample1_to_0',sam[1:],sam[:1])]:
 source_ctrl=x[(labels=='ctrl')&np.isin(samples,si)];recipient=x[(labels=='ctrl')&np.isin(samples,ti)]
 Y={g:np.mean([x[(labels==g)&(samples==s)].mean(0)-x[(labels=='ctrl')&(samples==s)].mean(0) for s in si],axis=0) for g in genes}
 for g in genes:
  tr=[h for h in train if h!=g];donor=nearest_training_donor(E,names,tr,g);donor_ko=x[(labels==donor)&np.isin(samples,si)]
  dg=retained_model.predict({'genes':np.array(tr),'E':E[[ei[h] for h in tr]],'Y':np.array([Y[h] for h in tr])},{'genes':np.array([g]),'E':E[[ei[g]]]})[0];beta=fit_log_multiplier(source_ctrl,dg)
  gate=(np.sign(donor_ko.mean(0,dtype=float)-source_ctrl.mean(0,dtype=float))==np.sign(dg)).astype(float)
  preds={'identity':recipient,'qtl025':quantile_response(recipient,source_ctrl,donor_ko,.25,np.log(2)).astype(np.float32),'dsign05':emit_mult(recipient,.5*gate*beta),'retained_mult05':emit_mult(recipient,.5*beta),'retained_mult1':emit_mult(recipient,beta)}
  truth=x[(labels==g)&np.isin(samples,ti)]
  for method,p in preds.items():rows.append({'scenario':sc,'split':'development17' if g in train else 'historical9','gene':g,'method':method,**measure(p,truth,recipient)})
  folds.append({'scenario':sc,'query':g,'train':tr,'donor':donor})
 print(sc,'complete',flush=True)
df=pd.DataFrame(rows);df.to_csv(OUT/'METRICS.tsv',sep='\t',index=False);dump(OUT/'OUTER_IDENTITIES.json',folds)
summary=df.groupby(['scenario','split','method'])[['de_score','de_direction','severity_abs','mmd_u','variogram','mean_response_mse','density']].mean();summary.to_csv(OUT/'SUMMARY.tsv',sep='\t');print(summary.to_string(),flush=True)
