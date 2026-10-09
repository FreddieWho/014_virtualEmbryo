import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/t1_quota_20261009'))
import numpy as np
from hurdle_margins import transform_column
from replicate_weights import uncertainty_weight

def test_unshrunk_exact_parent():
 p=np.array([0,0,1,3,2],np.float32);c=np.array([1,0,4,0,2],np.float32)
 assert np.array_equal(transform_column(p,c,1,1),p)

def test_zero_weights_exact_carrier_margins():
 p=np.array([0,0,1,3,2],np.float32);c=np.array([1,0,4,0,2],np.float32)
 assert np.array_equal(np.sort(transform_column(p,c,0,0)),np.sort(c))

def test_empty_parent_or_carrier_distribution():
 for p,c in [(np.zeros(6),np.array([0,0,0,1,2,3])),(np.array([0,0,0,1,2,3]),np.zeros(6))]:
  x=transform_column(p,c,.5,.5);assert np.isfinite(x).all() and (x>=0).all() and (x>0).sum()==2
 assert not transform_column(np.zeros(6),np.zeros(6),.5,.5).any()

def test_detection_rounding_and_order():
 p=np.array([0,0,1,3,2],np.float32);c=np.array([1,2,4,1,2],np.float32)
 x=transform_column(p,c,.5,.3);assert (x>0).sum()==4
 order=np.lexsort((np.arange(len(p)),c,p));assert (np.diff(x[order])>=0).all()

def test_library_units_not_correlated_pairs():
 e=np.array([[0.],[2.]]);l=np.array([[3.],[5.]]);v=np.zeros((2,1));w,d=uncertainty_weight(e,l,v,v)
 assert np.allclose(d['between_library_variance_of_mean'],2)
 assert np.allclose(w,9/11)

def test_disagreement_zeroes_reliability():
 e=np.array([[0.],[2.]]);l=np.array([[1.],[4.]]);v=np.ones((2,1))*.01
 w,_=uncertainty_weight(e,l,v,v);assert w[0]==0
 pooled,_=uncertainty_weight(e,l,v,v,pooled=True);assert pooled[0]>0
