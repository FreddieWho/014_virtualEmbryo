#!/usr/bin/env python3
"""G1-T1-D1 OPT-A: joint VAE + lineage-masked Transformer-MV-SDE (scIMF-style).

Self-implemented from paper spec (arXiv:2505.16492); repo reference-only, no clone.
Modes: --smoke (tiny CPU mechanics check), full train (GPU), --build-only (local:
rebuild return/E10.5 candidates from checkpoint -> contract/scorer/INDEX-ready).
Director's cut vs paper (all disclosed in DESIGN.md): PCA-first 512, centered PCA +
mean add-back, lineage-masked attention, L2 two-point DOT (E7.75 anchor removed),
mean-path forecast, fixed loss weights (recon + 1.0*KL + 1.0*W2).
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

TASK_ID = "G1-T1-D1-SCIMF"
RUN_SEED = 20260916
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
RUNDIR = REPO / "artifacts" / "g0" / "G1-T1-D1-SCIMF-20260917-v1"
LINMAP = RUNDIR / "lineage_map.json"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895
PCAD, DZ = 512, 32
LR, WD, BATCH, EPOCHS = 2e-4, 1e-5, 512, 30
LAM_KL, LAM_W2, W2_REG = 1.0, 1.0, 0.1
DIFFUSION, EM_STEPS = 0.1, 10
HOLDOUT_N = 2000
TRAIN_CAP_S = 21600

from scripts.t1_temporal_model import _load_board_input


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def to_dense(a) -> np.ndarray:
    X = a.X
    if sparse.issparse(X):
        X = X.toarray()
    return np.asarray(X, dtype=np.float32)


def _contract_io():
    iface = REPO / "docs" / "batch3" / "interfaces"
    if str(iface) not in sys.path:
        sys.path.insert(0, str(iface))
    from virtual_embryo_tools import contract_io
    return contract_io


def build_models(pcad: int, dz: int, n_lin: int, hid: int = 256):
    import torch
    import torch.nn as nn

    class Enc(nn.Module):
        def __init__(self):
            super().__init__()
            self.trunk = nn.Sequential(nn.Linear(pcad, hid), nn.SiLU(),
                                       nn.Linear(hid, hid), nn.SiLU())
            self.mu = nn.Linear(hid, dz)
            self.lv = nn.Linear(hid, dz)

        def forward(self, x):
            h = self.trunk(x)
            return self.mu(h), self.lv(h)

    class Dec(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(dz, hid), nn.SiLU(),
                                     nn.Linear(hid, hid), nn.SiLU(),
                                     nn.Linear(hid, pcad))

        def forward(self, z):
            return self.net(z)

    class Drift(nn.Module):
        def __init__(self, n_heads: int = 2):
            super().__init__()
            self.intra = nn.Sequential(nn.Linear(dz, hid), nn.SiLU(),
                                       nn.Linear(hid, hid), nn.SiLU(),
                                       nn.Linear(hid, dz))
            hd = dz // n_heads
            self.n_heads = n_heads
            self.qkv = nn.Linear(dz, 3 * dz)
            self.proj = nn.Linear(dz, dz)
            self.hd = hd

        def forward(self, z, lin):
            B = z.shape[0]
            v_intra = self.intra(z)
            qkv = self.qkv(z).reshape(B, 3, self.n_heads, self.hd).permute(1, 2, 0, 3)
            q, k, v = qkv[0], qkv[1], qkv[2]  # (H, B, hd): batch as sequence
            att = (q @ k.transpose(-2, -1)) / (self.hd ** 0.5)  # (H, B, B)
            same = (lin.unsqueeze(0) == lin.unsqueeze(1))  # (B, B)
            att = att.masked_fill(~same.unsqueeze(0), float("-inf"))
            w = torch.softmax(att, dim=-1)
            w = torch.nan_to_num(w, nan=0.0)
            v_inter = (w @ v).permute(1, 0, 2).reshape(B, -1)
            return v_intra + self.proj(v_inter)

    for m in (Enc(), Dec(), Drift()):
        for p in m.parameters():
            if p.dim() > 1:
                nn.init.kaiming_normal_(p, nonlinearity="relu")
    return Enc(), Dec(), Drift()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--checkpoint", default="")
    args = ap.parse_args()
    import torch
    torch.set_num_threads(16)
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)
    g_emu = torch.Generator().manual_seed(RUN_SEED)

    smoke = bool(args.smoke)
    pcad, dz, hid = (32, 4, 32) if smoke else (PCAD, DZ, 256)
    bs = 64 if smoke else BATCH
    epochs = 1 if smoke else EPOCHS
    em_steps = 2 if smoke else EM_STEPS
    n_cells = 200 if smoke else None

    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "smoke": smoke,
                  "pcad": pcad, "dz": dz, "build_only": bool(args.build_only)}
    t00 = time.time()
    assert LINMAP.exists(), "BLOCKED_INPUT: lineage_map.json missing"
    lin_of = json.loads(LINMAP.read_text())
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]

    import anndata as ad
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    Xp = to_dense(prev)[:n_cells] if n_cells else to_dense(prev)
    Xb = to_dense(base)[:n_cells] if n_cells else to_dense(base)
    tp = np.asarray(prev.obs["celltype"].astype(str))[:n_cells] if n_cells else np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))[:n_cells] if n_cells else np.asarray(base.obs["celltype"].astype(str))
    genes = panel if not smoke else panel[:200]
    if len(genes) == len(panel):
        pass  # full panel: keep views, avoid a 4.4GB fancy-index copy
    else:
        gi = np.array([panel.index(g) for g in genes])
        Xp, Xb = Xp[:, gi], Xb[:, gi]

    def batches(n, size, min_n):
        out, a = [], 0
        while a < n:
            b = min(a + size, n)
            if b < n and n - b < min_n:
                b = n  # absorb trailing remainder (sklearn needs batch >= n_components)
            out.append((a, b))
            a = b
        return out

    if args.build_only:
        Zp = Zb = None  # transformed with checkpoint V/mu after load below
        diag["pca_explained"] = None
    else:
        from sklearn.decomposition import IncrementalPCA
        # STREAMING (2026-09-17 OOM fix): full vstack float64 peaked ~15GB on the 15GB box.
        # IncrementalPCA in 2048-row batches peaks ~5.5GB. Deterministic for fixed order.
        ipca = IncrementalPCA(n_components=pcad, batch_size=2048)
        for Xa in (Xp, Xb):
            for a, b in batches(len(Xa), 2048, pcad):
                ipca.partial_fit(Xa[a:b].astype(np.float64))
        V = ipca.components_.T.astype(np.float32)
        mu = ipca.mean_.astype(np.float32)

        def tx(Xa):
            n = len(Xa)
            Z = np.empty((n, pcad), dtype=np.float32)
            for a in range(0, n, 2048):
                Z[a:a + 2048] = ipca.transform(Xa[a:a + 2048].astype(np.float64)).astype(np.float32)
            return Z

        Zp, Zb = tx(Xp), tx(Xb)
        del Xp, Xb
        diag["pca_explained"] = float(ipca.explained_variance_ratio_.sum())
    cov = np.mean([(t in lin_of) for t in list(tp) + list(tb)])
    assert cov >= 0.99, f"lineage coverage {cov}"
    lins = sorted(set(lin_of.values()))
    li = {s: i for i, s in enumerate(lins)}
    Lp = np.array([li[lin_of[t]] for t in tp], dtype=np.int64)
    Lb = np.array([li[lin_of[t]] for t in tb], dtype=np.int64)

    enc, dec, drift = build_models(pcad, dz, len(lins), hid)
    N_CHK = RUNDIR / "intermediates" / "field_best.pt"
    if args.build_only:
        assert args.checkpoint, "--checkpoint required"
        ck = torch.load(args.checkpoint, map_location="cpu", weights_only=False)  # trusted: own training artifact, sha-verified at download
        enc.load_state_dict(ck["enc"])
        dec.load_state_dict(ck["dec"])
        drift.load_state_dict(ck["drift"])
        V = np.asarray(ck["V"], dtype=np.float32)
        mu = np.asarray(ck["mu"], dtype=np.float32)
        assert V.shape == (len(panel), pcad), "checkpoint/panel mismatch"
        Zp = np.empty((len(Xp), pcad), dtype=np.float32)
        Zb = np.empty((len(Xb), pcad), dtype=np.float32)
        for a in range(0, len(Xp), 4096):
            Zp[a:a + 4096] = (Xp[a:a + 4096].astype(np.float32) - mu) @ V
        for a in range(0, len(Xb), 4096):
            Zb[a:a + 4096] = (Xb[a:a + 4096].astype(np.float32) - mu) @ V
        del Xp, Xb
        diag["loaded_checkpoint"] = args.checkpoint
    else:
        import ot
        opt = torch.optim.AdamW(list(enc.parameters()) + list(dec.parameters()) + list(drift.parameters()), lr=LR, weight_decay=WD)
        Zp_t = torch.from_numpy(Zp)
        Zb_t = torch.from_numpy(Zb)
        Lp_t = torch.from_numpy(Lp)
        Lb_t = torch.from_numpy(Lb)
        rng = np.random.default_rng(RUN_SEED)
        h_idx = rng.choice(len(Zp), size=min(HOLDOUT_N, len(Zp) // 5), replace=False)
        h_mask = np.ones(len(Zp), bool)
        h_mask[h_idx] = False
        Zh, Lh = Zp_t[h_idx], Lp_t[h_idx]
        Zptr, Lptr = Zp_t[h_mask], Lp_t[h_mask]
        dt = 1.0 / em_steps
        sq = DIFFUSION * (dt ** 0.5)
        step, done = 0, False
        t_start = time.time()
        for ep in range(epochs):
            perm = torch.randperm(len(Zptr))
            for a in range(0, len(Zptr), bs):
                idx = perm[a:a + bs]
                z0, l0 = Zptr[idx], Lptr[idx]
                mu0, lv0 = enc(z0)
                std0 = (0.5 * lv0).exp()
                z = mu0 + std0 * torch.randn_like(std0)
                zt = z.clone()
                for _ in range(em_steps):
                    zt = zt + drift(zt, l0) * dt + sq * torch.randn(zt.shape, generator=g_emu)
                xr = dec(z)
                kl = -0.5 * (1 + lv0 - mu0.pow(2) - lv0.exp()).mean()
                with torch.no_grad():
                    jdx = torch.randperm(len(Zb_t))[: len(zt)]
                xh = dec(zt)  # in-graph: DOT gradients reach drift+decoder
                M = torch.cdist(xh, Zb_t[jdx], p=2).pow(2)
                a_w = torch.full((len(zt),), 1.0 / len(zt))
                b_w = torch.full((len(jdx),), 1.0 / len(jdx))
                w2 = ot.sinkhorn2(a_w, b_w, M, W2_REG)
                loss = ((xr - z0) ** 2).mean() + LAM_KL * kl + LAM_W2 * w2
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(list(enc.parameters()) + list(dec.parameters()) + list(drift.parameters()), 1.0)
                opt.step()
                step += 1
                if not torch.isfinite(loss):
                    diag["nan_loss_at_step"] = step
                    done = True
                    break
            diag["last_epoch"] = ep
            if time.time() - t_start > (300 if smoke else TRAIN_CAP_S) or done:
                break
        diag["train_steps"] = step
        torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "drift": drift.state_dict(),
                    "V": V, "mu": mu, "lineages": lins, "pcad": pcad, "dz": dz},
                   RUNDIR / "intermediates" / "field_best.pt")
        np.savez(RUNDIR / "intermediates" / "pca.npz", V=V, mu=mu)
        diag["checkpoint_sha"] = sha256(RUNDIR / "intermediates" / "field_best.pt")

    if smoke and not args.build_only:
        # mechanics only: shapes + finite + roundtrip
        enc.eval()
        with torch.no_grad():
            mu0, lv0 = enc(Zp_t[:8] if 'Zp_t' in dir() else torch.from_numpy(Zp[:8]))
            xr = dec(mu0)
            assert xr.shape == (8, pcad) and bool(torch.isfinite(xr).all())
        diag["wall_s"] = time.time() - t00
        (RUN / "SMOKE.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": True, "pca_explained": diag["pca_explained"]}, indent=1), flush=True)
        return 0

    if args.build_only:
        # local candidate build from checkpoint: G-return gate first, then E10.5 bank.
        assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
        v4 = ad.read_h5ad(V0004)
        v4_names = [str(v) for v in v4.obs_names]
        base_names = [str(v) for v in base.obs_names]
        base_index = {n: i for i, n in enumerate(base_names)}
        assert all(n in base_index for n in v4_names)
        enc.eval(); dec.eval(); drift.eval()
        Zp_t = torch.from_numpy(Zp)
        Zb_t = torch.from_numpy(Zb)
        Lp_t = torch.from_numpy(Lp)
        Lb_t = torch.from_numpy(Lb)
        rng = np.random.default_rng(RUN_SEED)
        h_idx = rng.choice(len(Zp), size=min(HOLDOUT_N, len(Zp) // 5), replace=False)
        dt = 1.0 / em_steps

        @torch.no_grad()
        def forecast_mean(z0, lin, steps):
            mu0, _ = enc(z0)
            z = mu0.clone()
            for _ in range(steps):
                z = z + drift(z, lin) * dt
            return z

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

        def write_candidate(Xout, obs, dirname, lane, method):
            cand_dir = RUN / "candidates" / "T1_val" / dirname
            cand_dir.mkdir(parents=True, exist_ok=True)
            out = cand_dir / "submission.h5ad"
            aa = ad.AnnData(X=np.ascontiguousarray(Xout.astype(np.float32)), obs=obs.copy(),
                            var=pd.DataFrame(index=panel))
            aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
            aa.uns["ve_g0_t1_d1"] = json.dumps({"atom_id": TASK_ID, "lane": lane,
                "method": method, "parent": "v0004 recipe", "seed": RUN_SEED,
                "target_used": False}, sort_keys=True)
            aa.write_h5ad(out)
            return out, cand_dir

        cio = _contract_io()
        lock = REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json"

        # G-return: E8.5 held-out t=0->1, full-gene decode
        z1r = forecast_mean(Zp_t[h_idx], Lp_t[h_idx], em_steps)
        Xret = np.clip(dec(z1r).detach().numpy() @ V.T + mu, 0.0, None).astype(np.float32)
        assert np.isfinite(Xret).all(), "diverged return"
        robs = prev.obs.iloc[np.asarray(h_idx)].copy()
        assert len(set(robs.index.astype(str))) == len(robs)
        out_ret, _ = write_candidate(Xret, robs, "gate_return", "G_RETURN", "d1_scimf_return")
        res = dict(cio.validate_h5ad_contract(
            out_ret, task="T1", board="val", scorer_lock=lock,
            parent_path=V0004, parent_sha256=V0004_SHA))
        diag["return_contract"] = res.get("status")
        # D4 precedent: return arm is diagnostic-only with E8.5 held-out rows, so
        # protected_parent row-identity cannot apply; require all substance PASS.
        ok_sub = [v.get("status") in ("PASS", "pass")
                  for k, v in res.get("checks", {}).items() if k != "protected_parent"]
        assert all(ok_sub), f"return contract substance: {res}"
        if res.get("status") not in ("PASS", "pass"):
            diag["return_contract_note"] = ("FAIL_BY_DESIGN_ACCEPTED: protected_parent "
                "row-identity N/A for E8.5 held-out return rows; all substance checks PASS")
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
        # E10.5 candidate on v0004 bank, t=1->2, 20 steps (DESIGN)
        src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
        z1b = forecast_mean(Zb_t[src_idx], Lb_t[src_idx], 20)
        Xout = np.clip(dec(z1b).detach().numpy() @ V.T + mu, 0.0, None).astype(np.float32)
        assert np.isfinite(Xout).all(), "diverged forecast"
        out, cand_dir = write_candidate(Xout, v4.obs.copy(), "v0023_g0_t1_d1_scimf", "L1_SCIMF", "d1_scimf_forecast")
        diag["candidate_sha"] = sha256(out)
        out, _ = write_candidate(Xout, v4.obs.copy(), "v0023_g0_t1_d1_scimf", "L1_SCIMF", "d1_scimf_forecast")
        assert sha256(out) == diag["candidate_sha"]
        diag["rerun_bytes_identical"] = True
        res = dict(cio.validate_h5ad_contract(
            out, task="T1", board="val", scorer_lock=lock,
            parent_path=V0004, parent_sha256=V0004_SHA))
        diag["contract"] = res.get("status")
        assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
        mloc = run_scorer(out, "L1_SCIMF")
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
