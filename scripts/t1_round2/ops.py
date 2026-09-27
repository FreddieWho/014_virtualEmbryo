"""Whole-row mixture and uncertainty operators; no truth input."""
import numpy as np
from scipy.special import expit, logit
from scripts.t1_five.ops import systematic_resample


def bounded_weights(logw, cap=2.):
    x=np.asarray(logw,float)
    if not np.isfinite(x).all():raise ValueError('nonfinite weights')
    return np.exp(np.clip(x-np.median(x),-np.log(cap),np.log(cap)))


def abundance_step(early,late,alpha=.5,strength=.5,cap=2.):
    a=np.asarray(early,float);b=np.asarray(late,float)
    if (a<0).any() or (b<0).any():raise ValueError('negative counts')
    pa=(a+alpha)/(a.sum()+alpha*len(a));pb=(b+alpha)/(b.sum()+alpha*len(b))
    return np.clip(strength*np.log(pb/pa),-np.log(cap),np.log(cap))


def mixture_donors(types,steps):
    w=np.exp(np.array([steps.get(t,0.) for t in types]))
    return systematic_resample(w)


def shrink_step(delta,variance):
    d=np.asarray(delta,float);v=np.asarray(variance,float)
    if (v<0).any():raise ValueError('negative variance')
    return d*np.divide(d*d,d*d+v,out=np.zeros_like(d),where=(d*d+v)>0)


def mass_shrink(a,b,m,future,bandwidth=.05,alpha=.5):
    """Shrink logit and positive quantile increments using sampling variance."""
    a=np.asarray(a);b=np.asarray(b);ap=a[a>0];bp=b[b>0]
    if m is None or m.get('identity'):return m
    out=dict(m)
    za=len(a)-len(ap);zb=len(b)-len(bp)
    # Jeffreys-smoothed variance; retain original point estimator for comparability.
    var=sum(1./(v+alpha) for v in [za,len(ap),zb,len(bp)])
    ps=m['psource'];step=logit(np.clip(m['pout'],1e-6,1-1e-6))-logit(np.clip(ps,1e-6,1-1e-6))
    out['pout']=float(expit(logit(np.clip(ps,1e-6,1-1e-6))+shrink_step(step,var)))
    q=np.linspace(0,1,len(m['qsource']))
    # Quantile variance q(1-q)/(n f(Q(q))^2); finite-difference quantile density.
    variance=np.zeros(len(q))
    for x in [ap,bp]:
        lo=np.maximum(q-bandwidth,0);hi=np.minimum(q+bandwidth,1)
        derivative=(np.quantile(x,hi)-np.quantile(x,lo))/(hi-lo)
        qe=np.clip(q,1/(2*len(x)),1-1/(2*len(x)))
        variance+=qe*(1-qe)*derivative**2/len(x)
    delta=m['qout']-m['qsource']
    out['qout']=np.maximum.accumulate(np.maximum(m['qsource']+shrink_step(delta,variance),0))
    out['zero_step_variance']=float(var)
    out['quantile_step_variance']=variance
    return out
