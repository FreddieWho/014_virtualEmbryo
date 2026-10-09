import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/t1_quota_20261009'))
from hurdle_margins import transform_column
from assay_displacement import transform_positive


def test_assay_disabled_reproduces_either_component():
 p=np.array([0,0,1,2,5],np.float32);c=np.array([0,1,3,4,6],np.float32)
 for wd,wl in [(.3,1),(1,.4)]:
  component=transform_column(p,c,wd,wl)
  assert np.array_equal(transform_positive(component,c,1)[0],component)


def test_component_disabled_reproduces_assay():
 p=np.array([0,0,1,2,5],np.float32);c=np.array([0,1,3,4,6],np.float32)
 assay=transform_positive(p,c,1.4)[0]
 assert np.array_equal(transform_positive(transform_column(p,c,1,1),c,1.4)[0],assay)
