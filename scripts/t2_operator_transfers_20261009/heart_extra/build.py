import runtime
import argparse,json,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np,pandas as pd
from zp_operator import apply

EXPECTED_X2='b884e3b6d2abda1aa4a01e64a198080f30cbdac7e3310d80c2a4f3da3ac7917b'

def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,default=lambda o:o.item() if isinstance(o,np.generic) else str(o))+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--split',choices=['dev','final'],required=True);args=ap.parse_args()
    v=runtime.initialize(args.data)
    import t2_recipes as r
    out=Path(args.out)
    if (out/'BUILD.json').exists():raise FileExistsError('Completed output is frozen; choose a new output directory')
    out.mkdir(parents=True,exist_ok=True)
    en,ln,target=('E8.25_late:8.25','E8.75:8.75',9.5) if args.split=='dev' else ('E8.75:8.75','E9.5:9.5',10.5)
    a=NS(board='T2:heart:val_extrap',prev=en,last=ln,target=target,n=25179,seed=20261008,label='celltype',rows='repo',row_seed=20260821,damp=.9,timescale='none',stat='median',min_cells=30,lib_preserve=True)
    # Actual parent generation invokes the unchanged historical function, including output metadata.
    parent,prov=r.run_extrap(a);pp=out/'parent_x2_recipe.h5ad';parent.write_h5ad(pp)
    genes=v.panel(a.board);E=v.load_stage(en.split(':')[0],genes);L=v.load_stage(ln.split(':')[0],genes)
    le=np.asarray(E.obs.celltype.astype(str));ll=np.asarray(L.obs.celltype.astype(str))
    rows=r.stratified_indices(ll,min(25179,L.n_obs),a.row_seed);labels=ll[rows];x=L.X[rows]
    states=prov['shared_states'];delta=np.stack([np.median(L.X[ll==s],axis=0)-np.median(E.X[le==s],axis=0) for s in states])
    permutation=np.random.default_rng(20261009).permutation(len(genes))
    np.savez_compressed(out/'frozen_model.npz',source_rows=rows,states=np.asarray(states),delta=delta,genes=np.asarray(genes),permutation=permutation)
    pd.DataFrame({'output_row':np.arange(len(rows)),'source_row':rows,'source_obs_name':np.asarray(L.obs_names)[rows],'output_obs_name':parent.obs_names,'celltype':labels}).to_csv(out/'source_rows.tsv',sep='\t',index=False)
    replay,diag=apply(x,labels,states,delta,'parent');assert np.array_equal(replay,parent.X),'own parent replay must be exact'
    digest=lambda z:hashlib.sha256(np.ascontiguousarray(z).tobytes()).hexdigest()
    artifacts={'parent':{'path':str(pp),'sha256':v.sha256(pp),'diagnostics':diag,'format':v.format_check(pp,a.board),'X_sha256':digest(parent.X)}}
    for mode in ['zp','copy_last','geneperm','zero_drift']:
        if mode=='copy_last':y=x.copy();diag={'identity':True}
        else:y,diag=apply(x,labels,states,delta,mode,permutation)
        if mode=='zero_drift':assert np.array_equal(y,x),'zero-dose identity must be exact'
        q=parent.copy();q.X=y
        q.uns['operator_transfer']=json.dumps({'operator':mode,'parent':'X2 recipe reconstruction; original v0030 not restored','parent_artifact_sha256':v.sha256(pp),'drift':'0.9*(median_last-median_prev), unchanged','support':'only positive source entries; detection floor .05' if mode!='copy_last' else 'copy raw source','external_sources':'none','protected_target_used':False,'frozen_model_sha256':v.sha256(out/'frozen_model.npz')},sort_keys=True)
        path=out/('submission.h5ad' if mode=='zp' and args.split=='final' else f'{mode}.h5ad');q.write_h5ad(path,compression='gzip')
        assert np.array_equal(q.obsm['spatial_3D'],parent.obsm['spatial_3D'])
        assert q.obs.equals(parent.obs) and q.var.equals(parent.var)
        if mode!='parent':assert diag.get('zero_to_positive',0)==0
        artifacts[mode]={'path':str(path),'sha256':v.sha256(path),'diagnostics':diag,'format':v.format_check(path,a.board),'X_sha256':digest(y)}
    source_hashes={n:v.sha256(Path(args.data)/(n+'.h5ad')) for n in [en.split(':')[0],ln.split(':')[0]]}
    record={'split':args.split,'args':vars(a),'full_input_shapes':{en:list(E.shape),ln:list(L.shape)},'prediction_shape':list(parent.shape),'source_hashes':source_hashes,'panel_file_sha256':v.sha256(v.PANEL_FILE[a.board]),'panel_content_sha256':hashlib.sha256('\n'.join(genes).encode()).hexdigest(),'historical_x2_sha256':EXPECTED_X2,'historical_x2_byte_parity':v.sha256(pp)==EXPECTED_X2 if args.split=='final' else None,'historical_v30_byte_parity':False,'own_parent_replay_exact':True,'artifacts':artifacts,'all_contracts_pass':all(z['format']['pass'] for z in artifacts.values()),'no_extra_endpoint':True,'protected_target_used':False}
    write_json(out/'BUILD.json',record);print(json.dumps(record,indent=2),flush=True)

if __name__=='__main__':main()
