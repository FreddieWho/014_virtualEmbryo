"""Unseen-intervention interface. Fixed hyperparameters; all fitting excludes heldout KOs.
Fits untreated state atlas and donor-specific state marginal/occupancy responses.
Embedding must be supplied from independent ontology or untreated features.
No biological claims from synthetic tests. No gene-shape or response-scaled tuning.
"""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans
from scipy.stats import rankdata
from scipy.special import logsumexp
def closed(x):
 if not np.isfinite(x).all() or (x<0).any():raise ValueError("Invalid log expression")
 if not np.allclose(np.expm1(x.astype(float)).sum(1),10000,rtol=1e-5,atol=.02):raise ValueError("Expected closed panel log1p units")
class CrossKO:
 def __init__(self,states=32,quantiles=21,alpha=10,seed=241,min_cells=20):
  self.S=states;self.q=np.linspace(0,1,quantiles);self.alpha=alpha;self.seed=seed;self.min_cells=min_cells
 def fit_atlas(self,wt,features=None):
  closed(wt)
  self.features=np.arange(wt.shape[1]) if features is None else np.asarray(features)
  self.pca=PCA(n_components=min(12,len(self.features),len(wt)-1),random_state=self.seed).fit(wt[:,self.features]);z=self.pca.transform(wt[:,self.features]);self.km=MiniBatchKMeans(n_clusters=self.S,n_init=3,batch_size=1024,random_state=self.seed).fit(z);self.G=wt.shape[1];return self
 def assign(self,x):return self.km.predict(self.pca.transform(x[:,self.features]))
 def summarize_response(self,control,ko):
  closed(control);closed(ko)
  cl=self.assign(control);kl=self.assign(ko);nc=np.bincount(cl,minlength=self.S);nk=np.bincount(kl,minlength=self.S)
  global_q=np.quantile(ko,self.q,axis=0).T-np.quantile(control,self.q,axis=0).T
  d=[];support=[]
  for s in range(self.S):
   valid=nc[s]>=self.min_cells and nk[s]>=self.min_cells;support.append(valid)
   if valid:
    local=np.quantile(ko[kl==s],self.q,axis=0).T-np.quantile(control[cl==s],self.q,axis=0).T;lam=nk[s]/(nk[s]+50);d.append(lam*local+(1-lam)*global_q)
   else:d.append(np.zeros_like(global_q)) # explicit abstention in unsupported states
  # Smoothed compositional ratio, centered; do not equate cell counts with survival.
  comp=np.log((nk+.5)/(nk.sum()+.5*self.S))-np.log((nc+.5)/(nc.sum()+.5*self.S));comp-=comp.mean()
  return dict(delta=np.asarray(d),composition=comp,support=np.asarray(support))
 def fit_interventions(self,records,priors,heldout):
  # records: {gene,sample_unit,unit_kind,control,ko}; matching is required upstream.
  # unit_kind='embryo' only when metadata establishes biological replication; otherwise technical.
  self.training_genes=sorted({r['gene'] for r in records if r['gene']!=heldout});assert heldout not in self.training_genes
  if not self.training_genes:raise ValueError('No training interventions')
  missing=[g for g in self.training_genes if g not in priors]
  if missing:raise ValueError('Missing independent identity priors: '+str(missing))
  responses=[];supports=[]
  for gene in self.training_genes:
   # Equal declared-unit weighting; technical libraries are never called biological replicates.
   group=[self.summarize_response(r['control'],r['ko']) for r in records if r['gene']==gene]
   if len({r['sample_unit'] for r in records if r['gene']==gene})!=len(group):raise ValueError('One response record per declared sample unit required')
   responses.append(np.r_[np.mean([a['delta'] for a in group],axis=0).ravel(),np.mean([a['composition'] for a in group],axis=0)]);supports.append(np.mean([a['support'] for a in group],axis=0))
  self.priors={g:np.asarray(priors[g],float) for g in priors};A=np.stack([self.priors[g] for g in self.training_genes]);self.prior_mean=A.mean(0);self.prior_scale=np.maximum(A.std(0),.1);A=(A-self.prior_mean)/self.prior_scale
  self.R=np.asarray(responses);self.mean=self.R.mean(0);self.A=A;self.coef=np.linalg.solve(A@A.T+self.alpha*np.eye(len(A)),self.R-self.mean);self.supports=np.asarray(supports);return self
 def predict(self,gene,method='ridge'):
  if gene not in self.priors:raise ValueError('No independent identity prior for query '+gene)
  a=(self.priors[gene]-self.prior_mean)/self.prior_scale
  if method=='ridge':v=self.mean+(a@self.A.T)@self.coef
  elif method=='nearest':v=self.R[np.argmin(np.sum((self.A-a)**2,axis=1))]
  elif method=='mean':v=self.mean.copy() # identity-free control
  else:raise ValueError(method)
  n=self.S*self.G*len(self.q);return dict(delta=v[:n].reshape(self.S,self.G,len(self.q)),composition=v[n:],support=np.mean(self.supports,axis=0)>=.5)
 def emit(self,carrier,response,mode='within',locked_zero=None):
  closed(carrier)
  rng=np.random.default_rng(self.seed);lab=self.assign(carrier);ix=np.arange(len(carrier))
  if mode in ('composition','combined'):
   mass=np.bincount(lab,minlength=self.S).astype(float);mass*=np.exp(np.clip(response['composition'],-2,2));mass/=mass.sum();prob=mass[lab]/np.maximum(np.bincount(lab,minlength=self.S)[lab],1);prob/=prob.sum();ix=rng.choice(ix,len(ix),replace=True,p=prob)
  out=carrier[ix].copy().astype(float);labels=lab[ix]
  if mode in ('within','combined'):
   for s in range(self.S):
    rows=np.flatnonzero(labels==s)
    if not len(rows) or not response['support'][s]:continue
    for j in range(self.G):
     # Randomly order ties to allow zero-to-positive changes. Shared-cell copula is approximate,
     # not the empirical joint donor operator used in same-Mab ceiling experiments.
     v=out[rows,j];r=(rankdata(v+rng.uniform(0,1e-8,len(v)),method='ordinal')-.5)/len(v)
     out[rows,j]=np.maximum(v+np.interp(r,self.q,response['delta'][s,j]),0)
  if not np.isfinite(out).all():raise ValueError('Nonfinite response prediction')
  with np.errstate(divide='ignore',invalid='ignore'):
   logcounts=out+np.log(-np.expm1(-out))
  if locked_zero is not None:logcounts[:,locked_zero]=-np.inf
  logtot=logsumexp(logcounts,axis=1)
  if not np.isfinite(logtot).all():raise ValueError('Empty output cell')
  out=np.log1p(10000*np.exp(logcounts-logtot[:,None])).astype('float32');closed(out);return out,ix
