import warnings
import numpy as np
from scipy.special import logit
from sklearn.linear_model import Ridge,LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from scripts.t3_next.five import Hurdle
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.repair_ops import decode_rate
from .ops import occupancy_decode


def old_hurdle(saved):
    model=Hurdle();model.encoder=saved['encoder'];model.positive=saved['positive'];return model


def hurdle_effect(model,c):
    a=c.x[c.rows][:,[c.gi]];z=c.coords[c.rows]
    factual,_=model.predict(a,z,c.plabels);cf,_=model.predict(np.zeros_like(a),z,c.plabels)
    return cf-factual


class LogisticHurdle:
    def fit(self,a,z,types,y,cfg):
        self.old=Hurdle().fit(a,z,types,y,100.)
        features=self.old.encoder.features(a,z,types);self.logistic=[]
        for j in range(y.shape[1]):
            binary=(y[:,j]>0).astype(int)
            if np.unique(binary).size==1:self.logistic.append(float(binary[0]));continue
            model=LogisticRegression(C=cfg['logistic_C'],solver='liblinear',max_iter=cfg['logistic_max_iter'],tol=cfg['logistic_tol'],random_state=20260927)
            with warnings.catch_warnings():
                warnings.simplefilter('error',ConvergenceWarning);model.fit(features,binary)
            self.logistic.append(model)
        return self
    def components(self,a,z,types):
        f=self.old.encoder.features(a,z,types)
        p=np.column_stack([np.full(len(f),m) if isinstance(m,float) else m.predict_proba(f)[:,1] for m in self.logistic])
        oldp=np.clip(self.old.encoder.model.predict(f),0,1)
        pos=np.column_stack([np.full(len(f),m) if isinstance(m,float) else np.maximum(m.predict(f),0) for m in self.old.positive])
        return p,pos,oldp
    def predict(self,a,z,types):
        p,pos,_=self.components(a,z,types);return p*pos,p


class Nuisance:
    def fit(self,z,types,y,alpha):
        self.scaler=StandardScaler().fit(np.column_stack([z,z*z]));self.types=sorted(set(types))
        self.model=Ridge(alpha).fit(self.features(z,types),y);return self
    def features(self,z,types):
        return np.column_stack([self.scaler.transform(np.column_stack([z,z*z])),np.column_stack([types==t for t in self.types])])
    def predict(self,z,types):return self.model.predict(self.features(z,types))


def orth_fit(x,gi,z,types,blocks,cfg,seed):
    cols=np.flatnonzero(np.arange(x.shape[1])!=gi);a=x[:,gi];y=x[:,cols];both=np.column_stack([a,y]);res=np.zeros_like(both,dtype=float)
    for fold in np.unique(blocks):
        train=blocks!=fold;test=~train
        n=Nuisance().fit(z[train],types[train],both[train],cfg['context_ridge'])
        res[test]=both[test]-n.predict(z[test],types[test])
    ra=res[:,0];ry=res[:,1:];alpha=cfg['orthogonal_slope_ridge']
    def slopes(activity):
        global_b=(activity[:,None]*ry).sum(0)/(np.sum(activity**2)+alpha)
        group={}
        for t in set(types):
            ix=types==t
            group[t]=((activity[ix,None]*ry[ix]).sum(0)+alpha*global_b)/(np.sum(activity[ix]**2)+alpha)
        return global_b,group
    beta,groups=slopes(ra);permuted=ra.copy();rng=np.random.default_rng(seed)
    for t in set(types):
        ix=np.flatnonzero(types==t);permuted[ix]=ra[rng.permutation(ix)]
    null_beta,null_groups=slopes(permuted)
    nuisance=Nuisance().fit(z,types,both,cfg['context_ridge'])
    return {'nuisance':nuisance,'beta':beta,'groups':groups,'null_beta':null_beta,'null_groups':null_groups,'cols':cols,'residual_activity_variance':float(np.var(ra))}


def orth_prediction(m,a,z,types,null=False):
    nuisance=m['nuisance'].predict(z,types)
    key='null_groups' if null else 'groups';fallback=m['null_beta' if null else 'beta']
    slopes=np.stack([m[key].get(t,fallback) for t in types])
    return nuisance[:,1:]+(a-nuisance[:,0])[:,None]*slopes,nuisance[:,1:]


def predict_saved(m,c):
    lane=m['lane'];out=c.base.copy();cfg=c.cfg['round2'];cols=np.flatnonzero(np.arange(500)!=c.gi)
    if lane=='n1stack':
        h=old_hurdle(m['hurdle']);out[:,cols]=bounded_add(c.base[:,cols],hurdle_effect(h,c),.25)
        out=decode_rate(out,m['rate'])
    elif lane=='n2orth':
        ort=m['model'];b=np.stack([ort['groups'].get(t,ort['beta']) for t in c.plabels]);delta=-c.x[c.rows,c.gi,None]*b
        out[:,cols]=bounded_add(c.base[:,cols],delta,cfg['response_strength'])
    elif lane=='o1logit':
        out[:,cols]=bounded_add(c.base[:,cols],hurdle_effect(m['model'],c),cfg['response_strength'])
    elif lane=='n3occup':out=occupancy_decode(c.base,m['target_params'],c.plabels,cfg['sample_occupancy_strength'])
    elif lane=='o2geneshrink':out=decode_rate(c.base,m['target_rate'])
    else:raise ValueError(lane)
    out[:,c.gi]=0
    return np.asarray(out,dtype=np.float32)
