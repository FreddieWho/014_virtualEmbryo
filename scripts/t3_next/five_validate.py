"""Replay all five final prediction operators and audit immutable candidate identity."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='8'
import argparse,csv,json,pickle
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import anndata as ad
from scipy import sparse
from .common import ROOT,sha,dump,dense,indexed
from .five import Hurdle
from .five_ops import quantile_response,bounded_add,stability_weight
from .repair import mechanism_predict
from .repair_ops import decode_rate


def read_model(run,name):
    with (run/name).open('rb') as f:return pickle.load(f)


def source_features(run):
    lock=json.loads((run/'SOURCE_LOCK.json').read_text())
    assert sha(ROOT/lock['manifest'])==lock['manifest_sha256']
    for f in lock['files'].values():assert sha(ROOT/f['path'])==f['sha256']
    emb=np.load(ROOT/lock['files']['embedding']['path']);names=emb['genes'].astype(str).tolist()
    ii=[names.index(g) for g in lock['conditions']+['Gata4']]
    z=emb['embedding'][ii]
    adj=sparse.load_npz(ROOT/lock['files']['adjacency']['path'])[ii][:,ii].toarray()
    return z,adj


def replay(c,run,lane):
    cfg=c.cfg['five'];out=c.base.copy()
    if lane=='n1quant':
        m=read_model(run,'quantile_model.pkl');cols=m['cols']
        depth=np.log1p(np.expm1(c.x[:,np.arange(500)!=c.gi]).sum(1))
        for g in m['groups']:
            ix=np.flatnonzero((c.plabels==g['type'])&(np.searchsorted(g['edges'],depth[c.rows],side='right')==g['bin'])&(c.x[c.rows,c.gi]>=g['high']))
            if len(ix):out[np.ix_(ix,cols)]=quantile_response(c.base[np.ix_(ix,cols)],g['hi'],g['lo'],m['strength'],m['bound'])
    elif lane=='n2hurdle':
        model=read_model(run,'hurdle_model.pkl');m=Hurdle();m.encoder=model['encoder'];m.positive=model['positive'];cols=model['cols']
        a=c.x[c.rows][:,[c.gi]];z=c.coords[c.rows]
        factual,_=m.predict(a,z,c.plabels);cf,_=m.predict(np.zeros_like(a),z,c.plabels)
        out[:,cols]=bounded_add(c.base[:,cols],cf-factual,cfg['hurdle_strength'])
    elif lane=='n3latent':
        m=read_model(run,'final_model.pkl');z,_=source_features(run)
        target=(z[-1:]-m['feature_mean'])/m['feature_sd']
        cross=np.exp(-((target[:,None]-m['train_features'][None,:])**2).mean(2)/(2*m['bandwidth']))
        rate=(m['response_mean']+cross@m['weights']@m['basis'])[0]
        rate=np.clip(rate,-cfg['rate_bound'],cfg['rate_bound'])
        np.testing.assert_allclose(rate,np.load(run/'target_rate.npy'),atol=1e-8,rtol=1e-7)
        out=decode_rate(c.base,rate)
    elif lane=='o1stable':
        m=read_model(run,'final_model.pkl');saved=np.load(run/'stability.npz')
        assert np.all(saved['effects'][:,c.gi]==0)
        np.testing.assert_array_equal(stability_weight(saved['effects'],cfg['stability_prior']),m['weights'])
        z=np.column_stack([np.log1p(np.expm1(c.x).sum(1)),c.coords]);actual=c.x[c.rows]
        cf=mechanism_predict(c,m['models'],actual,z[c.rows],c.plabels)
        rate=np.zeros_like(cf,dtype=float);mask=c.base>0
        rate[mask]=np.log(np.maximum(np.expm1(cf[mask]),1e-20)/np.expm1(c.base[mask]))
        out=decode_rate(c.base,np.clip(rate,-cfg['rate_bound'],cfg['rate_bound'])*m['weights'])
    elif lane=='o2shrink':
        import torch
        torch.set_num_threads(8)
        saved=read_model(run,'final_model.pkl');model=saved['model'];z,adj=source_features(run)
        z=np.asarray((z-model['embedding_mean'])/model['embedding_std'],dtype=np.float32)
        a=np.asarray(adj,dtype=np.float32)+np.eye(len(adj),dtype=np.float32);a/=np.maximum(a.sum(1,keepdims=True),1e-8)
        h=torch.nn.Linear(z.shape[1],32);layer=torch.nn.Linear(32,500)
        h.load_state_dict(model['state_dict']['h']);layer.load_state_dict(model['state_dict']['out'])
        with torch.no_grad():pr=layer(torch.from_numpy(a)@torch.relu(h(torch.from_numpy(a)@torch.from_numpy(z)))).numpy()[-1]
        np.testing.assert_allclose(pr,model['graph_prediction'][0],atol=1e-7,rtol=1e-6)
        rate=np.clip(saved['mean_rate']+saved['weight']*(pr-saved['mean_rate']),-cfg['rate_bound'],cfg['rate_bound'])
        np.testing.assert_allclose(rate,np.load(run/'target_rate.npy'),atol=1e-7,rtol=1e-6)
        out=decode_rate(c.base,rate)
    else:raise ValueError(lane)
    out[:,c.gi]=0
    return np.asarray(out,dtype=np.float32)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--runs',nargs=5,type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    _,p=indexed('v0009');parent=ad.read_h5ad(p);wt=ad.read_h5ad(ROOT/'data/E8.75.h5ad');genes=list(parent.var_names)
    rows=wt.obs_names.get_indexer(parent.obs_names);labels=wt.obs.celltype.astype(str).to_numpy()
    c=SimpleNamespace(base=dense(parent.X),x=dense(wt[:,genes].X),rows=rows,genes=genes,gi=genes.index('Gata4'),labels=labels,plabels=labels[rows],coords=np.asarray(wt.obsm['spatial_3D'])[:,:3].astype(float))
    records=[];matrices=[]
    for run in args.runs:
        result=json.loads((run/'RESULT.json').read_text());assert result['status']=='CANDIDATES_READY' and len(result['candidates'])==1
        cc=result['candidates'][0];lane=cc['lane'];row,path=indexed(cc['version']);a=ad.read_h5ad(path);x=dense(a.X)
        assert row['score_status']=='score_pending' and row['local_contract']=='pass'
        assert sha(path)==cc['sha256'] and x.shape==(7449,500)
        assert np.array_equal(a.obs_names,parent.obs_names) and np.array_equal(a.var_names,parent.var_names)
        assert np.array_equal(a.obsm['spatial_3D'],parent.obsm['spatial_3D'])
        assert np.isfinite(x).all() and (x>=0).all() and np.all(x[:,c.gi]==0)
        assert json.loads((run/(lane+'_CONTRACT.json')).read_text())['status']=='PASS'
        assert json.loads((run/(lane+'_CHECKS.json')).read_text())['status']=='PASS'
        lock=json.loads((run/'INPUT_LOCK.json').read_text())
        for name,digest in lock['inputs'].items():
            if name.startswith('scripts/t3_next/'):p=run/'code'/Path(name).name
            elif name.startswith('configs/t3_next/'):p=run/'code/design.json'
            else:p=ROOT/name
            assert sha(p)==digest,(name,'hash drift')
        c.cfg=json.loads((run/'code/design.json').read_text())
        metadata=json.loads(a.uns['ve_t3_next']);assert metadata['design_sha256']==sha(run/'code/design.json')
        reconstructed=replay(c,run,lane)
        np.testing.assert_array_equal(reconstructed,x)
        for previous in matrices:assert not np.array_equal(previous,x)
        matrices.append(x)
        model_hashes={str(p.relative_to(run)):sha(p) for p in run.glob('*.pkl')}
        records.append({'lane':lane,'version':cc['version'],'candidate_sha_matches_index':True,'contract':'PASS','snapshot_inputs':'PASS','exact_model_replay':'PASS','pairwise_distinct':True,'changed_entries':int(np.count_nonzero(x!=c.base)),'changed_genes':int(np.any(x!=c.base,axis=0).sum()),'changed_cells':int(np.any(x!=c.base,axis=1).sum()),'zero_to_positive':int(np.sum((c.base==0)&(x>0))),'models':model_hashes,'run':str(run)})
    assert {r['lane'] for r in records}=={'n1quant','n2hurdle','n3latent','o1stable','o2shrink'}
    dump(args.output,{'status':'PASS','routes':records,'new_routes':3,'optimizations':2,'server_scoring':'NOT_RUN_NO_MATCHED_GATA4_TARGET','blocks_submission':False})
    print('PASS: five routes, all input/snapshot hashes, all contracts, exact model replay, pairwise distinct')


if __name__=='__main__':main()
