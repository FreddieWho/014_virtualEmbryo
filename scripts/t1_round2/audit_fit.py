"""Validate fitted parameter provenance independently of prediction replay."""
import numpy as np
from scripts.t1_round2.models import load_old
from scripts.t1_round2.ops import abundance_step


def audit(model,a,ta,b,tb):
    lane=model['lane'];checks={}
    density=load_old('n1density',True)
    np.testing.assert_array_equal(model['density']['svd'].components_,density['svd'].components_)
    for t,g in density['groups'].items():
        np.testing.assert_array_equal(model['density']['groups'][t]['classifier'].coef_,g['classifier'].coef_)
        np.testing.assert_array_equal(model['density']['groups'][t]['classifier'].intercept_,g['classifier'].intercept_)
        np.testing.assert_array_equal(model['density']['groups'][t]['scaler'].mean_,g['scaler'].mean_)
        np.testing.assert_array_equal(model['density']['groups'][t]['scaler'].scale_,g['scaler'].scale_)
    checks['density_component_parameters']='PASS'
    if lane=='n1stack':
        original=load_old('o1mass',True)
        assert model['mass']['groups'].keys()==original['groups'].keys()
        for t,g in original['groups'].items():
            for j,m in g.items():
                for key in ['psource','pout','qsource','qout','positive_sorted']:
                    np.testing.assert_array_equal(model['mass']['groups'][t][j][key],m[key])
        checks['mass_component_parameters']='PASS'
    elif lane=='n2composition':
        ca=np.array([np.sum(ta==t) for t in model['labels']]);cb=np.array([np.sum(tb==t) for t in model['labels']]);p=model['cfg']['round2']['composition']
        np.testing.assert_array_equal(ca,model['counts_early']);np.testing.assert_array_equal(cb,model['counts_late'])
        np.testing.assert_array_equal(abundance_step(ca,cb,p['pseudocount'],p['strength'],p['ratio_cap']),[model['steps'][t] for t in model['labels']]);checks['full_stage_counts_and_rates']='PASS'
    elif lane in ['n3states','o1caldensity']:
        za=model['density']['svd'].transform(a);zb=model['density']['svd'].transform(b)
        for t,g in model['groups'].items():
            x=np.vstack([za[ta==t],zb[tb==t]]);y=np.r_[np.zeros(np.sum(ta==t)),np.ones(np.sum(tb==t))].astype(int)
            if lane=='n3states':
                labels=g['kmeans'].predict(g['scaler'].transform(x));k=len(g['step']);p=model['cfg']['round2']['states']
                ca=np.bincount(labels[y==0],minlength=k);cb=np.bincount(labels[y==1],minlength=k)
                np.testing.assert_array_equal(ca,g['early_counts']);np.testing.assert_array_equal(cb,g['late_counts'])
                np.testing.assert_array_equal(abundance_step(ca,cb,p['pseudocount'],p['strength'],p['weight_cap']),g['step'])
            else:
                np.testing.assert_array_equal(y,g['labels']);seen=[]
                for i,f in enumerate(g['fold_models']):
                    tr,te=f['train'],f['test'];assert not np.intersect1d(tr,te).size
                    np.testing.assert_array_equal(np.sort(np.r_[tr,te]),np.arange(len(x)));seen.extend(te)
                    np.testing.assert_array_equal(g['folds'][te],i)
                    logits=f['classifier'].decision_function(f['scaler'].transform(x[te]))
                    np.testing.assert_array_equal(logits,g['oof_logits'][te])
                np.testing.assert_array_equal(np.sort(seen),np.arange(len(x)))
        checks['full_training_states' if lane=='n3states' else 'full_OOF_predictions_and_disjoint_folds']='PASS'
    elif lane=='o2shrinkmass':
        original=load_old('o1mass',True)
        assert model['mass']['groups'].keys()==original['groups'].keys()
        n=0
        for t,g in original['groups'].items():
            for j,m in g.items():
                s=model['mass']['groups'][t][j]
                for k in ['psource','qsource','positive_sorted']:np.testing.assert_array_equal(s[k],m[k])
                assert min(s['qout'])>=0 and np.all(np.diff(s['qout'])>=0)
                assert min(m['psource'],m['pout'])-1e-6<=s['pout']<=max(m['psource'],m['pout'])+1e-6
                n+=1
        checks['full_unshrunk_fit_identity_and_monotone_shrink']={'status':'PASS','type_gene_models':n}
    return checks
