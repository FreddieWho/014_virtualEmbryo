import numpy as np
import pytest
from scripts.t1_round2.ops import abundance_step,mixture_donors,shrink_step,mass_shrink,bounded_weights
from scripts.t1_five.ops import fit_mixture,apply_mixture
from scripts.t1_round2.models import predict


def test_abundance_scale_identity_and_new_type_finite():
    np.testing.assert_allclose(abundance_step([10,20],[10,20]),0)
    x=abundance_step([0,100],[100,0]);assert np.isfinite(x).all() and max(abs(x))<=np.log(2)


def test_mixture_changes_counts_without_fabricating_rows():
    types=np.array(['a']*50+['b']*50);d=mixture_donors(types,{'a':np.log(2),'b':-np.log(2)})
    x=np.arange(700).reshape(100,7);out=x[d]
    assert len(out)==100 and (types[d]=='a').sum()==80
    assert all(np.array_equal(row,x[i]) for row,i in zip(out,d))


def test_mixture_identity():
    np.testing.assert_array_equal(mixture_donors(['x']*10,{'x':0}),np.arange(10))


def test_shrink_no_noise_and_zero_signal():
    np.testing.assert_array_equal(shrink_step(np.array([-2.,0,3]),0),[-2,0,3])
    d=np.array([-2.,0,3]);out=shrink_step(d,2)
    assert np.all(abs(out)<=abs(d)) and np.all(np.sign(out)==np.sign(d))
    with pytest.raises(ValueError):shrink_step(d,-1)


def test_mass_shrink_monotone_nonnegative_and_identity():
    a=np.r_[np.zeros(30),np.linspace(.1,4,70)];b=np.r_[np.zeros(50),np.linspace(.2,5,50)]
    m=fit_mixture(a,b,'o1mass',True)
    s=mass_shrink(a,b,m,True)
    assert np.all(np.diff(s['qout'])>=0) and (s['qout']>=0).all()
    p=apply_mixture(s,b,(np.arange(100)+.5)/100);assert np.isfinite(p).all() and min(p)>=0
    same=mass_shrink(a,a,fit_mixture(a,a,'o1mass',True),True)
    np.testing.assert_array_equal(apply_mixture(same,a,np.ones(100)*.5),a)


def test_weight_offset_invariance():
    x=np.array([-10.,0,1,2,30]);np.testing.assert_allclose(bounded_weights(x),bounded_weights(x+100))
    assert bounded_weights(x).min()>=.5 and bounded_weights(x).max()<=2


def test_stack_uses_mass_rows_once(monkeypatch):
    raw=np.arange(12,dtype=np.float32).reshape(4,3);donors=np.array([1,1,3,3]);mass=raw+100
    def fake(model,raw,types,legacy):return (raw[donors],{'donor_indices':donors}) if model=='density' else (mass,{})
    monkeypatch.setattr('scripts.t1_round2.models.old_predict',fake)
    out,details=predict({'lane':'n1stack','density':'density','mass':'mass'},raw,np.array(['a']*4),raw)
    np.testing.assert_array_equal(out,mass[donors]);np.testing.assert_array_equal(details['donor_indices'],donors)
