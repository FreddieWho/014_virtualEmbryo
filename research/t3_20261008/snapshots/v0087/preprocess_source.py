import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import gzip,tarfile,json,time,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from scipy import sparse
P=Path(__file__).parent;S=Path('/workspace/shared/t3_developmental_sources');A=S/'admitted';O=P/'source_panel';O.mkdir(exist_ok=True)
panel=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad',backed='r').var_names.tolist();alias={'Wisp2':'Ccn5','Tmem2':'Cemip2'};reports=[]
for gene,prefix in [('WT','GSE122187_WT'),('Dnmt3a','GSE137337_DNMT3A'),('Kmt2a','GSE137337_KMT2A'),('Kdm2b','GSE137337_KDM2B')]:
 t=time.time();tar=None;f=next(A.glob(prefix+'*'))
 if gene=='Dnmt3a':
  f=A/'GSE137337_DNMT3A_E8.5_1ab.matrix.mtx.gz';m=gzip.open(f,'rb');features=gzip.open(S/'GSE137337_features.gz','rt').read().splitlines();bar=lambda:gzip.open(A/'GSE137337_DNMT3A_E8.5_1ab.barcodes.tsv.gz','rt')
 else:
  f=next(A.glob(prefix+'*.tar.gz'));tar=tarfile.open(f,'r:gz');members=tar.getmembers()
  def openmember(kind):
   mm=[a for a in members if a.isfile() and (Path(a.name).name.startswith(kind))][0];raw=tar.extractfile(mm);return gzip.GzipFile(fileobj=raw) if mm.name.endswith('.gz') else raw
  features=openmember('genes' if gene=='WT' else 'features').read().decode().splitlines();m=openmember('matrix');bar=lambda:openmember('barcodes')
 genes=[x.split('\t')[1] for x in features];mapping=np.array([panel.index(alias.get(g,g)) if alias.get(g,g) in panel else -1 for g in genes],dtype=np.int32)
 line=m.readline()
 while line.startswith(b'%'):line=m.readline()
 ng,nc,nnz=map(int,line.split());assert ng==len(genes);print(gene,ng,nc,nnz,flush=True);tot=np.zeros(nc,dtype=np.float64);det=np.zeros(nc,dtype=np.int32);rr=[];cc=[];vv=[];left=b'';seen=0
 while True:
  chunk=m.read(8*1024*1024)
  if not chunk:break
  chunk=left+chunk;end=chunk.rfind(b'\n');left=chunk[end+1:];z=np.fromstring(chunk[:end].decode(),dtype=np.int64,sep=' ').reshape(-1,3);rows=z[:,0]-1;cols=z[:,1]-1;val=z[:,2];np.add.at(tot,cols,val);np.add.at(det,cols,1);mask=mapping[rows]>=0;rr.append(cols[mask].astype('int32'));cc.append(mapping[rows[mask]]);vv.append(val[mask].astype('float32'));seen+=len(z)
 assert not left.strip();assert seen==nnz;(m.close());mat=sparse.coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(nc,500)).tocsr();del rr,cc,vv
 # Retain every barcode with any panel signal; no heuristic cell call. Metadata selects true cells later.
 use=np.flatnonzero(np.asarray(mat.sum(1)).ravel()>0);mat=mat[use];wanted=set(use.tolist());names=[]
 with bar() as b:
  for i,line in enumerate(b):
   if i in wanted:names.append((line.decode() if isinstance(line,bytes) else line).strip())
 assert len(names)==len(use);a=ad.AnnData(mat,obs=pd.DataFrame({'raw_column':use,'native_umi':tot[use],'native_genes':det[use],'source_condition':gene},index=names),var=pd.DataFrame(index=panel));a.uns['normalization']='raw panel UMI counts, all panel-positive droplets; not yet genotype/cell filtered';a.uns['aliases']=alias;out=O/f'{gene}_raw_panel.h5ad';a.write_h5ad(out,compression='gzip');report=dict(gene=gene,raw_matrix_shape=[ng,nc],nnz=nnz,panel_symbols_found=int((mapping>=0).sum()),retained_panel_positive_droplets=len(use),seconds=time.time()-t,output=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest());reports.append(report);(O/'PREPROCESS.json').write_text(json.dumps(reports,indent=2));print(report,flush=True)
 if tar:tar.close()
