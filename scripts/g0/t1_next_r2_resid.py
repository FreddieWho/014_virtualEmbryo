#!/usr/bin/env python3
"""T1-NEXT-R2: decoder isolation via residual-preserving interface.

Question: does a low-dim bottleneck destroy single-cell heterogeneity
(A=reconstruct-everything) vs preserving per-cell full-gene residuals
(B=transform latent only, keep residual)? Same time predictor, same
recipient rows, same composition. v0004/strict-shift as baselines.

Report scenario E8.5->E9.5 with cell-level holdout:
  fit zone = 60% stratified train cells (PCA + per-type means + latent deltas)
  recipients = E8.5 outer-test 20% cells
  pseudo-target = E9.5 outer-test 20% cells (temp file, never used in fitting)
  reference = E8.5 train cells (temp file)
Arms: identity / strict_shift(train-fitted) / A-reconstruct / B-residual.
Zero-delta identity check: B(delta=0) must reproduce source rows.
No candidates registered; diagnostic only. CPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split

TASK_ID = "T1-NEXT-R2"
RUN_SEED = 20260921
N_PC = 50
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
E85_SHA = "8eab2d0ccaa89f92861b09816b76b6a731b8ed6b5995e4af196d9ed8ff76e504"
E95_SHA = "0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def to_dense(a: ad.AnnData) -> np.ndarray:
    X = a.X
    if sparse.issparse(X):
        X = X.toarray()
    return np.asarray(X, dtype=np.float32)


def load_panel(path: Path):
    a = ad.read_h5ad(path)
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    names = [str(g) for g in a.var_names]
    assert len(set(names)) == len(names), "dup var_names"
    missing = [g for g in panel if g not in set(names)]
    assert not missing, f"missing panel genes {missing[:5]}"
    a = a[:, panel].copy()
    X = to_dense(a)
    assert np.isfinite(X).all() and (X >= 0).all()
    types = np.asarray(a.obs["celltype"].astype(str))
    return X, types


def run_scorer(inp: Path, tgt: Path, ref: Path, out: Path) -> dict:
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(inp), "--target", str(tgt),
           "--reference", str(ref), "--seed", str(RUN_SEED), "--out", str(out)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-2000:])
    return json.loads(out.read_text())["metrics"]


def write_sub(X: np.ndarray, types: np.ndarray, path: Path, panel: list[str]) -> None:
    aa = ad.AnnData(X=np.ascontiguousarray(X, dtype=np.float32),
                    obs=pd.DataFrame({"celltype": pd.Categorical(types)}),
                    var=pd.DataFrame(index=panel))
    aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    aa.uns["ve_t1_next_r2"] = json.dumps({"atom_id": TASK_ID, "seed": RUN_SEED,
                                          "diagnostic": True, "target_used": False})
    aa.write_h5ad(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    res: dict = {"task": TASK_ID, "seed": RUN_SEED, "n_pc": N_PC}
    t00 = time.time()

    assert sha256(E85) == E85_SHA, "E8.5 hash drift"
    assert sha256(E95) == E95_SHA, "E9.5 hash drift"
    res["inputs_sha_ok"] = True
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    D = len(panel)

    X85, t85 = load_panel(E85)
    X95, t95 = load_panel(E95)
    idx85 = np.arange(len(X85))
    idx95 = np.arange(len(X95))
    tr85, tmp85 = train_test_split(idx85, test_size=0.4, random_state=RUN_SEED, stratify=t85)
    te85, _in85 = train_test_split(tmp85, test_size=0.5, random_state=RUN_SEED + 1,
                                   stratify=t85[tmp85])
    tr95, tmp95 = train_test_split(idx95, test_size=0.4, random_state=RUN_SEED, stratify=t95)
    te95, _in95 = train_test_split(tmp95, test_size=0.5, random_state=RUN_SEED + 1,
                                   stratify=t95[tmp95])
    res["split"] = {"e85_train": len(tr85), "e85_outer": len(te85),
                    "e95_train": len(tr95), "e95_outer": len(te95)}
    assert len(te85) >= 1000 and len(te95) >= 1000, "outer test too small for scorer"

    # ---- fit zone: train cells only ----
    Xtr = np.vstack([X85[tr85], X95[tr95]]).astype(np.float32)
    pca = PCA(n_components=N_PC, svd_solver="randomized", random_state=RUN_SEED)
    Ztr = pca.fit_transform(Xtr).astype(np.float32)
    res["pca_explained_var"] = float(pca.explained_variance_ratio_.sum())
    Z85tr, Z95tr = Ztr[:len(tr85)], Ztr[len(tr85):]
    ttr85, ttr95 = t85[tr85], t95[tr95]
    alltypes = sorted(set(ttr85) | set(ttr95))
    mu85 = {c: X85[tr85][ttr85 == c].mean(axis=0) for c in alltypes if (ttr85 == c).any()}
    mu95 = {c: X95[tr95][ttr95 == c].mean(axis=0) for c in alltypes if (ttr95 == c).any()}
    zmu85 = {c: Z85tr[ttr85 == c].mean(axis=0) for c in alltypes if (ttr85 == c).any()}
    zmu95 = {c: Z95tr[ttr95 == c].mean(axis=0) for c in alltypes if (ttr95 == c).any()}
    common = sorted(set(mu85) & set(mu95))
    res["types_common"] = len(common)
    gshift = {c: (mu95[c] - mu85[c]).astype(np.float32) for c in common}
    zdelta = {c: (zmu95[c] - zmu85[c]).astype(np.float32) for c in common}

    # ---- recipients: E8.5 outer-test cells ----
    Xr = X85[te85].astype(np.float32)
    tr_ = t85[te85]
    unsupported = sorted(set(tr_) - set(zdelta))
    res["fallback_types"] = unsupported
    res["fallback_cells"] = int(sum((tr_ == c).sum() for c in unsupported))
    Dz = np.stack([zdelta.get(c, np.zeros(N_PC, dtype=np.float32)) for c in tr_]).astype(np.float32)
    Gshift = np.stack([gshift.get(c, np.zeros(D, dtype=np.float32)) for c in tr_]).astype(np.float32)
    Zr = pca.transform(Xr).astype(np.float32)
    Drecon_r = pca.inverse_transform(Zr).astype(np.float32)
    Eres = Xr - Drecon_r  # full-gene per-cell residual
    res["residual_share"] = float((Eres ** 2).mean() / (Xr ** 2).mean())
    res["residual_share_per_type"] = {
        c: float((Eres[tr_ == c] ** 2).mean() / (Xr[tr_ == c] ** 2).mean())
        for c in sorted(set(tr_))}

    # ---- identity check: B(delta=0) == source rows ----
    B0 = np.clip(Drecon_r + Eres, 0.0, None).astype(np.float32)
    res["identity_maxabs"] = float(np.abs(B0 - np.clip(Xr, 0, None)).max())
    assert res["identity_maxabs"] < 1e-5, "identity NOT conserved"

    Zpred = Zr + Dz
    Dpred = pca.inverse_transform(Zpred).astype(np.float32)

    arms = {
        "identity": Xr.copy(),
        "strict_shift": np.clip(Xr + Gshift, 0.0, None).astype(np.float32),
        "A_reconstruct": np.clip(Dpred, 0.0, None).astype(np.float32),
        "B_residual": np.clip(Dpred + Eres, 0.0, None).astype(np.float32),
    }
    res["clip_frac"] = {k: float((v < 0).mean() if k in ("A_reconstruct",) else 0.0)
                        for k, v in arms.items()}
    res["clip_frac"]["B_residual"] = float(((Dpred + Eres) < 0).mean())
    res["zero_rate"] = {k: float((v == 0).mean()) for k, v in arms.items()}
    res["zero_rate"]["source"] = float((Xr == 0).mean())
    res["lib_mean"] = {k: float(v.sum(axis=1).mean()) for k, v in arms.items()}
    res["lib_mean"]["e95_outer"] = float(X95[te95].sum(axis=1).mean())

    # ---- temp target/reference files (fit-zone + outer only, disjoint) ----
    tgt = RUN / "intermediates" / "pseudo_target_e95_outer.h5ad"
    ref = RUN / "intermediates" / "reference_e85_train.h5ad"
    write_sub(X95[te95], t95[te95], tgt, panel)
    write_sub(X85[tr85], t85[tr85], ref, panel)

    KEEP = ("de_score", "de_direction", "energy_distance", "mmd_u", "variogram",
            "pb_rel_err", "library_size_ratio", "variance_ratio", "composition_JSD",
            "pseudobulk_pearson")
    res["arms"] = {}
    for name, X in arms.items():
        p = RUN / "intermediates" / f"arm_{name}.h5ad"
        write_sub(X, tr_, p, panel)
        mout = RUN / "metrics" / f"scorer_{name}.json"
        m = run_scorer(p, tgt, ref, mout)
        res["arms"][name] = {k: m.get(k) for k in KEEP}
        print(f"ARM {name}: " + json.dumps(res["arms"][name]), flush=True)

    res["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({"identity_maxabs": res["identity_maxabs"],
                      "residual_share": res["residual_share"],
                      "pca_var": res["pca_explained_var"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
