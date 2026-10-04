#!/usr/bin/env python3
"""T2 探针 D：定位 B4-T2-R2 表达桥的哪一臂破坏了基因间协方差。

背景（D-20260927-T2GATES-001 探针 C）：在两个插值板上，现役 selection 相对
"什么都不改"基线**主动恶化**官方 ``variogram`` 子分——embryo 2.49x、heart_interp
1.44x。而 ``variogram_score(pred_X, true_X)`` 经闸门 A 实证确认为**基因间协方差**
（坐标无关；行置换不可分辨，基因独立打乱恶化 4.35x）。registry 里 heart 的
``variogram`` 子分仅 32.2（其余 53-62），方向一致。

本探针要回答的问题：**B4-T2-R2 的两条臂里，是 L1（mean bridge）还是
L2（mean + mass，即组成重采样）造成了这笔损失？**

为什么这个定位值得先做：

* L2 mean+mass 拿到的服务器增益最大（embryo +2.14 / heart +4.79），若破坏协方差
  的是 mass 臂，那么存在一块**已被牺牲、可以在不动其他子分的前提下拿回**的分数；
* 若破坏来自 L1 mean bridge 本身，则机制不同（表达插值本身在基因维度引入独立
  扰动），修复方向也不同；
* 四臂均已评分、文件在盘、pseudo-target 与 seed 已冻结，因此本探针**只读、不训练、
  不建候选、不动任何已评分文件**。

设计上刻意做两件事：

1. 报出每个臂的 ``variogram_score`` **与其父版本的差**，而不是绝对值（绝对值在
   pseudo-target 上不可解释，差值是同目标同 seed 的相对量）。
2. 同时报 ``mmd_u`` / ``energy_distance`` 作为分布侧对照，判断协方差的损失是否
   伴随分布整体漂移——若伴随，则"协方差损失"只是更大问题的伴随现象，不宜单独归因。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VECKIT = PROJECT_ROOT / "third_party/veckit"
if str(VECKIT) not in sys.path:
    sys.path.insert(0, str(VECKIT))

from common.core_metrics import (  # noqa: E402
    energy_distance,
    mmd_unbiased,
    variogram_score,
)

OUT_DIR = PROJECT_ROOT / "artifacts/gate/T2_PROBE_D_GENE_COV-20260927-v1"

# board -> (pseudo-target, reference, seed)  全部沿用 B4-T2-R2 自身记录的口径
BOARDS: dict[str, dict[str, Any]] = {
    "T2_embryo_val_interp": {
        "target": "data/E7.25.h5ad",
        "reference": "data/E6.75.h5ad",
        "seed": 20260911,
        "arms": {
            # 父版本（迭代基线，未经表达桥）
            "parent_v0002_g1_formal_log_rms":
                "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
            "L1_mean_bridge_v0009":
                "submissions/candidates/T2_embryo_val_interp/v0009_b4_t2_r2_l1_mean_bridge/submission.h5ad",
            "L2_mean_mass_bridge_v0010":
                "submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        },
    },
    "T2_heart_val_interp": {
        "target": "data/E8.75.h5ad",
        "reference": "data/E8.25_late.h5ad",
        "seed": 20260911,
        "arms": {
            "parent_v0007_t2_s3_l1_pycpd":
                "submissions/candidates/T2_heart_val_interp/v0007_t2_s3_l1_pycpd/submission.h5ad",
            "L1_mean_bridge_v0012":
                "submissions/candidates/T2_heart_val_interp/v0012_b4_t2_r2_l1_mean_bridge/submission.h5ad",
            "L2_mean_mass_bridge_v0013":
                "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        },
    },
    "T2_heart_val_extrap": {
        "target": "data/E9.5.h5ad",
        "reference": "data/E8.75.h5ad",
        "seed": 20260916,
        "arms": {
            "parent_baseline_v0001_pseudobulk_shift":
                "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad",
            "G1_R2_shrink_v0011":
                "submissions/candidates/T2_heart_val_extrap/v0011_g0_t2_r2_shrink/submission.h5ad",
        },
    },
}

N_SUBSAMPLE = 2000
MMD_SEED = 0


def _load(path: Path) -> tuple[np.ndarray, list[str]]:
    import anndata as ad

    adata = ad.read_h5ad(path)
    X = adata.X
    X = np.asarray(X.todense()) if hasattr(X, "todense") else np.asarray(X)
    return np.asarray(X, dtype=np.float64), [str(g) for g in adata.var_names]


def _load_truth(path: Path) -> np.ndarray:
    import anndata as ad

    adata = ad.read_h5ad(path)
    X = adata.X
    X = np.asarray(X.todense()) if hasattr(X, "todense") else np.asarray(X)
    return np.asarray(X, dtype=np.float64)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema": "ve.t2.probe-d-gene-cov.v1",
        "atom": "T2-PROBE-D-GENE-COV-20260927-v1",
        "question": "which arm of B4-T2-R2 destroys gene-gene covariance: L1 mean bridge or L2 mean+mass?",
        "metric_note": "variogram_score is CONFIRMED by gate A to be gene-gene covariance and coordinate-free; only same-target same-seed DIFFERENCES against the parent are interpretable.",
        "boards": {},
    }

    for board, spec in BOARDS.items():
        started = time.time()
        true_X = _load_truth(PROJECT_ROOT / spec["target"])
        board_rows: dict[str, Any] = {}
        for arm, rel in spec["arms"].items():
            path = PROJECT_ROOT / rel
            if not path.is_file():
                board_rows[arm] = {"status": "MISSING", "path": rel}
                continue
            pred_X, genes = _load(path)
            if pred_X.shape[1] != true_X.shape[1]:
                board_rows[arm] = {
                    "status": "GENE_COUNT_MISMATCH",
                    "pred_genes": int(pred_X.shape[1]),
                    "true_genes": int(true_X.shape[1]),
                    "path": rel,
                }
                continue
            board_rows[arm] = {
                "status": "OK",
                "path": rel,
                "n_cells": int(pred_X.shape[0]),
                "n_genes": int(pred_X.shape[1]),
                "variogram_score": float(variogram_score(pred_X, true_X)),
                "mmd_u": float(mmd_unbiased(pred_X, true_X, n=N_SUBSAMPLE, seed=MMD_SEED)),
                "energy_distance": float(energy_distance(pred_X, true_X)),
            }
            print(
                f"{board} | {arm}: variogram={board_rows[arm]['variogram_score']:.6f} "
                f"mmd_u={board_rows[arm]['mmd_u']:.5f} "
                f"energy={board_rows[arm]['energy_distance']:.5f}",
                flush=True,
            )

        # 同目标相对差：L1/L2 各自相对父版本
        parent_key = next((k for k in spec["arms"] if k.startswith("parent_")), None)
        if parent_key and board_rows.get(parent_key, {}).get("status") == "OK":
            base = board_rows[parent_key]["variogram_score"]
            for key, row in board_rows.items():
                if key == parent_key or row.get("status") != "OK":
                    continue
                row["variogram_delta_vs_parent"] = row["variogram_score"] - base
                row["variogram_ratio_vs_parent"] = row["variogram_score"] / base
        payload["boards"][board] = {
            "pseudo_target": spec["target"],
            "reference": spec["reference"],
            "seed": spec["seed"],
            "parent_arm": parent_key,
            "arms": board_rows,
            "wall_seconds": time.time() - started,
        }
        print(f"-- {board} done in {payload['boards'][board]['wall_seconds']:.1f}s", flush=True)

    payload["declarations"] = [
        "read-only: no candidate, no h5ad output, no submission, no INDEX row, no upload",
        "no server score is claimed or implied; pseudo-target stages are observed source stages",
        "variogram_score carries ~4.2% seed noise (gate calibration); differences below that are not interpretable",
        "only differences against the same-target same-seed parent are interpreted, never absolute values",
        "arm paths are taken verbatim from submissions/INDEX.tsv (verified against it before the run)",
    ]
    (OUT_DIR / "probe_d_gene_cov.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {OUT_DIR / 'probe_d_gene_cov.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
