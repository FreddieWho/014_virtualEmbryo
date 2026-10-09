"""Full empirical hurdle margins with the exact parent's gene-wise ordering."""
import numpy as np

def positive_at_ranks(values,q):
    values=np.sort(np.asarray(values,dtype=np.float64))
    if not len(values):raise ValueError('No observed positive values to interpolate')
    if len(values)==len(q) and np.array_equal(q,(np.arange(len(q))+.5)/len(q)):
        return values.copy()
    return np.interp(q,(np.arange(len(values))+.5)/len(values),values)

def transform_column(parent,carrier,wd,wl):
    p=np.asarray(parent,np.float32);c=np.asarray(carrier,np.float32)
    if wd==1 and wl==1:return p.copy()
    pv=p[p>0];cv=c[c>0];n=int(np.floor(len(cv)+float(wd)*(len(pv)-len(cv))+.5))
    out=np.zeros(len(p),np.float32)
    if not n:return out
    q=(np.arange(n)+.5)/n
    qp=positive_at_ranks(pv if len(pv) else cv,q)
    qc=positive_at_ranks(cv if len(cv) else pv,q)
    values=((1-float(wl))*qc+float(wl)*qp).astype(np.float32)
    # Highest parent values get the highest new positive values. Tied parent
    # zeros use paired observed-carrier expression, then fixed row order.
    order=np.lexsort((np.arange(len(p)),c,p))
    out[order[-n:]]=values
    return out

def apply_hurdle(parent,carrier,states,coarse_map,weights):
    if parent.shape!=carrier.shape or parent.shape[0]!=len(states):raise ValueError('Paired arrays required')
    out=np.array(parent,dtype=np.float32,copy=True);report={}
    for state in sorted(set(states)):
        rows=np.flatnonzero(states==state);group=coarse_map[state]
        if group not in weights:continue
        wd,wl=weights[group];changed=np.flatnonzero((wd!=1)|(wl!=1));entries=0;on=0;off=0
        for g in changed:
            before=parent[rows,g];after=transform_column(before,carrier[rows,g],wd[g],wl[g]);out[rows,g]=after
            entries+=int(np.count_nonzero(before!=after));on+=int(np.count_nonzero((before==0)&(after>0)));off+=int(np.count_nonzero((before>0)&(after==0)))
        report[state]={'group':group,'rows':len(rows),'reliability_active_genes':len(changed),'changed_entries':entries,'on':on,'off':off}
    return out,report
