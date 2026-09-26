#!/usr/bin/env python3
"""T1-NEXT-R4: transport restricted to learnable modules (+orthogonal residuals).

Fixed modules: MiniBatchKMeans K=32 on standardized train gene profiles
(same recipe/seed as R5). Cell = module means (K-dim) + within-module residuals.
Transport (per common type, module-score space, POT Sinkhorn reg=0.1, <=800
train cells/stage seed-subsampled):
  cost: squared Euclidean on module scores; arm A uniform, arm B weighted by
  bootstrap reliability (20 resamples of train mean-shift; w=1/(1+var), normalized).
Out-of-sample map for recipients: RBF-kernel barycentric projection through the
train coupling (bandwidth = median pairwise distance, seed-fixed, no RNG).
Output gene = gene + (m'_mod - m_mod): module direction moves, within-module
residuals strictly kept; zero-var / dropped-module / unsupported-type genes and
cells fall back to source rows. Never a high-dim barycenter as whole-cell output.
Validation: train transport error + full-gene scorer (all 32285 cols).
Stop: weight collapse, unstable modules, uniform/weighted indistinguishable.
Report E8.5->E9.5. Diagnostic only. CPU.
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
import ot
import pandas as pd
from scipy import sparse
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import pairwise_distances
from sklearn.model_selection import train_test_split

TASK_ID = "T1-NEXT-R4"
RUN_SEED = 20260921
N_MOD = 32
SINK_REG = 0.1
MAXN = 800
N_BOOT = 20
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
    a = a[:, panel].copy()
    X = to_dense(a)
    assert np.isfinite(X).all() and (X >= 0).all()
    return X, np.asarray(a.obs["celltype"].astype(str))


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
    aa.uns["ve_t1_next_r4"] = json.dumps({"atom_id": TASK_ID, "seed": RUN_SEED,
                                          "diagnostic": True, "target_used": False})
    aa.write_h5ad(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    res: dict = {"task": TASK_ID, "seed": RUN_SEED, "n_mod": N_MOD}
    t00 = time.time()

    assert sha256(E85) == E85_SHA and sha256(E95) == E95_SHA, "input drift"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    D = len(panel)
    X85, t85 = load_panel(E85)
    X95, t95 = load_panel(E95)
    idx85 = np.arange(len(X85))
    idx95 = np.arange(len(X95))
    tr85, tmp85 = train_test_split(idx85, test_size=0.4, random_state=RUN_SEED, stratify=t85)
    te85, _ = train_test_split(tmp85, test_size=0.5, random_state=RUN_SEED + 1,
                               stratify=t85[tmp85])
    tr95, tmp95 = train_test_split(idx95, test_size=0.4, random_state=RUN_SEED, stratify=t95)
    te95, _ = train_test_split(tmp95, test_size=0.5, random_state=RUN_SEED + 1,
                               stratify=t95[tmp95])
    assert (len(tr85), len(te85), len(tr95), len(te95)) == (10072, 3357, 10234, 3411)
    res["split_ok_r2match"] = True
    rng = np.random.RandomState(RUN_SEED)
    ttr85, ttr95 = t85[tr85], t95[tr95]
    X85tr = X85[tr85].astype(np.float64)
    X95tr = X95[tr95].astype(np.float64)
    Xr = X85[te85].astype(np.float64)
    tr_ = t85[te85]
    common = sorted(set(ttr85) & set(ttr95))

    Xtr_all = np.vstack([X85tr, X95tr])
    mu = Xtr_all.mean(axis=0)
    sd = Xtr_all.std(axis=0)
    nz = sd > 1e-12
    res["zero_var_genes"] = int((~nz).sum())
    G = ((Xtr_all[:, nz] - mu[nz]) / sd[nz]).T
    km = MiniBatchKMeans(n_clusters=N_MOD, random_state=RUN_SEED, batch_size=4096,
                         max_iter=50, n_init=3)
    mod_of_gene = np.full(D, -1, dtype=np.int64)
    mod_of_gene[np.where(nz)[0]] = km.fit_predict(G)
    res["mod_sizes"] = [int((mod_of_gene == m).sum()) for m in range(N_MOD)]
    print("modules fit", flush=True)

    def mod_scores(X: np.ndarray) -> np.ndarray:
        S = np.zeros((X.shape[0], N_MOD))
        for m in range(N_MOD):
            cols = np.where(mod_of_gene == m)[0]
            if len(cols):
                S[:, m] = X[:, cols].mean(axis=1)
        return S

    outA = Xr.copy()
    outB = Xr.copy()
    res["per_type"] = {}
    for c in sorted(set(tr_)):
        if c not in common:
            continue
        A85, A95 = X85tr[ttr85 == c], X95tr[ttr95 == c]
        if len(A85) < 100 or len(A95) < 100:
            res["per_type"][c] = {"skipped": "low_n"}
            continue
        i85 = rng.choice(len(A85), min(MAXN, len(A85)), replace=False)
        i95 = rng.choice(len(A95), min(MAXN, len(A95)), replace=False)
        S, T = mod_scores(A85[i85]), mod_scores(A95[i95])
        ssd = S.std(axis=0)
        ssd[ssd < 1e-12] = 1.0
        Sn, Tn = S / ssd, T / ssd
        # arm B weights: bootstrap reliability of train mean shift
        b_rng = np.random.RandomState(RUN_SEED + abs(hash(c)) % 10000)
        shifts = []
        for _ in range(N_BOOT):
            j = b_rng.choice(len(A85), len(A85), replace=True)
            k = b_rng.choice(len(A95), len(A95), replace=True)
            shifts.append(mod_scores(A95[k]).mean(axis=0) - mod_scores(A85[j]).mean(axis=0))
        shifts = np.stack(shifts)
        w = 1.0 / (1.0 + shifts.var(axis=0) / max(shifts.mean(axis=0).var(), 1e-12))
        w = w / w.sum() * N_MOD  # mean 1
        eff = float((w.sum() ** 2) / (w ** 2).sum())
        Mw = np.diag(np.sqrt(w))
        C = pairwise_distances(Sn, Tn, metric="sqeuclidean")
        Cw = pairwise_distances(Sn @ Mw, Tn @ Mw, metric="sqeuclidean")
        a = np.full(len(Sn), 1 / len(Sn))
        b = np.full(len(Tn), 1 / len(Tn))
        P = ot.sinkhorn(a, b, C, reg=SINK_REG)
        Pw = ot.sinkhorn(a, b, Cw, reg=SINK_REG)
        # train transport error (barycentric self-map, module space)
        Tpred_tr = (P.T @ Sn) / P.sum(axis=0, keepdims=True).T.clip(min=1e-12)
        tr_err = float(np.linalg.norm(Tpred_tr.mean(axis=0) - Tn.mean(axis=0)))
        res["per_type"][c] = {"n85": len(A85), "n95": len(A95),
                              "train_err": tr_err, "eff_modules": round(eff, 2),
                              "w_max": round(float(w.max()), 3)}
        if eff < 2.0:
            res["per_type"][c]["weight_collapse"] = True
        # out-of-sample RBF barycentric map for recipients
        m = (tr_ == c)
        Sr = mod_scores(Xr[m]) / ssd
        Dmat = pairwise_distances(Sr, Sn, metric="sqeuclidean")
        bw = float(np.median(Dmat)) + 1e-12
        K = np.exp(-Dmat / bw)
        Wf = K @ P
        Wf = Wf / Wf.sum(axis=1, keepdims=True).clip(min=1e-12)
        Ww = K @ Pw
        Ww = Ww / Ww.sum(axis=1, keepdims=True).clip(min=1e-12)
        TmA = Wf @ Tn * ssd
        TmB = Ww @ Tn * ssd
        Sm = mod_scores(Xr[m])
        rec_idx = np.where(m)[0]
        dA = TmA - Sm
        dB = TmB - Sm
        for g in range(D):
            gm = mod_of_gene[g]
            if gm < 0:
                continue
            outA[rec_idx, g] = Xr[m][:, g] + dA[:, gm]
            outB[rec_idx, g] = Xr[m][:, g] + dB[:, gm]
        print(f"type {c}: mapped", flush=True)

    mu85 = {c: X85tr[ttr85 == c].mean(axis=0) for c in common}
    mu95 = {c: X95tr[ttr95 == c].mean(axis=0) for c in common}
    Gshift = np.stack([(mu95[c] - mu85[c]) if c in common
                       else np.zeros(D) for c in tr_])
    arms_ordered = {
        "identity": Xr.copy().astype(np.float32),
        "strict_shift": np.clip(Xr + Gshift, 0.0, None).astype(np.float32),
        "A_uniform": np.clip(outA, 0.0, None).astype(np.float32),
        "B_reliab": np.clip(outB, 0.0, None).astype(np.float32),
    }
    res["zero_rate"] = {k: float((np.asarray(v) == 0).mean()) for k, v in arms_ordered.items()}
    res["lib_mean"] = {k: float(np.asarray(v).sum(axis=1).mean()) for k, v in arms_ordered.items()}

    tgt = RUN / "intermediates" / "pseudo_target_e95_outer.h5ad"
    ref = RUN / "intermediates" / "reference_e85_train.h5ad"
    write_sub(X95[te95].astype(np.float32), t95[te95], tgt, panel)
    write_sub(X85[tr85].astype(np.float32), t85[tr85], ref, panel)
    res["lib_mean"]["e95_outer"] = float(X95[te95].sum(axis=1).mean())

    KEEP = ("de_score", "de_direction", "energy_distance", "mmd_u", "variogram",
            "pb_rel_err", "library_size_ratio", "variance_ratio", "composition_JSD",
            "pseudobulk_pearson")
    res["arms"] = {}
    for name, X in arms_ordered.items():
        p = RUN / "intermediates" / f"arm_{name}.h5ad"
        write_sub(np.asarray(X, dtype=np.float32), tr_, p, panel)
        mout = RUN / "metrics" / f"scorer_{name}.json"
        m = run_scorer(p, tgt, ref, mout)
        res["arms"][name] = {k: m.get(k) for k in KEEP}
        print(f"ARM {name}: " + json.dumps(res["arms"][name]), flush=True)

    res["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
