"""iter15 (Route C): QTE marginals x composition-trend resample. COMBINATION of two channels.

Channel 1 (marginal, champion): iter12 QTE on the full baseline.
Channel 2 (composition): x_n3's frozen compmix plan (log-ratio share trend, max_fold 2.0,
largest-remainder counts, deterministic select_rows) — the only mechanism that has ever
moved the geometry channels, because resampling changes which coordinates are present.

Resampling design => 3-seed rule (median composite must beat the champion +2.377).
Seeds: 20260929 (the x_n3 design seed) + 20261007 + 20261008. Deterministic per seed.
"""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / ".auto"))
from scripts.t2_round2 import common, run as r2run   # read-only imports
from composite import composite

PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
GRID = 2001
SEEDS = [20260929, 20261007, 20261008]
TARGET = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad"
REF = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad"


def qte_matrix(XV, tV, X875, t875, X95, t95, pgrid):
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
        Qpred = Q9 + (Q9 - Q8)
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
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    Xq = qte_matrix(XV, tV, X875, t875, X95, t95, pgrid)
    cfg = common.load_config()
    ctx = r2run.ExtrapCtx(cfg["boards"]["extrap"])
    results = []
    for sd in SEEDS:
        chosen, final, counts, raw_n, types = r2run.compmix_plan(ctx, sd)
        out_a = V[chosen].copy()
        out_a.obs_names = final
        out_a.X = np.ascontiguousarray(Xq[chosen], dtype=np.float32)
        common.fix_obsm(out_a)
        common.stamp_uns(out_a, normalization="log_normalized",
                         provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 15,
                                     "method": "qte_marginal_x_compmix_resample", "seed": sd,
                                     "target_used": False})
        p = REPO / ".auto" / f"cand_qtec_s{sd}.h5ad"
        if p.exists():
            p.unlink()
        common.write_candidate(out_a, p)
        m = score(p)
        c = composite(m)
        results.append({"seed": sd, "composite": c["composite"], "guards": c["guardrails_pass"],
                        "gains": {k: (None if v is None else round(v, 4)) for k, v in c["gains"].items()},
                        "metrics": {k: m.get(k) for k in ("de_score", "de_direction", "variogram",
                                                          "mmd_u", "neighborhood_mmd", "d2_shape",
                                                          "occupancy_dice", "variance_ratio")}})
        print(f"seed {sd}: composite={c['composite']:.3f} guards={c['guardrails_pass']} "
              f"worst={c['worst_channel']}", flush=True)
        p.unlink()
    comps = sorted(r["composite"] for r in results)
    med = float(np.median(comps))
    print(f"MEDIAN composite={med:.4f} MIN={comps[0]:.4f} all_guards={all(r['guards'] for r in results)}")
    print(f"CHAMPION=2.3768 -> {'BEATS' if med > 2.3768 else 'does not beat'}")
    json.dump({"seeds": results, "median": med, "min": comps[0]}, open(REPO / ".auto" / "iter15_summary.json", "w"), indent=1)
    for p in (REPO / ".auto").glob("cand_qtec_s*.score.json"):
        p.unlink()


if __name__ == "__main__":
    main()
