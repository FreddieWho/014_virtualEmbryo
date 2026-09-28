import numpy as np
from scripts.t3_next.five import Hurdle
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.repair_ops import decode_rate
from .ops import decompose,agree_rate,diffuse


def restore(saved):
    h=Hurdle();h.encoder=saved['encoder'];h.positive=saved['positive'];return h


def components(h,a,z,types):
    f=h.encoder.features(a,z,types);p=np.clip(h.encoder.model.predict(f),0,1)
    m=np.column_stack([np.full(len(f),v) if isinstance(v,float) else np.maximum(v.predict(f),0) for v in h.positive])
    return p,m


def responses(h,a,intervention,z,types):
    p1,m1=components(h,a,z,types);p0,m0=components(h,intervention,z,types)
    prob,intensity=decompose(p1,m1,p0,m0);delta=p0*m0-p1*m1
    np.testing.assert_allclose(prob+intensity,delta,rtol=1e-10,atol=1e-12)
    return delta,prob,intensity


def apply(lane,base,delta,prob,intensity,z,types,active,rate,cfg):
    h=np.asarray(bounded_add(base,delta,cfg['hurdle_strength']),np.float32);info={}
    if lane=='r1agree':
        r,mask=agree_rate(base,h,rate,cfg['agreement_source_strength'],cfg['effect_epsilon'])
        out=decode_rate(h,r);info['agreement_entries']=int(mask.sum())
    elif lane=='r2damp':
        d=cfg['probability_weight']*prob+cfg['positive_weight']*intensity
        out=bounded_add(base,d,cfg['hurdle_strength'])
        info.update(probability_norm=float(np.linalg.norm(prob)),positive_norm=float(np.linalg.norm(intensity)),cancellation_entries=int(np.sum(prob*intensity<0)))
    elif lane=='r3diffuse':
        d,groups=diffuse(delta,z,types,active,cfg['neighbors'],cfg['diffusion_strength'])
        out=bounded_add(base,d,cfg['hurdle_strength']);info['groups']=groups
        info['inactive_response_maxabs']=float(np.max(np.abs(d[~active]))) if (~active).any() else 0.
    else:raise ValueError(lane)
    return np.asarray(out,np.float32),info


def predict(m,c):
    h=restore(m['hurdle']);cols=m['cols'];a=c.x[c.rows][:,[c.gi]];z=c.coords[c.rows]
    d,p,i=responses(h,a,np.zeros_like(a),z,c.plabels)
    out=c.base.copy();out[:,cols],info=apply(m['lane'],c.base[:,cols],d,p,i,z,c.plabels,a[:,0]>0,m['rate'][cols],m['cfg'])
    out[:,c.gi]=0
    return out,info
