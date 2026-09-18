#!/usr/bin/env python3
"""G1-T2-R2 gene-shrinkage deltas (T1-R4 port): regularize noisy-gene shifts toward zero.

R1/R2/R3 lesson: assignment is not the lever (null/negative/more-negative). The remaining
degree of freedom is the DELTA VALUES: V0001 applies full per-type mean delta to every gene
including noise genes. Shrink each gene's delta by w=|t|/(|t|+C), C=2 FIXED (no sweep, no
pseudo-target fitting): strong consistent changes keep ~full delta, noise genes -> 0.
Generic James-Stein-flavor regularization, server-plausible.
Frozen: V0001 obs_names/order (5118), panel, inputs, seeds. No training, no target data.
Caps: single process, numpy vectorized, deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

TASK_ID = "G1-T2-R2-SHRINK"
BOARD = "T2:heart_extrap"
RUN_SEED = 20260916
SHRINK_C = 2.0
PANEL = REPO / "data" / "gene_panel" / "T2__heart__val_extrap.genes.txt"
E85 = REPO / "data" / "E8.75.h5ad"
E95 = REPO / "data" / "E9.5.h5ad"
V0001 = REPO / "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
V0001_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
N_CELLS = 25179

from scripts.t1_temporal_model import _load_board_input


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _contract_io():
    iface = REPO / "docs" / "batch3" / "interfaces"
    if str(iface) not in sys.path:
        sys.path.insert(0, str(iface))
    from virtual_embryo_tools import contract_io
    return contract_io


def shrunk_deltas(Xp, tp, Xb, tb, panel_len: int, shrink_c: float = SHRINK_C):
    """Return {type: shrunk delta}. Pure function of inputs (deterministic)."""
    out = {}
    info = []
    for t in sorted(set(tb.tolist())):
        mb = Xb[tb == t]
        if (tp == t).sum() == 0:
            out[t] = np.zeros(panel_len, dtype=np.float32)
            info.append({"type": t, "n_e95": int(len(mb)), "n_e85": 0, "mean_w": 0.0})
            continue
        mp = Xp[tp == t]
        m9, m8 = mb.mean(axis=0), mp.mean(axis=0)
        v9, v8 = mb.var(axis=0), mp.var(axis=0)
        n9, n8 = len(mb), len(mp)
        se = np.sqrt(v9 / n9 + v8 / n8) + 1e-12
        tstat = np.abs((m9 - m8) / se)
        w = (tstat / (tstat + shrink_c)).astype(np.float32)
        out[t] = ((m9 - m8) * w).astype(np.float32)
        info.append({"type": t, "n_e95": int(n9), "n_e85": int(n8),
                     "mean_w": float(w.mean()),
                     "frac_w_lt_half": float((w < 0.5).mean())})
    return out, pd.DataFrame(info)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0011_g0_t2_r2_shrink")
    ap.add_argument("--lane", default="L1_SHRINK")
    ap.add_argument("--shrink-c", type=float, default=SHRINK_C)
    args = ap.parse_args()
    shrink_c = float(args.shrink_c)
    lane = str(args.lane)

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T2_heart_val_extrap").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "shrink": f"w=|t|/(|t|+{shrink_c})", "lane": lane}
    t00 = time.time()

    assert sha256(V0001) == V0001_SHA, "BLOCKED_INPUT: V0001 hash drift"
    diag["V0001_sha_ok"] = True
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    v4 = ad.read_h5ad(V0001)
    v4_names = [str(v) for v in v4.obs_names]
    base_names = [str(v) for v in base.obs_names]
    base_index = {n: i for i, n in enumerate(base_names)}
    assert all(n in base_index for n in v4_names)
    src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)

    def to_dense(a) -> np.ndarray:
        X = a.X
        if sparse.issparse(X):
            X = X.toarray()
        return np.asarray(X, dtype=np.float32)

    Xp, Xb = to_dense(prev), to_dense(base)
    tp = np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))

    deltas, info = shrunk_deltas(Xp, tp, Xb, tb, len(panel), shrink_c)
    info.to_csv(RUN / "intermediates" / "shrink_table.tsv", sep="\t", index=False)
    diag["mean_w_overall"] = float(info["mean_w"].mean())
    # Determinism gate: recompute, compare.
    deltas2, _ = shrunk_deltas(Xp, tp, Xb, tb, len(panel), shrink_c)
    assert all(np.array_equal(deltas[t], deltas2[t]) for t in deltas)
    diag["rerun_deltas_identical"] = True

    t_src = tb[src_idx]
    Xout = np.empty((N_CELLS, len(panel)), dtype=np.float32)
    for j, si in enumerate(src_idx):
        Xout[j] = Xb[si] + deltas[str(t_src[j])]
    Xout = np.clip(Xout, 0.0, None)

    cand_dir = RUN / "candidates" / "T2_heart_val_extrap" / args.out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=Xout, obs=v4.obs.copy(), var=pd.DataFrame(index=panel))
    for ok in list(v4.obsm.keys()):
        a.obsm[ok] = np.asarray(v4.obsm[ok])
    for k in list(v4.layers.keys()):
        a.layers[k] = v4.layers[k].copy()
    if v4.raw is not None:
        a.raw = v4.raw.to_adata()
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log_normalized"}
    a.uns["ve_g0_t2_r2"] = json.dumps({"atom_id": TASK_ID, "lane": lane,
        "method": f"tstat_shrinkage_C{shrink_c:g}", "parent": "V0001 recipe",
        "seed": RUN_SEED, "target_used": False}, sort_keys=True)
    a.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)

    cio = _contract_io()
    res = dict(cio.validate_h5ad_contract(
        out, task="T2", board="heart:val_extrap",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0001, parent_sha256=V0001_SHA))
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
    diag["contract"] = res.get("status")
    diag["candidate_sha_final"] = sha256(out)

    import subprocess
    mout = RUN / "metrics" / f"scorer_{lane}.json"
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T2", "--setting", "heart",
           "--input", str(out), "--target", "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad",
           "--reference", "artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad",
           "--seed", str(RUN_SEED), "--out", str(mout)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-1500:])
    m = json.loads(mout.read_text())["metrics"]
    keep = {k: m.get(k) for k in ("de_score", "de_direction", "energy_distance", "mmd_u",
                                  "variogram", "d2_shape", "occupancy_dice",
                                  "scale_log_ratio", "neighborhood_mmd", "composition_JSD",
                                  "pseudobulk_pearson", "pb_rel_err")}
    (RUN / "metrics" / f"scorer_{lane}_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["beats_baseline"] = bool(keep["de_score"] > 0.2466 and keep["de_direction"] > 0.4221)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"beats_baseline": diag["beats_baseline"], "local": keep,
                      "mean_w": diag["mean_w_overall"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
