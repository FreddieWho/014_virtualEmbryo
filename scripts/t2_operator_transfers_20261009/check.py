import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import sys,json,numpy as np,anndata as ad
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import build as b
D=Path(__file__).parent; p=ad.read_h5ad(D/'target/parent.h5ad');c=ad.read_h5ad(D/'target/t2_emb_int__e3_libself__v0023.h5ad');s=ad.read_h5ad(D/'target/shuffle_control.h5ad')
_,_,d=b.instrumented(b.args());L=b.V.load_stage('E7.25',list(p.var_names));idx=L.obs_names.get_indexer([x.rsplit('__r',1)[0] for x in p.obs_names]);assert min(idx)>=0
rawlib=np.expm1(L.X[idx].astype(float)).sum(1);lib=d['source_library'];clib=np.expm1(c.X.astype(float)).sum(1);slib=np.expm1(s.X.astype(float)).sum(1);t=d['touched']
report={'target_source_map_verified':True,'raw_E7_25_library_quantiles':np.quantile(rawlib,[0,.5,1]).tolist(),'bridge_input_XB_library_quantiles':np.quantile(lib,[0,.5,1]).tolist(),'raw_to_XB_median_library_fold':float(np.median(lib/rawlib)),'candidate_vs_source_max_relative_error':float(np.max(np.abs(clib[t]-lib[t])/lib[t])),'shuffled_negative_control_vs_source_median_relative_error':float(np.median(np.abs(slib[t]-lib[t])/lib[t])),'shuffled_negative_control_changed_X_fraction':float(np.mean(c.X!=s.X)),'parent_child_changed_X_fraction':float(np.mean(p.X!=c.X)),'replay_candidate_hash_match':b.sha(D/'target/t2_emb_int__e3_libself__v0023.h5ad')==b.sha(D/'replay/t2_emb_int__e3_libself__v0023.h5ad'),'replay_parent_hash_match':b.sha(D/'target/parent.h5ad')==b.sha(D/'replay/parent.h5ad'),'holdout_library_shuffle_control_note':'Released E6.75 source rows have ~10000 normalized library, so library shuffle degenerates numerically there; not evidence that row association is irrelevant. Target E3 XB source libraries vary and actual shuffle is nondegenerate.'}
assert report['replay_candidate_hash_match'] and report['replay_parent_hash_match'];assert report['shuffled_negative_control_changed_X_fraction']>.1
(D/'TEST_RESULTS.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
