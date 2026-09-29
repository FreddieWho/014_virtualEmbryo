import numpy as np
from scripts.t1_seven.ops import gaussian_map,shrunk_cov,moment_fit,moments,graph_fit,graph_query,stability_weights,bounded_weights

def test_gaussian_map_covariance_identity_and_transport():
    a=np.array([[2.,.3],[.3,1.]]);b=np.array([[1.,-.2],[-.2,3.]])
    m=gaussian_map(a,b);np.testing.assert_allclose(m@a@m.T,b,atol=1e-10);np.testing.assert_allclose(gaussian_map(a,a),np.eye(2),atol=1e-10)

def test_covariance_floor_for_constant_features():
    c=shrunk_cov(np.zeros((10,3)),.1);assert np.linalg.eigvalsh(c).min()>0

def test_moment_target_identity_and_mean_shift():
    z=np.linspace(-1,1,100)[:,None];f=moments(z);theta,info=moment_fit(f,f.mean(0),.1,2)
    np.testing.assert_allclose(theta,0,atol=1e-6);target=f.mean(0);target[0]+=.2;theta,_=moment_fit(f,target,.1,2);assert theta[0]>0 and info['success']

def test_graph_constant_label_and_query_self_exclusion():
    z=np.arange(10.)[:,None];g=graph_fit(z,np.full(10,.4),np.arange(10),3,.8);np.testing.assert_allclose(g['values'],.4,atol=1e-8)
    g['values']=np.r_[1.,np.zeros(9)];g['prior']=.5
    assert graph_query(g,np.array([[0.]]),np.array([0]),1)[0]<0

def test_stability_preserves_replicated_direction():
    a=np.ones((40,3));b=a*2;w0,w1,_=stability_weights(a,b,4,3,.25,1);np.testing.assert_array_equal(w0,1);np.testing.assert_array_equal(w1,1)

def test_weight_bounds_and_location_invariance():
    a=np.linspace(-100,100,50);w=bounded_weights(a);assert w.min()>=.5 and w.max()<=2;np.testing.assert_allclose(w,bounded_weights(a+10))

def test_graph_duplicate_coordinates_still_finite():
    z=np.zeros((20,2));y=np.r_[np.zeros(10),np.ones(10)];g=graph_fit(z,y,np.arange(20),5,.8);assert np.isfinite(g['values']).all() and g['solver_residual']<1e-5

def test_stability_keeps_partition_identity_and_reproducibility():
    rng=np.random.default_rng(4);a=rng.random((31,5));b=rng.random((43,5));w0,w1,e=stability_weights(a,b,4,3,.25,8)
    for key,n in [('early_parts',31),('late_parts',43)]:np.testing.assert_array_equal(np.sort(np.concatenate(e[key])),np.arange(n))
    assert set(w0)<=set([.25,1.]) and set(w1)<=set([.25,1.]);np.testing.assert_array_equal(w1,stability_weights(a,b,4,3,.25,8)[1])
