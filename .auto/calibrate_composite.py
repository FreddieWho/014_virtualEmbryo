#!/usr/bin/env python3
"""Calibration batch: local composite for every previously SERVER-SCORED extrap lane.

Purpose: test whether the frozen 8-channel composite tracks the portal board score on
this board (proxy validity), using lanes whose server scores already exist. This is
calibration/diagnostic work done BEFORE the new algorithm sweep, not metric tuning:
the composite definition in .auto/composite_config.json is frozen and is NOT changed
based on these results (if it looks bad, that gets recorded, not fixed).

Writes .auto/calibration_proxy_validity.json and prints a ranked table.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / ".auto"))
from composite import composite  # noqa: E402

TARGET = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad"
REF = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad"
CAND = REPO / "submissions/candidates/T2_heart_val_extrap"

# (label, candidate dir, server board score) — server scores from reports/SERVER_SCORE_REGISTRY.md
LANES = [
    ("baseline_v0001", None, 50.53),
    ("v0011_g0_t2_r2_shrink", "v0011_g0_t2_r2_shrink", 50.64),
    ("v0012_g0_t2_r3_spatial", "v0012_g0_t2_r3_spatial", 50.26),
    ("v0013_g0_t2_r4_k07", "v0013_g0_t2_r4_k07", 50.32),
    ("v0016_g0_t2_r5_k60", "v0016_g0_t2_r5_k60", 50.25),
    ("v0017_x_n1_lineage", "v0017_x_n1_lineage", 48.17),
    ("v0018_x_n2_trend3", "v0018_x_n2_trend3", 48.40),
    ("v0019_x_n3_compmix", "v0019_x_n3_compmix", 50.38),
    ("v0020_x_o1_trendshrink", "v0020_x_o1_trendshrink", 48.59),
    ("v0021_x_o2_shrinkcomp", "v0021_x_o2_shrinkcomp", 50.52),
    ("v0022_x_r1_lateref", "v0022_x_r1", 50.74),
    ("v0023_x_r2_shrinkc1", "v0023_x_r2", 50.03),
]


def score(cand: Path, out_json: Path) -> dict:
    if out_json.exists():
        return json.loads(out_json.read_text())["metrics"]
    cmd = (f"env LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH={REPO}/third_party/veckit "
           f"python {REPO}/third_party/veckit/score_h5ad.py --task T2 --setting heart "
           f"--input {cand} --target {TARGET} --reference {REF} --seed 20260916 --out {out_json}")
    r = subprocess.run(cmd, shell=True, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"scorer failed on {cand}: {r.stderr[-600:]}")
    return json.loads(out_json.read_text())["metrics"]


def main() -> int:
    outdir = REPO / ".auto" / "calibration"
    outdir.mkdir(exist_ok=True)
    rows = []
    for label, sub, server in LANES:
        cand = (REPO / "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
                if sub is None else CAND / sub / "submission.h5ad")
        if not cand.exists():
            print(f"SKIP {label}: missing {cand}", flush=True)
            continue
        m = score(cand, outdir / f"{label}.json")
        c = composite(m)
        rows.append({"label": label, "server_board": server, "composite": c["composite"],
                     "worst_channel": c["worst_channel"], "guards": c["guardrails_pass"],
                     "gains": {k: (None if v is None else round(v, 4)) for k, v in c["gains"].items()}})
        print(f"{label:26} server={server:6.2f} composite={c['composite']:8.3f} worst={c['worst_channel']}", flush=True)
    # rank correlation between composite and server board
    pairs = [(r["composite"], r["server_board"]) for r in rows if r["composite"] is not None]
    n = len(pairs)
    summary = {"n": n, "rows": rows}
    if n >= 3:
        xs = sorted(range(n), key=lambda i: pairs[i][0])
        ys = sorted(range(n), key=lambda i: pairs[i][1])
        rank_x = {i: k for k, i in enumerate(xs)}
        rank_y = {i: k for k, i in enumerate(ys)}
        d2 = sum((rank_x[i] - rank_y[i]) ** 2 for i in range(n))
        rho = 1 - (6 * d2) / (n * (n * n - 1))
        summary["spearman_composite_vs_server"] = round(rho, 4)
        # also vs the variogram channel only
        print(f"\nSpearman(composite, server board) = {rho:.3f}  (n={n})", flush=True)
    (outdir / "calibration_proxy_validity.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
