#!/usr/bin/env python3
"""G1-T1-D3 v0022 build: forecast E9.5 bank t=1->2 with the trained field_best.pt.

User override of the full-gene gate FAIL (local scoring not fully reliable):
single-metric-significant-gain + no-significant-degradation-elsewhere -> one upload.
Field: cosine 0.8125 > 0.7796 (gain); energy 0.4855 < 0.4340 (NOT significant
degradation at panel scale? recorded as-is; server arbitrates).
Replicates t1_d3_flow.py --full components exactly (same seeds/arch/scaler);
no retraining. Strict contract (bank rows kept). Locked scorer for the record.
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

TASK_ID = "G1-T1-D3-BUILD"
RUN_SEED = 20260916
HID = 512
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
RUNDIR = REPO / "artifacts" / "g0" / "G1-T1-D3-FLOW-20260917-v1"
FIELD = RUNDIR / "intermediates" / "field_best.pt"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118

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


def to_dense(a) -> np.ndarray:
    X = a.X
    if sparse.issparse(X):
        X = X.toarray()
    return np.asarray(X, dtype=np.float32)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0022_g0_t1_d3_otcfm")
    args = ap.parse_args()
    import torch
    import torch.nn as nn
    torch.set_num_threads(16)
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T1_val").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "from_field": str(FIELD)}
    t00 = time.time()
    assert FIELD.exists(), "BLOCKED_INPUT: trained field missing"
    assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"

    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    D = len(panel)
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    v4 = ad.read_h5ad(V0004)
    Xb_full = to_dense(base)
    Xp_full = to_dense(prev)
    # identical scaler recompute (combined train + floor 1e-3)
    Xcat = np.vstack([Xp_full, Xb_full])
    mu, sd = Xcat.mean(axis=0), Xcat.std(axis=0)
    sd = np.maximum(sd, 1e-3).astype(np.float32)
    del Xcat, Xp_full
    Zb = ((Xb_full - mu) / sd).astype(np.float32)
    del Xb_full
    tb = np.asarray(base.obs["celltype"].astype(str))

    class Field(nn.Module):
        def __init__(self, d: int, h: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(d + 1, h), nn.SiLU(),
                nn.Linear(h, h), nn.SiLU(),
                nn.Linear(h, h), nn.SiLU(),
                nn.Linear(h, d))

        def forward(self, x, t):
            if torch.is_tensor(t):
                tt = t.reshape(x.shape[0], 1).to(dtype=x.dtype, device=x.device)
            else:
                tt = torch.full((x.shape[0], 1), float(t), dtype=x.dtype, device=x.device)
            return self.net(torch.cat([x, tt], dim=1))

    field = Field(D, HID)
    field.load_state_dict(torch.load(FIELD, map_location="cpu"))
    field.eval()

    v4_names = [str(v) for v in v4.obs_names]
    base_names = [str(v) for v in base.obs_names]
    base_index = {n: i for i, n in enumerate(base_names)}
    assert all(n in base_index for n in v4_names)
    src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
    Zb_t = torch.from_numpy(Zb)

    @torch.no_grad()
    def integrate(x0: torch.Tensor, t0: float, t1: float, n_steps: int = 100) -> torch.Tensor:
        x = x0.clone()
        dt = (t1 - t0) / n_steps
        t = t0
        for _ in range(n_steps):
            x = x + dt * field(x, t)
            t += dt
        return x

    Zpred = np.empty((N_CELLS, D), dtype=np.float32)
    with torch.no_grad():
        for a in range(0, N_CELLS, 1024):
            b = src_idx[a:a + 1024]
            Zpred[a:a + 1024] = integrate(Zb_t[b], 1.0, 2.0).numpy()
    Xout = np.clip(Zpred * sd + mu, 0.0, None).astype(np.float32)
    del Zpred
    assert np.isfinite(Xout).all(), "diverged forecast"

    cand_dir = RUN / "candidates" / "T1_val" / args.out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    aa = ad.AnnData(X=np.ascontiguousarray(Xout), obs=v4.obs.copy(),
                    var=pd.DataFrame(index=panel))
    aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    aa.uns["ve_g0_t1_d3"] = json.dumps({"atom_id": TASK_ID, "lane": "L1_OTCFM",
        "method": "otcfm_field_forecast", "parent": "v0004 recipe",
        "seed": RUN_SEED, "target_used": False,
        "gate_note": "full-gene gate FAIL overridden by user (local-proxy-insufficiency); server arbitrates"},
        sort_keys=True)
    aa.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)
    aa.write_h5ad(cand_dir / "submission.rerun.h5ad")
    assert sha256(cand_dir / "submission.rerun.h5ad") == diag["candidate_sha"]
    (cand_dir / "submission.rerun.h5ad").unlink()
    diag["rerun_bytes_identical"] = True

    cio = _contract_io()
    res = dict(cio.validate_h5ad_contract(
        out, task="T1", board="val",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0004, parent_sha256=V0004_SHA))
    diag["contract"] = res.get("status")
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"

    import subprocess
    mout = RUN / "metrics" / "scorer_v0022.json"
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
    (RUN / "metrics" / "scorer_v0022_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["wall_s"] = time.time() - t00
    (RUN / "BUILD.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"candidate_sha": diag["candidate_sha"], "contract": diag["contract"],
                      "local": keep}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
