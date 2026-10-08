from pathlib import Path
import hashlib,json,sys,zipfile
import anndata as ad,numpy as np,pandas as pd
P=Path('/workspace/shared/t3_v88_optimization_20261008');R=Path('/workspace/shared/t3_v87_restored');O=P/'v0088';out=Path('/workspace/shared/t3_v88_independent_audit')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common.core_metrics import skill
w={'de':.3,'direction':.25,'severity_abs':.25,'mmd':.12,'variogram':.08};f=pd.read_csv(P/'source_evaluation/metrics.csv');assert len(f)==84 and f.groupby(['query','model']).size().eq(3).all();anchors={(a['query'],a['seed']):a for a in json.loads((P/'source_evaluation/anchors.json').read_text())}
for _,r in f.iterrows():
 a=anchors[(r.query,r.seed)];s={m:100*skill(r[m],a['floor'][m],a['ceiling'][m],lower_is_better=m in ['severity_abs','mmd','variogram']) for m in w};total=sum(w[m]*s[m] for m in w);assert np.isfinite(total) and abs(total-r.total)<1e-9
q=f.groupby(['query','model']).mean(numeric_only=True);dec=[]
for arm in ['residual','conditional','both']:
 d=q.xs(arm,level='model')-q.xs('baseline',level='model');eligible=bool(d.total.mean()>0 and (d.total>0).sum()>=4 and all(d[m+'_skill'].mean()>=-2 for m in ['de','direction','severity_abs']));dec.append({'arm':arm,'eligible':eligible,'gain':d.total.mean(),'wins':int((d.total>0).sum())})
selected=max([d for d in dec if d['eligible']],key=lambda d:d['gain'])['arm'];assert selected=='conditional';assert json.loads((P/'source_evaluation/SELECTION.json').read_text())['chosen']==selected
old=pd.read_csv(R/'crossko7_hurdle_v2_results/metrics.csv');old=old[old.model=='mean_combined'].set_index('query');new=f[(f.model=='baseline')&(f.seed==0)].set_index('query');metrics=list(w)+['severity_r2','mse'];assert np.array_equal(new[metrics].values,old.loc[new.index,metrics].values)
m=json.loads((O/'MANIFEST.json').read_text());p=Path(m['file']);a=ad.read_h5ad(p);parentfile=R/'v0087/t3_gata4__embhurdle__v0087.h5ad';parent=ad.read_h5ad(parentfile);frozen=ad.read_h5ad(P/'deployment/gata4_conditional.h5ad');assert sha(p)==m['sha256'];assert sha(parentfile)=='b0cfdf5e870f762185efd9f2bdc803cab26ecb0a54e18a870286d41165ce5fc9';assert np.array_equal(a.X,frozen.X);assert a.obs.equals(parent.obs) and a.var.equals(parent.var);assert np.array_equal(a.obsm['spatial_3D'],parent.obsm['spatial_3D']);assert a.shape==(7449,500) and np.isfinite(a.X).all() and (a.X>=0).all();mass=float(abs(np.expm1(a.X.astype(float)).sum(1)-10000).max());assert mass<.02
metadata=a.uns['t3_v0088'];assert metadata['arm']=='conditional';assert metadata['protocol_sha256']==sha(P/'PROTOCOL.md');assert metadata['emitter_sha256']==sha(P/'emitter_v88.py');assert metadata['selection_sha256']==sha(P/'source_evaluation/SELECTION.json');assert metadata['frozen_prediction_sha256']==sha(P/'deployment/gata4_conditional.h5ad')
for name,h in json.loads(metadata['source_permit_hashes_json']).items():assert sha(R/'external_sources'/name)==h
zman=json.loads((O/'ZIP_MANIFEST.json').read_text());zp=Path(zman['file']);assert sha(zp)==zman['sha256']
with zipfile.ZipFile(zp) as z:assert z.namelist()==[p.name];assert z.testzip() is None;assert hashlib.sha256(z.read(p.name)).hexdigest()==sha(p)
sys.path.insert(0,'/workspace/shared/t3cpu/docs/batch3/interfaces');from virtual_embryo_tools.contract_io import validate_h5ad_contract
contract=validate_h5ad_contract(p,task='T3',board='gata4',scorer_lock=Path('/workspace/shared/t3cpu/experiments/cpu_20261008/SCORER_LOCK.json'),parent_path=parentfile,parent_sha256=sha(parentfile));assert contract['status']=='PASS'
report={'status':'PASS','selection':selected,'source_scores_independently_recomputed':84,'all7_baseline_metrics_exact':True,'decisions':dec,'file':str(p),'sha256':sha(p),'expression_sha256':hashlib.sha256(a.X.tobytes()).hexdigest(),'parent_immutable':True,'parent_metadata_geometry_exact':True,'frozen_selected_expression_exact':True,'panel_mass_max_error':mass,'contract':contract,'zip':str(zp),'zip_sha256':sha(zp)}
(out/'FINAL_ARTIFACT_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
