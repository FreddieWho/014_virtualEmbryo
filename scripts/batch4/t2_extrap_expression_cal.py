#!/usr/bin/env python3
"""B4-T2-R3 heart-extrap expression calibration: damp / time / popmix lanes.

Parent is verified strict per-celltype shift damp=1.0, so:
  L1 (damp 0.5)  = X_parent - 0.5*Delta
  L2 (damp 4/3)  = X_parent + (1/3)*Delta
  L3 (popmix)    = same rows; first half unshifted E9.5 values, second half parent
Delta_c = mean(E9.5,c) - mean(E8.75,c) in log1p space; unshared types keep parent.
Coordinates/geometry row-identical to parent. No target data, no external data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

TASK_ID = "B4-T2-R3-HEART-EXTRAP-EXPRESSION-CAL"
PARENT = REPO / "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PSHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = [l.strip() for l in (REPO / "data" / "gene_panel" / "T2__heart__val_extrap.genes.txt").read_text().splitlines() if l.strip()]
LANES = ["L1_DAMP050", "L2_TIME1333", "L3_POPMIX050"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dense(X):
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def load_mat(path: str):
    a = ad.read_h5ad(REPO / path, backed="r")
    vn = [str(v) for v in a.var_names]
    pos = np.array([vn.index(g) for g in PANEL])
    Xd = dense(a.X[:, pos]).astype(np.float64)
    t = np.asarray(a.obs["celltype"].astype(str))
    a.file.close()
    return Xd, t


def verify() -> dict:
    assert sha256(PARENT) == PSHA, "BLOCKED_INPUT: parent drift"
    a = ad.read_h5ad(PARENT, backed="r")
    vb = dict(a.uns.get("ve_baseline", {}))
    a.file.close()
    assert vb.get("method") == "pseudobulk_shift" and float(vb.get("damp", -1)) == 1.0, vb
    X95, t95 = load_mat("data/E9.5.h5ad")
    X75, t75 = load_mat("data/E8.75.h5ad")
    P = ad.read_h5ad(PARENT, backed="r")
    pt = sorted(set(str(v) for v in P.obs["celltype"]))
    P.file.close()
    shared = sorted(set(pt) & set(t95.tolist()) & set(t75.tolist()))
    out = {"parent_sha_ok": True, "parent_rule": "strict_shift_damp_1.0",
           "parent_types": len(pt), "shared_types": len(shared),
           "unshared_types": sorted(set(pt) - set(shared)),
           "unshared_policy": "keep_parent"}
    print(json.dumps(out, indent=1))
    return out


def compute_delta():
    X95, t95 = load_mat("data/E9.5.h5ad")
    X75, t75 = load_mat("data/E8.75.h5ad")
    m95, m75 = {}, {}
    for c in np.unique(t95):
        m95[str(c)] = X95[t95 == c].mean(axis=0)
    for c in np.unique(t75):
        m75[str(c)] = X75[t75 == c].mean(axis=0)
    return m95, m75


def build_lane(run_dir: Path, lane: str) -> dict:
    t0 = time.time()
    out = run_dir / "candidates" / "T2_heart_val_extrap" / lane / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(str(out))
    m95, m75 = compute_delta()
    P = ad.read_h5ad(PARENT)
    pnames = [str(v) for v in P.obs_names]
    ptypes = np.asarray(P.obs["celltype"].astype(str))
    XP = dense(P.X).astype(np.float64)
    Delta = np.zeros_like(XP)
    for s in np.unique(ptypes):
        s = str(s)
        if s in m95 and s in m75:
            Delta[ptypes == s] = m95[s] - m75[s]
    if lane == "L1_DAMP050":
        X1 = XP - 0.5 * Delta
    elif lane == "L2_TIME1333":
        X1 = XP + (1.0 / 3.0) * Delta
    else:
        n = len(pnames)
        half = n // 2
        X1 = XP.copy()
        X1[:half] -= Delta[:half]  # unshift -> copy-last E9.5 values
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    X1 = np.ascontiguousarray(X1, dtype=np.float32)
    assert np.isfinite(X1).all() and (X1 >= 0).all()
    assert X1.shape == (25179, 500), X1.shape
    out_a = P[np.arange(len(pnames))].copy()
    out_a.X = X1
    for k in list(out_a.obsm.keys()):
        out_a.obsm[k] = np.ascontiguousarray(np.asarray(out_a.obsm[k])[:, :3] if np.asarray(out_a.obsm[k]).ndim == 2 and np.asarray(out_a.obsm[k]).shape[1] >= 3 else np.asarray(out_a.obsm[k]), dtype=np.float32)
    out_a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    out_a.uns["ve_b4_t2_r3"] = json.dumps({
        "atom_id": TASK_ID, "lane": lane, "parent": "baseline-001 v0001 damp=1.0",
        "parent_sha256": PSHA, "target_used": False}, sort_keys=True)
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    out_a.write_h5ad(tmp)
    Path(tmp).replace(out)
    diag = {"lane": lane, "output": str(out), "sha256": sha256(out), "n_obs": 25179,
            "clip_fraction": clip_frac, "wall_s": time.time() - t0}
    (run_dir / "intermediates").mkdir(exist_ok=True)
    (run_dir / "intermediates" / f"diag_{lane}.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps(diag, indent=1, sort_keys=True), flush=True)
    return diag


def backtest(run_dir: Path) -> dict:
    """Source-only: E8.25->E8.75 shift predicts E9.5 ladder position. Recorded only."""
    X25, t25 = load_mat("data/E8.25_late.h5ad")
    X75, t75 = load_mat("data/E8.75.h5ad")
    X95, t95 = load_mat("data/E9.5.h5ad")
    m25 = {str(c): X25[t25 == c].mean(axis=0) for c in np.unique(t25)}
    m75 = {str(c): X75[t75 == c].mean(axis=0) for c in np.unique(t75)}
    m95 = {str(c): X95[t95 == c].mean(axis=0) for c in np.unique(t95)}
    rows = []
    for damp in (0.5, 1.0, 4.0 / 3.0):
        errs = []
        for s in sorted(set(m25) & set(m75) & set(m95)):
            pred = m75[s] + damp * (m75[s] - m25[s])
            errs.append(float(np.abs(pred - m95[s]).mean()))
        rows.append({"damp": damp, "states": len(errs), "mean_abs_err": float(np.mean(errs))})
    pd.DataFrame(rows).to_csv(run_dir / "metrics" / "backtest.tsv", sep="\t", index=False)
    print(pd.DataFrame(rows).to_string(), flush=True)
    return {"rows": rows, "note": "source-only ladder simulation; not a server preview"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["verify", "build", "backtest"])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--lane", default=None)
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    (run_dir / "metrics").mkdir(parents=True, exist_ok=True)
    if args.command == "verify":
        verify()
    elif args.command == "build":
        assert args.lane in LANES, args.lane
        build_lane(run_dir, args.lane)
    else:
        print(json.dumps(backtest(run_dir), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
