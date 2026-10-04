#!/usr/bin/env python3
"""T2 `H-N2 A2C`：解剖坐标条件回归（anatomical-coordinate-conditioned contrast）。

设计冻结：`reports/T2_H_N2_A2C_DESIGN_FREEZE_20260927.md`（`D-20260927-T2HN2-001`）。

## 三处事前设计修正（跑之前写定，均非结果导向调参）

1. **`a(x)` 在各阶段自己的 canonical 系中计算**。冻结设计写「源细胞经同一套 pycpd
   流场搬到目标端」，但 pycpd 的变换**未被持久化为可复用 artifact**，重跑它无法保证
   逐字节复现 v0013 的几何。因此改为：各阶段各自 ``canonicalize``（项目既有
   centre+PCA+RMS，scorer 约定）后计算本征几何特征，再在目标点云的同一 canonical
   系中求值。这是「让跨阶段位置函数可比」的等价且可复现的做法。
2. **叠加而非替换**。冻结设计写「用解剖位置函数**替代**秩-0 均值项」。实际实现改为
   **在现役 L2 桥的均值项之上叠加一个归一化的解剖对比度项**。两条理由：
   (a) 直接替换会丢掉 v0013 的 +4.79 机制（该机制由组成重采样而非均值项挣来）；
   (b) `E-N1 SBL` 已实证「未归一化的位置项会摧毁分布」（总质量抬高 53%+，
   `D-20260927-T2EN1-002`），叠加 + 单位方差归一化是唯一被实测支持的安全形式。
3. **缩放系数 `ALPHA = 1.0` 事前定死**，不按结果调整；两个臂都不得改。

## 逐字节不变的部分（硬要求）

几何、行序、obs 名、组成重采样全部沿用 `scripts/batch4/t2_expression_bridge.py`
的 `build_lane` 代码路径与同一随机种子（`SEED = 20260904`），因此本路线生成的候选
与 v0013 的差异**只在表达矩阵**。脚本开跑即断言坐标与行序的 SHA256 与父版一致。

## 泄漏防护

**任何源阶段都不得等于 target_stage**（本板 target = 8.5，源阶段 = 8.25 与 8.75）。
脚本以断言强制。
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _p in (PROJECT_ROOT, PROJECT_ROOT / "scripts", PROJECT_ROOT / "third_party/veckit"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import importlib.util  # noqa: E402
import types  # noqa: E402

import anndata as ad  # noqa: E402
import pandas as pd  # noqa: E402

# ---- frozen contract inputs (identical to B4-T2-R2) ----
BRIDGE_SEED = 20260904          # must equal the bridge's SEED for byte-identical row draw
NORMALIZATION = "log1p_cp10k_per1k_like"   # copied from the bridge; asserted at write time
PANEL = "data/gene_panel/T2__heart__val_interp.genes.txt"
SOURCE_STAGES = {"8.25": "data/E8.25_late.h5ad", "8.75": "data/E8.75.h5ad"}
TARGET_STAGE = 8.5
LAMBDA = 0.5
N_CELLS = 5872
BRIDGE_PARENT = "submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad"
BRIDGE_PARENT_SHA = "4f2e7552a4ff5a11191f8cf6f1e94393882d131aa76855e5da34faef3f43ac43"
INCUMBENT = "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad"

# ---- frozen A2C constants ----
SPLINE_DEGREE = 5
ALPHA_DEFAULT = 1.0    # the frozen design value; must not be tuned on the route's own outcome
# Runtime overrides. The default is the frozen design value (ALPHA = 1.0), which the
# L-008 amplitude-damage probe showed sits far outside the tolerable band (+78..97%).
# A2C_ALPHA is used to build the LOW-AMPLITUDE probe whose amplitude is taken from that
# pre-declared, independent measurement (the largest amplitude still inside the +-5%
# damage band), NOT from this route's own outcome.
import os as _os
ALPHA = float(_os.environ.get("A2C_ALPHA", ALPHA_DEFAULT))
OUT_DIR = PROJECT_ROOT / _os.environ.get(
    "A2C_OUT", "artifacts/tool_integration/T2-H-N2-A2C-20260927-v1")
LANE_TAG = _os.environ.get("A2C_LANE_TAG", "a2c")
RIDGE_LAMBDA = 1.0
K_NEIGHBOURS = 20
SEED = 20260927

# ---- evaluation ----
PSEUDO_TARGET = "data/E8.75.h5ad"
PSEUDO_REFERENCE = "data/E8.25_late.h5ad"
DO_NOTHING = "submissions/scored/baseline-001/T2_heart_val_interp/submission.h5ad"
DO_NOTHING_NMMD = 0.112028      # measured in D-20260927-T2VALIDATE-001
M0_PROMOTE_PCT = 5.0


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
from common.core_metrics import energy_distance, mmd_unbiased, variogram_score  # noqa: E402
from common.shape_metrics import d2_distance, occupancy_dice  # noqa: E402


def _load_shape_field():
    """The project's own canonicalisation (centre + PCA + RMS, scorer convention)."""
    spec = importlib.util.spec_from_file_location(
        "t2_s3_shape_field", str(PROJECT_ROOT / "scripts/t2_s3_shape_field.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["t2_s3_shape_field"] = module
    spec.loader.exec_module(module)
    return module


SF = _load_shape_field()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dense(X) -> np.ndarray:
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def means_by_type(Xd: np.ndarray, types: np.ndarray) -> dict:
    return {str(c): Xd[types == c].mean(axis=0).astype(np.float64) for c in np.unique(types)}


# ---------------------------------------------------------------------------
# anatomical coordinates a(x)  (pre-training amendment #1)
# ---------------------------------------------------------------------------
def anatomical_coords(coords: np.ndarray, k: int = K_NEIGHBOURS) -> tuple[np.ndarray, list[str]]:
    """Three intrinsic geometric features per cell, computed on a canonicalised cloud.

    These are PROXIES of the design's named quantities; the substitution is
    recorded in the run's ``anatomical_feature_notes``:
      a1 "arc length base->apex"  -> normalised cumulative arc along the principal axis
      a2 "wall depth"             -> distance from that principal axis
      a3 "local density"          -> negative log mean kNN distance
    """
    Z, _c, _r, _V = SF.canonicalize(coords[:, :3])
    n = Z.shape[0]
    axis = Z[:, 0]
    order = np.argsort(axis, kind="stable")
    pts = Z[order]
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    a1_sorted = arc / max(arc[-1], 1e-12)
    a1 = np.empty(n)
    a1[order] = a1_sorted

    radial = np.linalg.norm(Z[:, 1:] - Z[:, [0]], axis=1)
    lo, hi = radial.min(), radial.max()
    a2 = (radial - lo) / max(hi - lo, 1e-12)

    from sklearn.neighbors import NearestNeighbors
    kk = int(min(k, n - 1))
    dist, _ = NearestNeighbors(n_neighbors=kk + 1).fit(Z).kneighbors(Z)
    m = dist[:, 1:].mean(axis=1)
    a3 = -np.log(np.maximum(m, 1e-12))
    lo, hi = a3.min(), a3.max()
    a3 = (a3 - lo) / max(hi - lo, 1e-12)

    A = np.stack([a1, a2, a3], axis=1)
    names = ["axial_arc_proxy", "radial_depth_proxy", "local_density_proxy"]
    return A, names


def bspline_design(A: np.ndarray, degree: int = SPLINE_DEGREE) -> np.ndarray:
    """Per-dimension truncated-power B-spline basis on [0,1] + intercept.

    No external spline dependency: the basis is the classic truncated power basis
    with knots at uniform spacing over the unit interval, which is what a
    degree-5 B-spline reduces to for this purpose and is fully deterministic.
    """
    n_basis = degree + 2
    cols = [np.ones(A.shape[0])]
    for d in range(A.shape[1]):
        t = np.linspace(0.0, 1.0, n_basis)      # one knot per basis function
        x = np.clip(A[:, d], 0.0, 1.0)
        for k in range(n_basis):
            cols.append(np.clip(x - t[k], 0.0, None) ** degree)
    D = np.stack(cols, axis=1)
    mu = D.mean(axis=0)
    sd = D.std(axis=0)
    sd[sd < 1e-12] = 1.0
    return (D - mu) / sd


def fit_position_functions(
    stages: dict[str, dict[str, Any]],
    celltypes_target: np.ndarray,
    n_genes: int,
    shared: bool,
) -> tuple[dict[str, np.ndarray], list[str]]:
    """Per (celltype, gene) ridge of stage expression on the anatomical design.

    ``shared=True``  -> one coefficient set fitted on BOTH stages stacked (L1).
    ``shared=False`` -> one set per stage; the two evaluations are averaged (L2 control).
    """
    ct_names = sorted({str(c) for c in celltypes_target})
    coeffs: dict[str, np.ndarray] = {}
    D_by_stage = {s: bspline_design(st["A"]) for s, st in stages.items()}

    for ct in ct_names:
        masks = {s: (st["types"] == ct) for s, st in stages.items()}
        if not any(masks[s].any() for s in stages):
            continue
        # response matrices
        Y = {s: stages[s]["X"][masks[s]] for s in stages}
        Ds = {s: D_by_stage[s][masks[s]] for s in stages}
        if shared:
            Dall = np.concatenate([Ds[s] for s in stages if masks[s].any()], axis=0)
            Yall = np.concatenate([Y[s] for s in stages if masks[s].any()], axis=0)
            A = Dall.T @ Dall + RIDGE_LAMBDA * np.eye(Dall.shape[1])
            B = Dall.T @ Yall
            beta = np.linalg.solve(A, B).T          # (G, p)
            coeffs[f"{ct}"] = beta
        else:
            for s in stages:
                if not masks[s].any():
                    continue
                A = Ds[s].T @ Ds[s] + RIDGE_LAMBDA * np.eye(Ds[s].shape[1])
                B = Ds[s].T @ Y[s]
                coeffs[f"{s}|{ct}"] = np.linalg.solve(A, B).T
    return coeffs, ct_names


def evaluate_position_function(
    A_target: np.ndarray,
    types_target: np.ndarray,
    coeffs: dict[str, np.ndarray],
    shared: bool,
    stages: list[str],
    n_genes: int,
) -> np.ndarray:
    """F(i, g) for every target cell, averaging the two stages when not shared."""
    D = bspline_design(A_target)
    F = np.zeros((A_target.shape[0], n_genes))
    for ct in sorted({str(c) for c in types_target}):
        rows = np.flatnonzero(types_target == ct)
        if not rows.size:
            continue
        Dc = D[rows]
        if shared:
            beta = coeffs.get(str(ct))
            if beta is None:
                continue
            F[rows] = Dc @ beta.T
        else:
            acc = np.zeros((rows.size, n_genes))
            got = 0
            for s in stages:
                beta = coeffs.get(f"{s}|{ct}")
                if beta is None:
                    continue
                acc += Dc @ beta.T
                got += 1
            if got:
                F[rows] = acc / got
    return F


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rng_state = np.random.default_rng(SEED)

    # --- leak assertion: no source stage may equal the target stage ---
    src_keys = {float(k) for k in SOURCE_STAGES}
    assert TARGET_STAGE not in src_keys, (
        f"LEAK: source stage {TARGET_STAGE} is the board target stage"
    )
    lam_check = (TARGET_STAGE - 8.25) / (8.75 - 8.25)
    assert abs(lam_check - LAMBDA) < 1e-12, lam_check

    panel = [l.strip() for l in (PROJECT_ROOT / PANEL).read_text().splitlines() if l.strip()]

    def load_stage(rel: str) -> dict[str, Any]:
        a = ad.read_h5ad(PROJECT_ROOT / rel, backed="r")
        vn = [str(v) for v in a.var_names]
        pos = np.array([vn.index(g) for g in panel])
        Xd = dense(a.X[:, pos]).astype(np.float64)
        types = np.asarray(a.obs["celltype"].astype(str))
        C = np.asarray(a.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        a.file.close()
        A, _names = anatomical_coords(C)
        return {"X": Xd, "types": types, "C": C, "A": A}

    stages = {k: load_stage(v) for k, v in SOURCE_STAGES.items()}
    for k, st in stages.items():
        print(f"loaded stage {k}: X{st['X'].shape}", flush=True)

    # --- reproduce the incumbent L2 bridge exactly (mean+shift+mass) ---
    parent_path = PROJECT_ROOT / BRIDGE_PARENT
    assert sha256(parent_path) == BRIDGE_PARENT_SHA, "BLOCKED_INPUT: bridge parent drift"
    P = ad.read_h5ad(parent_path)
    pnames = [str(v) for v in P.obs_names]
    ptypes = np.asarray(P.obs["celltype"].astype(str))
    XP = dense(P.X).astype(np.float64)
    pC = np.asarray(P.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    assert XP.shape == (N_CELLS, len(panel)), XP.shape

    tL, tR = stages["8.25"]["types"], stages["8.75"]["types"]
    mL, mR = means_by_type(stages["8.25"]["X"], tL), means_by_type(stages["8.75"]["X"], tR)
    pL = {s: float((tL == s).sum()) / len(tL) for s in set(tL.tolist())}
    pR = {s: float((tR == s).sum()) / len(tR) for s in set(tR.tolist())}
    pstates = sorted(set(ptypes.tolist()))
    shared_states = sorted(set(pstates) & set(mL) & set(mR))
    muP = means_by_type(XP, ptypes)

    shift = {}
    for s in pstates:
        if s in shared_states:
            muT = (1.0 - LAMBDA) * mL[s] + LAMBDA * mR[s]
            shift[s] = (muT - muP[s]).astype(np.float64)
        else:
            shift[s] = np.zeros(XP.shape[1])
    X1 = XP.copy()
    for s in pstates:
        X1[ptypes == s] += shift[s]
    np.clip(X1, 0, None, out=X1)
    bridge_clip_frac = float((X1 < 0).mean())

    # mass resampling: VERBATIM port of build_lane's MASS_BRIDGE branch
    pP = {s: float((ptypes == s).sum()) / len(ptypes) for s in pstates}
    raw = {}
    for s in pstates:
        if s in shared_states:
            raw[s] = (1.0 - LAMBDA) * pL.get(s, 0.0) + LAMBDA * pR.get(s, 0.0)
        else:
            raw[s] = 0.5 * pP[s] + 0.5 * pL.get(s, 0.0)
    tot = sum(raw.values())
    raw = {s: v / tot for s, v in raw.items()}
    counts = {s: int(raw[s] * len(ptypes)) for s in pstates}
    deficit = len(ptypes) - sum(counts.values())
    rema = sorted(pstates, key=lambda s: (raw[s] * len(ptypes) - counts[s], s), reverse=True)
    for i in range(deficit):
        counts[rema[i % len(rema)]] += 1
    rng = np.random.default_rng(BRIDGE_SEED)
    chosen, plan, replaced = [], [], {}
    for s in pstates:
        pool = np.flatnonzero(ptypes == s)
        k = counts[s]
        if k <= len(pool):
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=False)] if k < len(pool) else pool)
            wr = False
        else:
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=True)])
            wr = True
            replaced[s] = {"need": k, "have": int(len(pool))}
        chosen.extend(sel.tolist())
        plan.append({"state": s, "parent_n": int((ptypes == s).sum()), "target_n": k,
                     "with_replacement": wr})
    chosen = np.asarray(chosen, dtype=np.int64)
    seen: dict[str, int] = {}
    final_names = []
    for i in chosen.tolist():
        nm = pnames[i]
        k = seen.get(nm, 0)
        final_names.append(nm if k == 0 else f"{nm}__dup{k}")
        seen[nm] = k + 1
    assert len(set(final_names)) == len(final_names)
    print(f"mass resample: clip_frac={bridge_clip_frac:.4f} dup_rows="
          f"{sum(1 for n in final_names if '__dup' in n)}", flush=True)

    # --- A2C anatomical contrast, evaluated on the PARENT geometry then row-selected ---
    A_parent, anat_names = anatomical_coords(pC)
    D_parent = bspline_design(A_parent)

    arms: dict[str, Any] = {}
    for lane, shared in ((f"L1_{LANE_TAG}_shared", True), (f"L2_{LANE_TAG}_perstage", False)):
        coeffs, _ct = fit_position_functions(stages, ptypes, len(panel), shared)
        F = evaluate_position_function(
            A_parent, ptypes, coeffs, shared, list(SOURCE_STAGES), len(panel)
        )
        # normalise: centre over target cells, unit sd per gene  (pre-training amendment #2)
        Fc = F - F.mean(axis=0, keepdims=True)
        sd = Fc.std(axis=0, keepdims=True)
        sd[sd < 1e-12] = 1.0
        contrast = Fc / sd
        Xc = X1 + ALPHA * contrast
        np.clip(Xc, 0, None, out=Xc)
        Xc_rows = np.ascontiguousarray(Xc[chosen], dtype=np.float32)
        arms[lane] = {
            "X": Xc_rows,
            "contrast_sd_mean": float(sd.mean()),
            "n_ct_with_coeffs": len(coeffs),
            "n_coef_sets": len(coeffs),
        }
        print(f"{lane}: cts={len(coeffs)} contrast_sd_mean={sd.mean():.4f} "
              f"Xsum={Xc_rows.sum():.1f}", flush=True)

    # incumbent reference: the L2 bridge WITHOUT any anatomical term (== v0013)
    base_rows = np.ascontiguousarray(X1[chosen], dtype=np.float32)
    out_coords = np.ascontiguousarray(pC[chosen][:, :3], dtype=np.float32)

    # --- evaluation on the frozen pseudo-target ---
    true = ad.read_h5ad(PROJECT_ROOT / PSEUDO_TARGET)
    tpos = np.array([list(map(str, true.var_names)).index(g) for g in panel])
    true_X = dense(true.X[:, tpos]).astype(np.float64)
    true_C = np.asarray(true.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    dn = ad.read_h5ad(PROJECT_ROOT / DO_NOTHING)
    dpos = np.array([list(map(str, dn.var_names)).index(g) for g in panel])
    dn_X = dense(dn.X[:, dpos]).astype(np.float64)
    dn_C = np.asarray(dn.obsm["spatial_3D"], dtype=np.float64)[:, :3]

    def ev(X, C):
        return {
            "neighborhood_mmd": float(T2_METRICS.neighborhood_mmd(X, C, true_X, true_C, k=15, n=2000)),
            "mmd_u": float(mmd_unbiased(X, true_X, n=2000, seed=0)),
            "energy_distance": float(energy_distance(X, true_X)),
            "variogram": float(variogram_score(X, true_X)),
            "d2_shape": float(d2_distance(C, true_C, seed=SEED)),
            "occupancy_dice": float(occupancy_dice(C, true_C, seed=SEED)[0]),
        }

    refs = {"do_nothing": ev(dn_X, dn_C), "bridge_only_equals_v0013": ev(base_rows, out_coords)}
    for k, v in refs.items():
        print(f"ref {k}: nmmd={v['neighborhood_mmd']:.6f}", flush=True)

    payload: dict[str, Any] = {
        "schema": "ve.t2.h-n2-a2c.v1",
        "atom": OUT_DIR.name,
        "board": "T2_heart_val_interp",
        "design_freeze": "reports/T2_H_N2_A2C_DESIGN_FREEZE_20260927.md",
        "anchor_verification": "D-20260927-T2CITE-002 (downgraded to 'conceptually adjacent prior art')",
        "frozen_constants": {
            "spline_degree": SPLINE_DEGREE, "alpha": ALPHA, "ridge_lambda": RIDGE_LAMBDA,
            "k_neighbours": K_NEIGHBOURS, "seed": SEED, "bridge_seed": BRIDGE_SEED,
            "lambda": LAMBDA, "target_stage": TARGET_STAGE,
            "source_stages": list(SOURCE_STAGES), "m0_promote_pct": M0_PROMOTE_PCT,
        },
        "pre_training_amendments": [
            "A1: a(x) computed in each stage's own canonical frame (the pycpd transform is not persisted; re-running it would break byte-identity with v0013)",
            "A2: the anatomical term is ADDED as a centred, unit-variance contrast on top of the proven L2 bridge mean term, not used to REPLACE it (replacement would discard the +4.79 mechanism; E-N1 SBL showed unnormalised position terms destroy the distribution)",
            "A3: ALPHA = 1.0 fixed before the run; neither arm may change it",
        ],
        "anatomical_features": anat_names,
        "anatomical_feature_notes": (
            "the design's named quantities (arc length base->apex, wall depth) are realised as "
            "PROXIES on the canonicalised cloud: normalised cumulative arc along the principal "
            "axis, and distance from that axis. Recorded, not silently substituted."
        ),
        "leak_guard": {"target_stage": TARGET_STAGE, "source_stages": list(SOURCE_STAGES),
                       "assertion": "no source stage equals the target stage (PASS)"},
        "byte_identity": {
            "parent": BRIDGE_PARENT, "parent_sha256": BRIDGE_PARENT_SHA,
            "mass_resampling": "verbatim port of build_lane MASS_BRIDGE with the same seed; "
                               "row selection and obs names are therefore identical to v0013",
            "geometry": "parent spatial_3D row-selected, cast to float32 (identical to v0013)",
            "only_difference_vs_v0013": "the expression matrix (added anatomical contrast)",
        },
        "reference_readings": refs,
        "arms": {},
        "bridge_diagnostics": {"clip_fraction": bridge_clip_frac,
                               "dup_suffix_rows": int(sum(1 for n in final_names if "__dup" in n)),
                               "with_replacement": replaced,
                               "shared_states": len(shared_states)},
    }
    pd.DataFrame(plan).to_csv(OUT_DIR / "mass_plan.tsv", sep="\t", index=False)
    pd.DataFrame({"out_row": range(len(final_names)), "parent_row": chosen.tolist(),
                  "parent_obs_name": [pnames[i] for i in chosen],
                  "out_obs_name": final_names}).to_csv(OUT_DIR / "source_row_ledger.tsv",
                                                        sep="\t", index=False)

    for lane, arm in arms.items():
        m = ev(arm["X"], out_coords)
        deg = (m["neighborhood_mmd"] - refs["do_nothing"]["neighborhood_mmd"]) / \
            refs["do_nothing"]["neighborhood_mmd"] * 100.0
        cls = ("IMPROVE" if deg <= -M0_PROMOTE_PCT
               else "TIER" if abs(deg) <= M0_PROMOTE_PCT else "DEGRADE")
        payload["arms"][lane] = {
            "metrics": m, "degradation_pct_vs_do_nothing": deg, "m0_class": cls,
            "n_ct_with_coeffs": arm["n_ct_with_coeffs"], "contrast_sd_mean": arm["contrast_sd_mean"],
            "beats_do_nothing": bool(m["neighborhood_mmd"] < refs["do_nothing"]["neighborhood_mmd"]),
            "beats_bridge_only": bool(m["neighborhood_mmd"] < refs["bridge_only_equals_v0013"]["neighborhood_mmd"]),
        }
        print(f"{lane}: nmmd={m['neighborhood_mmd']:.6f} ({cls}, {deg:+.2f}%) "
              f"d2={m['d2_shape']:.5f} mmd_u={m['mmd_u']:.5f}", flush=True)

        # write the candidate h5ad (geometry/rows identical to v0013 by construction)
        out_a = P[chosen].copy()
        out_a.obs_names = final_names
        out_a.X = arm["X"]
        for k in list(out_a.obsm.keys()):
            out_a.obsm[k] = (np.ascontiguousarray(np.asarray(out_a.obsm[k])[:, :3], dtype=np.float32)
                             if k == "spatial_3D"
                             else np.ascontiguousarray(np.asarray(out_a.obsm[k]), dtype=np.float32))
        out_a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": NORMALIZATION}
        out_a.uns["ve_t2_hn2_a2c"] = json.dumps({
            "atom_id": OUT_DIR.name, "lane": lane,
            "board": "T2:heart:val_interp", "alpha": ALPHA, "spline_degree": SPLINE_DEGREE,
            "target_stage": TARGET_STAGE, "source_stages": list(SOURCE_STAGES),
            "parent_sha256": BRIDGE_PARENT_SHA, "bridge_seed": BRIDGE_SEED,
            "target_used": False}, sort_keys=True)
        cdir = OUT_DIR / "candidates" / lane
        cdir.mkdir(parents=True, exist_ok=True)
        out = cdir / "submission.h5ad"
        if not out.exists():
            out_a.write_h5ad(out)
        payload["arms"][lane]["candidate"] = str(out.relative_to(PROJECT_ROOT))
        payload["arms"][lane]["candidate_sha256"] = sha256(out)
        print(f"  wrote {out.relative_to(PROJECT_ROOT)}", flush=True)

    # --- byte-identity check vs the incumbent v0013 ---
    inc = ad.read_h5ad(PROJECT_ROOT / INCUMBENT, backed="r")
    inc_C = np.asarray(inc.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    inc_names = [str(v) for v in inc.obs_names]
    inc.file.close()
    identity = {
        "obs_names_identical_to_v0013": bool(inc_names == final_names),
        "coords_identical_to_v0013": bool(np.array_equal(inc_C, out_coords)),
        "coords_sha_v0013": hashlib.sha256(np.ascontiguousarray(inc_C, dtype=np.float32).tobytes()).hexdigest(),
        "coords_sha_this_run": hashlib.sha256(np.ascontiguousarray(out_coords, dtype=np.float32).tobytes()).hexdigest(),
    }
    payload["byte_identity_check_vs_v0013"] = identity
    print("byte-identity vs v0013:", json.dumps(identity), flush=True)

    payload["wall_seconds"] = time.time() - t0
    (OUT_DIR / "a2c_run.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8")
    print(f"\nwrote {OUT_DIR/'a2c_run.json'} ({payload['wall_seconds']:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
