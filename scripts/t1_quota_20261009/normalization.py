"""Parameter-free restoration of the released RNA measurement convention."""
import numpy as np
from scipy import sparse

def restore_cp10k(X):
    """Invert log1p, enforce each existing row's CP10k mass, and re-log.

    Uses float64 for every arithmetic step and casts only the final values.
    No clipping, jitter, pseudocount, randomization, gene or row selection.
    """
    Y=sparse.csr_matrix(X,dtype=np.float64,copy=True)
    if not np.isfinite(Y.data).all() or (Y.data<0).any():
        raise ValueError('Expected finite nonnegative log1p values')
    Y.data=np.expm1(Y.data)
    masses=np.asarray(Y.sum(axis=1)).ravel()
    if (masses<=0).any():raise ValueError('Zero-mass rows are not normalizable')
    for r in range(Y.shape[0]):
        lo,hi=Y.indptr[r:r+2];Y.data[lo:hi]*=10000.0/masses[r]
    Y.data=np.log1p(Y.data).astype(np.float32)
    return Y.astype(np.float32),masses
