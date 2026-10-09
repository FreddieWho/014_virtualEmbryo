"""Reserved composition: approved single hurdle component, then frozen assay scale.

This builder does not decide eligibility or select the component. Its invocation
requires the parent's separate result-bound selection and exact input manifest.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,time,resource,gc
from pathlib import Path
import numpy as np,anndata as ad
from scipy import sparse
from assay_displacement import apply_displacement
from normalization import restore_cp10k
from build_cp10k import sha,expr_sha,masses
from close_replicate_cp10k import exact_sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vework/t1ext'))
from label_means_const import COARSE


def main():
 p=argparse.ArgumentParser()
 for n in ['v94','v98','raw-v98','component','raw-component','carrier','slopes','config','outdir']:p.add_argument('--'+n,required=True)
 a=p.parse_args();t=time.time();cfg=json.loads(Path(a.config).read_text());assert cfg['status']=='PARENT_SELECTED_COMPONENT_FOR_BUILD';assert cfg['selection_reference_sha256']==cfg['v98_sha256'] and cfg['numerical_parent_preclosure_sha256']==cfg['raw_component_sha256'];out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
 if (out/'submission.h5ad').exists() or (out/'BUILD.json').exists():raise FileExistsError('Immutable output exists')
 for n in ['v94','v98','raw_v98','component','raw_component','carrier','slopes']:assert sha(getattr(a,n))==cfg[n+'_sha256']
 p94=ad.read_h5ad(a.v94);v98=ad.read_h5ad(a.v98);r98=ad.read_h5ad(a.raw_v98);comp=ad.read_h5ad(a.component);raw=ad.read_h5ad(a.raw_component);c=np.load(a.carrier);C=c['X'];states=c['donor_types'].astype(str);s=np.load(a.slopes);slopes={g:s[g] for g in s.files}
 P=p94.X.toarray();single,_=apply_displacement(P,C,states,COARSE,slopes);assert exact_sparse(sparse.csr_matrix(single),r98.X);closed,_=restore_cp10k(sparse.csr_matrix(single));assert exact_sparse(closed,v98.X);del P,single,closed,p94,r98;gc.collect()
 P=raw.X.toarray();ones={g:np.ones(P.shape[1]) for g in slopes};identity,_=apply_displacement(P,C,states,COARSE,ones);assert np.array_equal(identity,P);closed,_=restore_cp10k(sparse.csr_matrix(identity));assert exact_sparse(closed,comp.X);del identity,closed,comp;gc.collect()
 O,changes=apply_displacement(P,C,states,COARSE,slopes);assert np.array_equal(O>0,P>0) and np.isfinite(O).all()
 keys=['positive_values','floored','adjacent_steps','negative_steps','reordered','repair_changed_values','rank_distance_sum','repair_abs_sum','changed_entries'];total={k:sum(v[k] for v in changes.values()) for k in keys}
 for k in ['rank_distance_max','repair_abs_max']:total[k]=max(v[k] for v in changes.values())
 n=max(total['positive_values'],1);total.update(floor_fraction=total['floored']/n,negative_step_fraction=total['negative_steps']/max(total['adjacent_steps'],1),reordered_fraction=total['reordered']/n,mean_rank_distance=total['rank_distance_sum']/n,mean_abs_repair=total['repair_abs_sum']/n)
 (out/'OPERATOR_AUDIT.json').write_text(json.dumps({'aggregate':total,'states':changes},indent=2));assert total['floor_fraction']<=.01,'Frozen floor gate failed; no final artifact'
 rawX=sparse.csr_matrix(O);del O,P,C;gc.collect();X,_=restore_cp10k(rawX)
 disclosure=json.loads(v98.uns['external_data_disclosure'])
 for s in disclosure['external_sources']:
  if s['accession'] in ['GSM7226268','GSM7226269']:s['role']='Direct E8.5-only assay scale fit and direct frozen raw-library reliability weights; inherited temporal field'
  if s['accession'] in ['GSM7226272','GSM7226273']:s['role']='Direct frozen raw-library reliability weights and inherited temporal field/support masks; no assay slope fit'
 prov={'candidate_id':cfg['candidate_id'],'numerical_parent_candidate':cfg['numerical_parent_candidate'],'numerical_parent_preclosure_sha256':cfg['numerical_parent_preclosure_sha256'],'selection_reference_candidate':cfg['selection_reference_candidate'],'selection_reference_sha256':cfg['selection_reference_sha256'],'configuration':cfg,'configuration_sha256':sha(a.config),'component_disabled_exact_v98_before_and_after_closure':True,'assay_disabled_exact_selected_component_before_and_after_closure':True,'no_new_fitted_parameter':True,'normalization':'same fixed CP10k closure','operator_order':'selected single component then frozen assay displacement then CP10k','code_sha256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('assay_displacement.py'),Path(__file__).with_name('normalization.py')]},'repair_audit':total,'full_source_disclosure':disclosure,'scientific_scope':'Candidate-selection composition, not hidden-target-property inference or causal source calibration'}
 final=ad.AnnData(X,obs=v98.obs.copy(),var=v98.var.copy());final.uns['ve_contract']={'normalization':'log1p_normalized','task':'T1','board':'val'};final.uns['external_data_disclosure']=json.dumps(disclosure,sort_keys=True);final.uns['t1_component_assay_provenance']=json.dumps(prov,sort_keys=True);assert 'no other data' not in json.dumps(dict(final.uns)).lower();target=out/'submission.h5ad';final.write_h5ad(target,compression='gzip');ad.AnnData(rawX,obs=v98.obs.copy(),var=v98.var.copy()).write_h5ad(out/'preclosure.h5ad',compression='gzip')
 m=masses(X);u=np.asarray(v98.X.astype(float).mean(0)).ravel();v=np.asarray(X.astype(float).mean(0)).ravel();vx=np.asarray(X.astype(float).power(2).mean(0)).ravel()-v*v;vr=np.asarray(v98.X.astype(float).power(2).mean(0)).ravel()-u*u
 result={'status':'CANDIDATE_BUILT_NOT_SUBMITTED','candidate_id':cfg['candidate_id'],'file':str(target),'sha256':sha(target),'expression_sha256':expr_sha(X),'bytes':target.stat().st_size,'shape':[5118,32285],'exact_disabled_endpoints':True,'detection_support_exact_selected_component':True,'row_mass_max_error':float(np.abs(m-10000).max()),'pseudobulk_l2_shift_vs_v98':float(np.linalg.norm(v-u)),'gene_variance_sum_ratio_vs_v98':float(vx.sum()/vr.sum()),'repair_audit':total,'preclosure_sha256':sha(out/'preclosure.h5ad'),'provenance':prov,'wall_seconds':time.time()-t,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 assert result['row_mass_max_error']<.002 and .5<result['gene_variance_sum_ratio_vs_v98']<2
 (out/'BUILD.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='provenance'},indent=2),flush=True)
if __name__=='__main__':main()
