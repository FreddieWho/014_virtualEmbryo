"""Serial registration and one manual-upload package, after all full inferences."""
from .common import *
import csv,io,zipfile,fcntl,shutil
LANES=['r1_celloracle','r3_activity','r4_functional','r4_bilinear','r5_scouter','r6_gears']

def tsv(rows,fields):
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);return out.getvalue()

def main():
    import anndata as ad
    sys.path.insert(0,str(ROOT/'docs/batch3/interfaces'))
    from virtual_embryo_tools.contract_io import validate_h5ad_contract
    expected=[RUN/l/'RESULT.json' for l in LANES]
    if not all(p.exists() for p in expected):raise RuntimeError('Full inference missing: '+str([str(p) for p in expected if not p.exists()]))
    if (RUN/'DELIVERY.json').exists():raise FileExistsError('immutable delivery already registered')
    parent_path=ROOT/'submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad'
    parent=ad.read_h5ad(parent_path);parent_sha=sha(parent_path)
    lock=ROOT/'artifacts/t3_next/REGISTRATION.lock';lock.parent.mkdir(exist_ok=True)
    with lock.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        index=ROOT/'submissions/INDEX.tsv'
        with index.open() as h:reader=csv.DictReader(h,delimiter='\t');fields=reader.fieldnames;rows=list(reader)
        next_version=max(int(r['version'][1:]) for r in rows if r['board']=='T3:gata4')+1
        prepared=[];members=[];mapping=[];runs=[];evidence=[]
        for k,lane in enumerate(LANES):
            result=json.loads((RUN/lane/'RESULT.json').read_text());assert result['status']=='FULL_TARGET_INFERENCE_COMPLETE_RESEARCH'
            assert sha(RUN/lane/'research.h5ad')==result['sha256']
            calibrated=json.loads((RUN/lane/'CALIBRATED.json').read_text())
            assert sha(RUN/lane/'calibrated.h5ad')==calibrated['sha256']
            a=ad.read_h5ad(RUN/lane/'calibrated.h5ad')
            scoped_parent=parent_path;scoped_sha=parent_sha
            if lane.startswith('r2_'):
                selected=np.load(RUN/'r2_sampling_indices.npy');carrier=parent[selected].copy();carrier.obs_names=a.obs_names.copy()
                carrier.uns['ve_contract']={'normalization':'log_normalized','source':'v0009 resampled WT; no expression alteration'}
                scoped_parent=RUN/lane/'resampled_WT_carrier.h5ad';carrier.write_h5ad(scoped_parent,compression='gzip');scoped_sha=sha(scoped_parent)
                np.testing.assert_array_equal(a.obsm['spatial_3D'],carrier.obsm['spatial_3D'])
                dump(RUN/lane/'CARRIER_LINEAGE.json',{'parent':'v0009','parent_sha256':parent_sha,'resampling_indices_sha256':sha(RUN/'r2_sampling_indices.npy'),'scoped_parent_sha256':scoped_sha,'candidate_rows_equal_resampled_WT':True,'scope':'official board schema does not require original WT row correspondence; internal validator binds this documented resampled carrier'})
            version=f'v{next_version+k:04d}';folder=ROOT/'submissions/candidates/T3_gata4'/f'{version}_six_{lane}'
            folder.mkdir(exist_ok=False);path=folder/'submission.h5ad';a.write_h5ad(path,compression='gzip')
            checks=validate_h5ad_contract(path,task='T3',board='gata4',scorer_lock=ROOT/'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',parent_path=scoped_parent,parent_sha256=scoped_sha)
            dump(folder/'contract.json',checks)
            assert checks['status']=='PASS',checks
            row=dict(status='candidate',submission_group='T3-PRIORITY-SIX-20260930',board='T3:gata4',version=version,method='priority_six_'+lane,path=str(path.relative_to(ROOT)),n_cells=7449,n_genes=500,seed=SEED,target_used='false',local_contract='pass',sha256=sha(path),server_score='',score_status='score_pending',notes=f'parent=v0009; scoped_parent={scoped_parent.relative_to(ROOT)}; run={RUN.relative_to(ROOT)}/{lane}; READY_NOT_SUBMITTED; no target truth; source/representation limitations in reports/t3_priority_six_20260930/REPORT.md')
            prepared.append(row);name=f't3_gata4__{lane}__{version}.h5ad';assert name==name.lower() and len(name)<=50
            members.append({'filename':name,'bytes':path.stat().st_size,'sha256':row['sha256']})
            mapping.append({'filename':name,'board':row['board'],'version':version,'canonical_path':row['path']})
            runs.append({'filename':name,'run_id':str(RUN.relative_to(ROOT)),'parent_version':'v0009','candidate_version':version})
            evidence.append({'filename':name,'input_lock':str((RUN/'INPUT_LOCK.json').relative_to(ROOT)),'contract':str((folder/'contract.json').relative_to(ROOT)),'result':str((RUN/lane/'CALIBRATED.json').relative_to(ROOT)),'core_model_result':str((RUN/lane/'RESULT.json').relative_to(ROOT))})
        # All checks finish before any candidate is added to the authority index.
        with index.open('a') as h:writer=csv.DictWriter(h,fieldnames=fields,delimiter='\t',lineterminator='\n');writer.writerows(prepared)
        for row,lane in zip(prepared,LANES):
            with (ROOT/'docs/coordination/T3_TRACKING.md').open('a') as h:h.write(f"\n- 2026-09-30｜T3-PRIORITY-SIX｜{row['version']} {lane}｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；{row['path']}；D-20260930-T3SIX-001。\n")
    path=ROOT/'deliveries/t3six__t3__upload__20260930.zip';path.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for m in mapping:z.write(ROOT/m['canonical_path'],m['filename'])
        for name,items in [('MANIFEST.tsv',members),('UPLOAD_MANIFEST.tsv',mapping),('RUN_ID_MAP.tsv',runs),('EVIDENCE_MANIFEST_POINTERS.tsv',evidence)]:z.writestr(name,tsv(items,list(items[0])))
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for m in members:assert hashlib.sha256(z.read(m['filename'])).hexdigest()==m['sha256']
    dump(RUN/'DELIVERY.json',{'status':'READY_NOT_SUBMITTED','zip':str(path.relative_to(ROOT)),'sha256':sha(path),'candidates':prepared,'members':members,'portal_upload':'NOT_RUN','server_scores':'NOT_RUN'})
    print('READY_NOT_SUBMITTED',str(path),flush=True)

if __name__=='__main__':main()
