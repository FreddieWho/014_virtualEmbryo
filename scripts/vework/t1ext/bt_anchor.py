"""Backtest E8.5 -> E9.5 (released only): carrier = E8.5 cells (disjoint from the ref draw), shift by the
external within-batch trajectory x warp fraction; score vs E9.5 with the official T1 metric code.
Primary readout: raw de_score / de_direction (floor exactly 0, same as server floor) — these do not depend on
the unreliable local ceilings. mmd_u/variogram reported raw vs the copy carrier only as sanity."""
import sys, json, numpy as np, scipy.sparse as sp, anndata as ad
sys.path.insert(0, "/workspace/ve/veckit_latest")
from common.core_metrics import de_score, de_direction, mmd_unbiased, variogram_score
import anchor as A
from label_means_const import COARSE
VE = "/workspace/ve"
a85 = ad.read_h5ad(f"{VE}/data/E8.5_RNA.h5ad"); a95 = ad.read_h5ad(f"{VE}/data/E9.5_RNA.h5ad")
X85 = a85.X.tocsr(); X95 = a95.X.tocsr(); g85 = a85.obs.celltype.astype(str).map(COARSE).values
A.set_inext(ad.read_h5ad(f"{VE}/ext/proc/GSM7226272_E14_5_1.h5ad", backed="r").var["in_external"].values)
frac = A.warp_fraction(8.5, 9.5)
def deltas(groups, perm=None, late=14.5):
    out = {}
    for g in groups:
        d = A.ext_delta(g, late)
        if d is None: continue
        d = d.copy(); d[A.ambient_mask(g, late)] = 0
        if perm is not None: d = d[perm]
        out[g] = frac * d
    return out
def avg1416(groups):
    d14 = deltas(groups, late=14.5); out = {}
    f14 = A.warp_fraction(8.5, 9.5); f16 = A.warp_fraction(8.5, 9.5, t_b=16.5)
    for g, v in d14.items():
        d16 = A.ext_delta(g, 16.5)
        if d16 is None: out[g] = v; continue
        d16 = d16.copy(); d16[A.ambient_mask(g, 16.5)] = 0
        out[g] = 0.5 * v + 0.5 * f16 * d16
    return out
ALL = deltas(A.GROUPS)
V2 = {"A_all_x2": {k: 2 * v for k, v in ALL.items()}, "A_all_x3": {k: 3 * v for k, v in ALL.items()},
      "A_all_x5": {k: 5 * v for k, v in ALL.items()}, "A_all_1416": avg1416(A.GROUPS),
      "A_all_1416_x3": {k: 3 * v for k, v in avg1416(A.GROUPS).items()}}
V3 = {"A_all_x2": V2["A_all_x2"], "A_all_x2_comp": V2["A_all_x2"], "A_all_x2_comp_half": V2["A_all_x2"]}
V4 = {"copy": {}, "A_all_x1": ALL, "A_all_x2_comp_half": V2["A_all_x2"]}
V = V4 if "--v4" in sys.argv else V3 if "--v3" in sys.argv else V2 if "--v2" in sys.argv else {"copy": {}, "A_cm": deltas(["CM_V", "CM_A"]), "A_core": deltas(["CM_V", "CM_A", "ENDO", "EPI"]),
     "A_all": deltas(A.GROUPS), "A_core_perm": deltas(["CM_V", "CM_A", "ENDO", "EPI"], perm=np.random.default_rng(1).permutation(len(A.GENES))),
     "A_core_x3": {k: 3 * v for k, v in deltas(["CM_V", "CM_A", "ENDO", "EPI"]).items()}}

res = {k: [] for k in V}
for seed in range(3):
    rng = np.random.default_rng(100 + seed)
    ref = rng.choice(X85.shape[0], 1706, replace=False); pool = np.setdiff1d(np.arange(X85.shape[0]), ref)
    car = rng.choice(pool, 5118, replace=False); tru = rng.choice(X95.shape[0], 1249, replace=False)
    R = X85[ref].toarray(); T = X95[tru].toarray()
    for k, d in V.items():
        c = car
        if "_comp" in k:
            w, info = A.comp_weights(g85[pool], frac, strength=0.5 if k.endswith("half") else 1.0)
            c = rng.choice(pool, 5118, replace=False, p=w / w.sum())
            if seed == 0: print(k, info)
        P = A.zp_shift(X85[c], g85[c], d) if d else X85[c]
        Pd = P.toarray()
        ds = de_score(Pd, T, R)
        row = {"de_score": ds["score"], "de_direction": de_direction(Pd, T, R), "chance": ds["chance"],
               "mmd_u": mmd_unbiased(Pd, T, seed=seed), "variogram": variogram_score(Pd, T, seed=seed)}
        res[k].append(row); print(seed, k, {a: round(b, 4) for a, b in row.items()}, flush=True)
        del Pd
mean = {k: {m: float(np.mean([r[m] for r in v])) for m in v[0]} for k, v in res.items()}
print(json.dumps(mean, indent=1))
json.dump({"per_seed": res, "mean": mean, "frac": frac}, open(f"{VE}/backtests/t1_anchor_e85_e95" + ("_v4_masked" if "--v4" in sys.argv else "_v3" if "--v3" in sys.argv else "_v2" if "--v2" in sys.argv else "") + ".json", "w"), indent=1)
