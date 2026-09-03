#!/usr/bin/env python3
"""MIOFlow worker for HX-DYNAMICS-KILLTEST — runs ONLY inside .venvs/ve-hx-mioflow.

One training run with library-default hyperparameters (mioflow 0.1.14):

* GrowthRateModel (hidden 32, use_time=True), UOT pretrain (reg_m=[1.0,100.0],
  div='l2', 50 epochs, lr 1e-3) — all library defaults;
* MIOFlow(use_sde=True) global training, 100 epochs, full batch, lr 1e-3,
  lambda_ot=1.0, lambda_energy=0.01, energy_time_steps=10, sde_dt=0.1,
  diffusion scales 0.1/0.1, grad_clip=1.0, no scheduler — all library defaults;
* generation: seeded identity-order pass over ALL t=0 (E8.5) initial points
  with torchsde.sdeint(dt=0.1), endpoints at t=1, denormalised back to the
  z-scored marker space; per-path weight = growth-model mass of its initial
  point at t=0 (softplus output; the growth/death signal).

Reads/writes only standard npz/json intermediates.  Never touches the network,
never reads hidden stages, never writes H5AD candidates.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import types
from pathlib import Path

import numpy as np


def _import_mioflow():
    """Import mioflow; work around the upstream broken `core.datasets` fallback
    import in mioflow.growth_rate by aliasing the real subpackage.  The library
    source is NOT modified."""
    import mioflow.core.datasets as _ds

    core = types.ModuleType("core")
    core.datasets = _ds
    sys.modules.setdefault("core", core)
    sys.modules.setdefault("core.datasets", _ds)

    from mioflow import MIOFlow  # noqa: WPS433
    from mioflow.growth_rate import GrowthRateModel  # noqa: WPS433

    return MIOFlow, GrowthRateModel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--epochs", type=int, default=100)      # library default
    parser.add_argument("--growth-epochs", type=int, default=50)  # library default
    args = parser.parse_args()

    import anndata as ad
    import pandas as pd
    import torch

    MIOFlow, GrowthRateModel = _import_mioflow()

    npz = np.load(args.input, allow_pickle=False)
    X0 = np.asarray(npz["X0"], dtype=np.float32)
    X1 = np.asarray(npz["X1"], dtype=np.float32)
    n0, dim = X0.shape

    embedding = np.vstack([X0, X1])
    adata = ad.AnnData(
        X=np.zeros((embedding.shape[0], 1), dtype=np.float32),
        obs=pd.DataFrame({"time_bin": ["E8.5"] * n0 + ["E9.5"] * X1.shape[0]}),
    )
    adata.obsm["X_pca"] = embedding  # gaga_model=None -> used as-is, z-normalised inside

    wall: dict[str, float] = {}

    torch.manual_seed(args.seed)
    np.random.seed(args.seed % (2**32))

    t0 = time.monotonic()
    growth_model = GrowthRateModel(
        adata,
        gaga_input_key="X_pca",
        obs_time_key="time_bin",
        use_cuda=False,  # CPU-only box; flag matches library default behaviour
    )
    growth_model.pretrain(num_epochs=args.growth_epochs)  # reg_m/div/lr = defaults
    wall["growth_pretrain_seconds"] = time.monotonic() - t0

    torch.manual_seed(args.seed)
    t0 = time.monotonic()
    mf = MIOFlow(
        adata,
        gaga_input_key="X_pca",
        obs_time_key="time_bin",
        use_sde=True,
        use_cuda=False,
        growth_rate_model=growth_model,
        n_epochs=args.epochs,
        n_trajectories=1,   # internal preview only; the measured generation pass below
        n_bins=100,         # covers all initial points in identity order instead
        debug_level="warning",
        exp_dir="/tmp/hx_mioflow_run",
    )
    mf.fit()
    wall["fit_seconds"] = time.monotonic() - t0

    # --- measured generation: every E8.5 initial point, identity order, seeded
    torch.manual_seed(args.seed + 1)
    t0 = time.monotonic()
    model = mf.ode_model
    model.eval()
    x0_normed = torch.tensor(mf.dataset.time_series_data[0][0], dtype=torch.float32)
    t_bins = torch.linspace(0.0, 1.0, 100)
    import torchsde

    with torch.no_grad():
        traj = torchsde.sdeint(model, x0_normed, t_bins, dt=0.1)  # library defaults
    endpoints = traj[-1].cpu().numpy() * mf.std_vals + mf.mean_vals

    growth_model.eval()
    with torch.no_grad():
        t_start = torch.tensor([0.0], dtype=torch.float32)
        weights = growth_model(x0_normed, t_start).cpu().numpy()
    wall["generation_seconds"] = time.monotonic() - t0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp.npz")
    np.savez(
        tmp,
        endpoints_z=endpoints.astype(np.float32),
        weights=weights.astype(np.float64),
        x0_z=(x0_normed.cpu().numpy() * mf.std_vals + mf.mean_vals).astype(np.float32),
        centroids_resolved_z=npz["centroids_resolved_z"],
        resolved_targets=npz["resolved_targets"],
        loss_epochs=np.asarray(mf.losses["epoch"], dtype=np.float64),
        loss_total=np.asarray(mf.losses["total_loss"], dtype=np.float64),
        loss_ot=np.asarray(mf.losses["ot_loss"], dtype=np.float64),
        loss_energy=np.asarray(mf.losses["energy_loss"], dtype=np.float64),
    )
    tmp.replace(out_path)

    summary = {
        "schema": "ve.hx.mioflow-train-summary.v1",
        "seed": args.seed,
        "n_initial_points": int(n0),
        "n_target_points": int(X1.shape[0]),
        "embedding_dim": int(dim),
        "n_epochs": args.epochs,
        "growth_pretrain_epochs": args.growth_epochs,
        "wall": wall,
        "loss_first": float(mf.losses["total_loss"][0]),
        "loss_last": float(mf.losses["total_loss"][-1]),
        "ot_loss_last": float(mf.losses["ot_loss"][-1]),
        "energy_loss_last": float(mf.losses["energy_loss"][-1]),
        "weight_summary": {
            "min": float(weights.min()),
            "mean": float(weights.mean()),
            "max": float(weights.max()),
            "frac_dead_below_0.05": float((weights < 0.05).mean()),
        },
        "endpoints_finite": bool(np.isfinite(endpoints).all()),
    }
    summary_path = Path(args.summary)
    tmpj = summary_path.with_suffix(".tmp.json")
    tmpj.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmpj.replace(summary_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
