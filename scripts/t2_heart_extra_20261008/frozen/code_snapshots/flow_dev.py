"""Source-only heterogeneous temporal transport; no target import in fit/build."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: os.environ.setdefault(k,'3')
import argparse, hashlib, json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd, anndata as ad
from scipy import sparse
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
ROOT=Path(__file__).resolve().parent
DATA=Path('/workspace/shared/virtual_embryo_data')
GO=Path('/workspace/shared/t2_external_sources_20261008/go_topology/panel_gene_go_interpro.json')
PANEL=DATA/'T2__heart__val_extrap.genes.txt'
SEED=20261008

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
def dense(x): return x.toarray().astype(np.float32) if sparse.issparse(x) else np.asarray(x,dtype=np.float32)
def load(name):
 assert name in ['E8.25_late','E8.75','E9.5']
 a=ad.read_h5ad(DATA/(name+'.h5ad'));genes=PANEL.read_text().splitlines();a=a[:,genes].copy();a.X=dense(a.X);return a

def normalize(x,lib):
 x=np.expm1(np.maximum(x,0).astype(np.float64));return np.log1p(x*(lib[:,None]/np.maximum(x.sum(1,keepdims=True),1e-20))).astype(np.float32)

def features_fit(x,kind):
 # Whitening is intentionally absent: weak/noisy source PCs must not dominate.
 p=PCA(n_components=min(64,x.shape[1]),svd_solver='randomized',random_state=SEED).fit(x)
 z=p.transform(x); model={'pca':p,'kind':kind}
 if kind=='go':
  go=json.loads(GO.read_text());genes=PANEL.read_text().splitlines();idx={g:i for i,g in enumerate(genes)}
  unique=sorted(set(tuple(sorted(gs)) for gs in go['modules'].values()))
  w=np.zeros((len(genes),len(unique)),dtype=np.float32)
  for j,gs in enumerate(unique):
   for g in gs:w[idx[g],j]=1/np.sqrt(len(gs))
  mod=x@w; q=PCA(n_components=min(32,mod.shape[1]),svd_solver='randomized',random_state=SEED).fit(mod)
  gz=q.transform(mod);ps=np.sqrt(np.mean(z[:,:32]**2));gs=np.sqrt(np.mean(gz**2))
  model.update(w=w,go_pca=q,pca_scale=ps,go_scale=gs)
  z=np.column_stack([z[:,:32]/ps,gz/gs])
 return z.astype(np.float64),model

def features(x,m):
 z=m['pca'].transform(x)
 if m['kind']=='go':z=np.column_stack([z[:,:32]/m['pca_scale'],m['go_pca'].transform(x@m['w'])/m['go_scale']])
 return z.astype(np.float64)

def cluster(x,z,k):
 km=KMeans(n_clusters=k,n_init=5,random_state=SEED,algorithm='lloyd').fit(z)
 labels=km.labels_; counts=np.bincount(labels,minlength=k).astype(float)
 means=np.stack([x[labels==j].mean(0,dtype=np.float64) for j in range(k)])
 return km.cluster_centers_,means,counts/counts.sum()

def coupling(e,l,pe,pl):
 cost=cdist(e,l,'sqeuclidean');eps=max(float(np.median(np.min(cost,axis=0))),1e-6)
 # Balanced OT within a source-established type, not spatial coordinate matching.
 k=np.exp(-cost/eps)+1e-100;u=np.ones(len(e));v=np.ones(len(l))
 for _ in range(500):
  u=pe/(k@v+1e-100);v=pl/(k.T@u+1e-100)
 plan=u[:,None]*k*v[None,:]
 fwd=plan/(plan.sum(1,keepdims=True)+1e-100)
 bwd=plan.T/(plan.sum(0)[:,None]+1e-100)
 recon=bwd@fwd@l
 within=cdist(l,l,'sqeuclidean');np.fill_diagonal(within,np.inf)
 spacing=np.min(within,axis=1)
 cycle=np.sum((recon-l)**2,axis=1)
 confidence=spacing/(spacing+cycle+1e-12)
 return bwd,confidence,{'entropy_epsilon':eps,'max_row_mass_error':float(np.max(np.abs(plan.sum(1)-pe))), 'cycle_error':cycle.tolist(),'within_spacing':spacing.tolist(),'confidence':confidence.tolist()}

def fit(early,late,kind):
 xe,xl=dense(early.X),dense(late.X);te=early.obs.celltype.astype(str).to_numpy();tl=late.obs.celltype.astype(str).to_numpy()
 shared=sorted(set(te)&set(tl));pool=np.vstack([xe,xl]);z,f=features_fit(pool,kind);ze,zl=z[:len(xe)],z[len(xe):]
 model={'features':f,'states':{},'kind':kind,'panel_sha':sha(PANEL),'topology_sha':sha(GO) if kind=='go' else None}
 sizes={s:np.sqrt(min(np.sum(te==s),np.sum(tl==s))) for s in shared};total=sum(sizes.values())
 audit={}
 for s in shared:
  ie=np.flatnonzero(te==s);il=np.flatnonzero(tl==s)
  if min(len(ie),len(il))<16:continue
  k=max(2,min(int(round(128*sizes[s]/total)),len(ie)//8,len(il)//8))
  ce,me,pe=cluster(xe[ie],ze[ie],k);cl,ml,pl=cluster(xl[il],zl[il],k)
  b,conf,info=coupling(ce,cl,pe,pl)
  # Center heterogeneous transport around the robust incumbent drift, so no
  # new uncontrolled global mean or whole-state remapping is introduced.
  vel=ml-b@me
  med=np.median(xl[il],axis=0)-np.median(xe[ie],axis=0)
  residual=vel-np.sum(pl[:,None]*vel,axis=0)
  signal=np.linalg.norm(med)
  hetero=np.sqrt(np.sum(pl*np.sum(residual**2,axis=1)))
  reliability=signal/(signal+hetero+1e-12)
  residual*=conf[:,None]*reliability
  residual-=np.sum(pl[:,None]*residual,axis=0)
  model['states'][s]={'centers':cl,'median_delta':med,'residual_velocity':residual,'mass':pl,'k':k}
  audit[s]={'early_cells':len(ie),'late_cells':len(il),'microstates':k,'signal_norm':float(signal),'heterogeneity_norm':float(hetero),'signal_reliability':float(reliability),**info}
 return model,audit

def predict(a,model,horizon_ratio,mode='flow'):
 x=dense(a.X);out=x.copy();types=a.obs.celltype.astype(str).to_numpy();z=features(x,model['features']);lib=np.expm1(x.astype(float)).sum(1)
 for s,m in model['states'].items():
  ix=np.flatnonzero(types==s)
  if not len(ix):continue
  delta=.9*m['median_delta'][None,:]
  if mode=='flow':
   d=cdist(z[ix],m['centers'],'sqeuclidean');nn=np.argsort(d,axis=1)[:,:min(8,len(m['centers']))];dist=np.take_along_axis(d,nn,axis=1)
   bw=np.maximum(np.median(dist,axis=1,keepdims=True),1e-12)
   weights=np.exp(-(dist-dist[:,:1])/bw);weights/=weights.sum(1,keepdims=True)
   delta=delta+horizon_ratio*np.sum(weights[:,:,None]*m['residual_velocity'][nn],axis=1)
  y=x[ix]+delta
  out[ix]=normalize(y,lib[ix])
 return out

def save(a,x,p,meta):
 b=a.copy();b.X=x;b.uns['ve_contract']={'schema':'ve.contract.v1','normalization':'log_normalized'};b.uns['t2_flow_provenance']=json.dumps(meta,sort_keys=True)
 b.write_h5ad(p);return {'path':str(p),'sha256':sha(p),'shape':list(b.shape)}

def build(split):
 out=ROOT/split;out.mkdir(exist_ok=True)
 early_name,late_name,ratio=('E8.25_late','E8.75',1.5) if split=='dev' else ('E8.75','E9.5',4/3)
 early,late=load(early_name),load(late_name)
 model_files={};artifacts={};inputhash={s:sha(DATA/(s+'.h5ad')) for s in [early_name,late_name]}
 if split=='final':
  sys.path.insert(0,'/workspace/shared/t3repo');from scripts.t2_pseudo_holdout import select_indices
  ix=select_indices(late.obs.celltype.astype(str).to_numpy(),n_cells=25179,seed=20260821)
  carrier=late[ix].copy();pd.DataFrame({'out_row':np.arange(len(ix)),'source_row':ix,'obs_name':carrier.obs_names}).to_csv(out/'source_row_ledger.tsv',sep='\t',index=False)
 else:carrier=late
 for kind in ['pca','go']:
  print('FIT',split,kind,flush=True);m,audit=fit(early,late,kind)
  mp=out/f'{kind}_model.pkl';mp.write_bytes(pickle.dumps(m,protocol=5));dump(out/f'{kind}_fit_audit.json',audit)
  model_files[kind]={'path':str(mp),'sha256':sha(mp)}
  meta={'method':kind+'_microstate_flow','early':early_name,'late':late_name,'input_hashes':inputhash,'horizon_ratio':ratio,'target_used':False,'model_sha256':sha(mp),'code_sha256':sha(__file__),'external_topology':m['topology_sha']}
  x=predict(carrier,m,ratio);artifacts[kind]=save(carrier,x,out/f'{kind}_flow.h5ad',meta)
  if kind=='pca':
   artifacts['incumbent_recipe']=save(carrier,predict(carrier,m,ratio,mode='median'),out/'incumbent_recipe.h5ad',{**meta,'method':'reconstructed_median09_library_recipe','not_exact_historical_parent':True})
   artifacts['copy']=save(carrier,dense(carrier.X),out/'copy.h5ad',{**meta,'method':'copy_last'})
 dump(out/'BUILD.json',{'models':model_files,'artifacts':artifacts,'input_hashes':inputhash,'code_sha256':sha(__file__)})
 print('DONE',split,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('split',choices=['dev','final']);args=p.parse_args();build(args.split)
