"""Deliver the predeclared server-informed half-step candidate."""
import csv
import fcntl
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'scripts'),str(ROOT/'docs/batch3/interfaces')]
from t3_sparse_response.evaluate import dense, dump, emit, sha, load, fit_log_multiplier
from virtual_embryo_tools.contract_io import validate_h5ad_contract

OUT = ROOT/'reports/t3_halfstep_20261003'
RUN = ROOT/'artifacts/t3_halfstep_20261003'

def tsv(rows):
    buf=io.StringIO()
    w=csv.DictWriter(buf,list(rows[0]),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(rows)
    return buf.getvalue()

def main():
    assert not (OUT/'HANDOFF.json').exists(), 'Never overwrite a delivery'
    result=json.loads((OUT/'EVALUATION_COMPLETE.json').read_text())
    selection=json.loads((OUT/'SELECTION.json').read_text())
    assert selection['strength']==0.5 and 'half step' in selection['basis']
    assert selection==result['selection']
    assert sha(OUT/'DESIGN.md')==selection['design_sha256']
    assert sha(OUT/'FULL_MATRIX_METRICS.tsv')==result['metrics_sha256']
    beta=np.load(RUN/'LOG_MULTIPLIER.npy')
    assert sha(RUN/'LOG_MULTIPLIER.npy')==result['multiplier_sha256']
    _,_,ctrl,cfg,predict=load()
    delta=predict(sum(cfg['split'].values(),[]),'Gata4')
    np.testing.assert_array_equal(beta,fit_log_multiplier(ctrl,delta))
    strength=selection['strength']
    with (ROOT/'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        index=ROOT/'submissions/INDEX.tsv'
        with index.open() as f:
            reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;rows=list(reader)
        t3=[r for r in rows if r['board']=='T3:gata4']
        record=next(r for r in t3 if r['version']=='v0048')
        parent_path=ROOT/record['path']
        assert sha(parent_path)==record['sha256']
        parent=ad.read_h5ad(parent_path)
        base=dense(parent.X)
        panel=(ROOT/'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
        assert parent.var_names.tolist()==panel and parent.shape==(7449,500)
        pred=emit(base,beta,strength)
        gi=panel.index('Gata4');pred[:,gi]=0
        assert np.array_equal(pred>0,base>0)
        assert np.isfinite(pred).all() and np.all(pred>=0) and np.any(pred!=base)
        np.testing.assert_allclose(emit(base,np.zeros(500),strength),base,rtol=1e-6,atol=1e-7)
        assert np.max(np.abs(beta*strength))<=np.log(2)+1e-9
        candidate=parent.copy();candidate.X=pred
        candidate.uns['ve_contract']={'normalization':'log_normalized','source':'v0048 bounded positive-intensity response scaling; exact support preserved'}
        candidate.uns['t3_sparse_response']={'parent_version':'v0048','source_model':'locked t3_autoresearch retained model',
            'strength':strength,'raw_intensity_ratio_bound':np.array([float(np.exp(-np.log(2)*strength)),float(np.exp(np.log(2)*strength))]),
            'operator':'log1p(expm1(parent.X)*exp(strength*source_log_multiplier)); Gata4=0',
            'source_full_matrix_selection':False,'target_truth_used':False,'target_transfer_validated':False,
            'layers_and_raw':'immutable parent references; prediction in X'}
        used=[int(r['version'][1:]) for r in t3]
        for p in (ROOT/'submissions/candidates/T3_gata4').iterdir():
            m=re.match(r'v(\d+)_',p.name)
            if m:used.append(int(m.group(1)))
        version=f'v{max(used)+1:04d}'
        folder=ROOT/f'submissions/candidates/T3_gata4/{version}_half_scale'
        folder.mkdir(exist_ok=False);path=folder/'submission.h5ad'
        candidate.write_h5ad(path,compression='gzip')
        contract=validate_h5ad_contract(path,task='T3',board='gata4',
            scorer_lock=ROOT/'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',
            parent_path=parent_path,parent_sha256=record['sha256'])
        dump(folder/'contract.json',contract)
        assert contract['status']=='PASS',contract
        reread=ad.read_h5ad(path)
        np.testing.assert_array_equal(dense(reread.X),pred)
        np.testing.assert_array_equal(reread.obsm['spatial_3D'],parent.obsm['spatial_3D'])
        assert reread.obs_names.equals(parent.obs_names) and reread.var_names.equals(parent.var_names)
        diag={'shape':list(pred.shape),'parent':'v0048','strength':strength,
            'parent_density':float(np.mean(base>0)),'output_density':float(np.mean(pred>0)),
            'zero_to_positive_entries':int(((base==0)&(pred>0)).sum()),'positive_to_zero_entries':int(((base>0)&(pred==0)).sum()),
            'changed_entries':int((pred!=base).sum()),'changed_genes':int(np.any(pred!=base,axis=0).sum()),
            'mean_absolute_change':float(np.abs(pred-base).mean()),
            'intensity_ratio_min':float(np.exp(strength*beta).min()),'intensity_ratio_max':float(np.exp(strength*beta).max()),
            'coordinates_preserved':True,'Gata4_zero':bool(np.all(pred[:,gi]==0)),
            'source_inference_replay':'PASS','roundtrip':'PASS','target_score':'NOT_RUN_NO_LEGAL_TARGET_TRUTH','blocks_submission':False}
        dump(OUT/'OUTPUT_CHECK.json',diag)
        dump(RUN/'INPUT_LOCK.json',{'source_manifest':'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json',
            'source_manifest_sha256':sha(ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'),
            'model_sha256':sha(ROOT/'scripts/t3_autoresearch/retained_model.py'),'evaluation_sha256':sha(OUT/'EVALUATION_COMPLETE.json'),
            'code':{p.name:sha(p) for p in Path(__file__).parent.glob('*.py')},'parent_index_version':'v0048','parent_sha256_verified':True})
        short=f't3_gata4__half_scale__{version}.h5ad'
        assert len(short)<=50 and short==short.lower()
        direct=ROOT/'deliveries'/short;assert not direct.exists();shutil.copyfile(path,direct)
        digest=sha(path);assert sha(direct)==digest
        package=ROOT/'deliveries/t3half__t3__upload__20261003.zip'
        with zipfile.ZipFile(package,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
            z.write(path,short)
            tables={'MANIFEST.tsv':[{'filename':short,'bytes':path.stat().st_size,'sha256':digest}],
                'UPLOAD_MANIFEST.tsv':[{'filename':short,'board':'T3:gata4','version':version,'canonical_path':str(path.relative_to(ROOT))}],
                'RUN_ID_MAP.tsv':[{'filename':short,'run_id':str(RUN.relative_to(ROOT)),'parent_version':'v0048','candidate_version':version}],
                'EVIDENCE_MANIFEST_POINTERS.tsv':[{'filename':short,'input_lock':str((RUN/'INPUT_LOCK.json').relative_to(ROOT)),
                    'contract':str((folder/'contract.json').relative_to(ROOT)),'diagnostics':str((OUT/'OUTPUT_CHECK.json').relative_to(ROOT)),
                    'source_report':str((OUT/'REPORT.md').relative_to(ROOT))}]}
            for name,rr in tables.items():z.writestr(name,tsv(rr))
        with zipfile.ZipFile(package) as z:assert hashlib.sha256(z.read(short)).hexdigest()==digest
        new=dict(status='candidate',submission_group='T3-HALFSTEP-20261003',board='T3:gata4',version=version,
            method='incumbent_sparse_half_scale',path=str(path.relative_to(ROOT)),n_cells=7449,n_genes=500,seed='0',target_used='false',
            local_contract='pass',sha256=digest,server_score='',score_status='score_pending',
            notes=f'parent=v0048; server-informed fixed half-step strength={strength}; exact parent support retained; READY_NOT_SUBMITTED; target transfer unvalidated; reports/t3_halfstep_20261003/REPORT.md')
        with index.open('a') as f:csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n').writerow(new)
        handoff={'task':'T3:gata4','version':version,'candidate_id':f'candidate/T3_gata4/{version}_half_scale','parent_version':'v0048',
            'artifact':new['path'],'sha256':digest,'contract':'PASS','download_h5ad':str(direct.relative_to(ROOT)),
            'zip':str(package.relative_to(ROOT)),'zip_sha256':sha(package),'status':'READY_NOT_SUBMITTED',
            'proposed_decision':'exploratory upload; incumbent unchanged until server return',
            'risks':['source domain transfer unvalidated','source data reused; not a new independent holdout','unchanged detection support cannot model newly activated genes'],
            'blocker':'no legal target truth; blocks_submission:false'}
        dump(OUT/'HANDOFF.json',handoff)
        with (ROOT/'docs/coordination/T3_TRACKING.md').open('a') as f:f.write(f'\n- 2026-10-03｜T3新候选{version}｜父v0048，固定半步strength={strength}，有界强度倍率、母本零值结构严格保留；7449×500、contract PASS、未提交/未评分。reports/t3_halfstep_20261003/REPORT.md；D-20261003-T3HALF-001。\n')
    print(json.dumps(handoff,ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
