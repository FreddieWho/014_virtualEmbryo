import unittest
import numpy as np
from scripts.t3_priority_six.common import rate_decode,delta_metrics
from scripts.t3_priority_six.target_routes import activity_feature,sample_mass
from scripts.t3_priority_six.calibrate import observation_decode

class PrioritySixTests(unittest.TestCase):
    def test_decoder_identity_and_nonnegative(self):
        x=np.array([[0.,.5,2.],[1.,0.,3.]],dtype='float32')
        np.testing.assert_allclose(rate_decode(x,np.zeros_like(x)),x,atol=3e-7)
        out=rate_decode(x,np.array([-1.,.7,2.]))
        self.assertTrue(np.isfinite(out).all() and (out>=0).all())
        self.assertEqual(out[0,0],0.)
        self.assertGreater(out[0,2],x[0,2])
    def test_activity_cannot_read_its_own_outcome(self):
        x=np.arange(20,dtype=float).reshape(5,4);w=np.array([1.,-2.,3.,4.])
        a=activity_feature(x,w,2);changed=x.copy();changed[:,2]+=10000
        np.testing.assert_array_equal(a,activity_feature(changed,w,2))
        changed[:,1]+=10
        self.assertFalse(np.array_equal(a,activity_feature(changed,w,2)))
    def test_delta_evaluation_does_not_reward_large_background(self):
        true=np.array([[.1,-.2,.3]]);perfect=delta_metrics(true,true)
        wrong=delta_metrics(-true,true)
        self.assertEqual(perfect['delta_mse'],0.)
        self.assertGreater(perfect['delta_cosine'],wrong['delta_cosine'])
        self.assertEqual(wrong['direction_accuracy_nontrivial'],0.)
    def test_detection_decoder_keeps_identity_and_state_mean(self):
        x=np.zeros((20,2),dtype='float32');x[:5,0]=1
        labels=np.array(['a']*20)
        np.testing.assert_array_equal(observation_decode(x,x,labels,1.),x)
        raw=rate_decode(x,np.array([1.,0.]))
        out=observation_decode(x,raw,labels,1.)
        self.assertGreater(np.sum(out[:,0]>0),np.sum(x[:,0]>0))
        self.assertTrue((out[:,1]==0).all())
        np.testing.assert_allclose(np.expm1(out).mean(0),np.expm1(raw).mean(0),rtol=1e-6)
    def test_mass_sampler_cannot_create_change_when_mass_is_unchanged(self):
        states=np.array([1,0,0,1,2,0,1,2]);mass=np.bincount(states)/len(states)
        np.testing.assert_array_equal(sample_mass(states,mass),np.arange(len(states)))
        moved=sample_mass(states,np.array([.125,.375,.5]))
        np.testing.assert_array_equal(np.bincount(states[moved]),[1,3,4])

if __name__=='__main__':unittest.main()
