import pickle,copy
from pathlib import Path
import numpy as np
from scipy.special import logit,expit
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from scripts.t1_three.ops import joint_donors,mixture_indices
from scripts.t1_round2.ops import mixture_donors,abundance_step
from scripts.t1_five.models import predict as mass_predict
from .ops import moments,moment_fit,shrunk_cov,gaussian_map,graph_fit,graph_query,stability_weights,bounded_weights
from .common import ROOT,sha

SHARED=ROOT/'artifacts/t1_seven/T1-SEVEN-20260930-v1/shared'
PARENTS=ROOT/'artifacts/t1_three/T1-THREE-20260929-v1'


def core_model(future):
    with (PARENTS/'r2joint'/('final_model.pkl' if future else 'report_model.pkl')).open('rb') as f:return pickle.load(f)


def cache(scope,name):return np.load(SHARED/scope/(name+'.npy'),mmap_mode='r')


def fit(c,lane,future):
    cfg=c.cfg['seven'];scope='final' if future else 'report';core=core_model(future);density=core['stack']['density'];aids=np.arange(len(c.xa)) if future else c.tr[0];bids=np.arange(len(c.xb)) if future else c.tr[1]
    za=cache(scope,'early_latent');zb=cache(scope,'late_latent');ta=c.ta[aids];tb=c.tb[bids]
    m={'lane':lane,'cfg':cfg,'future':future,'scope':scope,'groups':{},'train_early':aids,'train_late':bids,'cache_lock':sha(SHARED/'CACHE_LOCK.json'),'parent_model':str((PARENTS/'r2joint'/('final_model.pkl' if future else 'report_model.pkl')).relative_to(ROOT))}
    m['parent_model_sha256']=sha(ROOT/m['parent_model'])
    if lane=='s1growth':
        labels=sorted(set(ta)|set(tb));ca=np.array([sum(ta==t) for t in labels]);cb=np.array([sum(tb==t) for t in labels]);step=abundance_step(ca,cb,cfg['growth_pseudocount'],cfg['growth_strength'],cfg['growth_ratio_cap']);m.update(steps=dict(zip(labels,step)),counts_early=ca,counts_late=cb)
    elif lane=='f2stable':
        mass=core['stack']['mass'];diagnostics={}
        for typ,g in mass['groups'].items():
            ai=aids[ta==typ];bi=bids[tb==typ];w0,w1,evidence=stability_weights(c.xa[ai],c.xb[bi],cfg['stability_parts'],cfg['stability_required'],cfg['unstable_weight'],c.cfg['seed'])
            for j,v in g.items():
                v['pout']=float(expit(logit(np.clip(v['psource'],1e-6,1-1e-6))+w0[j]*(logit(np.clip(v['pout'],1e-6,1-1e-6))-logit(np.clip(v['psource'],1e-6,1-1e-6)))))
                v['qout']=np.maximum.accumulate(np.maximum(v['qsource']+w1[j]*(v['qout']-v['qsource']),0))
            m['groups'][typ]={'zero_weight':w0,'positive_weight':w1,'partition_evidence':evidence,'early_ids':ai,'late_ids':bi}
            print('stability fitted',scope,typ,flush=True)
        m['mass']=mass
    elif lane!='s2mix':
        for typ in density['common']:
            aa=np.asarray(za[ta==typ]);bb=np.asarray(zb[tb==typ]);dim=cfg['latent_dimensions'] if lane in ['n1moment','n2covot'] else za.shape[1]
            scaler=StandardScaler().fit(np.vstack([aa[:,:dim],bb[:,:dim]]));aa=scaler.transform(aa[:,:dim]);bb=scaler.transform(bb[:,:dim]);g={'scaler':scaler,'dim':dim}
            if lane=='n1moment':
                fa=moments(aa);fb=moments(bb);source=fb if future else fa;target=source.mean(0)+cfg['moment_strength']*(fb.mean(0)-fa.mean(0))
                theta,info=moment_fit(source,target,cfg['moment_ridge'],cfg['moment_theta_bound']);g.update(theta=theta,target=target,fit=info)
            elif lane=='n2covot':
                ca=shrunk_cov(aa,cfg['cov_shrink']);cb=shrunk_cov(bb,cfg['cov_shrink']);g.update(map=gaussian_map(ca,cb),mean_early=aa.mean(0),mean_late=bb.mean(0),cov_early=ca,cov_late=cb)
            elif lane=='n3graph':
                z=np.vstack([aa,bb]);y=np.r_[np.zeros(len(aa)),np.ones(len(bb))];ids=np.r_[-(aids[ta==typ]+1),bids[tb==typ]+1]
                g['graph']=graph_fit(z,y,ids,cfg['graph_neighbors'],cfg['graph_alpha'])
            elif lane=='f1soft':
                z=np.vstack([aa,bb]);k=max(2,min(cfg['soft_max_components'],len(z)//cfg['soft_min_cells']));gm=GaussianMixture(n_components=k,covariance_type='diag',reg_covar=.05,max_iter=500,n_init=2,random_state=c.cfg['seed']).fit(z)
                if not gm.converged_:raise ValueError('soft-state GMM did not converge')
                ca=gm.predict_proba(aa).sum(0);cb=gm.predict_proba(bb).sum(0);step=abundance_step(ca,cb,cfg['soft_prior'],cfg['soft_strength'],2.)
                g.update(gmm=gm,early_counts=ca,late_counts=cb,step=step)
            else:raise ValueError(lane)
            m['groups'][typ]=g;print('fit',scope,lane,typ,flush=True)
    return m


def predict(m,c):
    cfg=m['cfg'];lane=m['lane'];scope=m['scope'];future=m['future'];types=c.tb[c.rows] if future else c.ta[c.te[0]];ids=c.rows+1 if future else -(c.te[0]+1)
    raw=c.xb[c.rows] if future else c.xa[c.te[0]];z=cache(scope,'query_latent');mass=cache(scope,'mass');weights=np.array(cache(scope,'weights'));composition=np.asarray(cache(scope,'composition'));details={}
    if lane=='s2mix':
        a=cache(scope,'best');b=cache(scope,'backup');ta=np.asarray(cache(scope,'best_types'));tb=np.asarray(cache(scope,'backup_types'));side,rows=mixture_indices(ta,tb,cfg['mix_fraction_best'],cfg['mix_seed']);out=np.empty_like(a);labels=np.empty(len(a),dtype=ta.dtype)
        for s,pool,pt in [(0,a,ta),(1,b,tb)]:ix=side==s;out[ix]=pool[rows[ix]];labels[ix]=pt[rows[ix]]
        return np.asarray(out,np.float32),{'parent_side':side,'parent_rows':rows,'predicted_types':labels,'parent_best_count':int(sum(side==0)),'parent_backup_count':int(sum(side==1))}
    if lane=='s1growth':composition=mixture_donors(types,m['steps'])
    elif lane=='f2stable':
        fallback=c.legacy if future else cache(scope,'fallback');mass,_=mass_predict(m['mass'],raw,types,fallback)
    elif lane!='n2covot':
        for typ,g in m['groups'].items():
            ix=np.flatnonzero(types==typ)
            if not len(ix):continue
            q=g['scaler'].transform(z[ix,:g['dim']])
            if lane=='n1moment':logw=moments(q)@g['theta']
            elif lane=='n3graph':logw=graph_query(g['graph'],q,ids[ix],cfg['graph_query_neighbors'])
            elif lane=='f1soft':logw=.5*np.log(weights[ix])+.5*(g['gmm'].predict_proba(q)@g['step'])
            else:raise ValueError(lane)
            weights[ix]=bounded_weights(logw);details[typ]={'ess':float(weights[ix].sum()**2/(weights[ix]@weights[ix])),'query_cells':len(ix)}
    donor=joint_donors(types,weights,composition)
    if lane=='n2covot':
        for typ,g in m['groups'].items():
            pool=np.flatnonzero(types==typ);slots=np.flatnonzero(types[donor]==typ)
            if not len(slots):continue
            allq=g['scaler'].transform(z[pool,:g['dim']]);q=g['scaler'].transform(z[donor[slots],:g['dim']]);center=g['mean_late'] if future else g['mean_early']
            velocity=g['mean_late']-g['mean_early']+(q-center)@(g['map']-np.eye(g['dim'])).T
            target=q+cfg['cov_strength']*velocity;distance,chosen=cKDTree(allq).query(target,k=1);donor[slots]=pool[chosen]
            details[typ]={'projection_mean_distance':float(distance.mean()),'changed_donors':int(np.sum(np.asarray(cache(scope,'best_donors'))[slots]!=donor[slots]))}
    out=np.asarray(mass[donor],np.float32);labels=types[donor]
    details.update(donor_indices=donor,predicted_types=labels,unique_donors=len(np.unique(donor)),predicted_counts={t:int(sum(labels==t)) for t in sorted(set(labels))})
    return out,details
