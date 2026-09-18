#!/usr/bin/env python3
"""G1-T1-R1 neural-ODE dynamics: continuous-time latent dynamics replaces static shift assignment.

Parent: v0004 strict pseudobulk shift recipe (damp=1.0 repro gate required).
New component: neural ODE drift f(z,t) on 50-PC latent, E8.5(t=0)->E9.5(t=1) MMD fit (CPU torch);
  integrate E9.5 cells to t=2, nearest-E9.5-state-centroid assignment in latent space,
  decode with that state's pure Delta_c (same formula as v0004).
Frozen: v0004 obs_names/order (5118 rows), panel, E8.5/E9.5 inputs, seeds.
No target data (E10.5 unseen), no external data, no composition change.
Resource caps: OMP/torch/sklearn threads <= 16, single process.
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

import torch
import torch.nn as nn

TASK_ID = "G1-T1-R1-NEURAL-ODE"
BOARD = "T1:val"
RUN_SEED = 20260916
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118
N_PC = 50
HIDDEN = 128
EPOCHS = 200
BATCH = 2048
LR = 1e-3
RK_STEPS = 10

from scripts.t1_temporal_model import _load_board_input, _masked_means


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


class Drift(nn.Module):
    def __init__(self, dim: int, hidden: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim + 1, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, dim))
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.1)
                nn.init.zeros_(m.bias)

    def forward(self, z: torch.Tensor, t: float) -> torch.Tensor:
        tt = torch.full((z.shape[0], 1), t, dtype=z.dtype, device=z.device)
        return self.net(torch.cat([z, tt], dim=1))


def rk4_step(f: Drift, z: torch.Tensor, t: float, dt: float) -> torch.Tensor:
    k1 = f(z, t)
    k2 = f(z + 0.5 * dt * k1, t + 0.5 * dt)
    k3 = f(z + 0.5 * dt * k2, t + 0.5 * dt)
    k4 = f(z + dt * k3, t + dt)
    return z + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0


def integrate(f: Drift, z0: torch.Tensor, t0: float, t1: float, steps: int,
              no_grad: bool = True) -> torch.Tensor:
    def _go() -> torch.Tensor:
        z = z0.clone()
        dt = (t1 - t0) / steps
        t = t0
        for _ in range(steps):
            z = rk4_step(f, z, t, dt)
            t += dt
        return z
    if no_grad:
        with torch.no_grad():
            return _go()
    return _go()


def rbf_mmd(x: torch.Tensor, y: torch.Tensor, sigma: float) -> torch.Tensor:
    def k(a, b):
        d2 = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
        return torch.exp(-d2 / (2 * sigma * sigma))
    return k(x, x).mean() + k(y, y).mean() - 2 * k(x, y).mean()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0015_g0_t1_r1_neural_ode")
    args = ap.parse_args()
    torch.set_num_threads(16)
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)
    rng = np.random.default_rng(RUN_SEED)

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T1_val").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "torch_threads": torch.get_num_threads()}

    t00 = time.time()
    assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
    diag["v0004_sha_ok"] = True

    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    v4 = ad.read_h5ad(V0004)
    v4_names = [str(v) for v in v4.obs_names]
    assert len(v4_names) == N_CELLS and len(set(v4_names)) == N_CELLS
    base_names = [str(v) for v in base.obs_names]
    base_index = {n: i for i, n in enumerate(base_names)}
    assert all(n in base_index for n in v4_names), "v0004 rows must come from E9.5"
    src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
    diag["v0004_rows_subset_of_e95"] = True

    def to_dense(a) -> np.ndarray:
        X = a.X
        if sparse.issparse(X):
            X = X.toarray()
        return np.asarray(X, dtype=np.float32)

    Xp = to_dense(prev)
    Xb = to_dense(base)
    diag["x_range_prev"] = [float(Xp.min()), float(Xp.max())]
    diag["x_range_base"] = [float(Xb.min()), float(Xb.max())]

    # Pure per-type deltas (v0004 formula).
    prev_means, _ = _masked_means(prev.X, np.asarray(prev.obs["celltype"].astype(str)))
    base_means, _ = _masked_means(base.X, np.asarray(base.obs["celltype"].astype(str)))
    template = next(iter(base_means.values()))
    zeros = np.zeros_like(template, dtype=np.float32)
    deltas = {}
    for ct in np.unique(np.asarray(base.obs["celltype"].astype(str))):
        ct = str(ct)
        deltas[ct] = (base_means[ct] - prev_means[ct]).astype(np.float32) if ct in prev_means else zeros.copy()

    # Latent space: PCA-50 on combined E8.5+E9.5.
    Xall = np.vstack([Xp, Xb])
    mu = Xall.mean(axis=0, keepdims=True)
    sd = Xall.std(axis=0, keepdims=True) + 1e-6
    Zall = (Xall - mu) / sd
    pca = PCA(n_components=N_PC, svd_solver="randomized", random_state=RUN_SEED)
    Lall = pca.fit_transform(Zall).astype(np.float32)
    diag["pca_explained_var"] = float(pca.explained_variance_ratio_.sum())
    Lp = torch.from_numpy(Lall[: len(Xp)])
    Lb = torch.from_numpy(Lall[len(Xp):])
    n0, n1 = len(Xp), len(Xb)

    # Fit neural ODE drift: push E8.5 particles to E9.5 population (MMD).
    f = Drift(N_PC, HIDDEN)
    opt = torch.optim.Adam(f.parameters(), lr=LR)
    with torch.no_grad():
        d2 = ((Lb[:2000, None, :] - Lb[None, :2000, :]) ** 2).sum(-1)
        sigma = float(torch.median(d2).sqrt()) + 1e-6
    diag["mmd_sigma"] = sigma
    g = torch.Generator().manual_seed(RUN_SEED)
    curve = []
    f.train()
    for ep in range(EPOCHS):
        i0 = torch.randint(0, n0, (BATCH,), generator=g)
        i1 = torch.randint(0, n1, (BATCH,), generator=g)
        z0 = Lp[i0]
        pred = integrate(f, z0, 0.0, 1.0, RK_STEPS, no_grad=False)
        loss = rbf_mmd(pred, Lb[i1], sigma)
        opt.zero_grad()
        loss.backward()
        opt.step()
        curve.append(float(loss))
        if (ep + 1) % 50 == 0:
            print(json.dumps({"epoch": ep + 1, "mmd": float(loss)}), flush=True)
    diag["mmd_first"] = curve[0]
    diag["mmd_last"] = curve[-1]
    torch.save(f.state_dict(), RUN / "intermediates" / "drift.pt")

    # Predict E10.5 latent: integrate E9.5 cells t=1 -> t=2.
    f.eval()
    with torch.no_grad():
        Lpred = integrate(f, Lb, 1.0, 2.0, RK_STEPS).numpy()

    # State assignment in latent space: nearest E9.5 per-type centroid.
    Lb_np = Lb.numpy()
    ctypes = np.asarray(base.obs["celltype"].astype(str))
    states = sorted(set(ctypes.tolist()))
    centroids = {s: Lb_np[ctypes == s].mean(axis=0) for s in states}
    C = np.stack([centroids[s] for s in states])
    d2p = ((Lpred[:, None, :] - C[None, :, :]) ** 2).sum(-1)
    assign = np.array([states[i] for i in d2p.argmin(axis=1)])
    orig = ctypes
    diag["reassigned_frac"] = float((assign != orig).mean())
    flow = pd.crosstab(pd.Series(orig, name="orig"), pd.Series(assign, name="pred"))
    flow.to_csv(RUN / "intermediates" / "state_flow.tsv", sep="\t")

    # Decode: source E9.5 expression + assigned-state pure delta; v0004 row order.
    Xout = np.empty((N_CELLS, len(panel)), dtype=np.float32)
    for j, si in enumerate(src_idx):
        Xout[j] = Xb[si] + deltas[str(assign[si])]
    Xout = np.clip(Xout, 0.0, None)

    cand_dir = RUN / "candidates" / "T1_val" / args.out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=Xout, obs=v4.obs.copy(), var=pd.DataFrame(index=panel))
    # Provenance BEFORE validation: contract requires uns.ve_contract.normalization present.
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_g0_t1_r1"] = json.dumps({"atom_id": TASK_ID, "lane": "L1_NEURAL_ODE",
        "method": "neural_ode_dynamics_plus_pure_delta_decode", "parent": "v0004 recipe",
        "seed": RUN_SEED, "target_used": False}, sort_keys=True)
    a.write_h5ad(out)
    diag["candidate"] = str(out)
    diag["candidate_sha"] = sha256(out)

    # Rerun byte-identical gate: re-decode from saved drift (deterministic path).
    f2 = Drift(N_PC, HIDDEN)
    f2.load_state_dict(torch.load(RUN / "intermediates" / "drift.pt"))
    f2.eval()
    with torch.no_grad():
        Lpred2 = integrate(f2, Lb, 1.0, 2.0, RK_STEPS).numpy()
    assert np.array_equal(Lpred2, Lpred), "decode not deterministic"
    diag["rerun_latent_identical"] = True

    # Contract + provenance patch (expression bytes frozen).
    cio = _contract_io()
    res = dict(cio.validate_h5ad_contract(
        out, task="T1", board="val",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0004, parent_sha256=V0004_SHA))
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
    diag["contract"] = res.get("status")
    import hashlib as _hl
    c = ad.read_h5ad(out)
    cx = np.ascontiguousarray(c.X.toarray() if sparse.issparse(c.X) else np.asarray(c.X))
    diag["expression_digest"] = _hl.sha256(cx.tobytes()).hexdigest()
    assert c.uns.get("ve_contract", {}).get("normalization") == "log1p_normalized"
    diag["candidate_sha_final"] = sha256(out)

    # Local scorer gate (same invocation as B4 T1-R1).
    import subprocess
    mout = RUN / "metrics" / "scorer_L1_NEURAL_ODE.json"
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
    (RUN / "metrics" / "scorer_L1_NEURAL_ODE_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["beats_baseline"] = bool(keep["de_score"] > 0.8868 and keep["de_direction"] > 0.8895)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"beats_baseline": diag["beats_baseline"], "local": keep,
                      "reassigned_frac": diag["reassigned_frac"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
