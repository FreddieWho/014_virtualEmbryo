"""iter21 (Route C): e_r1-style LOG-LINEAR SHARE-TREND composition x time-normalized QTE.

iter15/20 used the x_n3 composition algorithm (log-ratio trend with a max_fold=2 cap) for
the composition channel. This lane swaps in the OTHER frozen composition algorithm used in
this project (goal-round e_r1/h_r1): per-state shares predicted by a log-space LINEAR fit
over the E8.25/E8.75/E9.5 stage shares (ops.share_series_predict), normalised, converted to
counts by largest remainder, rows chosen by the same deterministic select_rows. Same
expression channel (time-normalized QTE, 4/3). Resampling design -> 3 seeds, median rule.
"""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / ".auto"))
from scripts.t2_round2 import common, ops
from composite import composite

PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
GRID = 2001
FACTOR = 4.0 / 3.0
TIMES = np.array([8.25, 8.75, 9.5])
TT = 10.5
SEEDS = [20260929, 20261007, 20261008]
TARGET = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad"
REF = REPO / "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad"


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
    vnames = [str(v) for v in V.obs_names]
    stages = {}
    for k, rel in (("e825", "data/E8.25_late.h5ad"), ("e875", "data/E8.75.h5ad"), ("e95", "data/E9.5.h5ad")):
        X, t, _, _ = common.load_stage(rel, panel)
        stages[k] = (X, t)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    Xq = XV.copy()
    for s in sorted(set(stages["e95"][1].tolist()) & set(stages["e875"][1].tolist())):
        pred_idx = np.flatnonzero(tV == s)
        Xs = XV[pred_idx]
        o = np.argsort(Xs, axis=0, kind="stable")
        r = np.empty_like(o)
        np.put_along_axis(r, o, np.arange(len(pred_idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
        p2 = (r + 0.5) / len(pred_idx)
        Q9 = np.quantile(stages["e95"][0][stages["e95"][1] == s], pgrid, axis=0)
        Q8 = np.quantile(stages["e875"][0][stages["e875"][1] == s], pgrid, axis=0)
        Qpred = Q9 + FACTOR * (Q9 - Q8)
        new = np.empty_like(Xs)
        for g in range(Xs.shape[1]):
            new[:, g] = np.interp(p2[:, g], pgrid, Qpred[:, g])
        Xq[pred_idx] = new
    Xq = np.clip(Xq, 0, None)
    # ---- composition: log-linear share trend (e_r1 algorithm), fallback = baseline shares
    pV = common.shares(tV)
    pser = [common.shares(stages[k][1]) for k in ("e825", "e875", "e95")]
    pstates = sorted(set(tV.tolist()))
    three = sorted(set(pV) & set().union(*[set(d) for d in pser]))
    raw = {}
    for s in pstates:
        series = [d.get(s, 0.0) for d in pser]
        if s in three and all(v > 0 for v in series):
            raw[s] = ops.share_series_predict(TIMES, np.array(series), TT)
        else:
            raw[s] = pV.get(s, 0.0)
    n = int(V.n_obs)
    results = []
    for sd in SEEDS:
        counts, rawn = common.counts_from_raw(raw, pstates, n)
        chosen = common.select_rows(tV, counts, sd)
        final = common.dedup_names([vnames[i] for i in chosen])
        out_a = V[chosen].copy()
        out_a.obs_names = final
        out_a.X = np.ascontiguousarray(Xq[chosen], dtype=np.float32)
        common.fix_obsm(out_a)
        common.stamp_uns(out_a, normalization="log_normalized",
                         provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 21,
                                     "method": "qrte_time4over3_x_sharelin_trend", "seed": sd,
                                     "target_used": False})
        p = REPO / ".auto" / f"cand_share_s{sd}.h5ad"
        if p.exists():
            p.unlink()
        common.write_candidate(out_a, p)
        m = score(p)
        c = composite(m)
        results.append({"seed": sd, "composite": c["composite"], "expr": c["expr_composite"],
                        "guards": c["guardrails_pass"],
                        "gains": {k: (None if v is None else round(v, 4)) for k, v in c["gains"].items()}})
        print(f"seed {sd}: composite={c['composite']:.4f} expr={c['expr_composite']:.4f} guards={c['guardrails_pass']}", flush=True)
        p.unlink()
    med = float(np.median([r["composite"] for r in results]))
    print(f"MEDIAN composite={med:.4f} expr_median={np.median([r['expr'] for r in results]):.4f} "
          f"min={min(r['composite'] for r in results):.4f}")
    print(f"CHAMPION=3.913 -> {'BEATS' if med > 3.913 else 'no'}")
    json.dump({"seeds": results, "median": med}, open(REPO / ".auto" / "iter21_summary.json", "w"), indent=1)
    for q in (REPO / ".auto").glob("cand_share_s*.score.json"):
        q.unlink()


if __name__ == "__main__":
    main()
