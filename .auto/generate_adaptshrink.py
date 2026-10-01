"""Iter8: per-state adaptive shrinkage (deterministic, data-frozen, single shot).

Principle (pre-committed, not scanned): small-n states have noisier mean estimates,
so their shifts deserve stronger shrinkage. Per-gene t-shrink w=t/(t+1) (as iter6)
times a per-state factor f_s = n95_s/(n95_s+n0) with n0 = median n95 over shared
states — computed from data, frozen in provenance. No RNG, no resampling, no scan.
"""
from pathlib import Path
import numpy as np
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common, ops

C = 1.0
PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / ".auto" / "candidate.h5ad"

def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    m875, v875, n875 = common.means_vars_by_label(X875, t875)
    m95, v95, n95 = common.means_vars_by_label(X95, t95)
    shared = sorted(set(m95) & set(m875))
    n0 = float(np.median([n95[s] for s in shared]))
    X_out = XV.copy()
    fstates = {}
    for s in sorted(set(tV.tolist())):
        if s in shared:
            d = (m95[s] - m875[s]).astype(np.float64)
            se = ops.se_two_means(v875[s], n875[s], v95[s], n95[s]) + 1e-12
            w = ops.shrink_weights(d, se, C=C)
            f = n95[s] / (n95[s] + n0)
            fstates[s] = round(float(f), 4)
            d = (d * w * f).astype(np.float64)
        else:
            d = np.zeros(XV.shape[1])
        X_out[tV == s] += d
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP", "iter": 8,
                                 "method": "adaptive_shrink_C1_x_statefrac",
                                 "n0_median_n95": n0, "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    print(f"iter8 adaptshrink: sha={sha[:12]} clip={clip_frac:.4f} n0={n0:.1f} "
          f"shared={len(shared)} fstates={fstates}")

if __name__ == "__main__":
    main()
