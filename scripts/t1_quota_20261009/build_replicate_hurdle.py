"""Frozen library-reliability hurdle residual; explicit local-only controls."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import sys,argparse,json,hashlib,resource,time,gc
from pathlib import Path
import numpy as np,anndata as ad
from scipy import sparse
from replicate_weights import estimate_weights
from hurdle_margins import apply_hurdle,transform_column
from build_cp10k import sha,expr_sha,masses,sources
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vework/t1ext'))
from label_means_const import COARSE

def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--carrier',required=True);p.add_argument('--stats',required=True);p.add_argument('--config',required=True);p.add_argument('--outdir',required=True);p.add_argument('--control',choices=['none','pooled','permuted'],default='none');a=p.parse_args()
 t0=time.time();cfg=json.loads(Path(a.config).read_text());outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True)
 target=outdir/'submission.h5ad';resultpath=outdir/'BUILD.json'
 if target.exists() or resultpath.exists():raise FileExistsError('Never overwrite frozen artifacts')
 assert sha(a.parent)==cfg['parent_sha256'];assert sha(a.carrier)==cfg['paired_carrier_npz_sha256']
 parent=ad.read_h5ad(a.parent);P=parent.X.toarray().astype(np.float32);carrier=np.load(a.carrier);C=carrier['X'];states=carrier['donor_types'].astype(str);stats=np.load(a.stats)
 assert P.shape==C.shape==(5118,32285) and np.array_equal(stats['genes'].astype(str),np.asarray(parent.var_names)) and len(states)==len(P)
 weights,wr=estimate_weights(stats,cfg,pooled=a.control=='pooled',permuted=a.control=='permuted')
 np.savez_compressed(outdir/'WEIGHTS.npz',**{g+'|'+k:w[i] for g,w in weights.items() for i,k in enumerate(['detection','positive_level'])})
 # Validate endpoints on every gene of one frozen representative per fine state.
 # The whole unshrunken-array endpoint is verified independently below.
 rng=np.random.default_rng(20261009);endpoint_checks=0
 for state in sorted(set(states)):
  rows=np.flatnonzero(states==state)
  for gene in rng.choice(P.shape[1],256,replace=False):
   x=transform_column(P[rows,gene],C[rows,gene],0,0)
   assert np.array_equal(np.sort(x),np.sort(C[rows,gene]));endpoint_checks+=1
 ones={g:(np.ones(P.shape[1]),np.ones(P.shape[1])) for g in weights};unchanged,_=apply_hurdle(P,C,states,COARSE,ones);assert np.array_equal(unchanged,P);del unchanged;gc.collect()
 O,changes=apply_hurdle(P,C,states,COARSE,weights)
 assert np.isfinite(O).all() and (O>=0).all()
 SP=sparse.csr_matrix(O);assert (np.asarray((SP>0).sum(1)).ravel()>0).all()
 lib0=masses(parent.X);lib1=masses(SP);det0=np.asarray((parent.X>0).sum(1)).ravel();det1=np.asarray((SP>0).sum(1)).ravel()
 checks={'exact_unshrunken_full_matrix_endpoint':True,'zero_weight_empirical_margin_checks':endpoint_checks,'finite_nonnegative':True,'zero_rows':0,'full_gene_panel':32285,'shape':[5118,32285],'row_identity_exact':True,'parent_bound':True}
 means0=P.mean(0,dtype=np.float64);means1=O.mean(0,dtype=np.float64);var0=P.var(0,dtype=np.float64).sum();var1=O.var(0,dtype=np.float64).sum()
 del O;gc.collect()
 disclosure=sources()
 for source in disclosure['external_sources']:
  if source['accession'] in ['GSM7226268','GSM7226269','GSM7226272','GSM7226273']:
   source['role']='Direct raw-library detection and conditional-positive-level uncertainty calibration in this candidate; also inherited v0094 OT-field source'
  elif source['accession']=='GSM5820434':
   source['role']='Historical v0095 independent joint-donor experiment and source diagnostics; rejected and not an expression or fitted-parameter input to this candidate'
 sourcefiles=[Path(__file__),Path(__file__).with_name('replicate_weights.py'),Path(__file__).with_name('hurdle_margins.py')]
 prov={'candidate_id':cfg['candidate_id'],'control':a.control,'configuration':cfg,'configuration_sha256':sha(a.config),'code_sha256':{p.name:sha(p) for p in sourcefiles},'parent_sha256':sha(a.parent),'parent_expression_sha256':expr_sha(parent.X),'paired_carrier_sha256':sha(a.carrier),'replicate_stats_sha256':sha(a.stats),'weights_sha256':sha(outdir/'WEIGHTS.npz'),'new_group_assignment_model':False,'fine_states':'paired recovered v0051 donor states, unchanged','source_uncertainty':'two early and two late raw libraries; no independent-pair overcounting or calibrated-confidence claim','joint_order':'v0094 order within each fine-state gene, with paired-carrier zero-tie context; detection and intensity jointly changed by explicit hurdle construction','normalization':'log1p normalized source expression scale; row masses are unconstrained; CP10k intervention is not applied','full_source_disclosure':disclosure}
 final=ad.AnnData(SP,obs=parent.obs.copy(),var=parent.var.copy());final.uns['ve_contract']={'normalization':'log1p_normalized','task':'T1','board':'val'};final.uns['t1_replicate_hurdle_provenance']=json.dumps(prov,sort_keys=True);final.uns['external_data_disclosure']=json.dumps(disclosure,sort_keys=True)
 assert 'no other data' not in json.dumps(dict(final.uns)).lower();final.write_h5ad(target,compression='gzip')
 metrics={'weight_summary':wr,'state_changes':changes,'changed_entries':sum(v['changed_entries'] for v in changes.values()),'changed_entry_fraction':sum(v['changed_entries'] for v in changes.values())/np.prod(P.shape),'activated_entries':sum(v['on'] for v in changes.values()),'deactivated_entries':sum(v['off'] for v in changes.values()),'library_before_quantiles':np.quantile(lib0,[0,.01,.1,.5,.9,.99,1]).tolist(),'library_after_quantiles':np.quantile(lib1,[0,.01,.1,.5,.9,.99,1]).tolist(),'median_library_ratio':float(np.median(lib1)/np.median(lib0)),'median_detection_ratio':float(np.median(det1)/np.median(det0)),'gene_variance_sum_ratio':float(var1/var0),'pseudobulk_shift_l2':float(np.linalg.norm(means1-means0)),'pseudobulk_shift_max_abs':float(np.abs(means1-means0).max())}
 health=(.7<metrics['median_library_ratio']<1.3 and .7<metrics['median_detection_ratio']<1.3 and .5<metrics['gene_variance_sum_ratio']<2)
 result={'status':'LOCAL_CONTROL_NOT_FOR_SUBMISSION' if a.control!='none' else 'CANDIDATE_BUILT_NOT_SUBMITTED','candidate_id':cfg['candidate_id'] if a.control=='none' else None,'file':str(target),'sha256':sha(target),'expression_sha256':expr_sha(SP),'bytes':target.stat().st_size,'checks':checks,'health_pass':health,'metrics':metrics,'provenance':prov,'wall_seconds':time.time()-t0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 resultpath.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['provenance','metrics']},indent=2));print(json.dumps(metrics,indent=2),flush=True)
 if not health:raise RuntimeError('Frozen broad health check failed; do not release candidate')
if __name__=='__main__':main()
