#!/usr/bin/env python3
"""T2 验证 V1：本地判据 vs 服务器分数，全历史已评分候选。

目的
----
用户指令（2026-09-27）："我们测试一次我们的本地判据是否是成立的和服务器端可浮现的"。

本脚本回答一个此前只有零散轶事、没有系统答案的问题：**本项目的本地判据
（`neighborhood_mmd` 上的 5% 三分类、分布侧会签、结构性失败签名）在全部历史
已评分 T2 候选上，与服务器 board 分的实际关系是什么？**

为什么现在值得做：三个已知的本地门失效方向（extrap 空间族、B4-T2-R2 的
``mmd_u``、G1-T2-R2 收缩）此前都是逐个发现的，从来没有被合到一起量化。M0 冻结的
5% 判据选在 `neighborhood_mmd` 上，闸门已确认它零噪声（0.00% 相对极差），但
"零噪声"不等于"有预测力"——这是两件事，本脚本区分它们。

方法与它的边界
--------------
* **只读**。不训练、不建候选、不改任何已评分或候选文件、不上传。
* 全部本地指标在**各 board 冻结的 pseudo-target 与 seed** 上重算，与该候选
  当初被打分时的口径一致。pseudo-target 是观测期 stage，**不是隐藏目标**；
  因此本脚本**不预测任何未来服务器分**，只回答"历史上本地读数与服务器读数
  是否同向"。
* 样本量诚实标注：每 board 的候选数、以及其中**有多少条与父版本构成可比对照**
  （很多候选是不同族之间的比较，不是迭代父子关系，把它们混在一起算相关会失真）。
* 报告四个层面：(a) 排名相关（Spearman，按板 + 合并）；(b) 方向一致率；
  (c) 5% 判据的混淆矩阵（按 M0 三分类）；(d) 哪些指标是**反向**的。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for _p in (PROJECT_ROOT, PROJECT_ROOT / "third_party/veckit"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from common.core_metrics import (  # noqa: E402
    energy_distance,
    mmd_unbiased,
    variogram_score,
)
from common.shape_metrics import (  # noqa: E402
    d2_distance,
    occupancy_dice,
    sliced_wasserstein,
)


def _load_t2_metrics():
    """Load veckit T2/metrics.py without touching its data.py.

    Reuses score_h5ad's own loader verbatim: T2/metrics.py does
    ``from _reuse import t1_metrics``, and the real _reuse.py eagerly loads data.py
    (which references held-out data paths). score_h5ad registers a clean stand-in
    for that reason; we borrow the same mechanism rather than reimplementing it.
    """
    import importlib.util
    import types

    veckit_root = PROJECT_ROOT / "third_party/veckit"

    def _load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    t1_metrics = _load("t1_metrics", veckit_root / "T1" / "metrics.py")
    reuse = types.ModuleType("_reuse")
    reuse.t1_metrics = t1_metrics
    sys.modules["_reuse"] = reuse
    t2_metrics = _load("t2_metrics", veckit_root / "T2" / "metrics.py")
    sys.modules["metrics"] = t2_metrics
    return t2_metrics


T2_METRICS = _load_t2_metrics()

OUT_DIR = PROJECT_ROOT / "artifacts/gate/T2_VALIDATE_V1_LOCAL_VS_SERVER-20260927-v1"

# 各 board 冻结的 pseudo-target / reference / seed（沿用 registry 既有记录）
# 注意：index_key 是 submissions/INDEX.tsv 里的写法（冒号），与本脚本内部键（下划线）不同。
BOARDS: dict[str, dict[str, Any]] = {
    "T2_embryo_val_interp": {
        "index_key": "T2:embryo:val_interp",
        "target": "data/E7.25.h5ad", "reference": "data/E6.75.h5ad", "seed": 20260830,
    },
    "T2_heart_val_interp": {
        "index_key": "T2:heart:val_interp",
        "target": "data/E8.75.h5ad", "reference": "data/E8.25_late.h5ad", "seed": 20260830,
    },
    "T2_heart_val_extrap": {
        "index_key": "T2:heart:val_extrap",
        "target": "data/E9.5.h5ad", "reference": "data/E8.75.h5ad", "seed": 20260830,
    },
}

# 与「什么都不改」基线同几何的对照：M0 §3.1 的 5% 判据以父版本为基准
BASELINE: dict[str, str] = {
    "T2_embryo_val_interp": "submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad",
    "T2_heart_val_interp": "submissions/scored/baseline-001/T2_heart_val_interp/submission.h5ad",
    "T2_heart_val_extrap": "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad",
}

N_MMD = 2000
# 各指标的已知种子噪声带（闸门 D-20260927-T2GATES-001 §5 实测，相对极差）。
# “零噪声”只说明重复测量稳定，**不说明它对输入敏感**——本脚本要验证的正是后者。
NOISE_BAND = {
    "neighborhood_mmd": 0.0001,   # 0.00% —— 重复测量完全确定
    "variogram": 0.0418,
    "d2_shape": 0.0450,
    "occupancy_dice": 0.0301,
    "sliced_wasserstein": 0.0696,
    "mmd_u": 0.0900,
    "energy_distance": 0.0696,
}
PRIMARY = "neighborhood_mmd"
M0_PROMOTE_PCT = 5.0
METRIC_DIRECTION = {  # lower-better 与否
    "neighborhood_mmd": "lower", "variogram": "higher", "mmd_u": "higher",
    "energy_distance": "lower", "d2_shape": "lower", "occupancy_dice": "higher",
    "sliced_wasserstein": "lower",
}


def read_index() -> list[dict[str, str]]:
    path = PROJECT_ROOT / "submissions/INDEX.tsv"
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    with open(path, newline="", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if header is None:
                header = parts
                continue
            rows.append(dict(zip(header, parts)))
    return rows


def load_X(path: Path) -> np.ndarray | None:
    X, _ = _load_XC(path)
    return X


def _load_XC(path: Path) -> tuple[np.ndarray | None, np.ndarray | None]:
    if not path.is_file():
        return None, None
    import anndata as ad

    try:
        adata = ad.read_h5ad(path)
    except Exception as exc:  # noqa: BLE001
        print(f"    [read fail] {path.name}: {exc}")
        return None, None
    X = adata.X
    X = np.asarray(X.todense()) if hasattr(X, "todense") else np.asarray(X)
    C = None
    if "spatial_3D" in adata.obsm:
        C = np.asarray(adata.obsm["spatial_3D"], dtype=np.float32)[:, :3]
    return np.asarray(X, dtype=np.float64), C


def _nmmd(pred_X: np.ndarray, pred_C: np.ndarray, true_X: np.ndarray, true_C: np.ndarray) -> float:
    """Official veckit T2 neighborhood_mmd (coupling-free, lower-better)."""
    if pred_C is None or true_C is None:
        return float("nan")
    return float(T2_METRICS.neighborhood_mmd(pred_X, pred_C, true_X, true_C, k=15, n=2000))


def _first_number(value: Any) -> float:
    """shape_metrics returns (value, extra) for some metrics; take the first element."""
    if isinstance(value, tuple):
        return float(value[0])
    return float(value)


def spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3:
        return None
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    rx = np.argsort(np.argsort(x)).astype(np.float64)
    ry = np.argsort(np.argsort(y)).astype(np.float64)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_index()
    payload: dict[str, Any] = {
        "schema": "ve.t2.validate-v1-local-vs-server.v1",
        "atom": "T2-VALIDATE-V1-LOCAL-VS-SERVER-20260927-v1",
        "question": "are the project's local criteria actually predictive of server board scores, across ALL historically scored T2 candidates?",
        "primary_metric": PRIMARY,
        "m0_promote_threshold_pct": M0_PROMOTE_PCT,
        "noise_band_rel": NOISE_BAND,
        "boards": {},
        "declarations": [
            "read-only: no candidate, no h5ad, no submission, no INDEX row, no upload",
            "pseudo-target stages are observed source stages, NOT hidden targets: this script does NOT predict future server scores, it only measures historical local-vs-server agreement",
            "no server was queried; all server numbers are transcribed from reports/SERVER_SCORE_REGISTRY.md as already registered",
            "candidates from different mechanism families are not iteration parent-child pairs; pooled correlations mixing them are reported separately and flagged as weak evidence",
        ],
    }

    registry = (PROJECT_ROOT / "reports/SERVER_SCORE_REGISTRY.md").read_text(encoding="utf-8")

    for board, spec in BOARDS.items():
        started = time.time()
        base_X, base_C = _load_XC(PROJECT_ROOT / BASELINE[board])
        if base_X is None or base_C is None:
            payload["boards"][board] = {"status": "BASELINE_MISSING_OR_NO_COORDS"}
            continue
        true_X, true_C = _load_XC(PROJECT_ROOT / spec["target"])
        if true_X is None or true_C is None or true_X.shape[1] != base_X.shape[1]:
            payload["boards"][board] = {"status": "TARGET_OR_GENE_MISMATCH"}
            continue

        def metrics(pred_X: np.ndarray, pred_C: np.ndarray) -> dict[str, float]:
            return {
                PRIMARY: _nmmd(pred_X, pred_C, true_X, true_C),
                "variogram": float(variogram_score(pred_X, true_X)),
                "mmd_u": float(mmd_unbiased(pred_X, true_X, n=N_MMD, seed=0)),
                "energy_distance": float(energy_distance(pred_X, true_X)),
                # 几何敏感族：只读坐标，对“表达不变、几何变”的候选会直接反应
                "d2_shape": float(d2_distance(pred_C, true_C, seed=spec["seed"])),
                "occupancy_dice": float(occupancy_dice(pred_C, true_C, seed=spec["seed"])[0]),
                "sliced_wasserstein": float(_first_number(sliced_wasserstein(pred_C, true_C, seed=spec["seed"]))),
            }

        base_m = metrics(base_X, base_C)
        print(f"== {board}  baseline {PRIMARY}={base_m[PRIMARY]:.6f}  "
              f"d2_shape={base_m['d2_shape']:.6f}", flush=True)

        scored = [
            r for r in rows
            if r.get("board") == spec["index_key"] and r.get("server_score") not in (None, "")
        ]
        entries: list[dict[str, Any]] = []
        for r in scored:
            path = PROJECT_ROOT / r["path"]
            pred_X, pred_C = _load_XC(path)
            if pred_X is None:
                entries.append({"version": r["version"], "group": r["submission_group"],
                                "status": "FILE_MISSING_OR_UNREADABLE", "path": r["path"]})
                continue
            if pred_C is None:
                entries.append({"version": r["version"], "group": r["submission_group"],
                                "status": "NO_COORDS", "path": r["path"]})
                continue
            if pred_X.shape[1] != true_X.shape[1]:
                entries.append({"version": r["version"], "group": r["submission_group"],
                                "status": "GENE_COUNT_MISMATCH", "pred_genes": int(pred_X.shape[1]),
                                "true_genes": int(true_X.shape[1]), "path": r["path"]})
                continue
            m = metrics(pred_X, pred_C)
            deg = (m[PRIMARY] - base_m[PRIMARY]) / base_m[PRIMARY] * 100.0
            m0_class = (
                "IMPROVE" if deg <= -M0_PROMOTE_PCT
                else "TIER" if abs(deg) <= M0_PROMOTE_PCT
                else "DEGRADE"
            )
            entries.append({
                "version": r["version"],
                "group": r["submission_group"],
                "method": r.get("method", ""),
                "status": "OK",
                "path": r["path"],
                "sha256": r.get("sha256", ""),
                "server_score": float(r["server_score"]),
                "local": m,
                "degradation_pct_vs_baseline": deg,
                "m0_class": m0_class,
                "local_rel_vs_baseline_pct": {
                    k: (m[k] - base_m[k]) / abs(base_m[k]) * 100.0 if base_m[k] else float("nan")
                    for k in m
                },
            })
            print(f"   {r['version']:<5} {r['submission_group']:<14} "
                  f"server={float(r['server_score']):>6.2f}  "
                  f"nmmd={m[PRIMARY]:.6f}({m[PRIMARY] - base_m[PRIMARY]:+.2e})  "
                  f"{m0_class:<8} d2={m['d2_shape']:.5f} occ={m['occupancy_dice']:.4f} "
                  f"mmd_u={m['mmd_u']:.5f} vario={m['variogram']:.5f}", flush=True)

        ok = [e for e in entries if e.get("status") == "OK"]
        analysis: dict[str, Any] = {
            "index_board_key": spec["index_key"],
            "n_candidates_with_server_score": len(scored),
            "n_evaluated_ok": len(ok),
            "pseudo_target": spec["target"],
            "pseudo_reference": spec["reference"],
            "baseline": {"path": BASELINE[board], "local": base_m},
            "entries": entries,
        }
        if len(ok) >= 3:
            srv = [e["server_score"] for e in ok]
            analysis["spearman_vs_server"] = {
                k: spearman([e["local"][k] for e in ok], srv) for k in NOISE_BAND
            }
            # 方向一致：本地相对基线的改善方向 vs 服务器相对该板最高候选的方向
            best = max(srv)
            agree = sum(
                1 for e in ok
                if (e["local"][PRIMARY] < base_m[PRIMARY] and e["server_score"] >= best - 1e-9)
                or (e["local"][PRIMARY] > base_m[PRIMARY] and e["server_score"] < best + 1e-9)
            )
            analysis["direction_agreement_vs_board_best"] = {
                "n": len(ok), "agree": agree,
                "rate": round(agree / len(ok), 4),
            }
            analysis["m0_class_counts"] = {
                c: sum(1 for e in ok if e["m0_class"] == c) for c in ("IMPROVE", "TIER", "DEGRADE")
            }
            # 混淆：M0 判 DEGRADE 的候选，服务器实际是否也低于该板最优
            deg_rows = [e for e in ok if e["m0_class"] == "DEGRADE"]
            if deg_rows:
                analysis["m0_degrade_but_server_tied_or_better"] = [
                    {"version": e["version"], "server_score": e["server_score"],
                     "degradation_pct": round(e["degradation_pct_vs_baseline"], 3)}
                    for e in deg_rows if e["server_score"] >= best - 0.1
                ]
        payload["boards"][board] = analysis
        print(f"-- {board}: {len(ok)}/{len(scored)} evaluated in {time.time() - started:.1f}s", flush=True)

    # 合并（明确标注为弱证据：跨族混合）
    all_ok = [
        dict(e, board=b)
        for b, bd in payload["boards"].items()
        if isinstance(bd, dict)
        for e in bd.get("entries", [])
        if e.get("status") == "OK"
    ]
    if len(all_ok) >= 3:
        srv = [e["server_score"] for e in all_ok]
        payload["pooled_weak_evidence"] = {
            "note": "POOLS DIFFERENT MECHANISM FAMILIES AND DIFFERENT BOARDS; server scores are not comparable across boards, so this is reported only as a coarse sanity check, NOT as a validation result",
            "n": len(all_ok),
            "spearman_vs_server": {
                k: spearman([e["local"][k] for e in all_ok], srv) for k in NOISE_BAND
            },
        }

    payload["registry_mentions_registry_read"] = len(registry)
    (OUT_DIR / "validation_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {OUT_DIR / 'validation_v1.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
