import numpy as np
from scripts.t3_next.five_ops import quantile_response, bounded_add, latent_predict, shrink_weight, stability_weight


def test_quantile_identity_zeros_and_bounds():
    a=np.array([[0.,1.],[1.,2.],[2.,3.],[3.,4.]])
    assert np.array_equal(quantile_response(a,a,a,0.25,np.log(2)),a)
    out=quantile_response(a,a,a*2,0.25,np.log(2))
    assert out[0,0]==0
    assert np.isfinite(out).all() and (out>=0).all()
    assert np.all(np.diff(out,axis=0)>=0)
    assert np.max(np.expm1(out)/np.maximum(np.expm1(a),1e-9))<=2.000001


def test_bounded_add_identity_activation_and_cap():
    x=np.array([[0.,.3],[2.,0.]])
    assert np.array_equal(bounded_add(x,np.zeros_like(x),.25),x)
    y=bounded_add(x,np.array([[1.,-100.],[100.,-1.]]),.25)
    assert y[0,0]>0 and 0<y[0,1]<x[0,1] and y[1,1]==0
    np.testing.assert_allclose(np.expm1(y[0,1])/np.expm1(x[0,1]),.5)
    assert np.max(y-x)<=np.log(2)+1e-8


def test_latent_heldout_response_cannot_affect_prediction():
    r=np.random.default_rng(6);z=r.normal(size=(9,4));y=r.normal(size=(9,7))
    train=np.arange(6);test=np.arange(6,9)
    pred,_=latent_predict(z,y,train,test,rank=3,alpha=1.)
    altered=y.copy();altered[test]=1e6
    other,_=latent_predict(z,altered,train,test,rank=3,alpha=1.)
    np.testing.assert_array_equal(pred,other)
    constant=np.ones_like(y)*.12
    same,_=latent_predict(z,constant,train,test,rank=3,alpha=1.)
    np.testing.assert_allclose(same,.12)


def test_shrink_weight_known_solution_and_no_signal():
    mean=np.zeros((4,2));p=np.ones((4,2))
    assert shrink_weight(mean,p,.25*p)==.25
    assert shrink_weight(mean,p,-p)==0.
    assert shrink_weight(mean,p,2*p)==1.
    assert shrink_weight(mean,mean,p)==0.


def test_stability_cancels_disagreement_and_zeros():
    e=np.array([[1.,1.,0.],[1.,-1.,0.],[1.,1.,0.],[1.,-1.,0.]])
    w=stability_weight(e,.1)
    assert w[0]>.9 and w[1]==0 and w[2]==0


def test_nested_shrink_never_consumes_outer_labels(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from scripts.t3_next import five
    calls=[]
    def fit(z,y,adj,train,test,**kwargs):
        calls.append((set(train),set(test)))
        return {'graph_prediction':np.broadcast_to(y[train].mean(0)+.02,(len(test),500)).copy()}
    monkeypatch.setattr(five,'fit_graph_comparator',fit)
    r=np.random.default_rng(6);z=r.normal(size=(12,3));y=r.normal(size=(12,500));adj=np.eye(12)
    c=SimpleNamespace(cfg={'seed':4,'five':{'inner_folds':4,'epochs':1}},run=tmp_path)
    tr=np.arange(8);te=np.arange(8,12)
    p,info=five.graph_shrink(z,y,adj,tr,te,c,'one')
    y[te]=1e9
    other,other_info=five.graph_shrink(z,y,adj,tr,te,c,'two')
    np.testing.assert_array_equal(p,other)
    assert info['weight']==other_info['weight']
    assert all(not (a&b) and not (a&set(te)) for a,b in calls)


def test_hurdle_no_intervention_identity_and_finite_probabilities():
    from scripts.t3_next.five import Hurdle
    r=np.random.default_rng(2);a=r.uniform(size=(30,1));z=r.normal(size=(30,3));types=np.array(['a']*15+['b']*15)
    y=r.uniform(size=(30,5));y[r.random(size=y.shape)<.5]=0
    m=Hurdle().fit(a,z,types,y,10)
    pred,p=m.predict(a,z,types)
    assert np.isfinite(pred).all() and (pred>=0).all() and (p>=0).all() and (p<=1).all()
    np.testing.assert_array_equal(bounded_add(y,pred-pred,.25),y)
