"""Matched internal / external / shuffled-prior prototypes and released fold."""
import argparse,re,json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np,pandas as pd
from scipy import sparse
from runtime import initialize,REPO
from external_programs import load_prior
from transport import transport


def external_matrix(root,genes):
    root=Path(root)
    if not (root/'gsm8559288_e725_counts_csr.npz').exists():
        # Lightweight audited export for portable replay. No model change.
        cache=root/'gsm8559288_e725_panel498_qc_counts.npz'
        import hashlib
        receipt=json.loads((root/'PANEL498_EXPORT_MANIFEST.json').read_text())
        assert hashlib.sha256(cache.read_bytes()).hexdigest()==receipt['sha256']
        q=np.load(cache,allow_pickle=False);assert q['genes'].tolist()==list(genes)
        return q['counts']
    features=pd.read_csv(root/'gsm8559288_e725_features.tsv',sep='\t');C=sparse.load_npz(root/'gsm8559288_e725_counts_csr.npz')
    # Explicit same-symbol summation prior to rank transform; all cells stay in
    # the same sample. Fixed QC comes from the audited source intake.
    qc=np.load(root/'gsm8559288_e725_previous_panel_rank_covariance.npz',allow_pickle=False)['qc_keep']
    cols=[]
    for g in genes:
        idx=np.flatnonzero(features.symbol.values==g)
        if not len(idx):raise ValueError('Missing external gene '+g)
        cols.append(np.asarray(C[:,idx].sum(1)).ravel())
    return np.column_stack(cols)[qc]


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--external',required=True);p.add_argument('--fold',action='store_true');p.add_argument('--outdir',required=True);p.add_argument('--score',action='store_true');p.add_argument('--support',choices=['displacement','mixture'],default='displacement');p.add_argument('--arms',default='internal,spatial,spatial_shuffle,scrna,scrna_shuffle');a=p.parse_args()
    v,_=initialize(a.data);import t2_recipes as r
    genes=v.panel('T2:embryo:val_interp');left='E6.75' if a.fold else 'E7.25';target=7.25 if a.fold else 7.5;t=.4 if a.fold else 1/3
    L=v.load_stage(left,genes);R=v.load_stage('E8.0',genes)
    if a.fold:
        args=NS(board='T2:embryo:val_interp',left='E6.75:6.75',right='E8.0:8.0',target=7.25,n=5000,seed=20261009,label='celltype',carrier='left',C=2.,geometry='logrms',zero_preserve=False);base,_=r.run_interp(args)
    else:
        import anndata as ad
        base=ad.read_h5ad(REPO/'artifacts/t2_embryo_campaign_20261009/e3_original_recipe.h5ad')
    lookup={str(n):i for i,n in enumerate(L.obs_names)};rows=np.array([lookup[re.sub(r'__(?:r|dup)\d+$','',str(n))] for n in base.obs_names])
    w=ext=None;prior={}
    if any(n.startswith('spatial') for n in a.arms.split(',')):w,prior=load_prior(Path(a.external)/'gse65924_e70_gene_spatial_rank_prior.tsv',genes)
    if any(n.startswith('scrna') for n in a.arms.split(',')):ext=external_matrix(a.external,genes)
    outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True);pred={};result={'fold':a.fold,'target':target,'protected_target_used':False,'external_prior':prior,'external_singlecell_shape':None if ext is None else ext.shape,'arms':{}}
    for name,mode,shuffle in [('internal','internal',False),('spatial','spatial',False),('spatial_shuffle','spatial',True),('scrna','scrna',False),('scrna_shuffle','scrna',True)]:
        if name not in a.arms.split(','):continue
        C,diag=transport(base.obsm['spatial_3D'],base.obs.celltype,rows,L.obsm['spatial_3D'],L.obs.celltype,L.X,R.obsm['spatial_3D'],R.obs.celltype,R.X,t,mode=mode,prior=w,external_counts=ext,shuffle=shuffle,support=a.support)
        out=base.copy();out.obsm['spatial_3D']=C.astype('float32');out.uns['external_transport']=json.dumps(diag);out.write_h5ad(outdir/(name+'.h5ad'));pred[name]=out;result['arms'][name]={'diagnostics':diag,'contract':v.format_check(outdir/(name+'.h5ad'),'T2:embryo:val_interp')};print(name,'built',flush=True)
    if a.score:
        if not a.fold:raise ValueError('No protected true-target evaluation')
        from backtest import Board
        T=v.load_stage('E7.25',genes)
        for seed in [0,1,2]:
            B=Board('T2',genes,T,L,seed=seed)
            for name,P in pred.items():
                raw=B.raw(P);skill=B.skills(raw);result['arms'][name].setdefault('evaluation',[]).append({'seed':seed,'raw':raw,'skills':skill});print(seed,name,skill,flush=True)
            (outdir/'RESULT.json').write_text(json.dumps(result,indent=2,default=str))
    (outdir/'RESULT.json').write_text(json.dumps(result,indent=2,default=str))
if __name__=='__main__':main()
