"""Response operators only: never smooth WT expression or use KO truth."""
import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree


def decompose(p1,m1,p0,m0):
    probability=(p0-p1)*(m0+m1)*.5
    intensity=(m0-m1)*(p0+p1)*.5
    return probability,intensity


def agree_rate(base,hurdle,rate,strength=.5,eps=1e-8):
    change=np.asarray(hurdle,float)-base;r=np.broadcast_to(rate,change.shape)
    mask=(np.abs(change)>eps)&(np.abs(r)>eps)&(np.sign(change)==np.sign(r))
    return np.where(mask,strength*r,0.),mask


def graph_operator(coords,k,alpha):
    n=len(coords)
    if n<2:return sparse.eye(n,format='csr')
    neighbors=cKDTree(coords).query(coords,k=min(k+1,n))[1]
    i=np.repeat(np.arange(n),neighbors.shape[1]);j=neighbors.ravel();keep=i!=j
    adj=sparse.csr_matrix((np.ones(np.sum(keep)),(i[keep],j[keep])),shape=(n,n))
    adj=adj.maximum(adj.T);adj.data[:]=1
    degree=np.asarray(adj.sum(1)).ravel();scale=max(float(degree.max()),1.)
    return sparse.eye(n,format='csr')-alpha*(sparse.diags(degree)-adj)/scale


def diffuse(delta,coords,types,active,k=8,alpha=.5):
    if not 0<=alpha<=1:raise ValueError('alpha outside convex diffusion range')
    out=np.array(delta,dtype=float,copy=True);info=[]
    for t in sorted(set(types)):
        ix=np.flatnonzero((np.asarray(types)==t)&active)
        if not len(ix):continue
        w=graph_operator(coords[ix],k,alpha);out[ix]=w@out[ix]
        err=float(np.max(np.abs(out[ix].mean(0)-np.asarray(delta)[ix].mean(0))))
        if err>1e-10:raise ValueError('response mean changed')
        info.append({'type':t,'cells':len(ix),'edges_with_self':w.nnz,'predecode_mean_maxabs':err})
    return out,info
