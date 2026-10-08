from pathlib import Path
import h5py,json,numpy as np,pandas as pd,scipy.sparse as sp,anndata as ad,hashlib
from anndata.io import read_elem,sparse_dataset
r=Path('/workspace/shared/t2_external_sources_20261008');out=r/'e145_endpoint';out.mkdir(exist_ok=True);p=r/'quarantine/E14.5_E1S3.MOSTA.h5ad';panel=Path('/workspace/shared/virtual_embryo_data/T2__heart__val_extrap.genes.txt').read_text().splitlines();markers=['Tnnt2','Tnni3','Actc1','Myh6','Myh7','Myl2','Myl7']
rec=json.loads((r/'E145_FETCH_RECEIPT.json').read_text());assert rec['completed'] and rec['bytes']==p.stat().st_size
with h5py.File(p,'r') as f:
 obs=read_elem(f['obs']);var=read_elem(f['var']);names=list(var.index.astype(str));assert len(names)==len(set(names));idx={g:i for i,g in enumerate(names)}
 assert 'annotation' in obs,'No author anatomical annotation'
 mask=obs['annotation'].astype(str).str.lower().eq('heart').to_numpy();rows=np.flatnonzero(mask);assert len(rows)>0,'No heart label'
 assert 'count' in f['layers'],'No raw count layer'
 grp=f['layers/count']; ptr=grp['indptr'][:]; sizes=ptr[rows+1]-ptr[rows]; subptr=np.r_[0,np.cumsum(sizes)]; vals=np.concatenate([grp['data'][ptr[i]:ptr[i+1]] for i in rows]); cols=np.concatenate([grp['indices'][ptr[i]:ptr[i+1]] for i in rows]); counts=sp.csr_matrix((vals,cols,subptr),shape=(len(rows),len(var)));assert np.isfinite(counts.data).all() and (counts.data>=0).all() and np.equal(counts.data,np.round(counts.data)).all()
 marker_cols=[idx[g] for g in markers if g in idx];assert len(marker_cols)>=5;cm=np.asarray((counts[:,marker_cols]>0).sum(axis=1)).ravel()>=2
 present=np.array([g in idx for g in panel]);src_cols=[idx[g] for g in panel if g in idx];coo=counts[:,src_cols].tocoo();target_cols=np.flatnonzero(present)[coo.col];X=sp.csr_matrix((coo.data,(coo.row,target_cols)),shape=(len(rows),500))
 cleanobs=pd.DataFrame({'source_row':rows,'stage':'E14.5','sample':'E14.5_E1S3','anatomical_region':'Heart','cm_enriched_fixed_marker':cm,'raw_full_transcriptome_library_size':np.asarray(counts.sum(axis=1)).ravel()},index=obs.index[rows].astype(str));cleanvar=pd.DataFrame({'measured_in_source':present},index=panel);assert cleanobs.index.is_unique
 for label,keep in [('heart',np.ones(len(rows),bool)),('cm_enriched',cm)]:
  a=ad.AnnData(X=X[keep].astype(np.float32),obs=cleanobs.iloc[np.flatnonzero(keep)].copy(),var=cleanvar.copy());a.uns['source_url']=rec['url'];a.uns['source_sha256']=rec['sha256'];a.uns['counts_not_log_normalised']=True;a.uns['selection_rule']='author anatomical Heart; CM-enriched subset requires >=2 positive raw markers: '+','.join(markers);a.uns['missing_gene_semantics']='Zeros in unmeasured columns are placeholders; exclude using var.measured_in_source';a.write_h5ad(out/f'E14.5_{label}_panel_raw.h5ad',compression='gzip')
 cleanobs.to_csv(out/'selected_rows.tsv',sep='\t');pd.DataFrame({'gene':panel,'measured_in_source':present}).to_csv(out/'gene_presence.tsv',sep='\t',index=False)
 report={'stage':'E14.5','sample':'E14.5_E1S3','source_shape':[len(obs),len(var)],'heart_bins':len(rows),'cm_enriched_bins':int(cm.sum()),'present_panel_genes':int(present.sum()),'absent_panel_genes':[g for g,m in zip(panel,present) if not m],'markers':markers,'markers_present':[g for g in markers if g in idx],'cm_rule':'>=2 positive raw-count markers inside anatomical Heart','raw_layer':'layers/count','counts_integer_finite_nonnegative':True,'source_sha256':rec['sha256'],'source_url':rec['url'],'outputs':[]}
 for q in out.glob('*.h5ad'):report['outputs'].append({'path':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
 (out/'EXTRACTION_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
