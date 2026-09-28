"""Fresh-process acceptance using persisted models, source data, contracts and selection receipts."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import argparse,json,csv,sys
from pathlib import Path
import anndata as ad
import numpy as np
from .common import ROOT,dense,sha,dump,indexed,read_model
from .models import predict


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);args=ap.parse_args();run=args.run.resolve();checks=[]
    cfg=json.loads((run/'code/design.json').read_text());result=json.loads((run/'RESULT.json').read_text());selected=json.loads((run/'SELECTED.json').read_text());final=json.loads((run/'FINAL_SELECTION.json').read_text());audit=json.loads((run/'AUDIT_BLOCK.json').read_text());dev=json.loads((run/'DEVELOPMENT.json').read_text())
    assert sha(run/'SELECTED.json')==audit['selection_sha256_before_open']==final['selection_sha256']
    assert sha(run/'DEVELOPMENT.json')==selected['development_sha256'];assert not selected['audit_opened']
    assert (run/'SELECTED.json').stat().st_mtime_ns<(run/'AUDIT_BLOCK.json').stat().st_mtime_ns
    assert selected['selected']==final['selected'];checks.append('selection locked before audit and unchanged')
    for family in ['source','learned']:
        lanes=cfg['selection'][family+'_family'];rank=sorted(lanes,key=lambda x:(dev['weighted_mean_group_mse'].get(x,float('inf')),lanes.index(x)));assert rank==selected['rankings'][family]
    checks.append('development ranking independently recomputed')
    for p,digest in json.loads((run/'INPUT_LOCK.json').read_text())['inputs'].items():
        path=ROOT/p
        if p.startswith('scripts/t3_next/'):path=run/'code'/Path(p).name
        elif p.startswith('scripts/t3_five_select/'):path=run/'code_five_select'/Path(p).name
        elif p.startswith('configs/t3_five_select/'):path=run/'code/design.json'
        assert sha(path)==digest,p
    checks.append('input and executed-code hashes')
    _,bp=indexed('v0009');base=ad.read_h5ad(bp);wt=ad.read_h5ad(ROOT/'data/E8.75.h5ad');genes=list(base.var_names);gi=genes.index('Gata4');rows=wt.obs_names.get_indexer(base.obs_names);x=dense(wt[:,genes].X);z=np.asarray(wt.obsm['spatial_3D'])[:,:3].astype(float);types=wt.obs.celltype.astype(str).to_numpy();blocks=np.searchsorted(np.quantile(z[:,2],[.25,.5,.75]),z[:,2],side='right');train=np.flatnonzero(np.isin(blocks,cfg['train_blocks']));cols=np.flatnonzero(np.arange(len(genes))!=gi)
    for lane in cfg['lanes']:
        local=read_model(run/'local_models'/f'{lane}.pkl');full=read_model(run/'full_models'/f'{lane}.pkl')
        np.testing.assert_array_equal(local['train_ids'],train);np.testing.assert_array_equal(full['train_ids'],np.arange(len(x)))
        if lane=='r3bag':
            for m,pool in [(local,train),(full,np.arange(len(x)))]:
                assert len(m['model'])==len(cfg['bootstrap_seeds'])==4
                for sampled in m['sampled_ids']:
                    assert np.isin(sampled,pool).all()
                    for typ in np.unique(types[pool]):assert np.sum(types[sampled]==typ)==np.sum(types[pool]==typ)
        if lane=='r4spline':
            positive=x[train,gi];positive=positive[positive>0];np.testing.assert_allclose(local['model'].knots,np.quantile(positive,cfg['spline_quantiles']))
        if lane=='r5local':
            for _,_,ids in local['model'].groups.values():assert np.isin(ids,train).all()
        if lane in ['r1active','r2gene']:
            np.testing.assert_allclose(local['model'].encoder.scaler.mean_,x[train][:,[gi]].mean(0),rtol=1e-5)
        checks.append(lane+' local training boundary and full-data fit identity')
        a=x[rows][:,[gi]];expected=dense(base.X).copy();expected[:,cols]=predict(full,expected[:,cols],a,np.zeros_like(a),z[rows],types[rows],rows)
        research=ad.read_h5ad(run/lane/'research.h5ad');np.testing.assert_array_equal(dense(research.X),expected);np.testing.assert_array_equal(np.load(run/lane/'prediction.npy'),expected)
        assert research.shape==(7449,500) and list(research.obs_names)==list(base.obs_names) and list(research.var_names)==genes
        np.testing.assert_array_equal(research.obsm['spatial_3D'],base.obsm['spatial_3D']);assert np.isfinite(expected).all() and np.all(expected>=0) and np.all(expected[:,gi]==0)
        assert json.loads((run/lane/'CONTRACT.json').read_text())['status']=='PASS'
        checks.append(lane+' persisted-model replay, values, axes and spatial identity')
    assert len(result['candidates'])==3 and {r['lane'] for r in result['candidates']}==set(final['selected'])
    with (ROOT/'submissions/INDEX.tsv').open() as f:index={r['path']:r for r in csv.DictReader(f,delimiter='\t')}
    for candidate in result['candidates']:
        row=index[candidate['path']];assert sha(ROOT/row['path'])==row['sha256']==candidate['sha256'];assert row['score_status']=='score_pending' and row['local_contract']=='pass'
        a=ad.read_h5ad(ROOT/row['path']);np.testing.assert_array_equal(dense(a.X),np.load(run/candidate['lane']/'prediction.npy'))
    checks.append('exactly three registered candidates match full route predictions')
    dump(run/'VALIDATION.json',{'status':'PASS','checks':checks,'check_count':len(checks),'validator_sha256':sha(Path(__file__)),'limits':'engineering and split integrity only; no matched KO target; no server score'})
    print(json.dumps({'status':'PASS','checks':len(checks)}))
if __name__=='__main__':main()
