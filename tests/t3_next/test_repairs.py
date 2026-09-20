import numpy as np
from scripts.t3_next.repair_ops import decode_rate, calibrate_rate, mean_ratio, residual_calibration, calibrated_transfer


def test_sparse_decoder_identity_zero_support_and_known_rate_recovery():
    x=np.array([[0.,1.,2.],[0.,2.,0.],[0.,3.,4.]])
    np.testing.assert_array_equal(decode_rate(x,np.zeros(3)),x)
    y=decode_rate(x,np.array([.4,-.3,.2]))
    assert (y>=0).all() and np.array_equal(y==0,x==0)
    r=calibrate_rate(x,y.mean(0),.69)
    np.testing.assert_allclose(r,[0,-.3,.2],atol=1e-6)


def test_ratio_never_activates_zero_or_changes_identity():
    x=np.array([[0.,2.],[3.,0.]])
    pred=np.array([[-10.,1.],[2.,-3.]])
    np.testing.assert_array_equal(mean_ratio(x,pred,pred,.05,.69),x)
    assert (mean_ratio(x,pred,pred-10,.05,.69)>=0).all()


def test_mapping_calibration_test_targets_do_not_change_predictions():
    rng=np.random.default_rng(4); y=rng.normal(size=(80,3)); raw=y+rng.normal(size=y.shape)*.1
    types=np.array(['a','b']*40); train=np.arange(80)<60
    p,b,_=residual_calibration(raw,y,types,train,10.)
    modified=y.copy();modified[~train]=999
    p2,b2,_=residual_calibration(raw,modified,types,train,10.)
    np.testing.assert_array_equal(p,p2);np.testing.assert_array_equal(b,b2)
    assert np.mean((p[~train]-y[~train])**2)<np.mean((b[~train]-y[~train])**2)


def test_zero_calibration_slope_blocks_atlas_intervention_transfer():
    observed=np.array([[0.,2.],[1.,3.]])
    mapped=np.ones_like(observed);delta=np.array([[20.,-1.],[3.,-4.]])
    np.testing.assert_array_equal(calibrated_transfer(observed,mapped,delta,np.zeros_like(delta),.05,.69),observed)
    got=calibrated_transfer(observed,mapped,delta,np.ones_like(delta)*.1,.05,.69)
    assert not np.array_equal(got,observed)
    assert np.array_equal(got==0,observed==0) and (got>=0).all()
