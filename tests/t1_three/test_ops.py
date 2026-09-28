import numpy as np
from scripts.t1_three.ops import systematic_indices,joint_donors,mixture_indices


def test_systematic_count_identity_and_weight_scale():
    np.testing.assert_array_equal(systematic_indices(np.ones(5),5),np.arange(5))
    w=np.array([1.,2,4]);a=systematic_indices(w,7);b=systematic_indices(w*11,7)
    np.testing.assert_array_equal(a,b);assert len(a)==7 and a.min()>=0 and a.max()<3


def test_joint_preserves_composition_types_and_is_single_selection():
    t=np.array(['a','b','a','b']);c=np.array([0,0,1,2]);d=joint_donors(t,np.array([1.,1,8,1]),c)
    np.testing.assert_array_equal(t[d],t[c]);assert len(d)==len(t)
    x=np.arange(20).reshape(4,5);np.testing.assert_array_equal(x[d],np.stack([x[i] for i in d]))
    np.testing.assert_array_equal(joint_donors(t,np.ones(4),np.arange(4)),np.arange(4))


def test_mixture_parent_quota_no_replacement_and_determinism():
    ta=np.array(['a']*3+['b']*6);tb=np.array(['a']*7+['b']*2)
    source,rows=mixture_indices(ta,tb,.5,123)
    assert (source==0).sum()==4 and (source==1).sum()==5
    for side in [0,1]:assert len(np.unique(rows[source==side]))==(source==side).sum()
    s2,r2=mixture_indices(ta,tb,.5,123);np.testing.assert_array_equal(source,s2);np.testing.assert_array_equal(rows,r2)


def test_mixture_keeps_whole_rows_not_gene_averages():
    t=np.array(['a','a','b','b']);a=np.arange(12).reshape(4,3);b=a+100
    source,rows=mixture_indices(t,t,.5,7);out=np.stack([a[i] if s==0 else b[i] for s,i in zip(source,rows)])
    assert all(any(np.array_equal(row,p) for p in np.vstack([a,b])) for row in out)
