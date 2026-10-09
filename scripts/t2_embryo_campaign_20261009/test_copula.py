import unittest,numpy as np
from scripts.t2_embryo_campaign_20261009.copula import fit_conditional,regularize
class CopulaTests(unittest.TestCase):
 def test_exact_marginals_and_replay(self):
  rng=np.random.default_rng(82);X=rng.poisson(1,(100,20)).astype('float32');X[:,0]=0;lab=np.repeat(['a','b'],50)
  B,d=fit_conditional(rng.poisson(2,(200,20)));Y,_=regularize(X,lab,B);Z,_=regularize(X,lab,B)
  for s in ['a','b']:np.testing.assert_array_equal(np.sort(X[lab==s],axis=0),np.sort(Y[lab==s],axis=0))
  np.testing.assert_array_equal(Y,Z);self.assertTrue(np.isfinite(Y).all());self.assertTrue(np.all(Y[:,0]==0))
if __name__=='__main__':unittest.main()
