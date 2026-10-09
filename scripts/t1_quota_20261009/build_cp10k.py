"""Frozen CP10k builder. Never overwrite any existing candidate."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,hashlib,json,platform,time,resource
from pathlib import Path
import numpy as np,scipy,anndata as ad
from scipy import sparse
from normalization import restore_cp10k


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def expr_sha(X):
 h=hashlib.sha256()
 for lo in range(0,X.shape[0],128):h.update(np.ascontiguousarray(X[lo:lo+128].toarray(),dtype=np.float32).tobytes())
 return h.hexdigest()

def masses(X):
 Y=X.astype(np.float64);Y.data=np.expm1(Y.data);return np.asarray(Y.sum(1)).ravel()

def sources():
 items=[]
 for sample,stage,role in [
 ('GSM7226268',8.5,'Inherited v0094 early external OT-field input and historical diagnostics; new restoration does not refit the field'),
 ('GSM7226269',8.5,'Inherited v0094 early external OT-field input and historical diagnostics; new restoration does not refit the field'),
 ('GSM7226272',14.5,'Inherited v0094 late external OT-field input and historical diagnostics; new restoration does not refit the field'),
 ('GSM7226273',14.5,'Inherited v0094 late external OT-field input and historical diagnostics; new restoration does not refit the field'),
 ('GSM7226274',16.5,'Historical temporal-warp and alternative-anchor diagnostics, including unselected anchor arms; no direct final OT-field or emitted-expression contribution'),
 ('GSM7226276',16.5,'Historical temporal-warp and alternative-anchor diagnostics, including unselected anchor arms; no direct final OT-field or emitted-expression contribution')]:
  items.append({'study':'GSE230531','accession':sample,'stage':f'E{stage}','stage_numeric':stage,'url':f'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={sample}','role':role})
 items.append({'study':'GSE193746','accession':'GSM5820434','stage':'E9.5','stage_numeric':9.5,'url':'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5820434','role':'Historical v0095 independent joint-donor experiment and source diagnostics; v0095 rejected. Not an expression or fitted-parameter input to v0096'})
 return {'official_sources':[{'name':'E8.5_RNA','stage':'E8.5','sha256':'8eab2d0ccaa89f92861b09816b76b6a731b8ed6b5995e4af196d9ed8ff76e504','role':'Inherited carrier training; full-row normalization audit'}, {'name':'E9.5_RNA','stage':'E9.5','sha256':'0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361','role':'Inherited carrier training; full-row normalization audit and released-source-only diagnostics'}],
 'external_sources':items,'protected_targets_used':False,'prohibited_external_interval':'(E9.5,E13.5]','disclosure_scope':'All direct and inherited external inputs plus prior diagnostic/model-selection sources known in this campaign','prior_artifact_disclosure_gap':'Earlier scored artifacts were not modified; this complete ledger applies to this newly created candidate only'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--config',required=True);p.add_argument('--panel',required=True);p.add_argument('--states',required=True);p.add_argument('--outdir',required=True);a=p.parse_args()
 t0=time.time();cfg=json.loads(Path(a.config).read_text());root=Path(a.outdir);root.mkdir(parents=True,exist_ok=True)
 dest=root/'submission.h5ad';report=root/'BUILD.json'
 if dest.exists() or report.exists():raise FileExistsError('Immutable candidate destination already exists')
 assert sha(a.parent)==cfg['parent_sha256']
 parent=ad.read_h5ad(a.parent);genes=Path(a.panel).read_text().splitlines();assert list(parent.var_names)==genes and parent.shape==(5118,32285)
 before=parent.X.tocsr();after,lib0=restore_cp10k(before);lib1=masses(after)
 assert np.array_equal(before.indptr,after.indptr) and np.array_equal(before.indices,after.indices)
 assert np.isfinite(after.data).all() and (after.data>0).all() and np.max(np.abs(lib1-10000))<.002
 violated=0
 for r in range(len(parent)):
  lo,hi=before.indptr[r:r+2];o=np.argsort(before.data[lo:hi],kind='stable');violated+=int((np.diff(after.data[lo:hi][o])<0).sum())
 assert violated==0
 m0=np.asarray(before.mean(0)).ravel();m1=np.asarray(after.mean(0)).ravel()
 states=np.load(a.states).astype(str);assert len(states)==len(parent)
 perstate={}
 for st in sorted(set(states)):
  ix=states==st;delta=np.asarray(after[ix].mean(0)-before[ix].mean(0)).ravel()
  perstate[st]={'rows':int(ix.sum()),'mean_delta_l2':float(np.linalg.norm(delta)),'mean_delta_max_abs':float(np.abs(delta).max()),'median_library_before':float(np.median(lib0[ix]))}
 code={p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('normalization.py')]}
 provenance={'candidate_id':cfg['candidate_id'],'parent_candidate':cfg['parent_candidate'],'parent_sha256':sha(a.parent),'parent_expression_sha256':expr_sha(before),'configuration':cfg,'code_sha256':code,'configuration_sha256':sha(a.config),'official_panel_sha256':sha(a.panel),'paired_states_sha256':sha(a.states),'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'anndata':ad.__version__,'blas_threads':1},'representation':'full-panel log1p(CP10k), float32','biological_claim':'none; measurement-consistency candidate','full_source_disclosure':sources()}
 out=ad.AnnData(after,obs=parent.obs.copy(),var=parent.var.copy())
 out.uns['ve_contract']={'normalization':'log1p_normalized','task':'T1','board':'val'}
 out.uns['t1_cp10k_provenance']=json.dumps(provenance,sort_keys=True)
 out.uns['external_data_disclosure']=json.dumps(sources(),sort_keys=True)
 assert 'no other data' not in json.dumps(dict(out.uns)).lower()
 out.write_h5ad(dest,compression='gzip')
 metrics={'rows':len(parent),'genes':len(genes),'nnz_before':before.nnz,'nnz_after':after.nnz,'changed_nnz':int(np.count_nonzero(before.data!=after.data)),'zero_support_preserved':True,'within_row_order_violations':violated,'cross_cell_gene_rank_preservation_claim':False,'library_before_quantiles':np.quantile(lib0,[0,.01,.1,.5,.9,.99,1]).tolist(),'library_after_quantiles':np.quantile(lib1,[0,.01,.1,.5,.9,.99,1]).tolist(),'maximum_library_mass_error':float(np.abs(lib1-10000).max()),'pseudobulk_shift_l2':float(np.linalg.norm(m1-m0)),'pseudobulk_shift_max_abs':float(np.abs(m1-m0).max()),'per_state':perstate}
 result={'status':'CANDIDATE_BUILT_NOT_SUBMITTED','candidate_id':cfg['candidate_id'],'parent_candidate':cfg['parent_candidate'],'file':str(dest),'sha256':sha(dest),'expression_sha256':expr_sha(after),'bytes':dest.stat().st_size,'contract_pass':True,'metrics':metrics,'provenance':provenance,'wall_seconds':time.time()-t0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 report.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['provenance','metrics']},indent=2))
if __name__=='__main__':main()
