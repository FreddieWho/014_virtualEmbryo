#!/usr/bin/env python3
"""Eval-only cosine fix for direction-6 stage one + stage two.

Background: both scripts computed the cosine diagnostic as pooled cell-level
dot / pooled norm products. For constant-per-gene predictions that ratio is
NOT a cosine (denominator misses the sqrt(n) factor) and can exceed 1
(observed 1.293). MSE verdicts are unaffected (plain mean of squared diffs).
This script recomputes the diagnostic as cosine between per-gene MEAN
predicted and true responses (valid, matches precedent delta_metrics), using
the SAVED stage-two models (no retraining) and refit-identical ridge
(deterministic closed form). Patches both RESULT.json files in place with an
audit note; MSE values are asserted unchanged (not touched).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy as np

RUN_SEED = 20261002
ALPHA = 1.0
S1RES = REPO / "artifacts/t3_dir6/T3-DIR6-20261002-v1/RESULT.json"
S2RES = REPO / "artifacts/t3_dir6/T3-DIR6-20261002-v1/stage2/RESULT.json"
S2DIR = REPO / "artifacts/t3_dir6/T3-DIR6-20261002-v1/stage2"
INPUT = REPO / "infra/external_data/sanitized/T3-R6-OP2-20260921/expression.h5ad"
GO_EMB = REPO / "artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz"


def mean_cos(Pm, Tm):
    P = np.stack(Pm)
    T = np.stack(Tm)
    return float((P * T).sum() / (np.linalg.norm(P) * np.linalg.norm(T) + 1e-12))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    import anndata as ad
    from scipy import sparse
    from sklearn.linear_model import Ridge

    RUN = Path(args.run_dir)
    RUN.mkdir(parents=True, exist_ok=True)
    s1 = json.loads(S1RES.read_text())
    folds = [r["held_genes"] for r in s1["fold_detail"]]

    src = ad.read_h5ad(INPUT)
    from scipy import sparse as _sparse
    src.X = _sparse.csr_matrix(np.asarray(src.X))
    src.obs['original_condition'] = src.obs.condition.astype(str)
    src.obs['condition'] = src.obs.original_condition.map(
        lambda x: 'ctrl' if x == 'ctrl' else x + '+ctrl').astype('category')
    src.obs['cell_type'] = 'adult_mouse_cardiac_fibroblast'
    src.var['gene_name'] = src.var_names.astype(str)  # required by GEARS
    X = np.asarray(src.X.toarray() if sparse.issparse(src.X) else src.X,
                   dtype=np.float64)
    labels = np.asarray(src.obs.original_condition.astype(str))
    ctrl = X[labels == "ctrl"].mean(axis=0)

    go = np.load(GO_EMB)
    go_pos = {str(g): j for j, g in enumerate([str(x) for x in go["genes"]])}
    go_mat = go["embedding"].astype(np.float64)

    # ---- stage one: refit identical ridge, correct cosine, verify MSE
    s1c = []
    for fi, held in enumerate(folds):
        held_set = set(held)
        tr_m = np.array([c != "ctrl" and c not in held_set for c in labels])
        te_m = np.array([c in held_set for c in labels])
        mu = (X[tr_m] - ctrl).mean(axis=0, keepdims=True)
        ytr_c = (X[tr_m] - ctrl) - mu
        tr_genes = sorted(set(labels[tr_m].tolist()))
        Etr_raw = np.stack([go_mat[go_pos[g]] for g in tr_genes])
        mue = Etr_raw.mean(axis=0, keepdims=True)
        sde = Etr_raw.std(axis=0, keepdims=True) + 1e-8
        Ftr = np.stack([(go_mat[go_pos[c]] - mue.ravel()) / sde.ravel()
                        for c in labels[tr_m]])
        model = Ridge(alpha=ALPHA, solver="cholesky")
        model.fit(Ftr, ytr_c)
        Ete = np.stack([(go_mat[go_pos[c]] - mue.ravel()) / sde.ravel()
                        for c in labels[te_m]])
        pred = model.predict(Ete)
        t = (X[te_m] - ctrl) - mu
        mse = float(np.mean((t - pred) ** 2))
        old = s1["fold_detail"][fi]["mse_ridge"] if "mse_ridge" in s1["fold_detail"][fi] else None
        Pm = [pred[labels[te_m] == g].mean(axis=0) for g in held]
        Tm = [t[labels[te_m] == g].mean(axis=0) for g in held]
        s1c.append({"fold": fi, "mse": mse, "cos": mean_cos(Pm, Tm),
                    "mse_old": old})
    for a, b in zip(s1c, s1["fold_detail"]):
        assert abs(a["mse"] - b.get("mse_ridge", a["mse"])) < 1e-9, \
            f"stage-one MSE changed on refit (fold {a['fold']})"

    # ---- stage two: saved models, correct cosine, verify MSE
    sys.path.insert(0, str(REPO / "infra/toolchains/t3_priority_six/GEARS"))
    import torch
    from gears import GEARS, PertData
    from torch_geometric.data import Data, Batch
    torch.manual_seed(RUN_SEED)
    s2 = json.loads(S2RES.read_text())
    s2c = []
    tmp = Path(tempfile.mkdtemp(prefix="dir6cosfix_"))
    cwd0 = os.getcwd()
    try:
        for fi, held in enumerate(folds):
            import shutil as _sh
            fsrc = S2DIR / "intermediates" / f"fold{fi}"
            fdir = tmp / f"fold{fi}"
            _sh.copytree(fsrc, fdir, ignore=_sh.ignore_patterns("op2_stage2_f*"))
            for f in ("gene_set.pkl", "gene2go_all.pkl", "split.pkl"):
                _sh.copy2(fsrc / f, fdir / f)
            (fdir / "data").mkdir(exist_ok=True)
            os.chdir(fdir)
            try:
                data = PertData(str("."), gene_set_path="gene_set.pkl",
                                default_pert_graph=False)
                data.new_data_process(dataset_name=f"cosfix_f{fi}", adata=src)
                data.prepare_split(split="custom", seed=RUN_SEED,
                                   split_dict_path="split.pkl")
                data.get_dataloader(batch_size=32, test_batch_size=64)
                model = GEARS(data, device="cpu")
                model.model_initialize()
                model.load_pretrained(str(S2DIR / "models" / f"fold{fi}"))
                held_set = set(held)
                tr_m = np.array([c != "ctrl" and c not in held_set
                                 for c in labels])
                mu_f = (X[tr_m] - ctrl).mean(axis=0, keepdims=True)
                model.best_model.eval()
                Pm, Tm = [], []
                se = 0.0
                n = 0
                with torch.no_grad():
                    for g in held:
                        xg = X[labels == "ctrl"]
                        graphs = [Data(x=torch.tensor(row[:, None], dtype=torch.float32),
                                       pert_idx=[model.node_map_pert[g]])
                                  for row in xg]
                        outs = []
                        for s in range(0, len(graphs), 32):
                            outs.append(model.best_model(
                                Batch.from_data_list(graphs[s:s + 32])).cpu().numpy())
                        out = np.concatenate(outs)
                        pred_c = (out.mean(axis=0, keepdims=True) - ctrl) - mu_f
                        t_c = (X[labels == g] - ctrl) - mu_f
                        se += float(((pred_c - t_c) ** 2).sum())
                        n += int(t_c.size)
                        Pm.append(pred_c.ravel())
                        Tm.append(t_c.mean(axis=0))
                mse = se / max(n, 1)
                old = [r for r in s2["per_fold"] if r["fold"] == fi][0]
                assert abs(mse - old["mse"]) < 1e-6, \
                    f"stage-two MSE changed on reload (fold {fi}: {mse} vs {old['mse']})"
                s2c.append({"fold": fi, "mse": mse, "cos": mean_cos(Pm, Tm),
                            "cos_old": old["cos"]})
            finally:
                os.chdir(cwd0)
    finally:
        os.chdir(cwd0)
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- patch both RESULT.json files (MSE untouched; audit note added)
    note = ("cosine diagnostic recomputed 2026-10-03: original pooled cell-level "
            "dot/norm ratio is not a valid cosine for constant-per-gene predictions "
            "(could exceed 1); replaced by cosine of per-gene MEAN responses. "
            "MSE values verified unchanged; gate verdicts stand.")
    s1["fold_detail"] = [
        {**r, "cos_ridge": c["cos"], "cos_old_malformed": r.get("cos_ridge")}
        for r, c in zip(s1["fold_detail"], s1c)]
    s1_old_cos_mean = s1["cos_ridge_mean"]
    s1["cos_ridge_mean"] = float(np.mean([c["cos"] for c in s1c]))
    s1["cos_ridge_mean_old_malformed"] = s1_old_cos_mean
    s1["cos_fix_note"] = note
    S1RES.write_text(json.dumps(s1, indent=1, default=float))
    s2["per_fold"] = [
        {**r, "cos": c["cos"], "cos_old_malformed": c["cos_old"]} for r, c in
        zip(sorted(s2["per_fold"], key=lambda r: r["fold"]), s2c)]
    s2_old_cos = s2["cos_neural"]
    s2["cos_neural"] = float(np.mean([c["cos"] for c in s2c]))
    s2["cos_neural_old_malformed"] = s2_old_cos
    s2["cos_fix_note"] = note
    S2RES.write_text(json.dumps(s2, indent=1, default=float))
    print(json.dumps({"patched": True,
                      "s1_cos_mean": s1["cos_ridge_mean"],
                      "s2_cos_mean": s2["cos_neural"],
                      "s2_verdict": s2["verdict"]}, indent=1), flush=True)
    (RUN / "COS_FIX.json").write_text(json.dumps(
        {"stage_one": s1c, "stage_two": s2c}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
