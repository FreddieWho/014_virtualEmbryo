"""Transfer only reproducible spatial gene ranks, never external FPKM units.
The source contains E7.0 regional pools, so scores are priors, not observed
challenge-cell anatomical labels or physical coordinates.
"""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
from scipy.stats import rankdata,spearmanr

def load_prior(path,genes):
    p=Path(path);tab=pd.read_csv(p,sep='\t').set_index('gene');aligned=tab.reindex(genes)
    weights=np.column_stack([aligned[x+'_stable_weight'].fillna(0).values for x in ['ap','pd']])
    return weights,{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'overlap':int(aligned.ap_stable_weight.notna().sum()),'n_genes':len(genes),'nonzero_per_axis':np.count_nonzero(weights,axis=0).tolist(),'policy':'source-replicate stable rank weights; no absolute-expression transfer'}

def program_scores(X,weights):
    X=X.toarray() if hasattr(X,'toarray') else np.asarray(X)
    # Rank genes across cells within a released sample. Zero ties remain tied.
    R=(rankdata(X,axis=0,method='average')-.5)/len(X)-.5
    denom=np.sum(np.abs(weights),axis=0)
    if np.any(denom==0):raise ValueError('No informative shared genes for external axis')
    return (R@weights)/denom

def source_diagnostics(scores,coords):
    scores=np.asarray(scores);coords=np.asarray(coords)[:,:3]
    centered=coords-coords.mean(0);design=np.column_stack([np.ones(len(coords)),centered])
    fit=np.linalg.lstsq(design,scores,rcond=None)[0];hat=design@fit
    r2=1-((scores-hat)**2).sum(0)/((scores-scores.mean(0))**2).sum(0)
    return {'linear_coordinate_r2_per_axis':r2.tolist(),'fitted_direction_vectors':fit[1:].T.tolist(),'score_quantiles':np.quantile(scores,[0,.25,.5,.75,1],axis=0).tolist(),'interpretation':'released-source diagnostic, not target accuracy or inferred true anatomy'}
