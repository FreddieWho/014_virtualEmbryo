"""Frozen residual/conditional-activation emitter family. Source response unchanged."""
import numpy as np
from scipy.special import logsumexp
from crossko import closed

def detection_propensity(model, carrier, lab):
    # WT-only ridge association, explicitly subtract own gene contribution from PCs.
    z = model.pca.transform(carrier[:, model.features]).astype(float)
    load = model.pca.components_.T
    result = np.zeros(carrier.shape, dtype=np.float32)
    for s in range(model.S):
        rows = np.flatnonzero(lab == s)
        if len(rows) < 20: continue
        x = carrier[rows].astype(float); Z = z[rows]; Z -= Z.mean(0)
        xc = x - x.mean(0); Y = (x > 0).astype(float); Y -= Y.mean(0)
        C = Z.T @ Z; B = Z.T @ Y; ZX = Z.T @ xc
        xx = (xc * xc).sum(0); xy = (xc * Y).sum(0)
        for j in range(model.G):
            l = load[j]; c = C - np.outer(ZX[:,j],l) - np.outer(l,ZX[:,j]) + xx[j]*np.outer(l,l)
            penalty = .1 * max(float(np.trace(c))/len(l), 1.)
            beta = np.linalg.solve(c + penalty*np.eye(len(l)), B[:,j] - l*xy[j])
            result[rows,j] = Z@beta - xc[:,j]*(l@beta)
    return result

def emit(model, carrier, response, mode='combined', residual=False, conditional=False):
    if not residual and not conditional:
        return model.emit(carrier,response,mode=mode)
    closed(carrier)
    if not np.any(response['delta']) and (mode=='within' or not np.any(response['composition'])):
        return carrier.copy(),np.arange(len(carrier))
    rng=np.random.default_rng(model.seed);lab=model.assign(carrier);ix=np.arange(len(carrier))
    propensity=detection_propensity(model,carrier,lab) if conditional else None
    if mode in ('composition','combined'):
        mass=np.bincount(lab,minlength=model.S).astype(float);mass*=np.exp(np.clip(response['composition'],-2,2));mass/=mass.sum()
        p=mass[lab]/np.maximum(np.bincount(lab,minlength=model.S)[lab],1);p/=p.sum();ix=rng.choice(ix,len(ix),replace=True,p=p)
    out=carrier[ix].copy().astype(float);labels=lab[ix]
    global_q,_=model.positive_quantiles(carrier,np.zeros((model.G,len(model.positive_q))))
    if mode in ('within','combined') and np.any(response['delta']):
        for s in range(model.S):
            rows=np.flatnonzero(labels==s)
            if not len(rows) or not response['support'][s]:continue
            local=out[rows].copy();baseq,_=model.positive_quantiles(local,global_q)
            for j in range(model.G):
                d=response['delta'][s,j]
                if not np.any(d):continue
                frac=np.clip((local[:,j]>0).mean()+d[-1],0,1);n=int(np.floor(len(rows)*frac+rng.random()));out[rows,j]=0
                if not n:continue
                noise=rng.uniform(0,1e-8,len(rows));rankvalue=local[:,j]+noise
                if conditional:
                    zero=local[:,j]==0;v=propensity[ix[rows],j];rz=np.argsort(np.argsort(v[zero]+noise[zero],kind='stable'),kind='stable')
                    rankvalue[zero]=(rz+1)/(len(rz)+1)*1e-8
                order=np.argsort(rankvalue,kind='stable')[-n:]
                tq=np.maximum.accumulate(np.maximum(baseq[j]+d[:-1],0));values=np.interp((np.arange(n)+.5)/n,model.positive_q,tq)
                if residual:
                    pos=np.flatnonzero(local[:,j]>0);pos=pos[np.argsort(local[pos,j],kind='stable')]
                    rr=np.zeros(len(rows));rr[pos]=local[pos,j]-np.interp((np.arange(len(pos))+.5)/len(pos),model.positive_q,baseq[j])
                    values=np.maximum.accumulate(np.maximum(values+rr[order],0))
                out[rows[order],j]=values
    with np.errstate(divide='ignore',invalid='ignore'):lc=out+np.log(-np.expm1(-out))
    den=logsumexp(lc,axis=1)
    if not np.isfinite(den).all():raise ValueError('Empty output cell')
    out=np.log1p(10000*np.exp(lc-den[:,None])).astype('float32');closed(out);return out,ix
