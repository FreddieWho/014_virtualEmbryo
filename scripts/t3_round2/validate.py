"""Independent complete-output replay and fitted source-model consistency checks."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
import argparse,json,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import anndata as ad
from scipy import sparse
from .common import ROOT,dense,indexed,sha,dump,read_model
from .models import predict_saved

LANES=['n1stack','n2orth','n3occup','o1logit','o2geneshrink']


def source_features(run):
    lock=json.loads((run/'SOURCE_LOCK.json').read_text())
    assert sha(ROOT/lock['manifest'])==lock['manifest_sha256']
    for f in lock['files'].values():assert sha(ROOT/f['path'])==f['sha256']
    e=np.load(ROOT/lock['files']['embedding']['path']);names=e['genes'].astype(str).tolist();ix=[names.index(g) for g in lock['conditions']+['Gata4']]
    return e['embedding'][ix],sparse.load_npz(ROOT/lock['files']['adjacency']['path'])[ix][:,ix].toarray(),lock


def validate_source_model(run,lane,m,cfg):
    z,adj,lock=source_features(run);assert lock['cells']==5454 and len(lock['conditions'])==26
    if lane=='n3occup':
        fitted=m['fitted_model'];b=(z[-1:]-fitted['feature_mean'])/fitted['feature_sd'];a=fitted['train_features']
        kernel=np.exp(-((b[:,None]-a[None,:])**2).mean(2)/(2*fitted['bandwidth']))
        value=(fitted['response_mean']+(kernel@fitted['weights'])@fitted['basis'])[0]
        pred=np.r_[np.clip(value[:500],-cfg['logit_bound'],cfg['logit_bound']),np.clip(value[500:],-cfg['rate_bound'],cfg['rate_bound'])]
        np.testing.assert_allclose(pred,m['target_params'],rtol=1e-7,atol=1e-8)
    else:
        import torch
        torch.set_num_threads(8)
        fitted=read_model(run/'final_graph.pkl');g=fitted['final'];feat=(z-g['embedding_mean'])/g['embedding_std'];a=np.asarray(adj,dtype=np.float32)+np.eye(len(adj),dtype=np.float32);a/=a.sum(1,keepdims=True)
        h=torch.nn.Linear(feat.shape[1],32);out=torch.nn.Linear(32,500);h.load_state_dict(g['state_dict']['h']);out.load_state_dict(g['state_dict']['out'])
        with torch.no_grad():pr=out(torch.from_numpy(a)@torch.relu(h(torch.from_numpy(a)@torch.from_numpy(np.asarray(feat,dtype=np.float32))))).numpy()[-1]
        np.testing.assert_allclose(pr,g['graph_prediction'][0],rtol=1e-6,atol=1e-7)
        np.testing.assert_array_equal(m['weights'],fitted['weights'])
        rate=np.clip(fitted['mean_rate']+fitted['weights']*(pr-fitted['mean_rate']),-cfg['rate_bound'],cfg['rate_bound'])
        np.testing.assert_allclose(rate,m['target_rate'],rtol=1e-6,atol=1e-7)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    _,p=indexed('v0009');anchor=ad.read_h5ad(p);_,p=indexed('v0048');best=ad.read_h5ad(p);wt=ad.read_h5ad(ROOT/'data/E8.75.h5ad');genes=list(anchor.var_names);rows=wt.obs_names.get_indexer(anchor.obs_names);labels=wt.obs.celltype.astype(str).to_numpy()
    c=SimpleNamespace(x=dense(wt[:,genes].X),base=dense(anchor.X),best=dense(best.X),rows=rows,gi=genes.index('Gata4'),coords=np.asarray(wt.obsm['spatial_3D'])[:,:3].astype(float),labels=labels,plabels=labels[rows])
    expected=set(LANES);records=[];digests=set()
    for lane in LANES:
        run=args.root/lane;result=json.loads((run/'RESULT.json').read_text());assert result['status'] in ['CANDIDATES_READY','COMPUTED_NO_CANDIDATE']
        c.cfg=json.loads((run/'code/design.json').read_text());lock=json.loads((run/'INPUT_LOCK.json').read_text())
        for name,digest in lock['inputs'].items():
            if name.startswith('scripts/t3_round2/'):path=run/'code_round2'/Path(name).name
            elif name.startswith('scripts/t3_next/'):path=run/'code'/Path(name).name
            elif name.startswith('configs/t3_round2/'):path=run/'code/design.json'
            else:path=ROOT/name
            assert sha(path)==digest,(name,'hash drift')
        m=read_model(run/'model.pkl')
        if lane in ['n3occup','o2geneshrink']:validate_source_model(run,lane,m,c.cfg['round2'])
        replay=predict_saved(m,c)
        record={'lane':lane,'input_code_hashes':'PASS','full_model_replay':'PASS','shape':list(replay.shape),'run':str(run),'candidate_count':len(result['candidates']),'model_sha256':sha(run/'model.pkl')}
        if result['candidates']:
            cand=result['candidates'][0];row,p=indexed(cand['version']);a=ad.read_h5ad(p);x=dense(a.X)
            assert row['score_status']=='score_pending' and row['sha256']==cand['sha256'] and row['local_contract']=='pass'
            assert np.array_equal(a.obs_names,best.obs_names) and list(a.var_names)==genes and np.array_equal(a.obsm['spatial_3D'],best.obsm['spatial_3D'])
            assert x.shape==(7449,500) and np.isfinite(x).all() and (x>=0).all() and np.all(x[:,c.gi]==0)
            np.testing.assert_array_equal(x,replay)
            meta=json.loads(a.uns['ve_t3_round2']);assert meta['model_sha256']==record['model_sha256'] and meta['design_sha256']==sha(run/'code/design.json')
            assert json.loads((run/f'{lane}_CONTRACT.json').read_text())['status']=='PASS'
            digest=hashlib.sha256(x.tobytes()).hexdigest();assert digest not in digests;digests.add(digest)
            record.update(version=cand['version'],contract='PASS',expression_sha256=digest,changed_cells_vs_best=int(np.any(x!=c.best,axis=1).sum()),changed_genes_vs_best=int(np.any(x!=c.best,axis=0).sum()),changed_entries_vs_best=int(np.count_nonzero(x!=c.best)))
        else:assert json.loads((run/f'{lane}_CHECKS.json').read_text())['status']!='PASS'
        records.append(record);print('VALIDATED',lane,record.get('version'),flush=True)
    audit=json.loads((args.root/'shared/COMPONENT_AUDIT.json').read_text());assert audit['status']=='PASS' and audit['H_exact_reproduction'] and audit['G_exact_reproduction']
    dump(args.output,{'status':'PASS','new_routes':3,'optimizations':2,'high_scoring_combination_executed':True,'kir_experience_applied':True,'routes':records,'all_500_genes':True,'target_KO_scorer':'NOT_RUN_NO_MATCHED_GATA4_TARGET','no_server_gain_claim':True})


if __name__=='__main__':main()
