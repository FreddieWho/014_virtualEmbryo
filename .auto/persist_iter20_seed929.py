"""Persist the TRUE median-value seed (20260929, composite 3.913) of the iter20 champion."""
from pathlib import Path
import numpy as np, sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common
from scripts.t2_round2 import run as r2run

SEED = 20260929
PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
GRID = 2001
FACTOR = 4.0 / 3.0
OUT = REPO / "artifacts" / "autoresearch" / "t2-extrap-20261001-v1" / "submission.iter20-qte-time-compmix.seed20260929.h5ad"

panel = common.read_panel(PANEL)
V = common.load_parent(PARENT, PARENT_SHA)
XV = common.dense(V.X).astype(np.float64)
tV = np.asarray(V.obs["celltype"].astype(str))
X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
pgrid = (np.arange(GRID) + 0.5) / GRID
Xq = XV.copy()
for s in sorted(set(t95.tolist()) & set(t875.tolist())):
    pred_idx = np.flatnonzero(tV == s)
    Xs = XV[pred_idx]
    o = np.argsort(Xs, axis=0, kind="stable")
    r = np.empty_like(o)
    np.put_along_axis(r, o, np.arange(len(pred_idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
    p2 = (r + 0.5) / len(pred_idx)
    Q9 = np.quantile(X95[t95 == s], pgrid, axis=0)
    Q8 = np.quantile(X875[t875 == s], pgrid, axis=0)
    Qpred = Q9 + FACTOR * (Q9 - Q8)
    new = np.empty_like(Xs)
    for g in range(Xs.shape[1]):
        new[:, g] = np.interp(p2[:, g], pgrid, Qpred[:, g])
    Xq[pred_idx] = new
Xq = np.clip(Xq, 0, None)
ctx = r2run.ExtrapCtx(common.load_config()["boards"]["extrap"])
chosen, final, counts, raw_n, types = r2run.compmix_plan(ctx, SEED)
out_a = V[chosen].copy()
out_a.obs_names = final
out_a.X = np.ascontiguousarray(Xq[chosen], dtype=np.float32)
common.fix_obsm(out_a)
common.stamp_uns(out_a, normalization="log_normalized",
                 provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 20,
                             "method": "qte_time_normalized_4over3_x_compmix",
                             "seed": SEED, "role": "median_value_seed_of_3", "target_used": False})
if OUT.exists():
    OUT.unlink()
sha = common.write_candidate(out_a, OUT)
print("seed", SEED, "->", OUT.name, sha[:16])
