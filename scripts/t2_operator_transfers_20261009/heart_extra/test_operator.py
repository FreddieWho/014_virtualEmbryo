import runtime
import numpy as np
from zp_operator import apply

def run():
    x=np.array([[0.,1.,2.],[2.,0.,3.],[1.,4.,0.]],np.float32)
    labels=np.array(['a','a','orphan']);states=['a'];delta=np.array([[.2,-.2,.3]],np.float32)
    y,d=apply(x,labels,states,delta,'zp')
    assert np.all(y[x==0]==0)
    assert np.array_equal(y[2],x[2])
    assert np.allclose(np.expm1(y.astype(float)).sum(1),np.expm1(x.astype(float)).sum(1),rtol=1e-6)
    # Independently spell the H2 nonzero and inverse-detection operator followed by old library rule.
    source=x[:2].astype(float);nz=source>0;f=np.maximum(nz.mean(0),.05)
    expected=np.where(nz,source+.9*delta[0]/f,0.);expected=np.maximum(expected,0.)
    c=np.expm1(expected);expected=np.log1p(c*np.expm1(source).sum(1)[:,None]/c.sum(1)[:,None]).astype(np.float32)
    assert np.array_equal(y[:2],expected)
    zero,_=apply(x,labels,states,delta,'zero_drift');assert np.array_equal(zero,x)
    old,_=apply(x,labels,states,delta,'parent');assert old[0,0]>0
    # The mandated existing clip+rescale rule has no rescue when the whole row clips away.
    pathological,diag=apply(np.ones((2,3),np.float32),np.array(['a','a']),states,np.full((1,3),-10.,np.float32),'zp')
    assert np.all(pathological==0) and diag['max_abs_library_ratio_error']==1.
    print('PASS: source zero support, orphan identity, library preservation when nondegenerate, exact H2 allocation, zero-dose identity, parent densification control, explicit all-clipped edge case (7 checks)')

if __name__=='__main__':run()
