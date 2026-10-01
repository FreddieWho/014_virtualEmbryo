"""iter18 (Route C): quantile trend extrapolation in 30-PC space. NEW MECHANISM SPACE.

mmd_unbiased and neighborhood_mmd are computed in a 30-PC space, not gene space. This
lane extrapolates the marginals of the PC SCORES instead of the genes:

  1. PCA (30 comps, the metric panel's own n_pc — not a tuned knob) fitted on the
     baseline rows (which are E9.5 cells), no scaling (log-normalised values are
     already comparable), centred.
  2. Per state: project E9.5 and E8.75 cells; per PC build quantile functions Q9, Q8 and
     extrapolate Qpred = Q9 + (Q9 - Q8); map every baseline cell through Qpred at its own
     within-state rank probability.
  3. Apply only the PC-space DELTA back to gene space: X_new = X_old + (Zpred - Z_old) @ V^T,
     so the original full-rank residual structure is preserved.

Deterministic, no RNG, no knobs.
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
GRID = 2001
NPC = 30


def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    mu = XV.mean(0)
    U, sv, Vt = np.linalg.svd(XV - mu, full_matrices=False)
    W = Vt[:NPC].T                                  # (G, NPC)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    Z_all = (XV - mu) @ W
    Z95 = (X95 - mu) @ W
    Z875 = (X875 - mu) @ W
    X_out = XV.copy()
    for s in sorted(set(t95.tolist()) & set(t875.tolist())):
        pred_idx = np.flatnonzero(tV == s)
        Zp = Z_all[pred_idx]
        o = np.argsort(Zp, axis=0, kind="stable")
        r = np.empty_like(o)
        np.put_along_axis(r, o, np.arange(len(pred_idx))[:, None].repeat(NPC, axis=1), axis=0)
        p2 = (r + 0.5) / len(pred_idx)
        Q9 = np.quantile(Z95[t95 == s], pgrid, axis=0)
        Q8 = np.quantile(Z875[t875 == s], pgrid, axis=0)
        Qpred = Q9 + (Q9 - Q8)
        Znew = np.empty_like(Zp)
        for c in range(NPC):
            Znew[:, c] = np.interp(p2[:, c], pgrid, Qpred[:, c])
        X_out[pred_idx] = XV[pred_idx] + (Znew - Zp) @ W.T
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 18,
                                 "method": "qte_in_pc_space", "n_pc": NPC, "grid": GRID,
                                 "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    evr = float((sv[:NPC] ** 2).sum() / (sv ** 2).sum())
    print(f"iter18 pcQTE: sha={sha[:12]} clip={clip_frac:.4f} evr30={evr:.4f}")


if __name__ == "__main__":
    main()
