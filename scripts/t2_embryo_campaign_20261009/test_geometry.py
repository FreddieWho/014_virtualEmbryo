"""Run: python -m unittest scripts.t2_embryo_campaign_20261009.test_geometry"""
import unittest
import numpy as np
from scripts.t2_embryo_campaign_20261009.geometry import (
    interpolate_geometry, proper_alignment, gaussian_transport, rms_radius)


def fixture():
    rng = np.random.default_rng(32871)
    means = np.array([[0,0,0],[3,0,0],[0,2,0],[0,0,2.]])
    labels = np.repeat(['a','b','c','d'], 40)
    left = np.concatenate([rng.normal(size=(40,3))*.15 + m for m in means])
    right = np.concatenate([rng.normal(size=(40,3))*[.3,.1,.2] + m*1.2 for m in means])
    return left, right, labels


def rotation():
    q, _ = np.linalg.qr(np.random.default_rng(923).normal(size=(3,3)))
    q[:, -1] *= np.linalg.det(q)
    return q


class GeometryTests(unittest.TestCase):
    def test_identity_all_times(self):
        x, _, l = fixture()
        for t in [0, .333333333333, 1]:
            out, diag = interpolate_geometry(x,l,x,l,x,l,t)
            np.testing.assert_allclose(out, x, atol=2e-12)
            self.assertAlmostEqual(diag['rms_after_lock'], rms_radius(x), places=12)

    def test_left_endpoint(self):
        x,y,l = fixture()
        out, _ = interpolate_geometry(x,l,x,l,y,l,0)
        np.testing.assert_allclose(out, x, atol=2e-12)

    def test_right_endpoint_moments(self):
        x,y,l = fixture()
        aligned, _ = proper_alignment(x,l,y,l)
        out, _ = interpolate_geometry(x,l,x,l,y,l,1,target_rms=rms_radius(aligned))
        for s in set(l):
            np.testing.assert_allclose(out[l==s].mean(0), aligned[l==s].mean(0), atol=1e-11)
            np.testing.assert_allclose(np.cov(out[l==s].T,bias=True), np.cov(aligned[l==s].T,bias=True), atol=1e-11)

    def test_right_rigid_frame_invariance(self):
        x,y,l = fixture(); q=rotation()
        a, _ = interpolate_geometry(x,l,x,l,y,l,1/3)
        b, _ = interpolate_geometry(x,l,x,l,y@q + [23,-17,8],l,1/3)
        np.testing.assert_allclose(a,b,atol=1e-11)

    def test_global_rigid_covariance(self):
        x,y,l = fixture(); q=rotation(); shift=np.array([11,7,-23])
        a, _ = interpolate_geometry(x,l,x,l,y,l,1/3)
        b, _ = interpolate_geometry(x@q+shift,l,x@q+shift,l,y@q+shift,l,1/3)
        np.testing.assert_allclose(a@q+shift,b,atol=1e-11)

    def test_scale_covariance(self):
        x,y,l = fixture()
        a, _ = interpolate_geometry(x,l,x,l,y,l,1/3)
        b, _ = interpolate_geometry(x*14,l,x*14,l,y*14,l,1/3)
        np.testing.assert_allclose(a*14,b,atol=1e-10)

    def test_singular_states_remain_finite(self):
        x,y,l=fixture(); x[l=='a']=x[l=='a'].mean(0); y[l=='b',2]=0
        out, d=interpolate_geometry(x,l,x,l,y,l,1/3)
        self.assertTrue(np.isfinite(out).all())
        self.assertEqual(d['states']['a']['base']['regularized_axes'],3)
        self.assertAlmostEqual(rms_radius(out),rms_radius(x),places=10)

    def test_anchor_degeneracy_explicit(self):
        labels=np.repeat(['a','b','c'],3)
        x=np.column_stack([np.repeat([0.,1.,2.],3),np.zeros(9),np.zeros(9)])
        with self.assertRaisesRegex(ValueError,'collinear'):
            proper_alignment(x,labels,x,labels)

    def test_reflection_never_registered_as_improper(self):
        x,y,l=fixture(); y=y*np.array([-1,1,1])
        _,diag=proper_alignment(x,l,y,l)
        self.assertAlmostEqual(diag['determinant'],1,places=12)
        self.assertGreater(diag['anchor_weighted_residual_rms'],.1)

    def test_gaussian_map_covariance(self):
        a=np.diag([1.,2,3]); r=rotation(); b=r@np.diag([4.,1.,2.])@r.T
        t=gaussian_transport(a,b)
        np.testing.assert_allclose(t@a@t.T,b,atol=1e-12)

    def test_row_permutation_equivariance(self):
        x,y,l=fixture(); perm=np.random.default_rng(1).permutation(len(x))
        a,_=interpolate_geometry(x,l,x,l,y,l,1/3)
        b,_=interpolate_geometry(x[perm],l[perm],x,l,y,l,1/3)
        np.testing.assert_allclose(a[perm],b,atol=1e-11)

    def test_single_cell_state_and_missing_type(self):
        x,y,l=fixture()
        base=np.concatenate([x,np.array([[2.,3.,4.],[3.,3.,3.]])])
        bl=np.concatenate([l,['rare','new']])
        lx=np.concatenate([x,[[1,2,3]]]); ll=np.concatenate([l,['rare']])
        ry=np.concatenate([y,[[2,2,3]]])
        out,d=interpolate_geometry(base,bl,lx,ll,ry,ll,1/3)
        self.assertTrue(np.isfinite(out).all())
        self.assertEqual(d['fallback_absent_endpoint_types'],['new'])
        self.assertEqual(d['states']['rare']['base']['regularized_axes'],3)


if __name__ == '__main__':
    unittest.main()
