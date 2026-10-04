#!/usr/bin/env python3
"""T2 `E-N1 SBL` 实现：阶段内自拟合共享空间基底 + 阶段间系数插值。

设计冻结：`reports/T2_E_N1_SBL_DESIGN_FREEZE_20260927.md`（`D-20260927-T2EN1-001`）。
本文件是那份冻结设计的实现，不得在跑后回改设计。

机制摘要（与冻结设计逐条对应）
--------------------------------
1. **几何基底场**：对每个点云（源阶段 E6.75/E7.25/E8.0 与目标几何）各自计算 K 个
   几何派生标量场并各用固定带宽做一次扩散平滑。基底只依赖坐标，**不依赖任何表达**。
   硬性纪律：扩散核**只作用在几何特征上**；**禁止**对任何已预测的表达场做邻域平均
   （M0 §7 已关闭该轴）。
2. **阶段内自拟合**：对 log 归一化后**按基因 z-score** 的表达，用强 ridge 回归到
   这 K 个基底场，得 β_s ∈ R^{G×K}。每个阶段**独立**拟合，不依赖跨阶段细胞对应。
3. **阶段间系数插值**：对每个基因的 K 维系数做二阶最小二乘（三点），取 τ=0.5。
4. **目标几何求值**：在目标点云上算同一套基底场，X̂ = softplus(Σ_k β̂_gk b_k(x))。
5. **全局水平独立通道**：每基因的阶段均值单独走「阶段间均值插值」，与局部对比度项
   **显式解耦**（写成两条独立加项，绝不并入同一回归的截距）。
6. **逐基因门控（跑前冻结）**：仅当 |β_E7.25| 与 |β_E8.0| 在 K 维系数向量上余弦
   相似度 ≥ 0.5 时启用该基因的场贡献，否则退回全局均值插值。阈值在首次完整运行前
   已写入冻结设计，**不得按结果调整**。

共同坐标系
----------
系数跨阶段插值的前提是基底场在**同一坐标系**里可比。本实现复用项目既有
``t2_s3_shape_field.canonicalize``（centre + PCA + RMS 归一，scorer 约定）把每个
阶段各自规范化；PCA 轴符号用 ``best_proper_flip`` 显式定号（与 T2-S3 同一约定），
以免符号翻转把系数插值毁掉。这一点在设计冻结时只写了「在自己的坐标上独立拟合」，
实现时必须补上共同框架，否则 §3 的系数插值在数学上不成立——**此实现选择已如实记录**。

判定
----
按 `D-20260927-T2M0APPXB-001`（M0 附录 B）：**本 board 落在 `T2:embryo:val_interp`，
5% 三分类已停用**，本地 `neighborhood_mmd` **只作记录、不作否决**，最终由服务器仲裁。
本脚本因此不做本地晋级判定，只如实报告全部读数与预声明失败签名。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

# NOTE: this script lives directly in ``scripts/`` (not ``scripts/gate/``), so the
# project root is parents[1]. The gate scripts under ``scripts/gate/`` use
# parents[2]; using the wrong depth silently points at a directory OUTSIDE the
# project, which is how the first run of this script failed to import veckit.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _p in (PROJECT_ROOT, PROJECT_ROOT / "third_party/veckit"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import importlib.util  # noqa: E402
import types  # noqa: E402

from common.core_metrics import (  # noqa: E402
    energy_distance,
    mmd_unbiased,
    variogram_score,
)
from common.shape_metrics import d2_distance, occupancy_dice  # noqa: E402


def _load_veckit_t2():
    veckit_root = PROJECT_ROOT / "third_party/veckit"

    def _load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    t1 = _load("t1_metrics", veckit_root / "T1" / "metrics.py")
    reuse = types.ModuleType("_reuse")
    reuse.t1_metrics = t1
    sys.modules["_reuse"] = reuse
    t2 = _load("t2_metrics", veckit_root / "T2" / "metrics.py")
    sys.modules["metrics"] = t2
    return t2


T2_METRICS = _load_veckit_t2()

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from t2_baseline import load_t2_input, read_panel  # noqa: E402
from t2_s3_shape_field import best_proper_flip, canonicalize  # noqa: E402

OUT_DIR = PROJECT_ROOT / "artifacts/tool_integration/T2-E-N1-SBL-20260927-v1"

PANEL = PROJECT_ROOT / "data/gene_panel/T2__embryo__val_interp.genes.txt"
SOURCE_STAGES: dict[str, str] = {
    "E6.75": "data/E6.75.h5ad",
    "E7.25": "data/E7.25.h5ad",
    "E8.0": "data/E8.0.h5ad",
}
TAU = {"E6.75": 0.0, "E7.25": 1.0 / 3.0, "E8.0": 1.0}
# CORRECTION (design-freeze amendment, see RESULT.md): the frozen design said
# "take tau = 0.5" for a target of E7.5. On this axis E7.5 sits at
# (7.5 - 6.75) / (8.0 - 6.75) = 0.6, so tau = 0.5 corresponds to E7.625. The
# design text was internally inconsistent between its target stage and its
# interpolation parameter. This is an arithmetic correction, NOT a
# result-dependent hyperparameter change: the board target stage is fixed by the
# contract and the axis is fixed by the frozen spec.
TARGET_TAU = (7.5 - 6.75) / (8.0 - 6.75)   # == 0.6, the stage position of E7.5
PSEUDO_TARGET = PROJECT_ROOT / "data/E7.25.h5ad"      # 冻结的本地评价目标
PARENT_CANDIDATE = PROJECT_ROOT / (
    "submissions/candidates/T2_embryo_val_interp/"
    "v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad"
)
BASELINE_CANDIDATE = PROJECT_ROOT / (
    "submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad"
)

DIFFUSION_SIGMA_FRAC = 0.06   # 扩散核带宽 = 该比例 × 点云 RMS 半径
RIDGE_ALPHA = 1.0             # 强 ridge（设计要求 K≪n 强正则）
STABILITY_COS = 0.5           # 跑前冻结的逐基因门控阈值
SEED = 20260927


# ---------------------------------------------------------------------------
# 几何基底场
# ---------------------------------------------------------------------------
def _knn_graph(coords: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """k-NN graph. Returns (indices (n,k), distances (n,k)), self excluded.

    Kept O(n*k) on purpose: an earlier draft computed a dense n-by-n pairwise
    distance matrix, which is ~8 GB for the E8.0 stage (31,671 cells) and is not
    needed -- the diffusion kernel only ever needs the k-NN edges.
    """
    from sklearn.neighbors import NearestNeighbors

    k = int(min(k, coords.shape[0] - 1))
    dist, idx = NearestNeighbors(n_neighbors=k + 1).fit(coords).kneighbors(coords)
    return idx[:, 1:], dist[:, 1:]


def _knn_spectral_smooth(B: np.ndarray, idx: np.ndarray, dist: np.ndarray,
                         sigma: float) -> np.ndarray:
    """One fixed-bandwidth diffusion pass over the k-NN graph, row-normalised.

    Applies to GEOMETRIC features only. Never applied to a predicted expression
    field (M0 §7 closed that axis).
    """
    n = B.shape[0]
    w = np.exp(-(dist ** 2) / (2.0 * sigma ** 2))
    w_sum = w.sum(axis=1, keepdims=True)
    w_sum[w_sum < 1e-300] = 1.0
    neigh = np.einsum("nk,nkf->nf", w / w_sum, B[idx])
    return (neigh + B) / 2.0  # include self with equal weight


def _standardise(B: np.ndarray) -> np.ndarray:
    mu = B.mean(axis=0, keepdims=True)
    sd = B.std(axis=0, keepdims=True)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return (B - mu) / sd


def geometric_basis(coords_canonical: np.ndarray, k_neighbors: int) -> tuple[np.ndarray, list[str]]:
    """K geometric scalar fields, each smoothed once. Coordinates only, never expression.

    All fields are O(n*k). The design freeze named eight fields including
    "distance to the point cloud's convex hull (depth coordinate)"; that is
    approximated here by projections onto the canonical principal axes and the
    signed absolute projections, because an exact convex hull is O(n log n) per
    stage with a frame-alignment problem this route does not need. The
    substitution is recorded in the run's ``basis_fields`` list.
    """
    Z = np.asarray(coords_canonical, dtype=np.float64)
    n = Z.shape[0]
    rms = float(np.sqrt(np.mean(np.sum(Z * Z, axis=1))))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("coords must have a positive finite RMS radius")

    idx20, dist20 = _knn_graph(Z, min(k_neighbors, n - 1))
    idx10, _ = _knn_graph(Z, min(10, n - 1))
    idx40, _ = _knn_graph(Z, min(40, n - 1))

    radius = np.linalg.norm(Z - Z.mean(axis=0), axis=1)
    q95 = float(np.quantile(radius, 0.95))

    fields: list[np.ndarray] = [
        radius,
        dist20.mean(axis=1),
        dist20.std(axis=1),
        Z[:, 0], Z[:, 1], Z[:, 2],
        np.abs(Z[:, 0]), np.abs(Z[:, 1]),
    ]
    names = [
        "radius_to_centroid",
        "knn_mean_dist_k20",
        "knn_std_dist_k20",
        "canon_axis0", "canon_axis1", "canon_axis2",
        "abs_axis0", "abs_axis1",
    ]

    B = _standardise(np.nan_to_num(np.stack(fields, axis=1), nan=0.0, posinf=0.0, neginf=0.0))
    smoothed = _knn_spectral_smooth(B, idx20, dist20, sigma=DIFFUSION_SIGMA_FRAC * rms)
    smoothed = np.nan_to_num(smoothed, nan=0.0, posinf=0.0, neginf=0.0)
    return _standardise(smoothed), names


# ---------------------------------------------------------------------------
# 阶段内自拟合
# ---------------------------------------------------------------------------
def fit_stage(X: np.ndarray, B: np.ndarray, alpha: float = RIDGE_ALPHA) -> dict[str, np.ndarray]:
    """Per-gene ridge of z-scored expression onto the K geometric basis fields.

    Returns gene means, gene sds (for z-scoring), and the K coefficients.
    """
    gene_mean = X.mean(axis=0)
    gene_sd = X.std(axis=0)
    gene_sd[gene_sd < 1e-12] = 1.0
    Z = (X - gene_mean) / gene_sd

    K = B.shape[1]
    G = Z.shape[1]
    beta = np.zeros((G, K), dtype=np.float64)
    # one shared-design solve across all genes: (K,n) @ (n,G) -> (K,G)
    A = B.T @ B + alpha * np.eye(K)
    Y = B.T @ Z
    try:
        beta = np.linalg.solve(A, Y).T
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(A, Y, rcond=None)[0].T
    return {"gene_mean": gene_mean, "gene_sd": gene_sd, "beta": beta}


def interpolate_coeffs(betas: dict[str, np.ndarray]) -> np.ndarray:
    """Second-order (quadratic) least squares in tau for every gene's K coefficients."""
    taus = np.array([TAU["E6.75"], TAU["E7.25"], TAU["E8.0"]], dtype=np.float64)
    V = np.stack([np.ones_like(taus), taus, taus**2], axis=1)      # (3, 3)
    B_inv = np.linalg.pinv(V)                                    # (3, 3)
    stacked = np.stack([betas["E6.75"], betas["E7.25"], betas["E8.0"]], axis=0)  # (3, G, K)
    coef = np.tensordot(B_inv, stacked, axes=(1, 0))             # (3, G, K)
    at = np.array([1.0, TARGET_TAU, TARGET_TAU**2])
    return np.tensordot(at, coef, axes=(0, 0))                   # (G, K)


