"""One-time post-selection source holdout check; never used to tune the run."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import anndata as ad
import numpy as np
from scipy import sparse
from sklearn.linear_model import Ridge

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'artifacts/autoresearch/t3-20261002-v1'
OUT=ROOT/'reports/t3_autoresearch_20261002'
sys.path.insert(0,str(ROOT/'scripts'))
from t3_next.source_roles import require_response_role


def metrics(pred,truth):
    pred=np.asarray(pred,dtype=float);truth=np.asarray(truth,dtype=float)
    mse=np.mean((pred-truth)**2,axis=1)
    cosine=np.sum(pred*truth,axis=1)/np.maximum(np.linalg.norm(pred,axis=1)*np.linalg.norm(truth,axis=1),1e-12)
    return {'mse':float(mse.mean()),'per_perturbation_mse':mse.tolist(),'mean_cosine':float(cosine.mean())}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'FINAL_CHECK.json').exists(), 'Final check is immutable; do not re-open for tuning'
    history=[json.loads(s) for s in (RUN/'autoresearch-results/events.jsonl').read_text().splitlines()]
    assert history[-1]['event']=='complete'
    events=[e for e in history if e.get('event')=='iteration']
    assert events[-1]['retained_metric']>=20 and events[-1]['guard']=='pass'
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=RUN,text=True).strip()
    assert head==events[-1]['head']
    dirty=subprocess.check_output(['git','status','--porcelain'],cwd=RUN,text=True).splitlines()
    # The controller owns an intentionally untracked results directory.
    assert all(line=='?? autoresearch-results/' for line in dirty),dirty
    for path,digest in json.loads((RUN/'FROZEN.json').read_text()).items():
        assert hashlib.sha256((RUN/path).read_bytes()).hexdigest()==digest,path
    model_hash=hashlib.sha256((RUN/'model.py').read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('t3_retained_autoresearch',RUN/'model.py')
    model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    manifest=json.loads((ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json').read_text())
    require_response_role(manifest,ROOT,'SIGNED_RESPONSE')
    path=ROOT/manifest['files']['expression']['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['files']['expression']['sha256']
    a=ad.read_h5ad(path)
    assert a.shape==(5454,500) and a.obs.model_input.all()
    x=a.X.toarray() if sparse.issparse(a.X) else np.asarray(a.X)
    labels=a.obs.condition.astype(str).to_numpy();samples=a.obs['sample'].astype(str).to_numpy()
    ss=sorted(set(samples));ctrl=x[labels=='ctrl'].mean(0)
    sample_ctrl=np.array([x[(labels=='ctrl')&(samples==s)].mean(0) for s in ss])
    cfg=json.loads((RUN/'PROVENANCE.json').read_text())
    epath=ROOT/'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert hashlib.sha256(epath.read_bytes()).hexdigest()==cfg['embedding_sha256']
    emb=np.load(epath);ei={g:i for i,g in enumerate(emb['genes'])}
    def data(genes):
        return {'E':emb['embedding'][[ei[g] for g in genes]],
                'Y':np.array([x[labels==g].mean(0)-ctrl for g in genes]),
                'N':np.array([np.sum(labels==g) for g in genes]),
                'SEM2':np.array([x[labels==g].var(0,ddof=1)/np.sum(labels==g) for g in genes]),
                'sample_Y':np.array([[x[(labels==g)&(samples==s)].mean(0)-sample_ctrl[k] for k,s in enumerate(ss)] for g in genes]),
                'sample_N':np.array([[np.sum((labels==g)&(samples==s)) for s in ss] for g in genes]),
                'genes':np.array(genes),'ctrl':ctrl,'sample_ctrl':sample_ctrl,'panel':a.var_names.to_numpy(dtype=str)}
    train=data(cfg['split']['train'])
    # Ensure this final-check training input matches frozen development exactly.
    frozen=np.load(RUN/'development.npz')
    for key in ['E','Y','N','SEM2','sample_Y','sample_N','ctrl','sample_ctrl']:
        np.testing.assert_array_equal(train[key],frozen[key])
    baseline=Ridge(alpha=10).fit(train['E'],train['Y'])
    result={'schema':'t3.autoresearch.post-selection.v1','task':'T3 source-domain response prediction',
            'run_id':events[-1]['run_id'],'model_commit':head,'model_sha256':model_hash,
            'experiments':events[-1]['iteration'],'development_improvement_pct':events[-1]['retained_metric'],
            'fixed_training_genes':cfg['split']['train'],'target_Gata4_truth_used':False,
            'no_more_model_selection_after_this_check':True,
            'holdout_limitations':['source domain only','historical test was evaluated in earlier project runs; not pristine',
                                   'two samples, independent animals unestablished','17-condition development score selected after48 adaptive trials']}
    arrays={}
    for split in ['val','test']:
        genes=cfg['split'][split];truth=data(genes)['Y']
        query={'E':emb['embedding'][[ei[g] for g in genes]],'genes':np.array(genes)}
        pred=np.asarray(model.predict(train,query),dtype=float)
        assert pred.shape==truth.shape and np.isfinite(pred).all()
        ref=baseline.predict(query['E'])
        zero=np.zeros_like(truth);mean=np.repeat(train['Y'].mean(0)[None,:],len(genes),0)
        row={'genes':genes,'retained_model':metrics(pred,truth),'GO128_ridge10':metrics(ref,truth),
             'training_mean':metrics(mean,truth),'identity':metrics(zero,truth)}
        row['improvement_vs_GO_ridge_pct']=100*(1-row['retained_model']['mse']/row['GO128_ridge10']['mse'])
        result[split]=row
        arrays.update({split+'_prediction':pred,split+'_truth':truth,split+'_baseline':ref})
    # Uncertainty uses perturbations, not500 output genes as independent replicates.
    test=result['test'];delta=np.array(test['GO128_ridge10']['per_perturbation_mse'])-np.array(test['retained_model']['per_perturbation_mse'])
    rng=np.random.default_rng(20261002);boot=delta[rng.integers(0,len(delta),size=(10000,len(delta)))].mean(1)
    result['test_uncertainty']={'unit':'perturbation gene','wins':int(np.sum(delta>0)),
                                'n':len(delta),'paired_mean_mse_reduction':float(delta.mean()),
                                'descriptive_bootstrap_95pct':np.quantile(boot,[.025,.975]).tolist(),
                                'not_independent_animal_confidence_interval':True}
    all_genes=sum(cfg['split'].values(),[])
    final_train=data(all_genes)
    q={'genes':np.array(['Gata4']),'E':emb['embedding'][[ei['Gata4']]]}
    gata=np.asarray(model.predict(final_train,q),dtype=float)
    assert gata.shape==(1,500) and np.isfinite(gata).all()
    ids=[model.GENES.index(g) for g in all_genes];gid=model.GENES.index('Gata4')
    complex_sim=model.KERNEL[gid,ids];go_sim=q['E']@final_train['E'].T
    result['gata4_applicability']={'refit_conditions':len(all_genes),'specific_complex_max_similarity':float(complex_sim.max()),
                                  'specific_complex_support_count':int(np.sum(complex_sim>1e-8)),
                                  'GO128_max_similarity':float(go_sim.max()),
                                  'high_confidence_GO_gate_active':bool(go_sim.max()>.9),
                                  'prediction_l2':float(np.linalg.norm(gata)),
                                  'role':'source-scale research prediction only; not an embryo candidate or validation',
                                  'candidate_generated':False,'uploaded':False,'server_score':'NOT_RUN'}
    arrays['gata4_source_scale_prediction']=gata
    np.savez_compressed(OUT/'POST_SELECTION_ARRAYS.npz',**arrays)
    result['arrays_sha256']=hashlib.sha256((OUT/'POST_SELECTION_ARRAYS.npz').read_bytes()).hexdigest()
    assert hashlib.sha256((RUN/'model.py').read_bytes()).hexdigest()==model_hash
    (OUT/'FINAL_CHECK.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['development_improvement_pct','val','test','test_uncertainty','gata4_applicability']},indent=2))


if __name__=='__main__':main()
