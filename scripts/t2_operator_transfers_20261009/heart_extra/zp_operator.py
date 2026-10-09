"""Single-axis H2 detected-entry shift allocation on the frozen X2 drift recipe.

Only positive source entries receive shift / max(detected_fraction, 0.05).
Clipping can create new zeros. The old per-row expm1 library restoration remains.
"""
import numpy as np

def apply(x, labels, states, delta, mode, permutation=None):
    x=np.asarray(x,np.float64)
    y=x.copy();lib0=np.expm1(x).sum(1);touched=np.zeros(len(x),bool);audit={}
    for j,s in enumerate(states):
        m=labels==s;touched|=m
        if not m.any():continue
        raw_d=delta[j]
        if mode=='zero_drift':raw_d=np.zeros_like(raw_d)
        elif mode=='geneperm':raw_d=raw_d[permutation]
        # Preserve old float32 median-delta scalar multiplication before adding to float64 X.
        drift=.9*raw_d
        if mode=='parent':
            proposed=x[m]+drift
        else:
            nz=x[m]>0;frac=np.maximum(nz.mean(0),.05)
            proposed=np.where(nz,x[m]+drift/frac,0.)
        y[m]=proposed
        audit[s]={'rows':int(m.sum()),'source_zero_fraction':float((x[m]==0).mean()),
                  'drift_l2':float(np.linalg.norm(drift)),
                  'preclip_negative_entries':int((proposed<0).sum()),
                  'preclip_state_mean_shift_l2':float(np.linalg.norm((proposed-x[m]).mean(0))),
                  'preclip_mean_drift_error_l2':float(np.linalg.norm((proposed-x[m]).mean(0)-drift))}
    np.clip(y,0,None,out=y)
    e=np.expm1(y[touched]);lib1=e.sum(1)
    e*=(lib0[touched]/np.maximum(lib1,1e-12))[:,None]
    y[touched]=np.log1p(e)
    y=y.astype(np.float32)
    ratio=np.expm1(y.astype(np.float64)).sum(1)/np.maximum(lib0,1e-12)
    summary={'mode':mode,'states':audit,'touched_rows':int(touched.sum()),
             'zero_to_positive':int(((x==0)&(y>0)).sum()),
             'positive_to_zero':int(((x>0)&(y==0)).sum()),
             'orphan_exact':bool(np.array_equal(x[~touched].astype(np.float32),y[~touched])),
             'max_abs_library_ratio_error':float(np.max(np.abs(ratio-1))),
             'changed_values':int((x.astype(np.float32)!=y).sum())}
    return y,summary
