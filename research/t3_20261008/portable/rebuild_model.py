"""Rebuild the selected generic model from approved normalized panels.

Default verifies inputs and prints the plan; --execute explicitly fits once.
No scoring, source method search, Mab truth load, or competition artifact creation.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import argparse,json,hashlib,sys,copy
from pathlib import Path
import numpy as np,anndata as ad,joblib
from threadpoolctl import threadpool_limits
threadpool_limits(2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--normalized',type=Path,required=True);p.add_argument('--go',type=Path,required=True);p.add_argument('--wt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--evidence-root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=a.evidence_root.resolve();s=r/'snapshots/v0087';v=r/'snapshots/v0088';inv=json.loads((r/'SNAPSHOT_INVENTORY.json').read_text())
 for name in ['crossko.py','crossko_hurdle_v2.py','deploy_diagnostics.py']:
  f=s/name;assert sha(f)==next(x['sha256'] for x in inv if x['path']==str(f.relative_to(r)))
 assert sha(a.wt)=='149ab6df7c99ad85046c8aebebcf0c43689b3720c59ffb7cc550edcf2f13a83c'
 go_manifest=json.loads((s/'external_sources/go_expanded7/PROVENANCE.json').read_text());assert sha(a.go)==go_manifest['outputs']['GO_EXPANDED_EMBEDDING.npz']
 expected=json.loads((v/'source_panel/normalized/MERGE_RECEIPT.json').read_text());checked=[]
 for x in expected:
  f=a.normalized/f"{x['gene']}_whitelisted_panel10000.h5ad";assert sha(f)==x['sha256'],('Normalized artifact metadata/hash mismatch',x['gene']);panel=ad.read_h5ad(f);h=hashlib.sha256(np.ascontiguousarray(panel.X).tobytes()).hexdigest();assert h==x['expression_array_sha256'],x['gene'];assert panel.n_obs==x['matched'];checked.append({'gene':x['gene'],'expression_array_sha256':h,'cells':panel.n_obs})
 original=(s/'deploy_diagnostics.py').read_text()
 # Exact historical fit prefix, stopped before all deployment/scoring loops.
 marker="for name,stage in [('mab','E9.5'),('gata4','E8.75')]:"
 assert original.count(marker)==1;code=original.split(marker)[0]
 old="P=Path(__file__).parent;S=P/'crossko7_hurdle_v2_results';O=P/'deployment_diagnostics';O.mkdir(exist_ok=True)"
 new=f"P=Path({str(s)!r});S=Path({str(a.normalized.resolve())!r});O=Path({str(a.out.resolve())!r})"
 assert code.count(old)==1;code=code.replace(old,new)
 code=code.replace("selection=json.loads((S/'SELECTION.json').read_text())",f"selection=json.loads(Path({str(s/'crossko7_hurdle_v2_results/SELECTION.json')!r}).read_text())")
 code=code.replace('/workspace/shared/t3repo/third_party/veckit',str(s/'public_core')).replace('/workspace/shared/t3_observation_reset/go_expanded7/GO_EXPANDED_EMBEDDING.npz',str(a.go.resolve()))
 compile(code,str(s/'deploy_diagnostics.py'),'exec');report={'status':'INPUTS_AND_FIT_PREFIX_VERIFIED','fitting_executed':a.execute,'normalized_inputs':checked,'original_code_sha256':sha(s/'deploy_diagnostics.py'),'fit_prefix_sha256':hashlib.sha256(code.encode()).hexdigest(),'scope':'Same frozen fit prefix; stop before target deployment and all scoring loops'}
 if not a.execute:print(json.dumps(report,indent=2));return
 a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(s));ns={'__file__':str(s/'deploy_diagnostics.py'),'__name__':'__rebuild_fit__'};exec(compile(code,str(s/'deploy_diagnostics.py'),'exec'),ns)
 model=ns['model'];assert ns['chosen']=='mean_combined';response=model.predict('Gata4','mean');keep=['S','q','positive_q','alpha','seed','min_cells','features','pca','km','G'];frozen=copy.copy(model);frozen.__dict__={k:model.__dict__[k] for k in keep}
 joblib.dump(frozen,a.out/'state_emitter.joblib',compress=3);np.savez_compressed(a.out/'generic_response.npz',**response)
 wt=ad.read_h5ad(a.wt);rows=np.sort(np.random.default_rng(20260904).choice(wt.n_obs,7449,replace=False));carrier=wt[rows].copy();carrier.X=(carrier.X.toarray() if hasattr(carrier.X,'toarray') else np.asarray(carrier.X)).astype('float32');carrier.write_h5ad(a.out/'WT_carrier7449.h5ad',compression='gzip')
 pred,donor=frozen.emit(carrier.X,response,mode='combined');digest=hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest();assert digest=='2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98';np.save(a.out/'expected_donor_rows.npy',donor)
 sys.path.insert(0,str(v));from emitter_v88 import emit
 conditional,conditional_donor=emit(frozen,carrier.X,response,residual=False,conditional=True);h88=hashlib.sha256(np.ascontiguousarray(conditional).tobytes()).hexdigest();assert h88=='7cfe4e0cfcfe1a76c003e25eed7d3fab58868f1d6d5dd7cb6b0ab14b3dddf77c';assert np.array_equal(donor,conditional_donor)
 report.update(status='REBUILT_EXPRESSION_EXACT',v0087_expression_sha256=digest,v0088_expression_sha256=h88,files={f.name:sha(f) for f in a.out.iterdir() if f.is_file()},note='Re-serialized carrier/model bytes need not match historical binaries; do not pass off as immutable historical assets')
 (a.out/'REBUILD_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
