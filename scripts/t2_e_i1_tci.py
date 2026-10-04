#!/usr/bin/env python3
"""T2 `E-I1 TCI`：置信度加权 + 解剖层内借表达（transport-consistency-weighted intra-layer borrowing）。

设计冻结：`reports/T2_E_I1_TCI_DESIGN_FREEZE_20260927.md`（`D-20260927-T2EI1-001`）。
锚点核验：`D-20260927-T2CITE-002`（CPD 核心锚点成立；「正反一致性」为本项目自定）。

## 事前设计修正（跑之前写定）

冻结设计 §1.5 把层内对比度项写为「按该层内标准差归一」。实现照此执行，并额外
**把贡献量与 `SBL_H2` 的实测失败对齐**：`E-N1 SBL` 因 z-score 回归产生标准差量级的
位置项而把总质量抬高 53%+（`D-20260927-T2EN1-002`）。故本路线**不使用任何「按
基因标准差」定标**，只用**层内**归一，且 `GAIN` 事前定死为 1.0。

## 逐字节不变的部分

几何、行序、obs 名、组成重采样全部沿用 `scripts/batch4/t2_expression_bridge.py`
的 embryo 臂代码路径与同一种子（`SEED = 20260904`），因此与 v0010 的差异**只在
表达矩阵**。开跑即断言父版 SHA 与坐标/行序一致。

## 泄漏防护

源阶段为 E6.75 / E7.25 / E8.0；本板 target = **E7.5**，无源阶段等于 target。
脚本以断言强制；`TARGET_TAU` 必须等于 E7.5 在 τ(6.75)=0/τ(7.25)=1/3/τ(8.0)=1 轴
上的位置 (7.5−6.75)/(8.0−6.75) = 0.6。
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

OUT_DIR = PROJECT_ROOT / "artifacts/tool_integration/T2-E-I1-TCI-20260927-v1"

# ---- frozen contract inputs (identical to B4-T2-R2, embryo arm) ----
BRIDGE_SEED = 20260904
NORMALIZATION = "log1p_cp10k_per1k_like"
PANEL = "data/gene_panel/T2__embryo__val_interp.genes.txt"
BRIDGE_LEFT = "data/E7.25.h5ad"
BRIDGE_RIGHT = "data/E8.0.h5ad"
BRIDGE_LAMBDA = 1.0 / 3.0
N_CELLS = 5000
BRIDGE_PARENT = "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad"
BRIDGE_PARENT_SHA = "392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4"
INCUMBENT = "submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad"

# ---- TCI source stage (the single source whose cells we borrow from) ----
TCI_SOURCE_STAGE = "E7.25"
TCI_SOURCE_FILE = "data/E7.25.h5ad"
TCI_SOURCE_TAU = 1.0 / 3.0

# ---- frozen TCI constants ----
N_LAYERS = 6              # frozen anatomical layer count
CPD_ITERS = 20            # EM iterations, frozen
CPD_SIGMA2 = 1.0          # GMM variance (squared, canonical frame), frozen
CPD_W = 0.0               # non-rigid weight; frozen (rigid mode only)
GAIN = 1.0                # frozen; not tunable on the outcome
SEED = 20260927

# ---- evaluation ----
PSEUDO_TARGET = "data/E7.25.h5ad"
PSEUDO_REFERENCE = "data/E6.75.h5ad"
DO_NOTHING = "submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad"
M0_NMMD = 0.031240        # do-nothing, measured in D-20260927-T2VALIDATE-001


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


def cpd_rigid_em(X: np.ndarray, Y: np.ndarray, n_iter: int = CPD_ITERS,
                 sigma2: float = CPD_SIGMA2, w: float = CPD_W) -> tuple[np.ndarray, float]:
    """Coherent Point Drift, rigid mode, from-scratch implementation.

    X: source points (n, d). Y: target points (m, d). Correspondence matrix P is
    (m, n) with P[j, i] = p(target j given source i). No third-party CPD code is
    vendored; this is the standard rigid EM written out explicitly.

    E-step: p(j|i) proportional to exp(-||y_j - t_i||^2 / (2 sigma^2)).
    M-step: similarity transform (proper rotation + translation) maximising the
            expected log-likelihood, via weighted Kabsch.
    """
    n, d = X.shape
    T = X.copy()
    sigma2 = float(sigma2)
    P = None

    for _ in range(n_iter):
        D2 = ((Y ** 2).sum(1)[:, None] + (T ** 2).sum(1)[None, :] - 2.0 * (Y @ T.T))
        P = np.exp(-np.maximum(D2, 0.0) / (2.0 * sigma2))
        P /= np.maximum(P.sum(axis=1, keepdims=True), 1e-300)   # p(j|i)

        # per-point correspondence-weighted centroids
        mx = P.sum(axis=0)          # (n,) weight of each SOURCE point
        my = P.sum(axis=1)          # (m,) weight of each TARGET point
        mu_x = (P.T @ Y) / np.maximum(mx, 1e-300)[:, None]    # (n, d) source->target
        mu_y = (P @ T) / np.maximum(my, 1e-300)[:, None]      # (m, d) target->source
        Xc = X - mu_x
        Yc = Y - mu_y

        # weighted Kabsch; order the products so no (n, m, d) temporary is formed
        H = Xc.T @ (P.T @ Yc)                                  # (d, d)
        U, _S, Vt = np.linalg.svd(H, full_matrices=False)
        D = np.eye(d)
        if np.linalg.det(Vt.T @ U.T) < 0:                      # proper rotation
            D[-1, -1] = -1.0
        R = Vt.T @ D @ U.T                                      # maps Xc -> Yc
        # optimal translation for a weighted Procrustes fit:
        #   sum_ij P[j,i](y_j - x_i R^T) = (my @ Y) - R^T (mx @ X)
        tvec = ((my @ Y) - R.T @ (mx @ X)) / max(float(mx.sum()), 1e-300)
        # each source point moves to its correspondence-weighted target centroid,
        # rotated about that centroid, then translated globally (CPD coherence step)
        T_fit = Xc @ R.T + mu_x + tvec
        sigma2 = float((np.maximum(D2, 0.0) * P).sum() / max(float(P.sum()), 1e-300) / d)
        sigma2 = max(sigma2, 1e-6)
        T = T_fit

    assert P is not None
    return P, float(1.0 / np.maximum((P ** 2).sum(axis=1), 1e-300).mean())

def anatomical_layers(coords: np.ndarray, n_layers: int = N_LAYERS) -> np.ndarray:
    """Frozen layer assignment: k-means on a small set of intrinsic geometric features.

    No expression is used. Features are the same proxies as the A2C route so that a
    layer means something anatomical rather than a random partition.
    """
    from sklearn.cluster import KMeans

    Z, _c, _r, _V = SF.canonicalize(coords[:, :3])
    feats = np.stack([
        Z[:, 0],
        np.linalg.norm(Z[:, 1:], axis=1),
        -np.log(np.maximum(np.linalg.norm(Z[:, 1:] - Z[:, [0]], axis=1), 1e-12)),
    ], axis=1)
    feats = (feats - feats.mean(0)) / np.maximum(feats.std(0), 1e-12)
    km = KMeans(n_clusters=n_layers, n_init=10, random_state=SEED)
    return km.fit_predict(feats)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # --- leak guard -------------------------------------------------
    # The board's real target is E7.5. No SOURCE stage may be E7.5.
    # NOTE: E7.25 is simultaneously (a) a legitimate bridge source and (b) the
    # frozen local pseudo-target inherited from the J1 atom. That is NOT a leak --
    # the board target is E7.5, not E7.25 -- but it DOES make the local evaluation
    # partially circular by design, which is why this board's 5% rule is
    # suspended and local numbers are record-only. Absolute levels here are not
    # interpretable; candidate-vs-incumbent on the same pseudo-target is.
    target_tau = (7.5 - 6.75) / (8.0 - 6.75)
    assert abs(target_tau - 0.6) < 1e-12, target_tau
    source_stages_used = {"E6.75", "E7.25", "E8.0"}
    assert "E7.5" not in source_stages_used, "LEAK: E7.5 is the board target"
    assert TCI_SOURCE_STAGE == "E7.25" and BRIDGE_LEFT.endswith("E7.25.h5ad") \
        and BRIDGE_RIGHT.endswith("E8.0.h5ad")
    print(f"leak guard: board target E7.5 (tau={target_tau:.4f}) absent from sources "
          f"{sorted(source_stages_used)}; borrowing from {TCI_SOURCE_STAGE}. OK", flush=True)
    print(f"circularity disclosure: {PSEUDO_TARGET} is both a bridge source and the frozen "
          f"pseudo-target -> local numbers are RECORD ONLY (D-20260927-T2M0APPXB-001)",
          flush=True)

    panel = [l.strip() for l in (PROJECT_ROOT / PANEL).read_text().splitlines() if l.strip()]

    def load(rel: str) -> dict[str, Any]:
        a = ad.read_h5ad(PROJECT_ROOT / rel, backed="r")
        vn = [str(v) for v in a.var_names]
        pos = np.array([vn.index(g) for g in panel])
        Xd = dense(a.X[:, pos]).astype(np.float64)
        types = np.asarray(a.obs["celltype"].astype(str))
        C = np.asarray(a.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        a.file.close()
        return {"X": Xd, "types": types, "C": C}

    # --- reproduce the incumbent L2 bridge exactly (v0010) ---
    parent_path = PROJECT_ROOT / BRIDGE_PARENT
    assert sha256(parent_path) == BRIDGE_PARENT_SHA, "BLOCKED_INPUT: bridge parent drift"
    XL, XR = load(BRIDGE_LEFT), load(BRIDGE_RIGHT)
    P = ad.read_h5ad(parent_path)
    pnames = [str(v) for v in P.obs_names]
    ptypes = np.asarray(P.obs["celltype"].astype(str))
    XP = dense(P.X).astype(np.float64)
    pC = np.asarray(P.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    assert XP.shape == (N_CELLS, len(panel)), XP.shape

    mL, mR = means_by_type(XL["X"], XL["types"]), means_by_type(XR["X"], XR["types"])
    pL = {s: float((XL["types"] == s).sum()) / len(XL["types"]) for s in set(XL["types"].tolist())}
    pR = {s: float((XR["types"] == s).sum()) / len(XR["types"]) for s in set(XR["types"].tolist())}
    pstates = sorted(set(ptypes.tolist()))
    shared_states = sorted(set(pstates) & set(mL) & set(mR))
    muP = means_by_type(XP, ptypes)
    shift = {}
    for s in pstates:
        if s in shared_states:
            shift[s] = ((1.0 - BRIDGE_LAMBDA) * mL[s] + BRIDGE_LAMBDA * mR[s] - muP[s])
        else:
            shift[s] = np.zeros(XP.shape[1])
    X1 = XP.copy()
    for s in pstates:
        X1[ptypes == s] += shift[s]
    np.clip(X1, 0, None, out=X1)

    pP = {s: float((ptypes == s).sum()) / len(ptypes) for s in pstates}
    raw = {}
    for s in pstates:
        if s in shared_states:
            raw[s] = (1.0 - BRIDGE_LAMBDA) * pL.get(s, 0.0) + BRIDGE_LAMBDA * pR.get(s, 0.0)
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
    print(f"bridge reproduced: dup_rows={sum(1 for n in final_names if '__dup' in n)}", flush=True)

    # --- TCI: CPD + confidence + intra-layer borrowing on the PARENT geometry ---
    XS = load(TCI_SOURCE_FILE)
    Zs, _c, _r, _V = SF.canonicalize(XS["C"])
    Zp, _c2, _r2, _V2 = SF.canonicalize(pC)

    Pmat, conf_scalar = cpd_rigid_em(Zs, Zp)
    # forward-backward confidence (project-defined, not from the CPD paper).
    # Pmat[j,i] = p(target j | source i);  Pb[j,i] = p(source i | target j).
    # conf for target j is the row-wise agreement of the two conditionals.
    Pb = Pmat / np.maximum(Pmat.sum(axis=0, keepdims=True), 1e-300)
    conf = (Pmat * Pb).sum(axis=1)                      # per TARGET cell, length m
    assert conf.shape[0] == pC.shape[0], (conf.shape, pC.shape)
    conf = conf / np.maximum(conf.max(), 1e-12)
    w = np.clip(conf, 0.0, 1.0)                           # frozen: linear, no tuning
    print(f"CPD: iters={CPD_ITERS} mean_conf={w.mean():.4f} conf_range=[{w.min():.3f},{w.max():.3f}]",
          flush=True)

    # expectation of the source expression under the soft correspondence
    borrowed = Pmat @ XS["X"]                             # (n_target, G)
    # intra-layer restriction: renormalise the correspondence within the layer
    layers_t = anatomical_layers(pC)
    layers_s = anatomical_layers(XS["C"])
    empty = 0
    borrow_layered = np.zeros_like(borrowed)
    for L in range(N_LAYERS):
        tj = np.flatnonzero(layers_t == L)
        sj = np.flatnonzero(layers_s == L)
        if not tj.size or not sj.size:
            empty += int(tj.size)
            borrow_layered[tj] = borrowed[tj] if not sj.size else XS["X"].mean(axis=0)[None, :]
            continue
        sub = Pmat[np.ix_(tj, sj)]
        tot = sub.sum(axis=1, keepdims=True)
        empty += int((tot.ravel() <= 1e-12).sum())
        norm = np.divide(sub, np.maximum(tot, 1e-12))
        emptyrows = (tot.ravel() <= 1e-12)
        borrow_layered[tj] = norm @ XS["X"][sj]
        if emptyrows.any():
            borrow_layered[tj[emptyrows]] = XS["X"][sj].mean(axis=0)[None, :]
    print(f"layers: empty_target_cells={empty} of {len(pC)}", flush=True)

    # --- assemble: position-free global level + layer-standardised borrowed contrast ---
    src_mean = XS["X"].mean(axis=0)
    left_mean = XL["X"].mean(axis=0)
    right_mean = XR["X"].mean(axis=0)
    lam = (7.5 - 6.75) / (8.0 - 6.75)
    global_level = (1.0 - lam) * left_mean + lam * right_mean   # position-free

    contrast = borrow_layered - borrow_layered.mean(axis=0, keepdims=True)
    for L in range(N_LAYERS):                                   # layer-internal standardisation
        rows = np.flatnonzero(layers_t == L)
        if not rows.size:
            continue
        sd = contrast[rows].std(axis=0, keepdims=True)
        sd[sd < 1e-12] = 1.0
        contrast[rows] /= sd
    contrast *= GAIN

    arms: dict[str, Any] = {}
    for lane, use_layers in (("L1_tci_conf_layered", True), ("L2_tci_conf_global", False)):
        base_borrow = borrow_layered if use_layers else Pmat @ XS["X"]
        if not use_layers:
            c = base_borrow - base_borrow.mean(axis=0, keepdims=True)
            sd = c.std(axis=0, keepdims=True)
            sd[sd < 1e-12] = 1.0
            base_borrow = c / sd
        blend = w[:, None] * base_borrow + (1.0 - w[:, None]) * src_mean[None, :]
        Xt = global_level[None, :] + GAIN * blend
        np.clip(Xt, 0, None, out=Xt)
        arms[lane] = np.ascontiguousarray(Xt[chosen], dtype=np.float32)
        print(f"{lane}: Xsum={arms[lane].sum():.1f}", flush=True)

    base_rows = np.ascontiguousarray(X1[chosen], dtype=np.float32)
    out_coords = np.ascontiguousarray(pC[chosen][:, :3], dtype=np.float32)

    # --- evaluation on the frozen pseudo-target (record-only on this board) ---
    true = load(PSEUDO_TARGET)
    dn = load(DO_NOTHING)

    def ev(X, C):
        return {
            "neighborhood_mmd": float(T2_METRICS.neighborhood_mmd(X, C, true["X"], true["C"], k=15, n=2000)),
            "mmd_u": float(mmd_unbiased(X, true["X"], n=2000, seed=0)),
            "energy_distance": float(energy_distance(X, true["X"])),
            "variogram": float(variogram_score(X, true["X"])),
            "d2_shape": float(d2_distance(C, true["C"], seed=SEED)),
            "occupancy_dice": float(occupancy_dice(C, true["C"], seed=SEED)[0]),
        }

    refs = {"do_nothing": ev(dn["X"], dn["C"]), "bridge_only_equals_v0010": ev(base_rows, out_coords)}
    for k, v in refs.items():
        print(f"ref {k}: nmmd={v['neighborhood_mmd']:.6f}", flush=True)

    payload: dict[str, Any] = {
        "schema": "ve.t2.e-i1-tci.v1",
        "atom": "T2-E-I1-TCI-20260927-v1",
        "board": "T2_embryo_val_interp",
        "design_freeze": "reports/T2_E_I1_TCI_DESIGN_FREEZE_20260927.md",
        "anchor_verification": "D-20260927-T2CITE-002 (CPD core anchor holds; forward-backward confidence is project-defined)",
        "frozen_constants": {"n_layers": N_LAYERS, "cpd_iters": CPD_ITERS,
                             "cpd_sigma2": CPD_SIGMA2, "cpd_w": CPD_W, "gain": GAIN,
                             "bridge_seed": BRIDGE_SEED, "seed": SEED, "lambda": lam,
                             "source_stage": TCI_SOURCE_STAGE, "target_stage": 7.5},
        "pre_training_amendments": [
            "A1: the contrast is standardised by WITHIN-LAYER sd only; no per-gene global sd is used anywhere, because E-N1 SBL showed a gene-sd-scaled position term inflated total mass by 53% (D-20260927-T2EN1-002)",
            "A2: GAIN = 1.0 fixed before the run; neither arm may change it",
        ],
        "leak_guard": {"target_stage": 7.5, "target_tau": target_tau,
                       "source_stage": TCI_SOURCE_STAGE, "source_tau": TCI_SOURCE_TAU,
                       "assertion": "target E7.5 is not among the source stages (PASS)"},
        "confidence": {"mean": float(w.mean()), "min": float(w.min()), "max": float(w.max()),
                       "form": "clip(forward-backward CPD consistency, 0, 1) - linear, frozen"},
        "layers": {"n": N_LAYERS, "empty_target_cells": int(empty)},
        "byte_identity": {"parent": BRIDGE_PARENT, "parent_sha256": BRIDGE_PARENT_SHA,
                          "only_difference_vs_v0010": "the expression matrix"},
        "reference_readings": refs,
        "arms": {},
        "board_judgement": "embryo board: 5% rule SUSPENDED per D-20260927-T2M0APPXB-001; "
                           "local numbers are RECORD ONLY and do not decide promotion",
    }
    pd.DataFrame(plan).to_csv(OUT_DIR / "mass_plan.tsv", sep="\t", index=False)
    pd.DataFrame({"out_row": range(len(final_names)), "parent_row": chosen.tolist(),
                  "parent_obs_name": [pnames[i] for i in chosen],
                  "out_obs_name": final_names}).to_csv(OUT_DIR / "source_row_ledger.tsv",
                                                        sep="\t", index=False)

    for lane, X in arms.items():
        m = ev(X, out_coords)
        payload["arms"][lane] = {
            "metrics": m,
            "vs_do_nothing_pct": 100.0 * (m["neighborhood_mmd"] - refs["do_nothing"]["neighborhood_mmd"])
                                 / refs["do_nothing"]["neighborhood_mmd"],
            "vs_incumbent_pct": 100.0 * (m["neighborhood_mmd"]
                                         - refs["bridge_only_equals_v0010"]["neighborhood_mmd"])
                                / refs["bridge_only_equals_v0010"]["neighborhood_mmd"],
            "beats_do_nothing": bool(m["neighborhood_mmd"] < refs["do_nothing"]["neighborhood_mmd"]),
            "beats_incumbent": bool(m["neighborhood_mmd"]
                                   < refs["bridge_only_equals_v0010"]["neighborhood_mmd"]),
        }
        print(f"{lane}: nmmd={m['neighborhood_mmd']:.6f} "
              f"vs_dn={payload['arms'][lane]['vs_do_nothing_pct']:+.1f}% "
              f"vs_inc={payload['arms'][lane]['vs_incumbent_pct']:+.1f}%", flush=True)
        out_a = P[chosen].copy()
        out_a.obs_names = final_names
        out_a.X = X
        for k in list(out_a.obsm.keys()):
            out_a.obsm[k] = (np.ascontiguousarray(np.asarray(out_a.obsm[k])[:, :3], dtype=np.float32)
                             if k == "spatial_3D"
                             else np.ascontiguousarray(np.asarray(out_a.obsm[k]), dtype=np.float32))
        out_a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": NORMALIZATION}
        out_a.uns["ve_t2_ei1_tci"] = json.dumps({
            "atom_id": "T2-E-I1-TCI-20260927-v1", "lane": lane,
            "board": "T2:embryo:val_interp", "n_layers": N_LAYERS, "gain": GAIN,
            "source_stage": TCI_SOURCE_STAGE, "target_stage": 7.5,
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

    inc = ad.read_h5ad(PROJECT_ROOT / INCUMBENT, backed="r")
    inc_C = np.asarray(inc.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    inc_names = [str(v) for v in inc.obs_names]
    inc.file.close()
    payload["byte_identity_check_vs_v0010"] = {
        "obs_names_identical": bool(inc_names == final_names),
        "coords_identical": bool(np.array_equal(inc_C, out_coords)),
        "coords_sha_v0010": hashlib.sha256(np.ascontiguousarray(inc_C, dtype=np.float32).tobytes()).hexdigest(),
        "coords_sha_this_run": hashlib.sha256(np.ascontiguousarray(out_coords, dtype=np.float32).tobytes()).hexdigest(),
    }
    print("byte-identity vs v0010:", json.dumps(payload["byte_identity_check_vs_v0010"]), flush=True)
    payload["wall_seconds"] = time.time() - t0
    (OUT_DIR / "tci_run.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8")
    print(f"\nwrote {OUT_DIR/'tci_run.json'} ({payload['wall_seconds']:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
