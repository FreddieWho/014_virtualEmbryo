#!/usr/bin/env python3
"""Build tables and figures for the 2026-09-27 submitted-route synthesis.

Reads only submissions/INDEX.tsv and reports/SERVER_SUBMETRIC_REGISTRY.tsv.
Does not reconstruct board totals from rounded skills.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
DATA = OUT / "tables"

font_manager.fontManager.addfont(
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

BOARD_CN = {
    "T1:val": "T1 时间（心脏单细胞）",
    "T2:embryo:val_interp": "T2 胚胎插值",
    "T2:heart:val_interp": "T2 心脏插值",
    "T2:heart:val_extrap": "T2 心脏外推",
    "T3:gata4": "T3 基因敲除",
}
BOARD_SHORT = {
    "T1:val": "T1",
    "T2:embryo:val_interp": "T2胚胎",
    "T2:heart:val_interp": "T2心脏插值",
    "T2:heart:val_extrap": "T2心脏外推",
    "T3:gata4": "T3",
}

# Plain-language families. Versions are board-local.
FAMILIES = [
    ("T1:val", "复制上一阶段", ["v0001", "v0009", "v0010"]),
    ("T1:val", "均值位移/收缩", ["v0002", "v0003", "v0004", "v0011", "v0012", "v0013", "v0014", "v0018", "v0019", "v0020", "v0021"]),
    ("T1:val", "质量残差", ["v0005", "v0006"]),
    ("T1:val", "传输+生成器", ["v0007", "v0008", "v0022"]),
    ("T1:val", "神经动力/成熟度", ["v0015", "v0016", "v0017"]),
    ("T1:val", "分位数形状", ["v0023"]),
    ("T1:val", "密度比重采样", ["v0024"]),
    ("T1:val", "参数化分布运输", ["v0025"]),
    ("T1:val", "类型变化借用", ["v0026"]),
    ("T1:val", "显式零质量外推", ["v0027"]),
    ("T1:val", "对数倍率残差", ["v0028"]),
    ("T2:embryo:val_interp", "简单位移", ["v0001"]),
    ("T2:embryo:val_interp", "组织尺度", ["v0002", "v0003"]),
    ("T2:embryo:val_interp", "表达-坐标配对", ["v0004", "v0005"]),
    ("T2:embryo:val_interp", "点云配准", ["v0006"]),
    ("T2:embryo:val_interp", "表达桥+组成", ["v0009", "v0010"]),
    ("T2:heart:val_interp", "复制/中点", ["v0001", "v0002"]),
    ("T2:heart:val_interp", "组织尺度", ["v0003", "v0004"]),
    ("T2:heart:val_interp", "表达-坐标配对", ["v0005", "v0006", "v0009", "v0010", "v0011"]),
    ("T2:heart:val_interp", "点云配准", ["v0007"]),
    ("T2:heart:val_interp", "表达桥+组成", ["v0012", "v0013"]),
    ("T2:heart:val_extrap", "简单位移", ["v0001"]),
    ("T2:heart:val_extrap", "组织尺度", ["v0002", "v0003"]),
    ("T2:heart:val_extrap", "表达-坐标配对", ["v0004", "v0005"]),
    ("T2:heart:val_extrap", "收缩", ["v0011"]),
    ("T2:heart:val_extrap", "空间平滑", ["v0012", "v0013", "v0014", "v0015", "v0016"]),
    ("T3:gata4", "什么都不做", ["v0001", "v0008"]),
    ("T3:gata4", "照搬已知敲除", ["v0002", "v0003"]),
    ("T3:gata4", "带符号响应", ["v0004", "v0005"]),
    ("T3:gata4", "直接野生型改写", ["v0006", "v0007"]),
    ("T3:gata4", "敲除基因置零", ["v0009", "v0010"]),
    ("T3:gata4", "发育延迟剂量", ["v0011", "v0012"]),
    ("T3:gata4", "图/剂量传播", ["v0013", "v0014", "v0015", "v0016", "v0017", "v0018", "v0019", "v0020", "v0021", "v0022", "v0023", "v0024"]),
    ("T3:gata4", "空间平滑", ["v0025"]),
    ("T3:gata4", "非负修复", ["v0034", "v0035", "v0036"]),
    ("T3:gata4", "五路线新方法", ["v0042", "v0044", "v0046", "v0047", "v0048"]),
]

METRIC_CN = {
    "de_score": "差异基因找回",
    "de_direction": "变化方向",
    "mmd_u": "细胞群体分布",
    "variogram": "基因协变",
    "severity_slope": "响应强弱",
    "d2_shape": "整体形状",
    "occupancy_dice": "占位重叠",
    "scale_log_ratio": "大小缩放",
    "neighborhood_mmd": "邻里结构",
}


def load_index():
    rows = []
    with (ROOT / "submissions/INDEX.tsv").open(encoding="utf-8") as f:
        for rec in csv.DictReader(f, delimiter="\t"):
            raw = (rec.get("server_score") or "").strip()
            if not raw:
                continue
            rec["score"] = float(raw)
            rows.append(rec)
    return rows


def load_skills():
    data = {}
    with (ROOT / "reports/SERVER_SUBMETRIC_REGISTRY.tsv").open(encoding="utf-8") as f:
        for rec in csv.DictReader(f, delimiter="\t"):
            data[(rec["board"], rec["version"], rec["metric"])] = float(rec["skill"])
    return data


def main() -> None:
    scored = load_index()
    skills = load_skills()
    by_board = defaultdict(list)
    for rec in scored:
        by_board[rec["board"]].append(rec)

    baselines = {}
    bests = {}
    with (DATA / "all_scored.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["board", "version", "method", "score", "status", "family"])
        fam_of = {}
        for board, fam, vers in FAMILIES:
            for v in vers:
                fam_of[(board, v)] = fam
        for rec in scored:
            key = (rec["board"], rec["version"])
            w.writerow([
                rec["board"], rec["version"], rec["method"], f"{rec['score']:.2f}",
                rec["score_status"], fam_of.get(key, "未归类"),
            ])

    with (DATA / "family_best.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["board", "family", "best_version", "best_score", "baseline_score", "delta_vs_baseline", "n"])
        for board, fam, vers in FAMILIES:
            have = [r for r in by_board[board] if r["version"] in vers]
            if not have:
                continue
            base = min(by_board[board], key=lambda r: r["version"])
            # first submitted baseline is the lowest version id present, not min score
            base = sorted(by_board[board], key=lambda r: r["version"])[0]
            baselines[board] = base
            best = max(have, key=lambda r: r["score"])
            if board not in bests or best["score"] > bests[board]["score"]:
                bests[board] = best
            w.writerow([
                board, fam, best["version"], f"{best['score']:.2f}",
                f"{base['score']:.2f}", f"{best['score'] - base['score']:+.2f}", len(have),
            ])

    # highlighted submetric comparisons: winner vs a meaningful parent/baseline that has skills
    comparisons = [
        ("T1:val", "v0024", "v0023", "密度比重采样 vs 分位数父版本"),
        ("T1:val", "v0025", "v0023", "参数化运输 vs 分位数父版本"),
        ("T1:val", "v0026", "v0023", "类型借用 vs 分位数父版本"),
        ("T1:val", "v0027", "v0023", "显式零质量 vs 分位数父版本"),
        ("T1:val", "v0028", "v0023", "对数倍率 vs 分位数父版本"),
        ("T1:val", "v0023", "v0004", "分位数形状 vs 严格均值位移"),
        ("T1:val", "v0019", "v0004", "收缩微调 vs 严格均值位移"),
        ("T1:val", "v0022", "v0004", "全基因流匹配 vs 严格均值位移"),
        ("T2:embryo:val_interp", "v0010", "v0002", "表达桥 vs 组织尺度"),
        ("T2:heart:val_interp", "v0013", "v0009", "表达桥 vs 配对"),
        ("T2:heart:val_extrap", "v0011", "v0001", "收缩 vs 简单位移"),
        ("T2:heart:val_extrap", "v0012", "v0001", "空间平滑 vs 简单位移"),
        ("T3:gata4", "v0048", "v0009", "零膨胀 vs 基因置零"),
        ("T3:gata4", "v0046", "v0009", "收缩优化 vs 基因置零"),
        ("T3:gata4", "v0034", "v0009", "非负均值修复 vs 基因置零"),
        ("T3:gata4", "v0025", "v0009", "空间平滑 vs 基因置零"),
    ]
    with (DATA / "submetric_delta.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["board", "comparison", "metric", "new", "old", "delta"])
        for board, new, old, label in comparisons:
            metrics = sorted({m for (b, v, m) in skills if b == board and v in (new, old)})
            for m in metrics:
                a = skills.get((board, new, m))
                b = skills.get((board, old, m))
                if a is None or b is None:
                    continue
                w.writerow([board, label, m, a, b, f"{a - b:+.1f}"])

    # ---- figures ----
    order = [
        "T1:val", "T2:embryo:val_interp", "T2:heart:val_interp",
        "T2:heart:val_extrap", "T3:gata4",
    ]
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    x = range(len(order))
    base_y = [baselines[b]["score"] for b in order]
    best_y = [bests[b]["score"] for b in order]
    ax.bar([i - 0.18 for i in x], base_y, width=0.36, color="#b0b7c3", label="最早交上去的对照")
    ax.bar([i + 0.18 for i in x], best_y, width=0.36, color="#2f6f4e", label="目前最高")
    ax.axhline(50, color="#c47b2b", ls="--", lw=1, label="官网“什么都不做”=50（我们的复制件并未都落在50）")
    ax.set_xticks(list(x))
    ax.set_xticklabels([BOARD_SHORT[b] for b in order])
    ax.set_ylabel("服务器总分")
    ax.set_ylim(40, 70)
    ax.set_title("五个榜：最早对照 vs 目前最高")
    for i, b in enumerate(order):
        d = bests[b]["score"] - baselines[b]["score"]
        ax.text(i + 0.18, best_y[i] + 0.4, f"{d:+.1f}", ha="center", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "01_board_best_vs_baseline.png", dpi=140)
    plt.close()

    # family gains: top positive and notable negative
    fam_rows = []
    for board, fam, vers in FAMILIES:
        have = [r for r in by_board[board] if r["version"] in vers]
        if not have:
            continue
        base = baselines[board]["score"]
        best = max(r["score"] for r in have)
        fam_rows.append((best - base, f"{BOARD_SHORT[board]} · {fam}", best))
    fam_rows.sort()
    fig, ax = plt.subplots(figsize=(10.2, 9.6))
    ys = range(len(fam_rows))
    colors = ["#a33b3b" if d < -0.1 else "#2f6f4e" if d > 0.1 else "#8d93a0" for d, _, _ in fam_rows]
    ax.barh(list(ys), [d for d, _, _ in fam_rows], color=colors)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([name for _, name, _ in fam_rows], fontsize=8)
    ax.axvline(0, color="#333", lw=0.8)
    ax.set_xlabel("相对该榜最早对照的总分变化")
    ax.set_title("每条已评分路线族的最好成绩（绿=变好，红=变差）")
    fig.tight_layout()
    fig.savefig(FIG / "02_family_gain.png", dpi=140)
    plt.close()

    # submetric small multiples for the three confirmed wins + extrap non-win
    panels = [
        ("T1 密度比重采样\n相对分位数父版本", "T1:val", "v0024", "v0023",
         ["de_score", "de_direction", "mmd_u", "variogram"]),
        ("T2心脏插值 表达桥\n相对配对", "T2:heart:val_interp", "v0013", "v0009",
         ["de_score", "de_direction", "mmd_u", "scale_log_ratio", "variogram", "neighborhood_mmd"]),
        ("T3 零膨胀\n相对基因置零", "T3:gata4", "v0048", "v0009",
         ["de_score", "de_direction", "severity_slope", "mmd_u", "variogram"]),
        ("T2心脏外推 收缩\n总分只 +0.14，横轴被放大", "T2:heart:val_extrap", "v0011", "v0001",
         ["de_score", "de_direction", "mmd_u", "variogram", "neighborhood_mmd", "scale_log_ratio"]),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    for ax, (title, board, new, old, metrics) in zip(axes.ravel(), panels):
        deltas = []
        labels = []
        for m in metrics:
            a = skills.get((board, new, m))
            b = skills.get((board, old, m))
            if a is None or b is None:
                continue
            deltas.append(a - b)
            labels.append(METRIC_CN.get(m, m))
        colors = ["#2f6f4e" if d > 0.15 else "#a33b3b" if d < -0.15 else "#8d93a0" for d in deltas]
        ax.barh(range(len(deltas)), deltas, color=colors)
        ax.set_yticks(range(len(deltas)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.axvline(0, color="#333", lw=0.8)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("子项变化（正=变好）")
    fig.suptitle("已经确认的提分，钱主要花在哪个子项", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIG / "03_submetric_deltas.png", dpi=140)
    plt.close()
    print("assets ok", FIG)


if __name__ == "__main__":
    main()
