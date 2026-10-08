"""Bounded synthetic tests; no external download, training or scoring."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'frozen'))
import numpy as np
import endpoint_flow as ef,endpoint_residual as er
from test_endpoint_flow import fixture,test_conservation,test_endfree_orphan_identity,test_zero_horizon_identity,test_cardiac_orphan_is_not_frozen

def test_matched():
 a,m=fixture();base=ef.recipe(a,m['median_deltas']);common=m['endpoint']['common_indices'];other=np.setdiff1d(np.arange(500),common)
 for permuted in [False,True]:
  x,d=er.predict(a,m,permuted)
  assert np.isfinite(x).all() and x.min()>=0
  assert np.array_equal(x[:,other],base[:,other]) and np.array_equal(x[8:],base[8:])
  assert np.array_equal(x,er.predict(a,m,permuted)[0])
  np.testing.assert_allclose(np.expm1(x.astype(float)).sum(1),np.expm1(base.astype(float)).sum(1),rtol=1e-6)
  assert abs(d['endpoint_coefficient']-.104)<1e-12
 assert not np.array_equal(er.predict(a,m,False)[0],er.predict(a,m,True)[0])
if __name__=='__main__':
 for f in [test_conservation,test_endfree_orphan_identity,test_zero_horizon_identity,test_cardiac_orphan_is_not_frozen,test_matched]:f()
 print('PASS: 5 bounded synthetic endpoint/matched-drift tests; no biological validation claim')
