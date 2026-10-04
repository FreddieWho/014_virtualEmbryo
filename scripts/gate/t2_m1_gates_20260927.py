#!/usr/bin/env python3
"""T2 九路线 M1 预执行闸门（2026-09-27）。

两个闸门，各约 1 CPU·h 以内，**不消耗 9-lane 预算**，目的是在任何设计冻结与训练
之前把两条承重不确定性变成可判定的事实。

闸门 A（heart）：官方 ``variogram`` 子分究竟奖励什么？架构重置文件把它列为
「明确 headroom（heart 约 28 分）」，三份检索简报也都据此把新路线押在"空间
二阶结构"上。但 ``core_metrics.variogram_score`` 的签名是
``variogram_score(pred_X, true_X)``，**不接收坐标**，其 docstring 自述为
"gene-gene covariance structure"。若属实，则那三条路线的被预测量是错的。
本闸门不靠读码下结论，用三个对照臂实证：
  A1 坐标置乱：把预测的表达行随机置换、坐标不动。若分数不变 ⇒ 该分数与空间无关。
  A2 基因置乱：把基因列随机置换。若分数显著变差 ⇒ 该分数由基因间联合分布决定。
  A3 现役候选 vs 其父版本/基线：该子分当前的绝对水平与可移动空间。

闸门 B（embryo）："位置→表达参考"这一前提在该板是否整体失效？检索建议重算
探针三变体（z-score / 只留高 Δ 结构基因 / 层内算相关＋几何自洽性）。三变体
若全 ≤ 0，则该前提失效，算力应从 E-N2(VGM) 压到 E-N1(SBL)。

两闸门只读既有 artifact，不写任何候选、不改任何已评分文件。
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
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

OUT_DIR = PROJECT_ROOT / "artifacts/gate/T2_M1_GATES_20260927-v1"

import anndata as ad  # noqa: E402
import scipy.sparse as sp  # noqa: E402

from scripts.t2_j1_fgw_assignment import (  # noqa: E402
    REG_K,
    _coords,
    _dense_float32,
    best_proper_flip,
    canonicalize,
    load_stage_support,
    single_stage_cross_probe,
)

PANEL_EMBRYO = PROJECT_ROOT / "data/gene_panel/T2__embryo__val_interp.genes.txt"
PANEL_HEART = PROJECT_ROOT / "data/gene_panel/T2__heart__val_interp.genes.txt"
PANEL_HEART_EXTRAP = PROJECT_ROOT / "data/gene_panel/T2__heart__val_extrap.genes.txt"


def read_panel(path: Path) -> list[str]:
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_h5ad_X(path: Path) -> np.ndarray:
    a = ad.read_h5ad(path)
    X = a.X
    X = X.toarray() if sp.issparse(X) else np.asarray(X)
    return np.asarray(X, dtype=np.float64)


# --------------------------------------------------------------------------
# 闸门 A：官方 variogram 到底奖励什么
# --------------------------------------------------------------------------
def gate_a(veckit_dir: Path) -> dict[str, Any]:
    sys.path.insert(0, str(veckit_dir))
    from common.core_metrics import variogram_score  # type: ignore

    cand = PROJECT_ROOT / "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad"
    truth = PROJECT_ROOT / "data/E8.75.h5ad"
    started = time.time()

    X_pred = load_h5ad_X(cand)
    X_true = load_h5ad_X(truth)
    n_genes = min(X_pred.shape[1], X_true.shape[1])
    X_pred, X_true = X_pred[:, :n_genes], X_true[:, :n_genes]

    base = float(variogram_score(X_pred, X_true))

    # A1 坐标/行置乱：把预测的行随机打乱（等价于"空间排布完全改变、每基因边际分布不变"）
    rng = np.random.default_rng(20260927)
    perm_rows = rng.permutation(X_pred.shape[0])
    a1_rowshuffled = float(variogram_score(X_pred[perm_rows], X_true))

    # A1b 只打乱一行的子集，确认不是被 n_cells 抽样掩盖
    a1b = float(variogram_score(X_pred[rng.permutation(X_pred.shape[0])[: X_pred.shape[0] // 2]], X_true))

    # A2 基因列置乱：基因间联合被打散，每基因边际不变
    perm_genes = rng.permutation(n_genes)
    a2_geneshuffled = float(variogram_score(X_pred[:, perm_genes], X_true[:, perm_genes]))

    # A2b 同基因列置乱但 truth 不置乱（只打乱预测的联合）
    a2b = float(variogram_score(X_pred[:, perm_genes], X_true))

    # A3 对照：完美预测（用真值自身）与 do-nothing 基线
    a3_perfect = float(variogram_score(X_true, X_true))

    verdict_coord_free = bool(abs(a1_rowshuffled - base) / max(base, 1e-12) < 1e-9)
    verdict_gene_joint = bool(a2_geneshuffled > base * 1.5)

    return {
        "gate": "A_variogram_type",
        "question": "官方 variogram 子分奖励空间二阶结构，还是基因间协方差结构？",
        "candidate": str(cand.relative_to(PROJECT_ROOT)),
        "truth_pseudo_target": str(truth.relative_to(PROJECT_ROOT)),
        "n_pred_cells": int(X_pred.shape[0]),
        "n_true_cells": int(X_true.shape[0]),
        "n_genes_used": int(n_genes),
        "arms": {
            "base_current_candidate": base,
            "A1_pred_rows_shuffled_coords_fixed": a1_rowshuffled,
            "A1b_pred_rows_shuffled_half": a1b,
            "A2_genes_shuffled_both_sides": a2_geneshuffled,
            "A2b_genes_shuffled_pred_only": a2b,
            "A3_truth_against_itself": a3_perfect,
        },
        "derived": {
            "relative_change_under_row_shuffle": (a1_rowshuffled - base) / max(base, 1e-12),
            "ratio_under_gene_shuffle": a2_geneshuffled / max(base, 1e-12),
            "ratio_gene_shuffle_pred_only": a2b / max(base, 1e-12),
        },
        "verdict": {
            "insensitive_to_row_order_hence_coordinate_free": verdict_coord_free,
            "driven_by_gene_gene_joint": verdict_gene_joint,
            "conclusion": (
                "CONFIRMED_GENE_GENE: 该分数对行置乱完全不敏感、对基因列置乱敏感，"
                "故它约束的是基因间联合分布，不含任何空间信息。"
                if (verdict_coord_free and verdict_gene_joint)
                else "INCONCLUSIVE: 对照臂未同时满足两个条件，需人工判读。"
            ),
        },
        "wall_seconds": time.time() - started,
        "disclosure": "E8.75 为观测期源阶段，在此仅作结构判定之用，不作 leaderboard 证据。",
    }


# --------------------------------------------------------------------------
# 闸门 B：embryo 位置→表达参考三变体
# --------------------------------------------------------------------------
def _nbhd_pearson(ref: np.ndarray, truth: np.ndarray, coords: np.ndarray) -> float:
    from scripts.t2_j1_proxy import neighbourhood_pearson  # type: ignore

    return float(neighbourhood_pearson(ref, truth, coords))


def _probe_variant(
    src_X: np.ndarray,
    src_coords: np.ndarray,
    eval_X: np.ndarray,
    eval_coords: np.ndarray,
    *,
    variant: str,
    seed: int = 20260927,
) -> dict[str, Any]:
    from sklearn.neighbors import NearestNeighbors

    z_true, *_ = canonicalize(eval_coords)
    z_src, *_ = canonicalize(src_coords)
    flip, _ = best_proper_flip(z_src, z_true)
    z_src = z_src * flip
    knn = NearestNeighbors(n_neighbors=REG_K).fit(z_src)
    idx = knn.kneighbors(z_true, return_distance=False)
    ref = src_X[idx].mean(axis=1)

    if variant == "V0_baseline":
        pass
    elif variant == "V1_zscore":
        mu, sd = ref.mean(0, keepdims=True), ref.std(0, keepdims=True)
        sd = np.where(sd > 1e-9, sd, 1.0)
        ref = (ref - mu) / sd
        tmu, tsd = eval_X.mean(0, keepdims=True), eval_X.std(0, keepdims=True)
        tsd = np.where(tsd > 1e-9, tsd, 1.0)
        eval_X = (eval_X - tmu) / tsd
    elif variant == "V2_high_delta_genes":
        delta = np.abs(eval_X.mean(0) - ref.mean(0))
        keep = np.argsort(-delta)[: max(8, len(delta) // 8)]
        ref = ref[:, keep]
        eval_X = eval_X[:, keep]
    elif variant == "V3_within_layer":
        # 层内标准化：按 truth 坐标的粗 kNN 层标签分别标准化，削弱全局均值漂移
        from sklearn.neighbors import NearestNeighbors as _NN

        k = max(4, len(eval_coords) // 200)
        lab = _NN(n_neighbors=k + 1).fit(eval_coords).kneighbors(eval_coords, return_distance=False)[:, 1:].mean(1)
        lab = np.round(lab, 2)
        ref_out = np.empty_like(ref)
        for level in np.unique(lab):
            m = lab == level
            if m.sum() < 8:
                ref_out[m] = ref[m]
                continue
            blk = ref[m]
            mu, sd = blk.mean(0, keepdims=True), blk.std(0, keepdims=True)
            ref_out[m] = (blk - mu) / np.where(sd > 1e-9, sd, 1.0)
        ref = ref_out
    else:
        raise ValueError(variant)

    return {
        "variant": variant,
        "n_genes_used": int(ref.shape[1]),
        "nbhd_pearson": _nbhd_pearson(ref, eval_X, eval_coords),
    }


def gate_b() -> dict[str, Any]:
    started = time.time()
    from scripts.t2_baseline import load_t2_input  # type: ignore

    results: list[dict[str, Any]] = []
    # 两个方向：E7.25 预测 E8.0（历史为负），E8.0 预测 E7.25（历史为负）
    directions = [
        ("E7.25_to_E8.0", PROJECT_ROOT / "data/E7.25.h5ad", PROJECT_ROOT / "data/E8.0.h5ad"),
        ("E8.0_to_E7.25", PROJECT_ROOT / "data/E8.0.h5ad", PROJECT_ROOT / "data/E7.25.h5ad"),
    ]
    for label, src_path, eval_path in directions:
        src = load_stage_support(src_path, PANEL_EMBRYO, board="embryo", side=label)
        ev = load_t2_input(eval_path, PANEL_EMBRYO)
        eval_X = _dense_float32(ev.X).astype(np.float64)
        eval_coords = _coords(ev, eval_path)
        legacy = single_stage_cross_probe(src, eval_path, PANEL_EMBRYO)
        for variant in ("V0_baseline", "V1_zscore", "V2_high_delta_genes", "V3_within_layer"):
            v = _probe_variant(
                np.asarray(src["X"], dtype=np.float64),
                np.asarray(src["coords"], dtype=np.float64),
                eval_X.copy(),
                eval_coords.copy(),
                variant=variant,
            )
            v["direction"] = label
            v["legacy_probe_value"] = legacy["nbhd_pearson"]
            results.append(v)

    per_direction: dict[str, dict[str, float]] = {}
    for label, _, _ in directions:
        per_direction[label] = {
            r["variant"]: r["nbhd_pearson"] for r in results if r["direction"] == label
        }
    any_positive = any(
        any(v > 0 for k, v in d.items() if k != "V0_baseline") for d in per_direction.values()
    )
    all_nonpos = not any_positive

    return {
        "gate": "B_embryo_position_reference",
        "question": "embryo 板「位置→表达参考」这一前提是否整体失效？三变体全 ≤0 即失效。",
        "legacy_recorded_probe": {
            "7.25->8.0": -0.0292,
            "8.0->7.25": -0.0129,
            "source": "T2-J1-FGW-ASSIGNMENT-20260903-v1 RESULT.md",
        },
        "variants": results,
        "per_direction_summary": per_direction,
        "any_variant_positive_in_any_direction": bool(any_positive),
        "verdict": {
            "premise_holds_somewhere": bool(any_positive),
            "conclusion": (
                "PREMISE_HOLDS: 至少一个变体在一个方向上为正，算力不应从 E-N2(VGM) 压走。"
                if any_positive
                else "PREMISE_FAILS: 全部变体全部方向均 ≤0，「位置→表达」前提在该板整体失效，"
                "算力应从 E-N2(VGM) 压到 E-N1(SBL)。"
            ),
        },
        "wall_seconds": time.time() - started,
        "disclosure": "E7.25/E8.0 均为观测期 stage，探针为 source-only 诊断，不构成 leaderboard 证据。",
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    veckit = PROJECT_ROOT / "third_party/veckit"
    payload: dict[str, Any] = {"schema": "ve.t2.m1-gates.v1", "date": "2026-09-27"}
    for name, fn in (("A", gate_a), ("B", gate_b)):
        print(f"--- gate {name} ---", flush=True)
        t = time.time()
        try:
            payload[f"gate_{name}"] = fn(veckit) if name == "A" else fn()
        except Exception as exc:  # 记录原因，不静默跳过
            payload[f"gate_{name}"] = {"gate": name, "status": "ERROR", "error": repr(exc)}
        print(f"    done in {time.time() - t:.1f}s", flush=True)
    (OUT_DIR / "gates.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for name in ("A", "B"):
        g = payload[f"gate_{name}"]
        print(f"\n=== GATE {name} ===", flush=True)
        print(json.dumps(g.get("verdict", g), indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
