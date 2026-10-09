"""Sanity backtest E8.5 -> E9.5 (released data only, same draws as bt_anchor --v4): copy vs LA x1 vs OT x1."""
import sys, json, pickle, time, numpy as np, anndata as ad
sys.path.insert(0, "/workspace/ve/veckit_latest"); sys.path.insert(0, "/workspace/ve/vework/t1ext")
from common.core_metrics import de_score, de_direction, mmd_unbiased, variogram_score
import anchor as A, otfield as O
from label_means_const import COARSE
from pathlib import Path
VE = "/workspace/ve"; W = Path(f"{VE}/work/t1r3")
A.set_inext(ad.read_h5ad(f"{VE}/ext/proc/GSM7226272_E14_5_1.h5ad", backed="r").var["in_external"].values)
fp = W / "fields_14.5.pkl"
if fp.exists(): fields = pickle.loads(fp.read_bytes())
else:
    t0 = time.time(); fields = O.build_fields(log=lambda m: print(m, flush=True)); fp.write_bytes(pickle.dumps(fields, protocol=5)); print("fields", round(time.time() - t0), "s", flush=True)
if "--fields-only" in sys.argv: sys.exit()
a85 = ad.read_h5ad(f"{VE}/data/E8.5_RNA.h5ad"); a95 = ad.read_h5ad(f"{VE}/data/E9.5_RNA.h5ad")
X85 = a85.X.tocsr(); X95 = a95.X.tocsr(); g85 = a85.obs.celltype.astype(str).map(COARSE).values; del a85, a95
frac = A.warp_fraction(8.5, 9.5)
LA = {}
for g in A.GROUPS:
    d = A.ext_delta(g, 14.5)
    if d is None: continue
    d = d.copy(); d[A.ambient_mask(g, 14.5)] = 0; LA[g] = frac * d
VAR = {"OT_x1": {}}
if "--variants" in sys.argv:
    VAR = {"OT_neutral": dict(neutral=True), "OT_smooth_neutral": dict(smooth=True, neutral=True)}
res = {k: [] for k in (["copy", "LA_x1"] if "--variants" not in sys.argv else []) + list(VAR)}; diags = {}
NSEED = 1 if "--variants" in sys.argv else 3
if "--confirm" in sys.argv: VAR = {"OT_smooth_neutral": dict(smooth=True, neutral=True)}; res = {"OT_smooth_neutral": []}
for seed in range(NSEED):
    rng = np.random.default_rng(100 + seed)
    ref = rng.choice(X85.shape[0], 1706, replace=False); pool = np.setdiff1d(np.arange(X85.shape[0]), ref)
    car = rng.choice(pool, 5118, replace=False); tru = rng.choice(X95.shape[0], 1249, replace=False)
    R = X85[ref].toarray(); T = X95[tru].toarray(); C = X85[car]
    for k in res:
        if k == "copy": P = C
        elif k == "LA_x1": P = A.zp_shift(C, g85[car], LA)
        else: P, dg = O.generate(C, g85[car], fields, tau=frac, seed=1000 + seed, **VAR[k]); diags[seed] = dg
        Pd = P.toarray(); ds = de_score(Pd, T, R)
        row = {"de_score": ds["score"], "de_direction": de_direction(Pd, T, R), "mmd_u": mmd_unbiased(Pd, T, seed=seed),
               "variogram": variogram_score(Pd, T, seed=seed), "nnz_frac": float(P.nnz / np.prod(P.shape))}
        res[k].append(row); print(seed, k, {a: round(b, 5) for a, b in row.items()}, flush=True); del Pd
mean = {k: {m: float(np.mean([r[m] for r in v])) for m in v[0]} for k, v in res.items()}
print(json.dumps(mean, indent=1))
json.dump({"per_seed": res, "mean": mean, "frac": frac, "ot_diag_seed0": diags.get(0),
           "fields": {g: F["diag"] for g, F in fields.items()}}, open(f"{VE}/backtests/t1_ot_e85_e95" + ("_variants" if "--variants" in sys.argv else "_confirm" if "--confirm" in sys.argv else "") + ".json", "w"), indent=1, default=str)
