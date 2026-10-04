#!/usr/bin/env python3
"""T3 direction-6 stage one: ridge gene-embedding baseline on released source.

Lane: T3-DIR6-20261002-v1 (DESIGN.md frozen 2026-10-02; source frozen
D-20261002-T3DIR6SRC-001; owner release D-20261002-T3DIR6-001).
Pre-declared run parameters (frozen pre-run, recorded in RESULT.json, not tuned):
  INPUT_SHA = indexed sanitized derivation (R6 scope file, reused read-only)
  GO_SHA = indexed cached GO functional embedding (ontology only, no KO)
  SPLIT_SEED = 20261002, N_FOLDS = 5 over the 26 perturbation genes
    (fold sizes 5,5,5,5,6 from seeded shuffle of the sorted gene list)
  EMBED_FORM = fixed GO-128 rows (prior knowledge, identical for train/test
    genes by design; held-out validity holds because test RESPONSES are unseen)
  ALPHA = 1.0 single value; solver cholesky (deterministic); response and
    embedding columns centered/scaled with TRAIN-gene stats only (no leakage).
Model: per-target-gene Ridge(one-hot) = shrinkage per-gene response means.
Target: cell response = log1p profile - WT basal (ctrl mean, shared with any
  future neural model). Metric: pooled per-cell MSE on held-out genes;
  cosine similarity recorded as diagnostic only.
Bars recorded for the stage-two gate: no-change MSE (predict 0) and ridge MSE
on the SAME held-out genes. This round builds NO candidate, NO INDEX entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd

TASK_ID = "T3-DIR6-20261002-v1"
RUN_SEED = 20261002
SPLIT_SEED = 20261002
N_FOLDS = 5
ALPHA = 1.0
INPUT = REPO / "infra/external_data/sanitized/T3-R6-OP2-20260921/expression.h5ad"
INPUT_SHA = "8ddba6c0891a2d74fb2ea2193d5118a5e1eaeb20e0029a024a660a43c4a12487"
GO_EMB = REPO / "artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz"
GO_SHA = "acdb554d47989a4d8230fb8acc0fc7d20ec40e12086b56ef1715afb8fee11e0d"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    import anndata as ad
    from sklearn.linear_model import Ridge

    smoke = bool(args.smoke)
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "smoke": smoke,
                  "n_folds": N_FOLDS, "split_seed": SPLIT_SEED,
                  "alpha": ALPHA, "embed_form": "GO-128-fixed",
                  "go_sha": sha256(GO_EMB),
                  "input_sha": sha256(INPUT)}
    assert diag["input_sha"] == INPUT_SHA, "BLOCKED_INPUT: sanitized derivation hash drift"
    assert diag["go_sha"] == GO_SHA, "BLOCKED_INPUT: GO embedding hash drift"
    go = np.load(GO_EMB)
    go_genes = [str(x) for x in go["genes"]]
    go_mat = go["embedding"].astype(np.float64)
    go_pos = {g: j for j, g in enumerate(go_genes)}
    t00 = time.time()

    a = ad.read_h5ad(INPUT)
    X = np.asarray(a.X, dtype=np.float64)
    cond = np.asarray(a.obs["condition"].astype(str))
    genes = sorted(set(cond.tolist()) - {"ctrl"})
    assert len(genes) == 26, f"expected 26 perturbations, got {len(genes)}"
    basal = X[cond == "ctrl"].mean(axis=0)
    assert all(g in go_pos for g in genes), "GO embedding missing perturbation genes"
    diag["n_ctrl"] = int((cond == "ctrl").sum())
    diag["perturbation_genes"] = genes

    if smoke:
        genes = genes[:3]
        nfolds = 2
    else:
        nfolds = N_FOLDS
    rng = np.random.default_rng(SPLIT_SEED)
    order = rng.permutation(len(genes))
    folds: list[list[str]] = [[] for _ in range(nfolds)]
    for rank, gi in enumerate(order.tolist()):
        folds[rank % nfolds].append(genes[gi])
    diag["folds"] = folds

    fold_rows = []
    for fi, held in enumerate(folds):
        held_set = set(held)
        tr_mask = np.array([c != "ctrl" and c not in held_set for c in cond])
        te_mask = np.array([c in held_set for c in cond])
        Xtr, Xte = X[tr_mask], X[te_mask]
        ytr = Xtr - basal
        yte = Xte - basal
        mu = ytr.mean(axis=0, keepdims=True)  # train-only centering
        ytr_c, yte_c = ytr - mu, yte - mu
        tr_genes = sorted(set(cond[tr_mask].tolist()))
        Etr_raw = np.stack([go_mat[go_pos[g]] for g in tr_genes])
        mu_e = Etr_raw.mean(axis=0, keepdims=True)
        sd_e = Etr_raw.std(axis=0, keepdims=True) + 1e-8
        Ftr = np.stack([(go_mat[go_pos[c]] - mu_e.ravel()) / sd_e.ravel()
                        for c in cond[tr_mask]])
        model = Ridge(alpha=ALPHA, solver="cholesky")
        model.fit(Ftr, ytr_c)
        Ete = np.stack([(go_mat[go_pos[c]] - mu_e.ravel()) / sd_e.ravel()
                        for c in cond[te_mask]])
        pred = model.predict(Ete)
        # held-out validity: test genes' RESPONSES never enter training
        # (train/test split is by gene; embeddings are fixed prior knowledge).
        assert not (set(held) & set(tr_genes)), "gene-held-out violated"
        mse_ridge = float(np.mean((yte_c - pred) ** 2))
        mse_nochange = float(np.mean(yte_c ** 2))
        num = float((yte_c * pred).sum())
        den = float(np.linalg.norm(yte_c) * np.linalg.norm(pred) + 1e-12)
        fold_rows.append({"fold": fi, "held_genes": held,
                          "n_test_cells": int(te_mask.sum()),
                          "mse_nochange": mse_nochange, "mse_ridge": mse_ridge,
                          "cos_ridge": num / den})
    diag["fold_detail"] = fold_rows
    diag["mse_nochange_mean"] = float(np.mean([r["mse_nochange"] for r in fold_rows]))
    diag["mse_ridge_mean"] = float(np.mean([r["mse_ridge"] for r in fold_rows]))
    diag["cos_ridge_mean"] = float(np.mean([r["cos_ridge"] for r in fold_rows]))
    diag["wall_s"] = time.time() - t00

    if smoke:
        (RUN / "SMOKE.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": True,
                          "mse_nochange": diag["mse_nochange_mean"],
                          "mse_ridge": diag["mse_ridge_mean"]}, indent=1), flush=True)
        return 0

    prov = {"source_freeze": "D-20261002-T3DIR6SRC-001",
            "owner_release": "D-20261002-T3DIR6-001",
            "permit": "reports/t3_data_intake_20260920/TASK_DATA_PERMIT.json",
            "input": {"path": str(INPUT.relative_to(REPO)), "sha256": diag["input_sha"]},
            "wt_basal": "ctrl-cell mean, shared representation for stage two",
            "notes": "comparison round only; no candidate, no INDEX entry"}
    (RUN / "PROVENANCE.json").write_text(json.dumps(prov, indent=1))
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"stage_one_done": True,
                      "mse_nochange": diag["mse_nochange_mean"],
                      "mse_ridge": diag["mse_ridge_mean"],
                      "cos_ridge": diag["cos_ridge_mean"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
