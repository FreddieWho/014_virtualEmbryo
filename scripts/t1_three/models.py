import pickle
from pathlib import Path
import numpy as np
from scripts.t1_five.models import predict as predict_old
from scripts.t1_round2.ops import mixture_donors
from .ops import joint_donors,mixture_indices

PREVIOUS=Path('artifacts/t1_round2/T1-ROUND2-20260928-v1')


def build(lane,cfg,future):
    name='final_model.pkl' if future else 'report_model.pkl'
    with (PREVIOUS/'n1stack'/name).open('rb') as f:stack=pickle.load(f)
    with (PREVIOUS/'n2composition'/name).open('rb') as f:composition=pickle.load(f)
    return {'lane':lane,'cfg':cfg,'future':future,'stack':stack,'composition':composition}


def components(m,raw,types,legacy):
    density,dd=predict_old(m['stack']['density'],raw,types,legacy)
    mass,_=predict_old(m['stack']['mass'],raw,types,legacy)
    d=np.asarray(dd['donor_indices']);c=mixture_donors(types,m['composition']['steps'])
    np.testing.assert_array_equal(np.asarray(types)[d],types)
    return mass,d,c,density


def predict(m,raw,types,legacy):
    mass,d,c,density=components(m,raw,types,legacy);types=np.asarray(types);lane=m['lane'];details={}
    if lane=='r1compose':
        donor=d[c];out=mass[donor];labels=types[donor]
        details.update(donor_indices=donor,composition_indices=c,density_indices=d)
    elif lane=='r2joint':
        old=m['stack']['density'];z=old['svd'].transform(raw);weights=np.ones(len(raw))
        for t,g in old['groups'].items():
            ix=np.flatnonzero(types==t)
            if not len(ix):continue
            logits=g['classifier'].decision_function(g['scaler'].transform(z[ix]));logits-=np.median(logits)
            weights[ix]=np.exp(np.clip(logits,-old['cfg']['n1']['weight_log_cap'],old['cfg']['n1']['weight_log_cap']))
        donor=joint_donors(types,weights,c);out=mass[donor];labels=types[donor]
        np.testing.assert_array_equal(labels,types[c])
        details.update(donor_indices=donor,composition_indices=c,density_weights=weights,type_counts_equal_r1=True)
    elif lane=='r3mix':
        a=mass[d];b=density[c];tb=types[c];cfg=m['cfg']['three']
        sides,rows=mixture_indices(types,tb,cfg['mixture_fraction_A'],cfg['mixture_seed'])
        if np.array_equal(a,b) and np.array_equal(types,tb):rows=np.arange(len(a))
        out=np.empty_like(a);labels=np.empty_like(types);effective=np.empty(len(raw),int)
        for side,pool,ptypes,pdonors in [(0,a,types,d),(1,b,tb,d[c])]:
            ix=sides==side;out[ix]=pool[rows[ix]];labels[ix]=ptypes[rows[ix]];effective[ix]=pdonors[rows[ix]]
        details.update(donor_indices=effective,parent_model=sides,parent_row_indices=rows,parent_A_count=int((sides==0).sum()),parent_B_count=int((sides==1).sum()))
    else:raise ValueError(lane)
    details.update(predicted_types=labels,predicted_counts={t:int(np.sum(labels==t)) for t in sorted(set(labels))},unique_source_rows=len(np.unique(details['donor_indices'])))
    return np.asarray(out,np.float32),details
