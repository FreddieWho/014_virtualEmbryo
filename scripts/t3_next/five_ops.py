"""Five-route operators. No filesystem, KO truth or server-score access."""
import numpy as np


def quantile_response(values,high,low,strength,bound,grid=101):
    """Positive-value quantile transport, preserving zeros and within-column ranks."""
    out=np.asarray(values,dtype=float).copy()
    q=np.linspace(0,1,grid)
    for j in range(values.shape[1]):
        h=high[:,j];h=h[h>0];l=low[:,j];l=l[l>0]
        if len(h)<3 or len(l)<3:continue
        hq=np.quantile(h,q);lq=np.quantile(l,q)
        # Collapse tied source knots to avoid arbitrary interpolation at ties.
        knots,inv=np.unique(hq,return_inverse=True)
        dest=np.bincount(inv,weights=lq)/np.bincount(inv)
        use=values[:,j]>0
        mapped=np.interp(values[use,j],knots,dest)
        blended=(1-strength)*values[use,j]+strength*mapped
        old=np.expm1(values[use,j])
        new=np.clip(np.expm1(blended),old*np.exp(-bound),old*np.exp(bound))
        out[use,j]=np.log1p(new)
    # Exact identity avoids roundoff-only candidates.
    if np.array_equal(high,low):return np.asarray(values).copy()
    return out


def bounded_add(x,delta,strength):
    """Positive log-expression increments; negative raw-intensity attenuation.

    A two-part response avoids projecting negative requests at observed zeros.
    Both branches have exact zero-response identity. This is a prediction
    parameterization, not a calibrated count likelihood.
    """
    change=np.clip(strength*np.asarray(delta),-np.log(2),np.log(2))
    x=np.asarray(x)
    down=np.log1p(np.expm1(x)*np.exp(np.minimum(change,0)))
    return np.where(change<0,down,x+change)


def latent_predict(z,y,train,test,rank=6,alpha=1.):
    """Response factors and kernel bandwidth fitted exclusively on training genes."""
    train=np.asarray(train);test=np.asarray(test)
    if set(train)&set(test):raise ValueError('gene overlap')
    mu=z[train].mean(0);sd=np.maximum(z[train].std(0),1e-4)
    a=(z[train]-mu)/sd;b=(z[test]-mu)/sd
    dist=np.maximum(((a[:,None]-a[None,:])**2).mean(2),0)
    bandwidth=max(float(np.median(dist[np.triu_indices(len(a),1)])),1e-6)
    kernel=np.exp(-dist/(2*bandwidth))
    center=y[train].mean(0);u,s,vt=np.linalg.svd(y[train]-center,full_matrices=False)
    k=min(rank,len(train)-1,len(s));basis=vt[:k]
    weights=np.linalg.solve(kernel+alpha*np.eye(len(a)),(y[train]-center)@basis.T)
    cross=np.exp(-((b[:,None]-a[None,:])**2).mean(2)/(2*bandwidth))
    return center+(cross@weights)@basis,{'feature_mean':mu,'feature_sd':sd,'train_features':a,'bandwidth':bandwidth,'response_mean':center,'basis':basis,'weights':weights,'singular_values':s,'train_indices':train}


def shrink_weight(mean,pred,truth):
    d=np.asarray(pred)-mean;den=float(np.sum(d*d))
    return float(np.clip(np.sum((truth-mean)*d)/den,0,1)) if den>1e-15 else 0.


def stability_weight(effects,prior):
    e=np.asarray(effects);mu=e.mean(0);sd=e.std(0)
    sign=np.abs(np.sign(e).mean(0))
    return sign*np.abs(mu)/(np.abs(mu)+sd+prior*max(float(np.mean(np.abs(e))),1e-8))
