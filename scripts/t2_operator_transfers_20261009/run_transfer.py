#!/usr/bin/env python3
"""Frozen heart-specific transfer of embryo v21's margin-preserving operator.

Only legal released heart expression is fitted. The original embryo coefficient
matrix is never read. --mode holdout does not expose E8.75 to the fit or builder.
Run each mode in a fresh process; numerical libraries are pinned to one thread.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[k] = '1'
os.environ['NUMBA_NUM_THREADS']='1'
import sys
sys.dont_write_bytecode=True
import argparse, hashlib, json, time
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import anndata as ad
from threadpoolctl import threadpool_limits, threadpool_info

HERE = Path(__file__).resolve().parent
REPO = HERE.parent/'repo'
sys.path.insert(0,str(REPO/'scripts/t2_embryo_campaign_20261009'))
from runtime import initialize
from copula import fit_conditional, regularize
BOARD='T2:heart:val_interp'
EXPECTED_PARENT='7cc2e31445613a7e9e13525ea3b3ce8bf386855f8df0b70d6ba47f1ae2a23a37'


def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def write_json(p,x):
    p.write_text(json.dumps(x,indent=2,default=str)+'\n')


def get_args():
    p=argparse.ArgumentParser()
    p.add_argument('--data',required=True)
    p.add_argument('--mode',required=True,choices=['parent','holdout','final'])
    p.add_argument('--outdir',required=True)
    p.add_argument('--parent')
    p.add_argument('--parent-sha256',default=EXPECTED_PARENT)
    return p.parse_args()


def arrays(a):
    return np.asarray(a.X.toarray() if hasattr(a.X,'toarray') else a.X)


def audit(base,out):
    X,Y=arrays(base),arrays(out)
    labels=np.asarray(base.obs.celltype).astype(str)
    check={
      'state_gene_marginals_exact':all(np.array_equal(np.sort(X[labels==s],axis=0),np.sort(Y[labels==s],axis=0)) for s in sorted(set(labels))),
      'global_gene_marginals_exact':np.array_equal(np.sort(X,axis=0),np.sort(Y,axis=0)),
      'obs_exact':base.obs.equals(out.obs), 'var_exact':base.var.equals(out.var),
      'coordinates_exact':all(np.array_equal(base.obsm[k],out.obsm[k]) for k in base.obsm),
      'obs_names_order_exact':base.obs_names.equals(out.obs_names),
      'var_names_order_exact':base.var_names.equals(out.var_names),
      'finite_nonnegative':bool(np.isfinite(Y).all() and (Y>=0).all()),
      'changed_entries_fraction':float(np.mean(X!=Y)),
      'coordinate_row_order_retained':True,
      'cell_library_not_invariant':True,
      'classifier_derived_mass_not_invariant':True}
    lib0=np.expm1(X.astype(np.float64)).sum(1);lib1=np.expm1(Y.astype(np.float64)).sum(1)
    rel=np.abs(lib1-lib0)/np.maximum(lib0,1e-12)
    check['library_size_change']={'changed_cell_fraction':float(np.mean(lib0!=lib1)),'mean_abs_relative':float(rel.mean()),'median_abs_relative':float(np.median(rel)),'p95_abs_relative':float(np.quantile(rel,.95)),'max_abs_relative':float(rel.max())}
    for key in ('state_gene_marginals_exact','global_gene_marginals_exact','obs_exact','var_exact','coordinates_exact','obs_names_order_exact','var_names_order_exact','finite_nonnegative'):
        assert check[key],key
    return check


def classifier_diag(probe,base,out):
    p0=probe.predict_proba(arrays(base));p1=probe.predict_proba(arrays(out))
    mass0=p0.mean(0);mass1=p1.mean(0)
    return {'probe_role':'diagnostic only; predictions do not enter candidate generation',
       'classes':list(map(str,probe.classes_)),
       'parent_soft_mass':mass0.tolist(),'output_soft_mass':mass1.tolist(),
       'soft_mass_total_variation':float(np.abs(mass1-mass0).sum()/2),
       'hard_label_change_fraction':float(np.mean(p0.argmax(1)!=p1.argmax(1)))}


def parent_recipe(r,holdout=False):
    params=NS(board=BOARD,left='E8.25_late:8.25',right='E9.5:9.5' if holdout else 'E8.75:8.75',target=8.75 if holdout else 8.5,n=5872,seed=20261008,label='celltype',carrier='left',C=2.,geometry='aniso',zero_preserve=False)
    return r.run_interp(params)


def main():
    t0=time.time();a=get_args();outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True)
    v,init_provenance=initialize(a.data)
    import t2_recipes as r
    from backtest import Board
    genes=v.panel(BOARD)
    assert len(genes)==500 and len(set(genes))==500,'Must use exact500 unique heart panel'
    result={'board':BOARD,'mode':a.mode,'data_init':init_provenance,'protected_target_read':False,'embryo_data_or_B_read':False,'source_code':{str(p.relative_to(REPO)):sha(p) for p in [REPO/'scripts/t2_embryo_campaign_20261009/copula.py',REPO/'scripts/vework/t2_recipes.py',REPO/'scripts/vework/backtest.py',REPO/'scripts/vework/vecommon.py']},'threadpools':threadpool_info(),'parameter_search':False,'status':'RUNNING'}
    if a.mode=='parent':
        base,prov=parent_recipe(r)
        # The published source added this metadata field later for embryo E3.
        # Restoring its absence reproduces the historic H1 entire-file hash.
        legacy_prov=json.loads(base.uns['ve_provenance']);legacy_prov.pop('carrier')
        base.uns['ve_provenance']=json.dumps(legacy_prov,default=str)
        result['metadata_restoration']='Remove only ve_provenance.carrier, introduced after historical H1; no expression, coordinates, obs, var or other changes'
        path=outdir/'T2_heart_val_interp__H1_bridgeC2_aniso.h5ad'
        assert not path.exists(),'No overwrite of frozen parent'
        base.write_h5ad(path)
        result.update({'artifact':str(path),'sha256':sha(path),'expected_sha256':EXPECTED_PARENT,'byte_identity_verified':sha(path)==EXPECTED_PARENT,'recipe':prov,'contract':v.format_check(path,BOARD)})
        result['status']='COMPLETE';write_json(outdir/'PARENT_REPRODUCTION.json',result)
        print(json.dumps(result,indent=2));return
    stages=['E8.25_late','E9.5'] if a.mode=='holdout' else ['E8.25_late','E8.75']
    stages_ad=[v.load_stage(s,genes) for s in stages]
    fit_X=np.vstack([arrays(s) for s in stages_ad])
    result['fit_sources']=[{'stage':s,'path':str(Path(a.data)/(s+'.h5ad')),'sha256':sha(Path(a.data)/(s+'.h5ad')),'n_obs':int(x.n_obs),'n_vars_aligned':int(x.n_vars)} for s,x in zip(stages,stages_ad)]
    if a.mode=='holdout':
        base,prov=parent_recipe(r,True);result['parent_recipe']=prov
        result['fold']='Released E8.25_late + E9.5 predict E8.75; entire held-out stage excluded from recipe and copula fit'
    else:
        assert a.parent,'Final candidate requires chosen parent path'
        assert sha(a.parent)==a.parent_sha256,'Chosen parent does not match approved hash'
        base=ad.read_h5ad(a.parent)
        result['parent']={'path':a.parent,'sha256':sha(a.parent),'official_file':'T2_heart_val_interp__H1_bridgeC2_aniso.h5ad','official_model':'bridgeC2-r2','official_id':'d0fd25a74fed4aeabaa4e9fe128bfa74'}
    assert list(base.var_names)==genes,'Parent panel differs'
    assert 1000<=base.n_obs<=17616
    B,fit=fit_conditional(fit_X)
    np.save(outdir/'heart_B.npy',B,allow_pickle=False)
    result['fit']=fit;result['B_file']={'path':str(outdir/'heart_B.npy'),'sha256':sha(outdir/'heart_B.npy')}
    perm=np.random.default_rng(20261009).permutation(len(genes));np.save(outdir/'gene_shuffle_permutation.npy',perm)
    # A feature-identity shuffle of the same full-rank model. Equivalent to fitting
    # permuted columns up to numerical reduction ties, avoiding redundant fitting.
    shuffled_B=B[np.ix_(perm,perm)]
    result['shuffle_control']='B simultaneously permuted on both gene axes, fixed seed20261009; same coefficient multiset/eigenspectrum, gene identities deliberately incorrect'
    pred={'parent':base};result['arms']={}
    for name,bb in [('heart_copula',B),('gene_shuffle_control',shuffled_B)]:
        out=base.copy();out.X,operator_audit=regularize(arrays(base),base.obs.celltype,bb)
        checks=audit(base,out)
        replay,_=regularize(arrays(base),base.obs.celltype,bb)
        checks['same_process_array_replay_exact']=bool(np.array_equal(out.X,replay));assert checks['same_process_array_replay_exact']
        metadata={'mechanism':'heart_specific_v21_copula_transfer','fit_stages':stages,'fit':fit,'parent_sha256':result.get('parent',{}).get('sha256'),'control':name=='gene_shuffle_control','operator_audit':operator_audit,'per_cell_libraries_and_classifier_mass_not_invariants':True}
        out.uns['heart_copula_provenance']=json.dumps(metadata,sort_keys=True)
        path=outdir/('t2_hrt_int__heart_copula__v0025.h5ad' if a.mode=='final' and name=='heart_copula' else name+'.h5ad')
        assert not path.exists(),'No overwrite of output'
        out.write_h5ad(path)
        result['arms'][name]={'path':str(path),'sha256':sha(path),'checks':checks,'operator_audit':operator_audit,'contract':v.format_check(path,BOARD)}
        assert result['arms'][name]['contract']['pass']
        pred[name]=out;print(name,'built',checks['changed_entries_fraction'],flush=True)
    if a.mode=='holdout':
        # The held-out expression enters only evaluation after predictions freeze.
        T=v.load_stage('E8.75',genes)
        result['evaluation_stage']={'name':'E8.75','sha256':sha(Path(a.data)/'E8.75.h5ad'),'used_for_model_fitting':False}
        result['arms']['parent']={'evaluation':[]}
        for seed in [0,1,2]:
            board=Board('T2',genes,T,stages_ad[0],seed)
            for name,P in pred.items():
                raw=board.raw(P);sk=board.skills(raw)
                result['arms'][name].setdefault('evaluation',[]).append({'seed':seed,'raw':raw,'skills':sk,'floor':board.floor,'ceiling':board.ceil})
                if name!='parent':result['arms'][name].setdefault('classifier_diagnostics',[]).append({'seed':seed,**classifier_diag(board.probe,base,P)})
                print(seed,name,sk,flush=True)
                write_json(outdir/'RESULT.json',result)
        for name,arm in result['arms'].items():
            arm['mean_skills']={k:float(np.mean([row['skills'][k] for row in arm['evaluation']])) for k in arm['evaluation'][0]['skills']}
            arm['median_total']=float(np.median([row['skills']['TOTAL'] for row in arm['evaluation']]))
    else:
        import score_h5ad as sh
        metrics,_=sh._load_task_metrics('T2')
        lab=np.concatenate([np.asarray(s.obs.celltype).astype(str) for s in stages_ad])
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        with warnings.catch_warnings(record=True) as probe_warnings:
            warnings.simplefilter('always')
            probe=metrics.train_frozen_probe(fit_X,lab,seed=20261009)
        convergence=[str(w.message) for w in probe_warnings if issubclass(w.category,ConvergenceWarning)]
        result['classifier_probe_convergence']={'status':'ITERATION_LIMIT_REACHED' if convergence else 'NO_CONVERGENCE_WARNING','max_iter':300,'warnings':convergence,'role':'diagnostic only; frozen candidate built before probe fit, probe does not enter output','consequence':'soft-mass and hard-label change values are approximate diagnostic outputs, not precise mechanism evidence or server predictions'}
        for name in ['heart_copula','gene_shuffle_control']:
            result['arms'][name]['classifier_diagnostic']=classifier_diag(probe,base,pred[name])
        result['classifier_warning']='This released-heart-trained diagnostic probe is not the hidden target server probe; no claim of invariant or superior classifier mass.'
    result['seconds']=time.time()-t0;result['status']='COMPLETE'
    result['official_score_status']='NOT_SUBMITTED_NOT_SCORED'
    result['threadpools_after']=threadpool_info()
    write_json(outdir/'RESULT.json',result)
    print('COMPLETE',a.mode,'seconds',result['seconds'],flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
