"""Frozen positive-displacement-scale test, with complete operator health audit."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,time,resource,gc
from pathlib import Path
import numpy as np,anndata as ad
from scipy import sparse
from assay_displacement import apply_displacement
from replicate_weights import IEG
from normalization import restore_cp10k
from build_cp10k import sha,expr_sha,masses,sources
from close_replicate_cp10k import exact_sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vework/t1ext'))
from label_means_const import COARSE


def select_slopes(model,stats,cfg):
 genes=stats['genes'].astype(str);assert np.array_equal(genes,model['genes'])
 early=sorted(set(k.split('|')[0] for k in stats.files if k.startswith('GSM') and 'E8_5' in k));late=sorted(set(k.split('|')[0] for k in stats.files if k.startswith('GSM') and 'E14_5' in k))
 def pooled(ss,g):
  n=np.array([stats[s+'|'+g+'|n'] for s in ss]);m=np.stack([stats[s+'|'+g+'|mean'] for s in ss]);return (n[:,None]*m).sum(0)/max(n.sum(),1)
 cm=np.maximum(pooled(late,'CM_V'),pooled(late,'CM_A'));glob=np.array([g.startswith(('Hba','Hbb','mt-')) or g in IEG or g=='Malat1' for g in genes]);out={};audit={}
 for g in cfg['groups']:
  bad=glob.copy();m8=pooled(early,g);m14=pooled(late,g)
  if not g.startswith('CM'):bad|=(cm>4*np.maximum(m14,1e-3))&(cm>.3)
  eligible=stats['in_all_external']&~bad&((m8>=.02)|(m14>=.02))&model[g+'|fit_eligible']
  b=np.ones(len(genes));b[eligible]=model[g+'|slope'][eligible];out[g]=b
  audit[g]={'source_fitted_genes':int(model[g+'|fit_eligible'].sum()),'target_eligible_genes':int(eligible.sum()),'slope_quantiles':np.quantile(b[eligible],[0,.1,.5,.9,1]).tolist() if eligible.any() else [],'above_one':int((b>1).sum()),'below_one':int((b<1).sum())}
 return out,audit


def main():
 ap=argparse.ArgumentParser()
 for k in ['v94','v96','carrier','stats','model','assay-result','config','outdir']:ap.add_argument('--'+k,required=True)
 a=ap.parse_args();t=time.time();cfg=json.loads(Path(a.config).read_text());root=Path(a.outdir);root.mkdir(parents=True,exist_ok=True);target=root/'submission.h5ad'
 if target.exists() or (root/'BUILD.json').exists():raise FileExistsError('Immutable destination exists')
 assert sha(a.v94)==cfg['numerical_parent_sha256'] and sha(a.v96)==cfg['selection_reference_sha256'] and sha(a.carrier)==cfg['paired_carrier_sha256']
 assay=json.loads(Path(a.assay_result).read_text());assert assay['status']=='PASS_SOURCE_TRANSPORTABILITY_GATE'
 parent=ad.read_h5ad(a.v94);v96=ad.read_h5ad(a.v96);endpoint,_=restore_cp10k(parent.X);assert exact_sparse(endpoint,v96.X);del endpoint
 P=parent.X.toarray();carrier=np.load(a.carrier);C=carrier['X'];states=carrier['donor_types'].astype(str);assert P.shape==C.shape==(5118,32285)
 model=np.load(a.model);stats=np.load(a.stats);slopes,sa=select_slopes(model,stats,cfg);np.savez_compressed(root/'TARGET_SLOPES.npz',**slopes)
 one={g:np.ones(P.shape[1]) for g in slopes};identity,_=apply_displacement(P,C,states,COARSE,one);assert np.array_equal(identity,P);del identity;gc.collect()
 O,changes=apply_displacement(P,C,states,COARSE,slopes);assert np.isfinite(O).all() and (O>=0).all() and np.array_equal(O>0,P>0)
 additive=['positive_values','floored','adjacent_steps','negative_steps','reordered','repair_changed_values','rank_distance_sum','repair_abs_sum','changed_entries'];total={k:sum(v[k] for v in changes.values()) for k in additive}
 for k in ['rank_distance_max','repair_abs_max']:total[k]=max(v[k] for v in changes.values())
 n=max(total['positive_values'],1);total.update(floor_fraction=total['floored']/n,negative_step_fraction=total['negative_steps']/max(total['adjacent_steps'],1),reordered_fraction=total['reordered']/n,repair_changed_value_fraction=total['repair_changed_values']/n,mean_rank_distance=total['rank_distance_sum']/n,mean_abs_repair=total['repair_abs_sum']/n,changed_full_matrix_fraction=total['changed_entries']/P.size)
 (root/'OPERATOR_AUDIT.json').write_text(json.dumps({'aggregate':total,'states':changes,'slopes':sa},indent=2))
 if total['floor_fraction']>.01:raise RuntimeError('Frozen floor gate failed; no target artifact created')
 raw=sparse.csr_matrix(O);del O,P,C;gc.collect();raw_ad=ad.AnnData(raw,obs=parent.obs.copy(),var=parent.var.copy());raw_ad.write_h5ad(root/'preclosure.h5ad',compression='gzip');X,_=restore_cp10k(raw);assert np.array_equal(X.indptr,parent.X.indptr) and np.array_equal(X.indices,parent.X.indices)
 disclosure=sources()
 for s in disclosure['official_sources']:
  if s['stage']=='E8.5':s['role']='Inherited carrier input; direct source-only classifier and positive-SD scale fit; source classifier held-out check'
  else:s['role']='Inherited carrier input; held-out E9.5 source assay labels/moments and full-panel diagnostics only; not new classifier or slope fit'
 for s in disclosure['external_sources']:
  if s['accession'] in ['GSM7226268','GSM7226269']:s['role']='Direct E8.5-only expression/moment calibration with separate libraries; inherited v0094 temporal field input'
  elif s['accession'] in ['GSM7226272','GSM7226273']:s['role']='Inherited v0094 late temporal field; pooled means reproduce inherited target support masks; no new slope fit'
  elif s['accession']=='GSM5820434':s['role']='Held-out-stage cross-study E9.5 assay, using a fresh E8.5-only classifier; measured-gene availability metadata restricts common fitting panel, no E9.5 expression/labels/moments fit new parameters; historical rejected v0095 joint-donor route'
 prov={'candidate_id':cfg['candidate_id'],'configuration':cfg,'configuration_sha256':sha(a.config),'selection_reference_v96_sha256':sha(a.v96),'numerical_v94_sha256':sha(a.v94),'carrier_sha256':sha(a.carrier),'model_sha256':sha(a.model),'replicate_stats_sha256':sha(a.stats),'assay_result_sha256':sha(a.assay_result),'target_slopes_sha256':sha(root/'TARGET_SLOPES.npz'),'preclosure_sha256':sha(root/'preclosure.h5ad'),'code_sha256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('assay_displacement.py'),Path(__file__).with_name('hurdle_margins.py'),Path(__file__).with_name('normalization.py')]},'slope1_endpoint_exact_v94':True,'slope1_endpoint_then_closure_exact_v96':True,'detection_support_exact_v94_v96':True,'coarse_mapping_scope':'Fresh E8.5-only classifier determines E8.5 slope-fit populations and external E9.5 assay labels. Target rows retain inherited paired v0051 fine labels; broad-group names match, fitted cell populations differ. No E9.5 outcome-based state or gene selection. E9.5 measured-panel availability metadata is used.','operator_audit':total,'full_source_disclosure':disclosure}
 final=ad.AnnData(X,obs=parent.obs.copy(),var=parent.var.copy());final.uns['ve_contract']={'normalization':'log1p_normalized','task':'T1','board':'val'};final.uns['external_data_disclosure']=json.dumps(disclosure,sort_keys=True);final.uns['t1_assay_displacement_provenance']=json.dumps(prov,sort_keys=True);assert 'no other data' not in json.dumps(dict(final.uns)).lower();final.write_h5ad(target,compression='gzip')
 m=masses(X);mean=np.asarray(X.astype(float).mean(0)).ravel();ref=np.asarray(v96.X.astype(float).mean(0)).ravel();vf=np.asarray(X.astype(float).power(2).mean(0)).ravel()-mean**2;vr=np.asarray(v96.X.astype(float).power(2).mean(0)).ravel()-ref**2
 result={'status':'CANDIDATE_BUILT_NOT_SUBMITTED','candidate_id':cfg['candidate_id'],'file':str(target),'sha256':sha(target),'expression_sha256':expr_sha(X),'bytes':target.stat().st_size,'shape':[5118,32285],'finite_nonnegative':bool(np.isfinite(X.data).all() and (X.data>0).all()),'detection_support_preserved':True,'row_mass_max_error':float(np.abs(m-10000).max()),'pseudobulk_l2_shift_vs_v96':float(np.linalg.norm(mean-ref)),'gene_variance_sum_ratio_vs_v96':float(vf.sum()/vr.sum()),'operator_audit':total,'slope_audit':sa,'provenance':prov,'wall_seconds':time.time()-t,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 assert result['finite_nonnegative'] and result['row_mass_max_error']<.002
 (root/'BUILD.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='provenance'},indent=2),flush=True)
if __name__=='__main__':main()
