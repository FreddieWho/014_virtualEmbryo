"""Local scorer evaluation for T2 round2 lanes (record-only / flagging).

Embryo: pseudo-target E7.25, reference E6.75, seed 20260830 (record-only per M0 App B).
Heart interp: pseudo-target E8.75, reference E8.25_late, seed 20260830 (nmmd 5% flag).
Extrap: R1 proxy (E9.5 cardiac target / E8.75 cardiac reference), seed 20260916
(proxy known directionally wrong on two families; record-only).

Usage: python -m scripts.t2_round2.score_local --root RUN_DIR [--only lane1,lane2]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from scripts.t2_round2 import common
from scripts.t2_round2.run import LANES

REPO = common.REPO

EVAL_SPEC = {
    "embryo": {"setting": "embryo", "target": "data/E7.25.h5ad", "reference": "data/E6.75.h5ad",
               "seed": 20260830, "mode": "record_only"},
    "heart": {"setting": "heart", "target": "data/E8.75.h5ad", "reference": "data/E8.25_late.h5ad",
              "seed": 20260830, "mode": "flag_5pct_nmmd"},
    "extrap": {"setting": "heart",
               "target": "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad",
               "reference": "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad",
               "seed": 20260916, "mode": "record_plus_nmmd_flag"},
}

KEEP = ("de_score", "de_direction", "energy_distance", "mmd_u", "neighborhood_mmd",
        "morans_I_agreement", "variogram", "d2_shape", "occupancy_dice",
        "sliced_wasserstein", "scale_log_ratio", "count_log_ratio",
        "library_size_ratio", "variance_ratio", "pb_rel_err", "pseudobulk_pearson")


def score_one(input_rel: str, spec: dict, out_json: Path) -> dict:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T2",
           "--setting", spec["setting"], "--input", str(REPO / input_rel),
           "--target", str(REPO / spec["target"]), "--reference", str(REPO / spec["reference"]),
           "--seed", str(spec["seed"]), "--out", str(out_json)]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"scorer failed for {input_rel}: {r.stderr[-1500:]}")
    m = json.loads(out_json.read_text())["metrics"]
    slim = {k: m.get(k) for k in KEEP}
    slim["_wall_s"] = round(time.time() - t0, 1)
    return slim


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--only", default=None)
    args = ap.parse_args(argv)
    cfg = common.load_config()
    summ = json.loads((args.root / "BUILD_SUMMARY.json").read_text())
    only = set(args.only.split(",")) if args.only else None
    outdir = args.root / "local_eval"
    report: dict = {}
    # parents first (same-session reference values)
    parent_scores: dict = {}
    for board in LANES:
        spec = EVAL_SPEC[board]
        bc = cfg["boards"][board]
        pj = outdir / f"parent_{board}.json"
        if pj.exists():
            slim = json.loads(pj.read_text())
        else:
            slim = score_one(bc["parent"], spec, pj)
        parent_scores[board] = slim
        report[f"parent_{board}"] = slim
        print(json.dumps({f"parent_{board}": {k: slim[k] for k in ("neighborhood_mmd", "de_score", "variogram") if k in slim}}), flush=True)
    for r in summ["results"]:
        board, lane = r["board"], r["lane"]
        if only and lane not in only:
            continue
        spec = EVAL_SPEC[board]
        oj = outdir / f"{board}_{lane}.json"
        if oj.exists():
            slim = json.loads(oj.read_text())
        else:
            slim = score_one(r["output"], spec, oj)
        p = parent_scores[board]
        entry = {"metrics": slim}
        for k in KEEP:
            if isinstance(slim.get(k), (int, float)) and isinstance(p.get(k), (int, float)):
                entry[f"d_{k}"] = round(slim[k] - p[k], 6)
        if spec["mode"] == "flag_5pct_nmmd" and isinstance(slim.get("neighborhood_mmd"), (int, float)):
            base = p.get("neighborhood_mmd")
            if base and base > 0:
                rel = (slim["neighborhood_mmd"] - base) / base
                entry["nmmd_rel_change"] = round(rel, 6)
                entry["flag"] = "LOCAL_DEGRADE_FLAG" if rel > 0.05 else "ok"
        report[f"{board}/{lane}"] = entry
        print(json.dumps({f"{board}/{lane}": {k: entry.get(k) for k in
                         ("neighborhood_mmd", "d_neighborhood_mmd", "nmmd_rel_change", "flag", "de_score", "d_de_score", "variogram", "d_variogram")}}),
              flush=True)
    common.write_json(outdir / "LOCAL_EVAL_SUMMARY.json", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
