import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,pickle,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
R=Path('/workspace/shared/t2_heart_extra_20261008');P=R/'deliveries/t2_hrt_ext__x_endrank__v0036.h5ad';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dense=lambda x:x.toarray() if hasattr(x,'toarray') else np.asarray(x)
a=ad.read_h5ad(P);f=ad.read_h5ad(R/'final/endmatched.h5ad');src=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad');ids=pd.read_csv(R/'final/source_row_ledger.tsv',sep='\t').source_row.to_numpy();s=src[ids,a.var_names].copy()
assert sha(P)=='0b89c69adff3b5cb3d86f0d8b0dbfe667f289343b0d7ac8908ca9c70ed33fc03'
checks={'size':P.stat().st_size,'X_matches_audited':bool(np.array_equal(a.X,f.X)),'coords_match_audited':bool(np.array_equal(a.obsm['spatial_3D'],f.obsm['spatial_3D'])),'raw_E95_geometry_exact':bool(np.array_equal(a.obsm['spatial_3D'],s.obsm['spatial_3D'])),'raw_E95_obs_exact':list(a.obs_names)==list(s.obs_names),'source_layer_matches_raw_E95_X':bool(np.array_equal(dense(a.layers['log1p']),dense(s.X))),'canonical_alias_identical':sha(P)==sha(R/'submissions/candidates/T2_heart_val_extrap/v0036_x_endpoint_rank/submission.h5ad'),'portable_alias_identical':sha(P)==sha(R/'portable/candidate/submission.h5ad')}
# Replay portable emitter directly on true raw E9.5 carrier, never predictionX.
sys.path.insert(0,str(R/'portable'));import endpoint_residual as er
m=pickle.loads((R/'portable/model/endpoint_model.pkl').read_bytes());carrier=a.copy();carrier.X=dense(s.X).astype('float32');out,diag=er.predict(carrier,m,False);checks['portable_replay_from_independent_raw_source_exact']=bool(np.array_equal(out,a.X));checks['max_abs_replay_error']=float(np.max(np.abs(out-a.X)))
permit=json.loads((R/'portable/inputs/endpoint/T2_DATA_PERMIT.json').read_text());ep=R/'portable/inputs/endpoint/E14.5_cm_enriched_panel_raw.h5ad';checks['endpoint_sha_matches_model']=sha(ep)==m['endpoint']['external_sha'];checks['permit_model_allowed']=permit['model_input_allowed'] and permit['status']=='ALLOW_E145_ONLY_RAW_SPATIAL_ENDPOINT' and permit['stage']==14.5;checks['permit_source_hash_matches']=any(v['sha256']==sha(ep) for v in permit['model_artifacts']);checks['permit_sha_matches_model']=sha(R/'portable/inputs/endpoint/T2_DATA_PERMIT.json')==m['endpoint']['permit_sha'];checks['contract_uns']=dict(a.uns['ve_contract']);checks['uns_keys']=list(a.uns);checks['source_model_stage_times']={k:m[k] for k in ['early_time','late_time','target_time','endpoint_time']}
for k,v in checks.items():
 if isinstance(v,bool):assert v,k
report={'status':'RELEASE_READY','path':str(P),'sha256':sha(P),'checks':checks,'diagnostics':diag,'provenance':{k:str(a.uns[k]) for k in a.uns if 'provenance' in k or 'endpoint' in k}}
Path('/workspace/shared/t2_extra_independent_audit/PACKAGED_RELEASE_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
