"""Frozen-checkpoint source hurdle component audit. No fitting or candidate changes."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
import json
from pathlib import Path
import numpy as np
from .common import Context,ROOT,read_model,dump,sha
from .ops import occupancy_decode
from scripts.t3_next.five import source


def main():
    root=ROOT/'artifacts/t3_round2/T3-ROUND2-20260928-v1';original=root/'n3occup'
    c=Context(root/'n3occup_components');cfg=c.cfg['round2'];genes,samples,rates,effects,controls,z,adj=source(c);results={};locks={}
    for name,ti in [('pooled',[0,1]),('sample0_to_1',[1]),('sample1_to_0',[0])]:
        prediction={arm:np.zeros((len(genes),500)) for arm in ['full','occupancy_only','intensity_only']}
        for fold in range(5):
            path=original/f'{name}_fold{fold}.pkl';saved=read_model(path);locks[str(path.relative_to(ROOT))]=sha(path);m=saved['model'];test=saved['test']
            b=(z[test]-m['feature_mean'])/m['feature_sd'];a=m['train_features'];kernel=np.exp(-((b[:,None]-a[None,:])**2).mean(2)/(2*m['bandwidth']))
            p=m['response_mean']+(kernel@m['weights'])@m['basis'];p[:,:500]=np.clip(p[:,:500],-cfg['logit_bound'],cfg['logit_bound']);p[:,500:]=np.clip(p[:,500:],-cfg['rate_bound'],cfg['rate_bound'])
            for arm in prediction:
                pars=p.copy()
                if arm=='occupancy_only':pars[:,500:]=0
                if arm=='intensity_only':pars[:,:500]=0
                pred=np.mean([np.stack([occupancy_decode(controls[s],v,np.array(['ctrl']*len(controls[s])),cfg['sample_occupancy_strength']).mean(0)-controls[s].mean(0) for v in pars]) for s in ti],axis=0)
                prediction[arm][test]=pred
        old=np.load(original/(name+'_oof.npz'));np.testing.assert_allclose(prediction['full'],old['model'],rtol=1e-7,atol=1e-8)
        truth=effects[ti].mean(0);np.testing.assert_array_equal(truth,old['truth'])
        legacy=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v1/o2shrink'/(name+'_oof.npz');old_rate=np.load(legacy);np.testing.assert_array_equal(truth,old_rate['truth']);locks[str(legacy.relative_to(ROOT))]=sha(legacy)
        results[name]={k:float(np.mean((p-truth)**2)) for k,p in prediction.items()};results[name]['legacy_mean_rate_strength1']=float(np.mean((old_rate['mean_rate']-truth)**2));results[name]['no_change']=float(np.mean(truth**2))
        np.savez_compressed(c.run/(name+'_oof.npz'),truth=truth,**prediction)
    dump(c.run/'CHECKPOINT_LOCK.json',locks);dump(c.run/'EVALUATION.json',{'mse':results,'full_prediction_reproduced':True,'training':'NOT_RUN_REUSED_FROZEN_MODELS','reason':'component-only evaluation, not a new fitted route or replacement candidate','legacy_comparator':'same folds and exact same truth; its original rate strength=1 differs from new hurdle strength=.25','candidate_changes':False})
    c.finish('COMPONENT_ABLATION_COMPLETE',mse=results)
    print(results,flush=True)


if __name__=='__main__':main()
