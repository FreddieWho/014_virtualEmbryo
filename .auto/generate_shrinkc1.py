"""Iter6: baseline delta x t-shrink C=1, float64 path (deterministic, no resampling).

Fills a real gap: x_r2_shrinkc1 (goal R2) used the float32 shrunk_delta path with
C=1 and scored server 50.03 REJECT, but its LOCAL proxy value was never recorded.
This rebuilds the same mechanism via ops.shrink_weights (float64, identical math
to x_o1/x_o2 lineage modulo precision) on baseline d=mu95-mu875. Fully
deterministic: no RNG, no row luck, so any |Δde|>=0.005 is mechanism signal.
Single knob (C=1 frozen, no scan).
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
    X_out = XV.copy()
    wmeans = []
    for s in sorted(set(tV.tolist())):
        if s in shared:
            d = (m95[s] - m875[s]).astype(np.float64)
            se = ops.se_two_means(v875[s], n875[s], v95[s], n95[s]) + 1e-12
            w = ops.shrink_weights(d, se, C=C)
            wmeans.append(float(np.mean(w)))
            d = (d * w).astype(np.float64)
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
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP", "iter": 6,
                                 "method": f"baseline_delta_shrinkC{C}_f64",
                                 "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    print(f"iter6 shrinkC{C}-f64: sha={sha[:12]} clip={clip_frac:.4f} "
          f"mean_w={float(np.mean(wmeans)):.4f} shared={len(shared)}")

if __name__ == "__main__":
    main()
