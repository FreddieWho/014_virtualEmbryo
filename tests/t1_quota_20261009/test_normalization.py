import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/t1_quota_20261009'))
import numpy as np,pytest
from scipy import sparse
from normalization import restore_cp10k

def test_exact_support_and_closed_form():
 x=np.array([[0,1,2,3],[.001,0,8,1]],np.float32)
 y,_=restore_cp10k(x);v=np.expm1(x.astype(np.float64));e=np.log1p(v*(10000/v.sum(1))[:,None]).astype(np.float32)
 assert np.array_equal(y.toarray(),e)
 assert np.array_equal(y.toarray()>0,x>0)

def test_known_scale_repair():
 rng=np.random.default_rng(123);c=rng.poisson(.7,(50,128)).astype(float);c*=10000/c.sum(1)[:,None]
 x=np.log1p(c);wrong=np.log1p(c*np.linspace(.4,2,50)[:,None]);fixed,_=restore_cp10k(wrong)
 assert np.max(np.abs(fixed.toarray()-x))<5e-7

def test_zero_row_rejected():
 with pytest.raises(ValueError):restore_cp10k(np.zeros((1,3)))

def test_no_random_or_input_mutation():
 x=sparse.csr_matrix(np.array([[0,2,1],[2,0,4]],dtype=np.float32));old=x.copy()
 a,_=restore_cp10k(x);b,_=restore_cp10k(x)
 assert np.array_equal(a.data,b.data) and np.array_equal(x.data,old.data)
