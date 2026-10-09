"""Build v0095 from one frozen reconstructed-v0092 and independent E9.5 donors.

The historical v0092 server score is not assigned to this reconstructed parent.
No portal operation or repository publication is performed.
"""
import os
os.environ.update({k:'1' for k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']})
import gc,hashlib,json,sys,time
from pathlib import Path
import anndata as ad,numpy as np,scipy.sparse as sp
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'candidate_v0095';OUT.mkdir(exist_ok=True)
REC=Path(os.environ.get('T1_RECOVERY_ROOT', 't1_recovery_run'))
BASE=REC/'submit/T1_val__A_ot_gen_v51_reconstructed.h5ad'
BASE_SHA='65270f9782e4fa7111a56cc35658aa67db5300b3de55fd54f77eafbe425577dd'
OP=Path(__file__).resolve().parent/'copula_restore.py'
OP_SHA='57293de8027a347b345471922001e0b2a847528cae0ca1416183d3c6c5efa55c'
sys.path.insert(0,str(OP.parent));from copula_restore import restore
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts/vework/t1ext'));from label_means_const import COARSE
GROUPS=['CM_V','CM_A','ENDO','EPI','MESO','NCC','SHF'];SEED=20261009
IEG={'Fos','Fosb','Jun','Junb','Jund','Egr1','Egr2','Egr3','Atf3','Ier2','Ier3','Ier5','Dusp1','Zfp36','Klf2','Klf4','Klf6','Nr4a1','Hspa1a','Hspa1b','Hspa8','Hsph1','Btg2','Cyr61','Ccn1','Socs3','Gadd45b','Ppp1r15a','Mt1','Mt2'}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def xsha(a):
 h=hashlib.sha256()
 for s in range(0,len(a),128):h.update(np.ascontiguousarray(a[s:s+128],dtype=np.float32).tobytes())
 return h.hexdigest()
def health(a):
 lib=[];ng=[];mean=np.zeros(a.shape[1],np.float64)
 for s in range(0,len(a),128):
  z=np.asarray(a[s:s+128]);lib.extend(np.expm1(z.astype(np.float64)).sum(1).tolist());ng.extend((z>0).sum(1).tolist());mean+=z.sum(0,dtype=np.float64)
 return {'quantile_levels':[0,.01,.1,.5,.9,.99,1],'library_quantiles':np.quantile(lib,[0,.01,.1,.5,.9,.99,1]).tolist(),'detected_genes_quantiles':np.quantile(ng,[0,.01,.1,.5,.9,.99,1]).tolist(),'zero_rows':int(np.sum(np.asarray(ng)==0)),'mean':mean/len(a)}

t0=time.time();assert sha(BASE)==BASE_SHA;assert sha(OP)==OP_SHA
canonical=['source_donor_rows.npy','states.npy','trust_genes.npy','source_donor_barcodes.npy','parent.npy','paired_template.npy','prediction.npy','t1_val__joint_external_e95__v0095.h5ad','MANIFEST.json','FAILED_HEALTH.json']
assert not any((OUT/p).exists() for p in canonical),'Refusing to overwrite existing candidate-run artifacts'
base=ad.read_h5ad(BASE);assert base.shape==(5118,32285)
panelpath=REC/'data/T1__val.official.genes.txt'
assert sha(panelpath)=='2aeae4cd284933956242bbc9c5ab4f565c1d2acc7cc3fd3037977e4bce8be4bf'
assert list(base.var_names)==panelpath.read_text().splitlines()
genes=np.array(base.var_names.astype(str));statespath=REC/'work/repro51/chain/v0051_donor_types.npy';states=np.load(statespath).astype(str)
contextpath=REC/'work/repro51/chain/v0051.npy';context=np.load(contextpath,mmap_mode='r');assert context.shape==base.shape
assert sha(statespath)=='9c63848dbbee65f4302902a2ddc8ac0bc6f80ab78f6044a8c5f038c417bcaa47'
assert sha(contextpath)=='b4cb68a55d93970a8ee7f11da3fe0fc899db00afa3aa66005b3b8436fcdb5326'
assert xsha(context)=='541d0aa6b74c3d36c973264da5c224cd89119eccf99d151eb294ef7b873cf22c'
coarse=np.array([COARSE[g] for g in states]);assert len(coarse)==len(base)
sourcepath=ROOT/'audit/GSM5820434_panel_log1p.h5ad';source=ad.read_h5ad(sourcepath)
assert sha(sourcepath)=='1a9a89b2a170b21ffa6f2073f0b98542f7b79203e6cebef2c36e0e9b85113c09'
assert np.array_equal(source.var_names.astype(str),genes)
mpath=ROOT/'audit/mapping_arrays.npz';mapping=np.load(mpath)
assert sha(mpath)=='ad44601d15500ff4569ef5077eba3300bf620d400689af1f2378123848a125a6'
standardpath=ROOT/'audit/donor_matching_standardization.npz';standard=np.load(standardpath)
assert sha(standardpath)=='c01b57edf178fe288a3ce3dae9e014dac526ecad3a8935f85916ef37b1fb5071'
assert np.array_equal(mapping['markers'],standard['markers'])
quality=json.loads((ROOT/'audit/MAPPING_AUDIT.json').read_text())
assert sha(ROOT/'audit/MAPPING_AUDIT.json')=='bdea6ee18abfe947259715884331fc82a703639a7fde3497851b906d308f9f90'
threshold=20.951346729303403;assert quality['ood_threshold']==threshold
eligible=(mapping['confidence']>=.8)&(mapping['source_nn_distance']<=threshold)
slabels=mapping['predicted'];markers=standard['markers'];mu=standard['mu'];sd=standard['sd']
Q=(np.asarray(context[:,markers],dtype=np.float32)-mu)/sd
S=(source.X[:,markers].toarray()-mu)/sd
rng=np.random.default_rng(SEED);donors=np.full(len(base),-1,dtype=int);reuse={}
with threadpool_limits(limits=1):
 for g in GROUPS:
  rows=np.flatnonzero(coarse==g);pool=np.flatnonzero((slabels==g)&eligible)
  if len(pool)<50 or not len(rows):reuse[g]={'n_source_pool':len(pool),'n_recipient':len(rows),'fallback':True};continue
  nn=NearestNeighbors(n_neighbors=5,n_jobs=1).fit(S[pool]);ix=nn.kneighbors(Q[rows],return_distance=False)
  pick=pool[ix[np.arange(len(rows)),rng.integers(5,size=len(rows))]];donors[rows]=pick
  unique,count=np.unique(pick,return_counts=True);q=count/count.sum();entropy=float(-np.sum(q*np.log(q)))
  reuse[g]={'n_source_pool':len(pool),'n_recipient':len(rows),'n_unique':len(unique),'max_reuse':int(count.max()),'donor_entropy':entropy,'effective_donors':float(np.exp(entropy)),'fallback':False}
del Q,S,context;gc.collect()
trust=source.var.in_external.to_numpy()&~np.array([g.startswith(('Hba','Hbb','mt-')) or g in IEG or g=='Malat1' for g in genes])
np.save(OUT/'source_donor_rows.npy',donors);np.save(OUT/'states.npy',states);np.save(OUT/'trust_genes.npy',trust)
np.save(OUT/'source_donor_barcodes.npy',np.array([str(source.obs_names[i]) if i>=0 else 'FALLBACK' for i in donors]))
P=np.lib.format.open_memmap(OUT/'parent.npy',mode='w+',dtype='float32',shape=base.shape)
for s in range(0,len(base),128):P[s:s+128]=base.X[s:s+128].toarray()
P.flush()
T=np.lib.format.open_memmap(OUT/'paired_template.npy',mode='w+',dtype='float32',shape=base.shape);T[:]=0
rows=np.flatnonzero(donors>=0);selected=source.X[donors[rows]].tocsr()
for start in range(0,base.n_vars,256):
 cols=np.arange(start,min(start+256,base.n_vars));cols=cols[trust[cols]]
 if len(cols):T[np.ix_(rows,cols)]=selected[:,cols].toarray()
T.flush();del selected,source;gc.collect()
pred,diag=restore(P,T,states,blend=.5,block_size=256,seed=SEED)
unsupported=donors<0
assert np.array_equal(pred[unsupported],P[unsupported])
for start in range(0,base.n_vars,256):
 cols=np.arange(start,min(start+256,base.n_vars));cols=cols[~trust[cols]]
 if len(cols):assert np.array_equal(pred[:,cols],P[:,cols])
before=health(P);after=health(pred);mean_abs=float(np.max(np.abs(after.pop('mean')-before.pop('mean'))))
assert mean_abs<1e-10 and np.isfinite(pred).all() and (pred>=0).all()
ratios={'median_library':after['library_quantiles'][3]/before['library_quantiles'][3],
 'median_detection':after['detected_genes_quantiles'][3]/before['detected_genes_quantiles'][3],
 'q01_library':after['library_quantiles'][1]/before['library_quantiles'][1],
 'q99_library':after['library_quantiles'][5]/before['library_quantiles'][5]}
health_gate={'median_library':.8<=ratios['median_library']<=1.25,'median_detection':.8<=ratios['median_detection']<=1.25,
 'q01_library':.5<=ratios['q01_library']<=2,'q99_library':.5<=ratios['q99_library']<=2,'no_new_zero_rows':after['zero_rows']<=before['zero_rows']}
if not all(health_gate.values()):
 (OUT/'FAILED_HEALTH.json').write_text(json.dumps({'gate':health_gate,'ratios':ratios,'before':before,'after':after},indent=2))
 raise RuntimeError('Predeclared numerical health gate failed; no candidate emitted')
expression_hash=xsha(pred);parent_expression_hash=xsha(P);assert expression_hash!=parent_expression_hash
np.save(OUT/'prediction.npy',pred)
metadata={'candidate_id':'v0095','method':'paired independent E9.5 empirical joint rank restoration','source':'GSE193746/GSM5820434 only',
 'parent_kind':'RECONSTRUCTED_v0092_NOT_ORIGINAL_SCORED_ARTIFACT','parent_sha256':BASE_SHA,'operator_sha256':OP_SHA,'rank_blend':.5,'seed':SEED,
 'matching_context':'paired v0051 carrier; not OT-shifted parent','matching_standardization_sha256':sha(standardpath),
 'source_eligibility_standardization':'float64 source mapping audit','donor_matching_standardization':'separately frozen float32',
 'source_confidence_min':.8,'source_ood_distance_max':threshold,'min_source_cells_per_group':50,'k_donors':5,
 'source_absolute_expression_and_proportions_not_transferred':True,'fine_state_gene_marginals_exact':True,
 'row_libraries_and_frozen_probe_mass_not_invariants':True,'historical_parent_server_score_not_assigned':True}
out=ad.AnnData(sp.csr_matrix(pred),obs=base.obs.copy(),var=base.var.copy(),uns=dict(base.uns))
out.uns['t1_joint_external_e95']=json.dumps(metadata,sort_keys=True)
candidate=OUT/'t1_val__joint_external_e95__v0095.h5ad';out.write_h5ad(candidate,compression='gzip')
manifest={'status':'BUILT_NOT_SUBMITTED_NOT_SERVER_SCORED','metadata':metadata,'source_donor_reuse':reuse,'operator_diagnostics':diag,
 'full_population_pseudobulk_max_abs_difference':mean_abs,'unsupported_rows_unchanged':True,'protected_and_missing_genes_unchanged':True,
 'numerical_health_gate':health_gate,'health_ratios':ratios,
 'parent_health':before,'candidate_health':after,'shape':list(out.shape),'runtime_seconds':time.time()-t0,
 'candidate':{'path':str(candidate),'sha256':sha(candidate),'expression_sha256':expression_hash,'bytes':candidate.stat().st_size},
 'parent':{'path':str(BASE),'sha256':BASE_SHA,'expression_sha256':parent_expression_hash},
 'inputs':{str(p):sha(p) for p in [statespath,contextpath,sourcepath,mpath,standardpath,panelpath,OP]},
 'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in OUT.iterdir() if p.is_file()},'builder_sha256':sha(Path(__file__))}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)
