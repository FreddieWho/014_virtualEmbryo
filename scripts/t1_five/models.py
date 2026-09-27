"""Full-panel model fits and prediction. Report targets are not arguments."""
import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from .ops import empirical_transport,fit_mixture,apply_mixture,systematic_resample,rate_decode,borrow_rates,rate_factors


def library_ranks(x):
    order=np.argsort(-x.sum(1),kind='stable');rank=np.empty(len(x))
    rank[order]=(np.arange(len(x))+.5)/len(x)
    return rank


def baseline(a,ta,b,tb,recipient,types,fallback,min_n=30):
    out=fallback.copy();model={}
    for t in sorted(set(types)&set(ta)&set(tb)):
        ai=a[ta==t];bi=b[tb==t];ix=np.flatnonzero(types==t)
        if min(len(ai),len(bi))<min_n:continue
        lr=library_ranks(recipient[ix])
        for j in range(a.shape[1]):
            if np.mean(ai[:,j]==0)>.999 and np.mean(bi[:,j]==0)>.999:continue
            out[ix,j]=empirical_transport(ai[:,j].astype(float),bi[:,j].astype(float),recipient[ix,j].astype(float),lr)
        print('baseline type',t,'rows',len(ix),flush=True)
    return out


def fit(a,ta,b,tb,lane,cfg,future=False):
    common=sorted(t for t in set(ta)&set(tb) if min(np.sum(ta==t),np.sum(tb==t))>=cfg['min_type_cells'])
    model={'lane':lane,'common':common,'future':future,'cfg':cfg}
    if lane in ['n2param','o1mass']:
        groups={}
        for t in common:
            ai=a[ta==t];bi=b[tb==t];models={}
            for j in range(a.shape[1]):
                m=fit_mixture(ai[:,j],bi[:,j],lane,future,cfg['quantile_grid'])
                if m is not None:models[j]=m
            groups[t]=models
            print('fit',lane,'type',t,'genes',len(models),'future',future,flush=True)
        model['groups']=groups
    elif lane=='n1density':
        combined=sparse.vstack([sparse.csr_matrix(a),sparse.csr_matrix(b)],format='csr')
        svd=TruncatedSVD(cfg['embedding_components'],random_state=cfg['seed']);z=svd.fit_transform(combined);za=z[:len(a)];zb=z[len(a):];groups={}
        for t in common:
            x=np.vstack([za[ta==t],zb[tb==t]]);y=np.r_[np.zeros(np.sum(ta==t)),np.ones(np.sum(tb==t))]
            scaler=StandardScaler().fit(x);classifier=LogisticRegression(C=cfg['n1']['logistic_C'],class_weight='balanced',max_iter=1000,random_state=cfg['seed']).fit(scaler.transform(x),y)
            if np.max(classifier.n_iter_)>=1000:raise ValueError('density classifier not converged')
            groups[t]={'scaler':scaler,'classifier':classifier}
        model.update(svd=svd,groups=groups,explained_variance=float(svd.explained_variance_ratio_.sum()))
        print('fit density full-panel SVD +',len(groups),'classifiers',flush=True)
    else:
        early=np.stack([a[ta==t].mean(0) for t in common]);late=np.stack([b[tb==t].mean(0) for t in common])
        ma=np.stack([np.expm1(a[ta==t].astype(float)).mean(0) for t in common]);mb=np.stack([np.expm1(b[tb==t].astype(float)).mean(0) for t in common])
        floor=cfg['o2']['intensity_mean_floor'];rates=np.log((mb+floor)/(ma+floor));rates[(ma==0)&(mb==0)]=0
        if lane=='o2rate':
            reconstructed,factors=rate_factors(rates,cfg['o2']['response_rank'])
            model.update(rates=np.clip(reconstructed,-cfg['o2']['rate_bound'],cfg['o2']['rate_bound']),factors=factors,unprojected_rates=rates)
        elif lane=='n3borrow':
            model.update(rates=np.clip(rates,-cfg['n3']['rate_bound'],cfg['n3']['rate_bound']),centroids=late if future else early,source_centroids=early,source_log_means=early,target_log_means=late)
            loo=[]
            for i,t in enumerate(common):
                keep=np.arange(len(common))!=i
                rate,w=borrow_rates(early[i],early[keep],model['rates'][keep],cfg['n3']['neighbors'])
                x=a[ta==t];pred=rate_decode(x,rate*cfg['n3']['strength']).mean(0)
                avg=rate_decode(x,model['rates'][keep].mean(0)*cfg['n3']['strength']).mean(0)
                loo.append({'type':t,'donors':[common[j] for j in np.flatnonzero(keep)],'weights':w,'mse':float(np.mean((pred-late[i])**2)),'mean_rate_mse':float(np.mean((avg-late[i])**2)),'no_change_mse':float(np.mean((early[i]-late[i])**2)),'genes':a.shape[1]})
            model['leave_type_out']=loo
        else:raise ValueError(lane)
    return model


def predict(model,recipient,types,fallback,query_centroids=None):
    cfg=model['cfg'];lane=model['lane'];out=fallback.copy();details={}
    if lane in ['n2param','o1mass']:
        for t,group in model['groups'].items():
            ix=np.flatnonzero(types==t)
            if not len(ix):continue
            lr=library_ranks(recipient[ix])
            for j,m in group.items():out[ix,j]=apply_mixture(m,recipient[ix,j],lr)
            details[t]={'cells':len(ix),'genes':len(group)}
    elif lane=='n1density':
        z=model['svd'].transform(recipient);donors=np.arange(len(recipient))
        for t,m in model['groups'].items():
            ix=np.flatnonzero(types==t)
            if not len(ix):continue
            logw=m['classifier'].decision_function(m['scaler'].transform(z[ix]));logw=logw-np.median(logw)
            w=np.exp(np.clip(logw,-cfg['n1']['weight_log_cap'],cfg['n1']['weight_log_cap']))
            ess=float(w.sum()**2/np.sum(w*w))
            if ess<len(ix)*cfg['n1']['minimum_ess_fraction']:raise ValueError('density ESS below frozen gate')
            chosen=ix[systematic_resample(w)];out[ix]=fallback[chosen];donors[ix]=chosen
            details[t]={'cells':len(ix),'ess':ess,'unique_donors':len(np.unique(chosen)),'duplicate_draws_not_replicates':int(len(ix)-len(np.unique(chosen)))}
        details['donor_indices']=donors
    elif lane=='n3borrow':
        if query_centroids is None:raise ValueError('source-only query type centroids required')
        for t in sorted(set(types)-set(model['common'])):
            ix=np.flatnonzero(types==t)
            rate,w=borrow_rates(query_centroids[t],model['centroids'],model['rates'],cfg['n3']['neighbors'])
            out[ix]=rate_decode(fallback[ix],cfg['n3']['strength']*rate)
            details[t]={'cells':len(ix),'donors':model['common'],'weights':w,'rate':rate}
    elif lane=='o2rate':
        for t,rate in zip(model['common'],model['rates']):
            ix=np.flatnonzero(types==t)
            if len(ix):out[ix]=rate_decode(recipient[ix],rate);details[t]={'cells':len(ix)}
    else:raise ValueError(lane)
    return np.asarray(out,dtype=np.float32),details
