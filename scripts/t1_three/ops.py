"""Deterministic whole-row sampling with explicit output quotas."""
import numpy as np


def systematic_indices(weights,n):
    w=np.asarray(weights,float)
    if w.ndim!=1 or not len(w) or not np.isfinite(w).all() or (w<=0).any() or n<0:raise ValueError('invalid weights/count')
    if n==0:return np.empty(0,int)
    c=np.cumsum(w/w.sum());c[-1]=1
    return np.searchsorted(c,(np.arange(n)+.5)/n,side='left')


def joint_donors(types,weights,composition):
    types=np.asarray(types);target=types[composition];out=np.empty(len(target),int)
    for t in sorted(set(target)):
        pool=np.flatnonzero(types==t);slots=np.flatnonzero(target==t)
        out[slots]=pool[systematic_indices(np.asarray(weights)[pool],len(slots))]
    return out


def allocation(types,n):
    labels,counts=np.unique(types,return_counts=True);desired=counts*n/counts.sum();out=np.floor(desired).astype(int)
    order=np.argsort(-(desired-out),kind='stable');out[order[:n-out.sum()]]+=1
    return dict(zip(labels,out))


def mixture_indices(types_a,types_b,fraction,seed):
    if len(types_a)!=len(types_b) or not 0<=fraction<=1:raise ValueError('mixture shape/weight')
    n=len(types_a);na=int(np.floor(n*fraction));rng=np.random.default_rng(seed);rows=[];sides=[]
    for side,types,quota in [(0,np.asarray(types_a),na),(1,np.asarray(types_b),n-na)]:
        for t,k in allocation(types,quota).items():
            chosen=rng.permutation(np.flatnonzero(types==t))[:k]
            rows.extend(chosen.tolist());sides.extend([side]*len(chosen))
    order=rng.permutation(n)
    return np.asarray(sides)[order],np.asarray(rows)[order]
