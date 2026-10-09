"""Frozen T1 v0051 carrier recovery. No hyperparameter selection or scoring."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[k]='8'
import sys, json, hashlib, pickle, gc, time, platform
from pathlib import Path
import numpy as np, anndata as ad, scipy, scipy.sparse as sp, sklearn
from sklearn.preprocessing import StandardScaler
from scipy.spatial import cKDTree
ROOT=Path(os.environ.get('T1_RECOVERY_ROOT', 't1_recovery_run'))
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
from scripts.t1_temporal_model import select_indices_by_shares, _masked_means
from scripts.t1_five.models import fit, predict, baseline
from scripts.t1_round2.ops import abundance_step,mixture_donors
from scripts.t1_three.ops import joint_donors,mixture_indices
from scripts.t1_seven.ops import shrunk_cov,gaussian_map
CH=ROOT/'work/repro51/chain'; CH.mkdir(parents=True,exist_ok=True)
T=time.time()
expected={}
for r in ['t1_five_20260927','t1_round2_20260928','t1_three_20260929']:
    for d in json.loads((REPO/'reports'/r/'VALIDATION.json').read_text())['routes']:
        if 'version' in d and 'expression_sha256' in d:expected[d['version']]=d['expression_sha256']
manifest={'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'threads':8},'inputs':{},'ancestors':{}}
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def put(name,x,labels=None,detail=None):
    x=np.asarray(x,dtype=np.float32)
    np.save(CH/(name+'.npy'),x)
    h=hashlib.sha256()
    for lo in range(0,len(x),128):h.update(np.ascontiguousarray(x[lo:lo+128]).tobytes())
    d={'shape':list(x.shape),'expression_sha256':h.hexdigest(),'elapsed_s':round(time.time()-T,1)}
    if name in expected:
        d.update(reference_expression_sha256=expected[name],reference_match=h.hexdigest()==expected[name])
    if labels is not None:np.save(CH/(name+'_donor_types.npy'),np.asarray(labels,dtype=str))
    if detail is not None:np.savez_compressed(CH/(name+'_operators.npz'),**detail)
    manifest['ancestors'][name]=d
    (CH/'CHAIN.json').write_text(json.dumps(manifest,indent=2))
    print(name,d,flush=True)
    if name in expected and h.hexdigest()!=expected[name]:raise RuntimeError('Frozen reconstruction diverged at '+name)
def load(name):return np.load(CH/(name+'.npy'),mmap_mode='r')

data=[];labels=[];means=[]
for name,want in [('E8.5_RNA','8eab2d0ccaa89f92861b09816b76b6a731b8ed6b5995e4af196d9ed8ff76e504'),('E9.5_RNA','0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361')]:
    p=ROOT/'data'/f'{name}.h5ad';h=sha(p);assert h==want
    manifest['inputs'][name]={'path':str(p),'sha256':h}
    obj=ad.read_h5ad(p);lab=obj.obs.celltype.astype(str).to_numpy(); labels.append(lab)
    genes=list(obj.var_names);means.append(_masked_means(obj.X,lab)[0])
    out=CH/(name+'.npy')
    if not out.exists():
        mm=np.lib.format.open_memmap(out,mode='w+',dtype=np.float32,shape=obj.shape)
        for lo in range(0,len(obj),256):
            z=obj.X[lo:lo+256];mm[lo:lo+256]=z.toarray() if sp.issparse(z) else z
        mm.flush();del mm
    if name=='E9.5_RNA':names=np.asarray(obj.obs_names,dtype=str)
    del obj;gc.collect();data.append(np.load(out,mmap_mode='r'))
    print('input ready',name,flush=True)
(ROOT/'data/T1__val.genes.txt').write_text('\n'.join(genes)+'\n')
a,b=data;ta,tb=labels
typ,cnt=np.unique(tb,return_counts=True);shares=dict(zip(typ,cnt/len(tb)))
rows=select_indices_by_shares(tb,shares,n_cells=5118,seed=20260822)
np.save(CH/'recipient95.npy',rows);np.save(CH/'recipient95_names.npy',names[rows]);types=tb[rows];raw=b[rows]
v4=raw.copy()
for t in sorted(set(types)):
    if t in means[0]:v4[types==t]+=means[1][t]-means[0][t]
np.clip(v4,0,None,out=v4);put('v0004',v4,types)
legacy=baseline(a,ta,b,tb,raw,types,v4);put('v0023',legacy,types);del v4;gc.collect()
cfg=json.loads((REPO/'configs/t1_five/design_20260927.json').read_text())
dp=CH/'density.pkl'
if dp.exists():density=pickle.loads(dp.read_bytes())
else:
    density=fit(a,ta,b,tb,'n1density',cfg,True);dp.write_bytes(pickle.dumps(density,protocol=5))
den,dd=predict(density,raw,types,legacy);d=np.asarray(dd['donor_indices']);put('v0024',den,types,{'donors':d});del den;gc.collect()
mp=CH/'mass.pkl'
if mp.exists():mass_model=pickle.loads(mp.read_bytes())
else:
    mass_model=fit(a,ta,b,tb,'o1mass',cfg,True);mp.write_bytes(pickle.dumps(mass_model,protocol=5))
mass,_=predict(mass_model,raw,types,legacy);put('v0027',mass,types);del mass_model;gc.collect()
cfg2=json.loads((REPO/'configs/t1_round2/design_20260928.json').read_text())
alltypes=sorted(set(ta)|set(tb));ca=np.array([sum(ta==t) for t in alltypes]);cb=np.array([sum(tb==t) for t in alltypes]);p=cfg2['round2']['composition']
step=abundance_step(ca,cb,p['pseudocount'],p['strength'],p['ratio_cap']);c=mixture_donors(types,dict(zip(alltypes,step)))
put('v0029',mass[d],types,{'donors':d});den=load('v0024');put('v0030',den[c],types[c],{'composition':c});del den
z=density['svd'].transform(raw);weights=np.ones(len(raw))
for t,g in density['groups'].items():
    ix=np.flatnonzero(types==t)
    logits=g['classifier'].decision_function(g['scaler'].transform(z[ix]));logits-=np.median(logits)
    weights[ix]=np.exp(np.clip(logits,-cfg['n1']['weight_log_cap'],cfg['n1']['weight_log_cap']))
joint=joint_donors(types,weights,c);put('v0035',mass[joint],types[joint],{'donors':joint})
cfg3=json.loads((REPO/'configs/t1_three/design_20260929.json').read_text())['three']
side,rr=mixture_indices(types,types[c],cfg3['mixture_fraction_A'],cfg3['mixture_seed'])
v36=np.empty_like(raw);t36=np.empty(len(raw),dtype=types.dtype);x29=load('v0029');x30=load('v0030')
for s,pool,pt in [(0,x29,types),(1,x30,types[c])]:
    ix=side==s;v36[ix]=pool[rr[ix]];t36[ix]=pt[rr[ix]]
put('v0036',v36,t36,{'sides':side,'rows':rr});del v36,x29,x30;gc.collect()
cfg7=json.loads((REPO/'configs/t1_seven/design_20260930.json').read_text())['seven']
za=density['svd'].transform(a);zb=density['svd'].transform(b);donor=joint.copy();dim=cfg7['latent_dimensions']
for t in density['common']:
    aa=za[ta==t,:dim];bb=zb[tb==t,:dim];sc=StandardScaler().fit(np.vstack([aa,bb]));aa=sc.transform(aa);bb=sc.transform(bb)
    ca=shrunk_cov(aa,cfg7['cov_shrink']);cb=shrunk_cov(bb,cfg7['cov_shrink']);mapping=gaussian_map(ca,cb)
    pool=np.flatnonzero(types==t);slots=np.flatnonzero(types[donor]==t)
    allq=sc.transform(z[pool,:dim]);q=sc.transform(z[donor[slots],:dim]);center=bb.mean(0)
    velocity=bb.mean(0)-aa.mean(0)+(q-center)@(mapping-np.eye(dim)).T
    target=q+cfg7['cov_strength']*velocity;_,chosen=cKDTree(allq).query(target,k=1);donor[slots]=pool[chosen]
put('v0038',mass[donor],types[donor],{'donors':donor});del mass,legacy,raw;gc.collect()
# Historical build_t1_finals.py stratifies on inherited obs celltypes, not synthetic donor types.
side,rr=mixture_indices(types,types,0.7,20260921);v36=load('v0036');v38=load('v0038');out=np.empty_like(v36);labs=np.empty(len(types),dtype=types.dtype);t38=types[donor]
for s,pool,pt in [(0,v36,t36),(1,v38,t38)]:
    ix=side==s;out[ix]=pool[rr[ix]];labs[ix]=pt[rr[ix]]
put('v0051',out,labs,{'sides':side,'rows':rr})
manifest['v0051_prefix_reference']='541d0aa6';manifest['v0051_prefix_match']=manifest['ancestors']['v0051']['expression_sha256'].startswith('541d0aa6')
(CH/'CHAIN.json').write_text(json.dumps(manifest,indent=2))
print('RECOVERY COMPLETE',manifest['v0051_prefix_match'],flush=True)
