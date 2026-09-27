import numpy as np
from scipy.special import expit,logit
from scripts.t3_next.repair_ops import decode_rate
from scripts.t3_next.five_ops import shrink_weight


def gene_shrink(mean,pred,truth,prior_scale=10.):
    d=pred-mean;den=np.sum(d*d,axis=0);num=np.sum((truth-mean)*d,axis=0)
    global_w=shrink_weight(mean,pred,truth)
    positive=den[den>1e-15];tau=prior_scale*float(np.median(positive)) if len(positive) else 1.
    w=np.clip((num+tau*global_w)/(den+tau),0,1)
    return w,global_w,tau


def occupancy_decode(x,params,groups,strength=.25):
    """Deterministic hurdle distribution transfer; whole-group ranks, no smoothing.

    Shared library ranks allocate zero activations; positive intensities are
    within-group empirical quantiles. Returned expression, not expected tiny
    mass at every zero, is what both source evaluation and inference consume.
    """
    x=np.asarray(x,dtype=float);g=x.shape[1];dp=np.asarray(params[:g])*strength;rate=np.asarray(params[g:])*strength
    out=x.copy()
    for group in sorted(set(groups)):
        ids=np.flatnonzero(groups==group);a=x[ids];lib=a.sum(1)
        for j in range(g):
            pos=np.flatnonzero(a[:,j]>0);zero=np.flatnonzero(a[:,j]==0)
            if not len(pos):continue  # absent WT support: no arbitrary positive amplitude
            p=len(pos)/len(a);pnew=expit(logit(np.clip(p,1e-6,1-1e-6))+dp[j])
            # dp=0 preserves support exactly, including all-positive columns.
            count=len(pos) if dp[j]==0 else int(np.clip(np.rint(pnew*len(a)),0,len(a)))
            out[ids,j]=decode_rate(a[:,j],rate[j])
            if count<len(pos):
                kill=pos[np.argsort(a[pos,j],kind='stable')[:len(pos)-count]];out[ids[kill],j]=0
            elif count>len(pos):
                add=zero[np.argsort(-lib[zero],kind='stable')[:count-len(pos)]]
                q=(np.arange(len(add))+.5)/max(len(add),1)
                values=np.quantile(a[pos,j],q)
                out[ids[add],j]=decode_rate(values,rate[j])
    return out
