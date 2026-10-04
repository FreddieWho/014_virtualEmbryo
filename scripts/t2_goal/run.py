"""Lane builders for T2 goal round (frozen design 2026-10-01, reports/T2_GOAL_DESIGN_20261001.md).

Usage:
  python -m scripts.t2_goal.run verify --root RUN_DIR
  python -m scripts.t2_goal.run build  --root RUN_DIR [--lanes e_r1,h_r1,x_r1,e_r2,h_r2,x_r2]
  python -m scripts.t2_goal.run replay --root RUN_DIR --lane LANE

Deterministic given configs/t2_goal/design_20261001.json. No target data.
New code; reuses scripts.t2_round2.common/ops read-only (no lease needed, no writes there).
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

from scripts.t2_round2 import common, ops

REPO = common.REPO
CONFIG_PATH = REPO / "configs" / "t2_goal" / "design_20261001.json"
ATOM_ID = "T2-GOAL-20261001-v1"
GOAL_SEED = 20261001
ROUND2_BRIDGE_SEED = common.BRIDGE_SEED  # 20260904, for R2 row-plan reproduction only

BOARD_DIR = {"embryo": "T2_embryo_val_interp", "heart": "T2_heart_val_interp",
             "extrap": "T2_heart_val_extrap"}
CONTRACT_BOARD = {"embryo": "embryo:val_interp", "heart": "heart:val_interp",
                  "extrap": "heart:val_extrap"}
NORM_MARKER = {"embryo": "log1p_normalized", "heart": "log1p_normalized",
               "extrap": "log_normalized"}

LANES = {
    "e_r1": ("embryo", "v0016"), "e_r2": ("embryo", "v0017"),
    "h_r1": ("heart", "v0021"), "h_r2": ("heart", "v0022"),
    "x_r1": ("extrap", "v0022"), "x_r2": ("extrap", "v0023"),
}

THREE_STAGES = {"embryo": ("e675", "left", "right"), "heart": ("left", "right", "e95")}


def load_cfg() -> dict:
    return json.loads(CONFIG_PATH.read_text())


# ------------------------------------------------------------------ contexts

class GoalInterpCtx:
    """Incumbent pool + brackets for embryo/heart interp boards."""

    def __init__(self, board: str, bc: dict):
        self.board = board
        self.bc = bc
        self.panel = common.read_panel(bc["panel"])
        self.W = common.load_parent(bc["parent"], bc["parent_sha256"])
        self.XW = common.dense(self.W.X).astype(np.float64)
        self.wtypes = np.asarray(self.W.obs["celltype"].astype(str))
        self.wnames = [str(v) for v in self.W.obs_names]
        self.P = common.load_parent(bc["bridge_parent"], bc["bridge_parent_sha256"])
        self.XP = common.dense(self.P.X).astype(np.float64)
        self.ptypes = np.asarray(self.P.obs["celltype"].astype(str))
        self.pnames = [str(v) for v in self.P.obs_names]
        self.stages: dict[str, tuple] = {}
        for sk, sp in bc["stages"].items():
            self.stages[sk] = common.load_stage(sp, self.panel)
        self.lam = float(bc["lam"])
        self.n = int(bc["n_obs"])
        self.pstates = sorted(set(self.ptypes.tolist()))
        XL, tL, _, _ = self.stages["left"]
        XR, tR, _, _ = self.stages["right"]
        self.XL, self.tL = XL, tL
        self.XR, self.tR = XR, tR
        self.mL, self.vL, self.nL = common.means_vars_by_label(XL, tL)
        self.mR, self.vR, self.nR = common.means_vars_by_label(XR, tR)
        self.muP, _, _ = common.means_vars_by_label(self.XP, self.ptypes)
        self.shared = sorted(set(self.pstates) & set(self.mL) & set(self.mR))
        self.pP = common.shares(self.ptypes)
        self.pW = common.shares(self.wtypes)
        self.pL = common.shares(tL)
        self.pR = common.shares(tR)

    def three_way(self):
        s3key, sks = THREE_STAGES[self.board][0], THREE_STAGES[self.board]
        X3, t3, _, _ = self.stages[s3key]
        m3, _, _ = common.means_vars_by_label(X3, t3)
        p3 = common.shares(t3)
        return m3, p3, X3, t3

    def bridge_shift(self, state: str) -> np.ndarray:
        muT = (1.0 - self.lam) * self.mL[state] + self.lam * self.mR[state]
        return (muT - self.muP[state]).astype(np.float64)

    def winner_plan(self):
        counts, raw = common.mass_counts_bridge(
            self.pstates, self.pP, self.pL, self.pR, set(self.shared), self.lam, self.n)
        chosen = common.select_rows(self.ptypes, counts, ROUND2_BRIDGE_SEED)
        final = common.dedup_names([self.pnames[i] for i in chosen])
        winner_names = [str(v) for v in self.W.obs_names]
        if final != winner_names:
            raise AssertionError(f"{self.board}: plan != incumbent obs_names (plan drift)")
        return chosen, final, counts, raw


class GoalExtrapCtx:
    def __init__(self, bc: dict):
        self.bc = bc
        self.panel = common.read_panel(bc["panel"])
        self.V = common.load_parent(bc["parent"], bc["parent_sha256"])
        self.XV = common.dense(self.V.X).astype(np.float64)
        self.tV = np.asarray(self.V.obs["celltype"].astype(str))
        self.nV = [str(v) for v in self.V.obs_names]
        X825, t825, _, _ = common.load_stage(bc["stages"]["e825"], self.panel)
        X875, t875, _, _ = common.load_stage(bc["stages"]["left"], self.panel)
        X95, t95, _, _ = common.load_stage(bc["stages"]["right"], self.panel)
        self.m825, _, self.n825 = common.means_vars_by_label(X825, t825)
        self.m875, self.v875, self.n875 = common.means_vars_by_label(X875, t875)
        self.m95, self.v95, self.n95 = common.means_vars_by_label(X95, t95)
        self.n = int(bc["n_obs"])

    def baseline_delta(self, s: str) -> np.ndarray:
        return (self.m95[s] - self.m875[s]).astype(np.float64)

    def lateref_delta(self, s: str) -> np.ndarray:
        return (self.m95[s] - self.m825[s]).astype(np.float64)


# ------------------------------------------------------------------ output helper

def finalize(board: str, bc: dict, run_dir: Path, lane: str, version: str,
             X_out: np.ndarray, chosen: np.ndarray, final_names: list[str],
             *, base: ad.AnnData, normalization: str, provenance_extra: dict) -> dict:
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    if not np.isfinite(Xf).all() or (Xf < 0).any():
        raise AssertionError(f"{lane}: X not finite/nonnegative")
    if Xf.shape != (len(final_names), X_out.shape[1]):
        raise AssertionError(f"{lane}: shape mismatch")
    out_a = base[chosen].copy()
    out_a.obs_names = final_names
    out_a.X = Xf
    common.fix_obsm(out_a)
    prov = {"atom_id": ATOM_ID, "lane": lane, "board": bc["key"], "version": version,
            "seed": GOAL_SEED, "config_sha256": common.sha256(CONFIG_PATH),
            "parent_sha256": bc.get("parent_sha256"), "target_used": False,
            **provenance_extra}
    common.stamp_uns(out_a, normalization=normalization, provenance=prov)
    out = run_dir / "candidates" / board / lane / "submission.h5ad"
    sha = common.write_candidate(out_a, out)
    try:
        out_rel = str(out.resolve().relative_to(REPO))
    except ValueError:
        out_rel = str(out.resolve())  # replay temp dir lives outside repo
    common.source_row_ledger(run_dir / "intermediates" / f"source_row_ledger_{board}_{lane}.tsv",
                             chosen, [str(v) for v in base.obs_names], final_names)
    return {"output": out_rel, "sha256": sha,
            "n_obs": int(out_a.n_obs), "n_vars": int(out_a.n_vars)}


def eng_gate(X: np.ndarray, ref_libs: np.ndarray, ref_var: np.ndarray) -> dict:
    libs = X.sum(axis=1)
    lr = libs / np.maximum(ref_libs, 1e-12)
    q01, q99 = float(np.quantile(lr, 0.01)), float(np.quantile(lr, 0.99))
    vr = X.var(axis=0) / np.maximum(ref_var, 1e-12)
    ok = (q01 >= 0.25 and q99 <= 4.0 and bool(np.isfinite(vr).all())
          and float(np.nanmin(vr)) >= 0.1 and float(np.nanmax(vr)) <= 10.0)
    return {"lib_q01": q01, "lib_q99": q99, "var_min": float(np.nanmin(vr)),
            "var_max": float(np.nanmax(vr)), "pass": bool(ok)}


# ------------------------------------------------------------------ R1: compotrend (interp)

def dedup_names_pool(names: list[str], pool_names: list[str]) -> list[str]:
    """Dedup within output only (first occurrence keeps bare name); pool_names kept
    for signature compatibility. Bare pool names reused by single picks stay bare;
    only true repeats get __dupK (skipping any K already taken in output)."""
    _ = pool_names
    used: set[str] = set()
    out: list[str] = []
    for nm in names:
        cand, k = nm, 0
        while cand in used:
            k += 1
            cand = f"{nm}__dup{k}"
        used.add(cand)
        out.append(cand)
    if len(set(out)) != len(out):
        raise AssertionError("dedup_names_pool produced duplicate names")
    return out


def build_compotrend(board: str, bc: dict, run_dir: Path, lane: str, version: str) -> dict:
    ctx = GoalInterpCtx(board, bc)
    sks = THREE_STAGES[board]
    times = [bc["stage_times"][sk] for sk in sks]
    t_eval = bc["stage_times"]["target"]
    per_stage_shares = []
    for sk in sks:
        _, tk, _, _ = ctx.stages[sk]
        per_stage_shares.append(common.shares(tk))
    three = sorted(set(ctx.pW) & set().union(*[set(d) for d in per_stage_shares]))
    raw = {}
    for s in sorted(set(ctx.wtypes.tolist())):
        series = [d.get(s, 0.0) for d in per_stage_shares]
        if s in three and all(v > 0 for v in series):
            raw[s] = ops.share_series_predict(np.array(times), np.array(series), t_eval)
        else:
            raw[s] = ctx.pW.get(s, 0.0)
    pstates = sorted(set(ctx.wtypes.tolist()))
    counts, raw_n = common.counts_from_raw(raw, pstates, ctx.n)
    chosen = common.select_rows(ctx.wtypes, counts, GOAL_SEED)
    final = dedup_names_pool([ctx.wnames[i] for i in chosen], ctx.wnames)
    pd.DataFrame([{"state": s, "parent_n": int((ctx.wtypes == s).sum()),
                   "target_n": counts[s], "share_pred": raw_n[s]} for s in pstates]
                 ).to_csv(run_dir / "intermediates" / f"mass_plan_{board}_{lane}.tsv",
                          sep="\t", index=False)
    X_out = ctx.XW[chosen]  # expression identical to incumbent
    res = finalize(board, bc, run_dir, lane, version, X_out, chosen, final, base=ctx.W,
                   normalization=NORM_MARKER[board],
                   provenance_extra={"method": "trend_share_resample+incumbent_expression",
                                     "seed": GOAL_SEED, "t_eval": t_eval})
    gate = eng_gate(X_out, ctx.XW[chosen].sum(axis=1), ctx.XW.var(axis=0))
    res["diag"] = {"three_way_states": three, "n_three_way": len(three),
                   "fallback_states": sorted(set(pstates) - set(three)),
                   "expression_identical_to_incumbent": True,
                   "rows_from_incumbent_pool": True, "eng_gate": gate}
    res["composition_lane"] = True
    return res


# ------------------------------------------------------------------ R2: shrink C=1 (interp)

def build_shrinkc1(board: str, bc: dict, run_dir: Path, lane: str, version: str) -> dict:
    ctx = GoalInterpCtx(board, bc)
    X1 = ctx.XP.copy()
    wstats = []
    for s in ctx.pstates:
        if s in ctx.shared:
            shift = ctx.bridge_shift(s)
            se = ops.se_two_means(ctx.vL[s], ctx.nL[s], ctx.vR[s], ctx.nR[s])
            w = ops.shrink_weights(shift, se, C=1.0)
            X1[ctx.ptypes == s] += shift * w
            wstats.append(float(w.mean()))
        # unmatched: zeros (same convention as mean_shift_matrix)
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    chosen, final, counts, raw = ctx.winner_plan()  # asserts == incumbent rows
    res = finalize(board, bc, run_dir, lane, version, X1[chosen], chosen, final, base=ctx.P,
                   normalization=NORM_MARKER[board],
                   provenance_extra={"method": "mean_bridge_shrunk_C1+mass", "lambda": ctx.lam})
    gate = eng_gate(X1[chosen], ctx.XP[chosen].sum(axis=1), ctx.XP.var(axis=0))
    res["diag"] = {"mean_w_overall": float(np.mean(wstats)), "clip_fraction": clip_frac,
                   "rows_match_incumbent": True, "eng_gate": gate}
    return res


# ------------------------------------------------------------------ extrap lanes

def build_x_r1_lateref(bc: dict, run_dir: Path, lane: str, version: str) -> dict:
    ctx = GoalExtrapCtx(bc)
    shared = sorted(set(ctx.m95) & set(ctx.m825))
    X_out = ctx.XV.copy()
    for s in sorted(set(ctx.tV.tolist())):
        d = ctx.lateref_delta(s) if s in shared else np.zeros(ctx.XV.shape[1])
        X_out[ctx.tV == s] += d
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    chosen = np.arange(ctx.n)
    res = finalize("extrap", bc, run_dir, lane, version, X_out, chosen, list(ctx.nV), base=ctx.V,
                   normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "E8.25late_anchored_baseline_shift"})
    gate = eng_gate(X_out, ctx.XV.sum(axis=1), ctx.XV.var(axis=0))
    res["diag"] = {"shared_states": shared, "n_shared": len(shared),
                   "orphan_zero_states": sorted(set(ctx.tV.tolist()) - set(shared)),
                   "clip_fraction": clip_frac, "rows_match_parent": True,
                   "eng_gate": gate}
    return res


def build_x_r2_shrinkc1(bc: dict, run_dir: Path, lane: str, version: str) -> dict:
    ctx = GoalExtrapCtx(bc)
    shared = sorted(set(ctx.m95) & set(ctx.m875))
    X_out = ctx.XV.copy()
    for s in sorted(set(ctx.tV.tolist())):
        if s in shared:
            base = ctx.baseline_delta(s)
            se = ops.se_two_means(ctx.v875[s], ctx.n875[s], ctx.v95[s], ctx.n95[s]) + 1e-12
            tstat = np.abs(base / se)
            w = (tstat / (tstat + 1.0)).astype(np.float32)
            d = (base * w).astype(np.float32)
        else:
            d = np.zeros(ctx.XV.shape[1])
        X_out[ctx.tV == s] += d
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    chosen = np.arange(ctx.n)
    res = finalize("extrap", bc, run_dir, lane, version, X_out, chosen, list(ctx.nV), base=ctx.V,
                   normalization=NORM_MARKER["extrap"],
                   provenance_extra={"method": "baseline_shift_shrunk_C1_float32"})
    gate = eng_gate(X_out, ctx.XV.sum(axis=1), ctx.XV.var(axis=0))
    res["diag"] = {"shared_states": shared, "n_shared": len(shared),
                   "clip_fraction": clip_frac, "rows_match_parent": True,
                   "eng_gate": gate}
    return res


BUILDERS = {
    "e_r1": lambda bc, rd, ln, v: build_compotrend("embryo", bc, rd, ln, v),
    "h_r1": lambda bc, rd, ln, v: build_compotrend("heart", bc, rd, ln, v),
    "e_r2": lambda bc, rd, ln, v: build_shrinkc1("embryo", bc, rd, ln, v),
    "h_r2": lambda bc, rd, ln, v: build_shrinkc1("heart", bc, rd, ln, v),
    "x_r1": lambda bc, rd, ln, v: build_x_r1_lateref(bc, rd, ln, v),
    "x_r2": lambda bc, rd, ln, v: build_x_r2_shrinkc1(bc, rd, ln, v),
}


MASS_LANE_EXEMPTIONS = {
    "candidate obs_names/order does not exactly match the locked parent",
    "candidate obs metadata does not exactly match the locked parent",
    "candidate layers content changed relative to the locked parent",
    "candidate raw content changed relative to the locked parent",
}


def classify_contract(cc: dict, *, composition_lane: bool) -> tuple[str, str]:
    """Return (verdict, detail). PASS, or pre-declared pass_with_deviation for
    composition lanes whose ONLY errors are the 4 frozen exemption classes."""
    status = cc.get("status")
    if status == "PASS" and cc.get("valid"):
        return "pass", json.dumps(cc)[:3000]
    errs = [str(e) for e in cc.get("errors", [])]
    if composition_lane and errs and all(e in MASS_LANE_EXEMPTIONS for e in errs):
        return "pass_with_deviation", "exempted[" + "; ".join(errs) + "]"
    return "fail", json.dumps({"status": status, "errors": errs,
                                 "warnings": cc.get("warnings", [])})[:2000]


def do_build(root: Path, lanes: list[str]) -> dict:
    cfg = load_cfg()
    out: dict[str, dict] = {}
    for lane in lanes:
        board, version = LANES[lane]
        bc = cfg["boards"][board]
        res = BUILDERS[lane](bc, root, lane, version)
        res["lane"], res["version"], res["board"] = lane, version, board
        cc = common.contract_check(root / "candidates" / board / lane / "submission.h5ad",
                                   board=CONTRACT_BOARD[board], parent_rel=bc["parent"],
                                   parent_sha=bc["parent_sha256"])
        res["composition_lane"] = res.get("composition_lane", False)
        verdict, detail = classify_contract(cc, composition_lane=res["composition_lane"])
        res["contract"] = {"verdict": verdict, "detail": detail}
        if verdict == "fail":
            raise AssertionError(f"{lane}: contract FAIL: {detail[:500]}")
        # deterministic replay: rebuild expression hash and compare
        res["replay"] = {"note": "replay via `replay` subcommand (byte compare)"}
        common.write_json(root / "checks" / f"{lane}_{version}.json", res)
        out[lane] = res
        print(f"built {lane} {version}: {res['sha256'][:12]} contract={verdict}", flush=True)
    common.write_json(root / "BUILD_SUMMARY.json", out)
    return out


def do_contract(root: Path, lanes: list[str]) -> dict:
    """Re-evaluate contract on already-built candidates (no rebuild)."""
    cfg = load_cfg()
    out: dict[str, dict] = {}
    for lane in lanes:
        board, version = LANES[lane]
        bc = cfg["boards"][board]
        cc = common.contract_check(root / "candidates" / board / lane / "submission.h5ad",
                                   board=CONTRACT_BOARD[board], parent_rel=bc["parent"],
                                   parent_sha=bc["parent_sha256"])
        comp = lane in ("e_r1", "h_r1")
        verdict, detail = classify_contract(cc, composition_lane=comp)
        fp = root / "checks" / f"{lane}_{version}.json"
        res = json.loads(fp.read_text()) if fp.exists() else {}
        res["contract"] = {"verdict": verdict, "detail": detail}
        if verdict == "fail":
            raise AssertionError(f"{lane}: contract FAIL: {detail[:500]}")
        common.write_json(fp, res)
        out[lane] = verdict
        print(f"contract {lane} {version}: {verdict}", flush=True)
    return out


def do_verify(root: Path) -> dict:
    cfg = load_cfg()
    assert CONFIG_PATH.exists(), "config missing"
    assert cfg["seed"] == GOAL_SEED and cfg["no_parameter_search"] is True
    assert cfg["target_used"] is False
    for board, bc in cfg["boards"].items():
        common.load_parent(bc["parent"], bc["parent_sha256"])
        if "bridge_parent" in bc:
            common.load_parent(bc["bridge_parent"], bc["bridge_parent_sha256"])
        for sk, sp in bc["stages"].items():
            assert (REPO / sp).exists(), f"missing stage {sp}"
        common.read_panel(bc["panel"])
    return {"ok": True, "config_sha256": common.sha256(CONFIG_PATH)}


def do_replay(root: Path, lane: str) -> dict:
    import hashlib
    board, version = LANES[lane]
    p = root / "candidates" / board / lane / "submission.h5ad"
    before = hashlib.sha256(p.read_bytes()).hexdigest()
    # rebuild into a temp root then compare bytes
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "candidates").mkdir(parents=True)
        (t / "intermediates").mkdir(parents=True)
        (t / "checks").mkdir(parents=True)
        cfg = load_cfg()
        bc = cfg["boards"][board]
        res = BUILDERS[lane](bc, t, lane, version)
        after = hashlib.sha256((t / "candidates" / board / lane / "submission.h5ad").read_bytes()).hexdigest()
    ok = (before == after)
    print(f"replay {lane}: {ok} ({before[:12]} vs {after[:12]})", flush=True)
    return {"ok": ok, "before": before, "after": after, "replay_sha": res["sha256"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["verify", "build", "replay", "contract"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--lanes", default=",".join(LANES))
    ap.add_argument("--lane", default=None)
    a = ap.parse_args()
    root = Path(a.root)
    if not root.is_absolute():
        root = REPO / root
    if a.cmd == "verify":
        print(json.dumps(do_verify(root), indent=1))
    elif a.cmd == "build":
        lanes = [l.strip() for l in a.lanes.split(",") if l.strip()]
        bad = [l for l in lanes if l not in LANES]
        if bad:
            raise SystemExit(f"unknown lanes: {bad}")
        do_build(root, lanes)
    elif a.cmd == "contract":
        lanes = [l.strip() for l in a.lanes.split(",") if l.strip()]
        do_contract(root, lanes)
    elif a.cmd == "replay":
        if not a.lane:
            raise SystemExit("--lane required")
        print(json.dumps(do_replay(root, a.lane), indent=1))


if __name__ == "__main__":
    main()