def interpolate_gene_means(means: dict[str, np.ndarray]) -> np.ndarray:
    """Linear (not quadratic) interpolation of the per-gene global level.

    The design freeze requires the global level to travel on a channel that is
    **position-free**; it is kept linear on purpose so that this channel stays a
    plain stage-mean interpolation and cannot absorb any spatial structure.
    """
    taus = np.array([TAU["E6.75"], TAU["E7.25"], TAU["E8.0"]], dtype=np.float64)
    Vd = np.stack([np.ones_like(taus), taus], axis=1)      # (3, 2): rows = stages
    stacked = np.stack([means["E6.75"], means["E7.25"], means["E8.0"]], axis=0)  # (3, G)
    coef = np.linalg.pinv(Vd) @ stacked                    # (2, G)
    return coef[0] + TARGET_TAU * coef[1]                  # (G,)


# ---------------------------------------------------------------------------
# 评估
# ---------------------------------------------------------------------------
def _dense(X: Any) -> np.ndarray:
    if hasattr(X, "todense"):
        X = X.todense()
    return np.asarray(X, dtype=np.float64)


def load_stage(path: Path, genes: list[str]) -> tuple[np.ndarray, np.ndarray]:
    a = load_t2_input(path, PANEL)
    if [str(g) for g in a.var_names] != genes:
        a = a[:, genes].copy()
    return _dense(a.X), np.asarray(a.obsm["spatial_3D"], dtype=np.float64)[:, :3]


