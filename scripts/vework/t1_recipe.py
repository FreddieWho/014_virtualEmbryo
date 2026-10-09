#!/usr/bin/env python
"""T1 (whole-transcriptome, no coords) memory-bounded builders from released RNA stages.

copy_last : stratified draw of n cells of the LAST stage (official floor construction class)
shift     : shrunk pseudobulk shift (first-cycle T1 recipe): delta_s = w*(mu_last(s)-mu_prev(s)) + (1-w)*delta_global
            (types absent from prev use delta_global), x' = x + damp*timescale*delta_s, clip 0, then per-cell log1p
            library restored to `lib` (expm1 row sums), processed in row chunks; sparse inputs never densified whole.
NOT a replay of v0051 (70/30 row mix of v0036 x v0038): those parents depend on deep non-git artifact chains.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np, anndata as ad, pandas as pd
from scipy import sparse
sys.path.insert(0, str(Path(__file__).parent))
from vecommon import DATA, panel, format_check


def type_means(A, lab):
    X = A.X.tocsr() if sparse.issparse(A.X) else A.X
    out = {}
    for s in np.unique(lab):
        idx = np.flatnonzero(lab == s)
        out[s] = (np.asarray(X[idx].mean(0)).ravel().astype(np.float64), len(idx))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", default="E8.5_RNA:8.5"); ap.add_argument("--last", default="E9.5_RNA:9.5")
    ap.add_argument("--target", type=float, default=10.5); ap.add_argument("--n", type=int, default=5118)
    ap.add_argument("--method", choices=["copy_last", "shift"], default="shift")
    ap.add_argument("--w", type=float, default=0.5); ap.add_argument("--damp", type=float, default=0.5)
    ap.add_argument("--timescale", choices=["none", "linear"], default="linear")
    ap.add_argument("--zero-preserve", action="store_true"); ap.add_argument("--lib", type=float, default=10000.0); ap.add_argument("--seed", type=int, default=20261008)
    ap.add_argument("--board", default="T1:val"); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    g = panel(a.board)
    (np_, tp), (nl, tl) = [(s.rsplit(":", 1)[0], float(s.rsplit(":", 1)[1])) for s in (a.prev, a.last)]
    L = ad.read_h5ad(DATA / f"{nl}.h5ad")
    assert [str(x) for x in L.var_names] == g, "last stage gene order != T1 panel"
    labL = np.asarray(L.obs["celltype"]).astype(str)
    rng = np.random.default_rng(a.seed)
    shares = {s: (labL == s).mean() for s in np.unique(labL)}
    counts = {s: int(a.n * p) for s, p in shares.items()}
    rem = sorted(shares, key=lambda s: (a.n * shares[s] - counts[s], s), reverse=True)
    for i in range(a.n - sum(counts.values())): counts[rem[i]] += 1
    rows = np.sort(np.concatenate([rng.choice(np.flatnonzero(labL == s), k, replace=False) for s, k in counts.items() if k]))
    XL = L.X.tocsr()
    prov = dict(recipe=f"t1_{a.method}", prev=a.prev, last=a.last, target=a.target, n=a.n, seed=a.seed, external_sources="none")
    if a.method == "copy_last":
        Xout = XL[rows].astype(np.float32)
    else:
        mL = type_means(L, labL)
        P = ad.read_h5ad(DATA / f"{np_}.h5ad"); assert [str(x) for x in P.var_names] == g
        labP = np.asarray(P.obs["celltype"]).astype(str); mP = type_means(P, labP)
        gl = np.asarray(XL.mean(0)).ravel() - np.asarray(P.X.mean(0)).ravel(); del P
        ts = (a.target - tl) / (tl - tp) if a.timescale == "linear" else 1.0
        deltas = {s: (a.w * (mL[s][0] - mP[s][0]) + (1 - a.w) * gl) if s in mP else gl for s in mL}
        blocks = []
        lab_r = labL[rows]
        detfrac = {}
        if a.zero_preserve:
            for c in np.unique(labL):
                sub = XL[np.flatnonzero(labL == c)]
                detfrac[c] = np.maximum(np.bincount(sub.indices, minlength=XL.shape[1]) / sub.shape[0] if sparse.isspmatrix_csr(sub) else (np.asarray((sub > 0).mean(0)).ravel()), 0.05)
        for st in range(0, len(rows), 512):
            r = rows[st:st + 512]; B = XL[r].toarray().astype(np.float64)
            for s in np.unique(lab_r[st:st + 512]):
                m = lab_r[st:st + 512] == s
                if a.zero_preserve:   # move detected entries only, rescaled by the type's detected fraction
                    nzB = B[m] > 0
                    B[m] = np.where(nzB, B[m] + a.damp * ts * deltas[s] / detfrac[s], 0.0)
                else:
                    B[m] += a.damp * ts * deltas[s]
            np.clip(B, 0, None, out=B)
            E = np.expm1(B); E *= (a.lib / np.maximum(E.sum(1), 1e-12))[:, None]
            B = np.log1p(E).astype(np.float32); B[B < 1e-6] = 0
            blocks.append(sparse.csr_matrix(B))
        Xout = sparse.vstack(blocks).tocsr()
        prov.update(zero_preserve=a.zero_preserve, w=a.w, damp=a.damp, timescale=a.timescale, time_factor=ts, lib=a.lib,
                    mapped_types=sorted(set(mL) & set(mP)), unmapped_types=sorted(set(mL) - set(mP)))
    obs = pd.DataFrame(index=[f"{n}__r{i}" for i, n in enumerate(np.asarray(L.obs_names)[rows])])
    obs["celltype"] = labL[rows]
    out = ad.AnnData(X=Xout, obs=obs, var=pd.DataFrame(index=g)); out.uns["ve_provenance"] = json.dumps(prov, default=str)
    del L, XL
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); out.write_h5ad(a.out, compression="gzip")
    fc = format_check(Path(a.out), a.board)
    print(json.dumps({"provenance": prov, "format_check": fc}, indent=1, default=str))
    return 0 if fc["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
