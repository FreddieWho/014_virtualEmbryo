"""Joint within-state endpoint matching; external data alter the metric only.

No external absolute expression, proportions, or fabricated 3D coordinates are
transferred. One nearest right donor is selected per actual left carrier cell;
left residuals and parent expression are preserved. The zero-external control
uses the same internal expression PCA and geometric matching architecture.
"""
import numpy as np
from scipy.stats import rankdata
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from geometry import proper_alignment,rms_radius
from external_programs import program_scores

def ranks(X):return (rankdata(np.asarray(X),axis=0)-.5)/len(X)-.5

def standardize_pair(a,b):
    both=np.vstack([a,b]);mu=both.mean(0);sd=both.std(0);sd=np.maximum(sd,1e-6)
    return (a-mu)/sd,(b-mu)/sd

def transport(base_coords,base_labels,source_rows,left_coords,left_labels,LX,right_coords,right_labels,RX,t,mode='internal',prior=None,external_counts=None,shuffle=False,seed=20261009,support="displacement"):
    ll=np.asarray(left_labels).astype(str);rl=np.asarray(right_labels).astype(str);bl=np.asarray(base_labels).astype(str)
    lc=np.asarray(left_coords,float)[:,:3];rc=np.asarray(right_coords,float)[:,:3]
    right_shape_scale=1.
    if support=='mixture':
        right_shape_scale=rms_radius(lc)/rms_radius(rc);rc=rc.mean(0)+(rc-rc.mean(0))*right_shape_scale
    aligned,align=proper_alignment(lc,ll,rc,rl);lrank=ranks(LX);rrank=ranks(RX)
    # Baseline uses only released endpoint gene coexpression. Fixed 12 components.
    fit=np.vstack([lrank,rrank]);pca=PCA(n_components=12,svd_solver='randomized',random_state=seed).fit(fit)
    eL=pca.transform(lrank);eR=pca.transform(rrank)
    if mode=='scrna':
        ext=ranks(external_counts)
        if shuffle:ext=ext[:,np.random.default_rng(seed).permutation(ext.shape[1])]
        pca=PCA(n_components=12,svd_solver='randomized',random_state=seed).fit(ext)
        eL=pca.transform(lrank);eR=pca.transform(rrank)
    eL,eR=standardize_pair(eL,eR)
    eL/=np.sqrt(eL.shape[1]);eR/=np.sqrt(eR.shape[1])
    gL,gR=standardize_pair(lc,aligned);gL/=np.sqrt(3);gR/=np.sqrt(3)
    fL=np.column_stack([gL,eL]);fR=np.column_stack([gR,eR])
    if mode=='spatial':
        w=prior.copy()
        if shuffle:w=w[np.random.default_rng(seed).permutation(len(w))]
        sL=program_scores(LX,w);sR=program_scores(RX,w);sL,sR=standardize_pair(sL,sR)
        # External score block has same unit expected squared norm as each
        # geometry / internal-expression block. No weight or parameter search.
        fL=np.column_stack([fL,sL/np.sqrt(2)]);fR=np.column_stack([fR,sR/np.sqrt(2)])
    out=lc[source_rows].copy();audit={};shared=sorted(set(bl)&set(ll)&set(rl))
    for state in shared:
        m=np.flatnonzero(bl==state);right=np.flatnonzero(rl==state);left=source_rows[m]
        if support=='mixture':
            # Fixed time-proportion count, fixed per-state RNG, no metric tuning.
            k=int(np.floor(t*len(m)+.5));order=np.random.default_rng(seed+sum(map(ord,state))).permutation(len(m));take=order[:k]
            copies=max(1,int(np.ceil(k/len(right))));pool=np.tile(right,copies)
            cost=cdist(fL[left[take]],fR[pool],metric='sqeuclidean')
            ii,jj=linear_sum_assignment(cost);chosen=pool[jj]
            out[m[take[ii]]]=aligned[chosen]
            distances=np.sqrt(cost[ii,jj])
        else:
            nn=NearestNeighbors(n_neighbors=1,algorithm='brute',n_jobs=1).fit(fR[right]);dist,j=nn.kneighbors(fL[left]);chosen=right[j[:,0]]
            out[m]=(1-t)*lc[left]+t*aligned[chosen];distances=dist.ravel();k=len(m)
        unique,counts=np.unique(chosen,return_counts=True);prob=counts/max(1,counts.sum())
        audit[state]={'n_carrier':len(m),'n_right':len(right),'right_selected_rows':k,'unique_right_donors':len(unique),'max_right_reuse':int(counts.max()) if len(counts) else 0,'donor_entropy':float(-np.sum(prob*np.log(prob))) if len(prob) else 0,'mean_matching_distance':float(distances.mean()) if len(distances) else 0}
    before=rms_radius(out);target=rms_radius(base_coords);center=out.mean(0);out=center+(out-center)*(target/before)
    return out,{'mode':mode,'support':support,'right_shape_scale':right_shape_scale,'shuffle_control':shuffle,'t':t,'registration':align,'states':audit,'fallback_states':sorted(set(bl)-set(shared)),'rms_target':target,'rms_before_lock':before,'parent_expression_frozen':True,'mechanism':'paired nonlinear displacement, no generated Gaussian points','internal_pca_components':12,'blocks_equal_norm':True,'parameter_search':False}
