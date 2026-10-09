"""Local held-out-stage evaluation with the official veckit metric code (released stages only).
Truth = 10% subsample of a RELEASED stage held out from the recipe; reference = 10% of the reference stage."""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, anndata as ad
sys.path.insert(0, "/workspace/ve/veckit_latest"); sys.path.insert(0, str(Path(__file__).parent))
import score_h5ad as sh
from vecommon import load_stage, panel

HIGHER = {"de_score", "de_direction", "occupancy_dice", "severity_slope"}


def sub(a, frac, seed):
    rng = np.random.default_rng(seed); n = max(int(a.n_obs * frac), 10)
    return a[np.sort(rng.choice(a.n_obs, n, replace=False))]


def score(task, pred_path_or_ad, truth_stage, ref_stage, genes, frac=0.1, seed=0, truth_half=False):
    metrics, m2 = sh._load_task_metrics(task)
    T = sub(load_stage(truth_stage, genes), frac, seed + 1)
    if truth_half: T = T[: T.n_obs // 2]
    Rf = sub(load_stage(ref_stage, genes), frac, seed + 2)
    P = ad.read_h5ad(pred_path_or_ad) if isinstance(pred_path_or_ad, (str, Path)) else pred_path_or_ad
    P = P[:, genes]
    tX, rX = np.asarray(T.X, np.float32), np.asarray(Rf.X, np.float32)
    pX = P.X.toarray() if hasattr(P.X, "toarray") else np.asarray(P.X, np.float32)
    tct = np.asarray(T.obs["celltype"]).astype(str)
    probe = metrics.train_frozen_probe(tX, tct)
    pct = np.array(["NA"] * P.n_obs)
    if task == "T2":
        return m2.score_task2_v2(pX, np.asarray(P.obsm["spatial_3D"])[:, :3], pct, tX,
                                 np.asarray(T.obsm["spatial_3D"])[:, :3], tct, rX, probe=probe, seed=seed)
    if task == "T3":
        return m2.score_task3_v2(pX, np.asarray(P.obsm["spatial_3D"])[:, :3], pct, tX,
                                 np.asarray(T.obsm["spatial_3D"])[:, :3], tct, rX, probe=probe, seed=seed)
    return m2.score_task1_v2(pX, pct, tX, tct, rX, probe=probe, seed=seed)


def skill(v, floor, ceil):
    if v is None or floor is None: return None
    df, d = abs(floor - ceil), abs(v - ceil)
    return 100 * df / (df + d) if df + d > 0 else 50.0