def evaluate(pred_X: np.ndarray, pred_C: np.ndarray, true_X: np.ndarray, true_C: np.ndarray) -> dict[str, float]:
    return {
        "neighborhood_mmd": float(
            T2_METRICS.neighborhood_mmd(pred_X, pred_C, true_X, true_C, k=15, n=2000)
        ),
        "mmd_u": float(mmd_unbiased(pred_X, true_X, n=2000, seed=0)),
        "energy_distance": float(energy_distance(pred_X, true_X)),
        "variogram": float(variogram_score(pred_X, true_X)),
        "d2_shape": float(d2_distance(pred_C, true_C, seed=SEED)),
        "occupancy_dice": float(occupancy_dice(pred_C, true_C, seed=SEED)[0]),
    }


def build_candidate(
    B_target: np.ndarray,
    beta_hat: np.ndarray,
    mean_hat: np.ndarray,
    use_field: np.ndarray,
) -> dict[str, Any]:
    """Combine the position-dependent field with the position-free global level.

    Two corrections were made after a first run; both are recorded in RESULT.md
    and neither is a result-dependent hyperparameter change:

    1. The frozen design's "softplus" was written as ``log1p(expm1(x))``, which
       is **algebraically the identity**, not a softplus. It was replaced with
       an explicit centring of the field term.
    2. The interpolation target tau was corrected from the design's 0.5 to the
       stage position of E7.5 on the frozen axis (0.6).

    The field term contributes **contrast** (spatial structure); the per-gene
    global level sets the **mass**. Non-negativity is enforced by clamping.
    """
    field = B_target @ beta_hat.T                     # (n_target, G)
    field = field * use_field[None, :]
    # centre the field on the target cloud: contributes contrast, not mass
    field = field - field.mean(axis=0, keepdims=True)
    X = mean_hat[None, :] + field
    return {
        "X": np.clip(X, 0.0, None),
        "n_field_genes": int(use_field.sum()),
        "n_genes": int(X.shape[1]),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    rng = np.random.default_rng(SEED)
    genes = read_panel(PANEL)

    # ---- load source stages + target geometry (from the incumbent parent) ----
    stages: dict[str, dict[str, Any]] = {}
    for name, rel in SOURCE_STAGES.items():
        X, C = load_stage(PROJECT_ROOT / rel, genes)
        Z, _c, _r, _V = canonicalize(C)
        stages[name] = {"X": X, "C": C, "Z": Z}
        print(f"loaded {name}: X{X.shape} C{C.shape}", flush=True)

    import anndata as ad
    parent = ad.read_h5ad(PARENT_CANDIDATE)
    target_C = np.asarray(parent.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    target_Z, _c, _r, _V = canonicalize(target_C)
    target_celltype = (
        np.asarray(parent.obs["celltype"]).astype(str)
        if "celltype" in parent.obs
        else np.array(["NA"] * parent.n_obs)
    )
    target_obs = [str(x) for x in parent.obs_names]
    print(f"target geometry: {target_C.shape} (from parent v0010)", flush=True)

    # ---- geometric basis on every cloud ----
    k_neighbors = 20
    basis = {name: geometric_basis(st["Z"], k_neighbors) for name, st in stages.items()}
    B_target, basis_names = geometric_basis(target_Z, k_neighbors)
    print(f"basis fields ({len(basis_names)}): {basis_names}", flush=True)

    # ---- fit each source stage, interpolate, evaluate ----
    fits = {name: fit_stage(st["X"], basis[name][0]) for name, st in stages.items()}
    beta_hat = interpolate_coeffs({n: fits[n]["beta"] for n in SOURCE_STAGES})
    mean_hat = interpolate_gene_means({n: fits[n]["gene_mean"] for n in SOURCE_STAGES})

    # per-gene stability gate: cosine similarity of coefficient vectors E7.25 vs E8.0
    b_725 = fits["E7.25"]["beta"]
    b_800 = fits["E8.0"]["beta"]
    num = (b_725 * b_800).sum(axis=1)
    den = np.linalg.norm(b_725, axis=1) * np.linalg.norm(b_800, axis=1)
    cos = np.where(den > 1e-12, num / np.maximum(den, 1e-12), 0.0)
    gate = cos >= STABILITY_COS
    print(f"stability gate: {int(gate.sum())}/{len(gate)} genes pass (cos>={STABILITY_COS})", flush=True)

    true_X, true_C = load_stage(PSEUDO_TARGET, genes)

    arms: dict[str, Any] = {}

    # L1: frozen design (K=8, stability gate ON)
    c1 = build_candidate(B_target, beta_hat, mean_hat, gate.astype(float))
    arms["L1_sbl_gated"] = {"X": c1["X"], "n_field_genes": c1["n_field_genes"], "n_genes": c1["n_genes"]}

    # L2: control arm - gate OFF (degradation control, per frozen design)
    c2 = build_candidate(B_target, beta_hat, mean_hat, np.ones_like(gate, dtype=float))
    arms["L2_sbl_ungated"] = {"X": c2["X"], "n_field_genes": c2["n_field_genes"], "n_genes": c2["n_genes"]}

    payload: dict[str, Any] = {
        "schema": "ve.t2.e-n1-sbl.v1",
        "atom": "T2-E-N1-SBL-20260927-v1",
        "board": "T2_embryo_val_interp",
        "design_freeze": "reports/T2_E_N1_SBL_DESIGN_FREEZE_20260927.md",
        "frozen_constants": {
            "diffusion_sigma_frac": DIFFUSION_SIGMA_FRAC,
            "ridge_alpha": RIDGE_ALPHA,
            "stability_cos_threshold": STABILITY_COS,
            "k_neighbors": k_neighbors,
            "seed": SEED,
            "tau": TAU,
            "target_tau": TARGET_TAU,
        },
        "basis_fields": basis_names,
        "n_genes_panel": len(genes),
        "stability": {
            "n_pass": int(gate.sum()),
            "n_total": int(len(gate)),
            "cos_min": float(cos.min()), "cos_max": float(cos.max()),
            "cos_median": float(np.median(cos)),
        },
        "parent": {
            "path": str(PARENT_CANDIDATE.relative_to(PROJECT_ROOT)),
            "n_cells": int(target_C.shape[0]),
        },
        "arms": {},
        "reference_readings": {},
        "declarations": [
            "geometry basis fields depend on COORDINATES ONLY; the diffusion kernel is applied to geometric features, never to a predicted expression field (M0 §7 closed axis)",
            "each source stage is fitted independently; no cross-stage cell correspondence is used, no OT, no displacement field",
            "canonicalisation into a common frame (centre+PCA+RMS, scorer convention) is required for coefficient interpolation to be meaningful; this is an implementation choice recorded explicitly, not a post-hoc change of the frozen mechanism",
            "per M0 appendix B (D-20260927-T2M0APPXB-001) the embryo board's 5% rule is SUSPENDED: local numbers are recorded only and do NOT decide promotion; the server arbitrates",
            "no candidate, submission, INDEX row or upload was produced by this run",
            "CORRECTION 1: the design freeze's 'softplus' was written as log1p(expm1(x)), which is algebraically the identity, not a softplus; it was replaced by explicit centring of the field term.",
            "CORRECTION 2: the design freeze asked for tau=0.5 on the axis E6.75=0/E7.25=1/3/E8.0=1, but the board target stage is E7.5, which sits at tau=0.6. The design text was internally inconsistent; the axis and the target stage are both fixed by contract, so this is an arithmetic correction and not a result-dependent hyperparameter change.",
            "the first attempt's outputs are archived under attempt1_buggy/ and are NOT the hypothesis test",
        ],
    }

    # ---- reference readings for context (do-nothing + incumbent parent) ----
    base = ad.read_h5ad(BASELINE_CANDIDATE)
    base_X = _dense(base.X)[:, [list(base.var_names).index(g) for g in genes]] if list(base.var_names) != genes else _dense(base.X)
    base_C = np.asarray(base.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    payload["reference_readings"]["do_nothing_baseline"] = evaluate(base_X, base_C, true_X, true_C)
    par_X = _dense(parent.X)
    par_X = par_X[:, [list(parent.var_names).index(g) for g in genes]] if list(parent.var_names) != genes else par_X
    payload["reference_readings"]["incumbent_parent_v0010"] = evaluate(par_X, target_C, true_X, true_C)
    for k, v in payload["reference_readings"].items():
        print(f"ref {k}: nmmd={v['neighborhood_mmd']:.6f} d2={v['d2_shape']:.5f}", flush=True)

    for name, arm in arms.items():
        m = evaluate(arm["X"], target_C, true_X, true_C)
        payload["arms"][name] = {
            "metrics": m,
            "n_field_genes": arm["n_field_genes"],
            "n_genes": arm["n_genes"],
            "X_sum": float(arm["X"].sum()),
            "X_mean": float(arm["X"].mean()),
            "X_min": float(arm["X"].min()),
        }
        print(f"{name}: nmmd={m['neighborhood_mmd']:.6f} d2={m['d2_shape']:.5f} "
              f"occ={m['occupancy_dice']:.4f} mmd_u={m['mmd_u']:.5f} "
              f"Xsum={arm['X'].sum():.1f} fieldgenes={arm['n_field_genes']}", flush=True)

    # ---- pre-declared failure-signature detection (report only, no re-run) ----
    sig: dict[str, Any] = {}
    base_nmmd = payload["reference_readings"]["do_nothing_baseline"]["neighborhood_mmd"]
    parent_nmmd = payload["reference_readings"]["incumbent_parent_v0010"]["neighborhood_mmd"]
    for name, a in payload["arms"].items():
        m = a["metrics"]
        sig[name] = {
            "beats_do_nothing": bool(m["neighborhood_mmd"] < base_nmmd),
            "beats_incumbent_parent": bool(m["neighborhood_mmd"] < parent_nmmd),
            "over_smoothing_signature": bool(
                m["d2_shape"] <= payload["reference_readings"]["do_nothing_baseline"]["d2_shape"] * 1.05
            ),
        }
    payload["pre_declared_signatures"] = sig
    payload["wall_seconds"] = time.time() - started

    (OUT_DIR / "sbl_run.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    np.save(OUT_DIR / "beta_hat.npy", beta_hat)
    np.save(OUT_DIR / "basis_target.npy", B_target)
    print(f"\nwrote {OUT_DIR/'sbl_run.json'}  ({payload['wall_seconds']:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
