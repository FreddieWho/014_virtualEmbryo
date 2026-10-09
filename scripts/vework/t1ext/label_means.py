"""Coarse label transfer (competition E8.5+E9.5 labels -> external cells) and per-group stage means.
Classifier: multinomial logistic regression on ~300 competition marker genes (present in the external set),
standardised with competition statistics. Output: ext/proc/groups.npz with per (dataset, stage, group)
mean log-expression, detection fraction and n over all 32,285 panel genes."""
import json, numpy as np, scipy.sparse as sp, anndata as ad, pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
VE = Path("/workspace/ve"); P = VE / "ext/proc"
COARSE = {"OFT/RV-CM": "CM_V", "RV-CM": "CM_V", "LV-CM": "CM_V", "V-CM": "CM_V", "AVC-CM": "CM_V",
          "IFT-CM": "CM_A", "SV-CM": "CM_A", "Endothelium": "ENDO", "Endocardium": "ENDO", "BEC": "ENDO",
          "Pericardium": "EPI", "Proepicardium": "EPI", "Blood": "BLOOD", "pSHF": "SHF", "aSHF": "SHF", "JCF": "SHF",
          "pPHM": "MESO", "aPHM": "MESO", "ST": "MESO", "Paraxial Mesoderm": "MESO", "EXEM": "MESO",
          "NCC": "NCC", "NCC-derived": "NCC", "Foregut": "ENDODERM", "Hepatocyte": "ENDODERM", "Epithelium": "ENDODERM",
          "Surface Ectoderm": "ECTO", "Neural Tube": "ECTO"}
def load(path):
    a = ad.read_h5ad(path); X = a.X.tocsr() if sp.issparse(a.X) else sp.csr_matrix(a.X); return a, X
comp = {}
for s, t in [("E8.5_RNA", 8.5), ("E9.5_RNA", 9.5)]:
    a, X = load(VE / f"data/{s}.h5ad"); comp[t] = (X, a.obs["celltype"].astype(str).map(COARSE).values)
genes = None
ext = {}
for f in sorted(P.glob("GSM*.h5ad")):
    a, X = load(f); ext.setdefault(float(a.obs.stage.iloc[0]), []).append(X)
    inext = a.var["in_external"].values; genes = list(a.var_names)
ext = {t: sp.vstack(v).tocsr() for t, v in ext.items()}
G = len(genes)
# marker selection on pooled competition
Xc = sp.vstack([comp[8.5][0], comp[9.5][0]]).tocsr(); yc = np.concatenate([comp[8.5][1], comp[9.5][1]])
assert not pd.isna(yc).any(), set(yc)
groups = sorted(set(yc))
M = np.vstack([np.asarray(Xc[yc == g].mean(0)).ravel() for g in groups])
bad = np.array([g.startswith(("mt-", "Rpl", "Rps")) or g in ("Malat1",) for g in genes])
feat = set()
for k, g in enumerate(groups):
    other = np.max(np.delete(M, k, 0), 0); sc = M[k] - other; sc[~inext | bad] = -np.inf
    feat |= set(np.argsort(-sc)[:40].tolist())
feat = np.array(sorted(feat))
mu = np.asarray(Xc[:, feat].mean(0)).ravel(); sd = np.sqrt(np.asarray(Xc[:, feat].multiply(Xc[:, feat]).mean(0)).ravel() - mu**2) + 1e-3
rng = np.random.default_rng(0); idx = rng.choice(Xc.shape[0], 20000, replace=False)
clf = LogisticRegression(max_iter=500, C=0.5).fit((Xc[idx][:, feat].toarray() - mu) / sd, yc[idx])
hold = np.setdiff1d(np.arange(Xc.shape[0]), idx)[:6000]
acc = float((clf.predict((Xc[hold][:, feat].toarray() - mu) / sd) == yc[hold]).mean())
print("features", len(feat), "comp holdout acc", round(acc, 3))
out = {"genes": np.array(genes), "groups": np.array(groups), "features": feat}
summary = {"holdout_acc": acc, "n_features": int(len(feat)), "ext": {}}
def stats(X, lab, prefix):
    for g in groups:
        m = lab == g; n = int(m.sum())
        out[f"{prefix}|{g}|n"] = n
        if n:
            out[f"{prefix}|{g}|mean"] = np.asarray(X[m].mean(0)).ravel().astype(np.float32)
            out[f"{prefix}|{g}|det"] = (np.asarray((X[m] > 0).sum(0)).ravel() / n).astype(np.float32)
for t, (X, y) in comp.items(): stats(X, y, f"comp{t}")
for t, X in ext.items():
    pr = clf.predict_proba((X[:, feat].toarray() - mu) / sd); lab = clf.classes_[pr.argmax(1)]
    lab = np.where(pr.max(1) >= 0.5, lab, "LOWCONF")
    stats(X, lab, f"ext{t}")
    summary["ext"][str(t)] = pd.Series(lab).value_counts().to_dict()
    print("ext", t, summary["ext"][str(t)])
    np.save(P / f"ext{t}_labels.npy", lab)
# sanity: marker means per ext group
mk = ["Tnnt2", "Myl7", "Myl2", "Nppa", "Pecam1", "Cdh5", "Wt1", "Tcf21", "Postn", "Hbb-y", "Hba-a1", "Ptprc", "Isl1", "Afp", "Sox2", "Sox10"]
gi = [genes.index(m) for m in mk if m in genes]
rows = []
for t in sorted(ext):
    for g in groups:
        if out.get(f"ext{t}|{g}|n", 0) >= 30: rows.append([f"ext{t}", g] + list(np.round(out[f"ext{t}|{g}|mean"][gi], 2)))
for t in comp:
    for g in groups:
        if out.get(f"comp{t}|{g}|n", 0) >= 30: rows.append([f"comp{t}", g] + list(np.round(out[f"comp{t}|{g}|mean"][gi], 2)))
print(pd.DataFrame(rows, columns=["set", "group"] + [mk[i] for i in range(len(gi))]).to_string())
np.savez_compressed(P / "groups.npz", **out); json.dump(summary, open(P / "label_summary.json", "w"), indent=1)
