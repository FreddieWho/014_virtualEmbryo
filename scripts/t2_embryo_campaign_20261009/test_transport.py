import unittest,numpy as np
from scripts.t2_embryo_campaign_20261009.transport import transport
class TransportTests(unittest.TestCase):
 def test_fixed_seed_and_t0(self):
  rng=np.random.default_rng(27);labs=np.repeat(['a','b','c'],30);C=rng.normal(size=(90,3))+np.repeat([[0,0,0],[3,0,0],[0,3,0]],30,axis=0);X=rng.gamma(1,1,(90,20));R=C+rng.normal(0,.1,C.shape);RX=X+rng.uniform(0,.1,X.shape);prior=rng.normal(size=(20,2));ext=rng.poisson(2,(100,20));rows=np.arange(90)
  for mode in ['internal','spatial','scrna']:
   y,d=transport(C,labs,rows,C,labs,X,R,labs,RX,0,mode,prior,ext)
   np.testing.assert_allclose(y,C,atol=1e-12)
   y,_=transport(C,labs,rows,C,labs,X,R,labs,RX,.3,mode,prior,ext)
   z,_=transport(C,labs,rows,C,labs,X,R,labs,RX,.3,mode,prior,ext)
   np.testing.assert_array_equal(y,z);self.assertTrue(np.isfinite(y).all())
if __name__=='__main__':unittest.main()
