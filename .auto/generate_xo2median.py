"""Iter9: x_o2-analog 3-seed median (LAST DE-primary shot, pre-committed bar).

Rebuilds the x_o2 mechanism faithfully (v0011-shrink expression C=2 float32,
asserted exact vs scored v0011 parent; compmix mass plan with max_fold 2.0) at
3 seeds: design seed 20260929 (must reproduce local 0.2603 — harness check) +
20261004 + 20261005. Scores all three with the frozen proxy spec, reports
per-seed de + median + min.

Pre-committed keep bar (written before seeing results): KEEP iff
min(de_3seeds) > 0.2466, i.e. ALL THREE seeds beat baseline = seed-robust.
Anything less = row-luck, DISCARD. No post-hoc bar-moving.
"""
from pathlib import Path
import json
import subprocess
import sys
import time
import numpy as np
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common
from scripts.t2_round2 import run as r2run

SEEDS = [20260929, 20261004, 20261005]
BASELINE_DE = 0.2466
TARGET = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad"
REF = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad"

def score(path: Path) -> dict:
    out = path.with_suffix(".score.json")
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib",
           f"PYTHONPATH={REPO}/third_party/veckit",
           "python", f"{REPO}/third_party/veckit/score_h5ad.py",
           "--task", "T2", "--setting", "heart", "--input", str(path),
           "--target", str(TARGET), "--reference", str(REF),
           "--seed", "20260916", "--out", str(out)]
    r = subprocess.run(" ".join(cmd), shell=True, cwd=str(REPO),
                       capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"scorer failed: {r.stderr[-800:]}")
    return json.loads(out.read_text())["metrics"]

def main():
    cfg = common.load_config()
    bc = cfg["boards"]["extrap"]
    ctx = r2run.ExtrapCtx(bc)
    # 1) v0011 expression recompute (mirror build_x_o2_shrinkcomp block 1)
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
    v11 = common.load_parent(bc["shrink_parent"], bc["shrink_parent_sha256"])
    exact = bool(np.array_equal(X_re, common.dense(v11.X).astype(np.float32)))
    print(f"v0011_recompute_exact={exact}", flush=True)
    assert exact, "v0011 recompute drifted — STOP, do not score"
    # 2) three seeds
    results = []
    for sd in SEEDS:
        chosen, final, counts, raw_n, types = r2run.compmix_plan(ctx, sd)
        out_a = ctx.V[chosen].copy()
        out_a.obs_names = final
        out_a.X = np.ascontiguousarray(X_re[chosen].astype(np.float64), dtype=np.float32)
        common.fix_obsm(out_a)
        common.stamp_uns(out_a, normalization="log_normalized",
                         provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP", "iter": 9,
                                     "method": "xo2_analog_shrinkC2expr_compmix",
                                     "seed": sd, "target_used": False})
        p = REPO / ".auto" / f"cand_xo2_s{sd}.h5ad"
        if p.exists():
            p.unlink()
        common.write_candidate(out_a, p)
        m = score(p)
        de, dd = float(m["de_score"]), float(m["de_direction"])
        results.append({"seed": sd, "de": de, "dir": dd,
                        "nmmd": float(m["neighborhood_mmd"])})
        print(f"seed {sd}: de={de} dir={dd}", flush=True)
    des = sorted(r["de"] for r in results)
    med, mn = float(np.median(des)), des[0]
    print(f"MEDIAN de={med} MIN de={mn} BASELINE={BASELINE_DE}", flush=True)
    print(f"METRIC de_seed20260929={results[0]['de']}")
    print(f"METRIC de_seed20261004={results[1]['de']}")
    print(f"METRIC de_seed20261005={results[2]['de']}")
    print(f"METRIC de_median={med}")
    print(f"METRIC de_min={mn}")
    verdict = "KEEP" if mn > BASELINE_DE else "DISCARD"
    print(f"VERDICT={verdict} (bar: min3 > {BASELINE_DE})", flush=True)
    (REPO / ".auto" / "iter9_summary.json").write_text(json.dumps(
        {"seeds": results, "median": med, "min": mn,
         "baseline": BASELINE_DE, "verdict": verdict}, indent=1))

if __name__ == "__main__":
    main()
