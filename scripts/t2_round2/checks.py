"""Post-build checks for T2 round2: contract, engineering gate, replay.

Usage:
  python -m scripts.t2_round2.checks contract --root RUN_DIR
  python -m scripts.t2_round2.checks gate --root RUN_DIR
  python -m scripts.t2_round2.checks replay --root RUN_DIR --replay-root REPLAY_DIR
  python -m scripts.t2_round2.checks all --root RUN_DIR [--replay-root REPLAY_DIR]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.t2_round2 import common
from scripts.t2_round2.run import CONTRACT_BOARD, LANES

REPO = common.REPO

MASS_EXEMPT = {
    "candidate obs_names/order does not exactly match the locked parent",
    "candidate obs metadata does not exactly match the locked parent",
    "candidate layers content changed relative to the locked parent",
    "candidate raw content changed relative to the locked parent",
}

# parent mode per lane: "strict" = strict parent is the board winner/baseline;
# "mass" = bridge parent + composition-change exemptions.
PARENT_MODE = {
    "e_n1_qbridge": "strict", "e_o1_shrinkmerge": "strict", "e_o2_scalmass": "strict",
    "e_n2_trend3": "mass", "e_n3_substate2": "mass",
    "h_n1_qbridge": "strict", "h_o1_shrinkmerge": "strict", "h_o2_libnorm": "strict",
    "h_n2_curve95": "mass", "h_n3_cmjoin": "mass",
    "x_n1_lineage": "strict", "x_n2_trend3": "strict", "x_o1_trendshrink": "strict",
    "x_n3_compmix": "mass", "x_o2_shrinkcomp": "mass",
}

IMMEDIATE_PARENT = {  # for engineering gate row correspondence
    "embryo": "parent", "heart": "parent", "extrap": "parent",
}

# which AnnData the lane's ledger parent_row indexes into
GATE_BASE = {
    "e_n1_qbridge": "bridge_parent", "e_o1_shrinkmerge": "bridge_parent",
    "e_n2_trend3": "bridge_parent", "e_n3_substate2": "bridge_parent",
    "e_o2_scalmass": "parent",
    "h_n1_qbridge": "bridge_parent", "h_o1_shrinkmerge": "bridge_parent",
    "h_n2_curve95": "bridge_parent", "h_n3_cmjoin": "bridge_parent",
    "h_o2_libnorm": "parent",
    "x_n1_lineage": "parent", "x_n2_trend3": "parent", "x_n3_compmix": "parent",
    "x_o1_trendshrink": "parent", "x_o2_shrinkcomp": "parent",
}


def lane_result(root: Path, board: str, lane: str) -> dict:
    summ = json.loads((root / "BUILD_SUMMARY.json").read_text())
    for r in summ["results"]:
        if r["board"] == board and r["lane"] == lane:
            return r
    raise KeyError(f"{board}/{lane} not in BUILD_SUMMARY")


def run_contract(root: Path, cfg: dict) -> pd.DataFrame:
    rows = []
    for board, lanes in LANES.items():
        bc = cfg["boards"][board]
        for lane in lanes:
            res = lane_result(root, board, lane)
            mode = PARENT_MODE[lane]
            if mode == "strict":
                parent_rel, parent_sha = bc["parent"], bc["parent_sha256"]
            else:
                if board == "extrap":
                    parent_rel, parent_sha = bc["parent"], bc["parent_sha256"]
                else:
                    parent_rel, parent_sha = bc["bridge_parent"], bc["bridge_parent_sha256"]
            r = common.contract_check(REPO / res["output"], board=CONTRACT_BOARD[board],
                                      parent_rel=parent_rel, parent_sha=parent_sha)
            status = str(r.get("status"))
            errors = [str(e) for e in r.get("errors", [])]
            verdict = "PASS"
            if status.lower() != "pass":
                if mode == "mass" and set(errors) <= MASS_EXEMPT:
                    verdict = "FAIL_BY_DESIGN_ACCEPTED"
                else:
                    verdict = "FAIL"
            rows.append({"board": board, "lane": lane, "version": res["version"],
                         "mode": mode, "contract_status": status, "verdict": verdict,
                         "errors": " | ".join(errors)})
            print(json.dumps(rows[-1], sort_keys=True), flush=True)
            if verdict == "FAIL":
                raise RuntimeError(f"contract FAIL for {board}/{lane}: {errors}")
    df = pd.DataFrame(rows)
    out = root / "checks" / "contract_checks.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, sep="\t", index=False)
    return df


def run_gate(root: Path, cfg: dict) -> dict:
    gate_cfg = cfg["engineering_gate"]
    report: dict = {}
    for board, lanes in LANES.items():
        bc = cfg["boards"][board]
        parent = common.load_parent(bc["parent"], bc["parent_sha256"])
        XP = common.dense(parent.X).astype(np.float64)
        libP = XP.sum(axis=1)
        varP = float(XP.var())
        pnames = [str(v) for v in parent.obs_names]
        for lane in lanes:
            res = lane_result(root, board, lane)
            led = pd.read_csv(root / "intermediates" / f"source_row_ledger_{board}_{lane}.tsv",
                              sep="\t")
            src = led["parent_row"].to_numpy()
            # ledger parent rows index into the lane's BASE annData. For lanes built
            # from the bridge parent (mass lanes), base == bridge_parent; otherwise
            # base == immediate parent. Recompute library on the base actually used.
            mode = GATE_BASE[lane]
            if mode == "bridge_parent":
                base = common.load_parent(bc["bridge_parent"], bc["bridge_parent_sha256"])
            else:
                base = parent
            XB = common.dense(base.X).astype(np.float64)
            libB = XB.sum(axis=1)
            cand = common.ad.read_h5ad(REPO / res["output"], backed="r")
            XC = common.dense(cand.X).astype(np.float64)
            n_obs, n_vars = cand.n_obs, cand.n_vars
            cand.file.close()
            libC = XC.sum(axis=1)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = libC / np.where(libB[src] == 0, np.nan, libB[src])
            ratio = ratio[np.isfinite(ratio) & (libB[src] > 0)]
            var_ratio = float(XC.var() / varP) if varP > 0 else float("nan")
            q01, q99 = float(np.quantile(ratio, 0.01)), float(np.quantile(ratio, 0.99))
            ok = (q01 >= gate_cfg["library_ratio_q01_min"]
                  and q99 <= gate_cfg["library_ratio_q99_max"]
                  and gate_cfg["variance_ratio_min"] <= var_ratio <= gate_cfg["variance_ratio_max"]
                  and np.isfinite(XC).all() and (XC >= 0).all()
                  and n_obs == bc["n_obs"] and n_vars == len(common.read_panel(bc["panel"])))
            report[f"{board}/{lane}"] = {
                "lib_ratio_q01": q01, "lib_ratio_q99": q99, "var_ratio": var_ratio,
                "n_obs": int(n_obs), "n_vars": int(n_vars), "gate_pass": bool(ok)}
            print(json.dumps({board + "/" + lane: report[f"{board}/{lane}"]}, sort_keys=True),
                  flush=True)
            if not ok:
                raise RuntimeError(f"engineering gate FAIL for {board}/{lane}: "
                                   f"{report[f'{board}/{lane}']}")
    common.write_json(root / "checks" / "engineering_gate.json", report)
    return report


def run_replay(root: Path, replay_root: Path, cfg: dict) -> dict:
    report: dict = {}
    ok_all = True
    for board, lanes in LANES.items():
        for lane in lanes:
            a = root / "candidates" / board / lane / "submission.h5ad"
            b = replay_root / "candidates" / board / lane / "submission.h5ad"
            if not a.exists() or not b.exists():
                report[f"{board}/{lane}"] = {"replay": "MISSING", "a": a.exists(), "b": b.exists()}
                ok_all = False
                continue
            ha, hb = common.sha256(a), common.sha256(b)
            same = ha == hb
            ok_all &= same
            report[f"{board}/{lane}"] = {"replay": "BYTE_IDENTICAL" if same else "MISMATCH",
                                         "sha256": ha}
            print(json.dumps({f"{board}/{lane}": report[f"{board}/{lane}"]}, sort_keys=True),
                  flush=True)
    report["_all"] = {"byte_identical": bool(ok_all)}
    common.write_json(root / "checks" / "replay.json", report)
    if not ok_all:
        raise RuntimeError("replay mismatch; see checks/replay.json")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["contract", "gate", "replay", "all"])
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--replay-root", type=Path, default=None)
    args = ap.parse_args(argv)
    cfg = common.load_config()
    if args.command in ("contract", "all"):
        run_contract(args.root, cfg)
    if args.command in ("gate", "all"):
        run_gate(args.root, cfg)
    if args.command in ("replay", "all"):
        if args.replay_root is not None:
            run_replay(args.root, args.replay_root, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
