#!/usr/bin/env python
"""Selection backtests that mirror the OFFICIAL board construction as far as it is public:
  * every stage -> 10% working copy (seeded); the target copy is split in half: half A = truth, half B = ceiling
  * reference = 10% copy of the reference stage (preceding stage for T1/T2, matched WT for T3)
  * floor = copy_last / wt_identity = the reference working copy itself (so de/dir are exactly 0, as on the portal)
  * per-metric hyperbolic skill d_f/(d_f+d) against locally measured floor and ceiling values
  * official weights: T1 de .25 dir .25 mmd .30 vario .20; T2 de .125 dir .125 mmd .15 vario .10 d2/occ/scale .0833 nbhd .25;
    T3 de .30 dir .25 sev .25 mmd .12 vario .08
What it can NOT mirror: the organisers' exact subsample indices, the real held-out stage (LOO uses a released stage
as a stand-in target and therefore a different time gap / composition turnover), and replicate selection (T3).
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np, anndata as ad
sys.path.insert(0, "/workspace/ve/veckit_latest"); sys.path.insert(0, str(Path(__file__).parent))
import score_h5ad as sh
from vecommon import load_stage, panel

W = {"T1": {"de_score": .25, "de_direction": .25, "mmd_u": .30, "variogram": .20},
     "T2": {"de_score": .125, "de_direction": .125, "mmd_u": .15, "variogram": .10, "d2_shape": 1 / 12,
            "occupancy_dice": 1 / 12, "scale_log_ratio": 1 / 12, "neighborhood_mmd": .25},
     "T3": {"de_score": .30, "de_direction": .25, "severity_slope": .25, "mmd_u": .12, "variogram": .08}}


def working_copy(a, seed, frac=0.1):
    rng = np.random.default_rng(seed); n = max(int(round(a.n_obs * frac)), 10)
    return a[np.sort(rng.choice(a.n_obs, n, replace=False))].copy()


class Board:
    """One backtest board: target stage (held out), reference stage, task."""
    def __init__(self, task, genes, target_ad, ref_ad, seed=0):
        self.task, self.genes, self.seed = task, genes, seed
        self.metrics, self.m2 = sh._load_task_metrics(task)
        T = working_copy(target_ad, seed + 11); perm = np.random.default_rng(seed + 12).permutation(T.n_obs)
        h = T.n_obs // 2
        self.A, self.B = T[np.sort(perm[:h])].copy(), T[np.sort(perm[h:2 * h])].copy()
        self.R = working_copy(ref_ad, seed + 13)
        self.probe = self.metrics.train_frozen_probe(self._X(self.A), np.asarray(self.A.obs["celltype"]).astype(str))
        self.floor = self.raw(self.R); self.ceil = self.raw(self.B)

    @staticmethod
    def _X(a):
        X = a.X
        return np.asarray(X.toarray() if hasattr(X, "toarray") else X, np.float32)

    def raw(self, P):
        P = P[:, self.genes] if list(P.var_names) != self.genes else P
        pX = self._X(P); tX = self._X(self.A); rX = self._X(self.R)
        tct = np.asarray(self.A.obs["celltype"]).astype(str); pct = np.array(["NA"] * P.n_obs)
        if self.task == "T1":
            return self.m2.score_task1_v2(pX, pct, tX, tct, rX, probe=self.probe, seed=self.seed)
        pC = np.asarray(P.obsm["spatial_3D"])[:, :3]; tC = np.asarray(self.A.obsm["spatial_3D"])[:, :3]
        f = self.m2.score_task2_v2 if self.task == "T2" else self.m2.score_task3_v2
        return f(pX, pC, pct, tX, tC, tct, rX, probe=self.probe, seed=self.seed)

    def skills(self, m, ceil_from=None):
        """ceil_from: board key in index.json -> use the PUBLISHED ceiling anchors instead of the local half/half
        estimate (local 10%-half ceilings are much weaker than the published ones, e.g. T1 variogram 0.0021 vs 0.000158)."""
        out = {}
        from vecommon import INDEX
        anc = INDEX[ceil_from]["anchors"] if ceil_from else {}
        for k in W[self.task]:
            v, f = m.get(k), self.floor.get(k)
            c = anc[k]["ceiling"] if k in anc else self.ceil.get(k)
            if self.task == "T3" and k in ("de_score", "de_direction", "severity_slope"):
                c = {"de_score": 1.0, "de_direction": 1.0, "severity_slope": 0.0}[k] if c is None else c
            if v is None or f is None or c is None: out[k] = 50.0; continue
            df, d = abs(f - c), abs(v - c)
            out[k] = 100 * df / (df + d) if df + d > 0 else 50.0
        out["TOTAL"] = sum(W[self.task][k] * out[k] for k in W[self.task])
        return out


def fmt(name, sk):
    return f"{name:34s} TOTAL {sk['TOTAL']:6.2f} | " + " ".join(f"{k[:5]} {v:5.1f}" for k, v in sk.items() if k != "TOTAL")
