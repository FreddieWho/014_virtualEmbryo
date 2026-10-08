"""Explicit detection/positive-expression observation model, after initial seven-KO run.
Avoids interpolating unconditional quantiles across zero/positive discontinuity.
Uses the same training-only identities, biological units, atlas, shrinkage and ridge.
"""
import numpy as np
from scipy.special import logsumexp
from crossko import CrossKO,closed
class CrossKOHurdle(CrossKO):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.positive_q=self.q.copy();self.q=np.arange(len(self.positive_q)+1) # final response coordinate stores detection fraction delta
 def positive_quantiles(self,x,fallback):
  q=np.zeros((self.G,len(self.positive_q)));valid=np.zeros(self.G,bool)
  for j in range(self.G):
   v=x[:,j];v=v[v>0]
   if len(v)>=3:q[j]=np.quantile(v,self.positive_q);valid[j]=True
   else:q[j]=fallback[j]
  return q,valid
 def summarize_response(self,control,ko):
  closed(control);closed(ko);cl=self.assign(control);kl=self.assign(ko);nc=np.bincount(cl,minlength=self.S);nk=np.bincount(kl,minlength=self.S);zero=np.zeros((self.G,len(self.positive_q)));cq,cv=self.positive_quantiles(control,zero);kq,kv=self.positive_quantiles(ko,cq);global_delta=kq-cq;global_detect=(ko>0).mean(0)-(control>0).mean(0);global_valid=cv&kv
  result=[];supports=[]
  for s in range(self.S):
   supported=nc[s]>=self.min_cells and nk[s]>=self.min_cells;supports.append(supported)
   if not supported:result.append(np.zeros((self.G,len(self.q))));continue
   a=control[cl==s];b=ko[kl==s];aq,av=self.positive_quantiles(a,cq);bq,bv=self.positive_quantiles(b,kq);lam=nk[s]/(nk[s]+50);d=lam*(bq-aq)+(1-lam)*global_delta;rate=lam*((b>0).mean(0)-(a>0).mean(0))+(1-lam)*global_detect;d[~global_valid]=0;rate[~global_valid]=0;result.append(np.c_[d,rate])
  comp=np.log((nk+.5)/(nk.sum()+.5*self.S))-np.log((nc+.5)/(nc.sum()+.5*self.S));comp-=comp.mean();return dict(delta=np.array(result),composition=comp,support=np.array(supports))
 def emit(self,carrier,response,mode='within',locked_zero=None):
  closed(carrier)
  if locked_zero is None and not np.any(response['delta']) and (mode=='within' or not np.any(response['composition'])):return carrier.copy(),np.arange(len(carrier))
  rng=np.random.default_rng(self.seed);lab=self.assign(carrier);ix=np.arange(len(carrier))
  if mode in ('composition','combined'):
   mass=np.bincount(lab,minlength=self.S).astype(float);mass*=np.exp(np.clip(response['composition'],-2,2));mass/=mass.sum();p=mass[lab]/np.maximum(np.bincount(lab,minlength=self.S)[lab],1);p/=p.sum();ix=rng.choice(ix,len(ix),replace=True,p=p)
  out=carrier[ix].copy().astype(float);labels=lab[ix];global_q,_=self.positive_quantiles(carrier,np.zeros((self.G,len(self.positive_q))))
  if mode in ('within','combined') and np.any(response['delta']):
   for s in range(self.S):
    rows=np.flatnonzero(labels==s)
    if not len(rows) or not response['support'][s]:continue
    local=out[rows].copy();baseq,_=self.positive_quantiles(local,global_q)
    for j in range(self.G):
     d=response['delta'][s,j]
     if not np.any(d):continue
     frac=np.clip((local[:,j]>0).mean()+d[-1],0,1);n=int(np.floor(len(rows)*frac+rng.random()));out[rows,j]=0
     if not n:continue
     order=np.argsort(local[:,j]+rng.uniform(0,1e-8,len(rows)),kind='stable')[-n:];tq=np.maximum.accumulate(np.maximum(baseq[j]+d[:-1],0));out[rows[order],j]=np.interp((np.arange(n)+.5)/n,self.positive_q,tq)
  if not np.isfinite(out).all():raise ValueError('Nonfinite response')
  with np.errstate(divide='ignore',invalid='ignore'):lc=out+np.log(-np.expm1(-out))
  if locked_zero is not None:lc[:,locked_zero]=-np.inf
  den=logsumexp(lc,axis=1)
  if not np.isfinite(den).all():raise ValueError('Empty output cell')
  out=np.log1p(10000*np.exp(lc-den[:,None])).astype('float32');closed(out);return out,ix
