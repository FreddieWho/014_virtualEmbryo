"""Read-only input audit and fresh, source-only label mapping for GSM5820434.

One measured WT E9.5 sample only. No published expression embeddings or labels.
No candidate, temporal response, or target-stage expression is generated here.
"""
import os
os.environ.update({k:'1' for k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']})
import gc, gzip, hashlib, json, sys, time
from pathlib import Path
import h5py, numpy as np, pandas as pd, scipy.sparse as sp
from scipy.io import mmread
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score, classification_report
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_limits
import anndata as ad

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source'
OUT=ROOT/'audit'; OUT.mkdir(exist_ok=True)
OFFICIAL=Path(os.environ.get('T1_RECOVERY_ROOT', 't1_recovery_run'))/'data/E9.5_RNA.h5ad'
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'scripts/vework/t1ext'))
from label_means_const import COARSE
SEED=20261009

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def strings(x):return np.array([a.decode() if isinstance(a,bytes) else str(a) for a in x])
def stats(X):
 X=sp.csr_matrix(X)
 det=np.asarray((X>0).mean(0)).ravel();mu=np.asarray(X.mean(0)).ravel()
 rt=X.copy();rt.data=np.sqrt(rt.data)
 return {'mean':mu,'det':det,'sqrt_mean':np.asarray(rt.mean(0)).ravel()}
def pct(x):return np.quantile(x,[0,.1,.25,.5,.75,.9,1]).tolist()
def getcols(f,cols):
 x=f['X'];p=x['indptr'];blocks=[];n=int(x.attrs['shape'][0])
 assert x.attrs['encoding-type']=='csc_matrix'
 for c in cols:
  a,b=int(p[c]),int(p[c+1]);blocks.append(sp.csc_matrix((x['data'][a:b],x['indices'][a:b],[0,b-a]),shape=(n,1)))
 return sp.hstack(blocks,format='csr')

t0=time.time()
feat=pd.read_csv(SOURCE/'features.tsv.gz',sep='\t',header=None)
barcodes=pd.read_csv(SOURCE/'barcodes.tsv.gz',sep='\t',header=None)[0].astype(str).to_numpy()
with gzip.open(SOURCE/'matrix.mtx.gz','rb') as f:M=mmread(f).T.tocsr().astype(np.float32)
assert M.shape==(3042,31053) and M.nnz==10766230
assert np.isfinite(M.data).all() and np.all(M.data>=0) and np.array_equal(M.data,np.rint(M.data))
umi=np.asarray(M.sum(1)).ravel();ng=np.diff(M.indptr)
mt=feat[1].astype(str).str.startswith('mt-').to_numpy()
mtfrac=np.asarray(M[:,mt].sum(1)).ravel()/np.maximum(umi,1)
keep=(umi>=1500)&(ng>=700)&(mtfrac<=.25)
qc={'input_cells':len(umi),'input_genes':M.shape[1],'input_nnz':M.nnz,'kept_cells':int(keep.sum()),
 'thresholds':{'min_umi':1500,'min_genes':700,'max_mito_fraction':.25},
 'umi_quantiles':pct(umi[keep]),'genes_quantiles':pct(ng[keep]),'mito_fraction_quantiles':pct(mtfrac[keep])}
M=M[keep].tocsr();bc=barcodes[keep]
with h5py.File(OFFICIAL,'r') as f:
 genes=strings(f['var/_index'][:]);ct=f['obs/celltype'];labels=strings(ct['categories'][:])[ct['codes'][:]]
 yc=np.array([COARSE[x] for x in labels]);groups=np.array(sorted(set(yc)));n=len(yc)
train,test=train_test_split(np.arange(n),test_size=.3,random_state=SEED,stratify=yc)
sym=feat[1].astype(str).to_numpy();lookup={g:i for i,g in enumerate(genes)}
source_symbols=set(sym)
have=np.array([g in source_symbols for g in genes])
fr=np.array([i for i,g in enumerate(sym) if g in lookup]);to=np.array([lookup[sym[i]] for i in fr])
bridge=sp.csr_matrix((np.ones(len(fr),np.float32),(fr,to)),shape=(len(sym),len(genes)))
X=(M@bridge).tocsr()
X=sp.diags(1e4/umi[keep])@X;X=X.tocsr();X.data=np.log1p(X.data)
assert np.isfinite(X.data).all() and (X.data>=0).all()
dups=pd.Series(sym).value_counts();dups=dups[dups>1]
qc.update(panel_genes=len(genes),panel_present=int(have.sum()),duplicate_symbols={str(k):int(v) for k,v in dups.items()},
 normalization='Counts aggregated by symbol, CP10k denominator over all original features, then natural log1p')
del M,bridge;gc.collect()
obs=pd.DataFrame({'sample':'GSM5820434','stage':'E9.5','n_counts':umi[keep],'n_genes':ng[keep],'mito_fraction':mtfrac[keep]},index=bc)
a=ad.AnnData(X=X,obs=obs,var=pd.DataFrame({'in_external':have},index=genes))
a.uns['source']='GSM5820434 only; raw sample-specific CellRanger counts'
a.write_h5ad(OUT/'GSM5820434_panel_log1p.h5ad',compression='gzip')
(OUT/'QC.json').write_text(json.dumps(qc,indent=2))
print('SOURCE_QC',json.dumps(qc),flush=True)

