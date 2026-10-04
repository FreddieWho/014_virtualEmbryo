#!/usr/bin/env python3
"""T2 · 边际分布操作 → 官方子分响应面（只读预执行探针）。

为什么做
--------
三次「均值场 + 加性空间对比度」路线失败（`E-N1 SBL` +1085~1164%、
`H-N2 A2C` +78~97%、`E-I1 TCI` +2379~2568%），且 L-008 幅度探针已证明该族
在两板上**任何幅度都不可用**（可接受带 `a ≤ 0.05`，真值幅度超上限 24–31 倍，
`D-20260927-T2L008-001`）。T2 的搜索空间因此收窄到**唯一**方向：**作用在
边际分布上的机制**。

这一判断与唯一的服务器正向验证证据一致：`B4-T2-R2` 的 heart_interp **+4.79**
来自**组成重采样**，`G1-T2-R2` 的 heart_extrap **+0.11** 来自**收缩**——两者都
是边际操作，**没有一条被服务器确认有效的 T2 路线是靠空间结构赢的**。

本探针回答
----------
在现役 L2 桥（几何/行序逐字节冻结）上，**两个边际旋钮各自**如何推动 8 个官方
子分？哪些子分**还能被边际操作推动**、哪些**根本动不了**（几何量）？

设计（跑前定死）
----------------
* **两条独立的一维阶梯**（不是二维网格）：每条阶梯只扫一个旋钮。
  1. `COMP_INTENSITY` `c ∈ (0, 0.25, 0.5, 0.75, 1.0)`：把每型目标计数从现役的
     计数线性插值回**父版本的原始计数**。`c = 0` 必须逐位复现现役行序（脚本内
     断言）；`c = 1` 即不做组成重采样。
  2. `SHRINK_INTENSITY` `s ∈ (0, 0.25, 0.5, 0.75, 1.0)`：`X = (1-s)·X_incumbent
     + s·(每型均值)`。`s = 1` 即「钉死在每型均值」的场（G1-T2-R2 的机制）。
* **旋钮是唯一被扫的量**：几何、行序、panel、pseudo-target、seed 全部冻结。
* 报告**全部 8 个官方子分**（以 `data/gene_panel/index.json` 的 anchors 为准），
  而不只是主指标——因为边际操作可能只动其中几个。

预声明判定
----------
* **几何类子分**（`d2_shape`、`occupancy_dice`）：几何冻结 ⇒ 预期**恒定**。若实测
  有变化，说明实现破坏了 byte-identity，属实现缺陷而非发现。
* **可利用集** = 同时满足：(a) 随旋钮**单调**变化；(b) 变化方向与该旋钮的语义
  一致。下一条 lane 只允许针对可利用集立项，且旋钮取值必须**事前声明**。
* 本探针**不授权任何新 lane**，只产出响应面这一个事实。

诚实标注
--------
* 全部读数在 pseudo-target（E7.25 / E8.75 观测期 stage）上计算，**部分循环**；
  **绝对水平不可解释**，只有「同一基座下同一子分随旋钮的相对变化」有效。
* 另有一条已知事实必须随附：验证 V1（`D-20260927-T2VALIDATE-001`）显示
  `neighborhood_mmd` 在 **embryo 板与服务器强反向（+0.833）**，该板的 5% 规则已
  停用、`d2_shape` 在两板均与服务器反向。故本响应面**只用于筛选方向，不用于
  预测服务器增益**。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

# This script lives in scripts/gate/ -> project root is parents[2].
PROJECT_ROOT = Path(__file__).resolve().parents[2]
for _p in (PROJECT_ROOT, PROJECT_ROOT / "scripts", PROJECT_ROOT / "third_party/veckit"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import importlib.util  # noqa: E402
import types  # noqa: E402

import anndata as ad  # noqa: E402

OUT_DIR = PROJECT_ROOT / "artifacts/gate/T2_MARGINAL_RESPONSE-20260927-v1"

# ---- the two swept knobs (each a 1-D ladder; NOT a 2-D grid) ----
COMP_LADDER: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
SHRINK_LADDER: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)

BRIDGE_SEED = 20260904
SEED = 20260927

BOARDS: dict[str, dict[str, Any]] = {
    "T2_embryo_val_interp": {
        "index_key": "T2:embryo:val_interp",
        "panel": "data/gene_panel/T2__embryo__val_interp.genes.txt",
        "left": "data/E7.25.h5ad", "right": "data/E8.0.h5ad", "lam": 1.0 / 3.0,
        "bridge_parent": "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
        "incumbent": "submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        "pseudo_target": "data/E7.25.h5ad",
    },
    "T2_heart_val_interp": {
        "index_key": "T2:heart:val_interp",
        "panel": "data/gene_panel/T2__heart__val_interp.genes.txt",
        "left": "data/E8.25_late.h5ad", "right": "data/E8.75.h5ad", "lam": 0.5,
        "bridge_parent": "submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad",
        "incumbent": "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        "pseudo_target": "data/E8.75.h5ad",
    },
}

# official anchors per board (authoritative metric list)
OFFICIAL = json.loads((PROJECT_ROOT / "data/gene_panel/index.json").read_text(encoding="utf-8"))


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
from common.shape_metrics import d2_distance, occupancy_dice, scale_log_ratio, sliced_wasserstein  # noqa: E402


def _first_number(v: Any) -> float:
    """shape_metrics returns (value, extra) for some metrics; take the first element."""
    return float(v[0]) if isinstance(v, tuple) else float(v)


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


def bridge_counts(cfg: dict[str, Any], panel: list[str], ptypes: np.ndarray) -> tuple[dict, dict]:
    """Recompute the incumbent's target counts and the parent's original counts."""
    XL, XR = load(cfg["left"], panel), load(cfg["right"], panel)
    pL = {s: float((XL["t"] == s).sum()) / len(XL["t"]) for s in set(XL["t"].tolist())}
    pR = {s: float((XR["t"] == s).sum()) / len(XR["t"]) for s in set(XR["t"].tolist())}
    pstates = sorted(set(ptypes.tolist()))
    mL, mR = means_by_type(XL["X"], XL["t"]), means_by_type(XR["X"], XR["t"])
    shared = sorted(set(pstates) & set(mL) & set(mR))
    pP = {s: float((ptypes == s).sum()) / len(ptypes) for s in pstates}
    raw = {}
    for s in pstates:
        raw[s] = ((1.0 - cfg["lam"]) * pL.get(s, 0.0) + cfg["lam"] * pR.get(s, 0.0)) if s in shared \
            else 0.5 * pP[s] + 0.5 * pL.get(s, 0.0)
    tot = sum(raw.values())
    raw = {s: v / tot for s, v in raw.items()}
    inc_counts = {s: int(raw[s] * len(ptypes)) for s in pstates}
    deficit = len(ptypes) - sum(inc_counts.values())
    rema = sorted(pstates, key=lambda s: (raw[s] * len(ptypes) - inc_counts[s], s), reverse=True)
    for i in range(deficit):
        inc_counts[rema[i % len(rema)]] += 1
    parent_counts = {s: int(pP[s] * len(ptypes)) for s in pstates}
    return inc_counts, parent_counts


def draw_rows(counts: dict, ptypes: np.ndarray) -> np.ndarray:
    """Deterministic per-type row draw; identical code path to the bridge."""
    rng = np.random.default_rng(BRIDGE_SEED)
    chosen = []
    for s in sorted(counts):
        pool = np.flatnonzero(ptypes == s)
        k = counts[s]
        if k <= len(pool):
            sel = (np.sort(pool[rng.choice(len(pool), size=k, replace=False)])
                   if k < len(pool) else np.sort(pool))
        else:
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=True)])
        chosen.extend(sel.tolist())
    return np.asarray(chosen, dtype=np.int64)


def rename(chosen: np.ndarray, pnames: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for i in chosen.tolist():
        nm = pnames[i]
        k = seen.get(nm, 0)
        out.append(nm if k == 0 else f"{nm}__dup{k}")
        seen[nm] = k + 1
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    payload: dict[str, Any] = {
        "schema": "ve.t2.marginal-response.v1",
        "atom": "T2-MARGINAL-RESPONSE-20260927-v1",
        "purpose": "measure how the 8 official T2 subscores respond to the two MARGINAL knobs "
                   "on top of the frozen incumbent L2 bridge",
        "knobs": {"COMP_INTENSITY": list(COMP_LADDER), "SHRINK_INTENSITY": list(SHRINK_LADDER)},
        "not_a_grid": "two independent 1-D ladders; COMP and SHRINK are never swept together",
        "boards": {},
        "declarations": [
            "READ-ONLY probe: no candidate, no h5ad output, no submission, no INDEX row, no upload",
            "geometry, row order, panel, pseudo-target and seed are frozen; only the knob moves",
            "local readings are NOT server predictions; per D-20260927-T2VALIDATE-001 the primary "
            "metric is server-ANTAGONISTIC on the embryo board and d2_shape is server-antagonistic on both",
            "this probe authorises no new lane",
        ],
    }

    for board, cfg in BOARDS.items():
        started = time.time()
        panel = [l.strip() for l in (PROJECT_ROOT / cfg["panel"]).read_text().splitlines() if l.strip()]
        metrics_official = sorted(OFFICIAL[cfg["index_key"]]["anchors"])

        P = ad.read_h5ad(PROJECT_ROOT / cfg["bridge_parent"])
        pnames = [str(v) for v in P.obs_names]
        ptypes = np.asarray(P.obs["celltype"].astype(str))
        XP = dense(P.X).astype(np.float64)
        pC = np.asarray(P.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        P.file.close()

        parent_row_of_name_early = None  # set right after pnames is known
        inc = ad.read_h5ad(PROJECT_ROOT / cfg["incumbent"], backed="r")
        inc_names = [str(v) for v in inc.obs_names]
        inc_C = np.asarray(inc.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        inc_pos = [str(v) for v in inc.var_names]
        parent_row_of_name_early = {n: i for i, n in enumerate(pnames)}
        inc.file.close()
        ipos = np.array([inc_pos.index(g) for g in panel])
        X_inc = dense(inc.X[:, ipos]).astype(np.float64)      # incumbent, final row order

        inc_counts, parent_counts = bridge_counts(cfg, panel, ptypes)
        total = len(ptypes)

        # self-check: c=0 must reproduce the incumbent's row selection byte-for-byte
        chk = draw_rows(inc_counts, ptypes)
        verify = {
            "c0_obs_names_match_incumbent": bool(rename(chk, pnames) == inc_names),
            # cast BOTH sides to float32: the incumbent artifact stores spatial_3D as float32,
            # so comparing a float64 parent read against it would be a false positive.
            "c0_coords_match_incumbent": bool(
                np.array_equal(np.asarray(pC[chk], dtype=np.float32),
                               np.asarray(inc_C, dtype=np.float32))),
        }
        print(f"== {board}  verify={json.dumps(verify)}", flush=True)

        true = load(cfg["pseudo_target"], panel)
        ref = load(cfg["left"], panel)          # the scoring reference for this board
        # load T2/metrics_v2.py the same way the locked scorer does (it reuses T1/T2
        # metrics modules via the "_reuse" stand-in already registered above)
        def _load_mod(name: str, path: Path):
            spec = importlib.util.spec_from_file_location(name, str(path))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod

        MV2 = _load_mod("metrics_v2_probe", PROJECT_ROOT / "third_party/veckit/T2/metrics_v2.py")
        t1_metrics_probe = sys.modules["t1_metrics"]   # registered by _load_veckit_t2()

        def ev(Xm: np.ndarray, C: np.ndarray, pred_ct: np.ndarray) -> dict[str, float]:
            """The OFFICIAL T2 panel, via the same entry point the locked scorer uses."""
            out = MV2.score_task2_v2(
                np.asarray(Xm, dtype=np.float64), np.asarray(C, dtype=np.float32),
                np.asarray(pred_ct, dtype=str), true["X"], true["C"], true["t"],
                ref["X"], seed=SEED)
            # the official panel returns None for de_score when it is non-finite
            # (metrics_v2 rounds it only if finite). Keep None as an explicit "undefined"
            # rather than coercing, and exclude undefined metrics from the verdicts.
            return {k: (None if out[k] is None else float(out[k]))
                    for k in metrics_official if k in out}

        inc_types = np.array([ptypes[parent_row_of_name_early[n.split("__dup")[0]]]
                              for n in inc_names])
        base = ev(X_inc, inc_C, inc_types)
        print(f"   base(incumbent): " + " ".join(
            f"{k}={('UNDEF' if base[k] is None else format(base[k], '.5f'))}"
            for k in metrics_official), flush=True)

        def rel(new: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for k in new:
                if new[k] is None or old.get(k) is None or abs(old[k]) <= 1e-12:
                    out[k] = None
                else:
                    out[k] = 100.0 * (new[k] - old[k]) / abs(old[k])
            return out

        curves: dict[str, Any] = {}

        # ---- knob 1: composition intensity (changes the row multiset) ----
        comp_pts = []
        for c in COMP_LADDER:
            counts = {s: int(round((1.0 - c) * inc_counts[s] + c * parent_counts[s])) for s in inc_counts}
            # fix the total by adding/removing on the largest-|delta| types (same convention as the bridge)
            diff = total - sum(counts.values())
            if diff:
                order = sorted(counts, key=lambda s: ((1.0 - c) * inc_counts[s]
                                                       + c * parent_counts[s] - counts[s], s), reverse=True)
                i = 0
                while diff != 0:
                    s = order[i % len(order)]
                    step = 1 if diff > 0 else -1
                    counts[s] = max(0, counts[s] + step)
                    diff -= step
                    i += 1
            comp_pts.append({"intensity": c, "counts_total": int(sum(counts.values())),
                             "counts": {str(s): int(v) for s, v in counts.items()}})
        # the expression for a given row multiset is the incumbent's own expression re-indexed,
        # which keeps the value assignment identical and isolates the COMPOSITION effect only.
        # row pools for COMP are the INCUMBENT's own rows of each type, so that changing the
        # counts preserves the per-type value multiset and isolates composition.
        inc_pools = {s: np.flatnonzero(inc_types == s) for s in np.unique(inc_types)}
        inc_counts_eff = {str(s): int(len(p)) for s, p in inc_pools.items()}
        for pt in comp_pts:
            rng = np.random.default_rng(BRIDGE_SEED)
            sel = []
            for s in sorted(inc_pools):
                pool = inc_pools[s]
                k = pt["counts"][s]
                sel.extend((np.sort(pool[rng.choice(len(pool), size=k, replace=False)])
                            if k < len(pool) else (np.sort(pool) if k == len(pool)
                                else np.sort(pool[rng.choice(len(pool), size=k, replace=True)]))).tolist())
            sel = np.asarray(sel, dtype=np.int64)
            Xc = np.ascontiguousarray(X_inc[sel], dtype=np.float64)
            Cc = np.ascontiguousarray(inc_C[sel], dtype=np.float32)
            sel_ct = inc_types[sel]
            if pt["intensity"] == 0.0:
                assert np.array_equal(Xc, X_inc), "COMP c=0 must reproduce the incumbent exactly"
                assert np.array_equal(Cc, np.asarray(inc_C, dtype=np.float32)), \
                    "COMP c=0 must reproduce the incumbent coords exactly"
            m = ev(Xc, Cc, sel_ct)
            pt["metrics"] = m
            pt["rel_vs_incumbent_pct"] = rel(m, base)
            print(f"   COMP c={pt['intensity']:<5} " + " ".join(
                f"{k}={('UNDEF' if m[k] is None else format(m[k], '.5f'))}"
                for k in metrics_official), flush=True)
        curves["COMP_INTENSITY"] = comp_pts

        # ---- knob 2: shrinkage intensity (value operation, row order untouched) ----
        # the incumbent's obs names carry the parent row name (the __dup suffix preserves order of
        # first appearance), so the parent row index -> parent celltype is recoverable exactly.
        mu_inc = means_by_type(X_inc, inc_types)

        shrink_pts = []
        for s in SHRINK_LADDER:
            Xs = np.empty_like(X_inc)
            for t in np.unique(inc_types):
                rows = inc_types == t
                Xs[rows] = (1.0 - s) * X_inc[rows] + s * mu_inc[str(t)][None, :]
            np.clip(Xs, 0, None, out=Xs)
            m = ev(np.ascontiguousarray(Xs), inc_C, inc_types)
            shrink_pts.append({"intensity": s, "metrics": m, "rel_vs_incumbent_pct": rel(m, base)})
            print(f"   SHRINK s={s:<5} " + " ".join(
                f"{k}={('UNDEF' if m[k] is None else format(m[k], '.5f'))}"
                for k in metrics_official), flush=True)
        curves["SHRINK_INTENSITY"] = shrink_pts

        # ---- pre-declared verdict ----
        geom = [k for k in metrics_official if k in ("d2_shape", "occupancy_dice",
                                                     "sliced_wasserstein", "scale_log_ratio")]
        geom_frozen_shrink = all(
            (pt["rel_vs_incumbent_pct"].get(k) is not None
             and abs(pt["rel_vs_incumbent_pct"][k]) < 1e-9)
            for pt in curves["SHRINK_INTENSITY"] for k in geom)
        geom_frozen = all(
            (pt["rel_vs_incumbent_pct"].get(k) is not None
             and abs(pt["rel_vs_incumbent_pct"][k]) < 1e-9)
            for pts in curves.values() for pt in pts for k in geom)
        exploitable = {}
        for k in metrics_official:
            if k in geom:
                continue
            for knob, pts in curves.items():
                if any(pt["metrics"].get(k) is None for pt in pts):
                    continue                      # undefined at this pseudo-target: not exploitable
                series = [pt["metrics"][k] for pt in pts]
                deltas = [series[i + 1] - series[i] for i in range(len(series) - 1)]
                nz = [d for d in deltas if abs(d) > 1e-12]
                monotone = bool(nz) and (all(d > 0 for d in nz) or all(d < 0 for d in nz))
                if monotone:
                    exploitable.setdefault(k, []).append(
                        {"knob": knob, "span_pct": 100.0 * (series[-1] - series[0]) / abs(series[0])})

        payload["boards"][board] = {
            "incumbent_verification": verify,
            "official_metrics": metrics_official,
            "geometry_only_metrics": geom,
            "base_metrics": base,
            "curves": curves,
            "geometry_metrics_frozen_under_SHRINK": bool(geom_frozen_shrink),
            "geometry_metrics_frozen_under_COMP": bool(geom_frozen),
            "geometry_note": "geometry metrics are frozen under SHRINK because the row order is "
                             "untouched; under COMP the row multiset changes, so the point cloud "
                             "changes too -- that confound is inherent to composition resampling and "
                             "is NOT a byte-identity failure (c=0 is asserted to reproduce the "
                             "incumbent exactly).",
            "undefined_metrics_at_this_pseudo_target": [
                k for k in metrics_official if base.get(k) is None],
            "monotone_exploitable_subscores": exploitable,
            "verdict": (f"exploitable (monotone) subscores: "
                        f"{ {k: [e['knob'] for e in v] for k, v in exploitable.items()} }"
                        if exploitable else "NO monotone exploitable subscore"),
            "wall_seconds": time.time() - started,
        }
        print(f"   verdict: {payload['boards'][board]['verdict']}", flush=True)
        print(f"   geometry frozen as predicted: {geom_frozen}", flush=True)

    payload["wall_seconds"] = time.time() - t0
    (OUT_DIR / "marginal_response.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT_DIR/'marginal_response.json'} ({payload['wall_seconds']:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
