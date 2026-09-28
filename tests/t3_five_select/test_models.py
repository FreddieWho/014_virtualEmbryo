import numpy as np
from scripts.t3_five_select.models import ResidualHurdle,SplineHurdle,bootstrap_ids,activity_gate,delta
from scripts.t3_next.five import Hurdle

class Zero:
    def predict(self,a,z,t):return np.zeros((len(a),1)),None

def test_residual_excludes_same_id_even_after_counterfactual_move():
    a=np.array([[0.],[1.],[2.]]);z=np.zeros((3,3));t=np.array(['a']*3)
    m=ResidualHurdle().fit(Zero(),a,z,t,np.array([[100.],[2.],[4.]]),np.array([10,11,12]),{'neighbors':2,'residual_weight':1.})
    got=m.predict(np.array([[1.9]]),np.zeros((1,3)),np.array(['a']),np.array([10]))[0]
    np.testing.assert_allclose(got,[[3.]])

def test_residual_only_self_returns_zero_and_unseen_type_zero():
    m=ResidualHurdle().fit(Zero(),np.zeros((1,1)),np.zeros((1,3)),np.array(['a']),np.array([[10.]]),np.array([7]),{'neighbors':64,'residual_weight':1.})
    np.testing.assert_array_equal(m.predict(np.zeros((2,1)),np.zeros((2,3)),np.array(['a','b']),np.array([7,8]))[0],np.zeros((2,1)))

def test_bootstrap_type_counts_and_reproducibility():
    t=np.array(['b']*20+['a']*10);ids=np.arange(100,130);out=bootstrap_ids(t,ids,123)
    assert len(out)==30 and sum(out<120)==20 and len(np.unique(out))<30
    np.testing.assert_array_equal(out,bootstrap_ids(t,ids,123))

def test_activity_gate_zero_saturation_and_unseen_type():
    np.testing.assert_allclose(activity_gate(np.array([[0.],[1.],[9.],[1.]]),np.array(['a','a','a','b']),{'a':2.},4.),[0.,.5,1.,.25])

def test_spline_knots_training_only_and_zero_intervention_identity():
    rng=np.random.default_rng(2);a=np.linspace(0,2,40)[:,None];z=rng.normal(size=(40,3));t=np.array(['a']*20+['b']*20);y=np.maximum(rng.normal(size=(40,4)),0)
    cfg={'ridge_alpha':100,'spline_quantiles':[.25,.5,.75]};m=SplineHurdle().fit(a,z,t,y,cfg);knots=m.knots.copy()
    out=m.predict(np.full((40,1),100.),z,t)[0];assert np.isfinite(out).all() and (out>=0).all()
    np.testing.assert_array_equal(knots,m.knots);np.testing.assert_allclose(knots,np.quantile(a[a>0],[.25,.5,.75]))
    np.testing.assert_array_equal(delta(m,a,a,z,t,np.arange(40)),np.zeros_like(y))

def test_bag_delta_is_average_response():
    rng=np.random.default_rng(3);a=rng.random((30,1));z=rng.normal(size=(30,3));t=np.array(['a']*30);y=rng.random((30,2))
    h=Hurdle().fit(a,z,t,y,100);b=np.zeros_like(a)
    np.testing.assert_allclose(delta([h,h],a,b,z,t,np.arange(30)),h.predict(b,z,t)[0]-h.predict(a,z,t)[0])
