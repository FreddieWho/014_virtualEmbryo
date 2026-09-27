"""Audit full five-route receipts, independently replay saved models and package candidates."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
import argparse,csv,hashlib,io,json,pickle,zipfile
from pathlib import Path
import numpy as np
import anndata as ad
from .common import ROOT,sha,dump,dense,indexed
from .models import predict
from .audit_fit import audit

LANES=['n1stack','n2composition','n3states','o1caldensity','o2shrinkmass']


def table(rows):
    text=io.StringIO();writer=csv.DictWriter(text,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows);return text.getvalue()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--zip',type=Path,required=True);args=ap.parse_args()
    if args.zip.exists() or (args.report/'VALIDATION.json').exists():raise FileExistsError('immutable final delivery')
    _,parentpath=indexed('v0024');parent=ad.read_h5ad(parentpath);base=dense(parent.X);genes=list(parent.var_names)
    _,lp=indexed('v0023');legacy=dense(ad.read_h5ad(lp).X)
    a=ad.read_h5ad(ROOT/'data/E9.5_RNA.h5ad');ix=a.var_names.get_indexer(genes);x=dense(a.X[:,ix]);types=a.obs.celltype.astype(str).to_numpy();rows=a.obs_names.get_indexer(parent.obs_names)
    if (rows<0).any():raise ValueError('rows missing')
    early=ad.read_h5ad(ROOT/'data/E8.5_RNA.h5ad');ex=dense(early.X[:,early.var_names.get_indexer(genes)]);et=early.obs.celltype.astype(str).to_numpy();del early
    raw=x[rows];labels=types[rows]
    checks=[];members=[];mapping=[];runmap=[];pointers=[];expression_hashes=set();verified_hashes={}
    for lane in LANES:
        run=args.root/lane;result=json.loads((run/'RESULT.json').read_text());assert result['report_scorer']=='EXECUTED'
        assert result['status'] in ['CANDIDATES_READY','COMPUTED_NO_CANDIDATE']
        scorer=json.loads((run/'SCORER.json').read_text());assert scorer['meta']['genes']==32285 and scorer['meta']['prediction_cells']==3357 and scorer['meta']['truth_cells']==3411
        splits=np.load(run/'SPLITS.npz')
        for stage,total in [('85',16787),('95',17057)]:
            groups=[splits[name+stage] for name in ['train','report','reserved']]
            joined=np.concatenate(groups)
            assert len(joined)==total and np.array_equal(np.sort(joined),np.arange(total))
        assert np.array_equal(splits['recipient95'],rows)
        assert json.loads((run/'SCORER_PROCESS.json').read_text())['exit_code']==0
        assert json.loads((run/'MODEL_REPLAY.json').read_text())['exact_equal']
        lock=json.loads((run/'INPUT_LOCK.json').read_text());cfg=json.loads((run/'code/design.json').read_text())
        for name,digest in lock['inputs'].items():
            if name.startswith('scripts/t1_round2/'):p=run/'code'/Path(name).name
            elif name.startswith('scripts/t1_five/'):p=run/'code_legacy'/Path(name).name
            elif name.startswith('configs/t1_round2/'):p=run/'code/design.json'
            else:p=ROOT/name
            key=str(p)
            if key not in verified_hashes:verified_hashes[key]=sha(p)
            assert verified_hashes[key]==digest,(name,'drift')
        for name,digest in json.loads((run/'COMPONENT_LOCK.json').read_text()).items():
            assert sha(ROOT/name)==digest
        with (run/'final_model.pkl').open('rb') as f:model=pickle.load(f)
        assert model['cfg']==cfg
        fit_checks=audit(model,ex,et,x,types)
        replay,detail=predict(model,raw,labels,legacy);del model
        record={'lane':lane,'fitted_parameter_audit':fit_checks,'run':str(run),'scorer_full_panel':'PASS','disjoint_complete_splits':'PASS','input_and_code_hashes':'PASS','model_sha256':sha(run/'final_model.pkl'),'full_model_replay':'PASS','shape':list(replay.shape),'candidates':len(result['candidates'])}
        for c in result['candidates']:
            row,path=indexed(c['version']);pred=ad.read_h5ad(path);actual=dense(pred.X)
            assert c['sha256']==row['sha256'] and row['score_status']=='score_pending' and row['local_contract']=='pass'
            assert list(pred.var_names)==genes and np.array_equal(pred.obs_names,parent.obs_names)
            assert actual.shape==(5118,32285) and np.isfinite(actual).all() and (actual>=0).all()
            np.testing.assert_array_equal(actual,replay)
            assert json.loads((run/'CONTRACT.json').read_text())['status']=='PASS'
            assert json.loads((run/'CHECKS.json').read_text())['status']=='PASS'
            np.testing.assert_array_equal(pred.uns['predicted_celltype'],detail['predicted_types'])
            metadata=json.loads(pred.uns['ve_t1_round2']);assert metadata['model_sha256']==record['model_sha256'] and metadata['design_sha256']==sha(run/'code/design.json')
            digest=hashlib.sha256(actual.tobytes()).hexdigest();assert digest not in expression_hashes;expression_hashes.add(digest)
            record.update(version=c['version'],contract='PASS',expression_sha256=digest,changed_entries=int(np.count_nonzero(actual!=base)),changed_cells=int(np.any(actual!=base,axis=1).sum()),changed_genes=int(np.any(actual!=base,axis=0).sum()))
            name=c['portal_file'];assert name==name.lower() and len(name)<=50
            members.append({'filename':name,'sha256':c['sha256'],'bytes':path.stat().st_size})
            mapping.append({'filename':name,'board':'T1:val','version':c['version'],'canonical_path':c['path']})
            runmap.append({'filename':name,'run_id':str(run),'parent_version':'v0024'})
            pointers.append({'filename':name,'contract':str(run/'CONTRACT.json'),'result':str(run/'RESULT.json'),'input_lock':str(run/'INPUT_LOCK.json')})
        if not result['candidates']:assert json.loads((run/'CHECKS.json').read_text())['status'] in ['FAILED_ENGINEERING','NO_OP']
        checks.append(record);print('AUDIT PASS',lane,record.get('version','no candidate'),flush=True)
    assert members
    args.zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.zip,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for m in mapping:z.write(ROOT/m['canonical_path'],m['filename'])
        for name,rows_ in [('MANIFEST.tsv',members),('UPLOAD_MANIFEST.tsv',mapping),('RUN_ID_MAP.tsv',runmap),('EVIDENCE_MANIFEST_POINTERS.tsv',pointers)]:z.writestr(name,table(rows_))
    with zipfile.ZipFile(args.zip) as z:
        for m in members:
            h=hashlib.sha256()
            with z.open(m['filename']) as f:
                for block in iter(lambda:f.read(4<<20),b''):h.update(block)
            assert h.hexdigest()==m['sha256']
        assert z.testzip() is None
    dump(args.report/'VALIDATION.json',{'status':'PASS','routes':checks,'routes_executed':5,'new_routes':3,'existing_optimizations':2,'full_panel_scorers':5,'high_scoring_combination_executed':True,'package_candidates':len(members),'server_scored':False})
    dump(args.zip.with_suffix('.receipt.json'),{'status':'READY_NOT_SUBMITTED','path':str(args.zip),'sha256':sha(args.zip),'members':len(members),'runs':[str(args.root/lane) for lane in LANES],'portal_upload':'NOT_RUN','server_scoring':'NOT_RUN'})
    print('DELIVERY',args.zip,'candidates',len(members),flush=True)


if __name__=='__main__':main()
