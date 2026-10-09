"""Prespecified isolated components of the already frozen v0097 regularizer."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,time,resource,gc
from pathlib import Path
import numpy as np,anndata as ad
from scipy import sparse
from hurdle_margins import apply_hurdle
from normalization import restore_cp10k
from build_cp10k import sha,expr_sha,masses
from close_replicate_cp10k import exact_sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vework/t1ext'))
from label_means_const import COARSE


def main():
 p=argparse.ArgumentParser()
 for name in ['v94','v96','v97','raw-v97','carrier','weights','config','outdir']:p.add_argument('--'+name,required=True)
 a=p.parse_args();t=time.time();cfg=json.loads(Path(a.config).read_text());out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
 if (out/'submission.h5ad').exists() or (out/'BUILD.json').exists():raise FileExistsError('Immutable destination exists')
 for name in ['v94','v96','v97','raw_v97','carrier','weights']:assert sha(getattr(a,name))==cfg[name+'_sha256']
 parent=ad.read_h5ad(a.v94);ref=ad.read_h5ad(a.v96);v97=ad.read_h5ad(a.v97);raw=ad.read_h5ad(a.raw_v97);P=parent.X.toarray();car=np.load(a.carrier);C=car['X'];states=car['donor_types'].astype(str);w=np.load(a.weights)
 weights={g:(w[g+'|detection'],w[g+'|positive_level']) for g in sorted(set(k.split('|')[0] for k in w.files))}
 ones={g:(np.ones(P.shape[1]),np.ones(P.shape[1])) for g in weights}
 Z,_=apply_hurdle(P,C,states,COARSE,ones);assert np.array_equal(Z,P);del Z;endpoint,_=restore_cp10k(parent.X);assert exact_sparse(endpoint,ref.X);del endpoint
 both,_=apply_hurdle(P,C,states,COARSE,weights);assert exact_sparse(sparse.csr_matrix(both),raw.X);bothclosed,_=restore_cp10k(sparse.csr_matrix(both));assert exact_sparse(bothclosed,v97.X);del both,bothclosed,v97;gc.collect()
 component=cfg['component'];use={g:(x,np.ones_like(y)) if component=='detection' else (np.ones_like(x),y) for g,(x,y) in weights.items()}
 O,changes=apply_hurdle(P,C,states,COARSE,use);assert np.isfinite(O).all() and (O>=0).all()
 if component=='positive_level':assert np.array_equal(O>0,P>0)
 # Detection-only empirical positive values are evaluated at the new count's
 # midpoint ranks; calling that literal unchanged intensities would be false.
 rawX=sparse.csr_matrix(O);del O,P,C;gc.collect();X,_=restore_cp10k(rawX)
 disclosure=json.loads(raw.uns['external_data_disclosure'])
 for s in disclosure['external_sources']:
  if s['accession']=='GSM5820434':s['role']='Historical rejected joint-donor trial and current E8.5-fitted/E9.5-held-out assay-scale diagnostic and candidate-selection route; not an expression or weight input to this isolated-component candidate'
 prov={'candidate_id':cfg['candidate_id'],'configuration':cfg,'configuration_sha256':sha(a.config),'selection_reference':'exact v0096 r2','numerical_ancestry':'exact v0094, paired v0051 and exact frozen v0097 raw-library reliability weights','component':component,'weights_sha256':sha(a.weights),'opposite_component_weight':1,'both_enabled_exact_v97_preclosure_and_final':True,'both_disabled_exact_v94_then_v96':True,'detection_only_intensity_caveat':'Fixed parent conditional empirical positive shape, re-evaluated at changed positive count; values are not literally held pointwise','scientific_scope':'Bounded candidate selection, not inference of hidden target properties; previous gene-permuted source control was negative for specificity','code_sha256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('hurdle_margins.py'),Path(__file__).with_name('normalization.py')]},'complete_source_disclosure':disclosure}
 final=ad.AnnData(X,obs=parent.obs.copy(),var=parent.var.copy());final.uns['ve_contract']={'normalization':'log1p_normalized','task':'T1','board':'val'};final.uns['external_data_disclosure']=json.dumps(disclosure,sort_keys=True);final.uns['t1_hurdle_component_provenance']=json.dumps(prov,sort_keys=True);assert 'no other data' not in json.dumps(dict(final.uns)).lower();target=out/'submission.h5ad';final.write_h5ad(target,compression='gzip')
 pre=ad.AnnData(rawX,obs=parent.obs.copy(),var=parent.var.copy());pre.write_h5ad(out/'preclosure.h5ad',compression='gzip')
 m=masses(X);u=np.asarray(ref.X.astype(float).mean(0)).ravel();v=np.asarray(X.astype(float).mean(0)).ravel();vx=np.asarray(X.astype(float).power(2).mean(0)).ravel()-v*v;vr=np.asarray(ref.X.astype(float).power(2).mean(0)).ravel()-u*u;d0=np.asarray((ref.X>0).sum(1)).ravel();d1=np.asarray((X>0).sum(1)).ravel()
 result={'status':'CANDIDATE_BUILT_NOT_SUBMITTED','candidate_id':cfg['candidate_id'],'file':str(target),'sha256':sha(target),'expression_sha256':expr_sha(X),'bytes':target.stat().st_size,'shape':[5118,32285],'both_enabled_exact_v97_preclosure_and_final':True,'both_disabled_exact_v94_then_v96':True,'finite_nonnegative':True,'component':component,'state_changes':changes,'raw_changed_entries':sum(v['changed_entries'] for v in changes.values()),'activated_entries':sum(v['on'] for v in changes.values()),'deactivated_entries':sum(v['off'] for v in changes.values()),'detection_support_exact':bool(exact_sparse((X>0).astype(np.float32),(ref.X>0).astype(np.float32))),'row_mass_max_error':float(np.abs(m-10000).max()),'pseudobulk_l2_shift_vs_v96':float(np.linalg.norm(v-u)),'gene_variance_sum_ratio_vs_v96':float(vx.sum()/vr.sum()),'median_detection_ratio_vs_v96':float(np.median(d1)/np.median(d0)),'preclosure_sha256':sha(out/'preclosure.h5ad'),'provenance':prov,'wall_seconds':time.time()-t,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 assert result['row_mass_max_error']<.002 and .5<result['gene_variance_sum_ratio_vs_v96']<2
 (out/'BUILD.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['provenance','state_changes']},indent=2),flush=True)
if __name__=='__main__':main()
