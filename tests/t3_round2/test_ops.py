import numpy as np
from scripts.t3_round2.ops import gene_shrink,occupancy_decode
from scripts.t3_next.repair_ops import decode_rate


def test_stack_zero_rate_identity_and_nonnegative():
    h=np.array([[0.,.3],[1.,2.]])
    np.testing.assert_array_equal(decode_rate(h,np.zeros(2)),h)
    out=decode_rate(h,np.array([.1,-.2]));assert (out>=0).all() and out[0,0]==0


def test_gene_shrink_retains_heterogeneous_signal():
    mean=np.zeros((5,2));pred=np.ones((5,2));truth=np.column_stack([np.ones(5),-np.ones(5)])
    w,global_w,tau=gene_shrink(mean,pred,truth,1.)
    assert global_w==0 and w[0]>0 and w[1]==0 and tau>0
    w,g,t=gene_shrink(mean,mean,truth);assert g==0 and np.all(w==0)


def test_occupancy_identity_and_support_changes():
    x=np.column_stack([np.r_[np.zeros(10),np.ones(10)],np.ones(20)])
    groups=np.array(['a']*20)
    np.testing.assert_array_equal(occupancy_decode(x,np.zeros(4),groups),x)
    out=occupancy_decode(x,np.array([1.,0.,0.,0.]),groups,strength=1.)
    assert (out[:,0]>0).sum()>10 and np.isfinite(out).all() and (out>=0).all()
    np.testing.assert_array_equal(out[:,1],x[:,1])
    absent=np.zeros((20,2));np.testing.assert_array_equal(occupancy_decode(absent,np.ones(4),groups),absent)


def test_orthogonal_null_cannot_use_test_labels():
    from scripts.t3_round2.models import orth_fit,orth_prediction
    rng=np.random.default_rng(7);x=rng.uniform(size=(90,6));z=rng.normal(size=(90,3));types=np.array(['a']*45+['b']*45);blocks=np.arange(90)%3
    cfg={'context_ridge':10.,'orthogonal_slope_ridge':10.}
    model=orth_fit(x,0,z,types,blocks,cfg,1)
    before,_=orth_prediction(model,x[:8,0],z[:8],types[:8])
    x[:,1:]=1e8
    after,_=orth_prediction(model,x[:8,0],z[:8],types[:8])
    np.testing.assert_array_equal(before,after)
    assert np.isfinite(before).all()


def test_logistic_probabilities_and_zero_effect():
    from scripts.t3_round2.models import LogisticHurdle
    from scripts.t3_next.five_ops import bounded_add
    rng=np.random.default_rng(8);a=rng.uniform(size=(80,1));z=rng.normal(size=(80,3));types=np.array(['a']*40+['b']*40)
    y=rng.uniform(size=(80,5));y[rng.random(y.shape)<.6]=0;y[:,0]=0
    cfg={'logistic_C':.01,'logistic_max_iter':500,'logistic_tol':1e-5}
    model=LogisticHurdle().fit(a,z,types,y,cfg);pred,p=model.predict(a,z,types)
    assert (p>=0).all() and (p<=1).all() and np.all(p[:,0]==0)
    np.testing.assert_array_equal(bounded_add(y,pred-pred,.25),y)


def test_gene_shrink_outer_holdout_labels_unused(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from scripts.t3_round2 import run
    calls=[]
    def fit(z,y,adj,tr,te,**kwargs):
        calls.append((set(tr),set(te)))
        return {'graph_prediction':np.broadcast_to(y[tr].mean(0)+.03,(len(te),500)).copy()}
    monkeypatch.setattr(run,'fit_graph_comparator',fit)
    rng=np.random.default_rng(5);z=rng.normal(size=(10,3));y=rng.normal(size=(10,500));tr=np.arange(8);te=np.arange(8,10)
    c=SimpleNamespace(run=tmp_path,cfg={'seed':1,'round2':{'inner_folds':4,'source_epochs':2,'gene_shrink_prior_scale':10.}})
    a,w=run.fit_gene_shrink(c,z,y,np.eye(10),tr,te,'first');y[te]=1e9
    b,v=run.fit_gene_shrink(c,z,y,np.eye(10),tr,te,'second')
    np.testing.assert_array_equal(a['model'],b['model']);np.testing.assert_array_equal(w,v)
    assert all(not (a&b) and not (a&set(te)) for a,b in calls)
