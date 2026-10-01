"""iter13 (Route C): CORAL covariance alignment per state. NEW FAMILY.

Prior lanes only ever moved per-gene marginals (mean shift / quantile map). The
variogram channel scores the *joint* gene-gene structure, which marginals cannot fix.
CORAL re-colours the prediction's covariance to the E9.5 state covariance:

    W = Cp^{-1/2} (Cp^{1/2} C9 Cp^{1/2})^{1/2} Cp^{-1/2},   X_new = (Xp - mp) W + mp

with symmetric inverse square roots from the eigendecomposition, eigenvalues floored at
1e-8 (frozen rule, no scan). Applied per state to the FROZEN baseline (means untouched
by construction: centring cancels), so this isolates the covariance mechanism.
Deterministic, no RNG. States without E9.5 support keep their baseline values.
"""
from pathlib import Path
import numpy as np
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common

PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / ".auto" / "candidate.h5ad"
FLOOR = 1e-8


def sym_invsqrt(C: np.ndarray) -> np.ndarray:
    w, V = np.linalg.eigh(C)
    w = np.clip(w, FLOOR, None)
    return (V * (1.0 / np.sqrt(w))) @ V.T


def sym_sqrt(C: np.ndarray) -> np.ndarray:
    w, V = np.linalg.eigh(C)
    w = np.clip(w, FLOOR, None)
    return (V * np.sqrt(w)) @ V.T


def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    X_out = XV.copy()
    diag = {}
    for s in sorted(set(t95.tolist()) & set(tV.tolist())):
        Xp = XV[tV == s]
        X9 = X95[t95 == s]
        if Xp.shape[0] < 50 or X9.shape[0] < 50:
            continue
        mp = Xp.mean(0)
        Cp = np.cov(Xp - mp, rowvar=False) + FLOOR * np.eye(Xp.shape[1])
        C9 = np.cov(X9 - X9.mean(0), rowvar=False) + FLOOR * np.eye(X9.shape[1])
        Cp_sqrt = sym_sqrt(Cp)
        Cp_inv = sym_invsqrt(Cp)
        M = Cp_sqrt @ C9 @ Cp_sqrt
        W = Cp_inv @ sym_sqrt(M) @ Cp_inv
        new = (Xp - mp) @ W + mp
        X_out[tV == s] = new
        diag[s] = {"n_pred": int(Xp.shape[0]), "n9": int(X9.shape[0]),
                   "mean_abs_shift": float(np.abs(new.mean(0) - mp).mean()),
                   "std_change": float(new.std() / max(Xp.std(), 1e-12))}
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 13,
                                 "method": "coral_covariance_alignment", "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    print(f"iter13 CORAL: sha={sha[:12]} clip={clip_frac:.4f} states={len(diag)}")
    print("diag:", {k: round(v['std_change'], 3) for k, v in diag.items()})


if __name__ == "__main__":
    main()
