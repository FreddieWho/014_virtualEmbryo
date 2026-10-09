"""External partial-correlation regularizer with exact per-state marginals.

A rank-Gaussian precision matrix predicts each gene from the others. Average
original and conditional rank (fixed 1/2), then reassign existing sorted gene
values. This edits joint dependence only: zero mass, all positive values,
state means/counts, rows and geometry remain exact. It transfers no UMI units.
"""
import numpy as np
from scipy.stats import rankdata,norm
from sklearn.covariance import LedoitWolf

def gaussian_ranks(X):
    U=(rankdata(np.asarray(X),axis=0,method='average')-.5)/len(X)
    return norm.ppf(np.clip(U,1e-4,1-1e-4))

def fit_conditional(X):
    Z=gaussian_ranks(X);model=LedoitWolf().fit(Z);P=model.precision_;B=-P/np.diag(P)[None,:];np.fill_diagonal(B,0)
    return B,{'n_fit_cells':len(X),'n_genes':X.shape[1],'ledoit_wolf_shrinkage':float(model.shrinkage_),'rank_gaussian':True,'blend':.5,'parameter_search':False}

def regularize(X,labels,B):
    X=np.asarray(X);out=X.copy();labels=np.asarray(labels).astype(str);audit={}
    for s in sorted(set(labels)):
        idx=np.flatnonzero(labels==s);v=X[idx]
        if len(idx)<4:continue
        z=gaussian_ranks(v);conditional=z@B
        ranks=rankdata(z,axis=0,method='average');cranks=rankdata(conditional,axis=0,method='average');key=(ranks+cranks)*.5
        order=np.argsort(key,axis=0,kind='stable');sortedvals=np.sort(v,axis=0);new=np.empty_like(v)
        np.put_along_axis(new,order,sortedvals,axis=0);out[idx]=new
        assert np.array_equal(np.sort(new,axis=0),sortedvals),'Marginal preservation failed'
        audit[s]={'n':len(idx),'changed_entries_fraction':float(np.mean(new!=v))}
    return out,{'states':audit,'exact_state_gene_marginals':True,'zeros_and_positive_values_preserved':True}
