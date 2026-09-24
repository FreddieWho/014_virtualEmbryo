#!/usr/bin/env python3
"""T1-NEXT-R1 v0023 build: full-fit B-rule quantile-shape forecast.

Fit per (type,gene) zero-rate + quantile increments on ALL E8.5+E9.5 cells
(legal train). Recipients: v0004's 5118 E9.5 bank rows (identity-mapped).
B-rule transport (full predicted zero support); unsupported types/genes fall
back to the v0004 PARENT row (doc §2). Deterministic (fixed tie rule, no RNG).
Output 5118x32285 panel-ordered log1p_normalized; contract-gated vs v0004.
Local scorer vs full E9.5 recorded pipeline-only (full-fit seen, no validation
claim — D3 precedent). CPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
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

TASK_ID = "T1-NEXT-R1-BUILD"
RUN_SEED = 20260921
N_Q = 41
LOGIT_CAP = 2.0
MIN_N = 30
N_CELLS = 5118
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
E85_SHA = "8eab2d0ccaa89f92861b09816b76b6a731b8ed6b5995e4af196d9ed8ff76e504"
E95_SHA = "0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def to_dense(a: ad.AnnData) -> np.ndarray:
    X = a.X
    if sparse.issparse(X):
        X = X.toarray()
    return np.asarray(X, dtype=np.float32)


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0023_t1_next_r1_qshape")
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T1_val" / args.out_version).mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED}
    t00 = time.time()

    assert sha256(E85) == E85_SHA and sha256(E95) == E95_SHA, "input drift"
    assert sha256(V0004) == V0004_SHA, "v0004 drift"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    D = len(panel)
    a85 = ad.read_h5ad(E85)[:, panel].copy()
    a95 = ad.read_h5ad(E95)[:, panel].copy()
    X85, X95 = to_dense(a85), to_dense(a95)
    t85 = np.asarray(a85.obs["celltype"].astype(str))
    t95 = np.asarray(a95.obs["celltype"].astype(str))
    v4 = ad.read_h5ad(V0004)
    Xv4 = to_dense(v4)
    assert Xv4.shape == (N_CELLS, D)
    v4_names = [str(v) for v in v4.obs_names]
    b95_names = [str(v) for v in a95.obs_names]
    bidx = {n: i for i, n in enumerate(b95_names)}
    assert all(n in bidx for n in v4_names), "v0004 rows not subset of E9.5"
    src = np.array([bidx[n] for n in v4_names], dtype=np.int64)
    Xr, tr_ = X95[src], t95[src]
    Xpar = Xv4  # parent fallback rows

    common = sorted(set(t85) & set(t95))
    diag["types_common"] = len(common)
    U = np.linspace(0, 1, N_Q).astype(np.float64)
    lib_r = Xr.sum(axis=1)
    out = Xpar.copy()  # fallback = parent
    n_mapped = 0
    for c in sorted(set(tr_)):
        m_rec = (tr_ == c)
        rec_idx = np.where(m_rec)[0]
        if c not in common:
            continue
        v85 = X85[t85 == c]
        v95 = X95[t95 == c]
        if len(v85) < MIN_N or len(v95) < MIN_N:
            continue
        order = np.argsort(-lib_r[m_rec], kind="stable")
        lr = np.empty(m_rec.sum())
        lr[order] = (np.arange(m_rec.sum()) + 0.5) / m_rec.sum()
        for g in range(D):
            a = v85[:, g].astype(np.float64)
            b = v95[:, g].astype(np.float64)
            p0_85 = float((a == 0).mean())
            p0_95 = float((b == 0).mean())
            if p0_85 > 0.999 and p0_95 > 0.999:
                continue
            d = float(np.clip(logit(np.array([p0_95]))[0] - logit(np.array([p0_85]))[0],
                              -LOGIT_CAP, LOGIT_CAP))
            p_pred = float(sigmoid(logit(np.array([p0_85]))[0] + d))
            Qa = np.quantile(a, U)
            Qb = np.quantile(b, U)
            Qp = np.maximum.accumulate(np.maximum(Qa + (Qb - Qa), 0.0))
            x = Xr[m_rec][:, g].astype(np.float64)
            s = np.sort(a)
            u = np.searchsorted(s, x, side="right") / len(s)
            u[x == 0] = lr[x == 0] * p0_85
            out[rec_idx, g] = np.interp(u, U, Qp)
            n_mapped += m_rec.sum()
        print(f"type {c}: done", flush=True)
    Xout = np.clip(out, 0.0, None).astype(np.float32)
    assert np.isfinite(Xout).all() and (Xout >= 0).all()
    diag["transport_coverage"] = float(n_mapped / (N_CELLS * D))
    diag["zero_rate"] = float((Xout == 0).mean())
    diag["lib_mean"] = float(Xout.sum(axis=1).mean())

    cand_dir = RUN / "candidates" / "T1_val" / args.out_version
    outp = cand_dir / "submission.h5ad"
    aa = ad.AnnData(X=np.ascontiguousarray(Xout, dtype=np.float32),
                    obs=v4.obs.copy(), var=pd.DataFrame(index=panel))
    aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    aa.uns["ve_t1_next_r1"] = json.dumps({"atom_id": TASK_ID, "seed": RUN_SEED,
        "method": "quantile_shape_B_rule_fullfit", "parent": "v0004",
        "target_used": False}, sort_keys=True)
    aa.write_h5ad(outp)
    diag["candidate_sha"] = sha256(outp)

    sys.path.insert(0, str(REPO / "docs" / "batch3" / "interfaces"))
    from virtual_embryo_tools import contract_io as cio
    res = dict(cio.validate_h5ad_contract(
        outp, task="T1", board="val",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0004, parent_sha256=V0004_SHA))
    diag["contract"] = res.get("status")
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"

    mout = RUN / "metrics" / "scorer_v0023.json"
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(outp), "--target", str(E95),
           "--reference", str(E85), "--seed", str(RUN_SEED), "--out", str(mout)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-2000:])
    m = json.loads(mout.read_text())["metrics"]
    keep = {k: m.get(k) for k in ("de_score", "de_direction", "energy_distance", "mmd_u",
                                  "variogram", "pb_rel_err", "library_size_ratio",
                                  "variance_ratio", "composition_JSD", "pseudobulk_pearson")}
    diag["local_fullfit_record_only"] = keep
    diag["wall_s"] = time.time() - t00
    (RUN / "BUILD.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"candidate_sha": diag["candidate_sha"], "contract": diag["contract"],
                      "local": keep, "coverage": diag["transport_coverage"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
