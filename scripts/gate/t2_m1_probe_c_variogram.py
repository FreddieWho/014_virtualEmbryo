#!/usr/bin/env python3
"""T2 九路线 M1 探针 C：现役 selection 相对其父版本在「基因间协方差」子分上是赚是亏。

背景：闸门 A 若确认官方 ``variogram`` 奖励的是基因间联合分布（坐标无关），那么
一个关键问题立刻出现——**现役的表达桥在拿到 de/d2/occupancy 增益的同时，是否
牺牲了 variogram？** 表达桥按细胞类型重分配表达取值、并做组成重采样；只要它
在基因维度上引入任何独立扰动或跨基因混合，基因间协方差就会退化。

本探针对三个 board 各取「现役 selection」与其「迭代父版本」，在同一 pseudo-target
上计算 variogram_score，并同时给出 mmd_u / energy_distance 作为分布侧对照：

- 若 selection 的 variogram **劣于**父版本，说明存在一块"已被牺牲、可以免费拿回"
  的分数，且拿回它不影响任何其他子分——这是本轮最可能的高性价比入口。
- 若 selection 的 variogram **不劣于**父版本，说明该子分从未被这条流水线动过，
  headroom 需靠新机制而非"修复"。

只读既有 artifact，不写候选、不改已评分文件。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
VECKIT = PROJECT_ROOT / "third_party/veckit"
if str(VECKIT) not in sys.path:
    sys.path.insert(0, str(VECKIT))

import anndata as ad  # noqa: E402
import scipy.sparse as sp  # noqa: E402

from common.core_metrics import variogram_score  # type: ignore

OUT_DIR = PROJECT_ROOT / "artifacts/gate/T2_M1_GATES_20260927-v1"

# board -> (pseudo_target, [(role, path), ...])
BOARDS: dict[str, dict[str, Any]] = {
    "T2_embryo_val_interp": {
        "pseudo_target": "data/E7.25.h5ad",
        "arms": [
            ("selection_v0010", "submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad"),
            ("parent_v0002", "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad"),
            ("floor_copy_last", "submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad"),
        ],
    },
    "T2_heart_val_interp": {
        "pseudo_target": "data/E8.75.h5ad",
        "arms": [
            ("selection_v0013", "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad"),
            ("j1_fgw_v0009", "submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad"),
            ("floor_copy_last", "submissions/scored/baseline-001/T2_heart_val_interp/submission.h5ad"),
        ],
    },
    "T2_heart_val_extrap": {
        "pseudo_target": "data/E9.5.h5ad",
        "arms": [
            ("iteration_parent_v0011", "submissions/candidates/T2_heart_val_extrap/v0011_g0_t2_r2_shrink/submission.h5ad"),
            ("selection_v0001", "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"),
        ],
    },
}


def load_X(path: Path) -> np.ndarray:
    a = ad.read_h5ad(path)
    X = a.X
    X = X.toarray() if sp.issparse(X) else np.asarray(X)
    return np.asarray(X, dtype=np.float64)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema": "ve.t2.m1-probe-c.variogram-tradeoff.v1",
        "date": "2026-09-27",
        "question": "现役 selection 相对父版本/基线，在基因间协方差(variogram)子分上是赚还是亏？",
        "boards": {},
    }
    for board, spec in BOARDS.items():
        started = time.time()
        truth = load_X(PROJECT_ROOT / spec["pseudo_target"])
        rows: list[dict[str, Any]] = []
        for role, rel in spec["arms"]:
            p = PROJECT_ROOT / rel
            if not p.exists():
                rows.append({"role": role, "path": rel, "status": "MISSING"})
                continue
            X = load_X(p)
            g = min(X.shape[1], truth.shape[1])
            row: dict[str, Any] = {
                "role": role,
                "path": rel,
                "n_cells": int(X.shape[0]),
                "n_genes": int(g),
                "variogram": float(variogram_score(X[:, :g], truth[:, :g])),
            }
            # 分布侧对照：整体分布与协方差分离度
            from common.core_metrics import energy_distance, mmd_unbiased  # type: ignore

            row["energy_distance"] = float(energy_distance(X[:, :g], truth[:, :g]))
            row["mmd_u"] = float(mmd_unbiased(X[:, :g], truth[:, :g]))
            rows.append(row)
        payload["boards"][board] = {
            "pseudo_target": spec["pseudo_target"],
            "n_truth_cells": int(truth.shape[0]),
            "arms": rows,
            "wall_seconds": time.time() - started,
        }
        print(f"=== {board} ===", flush=True)
        for r in rows:
            if r.get("status") == "MISSING":
                print(f"  {r['role']:<24} MISSING", flush=True)
            else:
                print(
                    f"  {r['role']:<24} variogram={r['variogram']:.6f} "
                    f"energy={r['energy_distance']:.4f} mmd_u={r['mmd_u']:.5f}",
                    flush=True,
                )
    (OUT_DIR / "probe_c_variogram_tradeoff.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"\nwritten: {(OUT_DIR / 'probe_c_variogram_tradeoff.json').relative_to(PROJECT_ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
