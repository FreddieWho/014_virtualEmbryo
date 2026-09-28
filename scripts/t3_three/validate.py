"""Independent full-array replay, component/contract/identity checks, short-name export."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
import argparse,csv,json,hashlib,shutil
from pathlib import Path
import numpy as np
import anndata as ad
from .common import Context,ROOT,sha,dump,dense,read_model
from .models import predict,restore,responses
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.repair_ops import decode_rate


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--export',type=Path,required=True);args=ap.parse_args()
    assert json.loads((args.root/'COMPLETE.json').read_text())['status']=='ALL_THREE_EXECUTED'
    if (args.report/'VALIDATION.json').exists() or args.export.exists():raise FileExistsError('immutable validation/export')
    c=Context(args.root/'independent_validation');checks=[];newhashes={};hashcache={}
    with open(ROOT/'submissions/INDEX.tsv') as f:rows=list(csv.DictReader(f,delimiter='\t'))
    indexed={r['path']:r for r in rows};members=[]
    for lane in c.cfg['three']['lanes']:
        run=args.root/lane;result=json.loads((run/'RESULT.json').read_text());assert result['status']=='CANDIDATES_READY' and len(result['candidates'])==1
        for name,digest in json.loads((run/'INPUT_LOCK.json').read_text())['inputs'].items():
            p=ROOT/name
            if name.startswith('scripts/t3_three/'):p=run/'code_three'/Path(name).name
            elif name.startswith('scripts/t3_next/'):p=run/'code'/Path(name).name
            elif name.startswith('configs/t3_three/'):p=run/'code/design.json'
            key=str(p)
            if key not in hashcache:hashcache[key]=sha(p)
            assert hashcache[key]==digest,(name,'snapshot drift')
        for name,digest in json.loads((run/'COMPONENT_LOCK.json').read_text())['files'].items():assert sha(ROOT/name)==digest
        model=read_model(run/'model.pkl');assert model['cfg']==c.cfg['three']
        h=restore(model['hurdle']);a=c.x[c.rows][:,[c.gi]];cols=model['cols']
        d,prob,intensity=responses(h,a,np.zeros_like(a),c.coords[c.rows],c.plabels)
        original=c.base.copy();original[:,cols]=bounded_add(c.base[:,cols],d,.25);np.testing.assert_array_equal(original,c.best)
        graph=np.asarray(decode_rate(c.base,model['rate']),np.float32);graph[:,c.gi]=0;np.testing.assert_array_equal(graph,c.graph)
        out,detail=predict(model,c);item=result['candidates'][0];row=indexed[item['path']];path=ROOT/item['path'];candidate=ad.read_h5ad(path);actual=dense(candidate.X)
        assert sha(path)==item['sha256']==row['sha256'] and row['local_contract']=='pass' and row['score_status']=='score_pending'
        assert actual.shape==(7449,500) and np.isfinite(actual).all() and actual.min()>=0
        np.testing.assert_array_equal(out,actual);np.testing.assert_array_equal(candidate.obs_names,c.parent.obs_names);np.testing.assert_array_equal(candidate.var_names,c.genes);np.testing.assert_array_equal(candidate.obsm['spatial_3D'],c.parent.obsm['spatial_3D']);assert not actual[:,c.gi].any()
        assert json.loads((run/f'{lane}_CONTRACT.json').read_text())['status']=='PASS'
        assert json.loads((run/f'{lane}_CHECKS.json').read_text())['status']=='PASS'
        metadata=json.loads(candidate.uns['ve_t3_three']);assert metadata['model_sha256']==sha(run/'model.pkl') and metadata['design_sha256']==sha(run/'code/design.json')
        xhash=hashlib.sha256(actual.tobytes()).hexdigest();assert xhash not in newhashes;newhashes[xhash]=item['version']
        name=item['portal_file'];assert name==name.lower() and len(name)<=50
        members.append({'filename':name,'canonical_path':item['path'],'sha256':item['sha256'],'bytes':path.stat().st_size})
        checks.append({'lane':lane,'version':item['version'],'shape':list(actual.shape),'full_replay':'PASS','scored_components_replayed':'PASS','input_snapshots':'PASS','contract':'PASS','expression_sha256':xhash,'operator':detail})
        print('VALIDATED',lane,item['version'],flush=True)
    # Detect copied expression even if metadata/file bytes differ from older candidates.
    old_count=0
    for row in rows:
        if row['board']!='T3:gata4' or row['version'] in newhashes.values():continue
        path=ROOT/row['path']
        if not path.exists():continue
        old=ad.read_h5ad(path)
        if old.shape!=(7449,500):continue
        assert hashlib.sha256(dense(old.X).tobytes()).hexdigest() not in newhashes,('duplicate old expression',row['version'])
        old_count+=1
    diag=json.loads((args.root/'shared/LOCAL_DIAGNOSTICS.json').read_text());assert diag['full_WT_cells']==24826 and len(diag['factual_folds'])==4
    for record in diag['factual_folds']:
        fold=record['fold'];tr=c.blocks!=fold;te=~tr;assert tr.sum()==record['train_cells'] and te.sum()==record['test_cells']
        model=read_model(args.root/f'shared/fold{fold}.pkl');pred,_=model.predict(c.x[te][:,[c.gi]],c.coords[te],c.labels[te])
        mse=float(np.mean((pred-c.x[te][:,np.arange(500)!=c.gi])**2));assert abs(mse-record['factual_mse'])<1e-12
    args.export.mkdir(parents=True)
    for item in members:
        shutil.copy2(ROOT/item['canonical_path'],args.export/item['filename']);assert sha(args.export/item['filename'])==item['sha256']
    dump(args.export/'EXPORT_RECEIPT.json',{'status':'PASS','files':members,'portal_upload':'NOT_RUN'})
    dump(args.report/'VALIDATION.json',{'status':'PASS','routes':checks,'older_full_shape_artifacts_compared':old_count,'four_factual_fold_replays':'PASS','direct_export':str(args.export),'full_WT_cells':24826,'matched_KO_scorer':'NOT_RUN_NO_MATCHED_GATA4_TARGET'})
    print('ALL THREE VALIDATED AND EXPORTED',flush=True)


if __name__=='__main__':main()
