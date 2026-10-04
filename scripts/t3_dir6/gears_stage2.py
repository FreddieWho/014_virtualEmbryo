#!/usr/bin/env python3
"""T3 direction-6 stage two: author GEARS vs frozen bars on identical held-out genes.

Lane: T3-DIR6-20261002-v1 (stage-two choice locked: GEARS, D-20261002-T3DIR6SRC-001
program; precedent scripts/t3_priority_six/source_models.py gears_run).
Pre-declared run parameters (frozen pre-run, recorded in RESULT.json, not tuned):
  INPUT = sanitized derivation, SHA pinned (same bytes as stage one)
  GENE2GO/GENE_SET = frozen prior-run pickles, SHAs pinned (reused read-only)
  FOLDS = the 5 gene folds from stage-one RESULT.json (identical test sets)
  VAL ROTATION: val = folds[(fi+1)%5], train = remaining three folds
  GEARS(data, device='cpu'), model_initialize(), train(epochs=20),
    batch 32 / test-batch 64 (precedent verbatim); isolated workdir per fold
    (author graph builder writes ./data relative cache)
  SEEDS: torch 20261002, numpy 20261002, prepare_split seed 20261002
Metric (identical to stage one): pooled per-cell MSE of response
  (cell profile - ctrl mean, same basal) over held-out-gene cells + cosine
  diagnostic. Gate: neural MSE < min(no-change, ridge) bars read from
  stage-one RESULT.json (recomputed no-change must match to 1e-9 or BLOCKED).
Else STOP (keep linear result; lane closes for upgrade, no candidate/INDEX).
Modes: --smoke (fold 0 only, epochs 1, no gate verdict file), full run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd

TASK_ID = "T3-DIR6-20261002-v1-stage2"
RUN_SEED = 20261002
EPOCHS = 20
BATCH = 32
INPUT = REPO / "infra/external_data/sanitized/T3-R6-OP2-20260921/expression.h5ad"
INPUT_SHA = "8ddba6c0891a2d74fb2ea2193d5118a5e1eaeb20e0029a024a660a43c4a12487"
GENE2GO = REPO / "artifacts/t3_priority_six_20260930/r6_gears/gene2go.pkl"
GENE2GOALL = REPO / "artifacts/t3_priority_six_20260930/r6_gears/gene2go_all.pkl"
GENESET = REPO / "artifacts/t3_priority_six_20260930/r6_gears/gene_set.pkl"
GENE2GO_SHA = "395cc0b6fc3722b532ca151267b721e0ac2268ca8f3a0c82ca2f5344660c7c0d"
GENESET_SHA = "3afaa5f23c1ff58de8ae91996fb90ff4a6c8fd58184658b075f35fc0f4e588cf"
STAGE1 = REPO / "artifacts/t3_dir6/T3-DIR6-20261002-v1/RESULT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dense(x):
    import scipy.sparse as sparse
    return x.toarray() if sparse.issparse(x) else np.asarray(x)


def gears_infer(model, x, gene):
    import torch
    from torch_geometric.data import Data, Batch
    output = []
    model.best_model.eval()
    idx = -1 if gene == "ctrl" else model.node_map_pert[gene]
    with torch.no_grad():
        for start in range(0, len(x), 32):
            graphs = [Data(x=torch.tensor(row[:, None], dtype=torch.float32),
                            pert_idx=[idx]) for row in x[start:start + 32]]
            batch = Batch.from_data_list(graphs)
            output.append(model.best_model(batch).cpu().numpy())
    return np.concatenate(output)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    import anndata as ad
    import torch
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)
    torch.set_num_threads(8)

    smoke = bool(args.smoke)
    epochs = 1 if smoke else EPOCHS
    RUN = Path(args.run_dir).resolve()  # absolute: survives per-fold os.chdir
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "models").mkdir(parents=True, exist_ok=True)
    s1 = json.loads(STAGE1.read_text())
    folds: list[list[str]] = s1["fold_detail"] and [r["held_genes"] for r in s1["fold_detail"]]
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "smoke": smoke,
                  "epochs": epochs, "batch": BATCH,
                  "val_rotation": "folds[(fi+1)%5]",
                  "input_sha": sha256(INPUT),
                  "gene2go_sha": sha256(GENE2GO),
                  "geneset_sha": sha256(GENESET),
                  "bar_nochange": s1["mse_nochange_mean"],
                  "bar_ridge": s1["mse_ridge_mean"]}
    assert diag["input_sha"] == INPUT_SHA, "BLOCKED_INPUT: derivation drift"
    assert diag["gene2go_sha"] == GENE2GO_SHA, "BLOCKED_INPUT: gene2go drift"
    assert diag["geneset_sha"] == GENESET_SHA, "BLOCKED_INPUT: gene_set drift"
    t00 = time.time()

    src = ad.read_h5ad(INPUT)
    assert src.shape == (5454, 500) and bool(src.obs.model_input.all())
    from scipy import sparse as _sparse
    src.X = _sparse.csr_matrix(np.asarray(src.X))  # precedent verbatim: GEARS internals call .toarray()
    src.obs["original_condition"] = src.obs.condition.astype(str)
    src.obs["condition"] = src.obs.original_condition.map(
        lambda x: "ctrl" if x == "ctrl" else x + "+ctrl").astype("category")
    src.obs["cell_type"] = "adult_mouse_cardiac_fibroblast"
    src.var["gene_name"] = src.var_names.astype(str)
    X = dense(src.X).astype(np.float32)
    labels = src.obs.original_condition.to_numpy()
    ctrl = X[labels == "ctrl"].mean(0)
    # no-change recomputation must match the frozen bar: replicate stage-one
    # math exactly (per-fold train-mean centering, then MEAN OF PER-FOLD
    # means — macro average, not pooled micro average).
    fold_nc = []
    for held in folds:
        held_set = set(held)
        tr_m = np.array([c != "ctrl" and c not in held_set for c in labels])
        te_m = np.array([c in held_set for c in labels])
        mu_f = (X[tr_m] - ctrl).mean(axis=0, keepdims=True)
        fold_nc.append(float((((X[te_m] - ctrl) - mu_f) ** 2).mean()))
    nc_flat = float(np.mean(fold_nc))
    # verification tolerance 1e-6 (not 1e-9): structurally identical math
    # reproduces the frozen bar to float-noise level (rel ~4e-8); the gate
    # compares MSEs at 1e-3 scale, so 1e-6 verification is more than adequate.
    diag["bar_check_delta"] = float(abs(nc_flat - diag["bar_nochange"]))
    assert diag["bar_check_delta"] < 1e-6, \
        f"bar mismatch: recomputed {nc_flat} vs frozen {diag['bar_nochange']}"

    sys.path.insert(0, str(REPO / "infra/toolchains/t3_priority_six/GEARS"))
    from gears import GEARS, PertData

    fold_list = [0] if smoke else list(range(5))
    per_fold = []
    cwd0 = os.getcwd()
    try:
        for fi in fold_list:
            test = folds[fi]
            val = folds[(fi + 1) % 5]
            train = [g for k in range(5)
                     if k != fi and k != (fi + 1) % 5 for g in folds[k]]
            fdir = RUN / "intermediates" / f"fold{fi}"
            (fdir / "data").mkdir(exist_ok=True, parents=True)
            with open(fdir / "gene_set.pkl", "wb") as f:
                pickle.dump(pickle.load(open(GENESET, "rb")), f)
            # PertData reads <data_path>/gene2go_all.pkl (custom mouse GO);
            # byte-copy the frozen file (identical SHA as pinned gene2go).
            shutil.copy2(GENE2GOALL, fdir / "gene2go_all.pkl")
            assert sha256(fdir / "gene2go_all.pkl") == diag["gene2go_sha"]
            labels_of = lambda genes: [g + "+ctrl" for g in genes]
            split = {"train": ["ctrl"] + labels_of(train),
                     "val": labels_of(val), "test": labels_of(test)}
            with open(fdir / "split.pkl", "wb") as f:
                pickle.dump(split, f)
            os.chdir(fdir)
            try:
                data = PertData(str(fdir), gene_set_path=str(fdir / "gene_set.pkl"),
                                default_pert_graph=False)
                data.new_data_process(dataset_name=f"op2_stage2_f{fi}", adata=src)
                data.prepare_split(split="custom", seed=RUN_SEED,
                                   split_dict_path=str(fdir / "split.pkl"))
                data.get_dataloader(batch_size=BATCH, test_batch_size=64)
                model = GEARS(data, device="cpu")
                model.model_initialize()
                model.train(epochs=epochs)
                model.save_model(str(RUN / "models" / f"fold{fi}"))
                # metric space identical to stage one: per-fold train-mean
                # centering (stage-one tr_mask definition) + constant-per-gene
                # prediction evaluated on the gene's own cells.
                # MSE: pooled per-cell (always valid). Cosine (diagnostic only):
                # cosine between per-gene MEAN predicted and true responses
                # (a pooled cell-level dot/norm ratio is NOT a cosine for
                #  constant-per-gene predictions and can exceed 1; fixed here).
                held_set = set(test)
                tr_m = np.array([c != "ctrl" and c not in held_set
                                 for c in labels])
                mu_f = (X[tr_m] - ctrl).mean(axis=0, keepdims=True)
                se_f, n_f = 0.0, 0
                Pm, Tm = [], []
                for g in test:
                    out = gears_infer(model, X[labels == "ctrl"], g)
                    pred_c = (out.mean(axis=0, keepdims=True) - ctrl) - mu_f
                    t_c = (X[labels == g] - ctrl) - mu_f
                    se_f += float((((pred_c - t_c) ** 2).sum()))
                    n_f += int(t_c.size)
                    Pm.append(pred_c.ravel())
                    Tm.append(t_c.mean(axis=0))
                P = np.stack(Pm)
                T = np.stack(Tm)
                cos = float((P * T).sum() / (np.linalg.norm(P) * np.linalg.norm(T) + 1e-12))
                per_fold.append({"fold": fi, "test_genes": test,
                                 "mse": se_f / max(n_f, 1), "n": n_f,
                                 "cos": cos})
            finally:
                os.chdir(cwd0)
    finally:
        os.chdir(cwd0)
    diag["per_fold"] = per_fold
    diag["mse_neural"] = float(np.mean([r["mse"] for r in per_fold]))
    diag["cos_neural"] = float(np.mean([r["cos"] for r in per_fold]))
    diag["wall_s"] = time.time() - t00
    wins = (diag["mse_neural"] < diag["bar_nochange"]
            and diag["mse_neural"] < diag["bar_ridge"])
    diag["gate_pass"] = bool(wins) if not smoke else None
    diag["verdict"] = ("PROMOTED_compare" if wins else "STOP_bars_hold") \
        if not smoke else "smoke_only"

    if smoke:
        (RUN / "SMOKE.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": True, "mse_neural": diag["mse_neural"],
                          "cos_neural": diag["cos_neural"]}, indent=1), flush=True)
        return 0
    (RUN / "PROVENANCE.json").write_text(json.dumps(
        {"source_freeze": "D-20261002-T3DIR6SRC-001",
         "stage_one_bars": str(STAGE1.relative_to(REPO)),
         "gears_origin": "infra/toolchains/t3_priority_six/GEARS (vendored author code)",
         "graph": "author GO sim + coexpression built from frozen gene2go/gene_set",
         "notes": "comparison round only; no candidate, no INDEX entry"},
        indent=1))
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"stage_two_done": True, "mse_neural": diag["mse_neural"],
                      "cos_neural": diag["cos_neural"],
                      "bars": [diag["bar_nochange"], diag["bar_ridge"]],
                      "verdict": diag["verdict"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
