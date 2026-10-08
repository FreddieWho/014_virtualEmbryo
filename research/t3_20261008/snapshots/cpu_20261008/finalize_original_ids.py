"""Final metadata-only old-ID revision requested by user; no expression mutation.

Run after reproduce_backlog.py and disclosure packaging. Existing immutable
outputs deliberately cause failure rather than overwrite.
"""
from pathlib import Path
import json,hashlib,sys,anndata as ad,shutil
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'docs/batch3/interfaces'))
from virtual_embryo_tools.contract_io import validate_h5ad_contract
RUN=ROOT/'experiments/cpu_20261008';OUT=RUN/'backlog'
m=json.loads((OUT/'MANIFEST_DISCLOSED.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();uploads=OUT/'uploads_original_ids';uploads.mkdir(exist_ok=True)
for c in m['candidates']:
 old=Path(c['path']);a=ad.read_h5ad(old);cid=c['original_candidate'];previous=c['candidate_id'];meta=dict(a.uns['t3_reproduction']);meta.pop('new_version',None);meta.update(candidate_id=cid,reconstruction_date='2026-10-08',original_bytes_unavailable=True,same_version_new_serialized_artifact=True);a.uns['t3_reproduction']=meta
 disclosure=str(a.uns['external_data_disclosure']).replace('v0086: original v0083','v0083: same-ID').replace('v0087: original v0084','v0084: same-ID').replace('v0088: original v0085','v0085: same-ID').replace('new versioned artifacts','same-ID reconstructed artifacts');a.uns['external_data_disclosure']=disclosure
 folder=ROOT/f'artifacts/reproductions/20261008/{cid}';folder.mkdir(parents=True,exist_ok=False);p=folder/'submission.h5ad';a.write_h5ad(p,compression='gzip');parent=RUN/'baseline_compat_v2/hurdle_rebuild.h5ad';con=validate_h5ad_contract(p,task='T3',board='gata4',scorer_lock=RUN/'SCORER_LOCK.json',parent_path=parent,parent_sha256=sha(parent));assert con['status']=='PASS',con
 (folder/'contract.json').write_text(json.dumps(con,indent=2));filename=c['portal_filename'].replace(previous,cid);upload=uploads/filename;shutil.copyfile(p,upload)
 c['prior_metadata_only_artifact']={'path':c['path'],'sha256':c['sha256'],'unused_candidate_id':previous};c.update(candidate_id=cid,path=str(p),sha256=sha(p),upload_path=str(upload),portal_filename=filename,contract_path=str(folder/'contract.json'),reconstruction_date='2026-10-08',same_id_reconstruction=True)
m['identity_policy']='User explicitly requested original candidate IDs83/84/85. Historical SHA preserved separately; current reconstruction hash authoritative for this upload, not original-byte identity.'
(OUT/'MANIFEST_ORIGINAL_IDS.json').write_text(json.dumps(m,indent=2)+'\n')
