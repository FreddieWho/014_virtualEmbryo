"""Auditable embryo-only candidate builder, without access to protected targets.

Variants compare matched carrier rows and coordinates. Corrected legacy weights
use the actual parent-to-target correction; this remains a reconstruction, not
an exact historical artifact replay. No portal requests are made.
"""
from pathlib import Path
import argparse, hashlib, json, sys
from types import SimpleNamespace as NS
import numpy as np
from runtime import initialize, REPO


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def build(data,variant,seed=20261009):
    v, runtime=initialize(data)
    import t2_recipes as r
    args=NS(board='T2:embryo:val_interp',left='E7.25:7.25',right='E8.0:8.0',prev='E6.75:6.75',target=7.5,
            n=5000,seed=seed,label='celltype',carrier='baseline',base_n=5000,base_seed=20260821,
            bridge_seed=20260904,C=2.,geometry='logrms',zero_preserve=False)
    parent, pp=r.run_interp(args)
    g=v.panel(args.board); L=v.load_stage('E7.25',g);R=v.load_stage('E8.0',g);P=v.load_stage('E6.75',g)
    # Double precision reductions match the historical recipe's arithmetic intent.
    XL=np.asarray(L.X,np.float64);XR=np.asarray(R.X,np.float64);XP=np.asarray(P.X,np.float64)
    ll=np.asarray(L.obs.celltype.astype(str));lr=np.asarray(R.obs.celltype.astype(str));lp=np.asarray(P.obs.celltype.astype(str))
    base=r.stratified_indices(ll,args.base_n,args.base_seed);bl=ll[base]
    XB=XL.copy()
    for s in np.unique(ll):
        if np.any(lp==s): XB[ll==s]+=XL[ll==s].mean(0)-XP[lp==s].mean(0)
    np.clip(XB,0,None,out=XB); XB=XB[base]
    name_to_row={str(x):i for i,x in enumerate(L.obs_names)}
    sources=[str(x).rsplit('__r',1)[0] for x in parent.obs_names]
    rows=np.asarray([name_to_row[x] for x in sources]); labs=ll[rows]
    if variant=='e3_original': out=parent
    else:
        X=XL[rows].copy() if variant=='raw_matched' else XB[[{int(z):i for i,z in enumerate(base)}[int(z)] for z in rows]].copy()
        for s in sorted(set(ll)&set(lr)&set(bl)):
            a=XL[ll==s]; b=XR[lr==s];muT=(2*a.mean(0)+b.mean(0))/3
            legacy_shift=muT-XB[bl==s].mean(0)
            se=np.sqrt(a.var(0)/len(a)+b.var(0)/len(b))
            t=np.divide(np.abs(legacy_shift),se,out=np.zeros_like(se),where=se>0);w=t/(t+2.)
            shift=muT-XL[base][bl==s].mean(0) if variant=='raw_matched' else legacy_shift
            X[labs==s]+=w*shift
        # Orphan states retain the exact reconstructed baseline in either arm.
        shared=set(ll)&set(lr)&set(bl)
        if variant=='raw_matched':
            basepos={int(z):i for i,z in enumerate(base)}
            for j in np.flatnonzero(~np.isin(labs,list(shared))):X[j]=XB[basepos[int(rows[j])]]
        np.clip(X,0,None,out=X)
        out=parent.copy();out.X=X.astype(np.float32)
    prov={'variant':variant,'parent_identity':'reconstructed_E3_NOT_original_v0014','runtime':runtime,
          'protected_targets_read':False,'external_sources':[], 'released_inputs':{n:sha(Path(data)/f'{n}.h5ad') for n in ['E6.75','E7.25','E8.0']},
          'row_and_geometry_match_e3':bool(np.array_equal(out.obsm['spatial_3D'],parent.obsm['spatial_3D']) and list(out.obs_names)==list(parent.obs_names)),
          'raw_matched_weight_policy':'same legacy-parent correction weights; isolates carrier residual within matched rows',
          'n_shared_states':len(set(ll)&set(lr)&set(bl)), 'source_commit':'29a8e1976665a66a7378892857c815f589720971'}
    out.uns['ve_provenance']=json.dumps(prov,sort_keys=True)
    return out,prov,v


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--variant',choices=['e3_original','legacy_weight','raw_matched'],required=True);p.add_argument('--out',required=True)
    a=p.parse_args();out,prov,v=build(a.data,a.variant)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists(): raise FileExistsError('Immutable output already exists: '+str(dest))
    out.write_h5ad(dest);check=v.format_check(dest,'T2:embryo:val_interp')
    rec={'sha256':sha(dest),'bytes':dest.stat().st_size,'check':check,'provenance':prov}
    dest.with_suffix('.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec,indent=2))
    if not check['pass']:raise SystemExit(1)
if __name__=='__main__':main()
