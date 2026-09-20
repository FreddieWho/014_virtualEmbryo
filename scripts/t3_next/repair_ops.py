"""Nonnegative response operators and train-only mapping calibration."""
import numpy as np


def decode_rate(x, rate):
    x=np.asarray(x,dtype=float);rate=np.asarray(rate,dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(rate).all() or (x<0).any():
        raise ValueError('invalid response inputs')
    out=np.log1p(np.expm1(x)*np.exp(rate))
    return np.where(rate==0,x,out)


def calibrate_rate(controls,target_mean,bound,iterations=36):
    """Fit each rate to the mean of transformed individual controls, not a ratio of log means."""
    lo=np.full(controls.shape[1],-bound);hi=-lo
    for _ in range(iterations):
        mid=(lo+hi)/2;value=decode_rate(controls,mid).mean(0)
        lower=value<target_mean;lo=np.where(lower,mid,lo);hi=np.where(lower,hi,mid)
    return np.where(np.any(controls>0,axis=0),(lo+hi)/2,0.)


def mean_ratio(observed,factual,intervened,floor,bound):
    """Ratio of fitted geometric intensities, not arithmetic count means.

    The floor regularizes model intensities only. It never adds to observations.
    """
    rate=np.log((np.expm1(np.maximum(intervened,0))+floor)/(np.expm1(np.maximum(factual,0))+floor))
    return decode_rate(observed,np.clip(rate,-bound,bound))


def residual_calibration(raw,y,types,train,ridge):
    """Type means + train-fitted atlas residual slopes; no test outcomes consumed."""
    if not np.any(train):raise ValueError('empty calibration training set')
    pred=np.zeros_like(y,dtype=float);base=pred.copy();coeff={}
    fallback=y[train].mean(0)
    for t in sorted(set(types)):
        ix=types==t;tr=ix&train
        if not tr.any():pred[ix]=base[ix]=fallback;continue
        mu=y[tr].mean(0);rm=raw[tr].mean(0)
        xx=raw[tr]-rm;yy=y[tr]-mu
        slope=np.clip((xx*yy).sum(0)/((xx*xx).sum(0)+ridge),0,1)
        base[ix]=mu;pred[ix]=mu+(raw[ix]-rm)*slope;coeff[str(t)]=slope.tolist()
    return pred,base,coeff


def calibrated_transfer(observed,mapped_factual,source_delta,slopes,floor,bound):
    """Use the same fitted response slopes in validation and intervention transfer."""
    return mean_ratio(observed,mapped_factual,mapped_factual+source_delta*slopes,floor,bound)
