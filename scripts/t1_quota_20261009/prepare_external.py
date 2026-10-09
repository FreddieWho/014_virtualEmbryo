"""Hash-locked four-sample restoration; no label model refit.

QC and normalization reproduce t1ext/ext_prep.py. The original E8.5_1
source gzip is truncated; its last incomplete barcode is excluded explicitly.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): os.environ[k]='1'
import argparse,gzip,json,subprocess,zipfile,gc
from pathlib import Path
import numpy as np,pandas as pd,scipy.sparse as sp,anndata as ad
SAMPLES={'GSM7226268_E8_5_1':8.5,'GSM7226269_E8_5_2':8.5,'GSM7226272_E14_5_1':14.5,'GSM7226273_E14_5_2':14.5}

def matrix(path):
 proc=subprocess.Popen(['gzip','-cd',str(path)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 while True:
  line=proc.stdout.readline()
  if not line.startswith(b'%'): break
 ng,nb,nnz=map(int,line.split()); ii=[];jj=[];vv=[]
 for frame in pd.read_csv(proc.stdout,sep=r'\s+',header=None,names=['i','j','v'],dtype={'i':'int32','j':'int32','v':'float32'},chunksize=1000000,on_bad_lines='skip'):
  frame=frame.dropna(); ii.append(frame.i.to_numpy()-1);jj.append(frame.j.to_numpy()-1);vv.append(frame.v.to_numpy())
 proc.wait(); i=np.concatenate(ii);j=np.concatenate(jj);v=np.concatenate(vv);del ii,jj,vv
 truncated=len(v)<nnz
 if truncated:
  keep=j<j.max();i,j,v=i[keep],j[keep],v[keep]
 return sp.csc_matrix((v,(i,j)),shape=(ng,nb)),[truncated,len(v),nnz]

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--archive',required=True);a=p.parse_args()
 root=Path(a.root);out=root/'external_processed';out.mkdir(parents=True,exist_ok=True)
 genes=(root/'data/T1__val.official.genes.txt').read_text().splitlines()
 with zipfile.ZipFile(a.archive) as z:
  for t in [8.5,14.5]:
   path=root/f'frozen_external_labels/ext{t}_labels.npy'
   if not path.exists():path.write_bytes(z.read(f'frozen_external_labels/ext{t}_labels.npy'))
  expected=json.loads(z.read('receipts/proc/QC.json'))['samples']
 all_qc={};counts={8.5:0,14.5:0}
 for name,stage in SAMPLES.items():
  dest=out/(name+'.h5ad')
  if dest.exists():
   obj=ad.read_h5ad(dest,backed='r');counts[stage]+=obj.n_obs;obj.file.close();continue
  feats=pd.read_csv(root/'external_raw'/f'{name}_features.tsv.gz',sep='\t',header=None)
  M,tr=matrix(root/'external_raw'/f'{name}_matrix.mtx.gz')
  umi=np.asarray(M.sum(0)).ravel();ng=np.asarray((M>0).sum(0)).ravel();mt=feats[1].str.startswith('mt-').values
  mtf=np.asarray(M[mt].sum(0)).ravel()/np.maximum(umi,1)
  keep=(umi>=1500)&(ng>=700)&(mtf<=.25)
  M=M[:,keep].T.tocsr().astype(np.float32);lib=np.asarray(M.sum(1)).ravel()
  M=sp.diags(1e4/lib)@M;M.data=np.log1p(M.data)
  sym=feats[1].values;first=~pd.Series(sym).duplicated().values;idx={g:i for i,g in enumerate(sym) if first[i]}
  cols=np.array([idx.get(g,-1) for g in genes]);have=cols>=0
  P=sp.hstack([M.tocsc()[:,cols[have]],sp.csc_matrix((M.shape[0],(~have).sum()),dtype=np.float32)]).tocsc()
  P=P[:,np.argsort(np.concatenate([np.flatnonzero(have),np.flatnonzero(~have)]))].tocsr()
  labels=np.load(root/f'frozen_external_labels/ext{stage}_labels.npy',allow_pickle=True).astype(str)
  offset=counts[stage];lab=labels[offset:offset+P.shape[0]];assert len(lab)==P.shape[0]
  counts[stage]+=len(lab)
  obs=pd.DataFrame({'sample':name,'stage':stage,'coarse':lab,'umi':umi[keep],'n_genes':ng[keep],'mt_frac':mtf[keep]},index=[f'{name}:{i}' for i in range(len(lab))])
  obj=ad.AnnData(P,obs=obs,var=pd.DataFrame({'in_external':have},index=genes))
  qc={'stage':stage,'barcodes_raw':int(len(umi)),'cells_kept':int(keep.sum()),'median_umi':float(np.median(umi[keep])),'median_genes':float(np.median(ng[keep])),'panel_genes_present':int(have.sum()),'mtx_truncated_at_source':tr[0],'entries_read':tr[1],'entries_declared':tr[2]}
  assert qc==expected[name],(name,qc,expected[name])
  obj.uns['source_restoration']=json.dumps({'qc':qc,'label_source':'frozen_recovery_classifier_not_original_historical_v92','labels_source_sha':'tracked separately in INPUT_IDENTITIES.json'})
  obj.write_h5ad(dest,compression='gzip');all_qc[name]=qc;print(name,qc,flush=True)
  del obj,M,P,umi,ng,mtf;gc.collect()
 for t,n in counts.items():assert n==len(np.load(root/f'frozen_external_labels/ext{t}_labels.npy',allow_pickle=True))
 (out/'QC_RESTORATION.json').write_text(json.dumps(all_qc,indent=2))
if __name__=='__main__':main()
