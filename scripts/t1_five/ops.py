"""Array-only T1 operators. Fitted models never consume report targets."""
import numpy as np
from scipy.special import ndtr,ndtri,expit,logit


def systematic_resample(weights):
    w=np.asarray(weights,dtype=float)
    if w.ndim!=1 or not len(w) or not np.isfinite(w).all() or (w<=0).any():raise ValueError('invalid weights')
    c=np.cumsum(w/w.sum());c[-1]=1
    return np.searchsorted(c,(np.arange(len(w))+.5)/len(w),side='left')


def rate_decode(x,rate):
    x=np.asarray(x);r=np.asarray(rate)
    if (x<0).any() or not np.isfinite(x).all() or not np.isfinite(r).all():raise ValueError('invalid rate inputs')
    out=np.log1p(np.expm1(x.astype(float))*np.exp(r))
    return np.where(r==0,x,out)


def borrow_rates(query,centroids,rates,k):
    a=np.asarray(centroids,float);q=np.asarray(query,float)
    similarity=(a@q)/(np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(q),1e-12))
    ix=np.argsort(-similarity,kind='stable')[:min(k,len(a))]
    weights=np.exp((similarity[ix]-similarity[ix].max())/.1);weights/=weights.sum()
    full=np.zeros(len(a));full[ix]=weights
    return full@rates,full


def rate_factors(rates,rank):
    r=np.asarray(rates,float);mu=r.mean(0);u,s,vt=np.linalg.svd(r-mu,full_matrices=False)
    k=min(rank,max(0,len(r)-1));basis=vt[:k];scores=(r-mu)@basis.T
    return mu+scores@basis,{'mean':mu,'basis':basis,'scores':scores,'singular_values':s}


def empirical_transport(a,b,x,library_rank,grid=41):
    p=float(np.mean(a==0));q=np.linspace(0,1,grid)
    u=np.searchsorted(np.sort(a),x,side='right')/len(a)
    u[x==0]=library_rank[x==0]*p
    qa=np.quantile(a,q);qb=np.quantile(b,q)
    return np.interp(u,q,np.maximum.accumulate(np.maximum(qa+(qb-qa),0)))


def positive_stats(x):
    v=np.asarray(x)[np.asarray(x)>0]
    return float(np.mean(x==0)),v


def fit_mixture(a,b,lane,future,grid=101):
    pa,ap=positive_stats(a);pb,bp=positive_stats(b)
    if len(ap)<5 or len(bp)<5:return None
    same=pa==pb and len(ap)==len(bp) and np.array_equal(np.sort(ap),np.sort(bp))
    m={'lane':lane,'upper':float(b.max()+np.log(2)),'identity':bool(same)}
    if lane=='o1mass':
        step=np.clip(logit(np.clip(pb,1e-6,1-1e-6))-logit(np.clip(pa,1e-6,1-1e-6)),-2,2)
        m['psource']=pb if future else pa
        # Report and forecast use the exact same capped time increment.
        m['pout']=float(expit(logit(np.clip(m['psource'],1e-6,1-1e-6))+step))
        qa=np.quantile(ap,np.linspace(0,1,grid));qb=np.quantile(bp,np.linspace(0,1,grid))
        m['qsource']=qb if future else qa
        m['qout']=np.maximum.accumulate(np.maximum(m['qsource']+np.clip(qb-qa,-np.log(2),np.log(2)),0))
        m['positive_sorted']=np.sort(bp if future else ap)
    elif lane=='n2param':
        m.update(psource=pa,pout=pb,mu_source=float(np.log(ap).mean()),sd_source=max(float(np.log(ap).std()),.05),mu_out=float(np.log(bp).mean()))
        m['sd_out']=float(np.clip(max(float(np.log(bp).std()),.05),m['sd_source']*.5,m['sd_source']*2))
    else:raise ValueError(lane)
    return m


def apply_mixture(m,x,library_rank):
    x=np.asarray(x);p=m['psource'];dest=m['pout']
    if m.get('identity',False):return x.copy()
    if m['lane']=='o1mass':
        v=m['positive_sorted'];up=np.searchsorted(v,x,side='right')/len(v)
    else:up=ndtr((np.log(np.maximum(x,1e-12))-m['mu_source'])/m['sd_source'])
    u=p+(1-p)*up;u[x==0]=library_rank[x==0]*p
    positive=u>dest;out=np.zeros(len(x))
    rank=np.clip((u[positive]-dest)/max(1-dest,1e-8),1e-6,1-1e-6)
    if m['lane']=='o1mass':out[positive]=np.interp(rank,np.linspace(0,1,len(m['qout'])),m['qout'])
    else:out[positive]=np.exp(m['mu_out']+m['sd_out']*ndtri(rank))
    return np.minimum(out,m['upper'])


def mixture_transport(a,b,x,library_rank,lane,future,grid=101):
    m=fit_mixture(a,b,lane,future,grid)
    if m is None:return x.copy(),None
    return apply_mixture(m,x,library_rank),m
