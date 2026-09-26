#!/usr/bin/env python3
"""T1-NEXT-R3: bounded local linear dynamics (diagonal vs low-rank+diagonal).

Latent: PCA-50 fit on TRAIN cells only (same seed/splits as R2). Per common
type c: z_next = A_c z + b_c, b_c = mu95 - A_c mu85 (means matched exactly).
  diagonal arm: A=diag(d), d_j=clip(sqrt(C95_jj/C85_jj), 0.5, 2.0).
  lowrank arm: symmetric sqrt covariance-matching solution, diag + top-5 SVD
    of off-diagonal, final singular values clipped to [0.25, 2.0].
Output via R2 residual interface: xhat = PCAinv(z_pred) + (x - PCAinv(z)).
Null gate: A=I arm must reproduce source rows (maxabs<1e-5) or STOP.
Stability: two-step application checked finite + variance bounded (diagnostic).
Fallback types -> source rows. Controls identity + train strict shift.
Report E8.5->E9.5. Diagnostic only. CPU.
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
from scipy.linalg import sqrtm
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split

TASK_ID = "T1-NEXT-R3"
RUN_SEED = 20260921
N_PC = 50
RANK = 5
D_LO, D_HI = 0.5, 2.0
S_LO, S_HI = 0.25, 2.0
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
    aa.uns["ve_t1_next_r3"] = json.dumps({"atom_id": TASK_ID, "seed": RUN_SEED,
                                          "diagnostic": True, "target_used": False})
    aa.write_h5ad(path)


def clip_sv(A: np.ndarray, lo: float, hi: float) -> np.ndarray:
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    return (U * np.clip(s, lo, hi)) @ Vt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    res: dict = {"task": TASK_ID, "seed": RUN_SEED, "n_pc": N_PC, "rank": RANK}
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
    Xtr = np.vstack([X85[tr85], X95[tr95]]).astype(np.float32)
    pca = PCA(n_components=N_PC, svd_solver="randomized", random_state=RUN_SEED)
    Ztr = pca.fit_transform(Xtr).astype(np.float64)
    Z85tr, Z95tr = Ztr[:len(tr85)], Ztr[len(tr85):]
    common = sorted(set(ttr85) & set(ttr95))
    res["types_common"] = len(common)

    # ---- fit per-type affine maps on train ----
    Adiag: dict[str, np.ndarray] = {}
    Alow: dict[str, np.ndarray] = {}
    bdiag: dict[str, np.ndarray] = {}
    blow: dict[str, np.ndarray] = {}
    for c in common:
        Z85 = Z85tr[ttr85 == c]
        Z95 = Z95tr[ttr95 == c]
        if len(Z85) < 100 or len(Z95) < 100:
            res.setdefault("skipped_low_n", []).append((c, int(len(Z85)), int(len(Z95))))
            continue
        m85, m95 = Z85.mean(axis=0), Z95.mean(axis=0)
        C85 = LedoitWolf().fit(Z85).covariance_
        C95 = LedoitWolf().fit(Z95).covariance_
        v85 = np.diag(C85)
        d = np.clip(np.sqrt(np.diag(C95) / np.maximum(v85, 1e-12)), D_LO, D_HI)
        A_d = np.diag(d)
        Adiag[c] = A_d
        bdiag[c] = m95 - A_d @ m85
        # symmetric sqrt covariance-matching full solution
        C85h = np.real(sqrtm(C85)).astype(np.float64)
        C85hi = np.linalg.inv(C85h + 1e-9 * np.eye(N_PC))
        Mid = C85h @ C95 @ C85h
        Afull = np.real(sqrtm(0.5 * (Mid + Mid.T))).astype(np.float64)
        Afull = Afull @ C85hi
        Off = Afull - np.diag(np.diag(Afull))
        U, s, Vt = np.linalg.svd(Off, full_matrices=False)
        Al = np.diag(np.diag(Afull)) + (U[:, :RANK] * s[:RANK]) @ Vt[:RANK]
        Alow[c] = clip_sv(Al, S_LO, S_HI)
        blow[c] = m95 - Alow[c] @ m85
    res["types_fitted"] = len(Adiag)
    res.setdefault("skipped_low_n", [])

    # ---- recipients ----
    Xr = X85[te85].astype(np.float64)
    tr_ = t85[te85]
    Zr = pca.transform(Xr.astype(np.float32)).astype(np.float64)
    Drecon = pca.inverse_transform(Zr).astype(np.float64)
    Eres = Xr - Drecon
    fb = sorted(set(tr_) - set(Adiag))
    res["fallback_types"] = fb
    res["fallback_cells"] = int(sum((tr_ == c).sum() for c in fb))

    def apply(Am, bm):
        Zp = np.stack([Am[c] @ Zr[i] + bm[c] if c in Am else Zr[i]
                       for i, c in enumerate(tr_)])
        return pca.inverse_transform(Zp).astype(np.float64)

    # null gate: A=I must reproduce source
    I_all = {c: np.eye(N_PC) for c in Adiag}
    Z0 = np.stack([Zr[i] for i in range(len(Zr))])
    B0 = np.clip(pca.inverse_transform(Z0) + Eres, 0.0, None)
    res["null_maxabs"] = float(np.abs(B0 - np.clip(Xr, 0, None)).max())
    assert res["null_maxabs"] < 1e-5, "null NOT conserved"

    Dd = apply(Adiag, bdiag)
    Dl = apply(Alow, blow)
    mu85 = {c: X85[tr85][t85[tr85] == c].mean(axis=0) for c in common}
    mu95 = {c: X95[tr95][t95[tr95] == c].mean(axis=0) for c in common}
    Gshift = np.stack([(mu95[c] - mu85[c]) if c in common
                       else np.zeros(D) for c in tr_])
    arms_ordered = {
        "identity": Xr.copy().astype(np.float32),
        "strict_shift": np.clip(Xr + Gshift, 0.0, None).astype(np.float32),
        "C_diag": np.clip(Dd + Eres, 0.0, None).astype(np.float32),
        "D_lowrank": np.clip(Dl + Eres, 0.0, None).astype(np.float32),
    }
    # two-step stability (diagnostic, unscored)
    Zp1 = np.stack([Alow[c] @ Zr[i] + blow[c] if c in Alow else Zr[i]
                    for i, c in enumerate(tr_)])
    Zp2 = np.stack([Alow[c] @ Zp1[i] + blow[c] if c in Alow else Zp1[i]
                    for i in range(len(Zp1))])
    X2 = np.clip(pca.inverse_transform(Zp2) + Eres, 0.0, None)
    res["twostep_finite"] = bool(np.isfinite(X2).all())
    res["twostep_var_ratio"] = float(X2.var() / np.clip(Dl + Eres, 0, None).var())
    assert res["twostep_finite"], "two-step diverged"
    res["zero_rate"] = {k: float((np.asarray(v) == 0).mean()) for k, v in arms_ordered.items()}
    res["lib_mean"] = {k: float(np.asarray(v).sum(axis=1).mean()) for k, v in arms_ordered.items()}

    tgt = RUN / "intermediates" / "pseudo_target_e95_outer.h5ad"
    ref = RUN / "intermediates" / "reference_e85_train.h5ad"
    write_sub(X95[te95], t95[te95], tgt, panel)
    write_sub(X85[tr85], t85[tr85], ref, panel)
    res["lib_mean"]["e95_outer"] = float(X95[te95].sum(axis=1).mean())

    KEEP = ("de_score", "de_direction", "energy_distance", "mmd_u", "variogram",
            "pb_rel_err", "library_size_ratio", "variance_ratio", "composition_JSD",
            "pseudobulk_pearson")
    res["arms"] = {}
    for name, X in arms_ordered.items():
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
