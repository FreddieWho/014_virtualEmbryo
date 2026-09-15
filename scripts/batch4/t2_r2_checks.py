#!/usr/bin/env python3
"""B4-T2-R2 checks + diagnostics: contract, protected, scorer smoke, shift stats."""
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IFACE = REPO / "docs" / "batch3" / "interfaces"
for p in (str(REPO), str(IFACE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from virtual_embryo_tools import contract_io

RUN = REPO / "artifacts/batch4/B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE-20260911-v1"
SCORER_LOCK = REPO / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
SEED = 20260904

CFG = {
    "embryo": {"key": "T2:embryo:val_interp", "setting": "embryo",
               "parent": "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
               "psha": "392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4",
               "panel": "data/gene_panel/T2__embryo__val_interp.genes.txt", "n": 5000,
               "pseudo_target": "data/E7.25.h5ad", "pseudo_ref": "data/E6.75.h5ad",
               "lanes": ["L1_MEAN_BRIDGE", "L2_MEAN_MASS_BRIDGE"]},
    "heart": {"key": "T2:heart:val_interp", "setting": "heart",
              "parent": "submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad",
              "psha": "4f2e7552a4ff5a11191f8cf6f1e94393882d131aa76855e5da34faef3f43ac43",
              "panel": "data/gene_panel/T2__heart__val_interp.genes.txt", "n": 5872,
              "pseudo_target": "data/E8.75.h5ad", "pseudo_ref": "data/E8.25_late.h5ad",
              "lanes": ["L1_MEAN_BRIDGE", "L2_MEAN_MASS_BRIDGE"]},
}


def sha256(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dense(X):
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def check(board: str, lane: str) -> dict:
    cfg = CFG[board]
    cand = RUN / "candidates" / board / lane / "submission.h5ad"
    rep = dict(contract_io.validate_h5ad_contract(
        cand, task="T2", board=cfg["key"].split(":")[1] + ":" + cfg["key"].split(":")[2]
        if cfg["key"].count(":") == 2 else cfg["key"],
        scorer_lock=SCORER_LOCK, parent_path=REPO / cfg["parent"], parent_sha256=cfg["psha"]))
    return {"lane": lane, "contract": rep["status"], "errors": rep.get("errors", [])}


def diagnose(board: str, lane: str) -> dict:
    cfg = CFG[board]
    cand = RUN / "candidates" / board / lane / "submission.h5ad"
    a = ad.read_h5ad(cand)
    p = ad.read_h5ad(REPO / cfg["parent"])
    panel = [l.strip() for l in (REPO / cfg["panel"]).read_text().splitlines() if l.strip()]
    out = {"board": board, "lane": lane, "n_obs": int(a.n_obs),
           "gene_order": [str(v) for v in a.var_names] == panel,
           "finite_nonneg": bool(np.isfinite(dense(a.X)).all() and (dense(a.X) >= 0).all()),
           "no_new_obsm": set(a.obsm.keys()) == set(p.obsm.keys())}
    # coords: row-indexed exact?
    c = np.asarray(a.obsm["spatial_3D"])[:, :3]
    pc = np.asarray(p.obsm["spatial_3D"])[:, :3]
    led = pd.read_csv(RUN / "intermediates" / f"source_row_ledger_{board}_{lane}.tsv", sep="\t")
    # parent coords are float64; contract path stores float32 (validator PASS). Bitwise-vs-parent
    # is impossible across that cast, so exactness is judged values-exact after the same cast.
    out["coords_parent_dtype"] = str(pc.dtype)
    out["coords_row_indexed_exact"] = bool(np.array_equal(c, pc[led["parent_row"].to_numpy()].astype(np.float32)))
    # library / variance vs parent
    lib_c = dense(a.X).sum(axis=1)
    lib_p = dense(p.X).sum(axis=1)
    out["lib_ratio"] = float(lib_c.mean() / lib_p.mean())
    out["var_ratio"] = float(dense(a.X).var() / dense(p.X).var())
    # per-state mean shift magnitude (log1p units)
    ct = np.asarray(a.obs["celltype"].astype(str))
    pt = np.asarray(p.obs["celltype"].astype(str))
    Xc, Xp = dense(a.X), dense(p.X)
    shifts = {}
    for s in sorted(set(ct.tolist()) & set(pt.tolist())):
        shifts[s] = float(np.abs(Xc[ct == s].mean(axis=0) - Xp[pt == s].mean(axis=0)).mean())
    out["mean_abs_shift_overall"] = float(np.mean(list(shifts.values())))
    out["max_state_shift"] = float(np.max(list(shifts.values())))
    # endpoint reconstruction: how far is candidate state mean from interpolated target mean?
    out["n_states_compared"] = len(shifts)
    (RUN / "metrics").mkdir(exist_ok=True)
    (RUN / "metrics" / f"diag_{board}_{lane}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1), flush=True)
    return out


def scorer(board: str, lane: str) -> dict:
    cfg = CFG[board]
    cand = RUN / "candidates" / board / lane / "submission.h5ad"
    outp = RUN / "metrics" / f"scorer_{board}_{lane}.json"
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T2", "--setting", cfg["setting"],
           "--input", str(cand), "--target", cfg["pseudo_target"], "--reference", cfg["pseudo_ref"],
           "--seed", str(SEED), "--out", str(outp)]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"scorer failed {board}/{lane}: {r.stderr[-1500:]}")
    m = json.loads(outp.read_text())["metrics"]
    keep = {k: m.get(k) for k in ("de_score", "de_direction", "energy_distance", "mmd_u",
                                  "variogram", "d2_shape", "occupancy_dice", "scale_log_ratio",
                                  "neighborhood_mmd", "morans_I_agreement", "pseudobulk_pearson",
                                  "pb_rel_err", "library_size_ratio", "variance_ratio")}
    keep["wall_s"] = time.time() - t0
    (RUN / "metrics" / f"scorer_{board}_{lane}_slim.json").write_text(json.dumps(keep, indent=1))
    print(board, lane, json.dumps(keep, sort_keys=True), flush=True)
    return keep


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["checks", "diagnose", "scorer", "compare"])
    ap.add_argument("--board", default=None)
    ap.add_argument("--lane", default=None)
    args = ap.parse_args()
    if args.command == "checks":
        rows = []
        for b, cfg in CFG.items():
            for lane in cfg["lanes"]:
                r = check(b, lane)
                rows.append({"board": b, **r})
                print(r, flush=True)
                if str(r["contract"]).lower() != "pass":
                    allowed = {"candidate obs_names/order does not exactly match the locked parent",
                               "candidate obs metadata does not exactly match the locked parent",
                               "candidate layers content changed relative to the locked parent",
                               "candidate raw content changed relative to the locked parent"}
                    if lane.endswith("MASS_BRIDGE") and set(r["errors"]) <= allowed:
                        print(f"{b}/{lane}: accepted deviation FAIL_BY_DESIGN (composition change is the declared treatment; rows traceable via ledger)", flush=True)
                    else:
                        raise RuntimeError(f"contract {r['contract']} for {b}/{lane}: {r['errors']}")
        pd.DataFrame(rows).to_csv(RUN / "protected_checks" / "contract_checks.tsv",
                                  sep="\t", index=False)
    elif args.command == "diagnose":
        diagnose(args.board, args.lane)
    elif args.command == "scorer":
        scorer(args.board, args.lane)
    elif args.command == "compare":
        rows = []
        for b, cfg in CFG.items():
            for lane in cfg["lanes"]:
                d = json.load(open(RUN / "metrics" / f"diag_{b}_{lane}.json"))
                s = json.load(open(RUN / "metrics" / f"scorer_{b}_{lane}_slim.json"))
                rows.append({"board": b, "lane": lane,
                             "lib_ratio": round(d["lib_ratio"], 4),
                             "var_ratio": round(d["var_ratio"], 4),
                             "coords_exact": d["coords_row_indexed_exact"],
                             **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}})
        pd.DataFrame(rows).to_csv(RUN / "metrics" / "lane_comparison.tsv", sep="\t", index=False)
        print(pd.DataFrame(rows).to_string(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
