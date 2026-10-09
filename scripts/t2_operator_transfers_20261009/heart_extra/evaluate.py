import runtime
import argparse,json,time
from pathlib import Path
import numpy as np,anndata as ad
from threadpoolctl import threadpool_limits

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--artifacts',required=True);p.add_argument('--out',required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args()
    v=runtime.initialize(a.data)
    from backtest import Board
    ar=Path(a.artifacts);build=json.loads((ar/'BUILD.json').read_text())
    assert build['split']=='dev' and build['all_contracts_pass']
    # Read-only truth access occurs only after every source-only prediction is frozen.
    genes=v.panel('T2:heart:val_extrap');T=v.load_stage('E9.5',genes);R=v.load_stage('E8.75',genes)
    res={'seed':a.seed,'fold':'E8.25_late+E8.75 -> released E9.5','model_target_access':False,'full_panel':500,'evaluation_not_server_score':True,'prediction_freeze_sha256':v.sha256(ar/'BUILD.json'),'truth_source_sha256':v.sha256(Path(a.data)/'E9.5.h5ad'),'arms':{}}
    out=Path(a.out)
    with threadpool_limits(limits=1):
        board=Board('T2',genes,T,R,seed=a.seed)
        res['floor']=board.floor;res['ceiling']=board.ceil
        for mode in ['parent','zp','copy_last','geneperm']:
            artifact=build['artifacts'][mode];assert v.sha256(Path(artifact['path']))==artifact['sha256']
            pred=ad.read_h5ad(artifact['path']);started=time.time()
            raw=board.raw(pred);sk=board.skills(raw)
            res['arms'][mode]={'shape':list(pred.shape),'raw':raw,'local_skills':sk,'wall_seconds':time.time()-started,'artifact_sha256':artifact['sha256']}
            out.write_text(json.dumps(res,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
            print(json.dumps({'seed':a.seed,'arm':mode,'raw':raw,'local_skills':sk,'wall_seconds':time.time()-started}),flush=True)
    res['zero_drift_scoring']='Deduplicated: independently asserted expression-identical to copy_last; same geometry and rows'
    res['complete']=True
    out.write_text(json.dumps(res,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')

if __name__=='__main__':main()
