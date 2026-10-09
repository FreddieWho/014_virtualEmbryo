"""Detection-invariant positive displacement rescaling with explicit repair audit."""
import numpy as np
from hurdle_margins import positive_at_ranks


def transform_positive(parent, carrier, slope):
    p=np.asarray(parent,np.float32);c=np.asarray(carrier,np.float32)
    ix=np.flatnonzero(p>0);cv=c[c>0]
    stat={k:0 for k in ['positive_values','floored','adjacent_steps','negative_steps','reordered','repair_changed_values','rank_distance_sum','rank_distance_max','repair_abs_sum','repair_abs_max']}
    if slope==1 or not len(ix) or not len(cv):return p.copy(),stat
    order=ix[np.argsort(p[ix],kind='stable')];pv=p[order].astype(float)
    q=(np.arange(len(ix))+.5)/len(ix);qc=positive_at_ranks(cv,q)
    raw=qc+float(slope)*(pv-qc)
    floor=min(float(pv.min()),float(cv.min()));floored=np.maximum(raw,floor)
    permutation=np.argsort(floored,kind='stable');repaired=floored[permutation]
    dist=np.abs(permutation-np.arange(len(ix)));delta=np.abs(repaired-floored)
    stat.update(positive_values=len(ix),floored=int((raw<floor).sum()),adjacent_steps=max(len(ix)-1,0),negative_steps=int((np.diff(floored)<0).sum()),reordered=int((permutation!=np.arange(len(ix))).sum()),repair_changed_values=int((delta>0).sum()),rank_distance_sum=int(dist.sum()),rank_distance_max=int(dist.max(initial=0)),repair_abs_sum=float(delta.sum()),repair_abs_max=float(delta.max(initial=0)))
    out=p.copy();out[order]=repaired.astype(np.float32)
    assert np.array_equal(out>0,p>0) and np.all(np.diff(out[order])>=0)
    return out,stat


def apply_displacement(parent,carrier,states,coarse_map,slopes):
    out=np.array(parent,dtype=np.float32,copy=True);report={}
    for state in sorted(set(states)):
        rows=np.flatnonzero(states==state);group=coarse_map[state]
        if group not in slopes:continue
        genes=np.flatnonzero(slopes[group]!=1);total={k:0 for k in ['positive_values','floored','adjacent_steps','negative_steps','reordered','repair_changed_values','rank_distance_sum','rank_distance_max','repair_abs_sum','repair_abs_max']};changed=0;touched_genes=0
        for gene in genes:
            p=parent[rows,gene];v,s=transform_positive(p,carrier[rows,gene],slopes[group][gene]);out[rows,gene]=v
            changed+=int(np.count_nonzero(v!=p));touched_genes+=int(s['positive_values']>0)
            for k in total:total[k]=max(total[k],s[k]) if k.endswith('_max') else total[k]+s[k]
        total.update(rows=len(rows),group=group,eligible_genes=len(genes),touched_genes=touched_genes,changed_entries=changed)
        report[state]=total
    return out,report
