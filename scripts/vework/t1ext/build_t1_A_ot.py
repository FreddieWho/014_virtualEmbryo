"""(A) T1 candidate: OT-coupled two-part generative displacement (otfield.py) on the v0051 carrier.
tau = log-time warp 9.5->10.5 (0.187) x 1.46 (the same overall strength LA3 used, so A vs LA3 isolates the
mechanism). Neighbour-aware, complexity-neutral gene on/off + cell-specific level displacement."""
import sys, json, pickle, numpy as np, scipy.sparse as sp, anndata as ad, pandas as pd
from pathlib import Path
sys.path.insert(0, "/workspace/ve/vework"); sys.path.insert(0, "/workspace/ve/vework/t1ext")
import vecommon as V, anchor as A, otfield as O
from label_means_const import COARSE
VE = Path("/workspace/ve"); CH = VE / "work/repro51/chain"; W = VE / "work/t1r3"
name = sys.argv[1]; amp = float(sys.argv[2]) if len(sys.argv) > 2 else 1.46
genes = V.panel("T1:val")
A.set_inext(ad.read_h5ad(VE / "ext/proc/GSM7226272_E14_5_1.h5ad", backed="r").var["in_external"].values)
fields = pickle.loads((W / "fields_14.5.pkl").read_bytes())
X = sp.csr_matrix(np.load(CH / "v0051.npy")); lab = np.load(CH / "v0051_donor_types.npy").astype(str)
grp = pd.Series(lab).map(COARSE).values
frac = A.warp_fraction(9.5, 10.5); tau = frac * amp
P, diag = O.generate(X, grp, fields, tau=tau, seed=20261009, smooth=True, neutral=True)
P.eliminate_zeros()
pb = np.asarray(P.mean(0)).ravel() - np.asarray(X.mean(0)).ravel()
out = ad.AnnData(X=P.astype(np.float32), obs=pd.DataFrame(index=[f"c{i}" for i in range(P.shape[0])]), var=pd.DataFrame(index=genes))
prov = {"recipe": "t1_ot_generative_displacement", "carrier": "v0051 mix36x38a faithful rebuild (released E8.5/E9.5 only; expr 541d0aa6)",
        "tau": tau, "warp_frac": frac, "amp": amp, "seed": 20261009, "smooth": True, "complexity_neutral": True,
        "ot": "entropic (eps 0.05 x median cost, uniform marginals), within coarse group, ext E8.5 -> ext E14.5, 30-PC latent of 2000 HVGs",
        "transfer": "k=10 nearest ext E8.5 analogues in z-scored ext-E8.5 PCA", "groups": sorted(fields), "diag": diag,
        "field_diag": {g: F["diag"] for g, F in fields.items()},
        "external": "GSE230531 GSM7226268/9 (E8.5 embryo), GSM7226272/3 (E14.5 heart); no other data"}
out.uns["ve_provenance"] = json.dumps(prov, default=str)
path = VE / "submit" / f"T1_val__{name}.h5ad"; out.write_h5ad(path, compression="gzip")
fc = V.format_check(path, "T1:val"); top = np.argsort(pb)
res = {"file": str(path), "format": fc, "sha256": V.sha256(path), "nnz_frac": float(P.nnz / np.prod(P.shape)),
       "carrier_nnz_frac": float(X.nnz / np.prod(X.shape)), "pb_shift_l2": float(np.linalg.norm(pb)), "max_abs_pb": float(np.abs(pb).max()),
       "top_up": [genes[i] for i in top[-15:][::-1]], "top_down": [genes[i] for i in top[:15]], "prov": prov}
(W / f"{name}.build.json").write_text(json.dumps(res, default=str, indent=1)); print(json.dumps({k: v for k, v in res.items() if k != "prov"}, default=str, indent=1)); print(json.dumps(diag, indent=1))
