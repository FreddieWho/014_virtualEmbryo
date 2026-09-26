#!/usr/bin/env python3
"""T1-NEXT-R5: covariance evolution with strictly fixed marginals.

Fixed gene modules (MiniBatchKMeans on standardized train gene profiles, K=32,
seed-fixed). Per coarse type: module-score correlation R85/R95 on TRAIN cells,
log-Euclidean one-step extrapolation Lpred=L95+clip(L95-L85) -> Rpred (bounded,
PSD-projected). Recipient cells (E8.5 outer) get deterministic rank
reallocation: per gene, cells ordered by target-latent module score, gene values
assigned in sorted order = pure within-column permutation -> value sets,
sparsity, column order strictly preserved (asserted).
Arm A: learned module directions. Arm B: same change norm, fixed shuffled module
permutation pi (specificity control). Unsupported types/genes: parent rows.
Controls: identity + train-fitted strict shift, same splits (R2-asserted).
Report scenario E8.5->E9.5. Diagnostic only. CPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import expm, logm
from scipy.stats import norm
from sklearn.cluster import MiniBatchKMeans
from sklearn.model_selection import train_test_split

TASK_ID = "T1-NEXT-R5"
RUN_SEED = 20260921
N_MOD = 32
EIG_CAP = 0.5  # bound on log-eigenvalue extrapolation step
MIN_N = 30
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
E85_SHA = "8eab2d0ccaa89f92861b09816b76b6a731b8ed6b5995e4af196d9ed8ff76e504"
E95_SHA = "0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def to_dense(a: ad.AnnData) -> np.ndarray:
    X = a.X
    if sparse.issparse(X):
        X = X.toarray()
    return np.asarray(X, dtype=np.float32)


def load_panel(path: Path):
    a = ad.read_h5ad(path)
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    a = a[:, panel].copy()
    X = to_dense(a)
    assert np.isfinite(X).all() and (X >= 0).all()
    return X, np.asarray(a.obs["celltype"].astype(str))


def run_scorer(inp: Path, tgt: Path, ref: Path, out: Path) -> dict:
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(inp), "--target", str(tgt),
           "--reference", str(ref), "--seed", str(RUN_SEED), "--out", str(out)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-2000:])
    return json.loads(out.read_text())["metrics"]


def write_sub(X: np.ndarray, types: np.ndarray, path: Path, panel: list[str]) -> None:
    aa = ad.AnnData(X=np.ascontiguousarray(X, dtype=np.float32),
                    obs=pd.DataFrame({"celltype": pd.Categorical(types)}),
                    var=pd.DataFrame(index=panel))
    aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    aa.uns["ve_t1_next_r5"] = json.dumps({"atom_id": TASK_ID, "seed": RUN_SEED,
                                          "diagnostic": True, "target_used": False})
    aa.write_h5ad(path)


def spd_project(R: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    R = 0.5 * (R + R.T)
    w, V = np.linalg.eigh(R)
    w = np.clip(w, floor, None)
    return (V * w) @ V.T


def to_corr(R: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.clip(np.diag(R), 1e-12, None))
    return R / np.outer(d, d)


def rank_normal(S: np.ndarray) -> np.ndarray:
    n = S.shape[0]
    r = np.empty_like(S, dtype=np.float64)
    for j in range(S.shape[1]):
        o = np.argsort(S[:, j], kind="stable")
        rk = np.empty(n)
        rk[o] = (np.arange(n) + 0.5) / n
        r[:, j] = norm.ppf(np.clip(rk, 1e-9, 1 - 1e-9))
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    res: dict = {"task": TASK_ID, "seed": RUN_SEED, "n_mod": N_MOD}
    t00 = time.time()

    assert sha256(E85) == E85_SHA and sha256(E95) == E95_SHA, "input drift"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    D = len(panel)
    X85, t85 = load_panel(E85)
    X95, t95 = load_panel(E95)
    idx85 = np.arange(len(X85))
    idx95 = np.arange(len(X95))
    tr85, tmp85 = train_test_split(idx85, test_size=0.4, random_state=RUN_SEED, stratify=t85)
    te85, _ = train_test_split(tmp85, test_size=0.5, random_state=RUN_SEED + 1,
                               stratify=t85[tmp85])
    tr95, tmp95 = train_test_split(idx95, test_size=0.4, random_state=RUN_SEED, stratify=t95)
    te95, _ = train_test_split(tmp95, test_size=0.5, random_state=RUN_SEED + 1,
                               stratify=t95[tmp95])
    assert (len(tr85), len(te85), len(tr95), len(te95)) == (10072, 3357, 10234, 3411)
    res["split_ok_r2match"] = True
    ttr85, ttr95 = t85[tr85], t95[tr95]
    X85tr, X95tr = X85[tr85].astype(np.float64), X95[tr95].astype(np.float64)
    Xr = X85[te85].astype(np.float64)
    tr_ = t85[te85]
    common = sorted(set(ttr85) & set(ttr95))
    res["types_common"] = len(common)

    # ---- fixed modules: MiniBatchKMeans on standardized train gene profiles ----
    Xtr_all = np.vstack([X85tr, X95tr])  # genes x cells -> transpose
    mu = Xtr_all.mean(axis=0)
    sd = Xtr_all.std(axis=0)
    nz = sd > 1e-12
    res["zero_var_genes"] = int((~nz).sum())
    G = ((Xtr_all[:, nz] - mu[nz]) / sd[nz]).T  # n_genes_nz x n_cells
    km = MiniBatchKMeans(n_clusters=N_MOD, random_state=RUN_SEED, batch_size=4096,
                         max_iter=50, n_init=3)
    lab_nz = km.fit_predict(G)
    mod_of_gene = np.full(D, -1, dtype=np.int64)
    mod_of_gene[np.where(nz)[0]] = lab_nz
    res["mod_sizes"] = [int((mod_of_gene == m).sum()) for m in range(N_MOD)]
    print("modules fit", flush=True)

    def mod_scores(X: np.ndarray) -> np.ndarray:
        S = np.empty((X.shape[0], N_MOD))
        for m in range(N_MOD):
            cols = np.where(mod_of_gene == m)[0]
            S[:, m] = X[:, cols].mean(axis=1) if len(cols) else 0.0
        return S

    # ---- per-type correlation evolution (constant modules dropped per type) ----
    outA = Xr.copy()
    outB = Xr.copy()
    res["evol"] = {}
    res["dropped_mods"] = {}
    for ti, c in enumerate(sorted(set(tr_))):
        if c not in common:
            continue
        A85 = X85tr[ttr85 == c]
        A95 = X95tr[ttr95 == c]
        if len(A85) < MIN_N or len(A95) < MIN_N:
            continue
        S85, S95 = mod_scores(A85), mod_scores(A95)
        v85 = S85.var(axis=0)
        v95 = S95.var(axis=0)
        active = [m for m in range(N_MOD) if v85[m] > 1e-12 and v95[m] > 1e-12]
        res["dropped_mods"][c] = [m for m in range(N_MOD) if m not in active]
        S85a, S95a = S85[:, active], S95[:, active]
        k = len(active)
        if k < 2:
            continue
        R85 = np.corrcoef(S85a.T)
        R95 = np.corrcoef(S95a.T)
        L85 = np.real(logm(spd_project(R85))).astype(np.float64)
        L95 = np.real(logm(spd_project(R95))).astype(np.float64)
        Dl = L95 - L85
        w, V = np.linalg.eigh(0.5 * (Dl + Dl.T))
        w = np.clip(w, -EIG_CAP, EIG_CAP)
        Dlc = (V * w) @ V.T
        Rpred = to_corr(spd_project(np.real(expm(L95 + Dlc))))
        res["evol"][c] = {
            "frob_95_85": float(np.linalg.norm(R95 - R85)),
            "frob_pred_95": float(np.linalg.norm(Rpred - R95)),
        }
        # recipient latent with target correlation (active modules only)
        m = (tr_ == c)
        Sr = mod_scores(Xr[m])[:, active]
        Z = rank_normal(Sr)
        Cz = np.corrcoef(Z.T)
        Cz = 0.9 * Cz + 0.1 * np.eye(k)
        W = Z @ np.linalg.inv(np.linalg.cholesky(spd_project(Cz))).T
        Tlat = (np.linalg.cholesky(spd_project(Rpred)) @ W.T).T
        srt = np.argsort(Tlat, axis=0, kind="stable")  # per-module cell order
        pi = np.random.RandomState(RUN_SEED + ti).permutation(k)
        rec_idx = np.where(m)[0]
        pos = {gm: j for j, gm in enumerate(active)}
        for g in range(D):
            gm = mod_of_gene[g]
            if gm < 0 or gm not in pos:
                continue
            j = pos[gm]
            vals = np.sort(Xr[m][:, g], kind="stable")
            outA[rec_idx[srt[:, j]], g] = vals
            outB[rec_idx[srt[:, pi[j]]], g] = vals
        print(f"type {c}: assigned", flush=True)

    # ---- asserts: value sets strictly preserved ----
    for name, O in (("A", outA), ("B", outB)):
        S_in = np.sort(Xr, axis=0)
        S_out = np.sort(O, axis=0)
        assert np.array_equal(S_in, S_out), f"{name}: column value sets changed"
        assert (np.asarray((O == 0)).mean() == np.asarray((Xr == 0)).mean()), f"{name}: sparsity changed"
    res["marginal_assert"] = "PASS (column value sets + sparsity identical)"
    # output correlation movement diagnostic (common types pooled module scores)
    res["lib_mean"] = {k: float(v.sum(axis=1).mean())
                       for k, v in (("source", Xr), ("A", outA), ("B", outB))}

    mu85 = {c: X85tr[ttr85 == c].mean(axis=0) for c in common}
    mu95 = {c: X95tr[ttr95 == c].mean(axis=0) for c in common}
    Gshift = np.stack([(mu95[c] - mu85[c]) if c in common
                       else np.zeros(D) for c in tr_])
    arms = {
        "identity": Xr.copy(),
        "strict_shift": np.clip(Xr + Gshift, 0.0, None),
        "A_covdir": np.clip(outA, 0.0, None).astype(np.float32),
        "B_shuffled": np.clip(outB, 0.0, None).astype(np.float32),
    }
    res["zero_rate"] = {k: float((np.asarray(v) == 0).mean()) for k, v in arms.items()}

    tgt = RUN / "intermediates" / "pseudo_target_e95_outer.h5ad"
    ref = RUN / "intermediates" / "reference_e85_train.h5ad"
    write_sub(X95[te95].astype(np.float32), t95[te95], tgt, panel)
    write_sub(X85[tr85].astype(np.float32), t85[tr85], ref, panel)
    res["lib_mean"]["e95_outer"] = float(X95[te95].sum(axis=1).mean())

    KEEP = ("de_score", "de_direction", "energy_distance", "mmd_u", "variogram",
            "pb_rel_err", "library_size_ratio", "variance_ratio", "composition_JSD",
            "pseudobulk_pearson")
    res["arms"] = {}
    for name, X in arms.items():
        p = RUN / "intermediates" / f"arm_{name}.h5ad"
        write_sub(np.asarray(X, dtype=np.float32), tr_, p, panel)
        mout = RUN / "metrics" / f"scorer_{name}.json"
        m = run_scorer(p, tgt, ref, mout)
        res["arms"][name] = {k: m.get(k) for k in KEEP}
        print(f"ARM {name}: " + json.dumps(res["arms"][name]), flush=True)

    res["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
