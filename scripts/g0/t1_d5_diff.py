#!/usr/bin/env python3
"""G1-T1-D5 conditional diffusion: DDPM in PCA-512, conditioned on (t, celltype).

SquidDiff-style generation + v0004 0.5/0.5 blend (fixed w, disclosed).
Modes: --smoke (tiny CPU mechanics), full train (GPU), --build-only (local:
checkpoint -> return gate -> E10.5 candidate v0024 -> contract/scorer/INDEX-ready).
Director deviations disclosed in DESIGN.md. Seeded RNG throughout.
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

TASK_ID = "G1-T1-D5-DIFF"
RUN_SEED = 20260916
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
RUNDIR = REPO / "artifacts" / "g0" / "G1-T1-D5-DIFF-20260917-v1"
LINMAP = REPO / "artifacts" / "g0" / "G1-T1-D1-SCIMF-20260917-v1" / "lineage_map.json"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895
PCAD, NTYPES = 512, 28
LR, WD, BATCH, EPOCHS = 1e-4, 1e-5, 1024, 20
T_DIFF, BETA0, BETA1 = 200, 1e-4, 0.02
W_COMBO = 0.5
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


def energy_compJSD(A: np.ndarray, B: np.ndarray, la: np.ndarray, lb: np.ndarray, seed: int, n: int = 2000):
    rng = np.random.default_rng(seed)
    ia = rng.choice(len(A), size=min(n, len(A)), replace=False)
    ib = rng.choice(len(B), size=min(n, len(B)), replace=False)
    A, B = A[ia].astype(np.float64), B[ib].astype(np.float64)
    from scipy.spatial.distance import cdist
    e = float(2 * cdist(A, B).mean() - cdist(A, A).mean() - cdist(B, B).mean())
    ka, kb = sorted(set(la.tolist())), sorted(set(lb.tolist()))
    pa = np.array([np.mean(la[ia] == k) for k in ka])
    qa = np.array([np.mean(lb[ib] == k) for k in ka])
    m = 0.5 * (pa + qa) + 1e-12
    jsd = float(0.5 * (pa * np.log(pa / m + 1e-12)).sum() + 0.5 * (qa * np.log(qa / m + 1e-12)).sum())
    return {"energy": e, "composition_JSD": jsd}


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
    g_noise = torch.Generator().manual_seed(RUN_SEED)

    smoke = bool(args.smoke)
    pcad = 16 if smoke else PCAD
    hid = 64 if smoke else 1024
    nT = 20 if smoke else T_DIFF
    bs = 128 if smoke else BATCH
    epochs = 1 if smoke else EPOCHS
    cap_s = 600 if smoke else TRAIN_CAP_S

    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "smoke": smoke,
                  "pcad": pcad, "build_only": bool(args.build_only)}
    t00 = time.time()
    assert LINMAP.exists(), "BLOCKED_INPUT: lineage_map.json missing"
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
    gi = np.array([panel.index(g) for g in genes])
    if len(genes) == len(panel):
        pass
    else:
        Xp, Xb = Xp[:, gi], Xb[:, gi]
    D = len(genes)

    from sklearn.decomposition import IncrementalPCA

    def batches(n, size, min_n):
        out, a = [], 0
        while a < n:
            b = min(a + size, n)
            if b < n and n - b < min_n:
                b = n
            out.append((a, b))
            a = b
        return out

    states = sorted(set(tp.tolist()) | set(tb.tolist()))
    si = {s: i for i, s in enumerate(states)}
    diag["n_states"] = len(states)

    class Denoiser(nn.Module):
        def __init__(self, d: int, h: int, nty: int):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(d + 1 + nty, h), nn.SiLU(),
                                     nn.Linear(h, h), nn.SiLU(),
                                     nn.Linear(h, h), nn.SiLU(),
                                     nn.Linear(h, d))
            for m in self.net:
                if isinstance(m, nn.Linear):
                    nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                    nn.init.zeros_(m.bias)

        def forward(self, x, t, ty):
            if torch.is_tensor(t):
                tt = t.reshape(x.shape[0], 1).to(dtype=x.dtype)
            else:
                tt = torch.full((x.shape[0], 1), float(t), dtype=x.dtype, device=x.device)
            return self.net(torch.cat([x, tt, ty], dim=1))

    betas = torch.linspace(BETA0, BETA1, nT)
    alphas = 1.0 - betas
    abar = torch.cumprod(alphas, dim=0)

    den = Denoiser(pcad, hid, len(states))

    if args.build_only:
        assert args.checkpoint, "--checkpoint required"
        ck = torch.load(args.checkpoint, map_location="cpu", weights_only=False)  # trusted: own artifact, sha-verified
        den.load_state_dict(ck["den"])
        V = np.asarray(ck["V"], dtype=np.float32)
        mu = np.asarray(ck["mu"], dtype=np.float32)
        psd = np.asarray(ck["psd"], dtype=np.float32)
        assert V.shape == (len(panel), pcad)
        den.eval()
        diag["loaded_checkpoint"] = args.checkpoint
    else:
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
        T0 = torch.from_numpy(np.array([si[t] for t in tp], dtype=np.int64))
        T1 = torch.from_numpy(np.array([si[t] for t in tb], dtype=np.int64))
        oh = lambda v: torch.nn.functional.one_hot(v, len(states)).float()
        opt = torch.optim.AdamW(den.parameters(), lr=LR, weight_decay=WD)
        rng = np.random.default_rng(RUN_SEED)
        h_idx = rng.choice(len(Zp), size=min(HOLDOUT_N, len(Zp) // 5), replace=False)
        step, done = 0, False
        t_start = time.time()
        Zall = torch.cat([Zp_t, Zb_t])
        Tall = torch.cat([torch.zeros(len(Zp_t)), torch.ones(len(Zb_t))])
        Yall = torch.cat([T0, T1])
        for ep in range(epochs):
            perm = torch.randperm(len(Zall))
            for a in range(0, len(Zall), bs):
                idx = perm[a:a + bs]
                x0, tt0, yy0 = Zall[idx], Tall[idx], oh(Yall[idx])
                ti = torch.randint(0, nT, (len(idx),))
                ab = abar[ti].unsqueeze(1)
                eps = torch.randn(x0.shape, generator=g_noise)
                xt = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
                pred = den(xt, ti.float().unsqueeze(1) / nT, yy0)
                loss = ((pred - eps) ** 2).mean()
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(den.parameters(), 1.0)
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
        torch.save({"den": den.state_dict(), "V": V, "mu": mu, "psd": psd,
                    "states": states, "pcad": pcad, "nT": nT},
                   RUNDIR / "intermediates" / "field_best.pt")
        diag["checkpoint_sha"] = sha256(RUNDIR / "intermediates" / "field_best.pt")

    if smoke and not args.build_only:
        enc_ok = bool(all(bool(torch.isfinite(p).all()) for p in den.parameters()))
        diag["wall_s"] = time.time() - t00
        (RUN / "SMOKE.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": enc_ok, "pca_explained": diag["pca_explained"]}, indent=1), flush=True)
        return 0

    if args.build_only:
        assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
        v4 = ad.read_h5ad(V0004)
        Xb4 = to_dense(base)[:, [panel.index(g) for g in genes]]
        Zb4 = (((Xb4 - mu) @ V) / psd).astype(np.float32)
        Tb4 = np.array([si[t] for t in np.asarray(base.obs["celltype"].astype(str))], dtype=np.int64)

        @torch.no_grad()
        def generate(types, tcond, n_steps=100):
            n = len(types)
            x = torch.randn((n, pcad), generator=torch.Generator().manual_seed(RUN_SEED))
            ty = torch.nn.functional.one_hot(torch.from_numpy(types), len(states)).float()
            tc = torch.full((n, 1), float(tcond))
            for i in reversed(range(n_steps)):
                tcur = torch.full((n, 1), float(i) / nT)
                ep = den(x, tcur, ty)
                a, ab = alphas[i], abar[i]
                x = (x - (1 - a) / (1 - ab).sqrt() * ep) / a.sqrt()
                if i > 0:
                    x = x + betas[i].sqrt() * torch.randn(x.shape, generator=torch.Generator().manual_seed(RUN_SEED + i))
            return x.numpy()

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
            aa.uns["ve_g0_t1_d5"] = json.dumps({"atom_id": TASK_ID, "lane": lane,
                "method": method, "parent": "v0004 recipe + diffusion blend",
                "seed": RUN_SEED, "w_combo": W_COMBO, "target_used": False}, sort_keys=True)
            aa.write_h5ad(out)
            return out, cand_dir

        def decode(Z):
            return np.clip((Z * psd) @ V.T + mu, 0.0, None).astype(np.float32)

        # G-return: held-out E8.5 types, condition t=1
        rng = np.random.default_rng(RUN_SEED)
        h_idx = rng.choice(len(np.asarray(prev.obs["celltype"])), size=min(HOLDOUT_N, len(np.asarray(prev.obs["celltype"])) // 5), replace=False)
        Xp_h = to_dense(prev)[:, [panel.index(g) for g in genes]]
        Zp_h = (((Xp_h - mu) @ V) / psd).astype(np.float32)
        del Xp_h
        th = np.array([si[t] for t in np.asarray(prev.obs["celltype"].astype(str))[h_idx]], dtype=np.int64)
        G = generate(th, 1.0)
        Xret = decode(G)
        robs = prev.obs.iloc[np.asarray(h_idx)].copy()
        assert len(set(robs.index.astype(str))) == len(robs)
        out_ret, _ = write_candidate(Xret, robs, "gate_return", "G_RETURN", "d5_diff_return")
        res = dict(cio.validate_h5ad_contract(
            out_ret, task="T1", board="val", scorer_lock=lock,
            parent_path=V0004, parent_sha256=V0004_SHA))
        ok_sub = [v.get("status") in ("PASS", "pass")
                  for k, v in res.get("checks", {}).items() if k != "protected_parent"]
        assert all(ok_sub), f"return contract substance: {res}"
        mret = run_scorer(out_ret, "G_RETURN")
        # shift baseline in same full-gene space (exact-name shared types, else 0)
        Xb_full = to_dense(base)
        tb_all = np.asarray(base.obs["celltype"].astype(str))
        tp_all = np.asarray(prev.obs["celltype"].astype(str))
        Xp_full = to_dense(prev)
        sh = sorted(set(tp_all.tolist()) & set(tb_all.tolist()))
        dmap = {t: Xb_full[tb_all == t].mean(0) - Xp_full[tp_all == t].mean(0) for t in sh}
        Xs = Xp_full[h_idx] + np.stack([dmap.get(str(tp_all[i]), np.zeros(Xp_full.shape[1], np.float32)) for i in h_idx])
        base_m = energy_compJSD(Xs, Xb_full[rng.choice(len(Xb_full), 3000, replace=False)],
                                tp_all[h_idx], tb_all, RUN_SEED)
        mret_full = dict(mret)
        mret_full.update(energy_compJSD(Xret, Xb_full[rng.choice(len(Xb_full), 3000, replace=False)],
                                        np.asarray(prev.obs["celltype"].astype(str))[h_idx], tb_all, RUN_SEED))
        diag["return_local"] = mret
        diag["return_dist"] = {"field": {k: mret_full[k] for k in ("energy", "composition_JSD")},
                               "baseline": base_m}
        gate = bool(mret_full["energy"] < base_m["energy"]
                    and mret_full["composition_JSD"] < base_m["composition_JSD"])
        diag["gate_pass"] = gate
        print(json.dumps({"gate_pass": gate, "field_dist": diag["return_dist"]["field"],
                          "base_dist": base_m}, indent=1), flush=True)
        if not gate:
            diag["wall_s"] = time.time() - t00
            (RUN / "BUILD.json").write_text(json.dumps(diag, indent=1, default=float))
            print(json.dumps({"gate_pass": False, "note": "STOP, no E10.5 candidate"}, indent=1), flush=True)
            return 0
        # E10.5: per-bank-row type, condition t=2 (time-OOD, disclosed core risk)
        v4_names = [str(v) for v in v4.obs_names]
        base_names = [str(v) for v in base.obs_names]
        base_index = {n: i for i, n in enumerate(base_names)}
        assert all(n in base_index for n in v4_names)
        src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
        Gd = generate(Tb4[src_idx], 2.0)
        Xd = decode(Gd)
        Xv = to_dense(v4)
        Xout = np.clip(W_COMBO * Xd + (1 - W_COMBO) * Xv, 0.0, None).astype(np.float32)
        assert np.isfinite(Xout).all(), "diverged forecast"
        out, cand_dir = write_candidate(Xout, v4.obs.copy(), "v0024_g0_t1_d5_diff", "L1_DIFF", "d5_diff_combo")
        diag["candidate_sha"] = sha256(out)
        out, _ = write_candidate(Xout, v4.obs.copy(), "v0024_g0_t1_d5_diff", "L1_DIFF", "d5_diff_combo")
        assert sha256(out) == diag["candidate_sha"]
        diag["rerun_bytes_identical"] = True
        res = dict(cio.validate_h5ad_contract(
            out, task="T1", board="val", scorer_lock=lock,
            parent_path=V0004, parent_sha256=V0004_SHA))
        diag["contract"] = res.get("status")
        assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
        mloc = run_scorer(out, "L1_DIFF")
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