# Marker selection and standardization see only official training rows.
mean=np.zeros((len(groups),len(genes)),np.float64)
official_stats={g:{k:np.empty(len(genes),np.float32) for k in ['mean','det','sqrt_mean']} for g in groups}
with h5py.File(OFFICIAL,'r') as f:
 for j in range(0,len(genes),256):
  cols=np.arange(j,min(j+256,len(genes)));z=getcols(f,cols)
  for k,g in enumerate(groups):
   mean[k,cols]=np.asarray(z[train[yc[train]==g]].mean(0)).ravel()
   s=stats(z[yc==g])
   for name,v in s.items():official_stats[g][name][cols]=v
bad=np.array([g.startswith(('mt-','Rpl','Rps')) or g=='Malat1' for g in genes])
chosen=set()
for k,g in enumerate(groups):
 score=mean[k]-np.max(np.delete(mean,k,axis=0),axis=0);score[~have|bad]=-np.inf
 chosen.update(np.argsort(-score)[:40].tolist())
markers=np.array(sorted(chosen))
with h5py.File(OFFICIAL,'r') as f:C=getcols(f,markers).toarray().astype(np.float64)
mu=C[train].mean(0);sd=C[train].std(0)+1e-3
Ctr=(C[train]-mu)/sd;Cte=(C[test]-mu)/sd;Xe=(X[:,markers].toarray()-mu)/sd
with threadpool_limits(limits=1):
 clf=LogisticRegression(max_iter=1000,C=.5,random_state=SEED).fit(Ctr,yc[train])
 ph=clf.predict_proba(Cte);pe=clf.predict_proba(Xe)
pred=clf.classes_[pe.argmax(1)];conf=pe.max(1)
mapped=np.where(conf>=.5,pred,'LOWCONF')
nn=NearestNeighbors(n_neighbors=1,n_jobs=1).fit(Ctr)
dh=nn.kneighbors(Cte,return_distance=True)[0][:,0]
de=nn.kneighbors(Xe,return_distance=True)[0][:,0]
oodcut=float(np.quantile(dh,.95))
coverage=[];rawstats={}
for g in groups:
 ii=np.flatnonzero(mapped==g);ss=stats(X[ii]) if len(ii) else None
 row={'state':g,'n_external_confident':len(ii),'n_official':int((yc==g).sum()),
  'external_confidence_median':float(np.median(conf[ii])) if len(ii) else None,
  'fraction_external_above_official_holdout95_nn':float(np.mean(de[ii]>oodcut)) if len(ii) else None}
 if ss:
  for k,v in ss.items():rawstats[f'{g}|external|{k}']=v;rawstats[f'{g}|official|{k}']=official_stats[g][k]
  cm=official_stats[g]['mean'];em=ss['mean'];ok=have&~bad
  row.update(mean_spearman=float(pd.Series(cm[ok]).corr(pd.Series(em[ok]),method='spearman')),
   gene_detection_mean_official=float(official_stats[g]['det'].mean()),gene_detection_mean_external=float(ss['det'].mean()),
   sqrt_marginal_rmse=float(np.sqrt(np.mean((ss['sqrt_mean']-official_stats[g]['sqrt_mean'])**2))))
 coverage.append(row)
audit={'seed':SEED,'classifier_training':'official E9.5 only,70% stratified rows; feature selection and scaling on train only',
 'n_train':len(train),'n_test':len(test),'n_markers':len(markers),'max_iter':1000,'C':.5,
 'heldout_accuracy':float(np.mean(clf.classes_[ph.argmax(1)]==yc[test])),
 'heldout_balanced_accuracy':float(balanced_accuracy_score(yc[test],clf.classes_[ph.argmax(1)])),
 'heldout_report':classification_report(yc[test],clf.classes_[ph.argmax(1)],output_dict=True),
 'external_n_lowconf':int((mapped=='LOWCONF').sum()),'external_confidence_quantiles':pct(conf),
 'heldout_nn_distance_quantiles':pct(dh),'external_nn_distance_quantiles':pct(de),'ood_threshold':oodcut,
 'state_coverage':coverage,'runtime_seconds':time.time()-t0,
 'limitations':['Fresh source-label transfer is a diagnostic, not organizer frozen probe','Single pooled library,8 embryos; no biological replication','Whole-cell source versus multiome-nucleus challenge; absolute detection and positive values not portable','No temporal drift can be inferred from this one snapshot','No candidate generated or scored']}
np.savez_compressed(OUT/'mapping_arrays.npz',markers=markers,marker_symbols=genes[markers],genes=genes,
 labels=mapped,predicted=pred,confidence=conf,source_nn_distance=de,official_train=train,official_test=test,
 official_labels=yc,**rawstats)
pd.DataFrame({'barcode':bc,'state':mapped,'prediction':pred,'confidence':conf,'nearest_official_distance':de}).to_csv(OUT/'source_mapping.tsv',sep='\t',index=False)
pd.DataFrame(coverage).to_csv(OUT/'state_coverage.tsv',sep='\t',index=False)
(OUT/'MAPPING_AUDIT.json').write_text(json.dumps(audit,indent=2))
manifest={'source_accession':'GSM5820434','source_series':'GSE193746','stage':'E9.5','genotype':'wildtype','condition':'nondiabetic control','tissue':'whole heart','strain':'C57BL/6J',
 'raw_url':'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM5820nnn/GSM5820434/suppl/GSM5820434_mat_conE9_5_filtered_feature_bc_matrix.tar.gz',
 'forbidden_samples_never_downloaded':['GSM5820435','GSM5820436','GSM5820437'],
 'official_input_sha256':sha(OFFICIAL),'source_files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in SOURCE.iterdir() if p.is_file()},
 'script_sha256':sha(Path(__file__)),'output_files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in OUT.iterdir() if p.is_file()}}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print('MAPPING_AUDIT',json.dumps(audit),flush=True)
