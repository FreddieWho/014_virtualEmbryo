#!/usr/bin/env python3
"""Source-only diagnostic for the frozen T2 anisotropy warp.

Implements reports/T2_GEOM_ANISO_FREEZE_20261007.md. Reads spatial_3D only.
Does not write h5ad, does not read held-out targets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "third_party" / "veckit"))
from common.shape_metrics import d2_distance, occupancy_dice  # noqa: E402

FORBIDDEN = ("E7.5", "E7.75", "E8.5", "E10.5", "E12.5")
ASPECT_GAP_MIN = 0.05
DICE_STABLE = 0.90
D2_REL = 1.10
SEED = 0
OUT = ROOT / "artifacts" / "t2_geom_aniso_20261007-v1"


def load_xyz(path: Path) -> np.ndarray:
    name = path.name
    if any(tok in name for tok in FORBIDDEN):
        raise SystemExit(f"refusing held-out path: {path}")
    with h5py.File(path, "r") as handle:
        xyz = np.asarray(handle["obsm"]["spatial_3D"][:, :3], dtype=np.float64)
    if not np.isfinite(xyz).all() or xyz.shape[1] != 3:
        raise SystemExit(f"bad coordinates: {path}")
    return xyz


def center_rms(cloud: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    mu = cloud.mean(axis=0)
    centered = cloud - mu
    rms = float(np.sqrt((centered ** 2).sum(axis=1).mean()))
    return centered, mu, rms


def spectrum(cloud: np.ndarray) -> tuple[np.ndarray, float, int]:
    centered, _, rms = center_rms(cloud)
    _, singular, _ = np.linalg.svd(centered, full_matrices=False)
    lam = (singular ** 2) / centered.shape[0]
    aspects = np.sqrt(lam) / rms
    return aspects, rms, int(cloud.shape[0])


def warp(cloud: np.ndarray, target_aspects: np.ndarray) -> np.ndarray:
    centered, mu, rms = center_rms(cloud)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    aspects, _, _ = spectrum(cloud)
    scales = target_aspects / aspects
    stretched = (centered @ vt.T) * scales
    stretched = stretched @ vt
    restored = stretched * (rms / float(np.sqrt((stretched ** 2).sum(axis=1).mean())))
    return restored + mu


def pair_metrics(left: np.ndarray, right: np.ndarray) -> dict[str, float]:
    dice, resolution = occupancy_dice(left, right, seed=SEED)
    return {
        "occupancy_dice": float(dice),
        "dice_resolution": float(resolution),
        "d2_shape": float(d2_distance(left, right, seed=SEED)),
    }


def judge(name: str, gap: float, bracket_dice: float, inc: dict, warped: dict) -> dict:
    reasons = []
    if gap < ASPECT_GAP_MIN:
        reasons.append("INSUFFICIENT_ANISOTROPY")
    if bracket_dice >= DICE_STABLE:
        reasons.append("SUPPORT_STABLE")
    dice_both = (
        warped["early"]["occupancy_dice"] > inc["early"]["occupancy_dice"]
        and warped["late"]["occupancy_dice"] > inc["late"]["occupancy_dice"]
    )
    dice_one = (
        warped["early"]["occupancy_dice"] > inc["early"]["occupancy_dice"]
    ) ^ (
        warped["late"]["occupancy_dice"] > inc["late"]["occupancy_dice"]
    )
    d2_ok = (
        warped["early"]["d2_shape"] <= inc["early"]["d2_shape"] * D2_REL
        and warped["late"]["d2_shape"] <= inc["late"]["d2_shape"] * D2_REL
    )
    if reasons:
        verdict = "STOP"
    elif dice_both and d2_ok:
        verdict = "CONTINUE"
    elif dice_one or not dice_both or not d2_ok:
        verdict = "STOP"
        if dice_one:
            reasons.append("SLIDE_TO_ONE_BRACKET")
        elif not dice_both:
            reasons.append("DICE_NOT_BOTH")
        if not d2_ok:
            reasons.append("D2_WORSE")
    else:
        verdict = "STOP"
        reasons.append("UNCLASSIFIED")
    return {
        "board": name,
        "verdict": verdict,
        "reasons": reasons,
        "aspect_gap": gap,
        "bracket_dice": bracket_dice,
        "dice_both": dice_both,
        "d2_ok": d2_ok,
    }


def run_board(spec: dict) -> dict:
    early = load_xyz(ROOT / spec["early"])
    late = load_xyz(ROOT / spec["late"])
    incumbent = load_xyz(ROOT / spec["incumbent"])
    parent = load_xyz(ROOT / spec["parent"]) if spec.get("parent") else None
    a_early, rms_early, n_early = spectrum(early)
    a_late, rms_late, n_late = spectrum(late)
    a_inc, rms_inc, n_inc = spectrum(incumbent)
    target = (1.0 - spec["t"]) * a_early + spec["t"] * a_late
    warped = warp(incumbent, target)
    _, rms_warp, _ = spectrum(warped)
    identity = warp(incumbent, a_inc)
    isotropic = warp(incumbent, a_inc)  # placeholder replaced below
    centered, mu, rms = center_rms(incumbent)
    isotropic = centered * 0.9
    isotropic = isotropic * (rms / float(np.sqrt((isotropic ** 2).sum(axis=1).mean()))) + mu

    def close_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
        met = pair_metrics(a, b)
        return met

    controls = {
        "rms_rel": abs(rms_warp / rms_inc - 1.0),
        "identity_dice": close_metrics(identity, incumbent)["occupancy_dice"],
        "identity_d2": close_metrics(identity, incumbent)["d2_shape"],
        "isotropic_restore_dice": close_metrics(isotropic, incumbent)["occupancy_dice"],
        "isotropic_restore_d2": close_metrics(isotropic, incumbent)["d2_shape"],
        "coord_max_abs_identity": float(np.max(np.abs(identity - incumbent))),
        "coord_max_abs_isotropic_restore": float(np.max(np.abs(isotropic - incumbent))),
    }
    if controls["rms_rel"] >= 1e-6:
        raise SystemExit(f"{spec['name']}: RMS lock failed ({controls['rms_rel']})")
    if controls["coord_max_abs_identity"] > 1e-8:
        raise SystemExit(f"{spec['name']}: identity warp moved coordinates")
    if controls["coord_max_abs_isotropic_restore"] > 1e-6:
        raise SystemExit(f"{spec['name']}: isotropic restore leaked scale into coordinates")

    inc_metrics = {"early": pair_metrics(incumbent, early), "late": pair_metrics(incumbent, late)}
    warp_metrics = {"early": pair_metrics(warped, early), "late": pair_metrics(warped, late)}
    bracket = pair_metrics(early, late)
    gap = float(np.max(np.abs(a_early - a_late)))
    judged = judge(spec["name"], gap, bracket["occupancy_dice"], inc_metrics, warp_metrics)
    parent_same = None
    if parent is not None and parent.shape == incumbent.shape:
        parent_same = bool(np.allclose(parent, incumbent.astype(parent.dtype), rtol=0, atol=1e-5))
    return {
        "name": spec["name"],
        "t": spec["t"],
        "n": {"early": n_early, "late": n_late, "incumbent": n_inc},
        "rms": {"early": rms_early, "late": rms_late, "incumbent": rms_inc, "warp": rms_warp},
        "aspects": {
            "early": a_early.tolist(),
            "late": a_late.tolist(),
            "incumbent": a_inc.tolist(),
            "target": target.tolist(),
        },
        "bracket": bracket,
        "incumbent_vs_bracket": inc_metrics,
        "warp_vs_bracket": warp_metrics,
        "parent_coords_match_incumbent": parent_same,
        "controls": controls,
        "judgment": judged,
    }


def render(payload: dict) -> str:
    lines = [
        "# T2 各向异性诊断结果",
        "",
        "冻结：`reports/T2_GEOM_ANISO_FREEZE_20261007.md`。无候选，未读验证期真值。",
        "",
    ]
    heart = payload["boards"][0]["judgment"]["verdict"]
    embryo = payload["boards"][1]["judgment"]["verdict"]
    if heart == "CONTINUE" and embryo == "CONTINUE":
        overall = "CONTINUE_BOTH"
    elif heart == "CONTINUE":
        overall = "HEART_ONLY_CONTINUE"
    else:
        overall = "STOP"
    lines.append(f"总判：`{overall}`。心脏 `{heart}`，胚胎 `{embryo}`。")
    lines.append("")
    lines.append("CONTINUE 只表示这条线性族还没被源侧代理否定，不授权建候选，也不等于服务器 occupancy 会动。")
    lines.append("")
    for board in payload["boards"]:
        j = board["judgment"]
        lines.append(f"## {board['name']}")
        lines.append("")
        lines.append(f"判据：`{j['verdict']}`。原因：{', '.join(j['reasons']) or '通过写死的双括号条件'}。")
        lines.append(
            f"谱差 {j['aspect_gap']:.4f}（门 0.05），括号 dice {j['bracket_dice']:.4f}（稳定门 0.90）。"
        )
        lines.append("")
        lines.append("| 对照 | dice 早 | dice 晚 | d2 早 | d2 晚 |")
        lines.append("|---|---:|---:|---:|---:|")
        inc, warped = board["incumbent_vs_bracket"], board["warp_vs_bracket"]
        lines.append(
            f"| 现役 | {inc['early']['occupancy_dice']:.4f} | {inc['late']['occupancy_dice']:.4f} | "
            f"{inc['early']['d2_shape']:.5f} | {inc['late']['d2_shape']:.5f} |"
        )
        lines.append(
            f"| 形变 | {warped['early']['occupancy_dice']:.4f} | {warped['late']['occupancy_dice']:.4f} | "
            f"{warped['early']['d2_shape']:.5f} | {warped['late']['d2_shape']:.5f} |"
        )
        lines.append("")
        lines.append(
            "谱 "
            + " / ".join(
                f"{k}={np.array2string(np.asarray(v), precision=4)}"
                for k, v in board["aspects"].items()
            )
        )
        lines.append(f"父版本坐标与现役一致：{board['parent_coords_match_incumbent']}。")
        lines.append("")
    lines.append("实现锁：RMS 相对变化、恒等形变、各向同性 ×0.9 再锁回 RMS，均在脚本内失败即退出。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    boards = [
        {
            "name": "heart_interp",
            "t": 0.5,
            "early": "data/E8.25_late.h5ad",
            "late": "data/E8.75.h5ad",
            "incumbent": "submissions/candidates/T2_heart_val_interp/v0019_h_o1_shrinkmerge/submission.h5ad",
            "parent": "submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        },
        {
            "name": "embryo_interp",
            "t": (7.5 - 7.25) / (8.0 - 7.25),
            "early": "data/E7.25.h5ad",
            "late": "data/E8.0.h5ad",
            "incumbent": "submissions/candidates/T2_embryo_val_interp/v0014_e_o1_shrinkmerge/submission.h5ad",
            "parent": "submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad",
        },
    ]
    payload = {"freeze": "reports/T2_GEOM_ANISO_FREEZE_20261007.md", "boards": [run_board(s) for s in boards]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(payload, indent=2) + "\n")
    text = render(payload)
    (OUT / "RESULT.md").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
