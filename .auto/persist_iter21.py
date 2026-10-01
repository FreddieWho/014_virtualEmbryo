"""Persist iter21 (share-trend composition x time-normalized QTE), seed 20261008, for the upload probe."""
from pathlib import Path
import numpy as np, sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common, ops
SEED = 20261007
FACTOR = 4.0 / 3.0
TIMES = np.array([8.25, 8.75, 9.5]); TT = 10.5; GRID = 2001
PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / "artifacts/autoresearch/t2-extrap-20261001-v1/submission.iter21-sharetrend-qte.h5ad"
panel = common.read_panel(PANEL)
V = common.load_parent(PARENT, PARENT_SHA)
XV = common.dense(V.X).astype(np.float64)
tV = np.asarray(V.obs["celltype"].astype(str))
vnames = [str(v) for v in V.obs_names]
st = {}
for k, rel in (("e825", "data/E8.25_late.h5ad"), ("e875", "data/E8.75.h5ad"), ("e95", "data/E9.5.h5ad")):
    X, t, _, _ = common.load_stage(rel, panel); st[k] = (X, t)
pgrid = (np.arange(GRID) + 0.5) / GRID
Xq = XV.copy()
for s in sorted(set(st["e95"][1].tolist()) & set(st["e875"][1].tolist())):
    idx = np.flatnonzero(tV == s); Xs = XV[idx]
    o = np.argsort(Xs, axis=0, kind="stable"); r = np.empty_like(o)
    np.put_along_axis(r, o, np.arange(len(idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
    p2 = (r + 0.5) / len(idx)
    Q9 = np.quantile(st["e95"][0][st["e95"][1] == s], pgrid, axis=0)
    Q8 = np.quantile(st["e875"][0][st["e875"][1] == s], pgrid, axis=0)
    Qp = Q9 + FACTOR * (Q9 - Q8)
    for g in range(Xs.shape[1]):
        Xq[idx, g] = np.interp(p2[:, g], pgrid, Qp[:, g])
Xq = np.clip(Xq, 0, None)
pV = common.shares(tV); pser = [common.shares(st[k][1]) for k in ("e825", "e875", "e95")]
pstates = sorted(set(tV.tolist())); three = sorted(set(pV) & set().union(*[set(d) for d in pser]))
raw = {s: (ops.share_series_predict(TIMES, np.array([d.get(s, 0.0) for d in pser]), TT)
           if (s in three and all(d.get(s, 0.0) > 0 for d in pser)) else pV.get(s, 0.0)) for s in pstates}
counts, rawn = common.counts_from_raw(raw, pstates, int(V.n_obs))
chosen = common.select_rows(tV, counts, SEED)
out_a = V[chosen].copy(); out_a.obs_names = common.dedup_names([vnames[i] for i in chosen])
out_a.X = np.ascontiguousarray(Xq[chosen], dtype=np.float32)
common.fix_obsm(out_a)
common.stamp_uns(out_a, normalization="log_normalized",
                 provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 21, "seed": SEED,
                             "method": "share_lin_trend_x_qte_time4over3", "target_used": False})
if OUT.exists(): OUT.unlink()
print("iter21 persisted:", OUT.name, common.write_candidate(out_a, OUT)[:16])
