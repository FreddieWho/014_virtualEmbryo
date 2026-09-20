"""Immediately filter selected 10x columns; quarantine output, no model statistics."""
import csv,hashlib,json
from pathlib import Path
import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy import sparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/t3_data_intake_20260920';Q=ROOT/'infra/external_data/quarantine/T3-NEXT-R56-20260920'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
plan=pd.read_csv(OUT/'fibro_planned_keep_samples.tsv',sep='\t',keep_default_na=False)
fetch=json.loads((OUT/'MATRIX_FETCH_RECEIPT.json').read_text());expected={Path(x['path']).name:x['sha256'] for x in fetch['files'] if 'sha256' in x}
parts=[];audit=[];excluded=[];kept=[]
for f in sorted((Q/'raw').glob('*.h5')):
 assert sha(f)==expected[f.name]
 sample=f.name.split('_')[0];spec=plan[plan['sample']==sample].set_index('cell');assert spec.index.is_unique
 with h5py.File(f) as h:
  g=h['matrix'];barcodes=np.array([s.decode() for s in g['barcodes'][:]])
  names=np.array([s.decode() for s in g['features/name'][:]])
  ids=np.array([s.decode() for s in g['features/id'][:]])
  types=np.array([s.decode() for s in g['features/feature_type'][:]])
  gene_mask=types=='Gene Expression';features=np.where(gene_mask)[0];ptr=g['indptr'][:];selected=np.where(np.isin(barcodes,spec.index))[0]
  assert len(selected)==len(spec), 'planned barcode missing from expression matrix'
  # Access expression values only for explicitly retained columns; discard other cells.
  vals=[];inds=[];newptr=[0]
  for i in selected:
   a,b=int(ptr[i]),int(ptr[i+1]);idx=g['indices'][a:b];val=g['data'][a:b]
   vals.append(val);inds.append(idx);newptr.append(newptr[-1]+len(val))
  x=sparse.csc_matrix((np.concatenate(vals),np.concatenate(inds),np.array(newptr)),shape=(len(names),len(selected)))[features,:].T.tocsr()
  obs=spec.loc[barcodes[selected]].copy();obs.index=pd.Index([sample+':'+x for x in obs.index],name='cell_id');obs['cell_type']='adult_mouse_cardiac_fibroblast';obs['stage']='8_weeks_ex_vivo';obs['permit_status']='QUARANTINE_NOT_APPROVED';obs['model_input']=False
  var=pd.DataFrame({'gene_symbol':names[gene_mask]},index=pd.Index(ids[gene_mask],name='gene_id'));assert var.index.is_unique
  parts.append(ad.AnnData(x,obs=obs,var=var))
  for i,b in enumerate(barcodes):
   (kept if i in set(selected) else excluded).append(dict(sample=sample,cell=b,reason='PROVISIONAL_KEEP' if i in set(selected) else 'NOT_IN_PREDECLARED_KEEP_PLAN',model_input='false'))
  audit.append(dict(sample=sample,raw_shape=g['shape'][:].tolist(),raw_cells=len(barcodes),retained_cells=len(selected),removed_cells=len(barcodes)-len(selected),gene_expression_features=len(features),sha256=expected[f.name]))
a=ad.concat(parts,join='inner',merge='same');panel=json.loads((OUT/'panel_genes.json').read_text());assert set(panel)<=set(a.var.gene_symbol);assert a.n_obs==len(plan)
a.uns['data_use']='QUARANTINE_ONLY: incomplete manual phenocopy review; raw counts; no training permit'
p=Q/'filtered/GSE261783_OP2_resting_provisional_raw.h5ad';p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();a.write_h5ad(p,compression='gzip')
for name,rows in [('fibro_actual_keep_cells.tsv',kept),('fibro_actual_remove_cells.tsv',excluded)]:
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=['sample','cell','reason','model_input'],delimiter='\t');w.writeheader();w.writerows(rows)
r=dict(status='FILTERED_QUARANTINE_NOT_APPROVED',task='T3:gata4',path=str(p.relative_to(ROOT)),sha256=sha(p),shape=list(a.shape),panel_coverage=500,normalization='RAW_COUNTS_NOT_NORMALIZED',model_input=False,formal_training='NOT_RUN',forbidden_records_remaining='NOT_ASSERTED_MANUAL_PHENOCOPY_REVIEW_PENDING',project_symbol_blacklist_hits_remaining=0,embeddings='NONE',adjacency='NONE',samples=audit,condition_counts={k:int(v) for k,v in a.obs.condition.value_counts().items()},plan_sha256=sha(OUT/'fibro_planned_keep_samples.tsv'))
(OUT/'FIBRO_FILTER_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['status','shape','panel_coverage','path']}))
