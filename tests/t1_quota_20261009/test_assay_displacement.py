import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/t1_quota_20261009'))
from assay_displacement import transform_positive


def test_identity():
 p=np.array([0,1,3,0,7],np.float32);c=np.array([0,2,0,4,6],np.float32)
 assert np.array_equal(transform_positive(p,c,1)[0],p)


def test_empty_sides():
 p=np.array([0,1,2],np.float32)
 assert np.array_equal(transform_positive(p,p*0,1.8)[0],p)
 assert np.array_equal(transform_positive(p*0,p,1.8)[0],p*0)


def test_convex_case_preserves_support_order():
 p=np.array([0,1,4,2],np.float32);c=np.array([1,3,7,0],np.float32)
 v,s=transform_positive(p,c,.7)
 assert np.array_equal(v>0,p>0)
 assert np.all(np.diff(v[np.argsort(p)])>=0)
 assert s['negative_steps']==0


def test_crossing_audited_even_without_floor():
 p=np.array([10,11,12],np.float32);c=np.array([2,4,7],np.float32)
 v,s=transform_positive(p,c,2)
 assert s['floored']==0 and s['negative_steps']==1 and s['reordered']==3
 assert np.array_equal(v,np.array([17,18,18],np.float32))
 assert s['repair_abs_max']==1
