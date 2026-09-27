import numpy as np
from scripts.t1_five.ops import systematic_resample, rate_decode, borrow_rates, rate_factors, empirical_transport, mixture_transport


def test_resampling_identity_type_support_and_weight():
    np.testing.assert_array_equal(systematic_resample(np.ones(8)),np.arange(8))
    a=systematic_resample(np.array([1.,1.,8.,1.]))
    assert len(a)==4 and np.sum(a==2)>=2 and (a>=0).all() and (a<4).all()


def test_rate_decode_identity_zeros_and_bounds():
    x=np.array([[0.,1.,2.],[3.,0.,4.]])
    np.testing.assert_array_equal(rate_decode(x,np.zeros(3)),x)
    y=rate_decode(x,np.array([-.5,0,.5]))
    assert np.array_equal(x==0,y==0) and np.isfinite(y).all() and (y>=0).all()
    np.testing.assert_allclose(np.expm1(y[:,2])/np.expm1(x[:,2]),np.exp(.5))


def test_borrow_excludes_query_rate_and_uses_only_donors():
    centroids=np.array([[1.,0.],[.9,.1],[0.,1.]])
    rates=np.array([[100.,100.],[.2,-.2],[.4,-.4]])
    pred,w=borrow_rates(centroids[0],centroids[1:],rates[1:],2)
    assert np.allclose(pred,[.2,-.2],atol=.03) and len(w)==2
    assert np.isclose(sum(w),1)


def test_rate_factor_no_change_and_full_rank():
    y=np.arange(24,dtype=float).reshape(4,6)/100
    np.testing.assert_allclose(rate_factors(y,3)[0],y,atol=1e-12)
    np.testing.assert_array_equal(rate_factors(np.zeros_like(y),3)[0],np.zeros_like(y))


def test_empirical_transfer_matches_definition():
    a=np.array([0.,0.,1.,2.]);b=np.array([0.,1.,2.,3.]);x=np.array([0.,1.,2.]);lr=np.array([.8,.3,.5])
    q=np.linspace(0,1,41);u=np.searchsorted(np.sort(a),x,side='right')/len(a);u[x==0]=lr[x==0]*.5
    expected=np.interp(u,q,np.quantile(b,q))
    np.testing.assert_array_equal(empirical_transport(a,b,x,lr),expected)


def test_mixture_explicit_zero_mass_and_tail_bound():
    a=np.r_[np.zeros(80),np.linspace(.2,2,20)];b=np.r_[np.zeros(60),np.linspace(.2,2,40)]
    x=a.copy();lr=(np.arange(100)+.5)/100
    y,model=mixture_transport(a,b,x,lr,'o1mass',False,101)
    assert np.isclose(model['pout'],.6) and model['psource']==.8
    assert np.isfinite(y).all() and (y>=0).all()
    # Explicit forecast anchors its zero mass on late-stage rates.
    _,future=mixture_transport(a,b,b,lr,'o1mass',True,101)
    assert future['pout']<model['pout'] and future['psource']==.6


def test_parametric_model_replay_is_training_only():
    from scripts.t1_five.ops import fit_mixture,apply_mixture
    a=np.r_[np.zeros(20),np.linspace(.2,2,20)];b=np.r_[np.zeros(10),np.linspace(.3,2.5,30)]
    model=fit_mixture(a,b,'n2param',True)
    x=np.array([0.,.3,1.,3.]);rank=np.array([.9,.2,.3,.4])
    one=apply_mixture(model,x,rank);a[:]=100;b[:]=200
    np.testing.assert_array_equal(one,apply_mixture(model,x,rank))
    assert np.isfinite(one).all() and (one>=0).all() and one.max()<=model['upper']


def test_density_predict_preserves_whole_rows_and_types():
    from scripts.t1_five.models import fit,predict
    rng=np.random.default_rng(11);a=rng.uniform(size=(80,8));b=a.copy();b[:,0]+=np.linspace(0,1,80)
    labels=np.array(['a']*40+['b']*40)
    cfg={'min_type_cells':10,'embedding_components':3,'seed':3,'n1':{'logistic_C':1,'weight_log_cap':np.log(2),'minimum_ess_fraction':.5}}
    model=fit(a,labels,b,labels,'n1density',cfg)
    out,details=predict(model,a,labels,b)
    donors=details['donor_indices']
    np.testing.assert_array_equal(out,b[donors].astype(np.float32))
    np.testing.assert_array_equal(labels,labels[donors])


def test_zero_distribution_change_exact_identity_both_models():
    x=np.r_[np.zeros(8),np.linspace(.2,2,12)]
    for lane in ['n2param','o1mass']:
        for future in [False,True]:
            out,_=mixture_transport(x,x.copy(),x,np.linspace(.01,.99,len(x)),lane,future)
            np.testing.assert_array_equal(out,x)
