"""iter19/20 (Route C): time-normalized QTE, optionally x compmix. PRINCIPLED CORRECTION.

iter12 extrapolates from the E8.75->E9.5 interval (0.75 Myr... time units) to t=10.5, a
distance of 1.0 units, but scales the shift by 1.0. The canonical linear rule scales by
dt_target / dt_source = 1.0 / 0.75 = 4/3. The project used the same 4/3 convention before
in the mean-shift lane v0009 'time1333'. So this is a correction of a known under-
extrapolation, not a searched knob (no scan; 4/3 is arithmetically determined).

  Qpred(p) = Q9(p) + (4/3) * (Q9(p) - Q8(p))

Usage: python .auto/generate_qte_time.py [--compmix]   (compmix = 3 seeds, median rule)
"""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / ".auto"))
from scripts.t2_round2 import common
from composite import composite

PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / ".auto" / "candidate.h5ad"
GRID = 2001
FACTOR = 4.0 / 3.0
TARGET = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad"
REF = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad"
SEEDS = [20261008]


def qte_time(XV, tV, X875, t875, X95, t95, pgrid):
    X_out = XV.copy()
    for s in sorted(set(t95.tolist()) & set(t875.tolist())):
        pred_idx = np.flatnonzero(tV == s)
        Xs = XV[pred_idx]
        o = np.argsort(Xs, axis=0, kind="stable")
        r = np.empty_like(o)
        np.put_along_axis(r, o, np.arange(len(pred_idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
        p2 = (r + 0.5) / len(pred_idx)
        Q9 = np.quantile(X95[t95 == s], pgrid, axis=0)
        Q8 = np.quantile(X875[t875 == s], pgrid, axis=0)
        Qpred = Q9 + FACTOR * (Q9 - Q8)
        new = np.empty_like(Xs)
        for g in range(Xs.shape[1]):
            new[:, g] = np.interp(p2[:, g], pgrid, Qpred[:, g])
        X_out[pred_idx] = new
    return np.clip(X_out, 0, None)


def score(path):
    out = path.with_suffix(".score.json")
    cmd = (f"env LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH={REPO}/third_party/veckit "
           f"python {REPO}/third_party/veckit/score_h5ad.py --task T2 --setting heart "
           f"--input {path} --target {TARGET} --reference {REF} --seed 20260916 --out {out}")
    r = subprocess.run(cmd, shell=True, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    return json.loads(out.read_text())["metrics"]


def main():
    use_compmix = "--compmix" in sys.argv
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    Xq = qte_time(XV, tV, X875, t875, X95, t95, pgrid)
    if not use_compmix:
        out_a = V.copy()
        out_a.X = np.ascontiguousarray(Xq, dtype=np.float32)
        common.fix_obsm(out_a)
        common.stamp_uns(out_a, normalization="log_normalized",
                         provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 19,
                                     "method": "qte_time_normalized_4over3", "target_used": False})
        if OUT.exists():
            OUT.unlink()
        sha = common.write_candidate(out_a, OUT)
        m = score(OUT)
        c = composite(m)
        print(f"iter19 QTE-time: sha={sha[:12]} composite={c['composite']:.4f} expr={c['expr_composite']:.4f} "
              f"guards={c['guardrails_pass']} worst={c['worst_channel']}")
        print("gains:", {k: (None if v is None else round(v, 4)) for k, v in c["gains"].items()})
        return
    from scripts.t2_round2 import run as r2run
    ctx = r2run.ExtrapCtx(common.load_config()["boards"]["extrap"])
    results = []
    for sd in SEEDS:
        chosen, final, counts, raw_n, types = r2run.compmix_plan(ctx, sd)
        out_a = V[chosen].copy()
        out_a.obs_names = final
        out_a.X = np.ascontiguousarray(Xq[chosen], dtype=np.float32)
        common.fix_obsm(out_a)
        common.stamp_uns(out_a, normalization="log_normalized",
                         provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 20,
                                     "method": "qte_time_normalized_4over3_x_compmix", "seed": sd,
                                     "target_used": False})
        p = REPO / "artifacts" / "autoresearch" / "t2-extrap-20261001-v1" / "submission.iter20-qte-time-compmix.h5ad"
        if p.exists():
            p.unlink()
        common.write_candidate(out_a, p)
        m = score(p)
        c = composite(m)
        results.append({"seed": sd, "composite": c["composite"], "expr": c["expr_composite"],
                        "guards": c["guardrails_pass"],
                        "gains": {k: (None if v is None else round(v, 4)) for k, v in c["gains"].items()}})
        print(f"seed {sd}: composite={c['composite']:.4f} expr={c['expr_composite']:.4f} guards={c['guardrails_pass']}", flush=True)
    med = float(np.median([r["composite"] for r in results]))
    mede = float(np.median([r["expr"] for r in results]))
    print(f"MEDIAN composite={med:.4f} expr={mede:.4f} min={min(r['composite'] for r in results):.4f}")
    print(f"CHAMPION=3.4636 -> {'BEATS' if med > 3.4636 else 'no'}")
    json.dump({"seeds": results, "median": med, "median_expr": mede},
              open(REPO / ".auto" / "iter20_summary.json", "w"), indent=1)


if __name__ == "__main__":
    main()
