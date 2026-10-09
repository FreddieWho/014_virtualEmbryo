"""Fixed-support within-state row coupling via learned source spatial fields.

Spatial programme identities come from E7.0 Geo-seq. Only the row-to-position
permutation changes: complete expression rows and every coordinate are retained.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from geometry import proper_alignment,rms_radius
from external_programs import program_scores
from transport import ranks

def standardized(x):
    return (x-x.mean(0))/np.maximum(x.std(0),1e-6)

def design(C):
    x,y,z=C.T
    return np.column_stack([np.ones(len(C)),x,y,z,x*x,y*y,z*z,x*y,x*z,y*z])

def fit_field(C,S):
    D=design(C);penalty=.01*len(C)*np.eye(D.shape[1]);penalty[0,0]=0
    B=np.linalg.solve(D.T@D+penalty,D.T@standardized(S))
    prediction=D@B;truth=standardized(S)
    r2=1-((truth-prediction)**2).sum(0)/np.maximum((truth**2).sum(0),1e-12)
    return B,r2

def rewire(X,base_coords,base_labels,LX,LC,LL,RX,RC,RL,t,prior=None,mode='spatial',shuffle=False,seed=20261009,source_coords=None,locality=False):
    X=np.asarray(X);LL=np.asarray(LL).astype(str);RL=np.asarray(RL).astype(str);labels=np.asarray(base_labels).astype(str)
    LC=np.asarray(LC)[:,:3];RC=np.asarray(RC)[:,:3];RC=RC.mean(0)+(RC-RC.mean(0))*(rms_radius(LC)/rms_radius(RC))
    RC,reg=proper_alignment(LC,LL,RC,RL)
    # Parent is a uniform scaled/translated source-left draw. Bring physical
    # coordinates into the same normalized shape frame as both released stages.
    center=LC.mean(0);scale=rms_radius(LC)
    lc=(LC-center)/scale;rc=(RC-center)/scale
    if source_coords is None:raise ValueError('Verified source-left coordinates required for the carrier rows')
    bc=(np.asarray(source_coords)[:,:3]-center)/scale
    if mode=='spatial':
        w=prior.copy()
        if shuffle:w=w[np.random.default_rng(seed).permutation(len(w))]
        SL=program_scores(LX,w);SR=program_scores(RX,w);SB=program_scores(X,w)
    else:
        ZL,ZR,ZB=ranks(LX),ranks(RX),ranks(X);pca=PCA(n_components=12,svd_solver='randomized',random_state=seed).fit(np.vstack([ZL,ZR]));SL=pca.transform(ZL);SR=pca.transform(ZR);SB=pca.transform(ZB)
    perm=np.arange(len(X));audit={};shared=sorted(set(labels)&set(LL)&set(RL))
    for s in shared:
        rows=np.flatnonzero(labels==s);l=LL==s;r=RL==s
        if len(rows)<4:continue
        BL,ql=fit_field(lc[l],SL[l]);BR,qr=fit_field(rc[r],SR[r])
        expect=design(bc[rows])@((1-t)*BL+t*BR)
        target=standardized(expect);donor=standardized(SB[rows]);cost=cdist(target,donor,'sqeuclidean')/target.shape[1]
        local_scale=None
        if locality:
            near=NearestNeighbors(n_neighbors=min(16,len(rows)),n_jobs=1).fit(bc[rows]);dd,_=near.kneighbors(bc[rows]);local_scale=float(np.median(dd[:,-1]));local_scale=max(local_scale,1e-6)
            cost+=cdist(bc[rows],bc[rows],'sqeuclidean')/(local_scale**2)
        ii,jj=linear_sum_assignment(cost);perm[rows[ii]]=rows[jj]
        audit[s]={'n':len(rows),'locality_scale':local_scale,'left_field_r2':ql.tolist(),'right_field_r2':qr.tolist(),'mapping_identity_fraction':float(np.mean(ii==jj)),'mean_matching_cost':float(cost[ii,jj].mean())}
    out=X[perm].copy()
    assert np.array_equal(np.sort(perm),np.arange(len(X)))
    assert np.array_equal(labels[perm],labels)
    return out,perm,{'mode':mode,'locality':locality,'gene_shuffle':shuffle,'method':'fixed-coordinate within-state expression-row permutation, quadratic source spatial programme fields','t':t,'seed':seed,'ridge_per_n':.01,'state_audit':audit,'global_expression_row_multiset_exact':True,'coordinate_array_exact':True,'fallback_states':sorted(set(labels)-set(shared)),'registration':reg}
