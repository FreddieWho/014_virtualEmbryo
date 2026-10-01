"""iter16 (Route C): low-rank SVD denoising of the per-state mean-shift delta matrix.

Per-gene deltas estimated from a single state's cells are noisy. This borrows strength
across states: build D (S states x 500 genes) of per-state mean shifts m95-m875, take its
SVD, and reconstruct from the smallest rank that explains >= 0.90 of the squared spectrum
(frozen variance rule, no rank scan). The denoised deltas are then applied as a mean shift
to the frozen baseline (same convention as every shrink/cap lane, which keeps this a clean
single-mechanism test of the denoiser). Deterministic, no RNG.
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
ENERGY = 0.90


def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    shared = sorted(set(t95.tolist()) & set(t875.tolist()))
    D = np.stack([X95[t95 == s].mean(0) - X875[t875 == s].mean(0) for s in shared])  # (S,G)
    U, sv, Vt = np.linalg.svd(D, full_matrices=False)
    cum = np.cumsum(sv ** 2) / np.sum(sv ** 2)
    r = int(np.searchsorted(cum, ENERGY) + 1)
    D_hat = (U[:, :r] * sv[:r]) @ Vt[:r]
    X_out = XV.copy()
    shifts = {}
    for i, s in enumerate(shared):
        d = D_hat[i]
        X_out[tV == s] += d
        shifts[s] = float(np.abs(d).mean())
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 16,
                                 "method": "low_rank_svd_delta_energy0.90", "rank": r,
                                 "n_states": len(shared), "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    print(f"iter16 SVDdelta: sha={sha[:12]} clip={clip_frac:.4f} states={len(shared)} rank={r} "
          f"energy={cum[r-1]:.4f} spectrum_top5={np.round(sv[:5]/sv[0],3).tolist()}")


if __name__ == "__main__":
    main()
