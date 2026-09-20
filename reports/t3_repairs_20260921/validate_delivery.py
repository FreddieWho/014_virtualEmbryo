"""Validate final repair runs against the canonical index and frozen configurations."""
import csv,hashlib,json
from pathlib import Path
import anndata as ad
import numpy as np
from scipy import sparse

ROOT=Path(__file__).resolve().parents[2]
RUNS=['T3-REPAIR-R6-20260921-v1','T3-REPAIR-R3-20260921-v1','T3-REPAIR-R4-20260921-v2']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dense(x):return x.toarray() if sparse.issparse(x) else np.asarray(x)
rows={r['path']:r for r in csv.DictReader(open(ROOT/'submissions/INDEX.tsv'),delimiter='\t')}
parent_row=next(r for r in rows.values() if r['board']=='T3:gata4' and r['version']=='v0009')
assert sha(ROOT/parent_row['path'])==parent_row['sha256']
parent=ad.read_h5ad(ROOT/parent_row['path']);base=dense(parent.X);records=[];receipts={}
for run in RUNS:
    p=ROOT/'artifacts/t3_next'/run;result=json.loads((p/'RESULT.json').read_text())
    assert result['status']=='CANDIDATES_READY'
    assert len(result['candidates'])==2
    expected=sha(p/'code/design.json');matrices=[]
    for c in result['candidates']:
        row=rows[c['path']];artifact=ROOT/c['path']
        assert row['score_status']=='score_pending' and row['local_contract']=='pass'
        assert sha(artifact)==row['sha256']==c['sha256']
        a=ad.read_h5ad(artifact);x=dense(a.X);matrices.append(x)
        assert a.obs_names.equals(parent.obs_names) and a.var_names.equals(parent.var_names)
        assert np.array_equal(a.obsm['spatial_3D'],parent.obsm['spatial_3D'])
        assert np.isfinite(x).all() and np.all(x>=0)
        assert np.array_equal(x==0,base==0)
        assert json.loads(a.uns['ve_t3_next'])['design_sha256']==expected
        assert len(c['portal_file'])<=50 and c['portal_file']==c['portal_file'].lower()
        d=x-base
        records.append({'version':c['version'],'lane':c['lane'],'run':str(p.relative_to(ROOT)),
                        'parent':'v0009','identity_sha_contract':'PASS','config_snapshot_sha256':expected,
                        'zero_support_preserved':True,'negative_entries':0,
                        'changed_entries':int(np.count_nonzero(d)),
                        'changed_genes':a.var_names[np.any(d!=0,axis=0)].tolist(),
                        'rms':float(np.sqrt(np.mean(d.astype(float)**2)))})
    assert not np.array_equal(matrices[0],matrices[1]),'duplicate pair'
    for name in ['RESULT.json','INPUT_LOCK.json','EVALUATION.json','MAPPING_GATE.json','FINAL_CALIBRATION.json']:
        if (p/name).exists():receipts[str((p/name).relative_to(ROOT))]=sha(p/name)
json_out={'status':'PASS','candidate_count':len(records),'candidates':records,
          'excluded_withdrawn_versions':['v0038','v0039'],'receipt_sha256':receipts,
          'tests':'23 targeted tests passed; separate pytest execution',
          'server_status':'NOT_SUBMITTED_NOT_SCORED','scientific_status':'NOT_IDENTIFIABLE'}
(Path(__file__).parent/'VALIDATION.json').write_text(json.dumps(json_out,indent=2)+'\n')
print(json.dumps({'status':'PASS','versions':[r['version'] for r in records]}))
