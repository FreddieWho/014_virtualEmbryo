import numpy as np
from scripts.t3_three.ops import decompose,agree_rate,graph_operator,diffuse
from scripts.t3_three.models import apply


def test_midpoint_decomposition_and_zero_intervention():
    r=np.random.default_rng(1);p=r.uniform(size=(20,9));q=r.uniform(size=(20,9));m=r.uniform(size=(20,9));n=r.uniform(size=(20,9))
    a,b=decompose(p,m,q,n);np.testing.assert_allclose(a+b,q*n-p*m,atol=1e-14)
    a,b=decompose(p,m,p,m);assert not a.any() and not b.any()


def test_agreement_gate_rejects_conflict_and_zero():
    base=np.ones((2,3));h=np.array([[2,0,1],[0,2,2.]])
    rate,mask=agree_rate(base,h,np.array([.2,.3,-.1]))
    np.testing.assert_array_equal(mask,[[1,0,0],[0,1,0]])
    np.testing.assert_allclose(rate,[[.1,0,0],[0,.15,0]])


def test_graph_symmetric_doubly_stochastic_including_duplicate_coordinates():
    z=np.array([[0,0],[0,0],[1,0],[2,1],[4,2.]])
    w=graph_operator(z,2,.5).toarray()
    np.testing.assert_allclose(w,w.T);np.testing.assert_allclose(w.sum(0),1);np.testing.assert_allclose(w.sum(1),1);assert w.min()>=0


def test_diffusion_preserves_means_and_isolates_inactive_and_types():
    z=np.arange(18).reshape(6,3);types=np.array(['a']*3+['b']*3);active=np.array([1,1,0,1,1,0],bool);d=np.arange(12).reshape(6,2).astype(float);d[~active]=0
    out,_=diffuse(d,z,types,active,1,.5)
    np.testing.assert_array_equal(out[~active],0)
    for t in ['a','b']:np.testing.assert_allclose(out[types==t].mean(0),d[types==t].mean(0))
    np.testing.assert_array_equal(diffuse(d,z,types,active,1,0)[0],d)


def test_all_routes_zero_response_identity_and_nonnegativity():
    x=np.array([[0.,1.],[2.,0.]]);z=np.array([[0.,0,0],[1,0,0]]);types=np.array(['a','a']);zero=np.zeros_like(x)
    cfg={'hurdle_strength':.25,'agreement_source_strength':.5,'effect_epsilon':1e-8,'probability_weight':.5,'positive_weight':1.,'neighbors':1,'diffusion_strength':.5}
    for lane in ['r1agree','r2damp','r3diffuse']:
        out,_=apply(lane,x,zero,zero,zero,z,types,np.ones(2,bool),np.zeros(2),cfg);np.testing.assert_allclose(out,x,atol=1e-7)
        out,_=apply(lane,x,-np.ones_like(x),-np.ones_like(x)*.5,-np.ones_like(x)*.5,z,types,np.ones(2,bool),np.ones(2),cfg);assert np.isfinite(out).all() and out.min()>=0
