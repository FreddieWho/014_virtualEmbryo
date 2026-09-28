import numpy as np
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from scripts.t3_next.five import Hurdle
from scripts.t3_next.routes_local import ConditionalModel
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.repair_ops import decode_rate


class SplineHurdle:
    def fit(self,a,z,t,y,cfg):
        self.encoder=ConditionalModel('linear',cfg['ridge_alpha']).fit(a,z,t,(y>0).astype(float))
        positive=a[a>0];self.knots=np.quantile(positive,cfg['spline_quantiles']) if len(positive) else np.zeros(3)
        self.scale=max(float(np.std(positive)),1e-6) if len(positive) else 1.
        f=self.features(a,z,t);self.prob=Ridge(cfg['ridge_alpha']).fit(f,(y>0).astype(float));self.positive=[]
        for j in range(y.shape[1]):
            present=y[:,j]>0
            self.positive.append(Ridge(cfg['ridge_alpha']).fit(f[present],y[present,j]) if present.sum()>=3 else float(y[present,j].mean()) if present.any() else 0.)
        return self
    def features(self,a,z,t):
        hinges=np.maximum(a-self.knots,0)/self.scale
        one=np.column_stack([t==v for v in self.encoder.types]).astype(float)
        return np.column_stack([self.encoder.features(a,z,t),hinges,(hinges[:,:,None]*one[:,None,:]).reshape(len(a),-1)])
    def predict(self,a,z,t):
        f=self.features(a,z,t);p=np.clip(self.prob.predict(f),0,1)
        m=np.column_stack([np.full(len(f),v) if np.isscalar(v) else np.maximum(v.predict(f),0) for v in self.positive])
        return p*m,p


class ResidualHurdle:
    def fit(self,h,a,z,t,y,ids,cfg):
        self.h=h;self.cfg=cfg;self.scaler=StandardScaler().fit(np.column_stack([a,z]));f=self.scaler.transform(np.column_stack([a,z]))
        residual=y-h.predict(a,z,t)[0];self.groups={}
        for typ in sorted(set(t)):
            ix=np.flatnonzero(t==typ);self.groups[typ]=(cKDTree(f[ix]),residual[ix],np.asarray(ids)[ix])
        return self
    def predict(self,a,z,t,ids=None):
        out=self.h.predict(a,z,t)[0];f=self.scaler.transform(np.column_stack([a,z]));ids=np.full(len(a),-1) if ids is None else np.asarray(ids)
        for typ in sorted(set(t)):
            if typ not in self.groups:continue
            tree,residual,trainids=self.groups[typ];ix=np.flatnonzero(t==typ)
            for start in range(0,len(ix),256):
                q=ix[start:start+256];k=min(self.cfg['neighbors']+1,len(trainids));_,nn=tree.query(f[q],k=k)
                nn=np.asarray(nn).reshape(len(q),k)
                # Exclude by immutable global row ID at both factual and counterfactual query.
                valid=trainids[nn]!=ids[q,None];valid&=np.cumsum(valid,axis=1)<=self.cfg['neighbors']
                correction=(residual[nn]*valid[:,:,None]).sum(1)/np.maximum(valid.sum(1),1)[:,None]
                out[q]+=self.cfg['residual_weight']*correction
        return np.maximum(out,0),None


def bootstrap_ids(t,ids,seed):
    rng=np.random.default_rng(seed)
    return np.concatenate([rng.choice(np.asarray(ids)[t==typ],size=int(np.sum(t==typ)),replace=True) for typ in sorted(set(t))])


def gate_medians(a,t):
    pos=a[:,0]>0;fallback=float(np.median(a[pos])) if pos.any() else 1.
    return {typ:float(np.median(a[(t==typ)&pos])) if np.any((t==typ)&pos) else fallback for typ in sorted(set(t))},fallback


def activity_gate(a,t,medians,fallback):
    return np.clip(a[:,0]/np.array([max(medians.get(typ,fallback),1e-8) for typ in t]),0,1)


def delta(model,a,b,z,t,ids):
    if isinstance(model,list):return np.mean([delta(m,a,b,z,t,ids) for m in model],axis=0)
    if isinstance(model,ResidualHurdle):return model.predict(b,z,t,ids)[0]-model.predict(a,z,t,ids)[0]
    return model.predict(b,z,t)[0]-model.predict(a,z,t)[0]


def predict(m,base,a,b,z,t,ids):
    cfg=m['cfg'];d=delta(m['model'],a,b,z,t,ids)
    out=bounded_add(base,d,cfg['hurdle_strength'])
    if m['lane']=='r1active':
        gate=activity_gate(a,t,m['medians'],m['fallback'])
        out=decode_rate(out,cfg['source_strength']*gate[:,None]*m['rate'])
    elif m['lane']=='r2gene':out=decode_rate(out,cfg['source_strength']*m['mask']*m['rate'])
    return np.asarray(out,np.float32)


def train_all(c,ids,h,rate,cols,folder):
    from .common import save_model,dump
    cfg=c.cfg;a=c.x[ids][:,[c.gi]];z=c.coords[ids];t=c.labels[ids];y=c.x[ids][:,cols]
    medians,fallback=gate_medians(a,t)
    average=delta(h,a,np.zeros_like(a),z,t,ids).mean(0)
    mask=(average*rate[cols]>0)&(np.abs(average)>cfg['effect_epsilon'])&(np.abs(rate[cols])>cfg['effect_epsilon'])
    models={lane:{'lane':lane,'cfg':cfg,'cols':cols,'rate':rate[cols],'model':h,'train_ids':ids} for lane in cfg['lanes']}
    models['r1active'].update(medians=medians,fallback=fallback);models['r2gene'].update(mask=mask,mean_response=average)
    bag=[];samples=[]
    for seed in cfg['bootstrap_seeds']:
        rows=bootstrap_ids(t,ids,seed);samples.append(rows)
        bag.append(Hurdle().fit(c.x[rows][:,[c.gi]],c.coords[rows],c.labels[rows],c.x[rows][:,cols],cfg['ridge_alpha']))
        print('bootstrap fitted',folder.name,seed,flush=True)
    models['r3bag'].update(model=bag,sampled_ids=samples)
    models['r4spline']['model']=SplineHurdle().fit(a,z,t,y,cfg)
    print('spline fitted',folder.name,flush=True)
    models['r5local']['model']=ResidualHurdle().fit(h,a,z,t,y,ids,cfg)
    folder.mkdir(parents=True,exist_ok=False)
    for lane,m in models.items():save_model(folder/(lane+'.pkl'),m)
    dump(folder/'TRAINING.json',{'train_cells':len(ids),'responses':len(cols),'bootstrap_models':len(bag),'consensus_genes':int(mask.sum()),'spline_knots':models['r4spline']['model'].knots,'neighbors':cfg['neighbors'],'hurdle':'refit on local training only' if len(ids)<len(c.x) else 'frozen scored full WT hurdle'})
    return models
