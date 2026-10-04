"""Lane builders for T2 round2 (frozen design 2026-09-29).

Usage:
  python -m scripts.t2_round2.run verify --root RUN_DIR
  python -m scripts.t2_round2.run build  --root RUN_DIR [--lanes a,b,c] [--boards embryo,heart,extrap]

Deterministic given configs/t2_round2/design_20260929.json. No target data.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

from scripts.t2_round2 import common, ops

REPO = common.REPO
BRIDGE_SEED = common.BRIDGE_SEED

BOARD_DIR = {
    "embryo": "T2_embryo_val_interp",
    "heart": "T2_heart_val_interp",
    "extrap": "T2_heart_val_extrap",
}
CONTRACT_BOARD = {
    "embryo": "embryo:val_interp",
    "heart": "heart:val_interp",
    "extrap": "heart:val_extrap",
}
NORM_MARKER = {"embryo": "log1p_normalized", "heart": "log1p_normalized", "extrap": "log_normalized"}


# ------------------------------------------------------------------ contexts

class InterpCtx:
    """Loaded context for embryo/heart interp boards."""

    def __init__(self, board: str, bc: dict):
        self.board = board
        self.bc = bc
        self.panel = common.read_panel(bc["panel"])
        self.P = common.load_parent(bc["bridge_parent"], bc["bridge_parent_sha256"])
        self.W = common.load_parent(bc["parent"], bc["parent_sha256"])
        self.XP = common.dense(self.P.X).astype(np.float64)
        self.ptypes = np.asarray(self.P.obs["celltype"].astype(str))
        self.pnames = [str(v) for v in self.P.obs_names]
        self.pcm = (np.asarray(self.P.obs["cm_celltype"].astype(str))
                    if "cm_celltype" in self.P.obs.columns else None)
        self.stages: dict[str, tuple] = {}
        for sk, sp in bc["stages"].items():
            self.stages[sk] = common.load_stage(sp, self.panel, want_cm=True)
        self.lam = float(bc["lam"])
        self.n = int(bc["n_obs"])
        self.pstates = sorted(set(self.ptypes.tolist()))
        XL, tL, _, cmL = self.stages["left"]
        XR, tR, _, cmR = self.stages["right"]
        self.XL, self.tL, self.cmL = XL, tL, cmL
        self.XR, self.tR, self.cmR = XR, tR, cmR
        self.mL, self.vL, self.nL = common.means_vars_by_label(XL, tL)
        self.mR, self.vR, self.nR = common.means_vars_by_label(XR, tR)
        self.muP, _, self.nP = common.means_vars_by_label(self.XP, self.ptypes)
        self.shared = sorted(set(self.pstates) & set(self.mL) & set(self.mR))
        self.pP = common.shares(self.ptypes)
        self.pL = common.shares(tL)
        self.pR = common.shares(tR)

    def bridge_shift(self, state: str) -> np.ndarray:
        muT = (1.0 - self.lam) * self.mL[state] + self.lam * self.mR[state]
        return (muT - self.muP[state]).astype(np.float64)

    def rerun_winner_plan(self):
        counts, raw = common.mass_counts_bridge(
            self.pstates, self.pP, self.pL, self.pR, set(self.shared), self.lam, self.n)
        chosen = common.select_rows(self.ptypes, counts, BRIDGE_SEED)
        final = common.dedup_names([self.pnames[i] for i in chosen])
        winner_names = [str(v) for v in self.W.obs_names]
        if final != winner_names:
            raise AssertionError(f"{self.board}: rerun plan != winner obs_names (plan drift)")
        return chosen, final, counts, raw

    def mean_shift_matrix(self, shrink: bool = False) -> tuple[np.ndarray, dict]:
        X1 = self.XP.copy()
        diag: dict = {"shrink": shrink}
        wstats = []
        for s in self.pstates:
            if s in self.shared:
                shift = self.bridge_shift(s)
                if shrink:
                    se = ops.se_two_means(self.vL[s], self.nL[s], self.vR[s], self.nR[s])
                    w = ops.shrink_weights(shift, se, C=2.0)
                    shift = shift * w
                    wstats.append({"state": s, "mean_w": float(w.mean())})
            else:
                shift = np.zeros(self.XP.shape[1])
            X1[self.ptypes == s] += shift
        clip_frac = float((X1 < 0).mean())
        np.clip(X1, 0, None, out=X1)
        diag["clip_fraction"] = clip_frac
        if wstats:
            diag["mean_w_overall"] = float(np.mean([d["mean_w"] for d in wstats]))
            diag["shrink_table"] = wstats
        return X1, diag


class ExtrapCtx:
    def __init__(self, bc: dict):
        self.bc = bc
        self.panel = common.read_panel(bc["panel"])
        self.V = common.load_parent(bc["parent"], bc["parent_sha256"])
        self.XV = common.dense(self.V.X).astype(np.float64)
        self.tV = np.asarray(self.V.obs["celltype"].astype(str))
        self.nV = [str(v) for v in self.V.obs_names]
        X825, t825, _, _ = common.load_stage(bc["stages"]["e825"], self.panel)
        X875, t875, _, _ = common.load_stage(bc["stages"]["left"], self.panel)
        X95, t95, n95, _ = common.load_stage(bc["stages"]["right"], self.panel)
        self.X825, self.t825 = X825, t825
        self.X875, self.t875 = X875, t875
        self.X95, self.t95 = X95, t95
        idx = {n: i for i, n in enumerate(n95)}
        missing = [n for n in self.nV if n not in idx]
        if missing:
            raise AssertionError(f"extrap: {len(missing)} v0001 rows not found in E9.5")
        self.src_idx = np.array([idx[n] for n in self.nV], dtype=np.int64)
        self.Xe95_src = self.X95[self.src_idx]
        self.m825, _, self.n825 = common.means_vars_by_label(X825, t825)
        self.m875, self.v875, self.n875 = common.means_vars_by_label(X875, t875)
        self.m95, self.v95, self.n95 = common.means_vars_by_label(X95, t95)
        self.shared = sorted(set(self.m95) & set(self.m875))
        self.orphans = sorted(set(self.m95) - set(self.m875))
        self.three_way = sorted(set(self.shared) & set(self.m825))
        self.n = int(bc["n_obs"])

    def baseline_delta(self, s: str) -> np.ndarray:
        return (self.m95[s] - self.m875[s]).astype(np.float64)

    def trend_delta(self, s: str) -> np.ndarray:
        v1 = self.m875[s] - self.m825[s]
        v2 = self.m95[s] - self.m875[s]
        return (2.0 * v2 - v1).astype(np.float64)

    def shrink_se(self, s: str) -> np.ndarray:
        return ops.se_two_means(self.v875[s], self.n875[s], self.v95[s], self.n95[s])

    def shrunk_delta_f32(self, s: str, base: np.ndarray) -> np.ndarray:
        """Mirror scripts/g0/t2_r2_shrink.py dtype path exactly (float32 delta)."""
        se = self.shrink_se(s) + 1e-12
        tstat = np.abs(base / se)
        w = (tstat / (tstat + 2.0)).astype(np.float32)
        return (base * w).astype(np.float32)


# ------------------------------------------------------------------ lane output helper

def finalize(ctx, run_dir: Path, board: str, lane: str, version: str,
             X_out: np.ndarray, chosen: np.ndarray, final_names: list[str],
             *, base: ad.AnnData, normalization: str, provenance_extra: dict,
             coords_override: np.ndarray | None = None) -> dict:
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    if not np.isfinite(Xf).all() or (Xf < 0).any():
        raise AssertionError(f"{lane}: X not finite/nonnegative")
    if Xf.shape != (len(final_names), X_out.shape[1]):
        raise AssertionError(f"{lane}: shape mismatch")
    out_a = base[chosen].copy()
    out_a.obs_names = final_names
    out_a.X = Xf
    if coords_override is not None:
        c = np.asarray(coords_override, dtype=np.float32)
        out_a.obsm["spatial_3D"] = np.ascontiguousarray(c[:, :3], dtype=np.float32)
    common.fix_obsm(out_a)
    prov = {
        "atom_id": "T2-ROUND2-20260929-v1", "lane": lane, "board": ctx.bc["key"],
        "version": version, "seed": common.load_config()["seed"],
        "config_sha256": common.sha256(common.CONFIG_PATH),
        "parent_sha256": ctx.bc.get("parent_sha256"), "target_used": False,
        **provenance_extra,
    }
    common.stamp_uns(out_a, normalization=normalization, provenance=prov)
    out = run_dir / "candidates" / board / lane / "submission.h5ad"
    sha = common.write_candidate(out_a, out)
    common.source_row_ledger(run_dir / "intermediates" / f"source_row_ledger_{board}_{lane}.tsv",
                             chosen, [str(v) for v in base.obs_names], final_names)
    return {"output": str(out.resolve().relative_to(REPO)), "sha256": sha, "n_obs": int(out_a.n_obs),
            "n_vars": int(out_a.n_vars)}


# ------------------------------------------------------------------ interp lane builders

def build_e_n1_qbridge(ctx: InterpCtx, run_dir: Path, lane: str, version: str) -> dict:
    lam = ctx.lam
    min_cells = 30
    Xq = ctx.XP.copy()
    used_q, used_ms = [], []
    for s in ctx.shared:
        if ctx.nL[s] >= min_cells and ctx.nR[s] >= min_cells:
            rows = np.flatnonzero(ctx.ptypes == s)
            lcells = ctx.XL[ctx.tL == s]
            rcells = ctx.XR[ctx.tR == s]
            for g in range(ctx.XP.shape[1]):
                Xq[rows, g] = ops.quantile_bridge_map(ctx.XP[rows, g], lcells[:, g], rcells[:, g], lam)
            used_q.append(s)
        else:
            Xq[ctx.ptypes == s] += ctx.bridge_shift(s)
            used_ms.append(s)
    clip_frac = float((Xq < 0).mean())
    np.clip(Xq, 0, None, out=Xq)
    chosen, final, counts, raw = ctx.rerun_winner_plan()
    res = finalize(ctx, run_dir, ctx.board, lane, version, Xq[chosen], chosen, final,
                   base=ctx.P, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "quantile_bridge+mass", "lambda": lam})
    res["diag"] = {"quantile_states": used_q, "mean_shift_fallback_states": used_ms,
                   "unmatched_states": sorted(set(ctx.pstates) - set(ctx.shared)),
                   "clip_fraction": clip_frac, "rows_match_winner": True}
    return res


def build_e_o1_shrinkmerge(ctx: InterpCtx, run_dir: Path, lane: str, version: str) -> dict:
    X1, diag = ctx.mean_shift_matrix(shrink=True)
    chosen, final, counts, raw = ctx.rerun_winner_plan()
    res = finalize(ctx, run_dir, ctx.board, lane, version, X1[chosen], chosen, final,
                   base=ctx.P, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "mean_bridge_shrunk_C2+mass", "lambda": ctx.lam})
    diag.pop("shrink_table", None)
    res["diag"] = {**diag, "rows_match_winner": True}
    return res


def build_e_o2_scalmass(ctx: InterpCtx, run_dir: Path, lane: str, version: str) -> dict:
    W = ctx.W
    coords = np.asarray(W.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    times, rms_vals = [], []
    for sk in ("e675", "left", "right"):
        sp = ctx.bc["stages"][sk]
        a = ad.read_h5ad(REPO / sp, backed="r")
        st_coords = np.asarray(a.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        a.file.close()
        times.append(ctx.bc["stage_times"][sk])
        rms_vals.append(ops.rms_radius(st_coords))
    order = np.argsort(times)
    times = [times[i] for i in order]
    rms_vals = [rms_vals[i] for i in order]
    target_log = ops.l1_target_log_rms(np.array(times), np.array(rms_vals),
                                       ctx.bc["stage_times"]["target"])
    target_rms = float(np.exp(target_log))
    newc, factor = ops.scale_to_rms(coords, target_rms)
    chosen = np.arange(W.n_obs)
    final = [str(v) for v in W.obs_names]
    res = finalize(ctx, run_dir, ctx.board, lane, version, common.dense(W.X), chosen, final,
                   base=W, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "mass_bridge+post_mass_rms_refit",
                                     "scale_factor": factor, "target_rms": target_rms},
                   coords_override=newc)
    res["diag"] = {"stage_times": times, "stage_rms": rms_vals, "target_rms": target_rms,
                   "pre_rms": ops.rms_radius(coords), "scale_factor": factor,
                   "post_rms": ops.rms_radius(newc), "expression_unchanged": True}
    return res


def build_e_n2_trend3(ctx: InterpCtx, run_dir: Path, lane: str, version: str,
                      seed: int) -> dict:
    X3, t3, _, _ = ctx.stages["e675"]
    m3, _, n3 = common.means_vars_by_label(X3, t3)
    p3 = common.shares(t3)
    three = sorted(set(ctx.pstates) & set(m3) & set(ctx.mL) & set(ctx.mR))
    times3 = [ctx.bc["stage_times"]["e675"], ctx.bc["stage_times"]["left"], ctx.bc["stage_times"]["right"]]
    t_eval = ctx.bc["stage_times"]["target"]
    G = ctx.XP.shape[1]
    X1 = ctx.XP.copy()
    for s in ctx.pstates:
        if s in three:
            muT = np.empty(G)
            for g in range(G):
                muT[g] = ops.linfit_eval(np.array(times3),
                                         np.array([m3[s][g], ctx.mL[s][g], ctx.mR[s][g]]), t_eval)
            X1[ctx.ptypes == s] += (muT - ctx.muP[s])
        elif s in ctx.shared:
            X1[ctx.ptypes == s] += ctx.bridge_shift(s)
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    raw = {}
    for s in ctx.pstates:
        if s in three:
            raw[s] = ops.share_series_predict(np.array(times3),
                                              np.array([p3.get(s, 0.0), ctx.pL.get(s, 0.0), ctx.pR.get(s, 0.0)]),
                                              t_eval)
        elif s in ctx.shared:
            raw[s] = (1.0 - ctx.lam) * ctx.pL.get(s, 0.0) + ctx.lam * ctx.pR.get(s, 0.0)
        else:
            raw[s] = 0.5 * ctx.pP[s] + 0.5 * ctx.pL.get(s, 0.0)
    counts, raw_n = common.counts_from_raw(raw, ctx.pstates, ctx.n)
    chosen = common.select_rows(ctx.ptypes, counts, seed)
    final = common.dedup_names([ctx.pnames[i] for i in chosen])
    pd.DataFrame([{"state": s, "parent_n": int((ctx.ptypes == s).sum()), "target_n": counts[s],
                   "share_pred": raw_n[s]} for s in ctx.pstates]
                 ).to_csv(run_dir / "intermediates" / f"mass_plan_{ctx.board}_{lane}.tsv",
                          sep="\t", index=False)
    res = finalize(ctx, run_dir, ctx.board, lane, version, X1[chosen], chosen, final,
                   base=ctx.P, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "three_stage_trend_bridge+trend_mass",
                                     "seed": seed, "t_eval": t_eval})
    res["diag"] = {"three_way_states": three, "n_three_way": len(three),
                   "bracket_only_states": sorted(set(ctx.shared) - set(three)),
                   "unmatched_states": sorted(set(ctx.pstates) - set(ctx.shared)),
                   "clip_fraction": clip_frac}
    return res


def build_e_n3_substate2(ctx: InterpCtx, run_dir: Path, lane: str, version: str,
                         seed: int) -> dict:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    Xb = np.vstack([ctx.XL, ctx.XR])
    tb = np.concatenate([ctx.tL, ctx.tR])
    is_left = np.array([True] * len(ctx.tL) + [False] * len(ctx.tR))
    pca = PCA(n_components=10, random_state=seed)
    Zb = pca.fit_transform(Xb)
    Zp = pca.transform(ctx.XP)
    finalP = np.array(ctx.ptypes, dtype=object)
    finalL = np.array(ctx.tL, dtype=object)
    finalR = np.array(ctx.tR, dtype=object)
    n_split, resolved = 0, 0
    for s in sorted(set(tb.tolist())):
        mask_b = tb == s
        if mask_b.sum() < 120:
            continue
        km = KMeans(n_clusters=2, n_init=10, random_state=seed)
        lab_b = km.fit_predict(Zb[mask_b])
        # resolve: both brackets must have >=30 cells of the substate
        sub_ok = {}
        for k in (0, 1):
            n_l = int(((lab_b == k) & is_left[mask_b]).sum())
            n_r = int(((lab_b == k) & ~is_left[mask_b]).sum())
            sub_ok[k] = (n_l >= 30 and n_r >= 30)
        n_split += 1
        idx_b = np.flatnonzero(mask_b)
        zb_labels = np.array([f"{s}#{k}" if sub_ok[k] else s for k in lab_b], dtype=object)
        sel_l = is_left[mask_b]
        finalL[idx_b[sel_l]] = zb_labels[sel_l]
        finalR[idx_b[~sel_l] - len(ctx.tL)] = zb_labels[~sel_l]
        mask_p = ctx.ptypes == s
        if mask_p.any():
            lab_p = km.predict(Zp[mask_p])
            idx_p = np.flatnonzero(mask_p)
            finalP[idx_p] = [f"{s}#{k}" if sub_ok[k] else s for k in lab_p]
        resolved += sum(1 for k in (0, 1) if sub_ok[k])
    pstates = sorted(set(finalP.tolist()))
    mLf, _, _ = common.means_vars_by_label(ctx.XL, finalL)
    mRf, _, _ = common.means_vars_by_label(ctx.XR, finalR)
    muPf, _, _ = common.means_vars_by_label(ctx.XP, finalP)
    sharedf = sorted(set(pstates) & set(mLf) & set(mRf))
    pPf = common.shares(finalP)
    pLf = common.shares(finalL)
    pRf = common.shares(finalR)
    X1 = ctx.XP.copy()
    for s in pstates:
        if s in sharedf:
            muT = (1.0 - ctx.lam) * mLf[s] + ctx.lam * mRf[s]
            X1[finalP == s] += (muT - muPf[s])
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    counts, raw = common.mass_counts_bridge(pstates, pPf, pLf, pRf, set(sharedf), ctx.lam, ctx.n)
    chosen = common.select_rows(finalP, counts, seed)
    final = common.dedup_names([ctx.pnames[i] for i in chosen])
    pd.DataFrame([{"state": s, "parent_n": int((finalP == s).sum()), "target_n": counts[s],
                   "share_pred": raw[s]} for s in pstates]
                 ).to_csv(run_dir / "intermediates" / f"mass_plan_{ctx.board}_{lane}.tsv",
                          sep="\t", index=False)
    res = finalize(ctx, run_dir, ctx.board, lane, version, X1[chosen], chosen, final,
                   base=ctx.P, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "substate2_bridge+mass", "seed": seed,
                                     "pca_var_explained": float(pca.explained_variance_ratio_.sum())})
    res["diag"] = {"types_split": n_split, "substates_resolved": resolved,
                   "final_states": len(pstates), "shared_final_states": len(sharedf),
                   "clip_fraction": clip_frac}
    return res


def build_h_n2_curve95(ctx: InterpCtx, run_dir: Path, lane: str, version: str,
                       seed: int) -> dict:
    X9, t9, _, _ = ctx.stages["e95"]
    m9, _, n9 = common.means_vars_by_label(X9, t9)
    p9 = common.shares(t9)
    three = sorted(set(ctx.pstates) & set(ctx.mL) & set(ctx.mR) & set(m9))
    times3 = [ctx.bc["stage_times"]["left"], ctx.bc["stage_times"]["right"], ctx.bc["stage_times"]["e95"]]
    t_eval = ctx.bc["stage_times"]["target"]
    G = ctx.XP.shape[1]
    w3 = ops.lagrange3_weights(np.array(times3), t_eval)
    X1 = ctx.XP.copy()
    for s in ctx.pstates:
        if s in three:
            muT = w3[0] * ctx.mL[s] + w3[1] * ctx.mR[s] + w3[2] * m9[s]
            X1[ctx.ptypes == s] += (muT - ctx.muP[s])
        elif s in ctx.shared:
            X1[ctx.ptypes == s] += ctx.bridge_shift(s)
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    raw = {}
    for s in ctx.pstates:
        if s in three:
            raw[s] = ops.share_series_predict(np.array(times3),
                                              np.array([ctx.pL.get(s, 0.0), ctx.pR.get(s, 0.0), p9.get(s, 0.0)]),
                                              t_eval, quadratic=True)
        elif s in ctx.shared:
            raw[s] = (1.0 - ctx.lam) * ctx.pL.get(s, 0.0) + ctx.lam * ctx.pR.get(s, 0.0)
        else:
            raw[s] = 0.5 * ctx.pP[s] + 0.5 * ctx.pL.get(s, 0.0)
    counts, raw_n = common.counts_from_raw(raw, ctx.pstates, ctx.n)
    chosen = common.select_rows(ctx.ptypes, counts, seed)
    final = common.dedup_names([ctx.pnames[i] for i in chosen])
    pd.DataFrame([{"state": s, "parent_n": int((ctx.ptypes == s).sum()), "target_n": counts[s],
                   "share_pred": raw_n[s]} for s in ctx.pstates]
                 ).to_csv(run_dir / "intermediates" / f"mass_plan_{ctx.board}_{lane}.tsv",
                          sep="\t", index=False)
    res = finalize(ctx, run_dir, ctx.board, lane, version, X1[chosen], chosen, final,
                   base=ctx.P, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "lagrange3_curve_bridge+mass", "seed": seed,
                                     "weights": [float(w) for w in w3]})
    res["diag"] = {"three_way_states": three, "n_three_way": len(three),
                   "clip_fraction": clip_frac}
    return res


def build_h_n3_cmjoin(ctx: InterpCtx, run_dir: Path, lane: str, version: str,
                      seed: int, cm_table: dict) -> dict:
    if ctx.pcm is None or ctx.cmL is None or ctx.cmR is None:
        raise AssertionError("h_n3_cmjoin: cm_celltype missing in parent or brackets")

    def grp(cm: str) -> str | None:
        if cm == "Unknown":
            return None
        return cm_table.get(cm, cm)

    def joint(ct: np.ndarray, cm: np.ndarray) -> np.ndarray:
        out = np.array(ct, dtype=object)
        for i, c in enumerate(cm):
            g = grp(str(c))
            if g is not None:
                out[i] = f"{ct[i]}|{g}"
        return out

    jP = joint(ctx.ptypes, ctx.pcm)
    jL = joint(ctx.tL, ctx.cmL)
    jR = joint(ctx.tR, ctx.cmR)
    # resolve: joint state used only if >=30 cells in both brackets; else coarse
    cntL = pd.Series(jL).value_counts()
    cntR = pd.Series(jR).value_counts()
    finalP = np.array(ctx.ptypes, dtype=object)
    finalL = np.array(ctx.tL, dtype=object)
    finalR = np.array(ctx.tR, dtype=object)
    n_joint = 0
    for js in sorted(set(jL.tolist()) | set(jR.tolist())):
        if "|" not in js:
            continue
        if cntL.get(js, 0) >= 30 and cntR.get(js, 0) >= 30:
            n_joint += 1
            finalL[jL == js] = js
            finalR[jR == js] = js
            finalP[jP == js] = js
    pstates = sorted(set(finalP.tolist()))
    mLf, _, _ = common.means_vars_by_label(ctx.XL, finalL)
    mRf, _, _ = common.means_vars_by_label(ctx.XR, finalR)
    muPf, _, _ = common.means_vars_by_label(ctx.XP, finalP)
    sharedf = sorted(set(pstates) & set(mLf) & set(mRf))
    pPf = common.shares(finalP)
    pLf = common.shares(finalL)
    pRf = common.shares(finalR)
    X1 = ctx.XP.copy()
    for s in pstates:
        if s in sharedf:
            muT = (1.0 - ctx.lam) * mLf[s] + ctx.lam * mRf[s]
            X1[finalP == s] += (muT - muPf[s])
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    counts, raw = common.mass_counts_bridge(pstates, pPf, pLf, pRf, set(sharedf), ctx.lam, ctx.n)
    chosen = common.select_rows(finalP, counts, seed)
    final = common.dedup_names([ctx.pnames[i] for i in chosen])
    pd.DataFrame([{"state": s, "parent_n": int((finalP == s).sum()), "target_n": counts[s],
                   "share_pred": raw[s]} for s in pstates]
                 ).to_csv(run_dir / "intermediates" / f"mass_plan_{ctx.board}_{lane}.tsv",
                          sep="\t", index=False)
    res = finalize(ctx, run_dir, ctx.board, lane, version, X1[chosen], chosen, final,
                   base=ctx.P, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "cm_join_bridge+mass", "seed": seed,
                                     "cm_table": cm_table})
    res["diag"] = {"joint_states_resolved": n_joint, "final_states": len(pstates),
                   "shared_final_states": len(sharedf), "clip_fraction": clip_frac}
    return res


def build_h_o2_libnorm(ctx: InterpCtx, run_dir: Path, lane: str, version: str) -> dict:
    W = ctx.W
    X = common.dense(W.X).astype(np.float64)
    tW = np.asarray(W.obs["celltype"].astype(str))
    lam = ctx.lam
    for s in np.unique(tW):
        rows = np.flatnonzero(tW == s)
        libs = X[rows].sum(axis=1)
        ll = ctx.XL[ctx.tL == s].sum(axis=1)
        rr = ctx.XR[ctx.tR == s].sum(axis=1)
        if len(ll) == 0 or len(rr) == 0:
            continue
        tgt = ops.library_remap_targets(libs, ll, rr, lam)
        X[rows] = ops.apply_library_scale(X[rows], libs, tgt)
    chosen = np.arange(W.n_obs)
    final = [str(v) for v in W.obs_names]
    res = finalize(ctx, run_dir, ctx.board, lane, version, X, chosen, final,
                   base=W, normalization=NORM_MARKER[ctx.board],
                   provenance_extra={"method": "mass_bridge+library_rank_remap", "lambda": lam})
    res["diag"] = {"library_remap": "per-type rank-preserving", "expression_base": "v0013"}
    return res


# ------------------------------------------------------------------ extrap lane builders

def build_x_n1_lineage(ctx: ExtrapCtx, run_dir: Path, lane: str, version: str) -> dict:
    cand_means = {s: ctx.m875[s] for s in ctx.shared if ctx.n875[s] >= 30}
    lmap = ops.cosine_lineage_map(list(ctx.orphans), cand_means,
                                  {s: ctx.m95[s] for s in ctx.orphans})
    X = ctx.XV.copy()
    for t, a in lmap.items():
        X[ctx.tV == t] += ctx.baseline_delta(a)
    clip_frac = float((X < 0).mean())
    np.clip(X, 0, None, out=X)
    chosen = np.arange(ctx.V.n_obs)
    final = [str(v) for v in ctx.V.obs_names]
    res = finalize(ctx, run_dir, "extrap", lane, version, X, chosen, final,
                   base=ctx.V, normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "lineage_mapped_deltas", "lineage_map": lmap})
    res["diag"] = {"lineage_map": lmap, "n_orphans": len(ctx.orphans),
                   "clip_fraction": clip_frac}
    return res


def build_x_n2_trend3(ctx: ExtrapCtx, run_dir: Path, lane: str, version: str) -> dict:
    X = ctx.XV.copy()
    for s in ctx.three_way:
        rows = ctx.tV == s
        X[rows] = ctx.Xe95_src[rows] + ctx.trend_delta(s)
    clip_frac = float((X < 0).mean())
    np.clip(X, 0, None, out=X)
    chosen = np.arange(ctx.V.n_obs)
    final = [str(v) for v in ctx.V.obs_names]
    res = finalize(ctx, run_dir, "extrap", lane, version, X, chosen, final,
                   base=ctx.V, normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "three_stage_trend_delta_2v2-v1"})
    res["diag"] = {"three_way_states": ctx.three_way, "n_three_way": len(ctx.three_way),
                   "shared_states": ctx.shared, "clip_fraction": clip_frac}
    return res


def compmix_plan(ctx: ExtrapCtx, seed: int):
    types = sorted(ctx.m95.keys())
    times = [ctx.bc["stage_times"]["e825"], ctx.bc["stage_times"]["left"], ctx.bc["stage_times"]["right"]]
    p825, p875, p95 = common.shares(ctx.t825), common.shares(ctx.t875), common.shares(ctx.t95)
    S = np.array([[p825.get(s, 0.0), p875.get(s, 0.0), p95.get(s, 0.0)] for s in types])
    ref = S[:, -1]
    pred = ops.compmix_predict_shares(np.array(times), S, ctx.bc["stage_times"]["target"],
                                      ref, max_fold=2.0)
    raw = {s: float(pred[i]) for i, s in enumerate(types)}
    pstates = sorted(set(ctx.tV.tolist()))
    counts, raw_n = common.counts_from_raw({s: raw.get(s, 0.0) for s in pstates}, pstates, ctx.n)
    chosen = common.select_rows(ctx.tV, counts, seed)
    final = common.dedup_names([ctx.nV[i] for i in chosen])
    return chosen, final, counts, raw_n, types


def build_x_n3_compmix(ctx: ExtrapCtx, run_dir: Path, lane: str, version: str,
                       seed: int) -> dict:
    chosen, final, counts, raw_n, types = compmix_plan(ctx, seed)
    pd.DataFrame([{"state": s, "parent_n": int((ctx.tV == s).sum()), "target_n": counts[s],
                   "share_pred": raw_n[s]} for s in sorted(set(ctx.tV.tolist()))]
                 ).to_csv(run_dir / "intermediates" / f"mass_plan_extrap_{lane}.tsv",
                          sep="\t", index=False)
    res = finalize(ctx, run_dir, "extrap", lane, version, ctx.XV[chosen], chosen, final,
                   base=ctx.V, normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "composition_trend_extrapolation_mass",
                                     "seed": seed, "max_fold": 2.0})
    res["diag"] = {"n_states": len(types), "share_pred_sum": float(sum(raw_n.values()))}
    return res


def build_x_o1_trendshrink(ctx: ExtrapCtx, run_dir: Path, lane: str, version: str) -> dict:
    X = ctx.Xe95_src.astype(np.float64).copy()
    mean_w = []
    for s in ctx.shared:
        base = ctx.trend_delta(s) if s in ctx.three_way else ctx.baseline_delta(s)
        se = ctx.shrink_se(s)
        w = ops.shrink_weights(base, se, C=2.0)
        X[ctx.tV == s] += base * w
        mean_w.append(float(w.mean()))
    clip_frac = float((X < 0).mean())
    np.clip(X, 0, None, out=X)
    chosen = np.arange(ctx.V.n_obs)
    final = [str(v) for v in ctx.V.obs_names]
    res = finalize(ctx, run_dir, "extrap", lane, version, X, chosen, final,
                   base=ctx.V, normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "trend_delta_shrunk_C2"})
    res["diag"] = {"three_way_states": ctx.three_way, "mean_w_overall": float(np.mean(mean_w)),
                   "clip_fraction": clip_frac}
    return res


def build_x_o2_shrinkcomp(ctx: ExtrapCtx, run_dir: Path, lane: str, version: str,
                          seed: int) -> dict:
    # 1) recompute v0011 X exactly (mirror g0/t2_r2_shrink.py: ALL stats on float32)
    X95f = np.asarray(ctx.X95, dtype=np.float32)
    X875f = np.asarray(ctx.X875, dtype=np.float32)
    deltas = {}
    for t in sorted(set(ctx.t95.tolist())):
        mb = X95f[ctx.t95 == t]
        if (ctx.t875 == t).sum() == 0:
            deltas[t] = np.zeros(len(ctx.panel), dtype=np.float32)
            continue
        mp = X875f[ctx.t875 == t]
        m9, m8 = mb.mean(axis=0), mp.mean(axis=0)
        v9, v8 = mb.var(axis=0), mp.var(axis=0)
        n9, n8 = len(mb), len(mp)
        se = np.sqrt(v9 / n9 + v8 / n8) + 1e-12
        tstat = np.abs((m9 - m8) / se)
        w = (tstat / (tstat + 2.0)).astype(np.float32)
        deltas[t] = ((m9 - m8) * w).astype(np.float32)
    t_src = ctx.t95[ctx.src_idx]
    f32_src = X95f[ctx.src_idx]
    X_re = np.empty((ctx.n, len(ctx.panel)), dtype=np.float32)
    for j in range(ctx.n):
        X_re[j] = f32_src[j] + deltas[str(t_src[j])]
    X_re = np.clip(X_re, 0.0, None)
    v11 = common.load_parent(ctx.bc["shrink_parent"], ctx.bc["shrink_parent_sha256"])
    X_v11 = common.dense(v11.X).astype(np.float32)
    exact = bool(np.array_equal(X_re, X_v11))
    # 2) rerun x_n3 plan, assert names
    chosen, final, counts, raw_n, types = compmix_plan(ctx, seed)
    res = finalize(ctx, run_dir, "extrap", lane, version, X_re[chosen].astype(np.float64),
                   chosen, final, base=ctx.V, normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "shrunk_C2_expression+compmix_mass", "seed": seed})
    res["diag"] = {"v0011_recompute_exact": exact, "rows_match_x_n3": True}
    if not exact:
        res["diag"]["v0011_max_abs_diff"] = float(np.abs(X_re - X_v11).max())
    return res


# ------------------------------------------------------------------ driver

LANES = {
    "embryo": ["e_n1_qbridge", "e_n2_trend3", "e_n3_substate2", "e_o1_shrinkmerge", "e_o2_scalmass"],
    "heart": ["h_n1_qbridge", "h_n2_curve95", "h_n3_cmjoin", "h_o1_shrinkmerge", "h_o2_libnorm"],
    "extrap": ["x_n1_lineage", "x_n2_trend3", "x_n3_compmix", "x_o1_trendshrink", "x_o2_shrinkcomp"],
}


def build_one(board: str, lane: str, run_dir: Path, cfg: dict, ctx_cache: dict) -> dict:
    bc = cfg["boards"][board]
    version = bc["versions"][lane]
    seed = int(cfg["seed"])
    t0 = time.time()
    if board == "extrap":
        ctx = ctx_cache.get(board)
        if ctx is None:
            ctx = ctx_cache[board] = ExtrapCtx(bc)
        if lane == "x_n1_lineage":
            res = build_x_n1_lineage(ctx, run_dir, lane, version)
        elif lane == "x_n2_trend3":
            res = build_x_n2_trend3(ctx, run_dir, lane, version)
        elif lane == "x_n3_compmix":
            res = build_x_n3_compmix(ctx, run_dir, lane, version, seed)
        elif lane == "x_o1_trendshrink":
            res = build_x_o1_trendshrink(ctx, run_dir, lane, version)
        elif lane == "x_o2_shrinkcomp":
            res = build_x_o2_shrinkcomp(ctx, run_dir, lane, version, seed)
        else:
            raise ValueError(lane)
    else:
        ctx = ctx_cache.get(board)
        if ctx is None:
            ctx = ctx_cache[board] = InterpCtx(board, bc)
        if lane == "e_n1_qbridge" or lane == "h_n1_qbridge":
            res = build_e_n1_qbridge(ctx, run_dir, lane, version)
        elif lane == "e_o1_shrinkmerge" or lane == "h_o1_shrinkmerge":
            res = build_e_o1_shrinkmerge(ctx, run_dir, lane, version)
        elif lane == "e_o2_scalmass":
            res = build_e_o2_scalmass(ctx, run_dir, lane, version)
        elif lane == "e_n2_trend3":
            res = build_e_n2_trend3(ctx, run_dir, lane, version, seed)
        elif lane == "e_n3_substate2":
            res = build_e_n3_substate2(ctx, run_dir, lane, version, seed)
        elif lane == "h_n2_curve95":
            res = build_h_n2_curve95(ctx, run_dir, lane, version, seed)
        elif lane == "h_n3_cmjoin":
            res = build_h_n3_cmjoin(ctx, run_dir, lane, version, seed,
                                    cfg["mechanisms"]["cmjoin"]["cm_group_table"])
        elif lane == "h_o2_libnorm":
            res = build_h_o2_libnorm(ctx, run_dir, lane, version)
        else:
            raise ValueError(lane)
    res["lane"] = lane
    res["board"] = board
    res["version"] = version
    res["wall_s"] = time.time() - t0
    common.write_json(run_dir / "intermediates" / f"diag_{board}_{lane}.json",
                      {"lane": lane, "board": board, "version": version, **res["diag"]})
    print(json.dumps({"lane": lane, "sha256": res["sha256"], "wall_s": round(res["wall_s"], 1),
                      **{k: v for k, v in res["diag"].items() if not isinstance(v, (list, dict))}},
                     sort_keys=True), flush=True)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["verify", "build"])
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--lanes", default=None)
    ap.add_argument("--boards", default=None)
    args = ap.parse_args(argv)
    cfg = common.load_config()
    args.root.mkdir(parents=True, exist_ok=True)
    (args.root / "intermediates").mkdir(exist_ok=True)
    input_hashes = common.verify_all_inputs(cfg)
    if args.command == "verify":
        out = {"input_hashes": input_hashes, "config_sha256": common.sha256(common.CONFIG_PATH)}
        common.write_json(args.root / "INPUT_LOCK.json", out)
        print(json.dumps(out, indent=1, sort_keys=True))
        return 0
    boards = args.boards.split(",") if args.boards else list(LANES)
    only = set(args.lanes.split(",")) if args.lanes else None
    results = []
    ctx_cache: dict = {}
    for board in boards:
        for lane in LANES[board]:
            if only and lane not in only:
                continue
            results.append(build_one(board, lane, args.root, cfg, ctx_cache))
    summary_path = args.root / "BUILD_SUMMARY.json"
    merged: dict = {}
    if summary_path.exists():
        for r in json.loads(summary_path.read_text()).get("results", []):
            merged[(r["board"], r["lane"])] = r
    for r in results:
        merged[(r["board"], r["lane"])] = r
    ordered = [merged[k] for k in sorted(merged)]
    common.write_json(summary_path, {"results": ordered})
    print(json.dumps({"built": len(results), "total": len(ordered)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
