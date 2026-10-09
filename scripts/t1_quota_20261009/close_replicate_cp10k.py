"""Compose frozen replicate-hurdle margins with proven measurement restoration.

The full unshrunken endpoint must equal exact v0096, not merely be close.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,time,resource
from pathlib import Path
import numpy as np,anndata as ad
from normalization import restore_cp10k
from build_cp10k import sha,expr_sha,masses

P94='4795a48fb6fa8ca0a6106f3e38f1f4bca1ed2ed9b40c53465cb5662f31f7d95e'
P96='114a5e8b8cc397f8d6866fd221c5b4b312c791cdb487badf7aaa6e7bc9f714e0'

def exact_sparse(a,b):
 a=a.tocsr();b=b.tocsr()
 return a.shape==b.shape and np.array_equal(a.indptr,b.indptr) and np.array_equal(a.indices,b.indices) and np.array_equal(a.data,b.data)

def main():
 p=argparse.ArgumentParser();p.add_argument('--preclosure',required=True);p.add_argument('--preclosure-receipt',required=True);p.add_argument('--v94',required=True);p.add_argument('--v96',required=True);p.add_argument('--outdir',required=True);p.add_argument('--control',default='none',choices=['none','pooled','permuted']);a=p.parse_args()
 t0=time.time();root=Path(a.outdir);root.mkdir(parents=True,exist_ok=True);target=root/'submission.h5ad';report=root/'BUILD.json'
 if target.exists() or report.exists():raise FileExistsError('Immutable output already exists')
 receipt=json.loads(Path(a.preclosure_receipt).read_text());assert sha(a.preclosure)==receipt['sha256'];assert sha(a.v94)==P94 and sha(a.v96)==P96
 assert receipt['checks']['exact_unshrunken_full_matrix_endpoint']
 v94=ad.read_h5ad(a.v94);v96=ad.read_h5ad(a.v96);endpoint,_=restore_cp10k(v94.X);assert exact_sparse(endpoint,v96.X)
 # Combined proof: full unshrunken hurdle output equals v94 and closure(v94)
 # equals v96 exactly. Neither follows from an approximate quantile grid.
 del v94,endpoint
 raw=ad.read_h5ad(a.preclosure);X,rawmass=restore_cp10k(raw.X)
 assert raw.obs.equals(v96.obs) and raw.var.equals(v96.var)
 final=ad.AnnData(X,obs=raw.obs.copy(),var=raw.var.copy())
 disclosure=json.loads(raw.uns['external_data_disclosure'])
 for source in disclosure['external_sources']:
  if source['accession']=='GSM5820434':source['role']='Historical v0095 joint-donor experiment and current source-only assay-calibration feasibility diagnostics; not an expression or fitted-reliability input to this candidate'
 prov={'candidate_id':'T1_val/v0097_rephurdle_cp10k' if a.control=='none' else None,'control':a.control,'selection_reference_candidate':'T1_val/v0096_cp10k/r2','selection_reference_sha256':P96,'numerical_base_v94_sha256':P94,'preclosure_sha256':sha(a.preclosure),'preclosure_expression_sha256':expr_sha(raw.X),'preclosure_recipe':json.loads(raw.uns['t1_replicate_hurdle_provenance']),'postprocessor':'exact per-row float64 expm1 / sum * 10000 then log1p ->float32; no fit/clip/pseudocount','closure_code_sha256':sha(Path(__file__)),'normalizer_code_sha256':sha(Path(__file__).with_name('normalization.py')),'unshrunken_composite_endpoint_expression_exact_v96':True,'complete_source_disclosure':disclosure,'scientific_claim':'replicate-reliability hurdle marginal regularization at fixed observed CP10k convention; no hidden-stage data or calibrated-confidence claim'}
 final.uns['ve_contract']={'normalization':'log1p_normalized','task':'T1','board':'val'};final.uns['t1_replicate_hurdle_cp10k_provenance']=json.dumps(prov,sort_keys=True);final.uns['external_data_disclosure']=json.dumps(disclosure,sort_keys=True)
 final.write_h5ad(target,compression='gzip')
 m=masses(X);meanref=np.asarray(v96.X.astype(float).mean(0)).ravel();mean=np.asarray(X.astype(float).mean(0)).ravel();d0=np.asarray((v96.X>0).sum(1)).ravel();d1=np.asarray((X>0).sum(1)).ravel()
 result={'status':'CANDIDATE_BUILT_NOT_SUBMITTED' if a.control=='none' else 'LOCAL_CONTROL_NOT_FOR_SUBMISSION','candidate_id':prov['candidate_id'],'file':str(target),'sha256':sha(target),'expression_sha256':expr_sha(X),'bytes':target.stat().st_size,'actual_numerical_inputs':'exactv94 + pairedv51 + raw-library stats, followed by fixed CP10k closure','selection_reference':'exactv96r2','full_gene_panel':32285,'unshrunken_composite_endpoint_exact_v96':True,'raw_hurdle_health_pass':receipt['health_pass'],'finite_nonnegative':bool(np.isfinite(X.data).all() and (X.data>=0).all()),'row_mass_max_error':float(np.abs(m-10000).max()),'median_detection_ratio_vs_v96':float(np.median(d1)/np.median(d0)),'pseudobulk_l2_shift_vs_v96':float(np.linalg.norm(mean-meanref)),'preclosure_report_sha256':sha(a.preclosure_receipt),'provenance':prov,'wall_seconds':time.time()-t0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 assert result['finite_nonnegative'] and result['row_mass_max_error']<.002 and receipt['health_pass']
 report.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='provenance'},indent=2))
if __name__=='__main__':main()
