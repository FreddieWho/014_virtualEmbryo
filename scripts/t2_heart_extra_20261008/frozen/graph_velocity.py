import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ.setdefault(k,'2')
import sys,json,pickle
from pathlib import Path
import numpy as np
from scipy.linalg import solve
import flow
R=flow.ROOT

def graph_prior(kind):
 d=json.loads(flow.GO.read_text());genes=flow.PANEL.read_text().splitlines();assert d['genes']==genes
 w=np.zeros((len(genes),len(d['modules'])),float);gi={g:i for i,g in enumerate(genes)}
 for j,gs in enumerate(d['modules'].values()):
  for g in gs:w[gi[g],j]=1/len(gs)
 adj=w@w.T;norm=np.sqrt(np.diag(adj));adj=adj/np.maximum(norm[:,None]*norm[None,:],1e-12);np.fill_diagonal(adj,0)
 if kind=='perm':
  ix=np.random.default_rng(flow.SEED).permutation(len(genes));adj=adj[np.ix_(ix,ix)]
 return adj

def fit(e,l,kind):
 xe,xl=flow.dense(e.X),flow.dense(l.X);te=e.obs.celltype.astype(str).to_numpy();tl=l.obs.celltype.astype(str).to_numpy();prior=graph_prior(kind);models={};audit={}
 for s in sorted(set(te)&set(tl)):
  a,b=xe[te==s].astype(float),xl[tl==s].astype(float)
  if min(len(a),len(b))<16:continue
  sd=np.sqrt((a.var(0)+b.var(0))/2+.01)
  med=np.median(b,0)-np.median(a,0);effect=med/sd
  z=np.vstack([(a-a.mean(0))/sd,(b-b.mean(0))/sd]);corr=z.T@z/len(z);diag=np.sqrt(np.diag(corr));corr/=np.maximum(diag[:,None]*diag[None,:],1e-12)
  adj=prior*corr;nn=np.argsort(-np.abs(adj),axis=1)[:,:10];keep=np.zeros_like(adj,bool);np.put_along_axis(keep,nn,True,axis=1);keep|=keep.T;adj*=keep;np.fill_diagonal(adj,0)
  deg=np.abs(adj).sum(1);active=deg>1e-12;ds=np.sqrt(np.maximum(deg,1e-12));lap=np.diag(active.astype(float))-adj/(ds[:,None]*ds[None,:])
  noise=np.pi/2*(1/len(a)+1/len(b));signal=max(float(np.mean(effect**2))-noise,1e-12);alpha=min(1.,noise/signal)
  posterior=solve(np.eye(len(sd))+alpha*lap,effect,assume_a='pos')*sd
  models[s]={'delta':posterior,'raw_delta':med,'alpha':alpha,'laplacian':lap,'sd':sd}
  audit[s]={'early_cells':len(a),'late_cells':len(b),'alpha':alpha,'estimated_noise':noise,'estimated_signal':signal,'active_genes':int(active.sum()),'edges':int(np.count_nonzero(adj)//2),'delta_norm':float(np.linalg.norm(med)),'posterior_norm':float(np.linalg.norm(posterior)),'posterior_difference_norm':float(np.linalg.norm(posterior-med))}
 return {'kind':kind,'states':models,'topology_sha':flow.sha(flow.GO)},audit

def predict(a,m):
 x=flow.dense(a.X);y=x.copy();t=a.obs.celltype.astype(str).to_numpy();lib=np.expm1(x.astype(float)).sum(1)
 for s,v in m['states'].items():
  ix=np.flatnonzero(t==s);y[ix]=flow.normalize(x[ix]+.9*v['delta'],lib[ix])
 return y

def build(split):
 d=R/split;en,ln=('E8.25_late','E8.75') if split=='dev' else ('E8.75','E9.5');e,l=flow.load(en),flow.load(ln)
 if split=='final':
  import anndata as ad
  carrier=ad.read_h5ad(d/'copy.h5ad')
 else:carrier=l
 for kind in ['graph','perm']:
  m,a=fit(e,l,kind);p=d/(kind+'_model.pkl');p.write_bytes(pickle.dumps(m,protocol=5));flow.dump(d/(kind+'_fit_audit.json'),a)
  flow.save(carrier,predict(carrier,m),d/(kind+'.h5ad'),{'method':'signed_function_graph_posterior_'+kind,'source_stages':[en,ln],'topology_sha':flow.sha(flow.GO),'model_sha':flow.sha(p),'target_used':False,'code_sha':flow.sha(__file__)})
  print('DONE',split,kind,flush=True)
if __name__=='__main__':build(sys.argv[1])
