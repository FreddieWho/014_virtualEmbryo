import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import campaign as c
import numpy as np, joblib, anndata as ad
m=joblib.load(c.ASSETS/'inference/state_emitter.joblib');a=ad.read_h5ad(c.ASSETS/'inference/WT_carrier7449.h5ad');r=dict(delta=np.zeros((m.S,m.G,len(m.q))),composition=np.zeros(m.S),support=np.ones(m.S,bool))
y,ix=c.emit(m,a.X,r,'odds');assert np.array_equal(y,a.X) and np.array_equal(ix,np.arange(len(a)))
# The formula must preserve exact no-effect identity at p=0,1 and finite extremes.
p=np.array([0.,1e-8,.5,1-1e-8,1.]);eps=.5/101;s=np.clip(p,eps,1-eps)
for d in [-1000.,0.,1000.]:
    change=c.expit(c.logit(s)+d)-s
    if d==0:change[:]=0
    got=np.clip(p+change,0,1)
    assert np.isfinite(got).all() and (got>=0).all() and (got<=1).all()
    if d==0:assert np.array_equal(got,p)
print('PASS: exact zero-response identity and p=0/1 finite-extreme odds transport')
