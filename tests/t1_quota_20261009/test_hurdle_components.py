import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/t1_quota_20261009'))
from hurdle_margins import transform_column,positive_at_ranks


def test_detection_only_keeps_parent_positive_curve():
 p=np.array([0,0,1,3,5],np.float32);c=np.array([1,2,4,6,8],np.float32)
 y=transform_column(p,c,0,1);q=(np.arange(5)+.5)/5
 assert (y>0).sum()==5
 assert np.array_equal(np.sort(y),positive_at_ranks(p[p>0],q).astype(np.float32))


def test_level_only_keeps_support():
 p=np.array([0,0,1,3,5],np.float32);c=np.array([1,2,4,6,8],np.float32)
 y=transform_column(p,c,1,.3)
 assert np.array_equal(y>0,p>0)


def test_both_disabled_exact_identity():
 p=np.array([0,0,.01,1,2],np.float32);c=np.array([2,3,0,.5,2],np.float32)
 assert np.array_equal(transform_column(p,c,1,1),p)
