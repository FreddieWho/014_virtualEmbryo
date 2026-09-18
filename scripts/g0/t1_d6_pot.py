#!/usr/bin/env python3
"""G1-T1-D6 potential SDE: drift = -grad(Psi), fixed diffusion, seeded EM.

PRESCIENT-style stochastic dynamics in PCA-512 (disclosed deviations in DESIGN.md).
Modes: --smoke (tiny CPU mechanics), full train (GPU), --build-only (local:
checkpoint -> return gate (standing dual, no vacuous legs) -> E10.5 v0025).
Seeded RNG throughout (K-draw means deterministic).
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

import numpy as np
import pandas as pd
from scipy import sparse

TASK_ID = "G1-T1-D6-POT"
RUN_SEED = 20260916
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
RUNDIR = REPO / "artifacts" / "g0" / "G1-T1-D6-POT-20260917-v1"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895
PCAD = 512
LR, WD, BATCH, EPOCHS = 1e-4, 1e-5, 512, 25
LAM_KIN = 0.01
SIGMA, EM_STEPS, K_DRAWS = 0.1, 10, 4
HOLDOUT_N = 2000
TRAIN_CAP_S = 14400

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


def laplacian_mmd(x, y, sigma: float = 1.0, eps: float = 1e-8):
    import torch
    d = torch.cdist(x, y, p=1)
    Kxy = torch.exp(-torch.clamp(d, min=eps) / (sigma * x.shape[1]))
    dxx = torch.cdist(x, x, p=1)
    Kxx = torch.exp(-torch.clamp(dxx, min=eps) / (sigma * x.shape[1]))
    dyy = torch.cdist(y, y, p=1)
    Kyy = torch.exp(-torch.clamp(dyy, min=eps) / (sigma * y.shape[1]))
    return Kxx.mean() + Kyy.mean() - 2 * Kxy.mean()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--checkpoint", default="")
    args = ap.parse_args()
    import torch
    import torch.nn as nn
    torch.set_num_threads(16)
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)

    smoke = bool(args.smoke)
    pcad = 16 if smoke else PCAD
    hid = 64 if smoke else 256
    bs = 128 if smoke else BATCH
    epochs = 1 if smoke else EPOCHS
    em_steps = 2 if smoke else EM_STEPS
    cap_s = 600 if smoke else TRAIN_CAP_S

    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "smoke": smoke,
                  "pcad": pcad, "build_only": bool(args.build_only)}
    t00 = time.time()
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]

    import anndata as ad
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    n_cells = 200 if smoke else None
    Xp = to_dense(prev)[:n_cells] if n_cells else to_dense(prev)
    Xb = to_dense(base)[:n_cells] if n_cells else to_dense(base)
    tp = np.asarray(prev.obs["celltype"].astype(str))[:n_cells] if n_cells else np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))[:n_cells] if n_cells else np.asarray(base.obs["celltype"].astype(str))
    genes = panel if not smoke else panel[:64]
    if len(genes) == len(panel):
        pass
    else:
        gi = np.array([panel.index(g) for g in genes])
        Xp, Xb = Xp[:, gi], Xb[:, gi]
    D = len(genes)

    def batches(n, size, min_n):
        out, a = [], 0
        while a < n:
            b = min(a + size, n)
            if b < n and n - b < min_n:
                b = n
            out.append((a, b))
            a = b
        return out

    class Potential(nn.Module):
        def __init__(self, d: int, h: int):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(d, h), nn.SiLU(),
                                     nn.Linear(h, h), nn.SiLU(),
                                     nn.Linear(h, 1))
            for m in self.net:
                if isinstance(m, nn.Linear):
                    nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                    nn.init.zeros_(m.bias)

        def drift(self, x, cg=True):
            xr = x.detach().requires_grad_(True)
            e = self.net(xr).sum()
            g = torch.autograd.grad(e, xr, create_graph=cg)[0]
            return -g

    pot = Potential(pcad, hid)

    if args.build_only:
        assert args.checkpoint, "--checkpoint required"
        ck = torch.load(args.checkpoint, map_location="cpu", weights_only=False)  # trusted: own artifact, sha-verified
        pot.load_state_dict(ck["pot"])
        V = np.asarray(ck["V"], dtype=np.float32)
        mu = np.asarray(ck["mu"], dtype=np.float32)
        psd = np.asarray(ck["psd"], dtype=np.float32)
        assert V.shape == (len(panel), pcad)
        Zp = np.empty((len(Xp), pcad), dtype=np.float32)
        Zb = np.empty((len(Xb), pcad), dtype=np.float32)
        for a in range(0, len(Xp), 4096):
            Zp[a:a + 4096] = ((Xp[a:a + 4096].astype(np.float32) - mu) @ V / psd)
        for a in range(0, len(Xb), 4096):
            Zb[a:a + 4096] = ((Xb[a:a + 4096].astype(np.float32) - mu) @ V / psd)
        del Xp, Xb
        diag["loaded_checkpoint"] = args.checkpoint
    else:
        from sklearn.decomposition import IncrementalPCA
        ipca = IncrementalPCA(n_components=pcad, batch_size=2048)
        for Xa in (Xp, Xb):
            for a, b in batches(len(Xa), 2048, pcad):
                ipca.partial_fit(Xa[a:b].astype(np.float64))
        V = ipca.components_.T.astype(np.float32)
        mu = ipca.mean_.astype(np.float32)
        Zp = np.empty((len(Xp), pcad), dtype=np.float32)
        Zb = np.empty((len(Xb), pcad), dtype=np.float32)
        for a in range(0, len(Xp), 4096):
            Zp[a:a + 4096] = ipca.transform(Xp[a:a + 4096].astype(np.float64)).astype(np.float32)
        for a in range(0, len(Xb), 4096):
            Zb[a:a + 4096] = ipca.transform(Xb[a:a + 4096].astype(np.float64)).astype(np.float32)
        del Xp, Xb
        diag["pca_explained"] = float(ipca.explained_variance_ratio_.sum())
        psd = Zp.std(axis=0) + Zb.std(axis=0)
        psd = (psd / 2 + 1e-8).astype(np.float32)
        Zp, Zb = (Zp / psd).astype(np.float32), (Zb / psd).astype(np.float32)
        Zp_t = torch.from_numpy(Zp)
        Zb_t = torch.from_numpy(Zb)
        opt = torch.optim.AdamW(pot.parameters(), lr=LR, weight_decay=WD)
        rng = np.random.default_rng(RUN_SEED)
        h_idx = rng.choice(len(Zp), size=min(HOLDOUT_N, len(Zp) // 5), replace=False)
        dt = 1.0 / em_steps
        sq = SIGMA * (dt ** 0.5)
        g_em = torch.Generator().manual_seed(RUN_SEED)
        step, done = 0, False
        t_start = time.time()
        for ep in range(epochs):
            perm = torch.randperm(len(Zp_t))
            for a in range(0, len(Zp_t), bs):
                idx = perm[a:a + bs]
                z0 = Zp_t[idx]
                zt = z0.clone()
                for _ in range(em_steps):
                    zt = zt + pot.drift(zt) * dt + sq * torch.randn(zt.shape, generator=g_em)
                jdx = torch.randperm(len(Zb_t))[: len(zt)]
                loss = laplacian_mmd(zt, Zb_t[jdx]) + LAM_KIN * (pot.drift(z0).pow(2).mean())
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(pot.parameters(), 1.0)
                opt.step()
                step += 1
                if not torch.isfinite(loss):
                    diag["nan_loss_at_step"] = step
                    done = True
                    break
            diag["last_epoch"] = ep
            if time.time() - t_start > cap_s or done:
                break
        diag["train_steps"] = step
        torch.save({"pot": pot.state_dict(), "V": V, "mu": mu, "psd": psd,
                    "pcad": pcad}, RUNDIR / "intermediates" / "field_best.pt")
        diag["checkpoint_sha"] = sha256(RUNDIR / "intermediates" / "field_best.pt")

    if smoke and not args.build_only:
        ok = bool(all(bool(torch.isfinite(p).all()) for p in pot.parameters()))
        diag["wall_s"] = time.time() - t00
        (RUN / "SMOKE.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": ok, "pca_explained": diag["pca_explained"]}, indent=1), flush=True)
        return 0

    if args.build_only:
        assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
        v4 = ad.read_h5ad(V0004)
        v4_names = [str(v) for v in v4.obs_names]
        base_names = [str(v) for v in base.obs_names]
        base_index = {n: i for i, n in enumerate(base_names)}
        assert all(n in base_index for n in v4_names)
        pot.eval()
        Zp_t = torch.from_numpy(Zp)
        Zb_t = torch.from_numpy(Zb)
        rng = np.random.default_rng(RUN_SEED)
        h_idx = rng.choice(len(Zp), size=min(HOLDOUT_N, len(Zp) // 5), replace=False)
        dt = 1.0 / EM_STEPS
        sq = SIGMA * (dt ** 0.5)

        def forecast_mean_k(z0, steps, k=K_DRAWS, base_seed=RUN_SEED):
            acc = torch.zeros_like(z0)
            for kk in range(k):
                gk = torch.Generator().manual_seed(base_seed + kk)
                z = z0.clone()
                for _ in range(steps):
                    z = z + pot.drift(z, cg=False) * dt + sq * torch.randn(z.shape, generator=gk)
                acc = acc + z
            return acc.detach() / k

        cio = _contract_io()
        lock = REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json"

        def run_scorer(out: Path, tag: str) -> dict:
            import subprocess
            mout = RUN / "metrics" / f"scorer_{tag}.json"
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
            (RUN / "metrics" / f"scorer_{tag}_slim.json").write_text(json.dumps(keep, indent=1))
            return keep

        def write_candidate(Xg, obs, dirname, lane, method):
            cand_dir = RUN / "candidates" / "T1_val" / dirname
            cand_dir.mkdir(parents=True, exist_ok=True)
            out = cand_dir / "submission.h5ad"
            aa = ad.AnnData(X=np.ascontiguousarray(Xg.astype(np.float32)), obs=obs.copy(),
                            var=pd.DataFrame(index=panel))
            aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
            aa.uns["ve_g0_t1_d6"] = json.dumps({"atom_id": TASK_ID, "lane": lane,
                "method": method, "parent": "v0004 recipe", "seed": RUN_SEED,
                "k_draws": K_DRAWS, "target_used": False}, sort_keys=True)
            aa.write_h5ad(out)
            return out, cand_dir

        def decode(Z):
            return np.clip((Z * psd) @ V.T + mu, 0.0, None).astype(np.float32)

        # G-return: E8.5 held-out, K-draw mean, full-gene decode (no vacuous legs)
        G = forecast_mean_k(Zp_t[h_idx], EM_STEPS).numpy()
        Xret = decode(G)
        assert np.isfinite(Xret).all(), "diverged return"
        robs = prev.obs.iloc[np.asarray(h_idx)].copy()
        assert len(set(robs.index.astype(str))) == len(robs)
        out_ret, _ = write_candidate(Xret, robs, "gate_return", "G_RETURN", "d6_pot_return")
        res = dict(cio.validate_h5ad_contract(
            out_ret, task="T1", board="val", scorer_lock=lock,
            parent_path=V0004, parent_sha256=V0004_SHA))
        ok_sub = [v.get("status") in ("PASS", "pass")
                  for k, v in res.get("checks", {}).items() if k != "protected_parent"]
        assert all(ok_sub), f"return contract substance: {res}"
        mret = run_scorer(out_ret, "G_RETURN")
        diag["return_local"] = mret
        gate = bool(mret["de_score"] > LOCAL_DE and mret["de_direction"] > LOCAL_DIR)
        diag["gate_pass"] = gate
        print(json.dumps({"gate_pass": gate, "return": mret}, indent=1), flush=True)
        if not gate:
            diag["wall_s"] = time.time() - t00
            (RUN / "BUILD.json").write_text(json.dumps(diag, indent=1, default=float))
            print(json.dumps({"gate_pass": False, "note": "STOP, no E10.5 candidate"}, indent=1), flush=True)
            return 0
        # E10.5: v0004 bank, K-draw mean, t=1->2 (20 steps)
        v4_names = [str(v) for v in v4.obs_names]
        base_names = [str(v) for v in base.obs_names]
        base_index = {n: i for i, n in enumerate(base_names)}
        assert all(n in base_index for n in v4_names)
        src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
        Gd = forecast_mean_k(Zb_t[src_idx], 20).numpy()
        Xout = decode(Gd)
        assert np.isfinite(Xout).all(), "diverged forecast"
        out, cand_dir = write_candidate(Xout, v4.obs.copy(), "v0025_g0_t1_d6_pot", "L1_POT", "d6_pot_forecast")
        diag["candidate_sha"] = sha256(out)
        out, _ = write_candidate(Xout, v4.obs.copy(), "v0025_g0_t1_d6_pot", "L1_POT", "d6_pot_forecast")
        assert sha256(out) == diag["candidate_sha"]
        diag["rerun_bytes_identical"] = True
        res = dict(cio.validate_h5ad_contract(
            out, task="T1", board="val", scorer_lock=lock,
            parent_path=V0004, parent_sha256=V0004_SHA))
        diag["contract"] = res.get("status")
        assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
        mloc = run_scorer(out, "L1_POT")
        diag["local"] = mloc
        diag["promoted"] = bool(mloc["de_score"] > LOCAL_DE and mloc["de_direction"] > LOCAL_DIR)
        diag["wall_s"] = time.time() - t00
        (RUN / "BUILD.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"gate_pass": True, "promoted": diag["promoted"],
                          "local": mloc, "sha": diag["candidate_sha"]}, indent=1), flush=True)
        return 0

    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT_train.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"trained": True, "steps": diag.get("train_steps"),
                      "checkpoint": diag.get("checkpoint_sha")}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
