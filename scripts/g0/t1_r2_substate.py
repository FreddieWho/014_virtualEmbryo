#!/usr/bin/env python3
"""G1-T1-R2 sub-state split deltas: finer-than-celltype shift table.

R1 lesson: global reassignment (13% cells) ~= null locally. Attack intra-type heterogeneity:
  KMeans sub-states per E9.5 type in PC-50 latent (k=3 if n>=300, k=2 if n>=120, else 1);
  E8.5 same-type cells assigned to nearest E9.5 sub-centroid; delta_sub = sub-state mean diff;
  E8.5-absent types -> zero delta (v0004 convention). Decode source cell + its sub-delta.
Frozen: v0004 obs_names/order (5118), panel, inputs, seeds. No training, no target data.
Caps: sklearn/OMP threads <= 16, single process, deterministic (fixed random_state).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "16")
os.environ.setdefault("MKL_NUM_THREADS", "16")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "16")

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

TASK_ID = "G1-T1-R2-SUBSTATE"
BOARD = "T1:val"
RUN_SEED = 20260916
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118
N_PC = 50

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0016_g0_t1_r2_substate")
    ap.add_argument("--k-big", type=int, default=3)
    ap.add_argument("--k-mid", type=int, default=2)
    args = ap.parse_args()
    np.random.seed(RUN_SEED)

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T1_val").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED,
                  "k_rule": f"k={args.k_big} if n>=300, k={args.k_mid} if n>=120, else 1"}
    t00 = time.time()

    assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
    diag["v0004_sha_ok"] = True
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    v4 = ad.read_h5ad(V0004)
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

    Xall = np.vstack([Xp, Xb])
    mu, sd = Xall.mean(axis=0, keepdims=True), Xall.std(axis=0, keepdims=True) + 1e-6
    Lall = PCA(n_components=N_PC, svd_solver="randomized",
               random_state=RUN_SEED).fit_transform((Xall - mu) / sd).astype(np.float32)
    Lp, Lb = Lall[: len(Xp)], Lall[len(Xp):]
    diag["n_types_e95"] = int(len(set(tb.tolist())))

    # Sub-state split per E9.5 type; E8.5 same-type cells -> nearest sub-centroid.
    sub_of_cell = np.full(len(Xb), "", dtype=object)   # E9.5 cell -> "type#j"
    sub_delta: dict = {}
    rows = []
    for t in sorted(set(tb.tolist())):
        ib = np.flatnonzero(tb == t)
        n = len(ib)
        k = args.k_big if n >= 300 else (args.k_mid if n >= 120 else 1)
        if k == 1:
            cen = Lb[ib].mean(axis=0, keepdims=True)
            lab = np.zeros(n, dtype=int)
        else:
            km = KMeans(n_clusters=k, n_init=10, random_state=RUN_SEED)
            lab = km.fit_predict(Lb[ib])
            cen = km.cluster_centers_
        ip = np.flatnonzero(tp == t)
        for j in range(k):
            key = f"{t}#{j}"
            jb = ib[lab == j]
            sub_of_cell[jb] = key
            if len(ip) == 0 or len(jb) == 0:
                sub_delta[key] = np.zeros(len(panel), dtype=np.float32)
            else:
                d2 = ((Lp[ip][:, None, :] - cen[None, :, :]) ** 2).sum(-1)
                nearest = d2.argmin(axis=1)
                jp = ip[nearest == j]
                if len(jp) == 0:
                    sub_delta[key] = np.zeros(len(panel), dtype=np.float32)
                else:
                    sub_delta[key] = (Xb[jb].mean(axis=0) - Xp[jp].mean(axis=0)).astype(np.float32)
            rows.append({"sub": key, "n_e95": int(len(jb)), "n_e85": int((nearest == j).sum()) if len(ip) else 0})
        # type-level delta for reference (v0004 formula)
    pd.DataFrame(rows).to_csv(RUN / "intermediates" / "substate_table.tsv", sep="\t", index=False)
    diag["n_substates"] = int(len(sub_delta))
    diag["n_split_types"] = int(sum(1 for t in set(tb.tolist()) if (tb == t).sum() >= 120))

    # Determinism gate: recompute assignments from scratch, compare.
    sub2 = np.full(len(Xb), "", dtype=object)
    for t in sorted(set(tb.tolist())):
        ib = np.flatnonzero(tb == t)
        n = len(ib)
        k = args.k_big if n >= 300 else (args.k_mid if n >= 120 else 1)
        if k == 1:
            lab = np.zeros(n, dtype=int)
        else:
            lab = KMeans(n_clusters=k, n_init=10, random_state=RUN_SEED).fit_predict(Lb[ib])
        for j in range(k):
            sub2[ib[lab == j]] = f"{t}#{j}"
    assert (sub2 == sub_of_cell).all(), "sub-state assignment not deterministic"
    diag["rerun_assignment_identical"] = True

    Xout = np.empty((N_CELLS, len(panel)), dtype=np.float32)
    for j, si in enumerate(src_idx):
        Xout[j] = Xb[si] + sub_delta[str(sub_of_cell[si])]
    Xout = np.clip(Xout, 0.0, None)

    cand_dir = RUN / "candidates" / "T1_val" / args.out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=Xout, obs=v4.obs.copy(), var=pd.DataFrame(index=panel))
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_g0_t1_r2"] = json.dumps({"atom_id": TASK_ID, "lane": "L1_SUBSTATE",
        "method": "substate_split_deltas", "parent": "v0004 recipe",
        "seed": RUN_SEED, "target_used": False}, sort_keys=True)
    a.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)

    cio = _contract_io()
    res = dict(cio.validate_h5ad_contract(
        out, task="T1", board="val",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0004, parent_sha256=V0004_SHA))
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
    diag["contract"] = res.get("status")
    diag["candidate_sha_final"] = sha256(out)

    import subprocess
    mout = RUN / "metrics" / "scorer_L1_SUBSTATE.json"
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(out), "--target", "data/E9.5_RNA.h5ad",
           "--reference", "data/E8.5_RNA.h5ad", "--seed", str(RUN_SEED), "--out", str(mout)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-1500:])
    m = json.loads(mout.read_text())["metrics"]
    keep = {k: m.get(k) for k in ("de_score", "de_direction", "energy_distance", "mmd_u",
                                  "variogram", "pb_rel_err", "library_size_ratio",
                                  "variance_ratio", "composition_JSD", "pseudobulk_pearson")}
    (RUN / "metrics" / "scorer_L1_SUBSTATE_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["beats_baseline"] = bool(keep["de_score"] > 0.8868 and keep["de_direction"] > 0.8895)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"beats_baseline": diag["beats_baseline"], "local": keep,
                      "n_substates": diag["n_substates"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
