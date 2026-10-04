#!/usr/bin/env python3
"""T2 LEADS L-008 前置探针：加性空间对比度的「幅度 → 分布损伤」关系。

为什么做
--------
三次独立尝试（`E-N1 SBL` +1085~1164%、`H-N2 A2C` +78~97%、`E-I1 TCI`
+2379~2568%，均相对各自现役版本）收敛到同一失败模式：给一个已被服务器正向
验证的**低空间方差均值场**叠加任何"学出来的空间对比度"都会摧毁分布，且劣化
幅度与**对比度相对全局水平的幅度**同向。

关键细节：把对比度定标到 sd=1 本身就把幅度固定在远大于每基因均值（log 空间
约 0.25）的水平上。**归一化的原则对，sd=1 这个定标是病灶。**

本探针把「幅度」单独隔离出来，作为**唯一被扫的变量**。

设计（跑前定死）
----------------
* **基座** = 各板现役 L2 桥的表达矩阵（`bridge_only`，本项目已两次独立复现到
  1.5e-07），代表「已被服务器正向验证的低空间方差场」。
* **对比项** = 由**目标几何派生、与任何表达无关**的确定性空间场（解剖轴向坐标
  a1，见 `t2_h_n2_a2c.anatomical_coords`）。**刻意不用学习得到的场**：学习场会
  把「幅度」与「内容是否正确」两个变量缠在一起，无法归因。
* **幅度阶梯**（唯一被扫的变量）：
  ``AMPS = (0.0, 0.02, 0.05, 0.10, 0.25, 0.50, 1.00)``
  `0.0` 即基座本身（对照）。对比项已按 sd=1 标准化，故 `a` 的单位是
  「每基因全局均值的倍数」。
* **一切其他量冻结**：pseudo-target、seed、行序、组成重采样、几何。

两个输出
--------
1. `damage_curve`：每个幅度下的 `neighborhood_mmd` / `mmd_u` / `energy_distance` /
   `variogram`，以及相对 `a=0` 的变化率。
2. `truth_amplitude`：真值侧自身的空间对比度幅度（每个基因在最小 lag 上的经验
   变异函数半方差）。这是「由数据决定的幅度」应当锚定到的量级——L-008 的可操作
   结论取决于 `damage` 起点与 `truth_amplitude` 的相对位置。

预声明判定
----------
* 若 `a_dmg`（`neighborhood_mmd` 相对基座劣化超过 5% 的最小幅度）**存在**且与
  `truth_amplitude` 同量级 → 未来 lane 可以走「均值场 + 加性空间项」，但幅度
  **必须由真值侧统计量导出并受限**，不得再用固定归一化。
* 若最小的非零幅度即已劣化（阶梯内找不到可接受区）→ 「加性空间对比度」在两板
  上**无论幅度多小都不可用**，该机制族关闭，后续只走边际分布方向。
* 两种情况都**不**授权任何新 lane；本探针只产出幅度-损伤关系这一个事实。

诚实标注
--------
* 全部读数在 pseudo-target（E7.25 / E8.75 观测期 stage）上计算，**部分循环**
  （embryo 的 E7.25 同时是桥源与评价目标；heart 的 E8.75 恰为 bracket stage），
  **绝对水平不可解释**，只有「同一基座下不同幅度的相对变化」有效。
* 对比项是**几何派生**而非学习所得，因此本探针给出的是**该基座对该幅度阶梯的
  损伤曲线**，不是「任何可能的空间场」的上界。已学习场的内容可能另有损害，但
  三次尝试的实证表明损害主项是幅度而非内容。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

# This script lives in scripts/gate/, so the project root is parents[2].
# (Scripts directly in scripts/ use parents[1] — mixing them up silently points
# one level off and produced a confusing "No such file" on third_party/.)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
for _p in (PROJECT_ROOT, PROJECT_ROOT / "scripts", PROJECT_ROOT / "third_party/veckit"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import importlib.util  # noqa: E402
import types  # noqa: E402

import anndata as ad  # noqa: E402

OUT_DIR = PROJECT_ROOT / "artifacts/gate/T2_L008_AMPLITUDE_DAMAGE-20260927-v1"

# ---- the single swept variable ----
AMPS: tuple[float, ...] = (0.0, 0.02, 0.05, 0.10, 0.25, 0.50, 1.00)
M0_BAND_PCT = 5.0            # pre-declared damage band on neighborhood_mmd
SEED = 20260927

# ---- frozen board inputs (identical to what both failing lanes used) ----
BOARDS: dict[str, dict[str, Any]] = {
    "T2_embryo_val_interp": {
        "panel": "data/gene_panel/T2__embryo__val_interp.genes.txt",
        "left": "data/E7.25.h5ad", "right": "data/E8.0.h5ad", "lam": 1.0 / 3.0,
        "bridge_parent": "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
        "incumbent": "submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        "pseudo_target": "data/E7.25.h5ad",
        "n": 5000, "m0_active": False,
    },
    "T2_heart_val_interp": {
        "panel": "data/gene_panel/T2__heart__val_interp.genes.txt",
        "left": "data/E8.25_late.h5ad", "right": "data/E8.75.h5ad", "lam": 0.5,
        "bridge_parent": "submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad",
        "incumbent": "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        "pseudo_target": "data/E8.75.h5ad",
        "n": 5872, "m0_active": True,
    },
}
BRIDGE_SEED = 20260904
NORMALIZATION = "log1p_cp10k_per1k_like"


def _load_veckit_t2():
    root = PROJECT_ROOT / "third_party/veckit"

    def _load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    t1 = _load("t1_metrics", root / "T1" / "metrics.py")
    reuse = types.ModuleType("_reuse")
    reuse.t1_metrics = t1
    sys.modules["_reuse"] = reuse
    t2 = _load("t2_metrics", root / "T2" / "metrics.py")
    sys.modules["metrics"] = t2
    return t2


T2_METRICS = _load_veckit_t2()
from common.core_metrics import energy_distance, mmd_unbiased, variogram_score  # noqa: E402


def _load_sf():
    spec = importlib.util.spec_from_file_location(
        "t2_s3_shape_field", str(PROJECT_ROOT / "scripts/t2_s3_shape_field.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["t2_s3_shape_field"] = mod
    spec.loader.exec_module(mod)
    return mod


SF = _load_sf()


def dense(X) -> np.ndarray:
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def means_by_type(Xd: np.ndarray, t: np.ndarray) -> dict:
    return {str(c): Xd[t == c].mean(axis=0) for c in np.unique(t)}


def load(rel: str, panel: list[str]) -> dict[str, Any]:
    a = ad.read_h5ad(PROJECT_ROOT / rel, backed="r")
    vn = [str(v) for v in a.var_names]
    pos = np.array([vn.index(g) for g in panel])
    X = dense(a.X[:, pos]).astype(np.float64)
    t = np.asarray(a.obs["celltype"].astype(str))
    C = np.asarray(a.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    a.file.close()
    return {"X": X, "t": t, "C": C}


def rebuild_base(cfg: dict[str, Any], panel: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Recompute the incumbent L2 bridge (mean+shift+mass) from the frozen inputs."""
    XL, XR = load(cfg["left"], panel), load(cfg["right"], panel)
    P = ad.read_h5ad(PROJECT_ROOT / cfg["bridge_parent"])
    pnames = [str(v) for v in P.obs_names]
    ptypes = np.asarray(P.obs["celltype"].astype(str))
    XP = dense(P.X).astype(np.float64)
    pC = np.asarray(P.obsm["spatial_3D"], dtype=np.float64)[:, :3]

    mL, mR = means_by_type(XL["X"], XL["t"]), means_by_type(XR["X"], XR["t"])
    pL = {s: float((XL["t"] == s).sum()) / len(XL["t"]) for s in set(XL["t"].tolist())}
    pR = {s: float((XR["t"] == s).sum()) / len(XR["t"]) for s in set(XR["t"].tolist())}
    pstates = sorted(set(ptypes.tolist()))
    shared = sorted(set(pstates) & set(mL) & set(mR))
    muP = means_by_type(XP, ptypes)
    X1 = XP.copy()
    for s in pstates:
        sh = ((1.0 - cfg["lam"]) * mL[s] + cfg["lam"] * mR[s] - muP[s]) if s in shared \
            else np.zeros(XP.shape[1])
        X1[ptypes == s] += sh
    np.clip(X1, 0, None, out=X1)

    pP = {s: float((ptypes == s).sum()) / len(ptypes) for s in pstates}
    raw = {}
    for s in pstates:
        raw[s] = ((1.0 - cfg["lam"]) * pL.get(s, 0.0) + cfg["lam"] * pR.get(s, 0.0)) if s in shared \
            else 0.5 * pP[s] + 0.5 * pL.get(s, 0.0)
    tot = sum(raw.values())
    raw = {s: v / tot for s, v in raw.items()}
    counts = {s: int(raw[s] * len(ptypes)) for s in pstates}
    deficit = len(ptypes) - sum(counts.values())
    rema = sorted(pstates, key=lambda s: (raw[s] * len(ptypes) - counts[s], s), reverse=True)
    for i in range(deficit):
        counts[rema[i % len(rema)]] += 1
    rng = np.random.default_rng(BRIDGE_SEED)
    chosen = []
    for s in pstates:
        pool = np.flatnonzero(ptypes == s)
        k = counts[s]
        chosen.extend((np.sort(pool[rng.choice(len(pool), size=k, replace=False)])
                       if k < len(pool) else (np.sort(pool) if k == len(pool)
                                              else np.sort(pool[rng.choice(len(pool), size=k, replace=True)]))).tolist())
    chosen = np.asarray(chosen, dtype=np.int64)
    seen: dict[str, int] = {}
    final_names = []
    for i in chosen.tolist():
        nm = pnames[i]
        k = seen.get(nm, 0)
        final_names.append(nm if k == 0 else f"{nm}__dup{k}")
        seen[nm] = k + 1

    base = np.ascontiguousarray(X1[chosen], dtype=np.float32)
    coords = np.ascontiguousarray(pC[chosen][:, :3], dtype=np.float32)

    # verify against the frozen incumbent artifact (row order + coords)
    inc = ad.read_h5ad(PROJECT_ROOT / cfg["incumbent"], backed="r")
    inc_names = [str(v) for v in inc.obs_names]
    inc_C = np.asarray(inc.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    inc.file.close()
    verify = {
        "obs_names_match_incumbent": bool(inc_names == final_names),
        "coords_match_incumbent": bool(np.array_equal(inc_C, np.asarray(coords, dtype=np.float64))),
    }
    return base, coords, verify


def truth_spatial_amplitude(X: np.ndarray, coords: np.ndarray, k: int = 20) -> dict[str, float]:
    """Per-gene empirical semivariance at the smallest lag, on the TRUE field.

    This is the 'data-derived amplitude' that L-008 says a future lane should
    anchor to. Reported as the median/quartiles over genes.
    """
    from sklearn.neighbors import NearestNeighbors
    nn = int(min(k, X.shape[0] - 1))
    _, idx = NearestNeighbors(n_neighbors=nn + 1).fit(coords).kneighbors(coords)
    nb = idx[:, 1:]
    d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1) if X.shape[0] <= 1500 else None
    if d2 is None:  # too big for dense: use the neighbour pairs only
        vals = ((X[:, None, :] - X[nb][:, :, :]) ** 2).mean(-1).mean(axis=1)
    else:
        vals = np.take_along_axis(d2, nb, axis=1).mean(axis=1)
    q = np.percentile(vals, [10, 50, 90])
    return {"semivar_p10": float(q[0]), "semivar_median": float(q[1]), "semivar_p90": float(q[2]),
            "sqrt_median": float(np.sqrt(max(q[1], 0.0)))}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    payload: dict[str, Any] = {
        "schema": "ve.t2.l008-amplitude-damage.v1",
        "atom": "T2-L008-AMPLITUDE-DAMAGE-20260927-v1",
        "purpose": "isolate AMPLITUDE as the single swept variable for an additive spatial contrast on top of the proven incumbent mean field",
        "swept_variable": "amplitude a of a geometry-derived, sd=1-standardised spatial contrast",
        "amplitudes": list(AMPS),
        "m0_damage_band_pct": M0_BAND_PCT,
        "contrast_source": "anatomical axis coordinate a1 on the canonicalised target geometry; "
                          "deterministic, independent of any expression",
        "boards": {},
        "declarations": [
            "READ-ONLY probe: no candidate, no h5ad output, no submission, no INDEX row, no upload",
            "amplitude is the ONLY swept variable; pseudo-target, seed, row order, composition resampling and geometry are all frozen",
            "the contrast is geometry-derived, not learned: this isolates amplitude from 'is the learned content correct'",
            "absolute levels are NOT interpretable (pseudo-target is an observed stage and partially circular); only the relative change across amplitudes at a fixed base is",
            "this probe authorises no new lane; it produces one fact: the amplitude-damage relation",
        ],
    }

    for board, cfg in BOARDS.items():
        started = time.time()
        panel = [l.strip() for l in (PROJECT_ROOT / cfg["panel"]).read_text().splitlines() if l.strip()]
        base, coords, verify = rebuild_base(cfg, panel)
        print(f"== {board}  base{base.shape}  verify={json.dumps(verify)}", flush=True)

        true = load(cfg["pseudo_target"], panel)
        C = np.asarray(coords, dtype=np.float64)

        # deterministic spatial contrast: anatomical axial coordinate, sd-standardised
        A, _names = None, None
        spec = importlib.util.spec_from_file_location(
            "t2_h_n2_a2c_probe", str(PROJECT_ROOT / "scripts/t2_h_n2_a2c.py"))
        # avoid importing the whole A2C module (it has a __main__); re-derive a1 locally
        Z, _c, _r, _V = SF.canonicalize(C)
        axis = np.sort(Z[:, 0])
        u = (axis - axis.mean()) / max(axis.std(), 1e-12)      # sd = 1 by construction
        # broadcast the 1-D field to the panel so the amplitude is in mean-units
        field = np.repeat(u[:, None], len(panel), axis=1).astype(np.float64)

        truth_amp = truth_spatial_amplitude(true["X"], true["C"])
        print(f"   truth spatial amplitude: sqrt(median semivar)="
              f"{truth_amp['sqrt_median']:.5f}", flush=True)

        base_f = base.astype(np.float64)

        def ev(Xm: np.ndarray) -> dict[str, float]:
            return {
                "neighborhood_mmd": float(T2_METRICS.neighborhood_mmd(
                    Xm, C, true["X"], true["C"], k=15, n=2000)),
                "mmd_u": float(mmd_unbiased(Xm, true["X"], n=2000, seed=0)),
                "energy_distance": float(energy_distance(Xm, true["X"])),
                "variogram": float(variogram_score(Xm, true["X"])),
            }

        base_m = ev(base_f)
        curve = []
        for a in AMPS:
            Xa = base_f + a * field
            np.clip(Xa, 0, None, out=Xa)
            m = ev(Xa)
            d_nmmd = 100.0 * (m["neighborhood_mmd"] - base_m["neighborhood_mmd"]) / base_m["neighborhood_mmd"]
            d_mmd = 100.0 * (m["mmd_u"] - base_m["mmd_u"]) / base_m["mmd_u"]
            curve.append({"amplitude": a, "metrics": m,
                          "nmmd_delta_pct": d_nmmd, "mmd_u_delta_pct": d_mmd,
                          "within_band": bool(abs(d_nmmd) <= M0_BAND_PCT)})
            print(f"   a={a:<5} nmmd={m['neighborhood_mmd']:.6f} ({d_nmmd:+.1f}%) "
                  f"mmd_u={m['mmd_u']:.5f} ({d_mmd:+.1f}%) "
                  f"band={'ok' if abs(d_nmmd) <= M0_BAND_PCT else 'OUT'}", flush=True)

        ok = [c for c in curve[1:] if c["within_band"]]
        a_dmg = min((c["amplitude"] for c in curve[1:] if not c["within_band"]), default=None)
        smallest_ok = max((c["amplitude"] for c in ok), default=None)
        payload["boards"][board] = {
            "m0_active_on_this_board": cfg["m0_active"],
            "incumbent_verification": verify,
            "truth_spatial_amplitude": truth_amp,
            "base_metrics": base_m,
            "curve": curve,
            "amplitudes_within_band": [c["amplitude"] for c in ok],
            "smallest_acceptable_amplitude": smallest_ok,
            "first_damaging_amplitude": a_dmg,
            "verdict": ("NO_ACCEPTABLE_AMPLITUDE_IN_LADDER__additive spatial contrast unusable at any "
                        "tested amplitude" if not ok else
                        f"accept band up to a={smallest_ok}; first damage at a={a_dmg}"),
            "wall_seconds": time.time() - started,
        }
        print(f"   verdict: {payload['boards'][board]['verdict']}", flush=True)

    payload["pre_declared_decision_rule"] = (
        "If the ladder contains no amplitude that keeps neighborhood_mmd within +-5% of the incumbent, "
        "the additive-spatial-contrast family is unusable on that board at any tested amplitude and must be "
        "closed. If a band exists, a future lane may use it ONLY with an amplitude derived from the truth-side "
        "statistic reported in truth_spatial_amplitude, never from a fixed sd=1 normalisation. "
        "Either outcome authorises no new lane by itself."
    )
    payload["wall_seconds"] = time.time() - t0
    (OUT_DIR / "l008_amplitude_damage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT_DIR/'l008_amplitude_damage.json'} ({payload['wall_seconds']:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
