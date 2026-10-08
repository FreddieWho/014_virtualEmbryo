import numpy as np
from scripts.t1_six.ops import (squared_cost,exact_plan,plan_fields,consistency_distances,stability_fractions,
                               adaptive_sides,weighted_draw,covot_reselect_soft,conformal_radius,conformal_reselect,consistency_logw)


def test_squared_cost_matches_direct_and_nonnegative():
    rng=np.random.default_rng(3);a=rng.random((7,4));b=rng.random((5,4))
    d=squared_cost(a,b)
    direct=((a[:,None,:]-b[None,:,:])**2).sum(-1)
    np.testing.assert_allclose(d,direct,atol=1e-10);assert (d>=0).all()


def test_exact_plan_marginals_uniform_and_exact():
    rng=np.random.default_rng(5);a=rng.random((40,3));b=rng.random((31,3))
    plan,info=exact_plan(a,b)
    np.testing.assert_allclose(plan.sum(1),np.full(40,1/40),atol=1e-12)
    np.testing.assert_allclose(plan.sum(0),np.full(31,1/31),atol=1e-12)
    assert plan.min()>=0 and info['row_residual']<=1e-8


def test_plan_fields_identity_for_identical_clouds():
    rng=np.random.default_rng(7);z=rng.random((20,3))
    plan,_=exact_plan(z,z)
    d_early,d_late,row_t,col_s=plan_fields(plan,z,z)
    np.testing.assert_allclose(d_early,0,atol=1e-10);np.testing.assert_allclose(d_late,0,atol=1e-10)
    np.testing.assert_allclose(row_t,z,atol=1e-10)


def test_consistency_distances_zero_for_identity_plan():
    rng=np.random.default_rng(9);z=rng.random((15,3))
    plan,_=exact_plan(z,z)
    d_early,d_late=consistency_distances(plan,z,z)
    np.testing.assert_allclose(d_early,0,atol=1e-10);np.testing.assert_allclose(d_late,0,atol=1e-10)


def test_stability_fractions_two_level_rule():
    a=np.ones((40,3));b=a*2
    fraction,score,extra=stability_fractions(a,b,4,3,.25,1)
    assert score==1.0 and fraction==0.7 and extra['zero_stable']==1.0
    rng=np.random.default_rng(11);fraction,score,_=stability_fractions(rng.random((31,5)),rng.random((43,5)),4,3,.25,8)
    assert fraction in (0.3,0.7) and 0<=score<=1


def test_adaptive_sides_deterministic_type_preserving():
    rng=np.random.default_rng(13)
    types=np.array(['A','B','A','B','A','B','C','A','B','C'])
    fr={'A':0.7,'B':0.3,'C':0.5}
    s1,r1=adaptive_sides(types,fr,42);s2,r2=adaptive_sides(types,fr,42)
    np.testing.assert_array_equal(s1,s2);np.testing.assert_array_equal(r1,r2)
    for i in range(len(types)):
        assert 0<=r1[i]<len(types) and np.isfinite(r1[i])  # rows valid
    # after the global slot reorder, (side,row) pairs keep their pre-shuffle type-group:
    # per type t, #{side==0 with row of type t} == round(n_t*fr[t]) and side==1 complements it
    for t in ['A','B','C']:
        n_t=int((types==t).sum());na=int(round(n_t*fr[t]))
        assert int(np.sum((s1==0)&(types[r1]==t)))==na
        assert int(np.sum((s1==1)&(types[r1]==t)))==n_t-na
    # after the shuffle the per-type side fraction lives on the (side,row) pairs, not on slot types;
    # the global best-side total still equals the sum of per-type quotas
    assert int(np.sum(s1==0))==sum(int(round(int((types==t).sum())*fr[t])) for t in ['A','B','C'])


def test_adaptive_sides_missing_fraction_keeps_skeleton():
    types=np.array(['A','B','EXEM','A'])
    s,r=adaptive_sides(types,{'A':0.5},1)  # B/EXEM have no frozen fraction -> keep the skeleton
    for i in [1,2]:assert s[i]==0 and r[i]==i  # identity best rows
    for i in [0,3]:assert types[r[i]]=='A'  # covered type: rows stay within its pool


def test_weighted_draw_picks_within_candidates():
    cand=np.array([3,7,9]);d=np.array([0.1,1.0,5.0])
    picks={weighted_draw(cand,d,u/7) for u in range(7)}
    assert picks<=set(cand.tolist())


def test_covot_reselect_soft_fallback_and_validity():
    rng=np.random.default_rng(17);pool=np.arange(6);allq=rng.random((6,3))
    target=rng.random((10,3))
    chosen,dist,kk=covot_reselect_soft(target,allq,pool,8,5)
    assert kk==6 and set(chosen.tolist())<=set(pool.tolist()) and np.isfinite(dist)
    single=np.array([2])
    chosen1,_,kk1=covot_reselect_soft(target,allq[single],single,8,5)
    assert kk1==1 and (chosen1==2).all()
    c2,_,_=covot_reselect_soft(target,allq,pool,8,5)
    np.testing.assert_array_equal(chosen,c2)  # deterministic given seed


def test_conformal_radius_finite_and_infeasible_none():
    rng=np.random.default_rng(19)
    za=rng.random((60,3));zb=za*2+rng.random((60,3))*.1
    r=conformal_radius(za[:30],zb[:30],za[30:],zb,0.1,0.1,0.5)
    assert r is not None and r['radius']>0 and r['n_cal']==30
    assert conformal_radius(za[:3],zb[:3],za[30:],zb,0.1,0.1,0.5) is None


def test_conformal_reselect_radius_modes():
    rng=np.random.default_rng(23);pool=np.arange(9);allq=rng.random((9,3))
    target=allq[:5]+0.01
    chosen,dist,mode=conformal_reselect(target,allq,pool,1e9,7)
    assert mode=='conformal_ball' and set(chosen.tolist())<=set(pool.tolist())
    chosen0,dist0,mode0=conformal_reselect(target,allq,pool,1e-12,7)
    assert mode0=='k1_fallback'
    c2,_,_=conformal_reselect(target,allq,pool,1e9,7)
    np.testing.assert_array_equal(chosen,c2)


def test_consistency_logw_bounds_and_nearest_neighbor():
    rng=np.random.default_rng(29)
    train=rng.random((20,3));cons=np.linspace(0,1,20)
    q=train[:5]
    w,extra=consistency_logw(cons,train,q,0.5)
    assert w.min()>=0.5 and w.max()<=2 and np.isfinite(w).all()
    assert extra['sigma']==0.5 and len(w)==5
    w_far,_=consistency_logw(cons,train,train+10,0.5)  # far queries: nearest d large -> weights collapse
    assert w_far.min()>=0.5 and w_far.max()<=2 and len(w_far)==20


def test_operators_take_no_truth_input():
    # Structural leak guard: new-route operators accept only train-side arrays and seeds;
    # their signatures expose no hidden-target argument.
    import inspect
    for fn in [exact_plan,plan_fields,consistency_distances,stability_fractions,adaptive_sides,
               covot_reselect_soft,conformal_radius,conformal_reselect,consistency_logw]:
        names=inspect.signature(fn).parameters
        assert not any(k in names for k in ['target_h5ad','truth','E10.5','future_truth','hidden']), fn.__name__
