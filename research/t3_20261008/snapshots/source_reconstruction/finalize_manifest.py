from pathlib import Path
import json,hashlib,shutil,sys
import anndata as ad,numpy as np,pandas as pd
R=Path('/workspace/shared/t3repo');O=Path('/workspace/shared/t3source');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['reports/t3_r56_launch_20260921/SOURCE_REVIEW.json','docs/coordination/T3_EXTERNAL_DATA_POLICY_20260921.md']:
 (O/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,O/name)
m=json.loads((R/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json').read_text())
m['schema']='t3.source.reconstructed.20261008.v1';m['parent_manifest']={'path':str(R/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'),'sha256':sha(R/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json')}
m['files']={'expression':{'path':'expression.h5ad','sha256':sha(O/'expression.h5ad')},'go_embedding':{'path':'GO_EMBEDDING.npz','sha256':sha(O/'GO_EMBEDDING.npz')}}
m['filter_receipt']={'path':'RECONSTRUCTION.json','sha256':sha(O/'RECONSTRUCTION.json')}
m['reconstruction_notice']='New serialized H5AD; exact raw GEO hashes and frozen barcode plan, original filter and normalization code; not asserted byte-identical to original H5AD. GO embedding is byte-identical to frozen original.'
m.pop('adjacency_role');m['embedding_role']='WT_OR_ONTOLOGY_ONLY';(O/'SOURCE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
sys.path.insert(0,str(R/'scripts'));from t3_next.source_roles import require_response_role
require_response_role(m,O,'SIGNED_RESPONSE')
a=ad.read_h5ad(O/'expression.h5ad');orig=json.loads((R/'reports/t3_data_intake_20260920/FIBRO_FILTER_RECEIPT.json').read_text());f=json.loads((O/'filter_report/FIBRO_FILTER_RECEIPT.json').read_text())
assert orig['condition_counts']==f['condition_counts'];assert orig['plan_sha256']==f['plan_sha256'];assert a.shape==(5454,500);assert np.isfinite(a.X).all() and a.X.min()>=0;assert a.obs.model_input.all();assert list(a.var_names)==json.loads((R/'reports/t3_data_intake_20260920/panel_genes.json').read_text())
r={'permit_check':'PASS','panel_order':'PASS','shape':[5454,500],'all_finite_nonnegative':True,'counts_match_frozen_receipt':True,'barcode_plan_hash_matches_frozen_receipt':True,'expression_array_sha256':hashlib.sha256(a.X.tobytes()).hexdigest(),'validation_reader_environment':{'anndata':ad.__version__,'numpy':np.__version__,'pandas':pd.__version__}}
(O/'VALIDATION.json').write_text(json.dumps(r,indent=2)+'\n')
(O/'bioinf_data_index_additions.tsv').write_text('path\tsource\trole\tsha256\tstatus\n'+f"{O/'expression.h5ad'}\tGSE261783 GSM8151756/57 frozen allowlist\tSIGNED_RESPONSE\t{sha(O/'expression.h5ad')}\tRECONSTRUCTED_VERSION; original review retained\n"+f"{O/'GO_EMBEDDING.npz'}\tGO frozen inputs + original SVD recipe\tONTOLOGY_ONLY\t{sha(O/'GO_EMBEDDING.npz')}\tBYTE_IDENTICAL_RESTORATION\n")
print(json.dumps(r,indent=2))
