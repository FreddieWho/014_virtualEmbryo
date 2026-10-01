"""Iter4: composition-only extrap (new route, never tried on extrap).

Mirrors the e_r1/h_r1 compotrend wins on interp boards: predict E10.5 (t=10.5)
celltype shares via LOG-LINEAR trend over E8.25_late/E8.75/E9.5 shares (linear only,
no quadratic knob), resample BASELINE rows to those shares, expression/geometry
byte-identical to baseline. Isolates the composition channel: if DE moves, the
signal is compositional; if not, extrap DE is expression-locked.
Deterministic, seed 20261002 fixed. Fallback: states missing in any stage keep
baseline shares.
"""
from pathlib import Path
import numpy as np
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common, ops

SEED = 20261002
T_EVAL = 10.5
PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / ".auto" / "candidate.h5ad"

def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    vnames = [str(v) for v in V.obs_names]
    n = int(V.n_obs)
    stages = {}
    for key, rel in (("e825", "data/E8.25_late.h5ad"), ("e875", "data/E8.75.h5ad"),
                     ("e95", "data/E9.5.h5ad")):
        X, t, _, _ = common.load_stage(rel, panel)
        stages[key] = (X, t)
    times = np.array([8.25, 8.75, 9.5])
    pV = common.shares(tV)
    pseries = [common.shares(stages[k][1]) for k in ("e825", "e875", "e95")]
    three = sorted(set(pV) & set().union(*[set(d) for d in pseries]))
    raw = {}
    for s in sorted(set(tV.tolist())):
        series = [d.get(s, 0.0) for d in pseries]
        if s in three and all(v > 0 for v in series):
            raw[s] = ops.share_series_predict(times, np.array(series), T_EVAL)
        else:
            raw[s] = pV.get(s, 0.0)
    pstates = sorted(set(tV.tolist()))
    counts, rawn = common.counts_from_raw(raw, pstates, n)
    chosen = common.select_rows(tV, counts, SEED)
    final = common.dedup_names([vnames[i] for i in chosen])
    X_out = XV[chosen]  # expression identical to baseline rows
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V[chosen].copy()
    out_a.obs_names = final
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP", "iter": 4,
                                 "method": "comp_only_loglinear_t10.5", "seed": SEED,
                                 "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    n_trend = len([s for s in pstates if s in three and all(d.get(s, 0.0) > 0 for d in pseries)])
    print(f"iter4 comp-only: sha={sha[:12]} n_trend={n_trend} "
          f"n_fallback={len(pstates) - n_trend} expr_identical_to_baseline=True")

if __name__ == "__main__":
    main()
