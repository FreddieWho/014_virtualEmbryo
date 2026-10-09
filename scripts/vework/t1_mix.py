#!/usr/bin/env python
"""Whole-row mixture of two T1 predictions (the v0051 operator: 70/30 rows of A x B, seeded, without replacement)."""
import argparse, json, sys
from pathlib import Path
import numpy as np, anndata as ad
from scipy import sparse
sys.path.insert(0, str(Path(__file__).parent))
from vecommon import format_check
ap = argparse.ArgumentParser(); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
ap.add_argument("--frac-a", type=float, default=0.7); ap.add_argument("--n", type=int, default=5118)
ap.add_argument("--seed", type=int, default=20260921); ap.add_argument("--board", default="T1:val"); ap.add_argument("--out", required=True)
a = ap.parse_args()
A, B = ad.read_h5ad(a.a), ad.read_h5ad(a.b)
assert list(A.var_names) == list(B.var_names)
rng = np.random.default_rng(a.seed); na = int(round(a.n * a.frac_a)); nb = a.n - na
ia = np.sort(rng.choice(A.n_obs, na, replace=False)); ib = np.sort(rng.choice(B.n_obs, nb, replace=False))
X = sparse.vstack([sparse.csr_matrix(A.X[ia]), sparse.csr_matrix(B.X[ib])]).tocsr()
obs = ad.concat([A[ia].obs, B[ib].obs]).copy() if False else None
import pandas as pd
names = [f"A{i}_{n}" for i, n in zip(ia, A.obs_names[ia])] + [f"B{i}_{n}" for i, n in zip(ib, B.obs_names[ib])]
out = ad.AnnData(X=X, obs=pd.DataFrame(index=names), var=pd.DataFrame(index=A.var_names))
out.uns["ve_provenance"] = json.dumps(dict(recipe="t1_row_mix", a=a.a, b=a.b, frac_a=a.frac_a, seed=a.seed, external_sources="none"))
del A, B
out.write_h5ad(a.out, compression="gzip")
fc = format_check(Path(a.out), a.board); print(json.dumps(fc)); sys.exit(0 if fc["pass"] else 1)
