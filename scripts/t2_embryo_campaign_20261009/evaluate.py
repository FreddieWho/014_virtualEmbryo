"""One predeclared released-stage holdout: E6.75 + E8.0 -> E7.25.
Only the plain carrier and geometry mechanisms are valid in this fold: the
three-stage baseline carrier would need a fourth released earlier stage.
Never evaluate on E7.5 or use its protected labels.
"""
import argparse,json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from runtime import initialize

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--geometry',action='store_true');a=p.parse_args()
    v,_=initialize(a.data)
    import t2_recipes as r
    from backtest import Board
    genes=v.panel('T2:embryo:val_interp');L=v.load_stage('E6.75',genes);T=v.load_stage('E7.25',genes);R=v.load_stage('E8.0',genes)
    params=NS(board='T2:embryo:val_interp',left='E6.75:6.75',right='E8.0:8.0',target=7.25,n=5000,seed=20261009,label='celltype',carrier='left',C=2.,geometry='logrms',zero_preserve=False)
    P,_=r.run_interp(params);pred={'left_bridge':P}
    diagnostics={}
    if a.geometry:
        from geometry import interpolate_geometry
        Q=P.copy();Q.obsm['spatial_3D'],diagnostics=interpolate_geometry(P.obsm['spatial_3D'],np.asarray(P.obs.celltype.astype(str)),L.obsm['spatial_3D'],np.asarray(L.obs.celltype.astype(str)),R.obsm['spatial_3D'],np.asarray(R.obs.celltype.astype(str)),.4)
        pred['state_bures']=Q
        S=Q.copy();S.obsm['spatial_3D']=S.obsm['spatial_3D'][np.random.default_rng(20261009).permutation(S.n_obs)]
        pred['pair_shuffle_control']=S
    result={'fold':'E6.75+E8.0 -> released E7.25','protected_target_read':False,'legacy_carrier_fold':'NOT_IDENTIFIABLE_no_earlier_released_stage','predictions':{},'geometry_diagnostics':diagnostics,'proxy_not_server_score':True}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    for seed in [0,1,2]:
        B=Board('T2',genes,T,L,seed=seed)
        for name,P in pred.items():
            raw=B.raw(P);skills=B.skills(raw)
            result['predictions'].setdefault(name,[]).append({'seed':seed,'raw':raw,'skill_local_calibration':skills,'floor':B.floor,'ceiling':B.ceil})
            dest.write_text(json.dumps(result,indent=2,default=str));print(seed,name,skills,flush=True)
if __name__=='__main__':main()
