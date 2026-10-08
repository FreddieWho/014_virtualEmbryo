"""Reproduce frozen original v0083/84/85 recipes with new artifact identities."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,pickle,hashlib,csv
from pathlib import Path
import numpy as np,anndata as ad,pandas as pd
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'docs/batch3/interfaces')]
from t3_next.common import dense,dump,sha
from t3_next.source_roles import require_response_role
from t3_autoresearch import retained_model
from t3_six.common import fit_log_multiplier
from t3_six2.deliver import route_emit
from virtual_embryo_tools.contract_io import validate_h5ad_contract
threadpool_limits(limits=2)
SRC=Path('/workspace/shared/t3source');RUN=ROOT/'experiments/cpu_20261008';OUT=RUN/'backlog';OUT.mkdir(exist_ok=True)
require_response_role(json.loads((SRC/'SOURCE_MANIFEST.json').read_text()),SRC,'SIGNED_RESPONSE')
a=ad.read_h5ad(SRC/'expression.h5ad');x=dense(a.X);labels=a.obs.condition.astype(str).to_numpy();ctrl=x[labels=='ctrl']
sel=json.loads((ROOT/'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text());genes=sel['fixed_training_genes']+sel['val']['genes']+sel['test']['genes'];assert set(genes)==set(labels)-{'ctrl'}
emb=np.load(SRC/'GO_EMBEDDING.npz');ei={g:i for i,g in enumerate(emb['genes'])}
Y=np.array([x[labels==g].mean(0)-ctrl.mean(0) for g in genes]);E=emb['embedding'][[ei[g] for g in genes]]
delta=retained_model.predict({'genes':np.array(genes),'E':E,'Y':Y},{'genes':np.array(['Gata4']),'E':emb['embedding'][[ei['Gata4']]]})[0];beta=fit_log_multiplier(ctrl,delta);sd=np.std(Y,axis=0)
donor=max(genes,key=lambda g:float(emb['embedding'][ei['Gata4']]@emb['embedding'][ei[g]]));donor_ko=x[labels==donor]
sign=(np.sign(donor_ko.mean(0,dtype=float)-ctrl.mean(0,dtype=float))==np.sign(delta)).astype(float)
parent=RUN/'baseline_compat_v2/hurdle_rebuild.h5ad';b=ad.read_h5ad(parent);base=dense(b.X);gi=list(b.var_names).index('Gata4')
wtpath=Path('/workspace/shared/virtual_embryo_data/E8.75.h5ad');wt=ad.read_h5ad(wtpath);rows=wt.obs_names.get_indexer(b.obs_names);assert (rows>=0).all();wx=dense(wt[:,list(b.var_names)].X)
with (RUN/'baseline/hurdle_model.pkl').open('rb') as f:m=pickle.load(f)
f=m.encoder.features(wx[rows][:,[gi]],np.asarray(wt.obsm['spatial_3D'])[:,:3].astype(float)[rows],wt.obs.celltype.astype(str).to_numpy()[rows]);prob=np.clip(m.encoder.model.predict(f),0,1);cols=np.flatnonzero(np.arange(500)!=gi)
aux={'hurdle_prob':prob,'hurdle_cols':cols,'ctrl':ctrl,'donor_ko':donor_ko,'sign_gate':sign,'delta4':delta}
inputs={str(p):sha(p) for p in [wtpath,SRC/'expression.h5ad',SRC/'GO_EMBEDDING.npz',SRC/'SOURCE_MANIFEST.json',parent,RUN/'baseline/hurdle_model.pkl',ROOT/'scripts/t3_autoresearch/retained_model.py',ROOT/'scripts/t3_six2/deliver.py',ROOT/'scripts/t3_next/five_ops.py',RUN/'SCORER_LOCK.json']}
original={r['version']:r for r in csv.DictReader((ROOT/'submissions/INDEX.tsv').open(),delimiter='\t') if r['board']=='T3:gata4'}
manifest={'status':'CANDIDATES_READY_NOT_SUBMITTED','date':'2026-10-08','source_KO':'only approved GSE261783 adult cardiac fibroblast OP2 resting26 conditions','embryo_training':'official E8.75 WT','target_truth_used':False,'donor':donor,'inputs':inputs,'source_serialization_notice':'new source H5AD from verified original raw GEO hashes and frozen barcode selection; GO byte-identical','parent_rebuild':'historical v0048 algorithm and row seed reproduced; 301307 changed entries,1354 affected rows; original parent bytes unavailable','candidates':[]}
np.savez_compressed(OUT/'MODEL_ARRAYS.npz',delta4=delta,beta4=beta,sd4=sd,sign_gate=sign,hurdle_prob=prob)
for old,new,lane,params in [('v0083','v0086','o3_psb','psb'),('v0084','v0087','n1_qtl','q0.25'),('v0085','v0088','n2_dsign','g0.5')]:
 pred=route_emit(lane,params,base,beta,sd,aux);pred[:,gi]=0
 assert pred.shape==(7449,500) and np.isfinite(pred).all() and (pred>=0).all()
 short=lane.split('_')[1];folder=ROOT/f'submissions/candidates/T3_gata4/{new}_repro_{short}';folder.mkdir(parents=True,exist_ok=False)
 out=folder/'submission.h5ad';candidate=b.copy();candidate.X=pred;candidate.uns['ve_contract']={'normalization':'log_normalized','source':f'reproduced original {old} {lane} frozen recipe on v0048 numerical rebuild'};candidate.uns['t3_reproduction']={'original_candidate':old,'original_sha256':original[old]['sha256'],'new_version':new,'params':params,'donor':donor,'original_bytes_unavailable':True,'target_truth_used':False,'source_manifest_sha256':sha(SRC/'SOURCE_MANIFEST.json')};candidate.write_h5ad(out,compression='gzip')
 contract=validate_h5ad_contract(out,task='T3',board='gata4',scorer_lock=RUN/'SCORER_LOCK.json',parent_path=parent,parent_sha256=sha(parent));dump(folder/'contract.json',contract);assert contract['status']=='PASS',contract
 reread=ad.read_h5ad(out);np.testing.assert_array_equal(dense(reread.X),pred);np.testing.assert_array_equal(reread.obsm['spatial_3D'],b.obsm['spatial_3D']);assert list(reread.var_names)==list(b.var_names)
 rec={'candidate_id':new,'original_candidate':old,'original_sha256':original[old]['sha256'],'original_byte_identity':False,'recipe':lane,'params':params,'path':str(out),'sha256':sha(out),'array_sha256':hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest(),'portal_filename':f't3_gata4__repro{short}__{new}.h5ad','shape':list(pred.shape),'contract':'PASS','changed_entries_vs_parent':int(np.count_nonzero(pred!=base)),'density':float((pred>0).mean()),'response_mean_max_abs':float(np.max(np.abs(pred.mean(0)-base.mean(0))))}
 manifest['candidates'].append(rec);dump(folder/'REPRODUCTION.json',{'candidate':rec,'inputs':inputs,'source_manifest':str(SRC/'SOURCE_MANIFEST.json')});print(rec,flush=True)
dump(OUT/'MANIFEST.json',manifest)
