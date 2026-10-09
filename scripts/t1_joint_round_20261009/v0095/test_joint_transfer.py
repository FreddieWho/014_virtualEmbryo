"""Frozen cross-fit structural assay; no E10.5 data or candidate submission.

Known state-marginals are supplied by a released-stage heldout population.
The assay tests conditional joint reconstruction, not temporal forecasting.
"""
import os
os.environ.update({k:'1' for k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']})
import gc,hashlib,json,sys,time
from pathlib import Path
import h5py,numpy as np,anndata as ad
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'structural_assay';OUT.mkdir(exist_ok=True)
REC=Path(os.environ.get('T1_RECOVERY_ROOT', 't1_recovery_run'))
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from copula_restore import restore
from pair_diagnostics import uniform_pairs,pair_moments,compare_pair_moments
sys.path.insert(0,str(REPO/'third_party/veckit'))
from common.core_metrics import mmd_unbiased,energy_distance
sys.path.insert(0,str(REPO/'scripts/vework/t1ext'))
from label_means_const import COARSE
SEEDS=[20261009,20261010,20261011];N=512;GROUPS=['CM_V','CM_A','ENDO','EPI','MESO','NCC','SHF']
IEG={'Fos','Fosb','Jun','Junb','Jund','Egr1','Egr2','Egr3','Atf3','Ier2','Ier3','Ier5','Dusp1','Zfp36','Klf2','Klf4','Klf6','Nr4a1','Hspa1a','Hspa1b','Hspa8','Hsph1','Btg2','Cyr61','Ccn1','Socs3','Gadd45b','Ppp1r15a','Mt1','Mt2'}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def readstr(v):return np.array([x.decode() if isinstance(x,bytes) else str(x) for x in v])
def load_context():
 arrays=np.load(ROOT/'audit/mapping_arrays.npz');audit=json.loads((ROOT/'audit/MAPPING_AUDIT.json').read_text())
 with h5py.File(REC/'data/E9.5_RNA.h5ad','r') as f:
  ct=f['obs/celltype'];fine=readstr(ct['categories'][:])[ct['codes'][:]]
 X=np.load(REC/'work/repro51/chain/E9.5_RNA.npy',mmap_mode='r')
 assert X.shape==(17057,32285)
 markers=arrays['markers'];train=arrays['official_train'];hold=arrays['official_test']
 cm=np.asarray(X[:,markers],dtype=np.float32);mu=cm[train].mean(0);sd=cm[train].std(0)+1e-3
 coarse=arrays['official_labels'];src=ad.read_h5ad(ROOT/'audit/GSM5820434_panel_log1p.h5ad')
 have=src.var.in_external.to_numpy();genes=readstr(src.var_names)
 blocked=np.array([g.startswith(('Hba','Hbb','mt-')) or g in IEG or g=='Malat1' for g in genes])
 trust=have&~blocked
 eligible=(arrays['confidence']>=.8)&(arrays['source_nn_distance']<=audit['ood_threshold'])
 labels=arrays['predicted']
 em=(src.X[:,markers].toarray()-mu)/sd;cm=(cm-mu)/sd
 return X,fine,coarse,train,hold,src,em,cm,eligible,labels,trust

def draw_donors(context,states,donor_features,donor_states,eligible,seed):
 rng=np.random.default_rng(seed);chosen=np.full(len(context),-1,dtype=int);report={}
 for g in GROUPS:
  rows=np.flatnonzero(states==g);pool=np.flatnonzero((donor_states==g)&eligible)
  if len(pool)<50 or not len(rows):report[g]={'n_pool':len(pool),'n_recipient':len(rows),'fallback':True};continue
  k=min(5,len(pool));nn=NearestNeighbors(n_neighbors=k,n_jobs=1).fit(donor_features[pool]);ix=nn.kneighbors(context[rows],return_distance=False)
  pick=pool[ix[np.arange(len(rows)),rng.integers(k,size=len(rows))]];chosen[rows]=pick
  u,c=np.unique(pick,return_counts=True);q=c/c.sum();entropy=float(-np.sum(q*np.log(q)))
  report[g]={'n_pool':len(pool),'n_recipient':len(rows),'n_unique':len(u),'max_reuse':int(c.max()),'donor_entropy':entropy,'effective_donors':float(np.exp(entropy)),'fallback':False}
 return chosen,report

spec={'n_cells_per_half':N,'seeds':SEEDS,'blend':.5,'k_donors':5,'source_confidence_min':.8,'source_distance_max':20.951346729303403,
 'min_source_cells_per_group':50,'groups':GROUPS,'restore_states':'fine official donor celltype','blocked_genes':'current late-anchor Hb/mt/Malat1/IEG blacklist',
 'context':'unshuffled heldout A cells; emissions are within-fine-state gene-shuffled A; target is independent heldout B',
 'controls':['original_A','shuffled_A','official_train_donor','external_donor','gene_shuffled_external_donor'],
 'interpretation':'Conditional source joint-transfer assay with supplied state marginals; not a future prediction or leaderboard selector',
 'operator_sha256':sha(Path(__file__).resolve().parent/'copula_restore.py')}
(OUT/'DESIGN.json').write_text(json.dumps(spec,indent=2))
for seed in SEEDS:
 t0=time.time();folder=OUT/str(seed);folder.mkdir(exist_ok=True)
 X,fine,coarse,train,hold,src,em,cm,eligible,slabels,trust=load_context()
 rest,ai=train_test_split(hold,test_size=N,random_state=seed,stratify=fine[hold])
 _,bi=train_test_split(rest,test_size=N,random_state=seed+100,stratify=fine[rest])
 assert len(set(ai)&set(bi))==0 and len(set(train)&(set(ai)|set(bi)))==0
 np.savez_compressed(folder/'rows.npz',recipient=ai,target=bi,train=train)
 states=fine[ai];cs=coarse[ai];A=np.asarray(X[ai]).astype(np.float32);B=np.asarray(X[bi]).astype(np.float32)
 np.save(folder/'original_A.npy',A);np.save(folder/'target_B.npy',B)
 P=A.copy();rng=np.random.default_rng(seed)
 for state in sorted(set(states)):
  rr=np.flatnonzero(states==state)
  for j in range(P.shape[1]):P[rr,j]=P[rng.permutation(rr),j]
 np.save(folder/'shuffled_A.npy',P)
 external,er=draw_donors(cm[ai],cs,em,slabels,eligible,seed)
 ot_ok=np.zeros(len(X),bool);ot_ok[train]=True
 official,orr=draw_donors(cm[ai],cs,cm,coarse,ot_ok,seed)
 np.savez_compressed(folder/'donors.npz',external=external,official=official)
 reports={};del A,B,cm,em;gc.collect()
 for name,donors,data in [('external_donor',external,src.X),('official_train_donor',official,X)]:
  T=np.zeros_like(P);rows=np.flatnonzero(donors>=0)
  for start in range(0,P.shape[1],256):
   cols=np.arange(start,min(start+256,P.shape[1]));valid=cols[trust[cols]]
   if hasattr(data,'toarray'):block=data[donors[rows]][:,valid].toarray()
   else:block=np.asarray(data[np.ix_(donors[rows],valid)])
   T[np.ix_(rows,valid)]=block
  out,d=restore(P,T,states,blend=.5,block_size=256,seed=seed)
  np.save(folder/(name+'.npy'),out);reports[name]=d;del out;gc.collect()
  if name=='external_donor':
   out,d=restore(P,T,states,blend=.5,block_size=256,seed=seed,shuffle_template=True)
   np.save(folder/'gene_shuffled_external_donor.npy',out);reports['gene_shuffled_external_donor']=d;del out;gc.collect()
  del T;gc.collect()
 del src,X,P;gc.collect()
 # Evaluate each arm sequentially after releasing source and template matrices.
 B=np.load(folder/'target_B.npy');pairs=uniform_pairs(B.shape[1],seed=seed);bm=pair_moments(B,pairs)
 base=np.load(folder/'shuffled_A.npy',mmap_mode='r');pm=pair_moments(base,pairs)
 metrics={}
 for name in spec['controls']:
  a=np.load(folder/(name+'.npy'));am=pair_moments(a,pairs)
  with threadpool_limits(limits=1):
   mmd=mmd_unbiased(a,B,seed=seed);energy=energy_distance(a,B,seed=seed)
  metrics[name]={'mmd_u':mmd,'energy_distance':energy,'variogram':float(np.mean((am['moment']-bm['moment'])**2)),
   'pair_decomposition':compare_pair_moments(pm,am,bm),'mean_library':float(np.expm1(a).sum(1).mean()),
   'median_library':float(np.median(np.expm1(a).sum(1))),'mean_detected_genes':float((a>0).sum(1).mean())}
  del a;gc.collect()
 result={'seed':seed,'source_donor_reuse':er,'official_donor_reuse':orr,'operator_reports':reports,'metrics':metrics,'runtime_seconds':time.time()-t0}
 (folder/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 del B,base;gc.collect()
results=[json.loads((OUT/str(s)/'RESULT.json').read_text()) for s in SEEDS]
summary={'design':spec,'results':results,'script_sha256':sha(Path(__file__)),'source_audit_manifest_sha256':sha(ROOT/'audit/MANIFEST.json')}
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2));print('COMPLETE',flush=True)
