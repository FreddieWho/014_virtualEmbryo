"""Build the two T1 late-anchor candidates (val target E10.5; same code serves the test target E12.5 with
--t0 10.5 --t1 12.5 once E10.5 truth is the carrier).
Carrier: real E9.5 cells (whole rows), stratified by celltype. Shift: per coarse group, external within-batch
trajectory (GSE230531 E14.5 - E8.5, ambient-masked) x log-time warp fraction x amplitude, zero-preserving.
#2 additionally resamples the carrier so CM_V/CM_A/ENDO/SHF proportions move (half strength) a log-time
fraction toward the external E14.5 proportions."""
import sys, json, argparse, numpy as np, scipy.sparse as sp, anndata as ad, pandas as pd
from pathlib import Path
sys.path.insert(0, "/workspace/ve/vework")
import vecommon as V
import anchor as A
from label_means_const import COARSE
VE = Path("/workspace/ve")
ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--amp", type=float, default=1.0)
ap.add_argument("--comp", type=float, default=0.0); ap.add_argument("--n", type=int, default=5118)
ap.add_argument("--seed", type=int, default=20261008); ap.add_argument("--carrier", default="E9.5_RNA")
ap.add_argument("--t0", type=float, default=9.5); ap.add_argument("--t1", type=float, default=10.5)
a = ap.parse_args()
genes = V.panel("T1:val")
c = ad.read_h5ad(VE / f"data/{a.carrier}.h5ad"); assert list(c.var_names) == genes
X = c.X.tocsr(); ct = c.obs.celltype.astype(str).values; grp = pd.Series(ct).map(COARSE).values
A.set_inext(ad.read_h5ad(VE / "ext/proc/GSM7226272_E14_5_1.h5ad", backed="r").var["in_external"].values)
frac = A.warp_fraction(a.t0, a.t1)
rng = np.random.default_rng(a.seed)
# stratified (proportional) draw by fine celltype, then optional composition reweighting
w = np.ones(len(ct)); info = None
if a.comp > 0:
    w, info = A.comp_weights(grp, frac, strength=a.comp)
p = w / w.sum()
idx = rng.choice(len(ct), a.n, replace=False, p=p)
deltas = {}
for g in A.GROUPS:
    d = A.ext_delta(g, 14.5)
    if d is None: continue
    d = d.copy(); d[A.ambient_mask(g, 14.5)] = 0; deltas[g] = a.amp * frac * d
P = A.zp_shift(X[idx], grp[idx], deltas)
pb_shift = np.asarray(P.mean(0)).ravel() - np.asarray(X[idx].mean(0)).ravel()
out = ad.AnnData(X=P.astype(np.float32), obs=pd.DataFrame(index=[f"c{i}" for i in range(a.n)]),
                 var=pd.DataFrame(index=genes))
prov = {"recipe": "t1_late_anchor", "carrier": a.carrier, "n": a.n, "seed": a.seed, "warp": "log-time",
        "frac": frac, "amp": a.amp, "comp_strength": a.comp, "comp_ratio": info,
        "groups_anchored": sorted(deltas), "external": "GSE230531 GSM7226268/9 (E8.5), GSM7226272/3 (E14.5)"}
out.uns["ve_provenance"] = json.dumps(prov, default=str)
path = VE / "submit" / f"T1_val__{a.name}.h5ad"
out.write_h5ad(path, compression="gzip")
fc = V.format_check(path, "T1:val")
comp_out = pd.Series(ct[idx]).value_counts(normalize=True).round(4).to_dict()
top = np.argsort(pb_shift)
print(json.dumps({"file": str(path), "format": fc, "sha256": V.sha256(path), "prov": prov,
                  "top_up": [genes[i] for i in top[-15:][::-1]], "top_down": [genes[i] for i in top[:15]],
                  "composition": comp_out}, default=str, indent=1))
