"""New-route operators: exact OT plans, displacement fields, conformal calibration, consistency weights.

All operators are deterministic under frozen parameters and verify their own numerical preconditions.
POT ot.emd is used for exact discrete plans (amended 2026-10-07 pre-run: numpy Sinkhorn overflowed
on the raw squared-distance scale and was too slow; POT was restored usable by the env repair).
"""
import numpy as np
from scipy.spatial import cKDTree
from scripts.t1_three.ops import systematic_indices
from scripts.t1_seven.ops import bounded_weights, shrunk_cov, gaussian_map, stability_weights


def squared_cost(za,zb):
    za=np.asarray(za,np.float64);zb=np.asarray(zb,np.float64)
    if za.ndim!=2 or zb.ndim!=2 or za.shape[1]!=zb.shape[1] or not len(za) or not len(zb):raise ValueError('cost shape')
    if not np.isfinite(za).all() or not np.isfinite(zb).all():raise ValueError('cost values')
    sq_a=(za**2).sum(1);sq_b=(zb**2).sum(1)
    d2=sq_a[:,None]+sq_b[None,:]-2.0*(za@zb.T)
    return np.maximum(d2,0.0)


def exact_plan(za,zb):
    """Exact discrete OT plan between two uniform-mass point clouds; marginals verified to 1e-8."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        import ot
    cost=squared_cost(za,zb)
    a=np.full(len(za),1.0/len(za));b=np.full(len(zb),1.0/len(zb))
    plan=ot.emd(a,b,cost)
    if not np.isfinite(plan).all():raise ValueError('plan not finite')
    row_res=float(np.abs(plan.sum(1)-a).max());col_res=float(np.abs(plan.sum(0)-b).max())
    if row_res>1e-8 or col_res>1e-8:raise ValueError('plan marginals beyond tolerance')
    return plan,{'row_residual':row_res,'col_residual':col_res,'cost_mean':float(cost.mean())}


def plan_fields(plan,za,zb):
    """Row/column barycentric projections and displacement fields from an exact plan."""
    row_t=plan@zb/plan.sum(1,keepdims=True)
    col_s=plan.T@za/plan.sum(0)[:,None]
    d_early=row_t-za
    d_late=zb-col_s
    return d_early,d_late,row_t,col_s


def consistency_distances(plan,za,zb):
    """Forward/backward dominant-map consistency distances per train cell."""
    dom_t=plan.argmax(1);dom_s=plan.argmax(0)
    row_t=plan@zb/plan.sum(1,keepdims=True);col_s=plan.T@za/plan.sum(0)[:,None]
    d_early=np.linalg.norm(col_s[dom_t]-za,axis=1)
    d_late=np.linalg.norm(row_t[dom_s]-zb,axis=1)
    return d_early,d_late


def stability_fractions(a,b,parts,required,unstable,seed):
    """Per-type best/backup mixture fraction from 4-part direction stability evidence.

    fraction = 0.7 (s2mix's frozen proven ratio) when at least half the genes show a
    stable positive-mean direction across partitions, else 0.3. Two-level rule, no ratio scan.
    """
    w0,w1,evidence=stability_weights(a,b,parts,required,unstable,seed)
    score=float(np.mean(w1==1.0))
    fraction=0.7 if score>=0.5 else 0.3
    return fraction,score,{'zero_stable':float(np.mean(w0==1.0)),'positive_stable':score}


def adaptive_sides(types,fractions,seed):
    """Per-type best/backup side assignment with per-type fractions; deterministic frozen seeds.

    Mirrors mixture_indices: per-type quotas, within-type slot and row permutations, then a
    single global slot reorder. Types without a frozen fraction (no cross-stage stability
    evidence, e.g. stage-specific types outside density['common']) keep the original
    skeleton: side 0 with the slot's own best row (identity).
    """
    types=np.asarray(types);n=len(types);sides=np.zeros(n,int);rows=np.full(n,-1)
    rng=np.random.default_rng(seed);order=rng.permutation(n)
    labels=sorted(set(types))
    for ti,t in enumerate(labels):
        ix=np.flatnonzero(types==t)
        if not len(ix):continue
        if t not in fractions:
            sides[ix]=0;rows[ix]=ix;continue
        frac=float(fractions[t])
        if not 0<=frac<=1:raise ValueError('fraction range')
        na=int(round(len(ix)*frac))
        trng=np.random.default_rng([seed,10_000+ti])
        slot_perm=trng.permutation(len(ix))
        best_slots=ix[slot_perm[:na]];back_slots=ix[slot_perm[na:]]
        sides[best_slots]=0;sides[back_slots]=1
        row_perm=trng.permutation(len(ix))
        rows[best_slots]=ix[row_perm[:na]]
        k_back=len(ix)-na
        rows[back_slots]=ix[row_perm[na:na+k_back]]
    assert (rows>=0).all()
    return sides[order],rows[order]


def weighted_draw(candidates,distances,u):
    """One inverse-square-distance weighted draw from candidate indices."""
    w=1.0/(distances**2+1e-3)
    cum=np.cumsum(w/w.sum());cum[-1]=1.0
    return candidates[int(np.searchsorted(cum,float(u),side='left'))]


def covot_reselect_soft(target,allq,pool,k,seed):
    """Soft donor re-selection: k nearest with inverse-square-distance weighted draw; k=1 fallback."""
    tree=cKDTree(allq)
    distance,nearest=tree.query(target,k=1)
    kk=min(int(k),len(pool))
    if kk<2:return pool[np.asarray(nearest)],float(np.mean(distance)),int(kk)
    distance_k,nn=tree.query(target,k=kk)
    if np.asarray(nn).ndim==1:return pool[np.asarray(nn)],float(np.mean(distance_k)),int(kk)
    w=1.0/(distance_k**2+1e-3)
    cum=np.cumsum(w/w.sum(1,keepdims=True),axis=1);cum[:,-1]=1.0
    u=np.random.default_rng(seed).random(len(target))
    pos=np.minimum((u[:,None]>cum).sum(1),kk-1)
    chosen=nn[np.arange(len(target)),pos]
    return pool[chosen],float(np.mean(distance_k)),int(kk)


def conformal_radius(za_fit,zb_fit,za_cal,zb_all,alpha,cov_shrink,cov_strength):
    """Split-conformal radius: covot Gaussian map fit on the fit half only; scores on the calibration half.

    Nonconformity score = distance(mapped target, nearest late-train latent of the type).
    Returns None when the calibration is infeasible (too few cells or nonpositive covariance).
    """
    from sklearn.preprocessing import StandardScaler
    if len(za_fit)<10 or len(zb_fit)<10 or len(za_cal)<5 or len(zb_all)<5:return None
    scaler=StandardScaler().fit(np.vstack([za_fit,zb_fit]))
    a=scaler.transform(za_fit);b=scaler.transform(zb_fit)
    try:
        gmap=gaussian_map(shrunk_cov(a,cov_shrink),shrunk_cov(b,cov_shrink))
    except ValueError:
        return None
    mean_a=a.mean(0)
    cal=scaler.transform(za_cal)
    target=cal+cov_strength*(cal-mean_a)@(gmap-np.eye(a.shape[1])).T
    tree=cKDTree(scaler.transform(zb_all))
    distance,_=tree.query(target,k=1)
    n=len(distance)
    if n<5:return None
    level=min(int(np.ceil((n+1)*(1-alpha))),n)
    radius=float(np.sort(distance)[level-1])
    if not np.isfinite(radius) or radius<=0:return None
    return {'scaler':scaler,'map':gmap,'mean_fit':mean_a,'dim':int(a.shape[1]),'radius':radius,
            'n_fit':int(len(za_fit)),'n_cal':int(n),'radius_level':int(level),'score_median':float(np.median(distance))}


def conformal_reselect(target,allq,pool,radius,seed):
    """Donor candidates within the conformal radius; inverse-distance weighted draw; k=1 fallback."""
    tree=cKDTree(allq)
    distance,nearest=tree.query(target,k=1)
    donor=np.asarray(nearest).copy()
    mode='k1_fallback'
    if radius is not None and radius>0 and len(pool):
        balls=tree.query_ball_point(target,float(radius))
        rng=np.random.default_rng(seed)
        u=rng.random(len(target))
        n_ball=0
        for i,b in enumerate(balls):
            if not b:continue
            b=np.asarray(b)
            donor[i]=weighted_draw(b,np.linalg.norm(allq[b]-target[i],axis=1),u[i])
            n_ball+=1
        if n_ball:mode='conformal_ball'
    return pool[donor],float(np.mean(distance)),mode


def consistency_logw(cons_train,train_latent,query_latent,sigma):
    """Per-query-cell consistency log-weights from the k=1 nearest train neighbor."""
    tree=cKDTree(train_latent)
    distance,nn=tree.query(query_latent,k=1)
    d=np.asarray(cons_train)[nn]
    if not np.isfinite(d).all():raise ValueError('consistency values')
    logw=-(d**2)/(2.0*float(sigma)**2)
    return bounded_weights(logw),{'nearest_distance_mean':float(np.mean(distance)),'sigma':float(sigma)}
