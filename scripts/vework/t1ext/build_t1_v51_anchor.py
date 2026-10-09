"""Combined T1 candidate: late-anchor shift (GSE230531, same machinery as LA1/LA2) applied on top of the
v0051 carrier (faithful rebuild from released data; /workspace/ve/work/repro51/chain/v0051.npy).
Pre-registered setting rule (fixed before any score of this file exists):
  * composition reweighting OFF: v0051 already carries round2 composition steps through its donors, and the
    LA1->LA2 comparison attributes the variogram loss to the stronger/comp setting; v0051's vario (50.6) is kept.
  * amplitude: v0051 rows already contain an internal E8.5->E9.5 extrapolation (o1mass transform). Per anchored
    coarse group we project v0051's own pseudobulk shift (v0051 rows minus the raw E9.5 cells of the same donor
    types) onto the anchor unit (warp*delta, masked genes excluded). With pooled projection p (in units of
    the amp-1 anchor), amp = clip(2 - p, 1, 2): total along-anchor movement targets the LA2 level (amp 2, the
    better portal setting on de/dir/mmd) without double-counting, and never drops below LA1 (amp 1).
Shift is applied per row by the row's donor (source) cell type -> coarse group."""
import sys, json, argparse, numpy as np, scipy.sparse as sp, anndata as ad, pandas as pd
from pathlib import Path
sys.path.insert(0, "/workspace/ve/vework"); sys.path.insert(0, "/workspace/ve/vework/t1ext")
import vecommon as V
import anchor as A
from label_means_const import COARSE
VE = Path("/workspace/ve"); CH = VE / "work/repro51/chain"
ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--amp", default="auto")
ap.add_argument("--t0", type=float, default=9.5); ap.add_argument("--t1", type=float, default=10.5)
a = ap.parse_args()
genes = V.panel("T1:val")
X = np.load(CH / "v0051.npy", mmap_mode="r"); lab = np.load(CH / "v0051_donor_types.npy").astype(str)
assert X.shape == (5118, len(genes)) and len(lab) == len(X)
grp = pd.Series(lab).map(COARSE).values; assert not pd.isna(grp).any(), set(lab[pd.isna(grp)])
A.set_inext(ad.read_h5ad(VE / "ext/proc/GSM7226272_E14_5_1.h5ad", backed="r").var["in_external"].values)
frac = A.warp_fraction(a.t0, a.t1)
ref = ad.read_h5ad(VE / "data/E9.5_RNA.h5ad"); assert list(ref.var_names) == genes
rct = ref.obs.celltype.astype(str).values; rX = ref.X.tocsr()
units, proj = {}, {}
for g in A.GROUPS:
    d = A.ext_delta(g, 14.5)
    if d is None: continue
    m = A.ambient_mask(g, 14.5); u = (frac * d).astype(np.float64); u[m] = 0; units[g] = u
    rows = np.flatnonzero(grp == g)
    if not len(rows): continue
    # reference = raw E9.5 cells weighted to the same fine-type mix as the v0051 rows of this group
    vc = pd.Series(lab[rows]).value_counts(); refmean = np.zeros(len(genes))
    for t, k in vc.items(): refmean += k / len(rows) * np.asarray(rX[rct == t].mean(0)).ravel()
    internal = np.asarray(X[rows].mean(0), dtype=np.float64) - refmean
    keep = u != 0
    proj[g] = {"n": int(len(rows)), "p": float(internal[keep] @ u[keep] / (u[keep] @ u[keep])),
               "cos": float(internal[keep] @ u[keep] / np.linalg.norm(internal[keep]) / np.linalg.norm(u[keep])),
               "internal_norm_over_unit_norm": float(np.linalg.norm(internal[keep]) / np.linalg.norm(u[keep]))}
ntot = sum(v["n"] for v in proj.values()); p_pool = sum(v["n"] * v["p"] for v in proj.values()) / ntot
if a.amp == "pergroup":   # (B) each group's total along-anchor movement topped to the LA2 level individually
    amps = {g: float(np.clip(2 - proj[g]["p"], 0, 2)) if g in proj else 2.0 for g in units}; amp = amps
    deltas = {g: amps[g] * u for g, u in units.items()}
else:
    amp = float(np.clip(2 - p_pool, 1, 2)) if a.amp == "auto" else float(a.amp)
    deltas = {g: amp * u for g, u in units.items()}
C = sp.csr_matrix(np.asarray(X, dtype=np.float32))
P = A.zp_shift(C, grp, deltas)
pb_shift = np.asarray(P.mean(0)).ravel() - np.asarray(C.mean(0)).ravel()
out = ad.AnnData(X=P.astype(np.float32), obs=pd.DataFrame(index=[f"c{i}" for i in range(len(lab))]),
                 var=pd.DataFrame(index=genes))
prov = {"recipe": "t1_v51_late_anchor", "carrier": "v0051 mix36x38a faithful rebuild (released E8.5/E9.5 only)",
        "carrier_digest": json.loads((CH / "CHAIN.json").read_text())["v0051"]["expression_sha256"],
        "warp": "log-time", "frac": frac, "amp": amp, "amp_rule": "per group clip(2 - p_g, 0, 2)" if a.amp == "pergroup" else "clip(2 - pooled projection, 1, 2)",
        "pooled_projection": p_pool, "per_group": proj, "comp_strength": 0.0, "groups_anchored": sorted(deltas),
        "external": "GSE230531 GSM7226268/9 (E8.5), GSM7226272/3 (E14.5); E16.5 GSM7226274/6 warp calibration only"}
out.uns["ve_provenance"] = json.dumps(prov, default=str)
path = VE / "submit" / f"T1_val__{a.name}.h5ad"
out.write_h5ad(path, compression="gzip")
fc = V.format_check(path, "T1:val"); top = np.argsort(pb_shift)
res = {"file": str(path), "format": fc, "sha256": V.sha256(path), "prov": prov,
       "top_up": [genes[i] for i in top[-15:][::-1]], "top_down": [genes[i] for i in top[:15]],
       "groups_rows": pd.Series(grp).value_counts().to_dict()}
(VE / "work/repro51" / f"{a.name}.build.json").write_text(json.dumps(res, default=str, indent=1))
print(json.dumps(res, default=str, indent=1))
