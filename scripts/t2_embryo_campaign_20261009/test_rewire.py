import unittest,numpy as np
from scripts.t2_embryo_campaign_20261009.rewire import rewire
class RewireTests(unittest.TestCase):
 def test_bijection_types_replay(self):
  rng=np.random.default_rng(5);lab=np.repeat(['a','b','c'],25);C=rng.normal(size=(75,3))+np.repeat([[0,0,0],[3,0,0],[0,3,0]],25,axis=0);X=rng.gamma(1,1,(75,20));R=C+rng.normal(0,.1,C.shape);RX=X+rng.uniform(0,.1,X.shape);w=rng.normal(size=(20,2))
  Y,perm,d=rewire(X,C*2+17,lab,X,C,lab,RX,R,lab,.3,w,source_coords=C,locality=True)
  np.testing.assert_array_equal(np.sort(perm),np.arange(75));np.testing.assert_array_equal(lab[perm],lab);np.testing.assert_array_equal(Y,X[perm])
  Z,rep,_=rewire(X,C*2+17,lab,X,C,lab,RX,R,lab,.3,w,source_coords=C,locality=True)
  np.testing.assert_array_equal(perm,rep)
  inverse=np.argsort(perm);np.testing.assert_array_equal(Y[inverse],X)
if __name__=='__main__':unittest.main()
