"""Frozen-model composition and freshly fitted mixture/calibration estimators."""
import pickle
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.utils.class_weight import compute_sample_weight
from scripts.t1_five.models import predict as old_predict,fit as old_fit
from scripts.t1_five.ops import systematic_resample
from .ops import bounded_weights,abundance_step,mixture_donors,mass_shrink

OLD=Path('artifacts/t1_five/T1-FIVE-20260927-v1')


def load_old(lane,future):
    p=OLD/lane/('final_model.pkl' if future else 'report_model.pkl')
    with p.open('rb') as f:return pickle.load(f)


def fit(a,ta,b,tb,lane,cfg,future=False):
    density=load_old('n1density',future)
    m={'lane':lane,'cfg':cfg,'future':future,'density':density}
    if lane=='n1stack':m['mass']=load_old('o1mass',future)
    elif lane=='n2composition':
        labels=sorted(set(ta)|set(tb));p=cfg['round2']['composition']
        ca=np.array([np.sum(ta==t) for t in labels]);cb=np.array([np.sum(tb==t) for t in labels])
        steps=abundance_step(ca,cb,p['pseudocount'],p['strength'],p['ratio_cap'])
        m.update(steps=dict(zip(labels,steps)),counts_early=ca,counts_late=cb,labels=labels)
    elif lane in ['n3states','o1caldensity']:
        za=density['svd'].transform(a);zb=density['svd'].transform(b);groups={}
        for t in density['common']:
            x=np.vstack([za[ta==t],zb[tb==t]]);y=np.r_[np.zeros(np.sum(ta==t)),np.ones(np.sum(tb==t))].astype(int)
            if lane=='n3states':
                p=cfg['round2']['states'];scaler=StandardScaler().fit(x);z=scaler.transform(x)
                k=max(2,min(p['max_components'],len(x)//p['min_cells_per_component']))
                km=KMeans(n_clusters=k,n_init=p['n_init'],random_state=cfg['seed']).fit(z)
                ca=np.bincount(km.labels_[y==0],minlength=k);cb=np.bincount(km.labels_[y==1],minlength=k)
                step=abundance_step(ca,cb,p['pseudocount'],p['strength'],p['weight_cap'])
                groups[t]={'scaler':scaler,'kmeans':km,'step':step,'early_counts':ca,'late_counts':cb}
            else:
                p=cfg['round2']['calibration'];splits=StratifiedKFold(p['folds'],shuffle=True,random_state=cfg['seed'])
                oof=np.empty(len(x));folds=np.empty(len(x),int);fold_models=[]
                for f,(tr,te) in enumerate(splits.split(x,y)):
                    sc=StandardScaler().fit(x[tr]);cl=LogisticRegression(C=p['C'],class_weight='balanced',max_iter=1000,random_state=cfg['seed']).fit(sc.transform(x[tr]),y[tr])
                    if max(cl.n_iter_)>=1000:raise ValueError('OOF classifier convergence')
                    oof[te]=cl.decision_function(sc.transform(x[te]));folds[te]=f
                    fold_models.append({'train':tr,'test':te,'scaler':sc,'classifier':cl})
                def calibrate(mask):
                    return LogisticRegression(C=p['C'],max_iter=1000).fit(oof[mask,None],y[mask],sample_weight=compute_sample_weight('balanced',y[mask]))
                splitcal=calibrate(folds<3);test=folds>=3;prob=splitcal.predict_proba(oof[test,None])[:,1]
                from scipy.special import expit
                wt=compute_sample_weight('balanced',y[test]);before=float(np.average((expit(oof[test])-y[test])**2,weights=wt));after=float(np.average((prob-y[test])**2,weights=wt))
                groups[t]={'calibrator':calibrate(np.ones(len(x),bool)),'oof_logits':oof,'labels':y,'folds':folds,'fold_models':fold_models,'internal_diagnostic':{'uncalibrated_brier':before,'calibrated_brier':after,'rows':int(test.sum()),'scope':'supervised OOF; unsupervised SVD shared within fit region; not independent embryos'}}
            print('fit',lane,t,'rows',len(x),flush=True)
        m['groups']=groups
    elif lane=='o2shrinkmass':
        mass=old_fit(a,ta,b,tb,'o1mass',cfg,future);p=cfg['round2']['mass']
        for t,g in mass['groups'].items():
            ai=a[ta==t];bi=b[tb==t]
            for j,old in list(g.items()):g[j]=mass_shrink(ai[:,j],bi[:,j],old,future,p['quantile_density_bandwidth'],p['logit_prior'])
        m['mass']=mass
    else:raise ValueError(lane)
    return m


def predict(m,raw,types,legacy):
    lane=m['lane'];details={};donors=np.arange(len(raw));outtypes=np.asarray(types).copy()
    if lane in ['n1stack','n2composition']:
        density,dd=old_predict(m['density'],raw,types,legacy)
        if lane=='n1stack':
            mass,_=old_predict(m['mass'],raw,types,legacy)
            donors=np.asarray(dd['donor_indices']);out=mass[donors]
            details['operator']='mass rows indexed once by original density donors'
        else:
            donors=mixture_donors(types,m['steps']);out=density[donors];outtypes=np.asarray(types)[donors]
            details.update(predicted_counts={t:int(np.sum(outtypes==t)) for t in sorted(set(types))},recipient_counts={t:int(np.sum(np.asarray(types)==t)) for t in sorted(set(types))},steps=m['steps'],density_donors=np.asarray(dd['donor_indices']))
    elif lane=='o2shrinkmass':out,_=old_predict(m['mass'],raw,types,legacy)
    else:
        out=legacy.copy();z=m['density']['svd'].transform(raw)
        for t,g in m['groups'].items():
            ix=np.flatnonzero(np.asarray(types)==t)
            if not len(ix):continue
            if lane=='n3states':
                states=g['kmeans'].predict(g['scaler'].transform(z[ix]));logw=g['step'][states]
                w=np.exp(logw);details[t]={'state_counts':np.bincount(states,minlength=len(g['step']))}
            else:
                old=m['density']['groups'][t];logits=old['classifier'].decision_function(old['scaler'].transform(z[ix]))
                logw=g['calibrator'].decision_function(logits[:,None]);w=bounded_weights(logw,m['cfg']['round2']['calibration']['cap']);details[t]={'calibration_slope':float(g['calibrator'].coef_[0,0])}
            ess=float(w.sum()**2/(w@w))
            if ess<len(ix)*.5:raise ValueError('ESS below frozen 0.5 gate')
            chosen=ix[systematic_resample(w)];out[ix]=legacy[chosen];donors[ix]=chosen
            details[t].update(ess=ess,cells=len(ix),unique_donors=len(np.unique(chosen)))
    details.update(donor_indices=donors,predicted_types=outtypes)
    return np.asarray(out,np.float32),details
