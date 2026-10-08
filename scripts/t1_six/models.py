"""Six-route fit/predict dispatch over the frozen t1_three r2joint skeleton and shared caches."""
import json,pickle
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from scripts.t1_three.ops import joint_donors
from scripts.t1_seven.ops import bounded_weights,shrunk_cov,gaussian_map
from scripts.t1_round2.ops import abundance_step
from .ops import plan_fields,consistency_distances,stability_fractions,adaptive_sides,covot_reselect_soft,conformal_radius,conformal_reselect,consistency_logw
from .common import ROOT,sha

SHARED=ROOT/'artifacts/t1_six/T1-SIX-20261007-v1/shared'
PARENTS=ROOT/'artifacts/t1_three/T1-THREE-20260929-v1'
SEVEN=ROOT/'artifacts/t1_seven/T1-SEVEN-20260930-v1'


def core_model(future):
    with (PARENTS/'r2joint'/('final_model.pkl' if future else 'report_model.pkl')).open('rb') as f:return pickle.load(f)


def cache(scope,name):return np.load(SHARED/scope/(name+'.npy'),mmap_mode='r')


def plans(scope):
    with (SHARED/scope/'plans.pkl').open('rb') as f:return pickle.load(f)


def fit(c,lane,future):
    cfg=c.cfg['six'];scope='final' if future else 'report'
    core=core_model(future);density=core['stack']['density']
    aids=np.arange(len(c.xa)) if future else c.tr[0];bids=np.arange(len(c.xb)) if future else c.tr[1]
    za=cache(scope,'early_latent');zb=cache(scope,'late_latent');ta=c.ta[aids];tb=c.tb[bids]
    m={'lane':lane,'cfg':cfg,'future':future,'scope':scope,'groups':{},'train_early':aids,'train_late':bids,'cache_lock':sha(SHARED/'CACHE_LOCK.json'),'parent_model':str((PARENTS/'r2joint'/('final_model.pkl' if future else 'report_model.pkl')).relative_to(ROOT))}
    m['parent_model_sha256']=sha(ROOT/m['parent_model'])
    common=sorted(density['common'])
    if lane=='ocovstab':
        src=SEVEN/'n2covot'/'REPORT_OPERATOR.json' if not future else SEVEN/'n2covot'/'FINAL_OPERATOR.json'
        distances=json.loads(src.read_text())
        vals=[float(v['projection_mean_distance']) for v in distances.values() if isinstance(v,dict) and 'projection_mean_distance' in v]
        med=float(np.median(vals))
        m['reliability_median']=med;m['reliability_source']=str(src.relative_to(ROOT))
        for typ in common:
            aa=np.asarray(za[ta==typ,:8],dtype=np.float64);bb=np.asarray(zb[tb==typ,:8],dtype=np.float64)
            scaler=StandardScaler().fit(np.vstack([aa,bb]));a=scaler.transform(aa);b=scaler.transform(bb)
            ca=shrunk_cov(a,cfg['ocovstab']['cov_shrink']);cb=shrunk_cov(b,cfg['ocovstab']['cov_shrink'])
            strength=cfg['ocovstab']['strength_stable'] if float(distances[typ]['projection_mean_distance'])<=med else cfg['ocovstab']['strength_unstable']
            m['groups'][typ]={'scaler':scaler,'dim':8,'map':gaussian_map(ca,cb),'mean_early':a.mean(0),'mean_late':b.mean(0),'strength':strength}
            print('fit',scope,lane,typ,'strength',strength,flush=True)
    elif lane=='osoftcov':
        for typ in common:
            aa32=np.asarray(za[ta==typ],dtype=np.float64);bb32=np.asarray(zb[tb==typ],dtype=np.float64)
            z32=np.vstack([aa32,bb32]);k=max(2,min(cfg['osoftcov']['soft_max_components'],len(z32)//cfg['osoftcov']['soft_min_cells']))
            gm=GaussianMixture(n_components=k,covariance_type='diag',reg_covar=.05,max_iter=500,n_init=2,random_state=c.cfg['seed']).fit(z32)
            if not gm.converged_:raise ValueError('soft-state GMM did not converge')
            ca32=gm.predict_proba(aa32).sum(0);cb32=gm.predict_proba(bb32).sum(0)
            step=abundance_step(ca32,cb32,cfg['osoftcov']['soft_prior'],cfg['osoftcov']['soft_strength'],2.)
            aa8=aa32[:,:8];bb8=bb32[:,:8]
            scaler=StandardScaler().fit(np.vstack([aa8,bb8]));a8=scaler.transform(aa8);b8=scaler.transform(bb8)
            ca8c=shrunk_cov(a8,cfg['osoftcov']['cov_shrink']);cb8c=shrunk_cov(b8,cfg['osoftcov']['cov_shrink'])
            m['groups'][typ]={'gmm':gm,'step':step,'scaler':scaler,'dim':8,'map':gaussian_map(ca8c,cb8c),'mean_early':a8.mean(0),'mean_late':b8.mean(0),'soft_dim':int(aa32.shape[1])}
            print('fit',scope,lane,typ,flush=True)
    elif lane=='ostabmix':
        for typ in common:
            ai=aids[ta==typ];bi=bids[tb==typ]
            fraction,score,extra=stability_fractions(c.xa[ai],c.xb[bi],cfg['ostabmix']['stability_parts'],cfg['ostabmix']['stability_required'],0.25,cfg['ostabmix']['stability_seed'])
            m['groups'][typ]={'fraction':fraction,'stability_score':score,**extra,'early_ids':ai,'late_ids':bi}
            print('fit',scope,lane,typ,'fraction',fraction,'score %.3f'%score,flush=True)
    elif lane=='nconf':
        for ti,typ in enumerate(common):
            aa=np.asarray(za[ta==typ,:8],dtype=np.float64);bb=np.asarray(zb[tb==typ,:8],dtype=np.float64)
            perm=np.random.default_rng([c.cfg['seed'],1000+ti]).permutation(len(aa))
            half=max(10,len(aa)//2)
            perm_b=np.random.default_rng([c.cfg['seed'],2000+ti]).permutation(len(bb))
            r=conformal_radius(aa[perm[:half]],bb[perm_b[:max(10,len(bb)//2)]],aa[perm[half:]],bb,cfg['nconf']['conformal_alpha'],cfg['nconf']['cov_shrink'],cfg['nconf']['cov_strength'])
            if r is None:raise ValueError('conformal calibration infeasible: '+typ)
            m['groups'][typ]=r;print('fit',scope,lane,typ,'radius %.3f'%r['radius'],flush=True)
    elif lane in ('nwasser','nbidir'):
        m['consumes_plans']=True
    else:raise ValueError(lane)
    return m


def predict(m,c):
    cfg=m['cfg'];lane=m['lane'];scope=m['scope'];future=m['future']
    types=c.tb[c.rows] if future else c.ta[c.te[0]];ids=c.rows+1 if future else -(c.te[0]+1)
    z=cache(scope,'query_latent');mass=cache(scope,'mass');weights=np.array(cache(scope,'weights'));composition=np.asarray(cache(scope,'composition'));details={}
    if lane=='ostabmix':
        a=cache(scope,'best');b=cache(scope,'backup');tbk=np.asarray(cache(scope,'best_types'));tbt=np.asarray(cache(scope,'backup_types'))
        fractions={t:g['fraction'] for t,g in m['groups'].items()}
        sides,rows=adaptive_sides(types,fractions,c.cfg['seed'])
        out=np.empty_like(a);labels=np.empty(len(a),dtype=tbk.dtype)
        for s,pool,pt in [(0,a,tbk),(1,b,tbt)]:
            ix=sides==s;out[ix]=pool[rows[ix]];labels[ix]=pt[rows[ix]]
        return np.asarray(out,np.float32),{'parent_side':sides,'parent_rows':rows,'predicted_types':labels,'fractions':fractions,'parent_best_count':int(sum(sides==0)),'parent_backup_count':int(sum(sides==1))}
    if lane=='nbidir':
        P=plans(scope)
        for typ,g in P.items():
            ix=np.flatnonzero(types==typ)
            if not len(ix):continue
            side_latent=g['scaler'].transform(z[ix,:g['dim']])
            train_latent=g['early_train_std'] if not future else g['late_train_std']
            cons=g['cons_early'] if not future else g['cons_late']
            logw,extra=consistency_logw(cons,train_latent,side_latent,g['sigma'])
            weights[ix]=logw;details[typ]={**extra,'query_cells':len(ix)}
        donor=joint_donors(types,weights,composition)
    else:
        donor=joint_donors(types,weights,composition)
        if lane in ('ocovstab','osoftcov'):
            common=sorted(m['groups'])
            for ti,typ in enumerate(common):
                g=m['groups'][typ]
                pool=np.flatnonzero(types==typ)
                if not len(pool):continue
                allq=g['scaler'].transform(z[pool,:g['dim']]);q=g['scaler'].transform(z[donor[pool],:g['dim']]);center=g['mean_late'] if future else g['mean_early']
                velocity=g['mean_late']-g['mean_early']+(q-center)@(g['map']-np.eye(g['dim'])).T
                strength=float(g['strength']) if lane=='ocovstab' else float(cfg['osoftcov']['cov_strength'])
                target=q+strength*velocity
                kk=cfg['ocovstab']['knn_k'] if lane=='ocovstab' else 1
                chosen,dist,kk_eff=covot_reselect_soft(target,allq,pool,kk,[c.cfg['seed'],ti])
                donor[pool]=chosen
                details[typ]={'projection_mean_distance':dist,'soft_neighbors':kk_eff,'strength':strength,'changed_donors':int(np.sum(np.asarray(cache(scope,'best_donors'))[pool]!=donor[pool]))}
        elif lane=='nwasser':
            P=plans(scope)
            for typ,g in P.items():
                pool=np.flatnonzero(types==typ)
                if not len(pool):continue
                q=g['scaler'].transform(z[pool,:g['dim']])
                train_latent=g['early_train_std'] if not future else g['late_train_std']
                disp=g['d_early'] if not future else g['d_late']
                tree=cKDTree(train_latent)
                distance,nn=tree.query(q,k=min(cfg['nwasser']['knn_k'],len(train_latent)))
                if np.asarray(nn).ndim==1:nn=nn[:,None];distance=distance[:,None]
                w=1.0/(distance+cfg['nwasser']['knn_weight_floor'])
                dbar=(w[:,:,None]*disp[nn]).sum(1)/w.sum(1)[:,None]
                target=q+dbar
                dist,chosen=cKDTree(q).query(target,k=1)
                donor[pool]=pool[np.asarray(chosen)]
                details[typ]={'nearest_train_distance_mean':float(np.mean(distance)),'target_shift_mean':float(np.mean(dbar)),'changed_donors':int(np.sum(np.asarray(cache(scope,'best_donors'))[pool]!=donor[pool]))}
        elif lane=='nconf':
            common=sorted(m['groups'])
            for ti,typ in enumerate(common):
                g=m['groups'][typ]
                pool=np.flatnonzero(types==typ)
                if not len(pool):continue
                q=g['scaler'].transform(z[pool,:g['dim']])
                target=q+cfg['nconf']['cov_strength']*(q-g['mean_fit'])@(g['map']-np.eye(g['dim'])).T
                chosen,dist,mode=conformal_reselect(target,q,pool,g['radius'],[c.cfg['seed'],ti])
                donor[pool]=chosen
                details[typ]={'nearest_distance_mean':dist,'mode':mode,'radius':float(g['radius']),'score_median':float(g['score_median']),'changed_donors':int(np.sum(np.asarray(cache(scope,'best_donors'))[pool]!=donor[pool]))}
        else:raise ValueError(lane)
    out=np.asarray(mass[donor],np.float32);labels=types[donor]
    details.update(donor_indices=donor,predicted_types=labels,unique_donors=len(np.unique(donor)),predicted_counts={t:int(sum(labels==t)) for t in sorted(set(labels))})
    return out,details
