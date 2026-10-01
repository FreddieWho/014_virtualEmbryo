"""Iter1: late-anchor blend alpha=0.5 (new route, interior never tried).

Delta = 0.5*(mu95-mu875) + 0.5*(mu95-mu825late) applied to baseline-001 rows.
Endpoints: alpha=1 -> baseline shift; alpha=0 -> x_r1_lateref (server 50.74).
Deterministic, seed recorded in uns (no RNG used).
"""
from pathlib import Path
import numpy as np
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common

ALPHA = 0.5
PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / ".auto" / "candidate.h5ad"

def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X825, t825, _, _ = common.load_stage("data/E8.25_late.h5ad", panel)
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    m825, _, _ = common.means_vars_by_label(X825, t825)
    m875, _, _ = common.means_vars_by_label(X875, t875)
    m95, _, _ = common.means_vars_by_label(X95, t95)
    shared = sorted(set(m95) & set(m875) & set(m825))
    X_out = XV.copy()
    for s in sorted(set(tV.tolist())):
        if s in shared:
            d = (ALPHA * (m95[s] - m875[s]) + (1 - ALPHA) * (m95[s] - m825[s])).astype(np.float64)
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
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP", "iter": 1,
                                 "method": f"late_anchor_blend_alpha{ALPHA}", "target_used": False})
    if OUT.exists():
        OUT.unlink()
    # write_candidate refuses overwrite, so write via temp then move through it
    sha = common.write_candidate(out_a, OUT)
    print(f"iter1 blend{ALPHA}: sha={sha[:12]} clip={clip_frac:.4f} shared={len(shared)}")

if __name__ == "__main__":
    main()
