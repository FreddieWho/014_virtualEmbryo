#!/usr/bin/env python3
"""G1-T1-D3 OT-CFM panel prototype: minibatch-OT + conditional flow matching.

Vendor loss core: third_party/torchcfm (atong01, 7c65385, MIT),
ExactOptimalTransportConditionalFlowMatcher(sigma=0.0). Own MLP + harness
(seeds/threads fully controlled). OT is training scaffold only; prediction integrates
the learned field (essential difference from killed moscot usage).
Phase-1 (this script): top-500 HVG panel, E8.5(t=0)->E9.5(t=1) field fit (CPU).
Gate G-return (pre-declared): field-integrated E8.5->t=1 return must beat plain
per-type-shift return in the same 500-gene space on BOTH energy distance AND
mean-delta cosine. FAIL -> STOP, no full-gene build.
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
sys.path.insert(0, str(REPO / "third_party" / "torchcfm"))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

TASK_ID = "G1-T1-D3-FLOW"
RUN_SEED = 20260916
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
N_HVG = 500
BATCH = 512
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
N_CELLS = 5118
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895

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


def energy_distance(A: np.ndarray, B: np.ndarray, seed: int, n: int = 2000) -> float:
    rng = np.random.default_rng(seed)
    ia = rng.choice(len(A), size=min(n, len(A)), replace=False)
    ib = rng.choice(len(B), size=min(n, len(B)), replace=False)
    A, B = A[ia].astype(np.float64), B[ib].astype(np.float64)
    from scipy.spatial.distance import cdist
    dab = cdist(A, B, "euclidean").mean()
    daa = cdist(A, A, "euclidean").mean()
    dbb = cdist(B, B, "euclidean").mean()
    return float(2 * dab - daa - dbb)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    import torch
    import torch.nn as nn
    torch.set_num_threads(16)
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)
    from torchcfm.conditional_flow_matching import ExactOptimalTransportConditionalFlowMatcher

    n_hvg = 0 if args.full else (100 if args.smoke else N_HVG)
    hid = 512 if args.full else (64 if args.smoke else 256)
    steps = 1200 if args.full else (200 if args.smoke else 2000)
    eval_every = 300 if args.full else (100 if args.smoke else 200)
    bs = 256 if args.full else (128 if args.smoke else BATCH)
    n_eval = 800 if args.full else 1500
    cap_s = 10800 if args.full else None

    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "n_hvg": n_hvg,
                  "smoke": bool(args.smoke), "torchcfm_commit": "7c65385"}
    t00 = time.time()

    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    Xp_full, Xb_full = to_dense(prev), to_dense(base)
    tp = np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))

    hvg_name = "hvg_full.txt" if args.full else "hvg500.txt"
    if args.full:
        hvg = list(panel)
    else:
        import scanpy as sc
        both = ad.AnnData(X=np.vstack([Xp_full, Xb_full]),
                          var=pd.DataFrame(index=panel))
        sc.pp.highly_variable_genes(both, n_top_genes=n_hvg, flavor="seurat")  # seurat: no extra deps (v3 needs skmisc; env kept clean)
        hvg = both.var_names[both.var["highly_variable"]].tolist()
        assert len(hvg) == n_hvg
        del both
    (RUN / "intermediates" / hvg_name).write_text("\n".join(hvg))
    diag["hvg_sha"] = sha256(RUN / "intermediates" / hvg_name)
    gi = np.array([panel.index(g) for g in hvg])
    Xp, Xb = Xp_full[:, gi], Xb_full[:, gi]
    del Xp_full, Xb_full
    # Scaler fit on COMBINED train stages (E8.5+E9.5). E8.5-frozen sd blew up 9
    # E8.5-constant dims (sd=1e-8 -> 1e8 amplification, energy ~1.9e4). Floor 1e-3.
    Xcat = np.vstack([Xp, Xb])
    mu, sd = Xcat.mean(axis=0), Xcat.std(axis=0)
    sd = np.maximum(sd, 1e-3).astype(np.float32)
    del Xcat
    Zp = ((Xp - mu) / sd).astype(np.float32)
    Zb = ((Xb - mu) / sd).astype(np.float32)
    diag["scaler"] = "combined_train_zscore_sd_floor_1e-3"
    del Xp, Xb

    class Field(nn.Module):
        def __init__(self, d: int, h: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(d + 1, h), nn.SiLU(),
                nn.Linear(h, h), nn.SiLU(),
                nn.Linear(h, h), nn.SiLU(),
                nn.Linear(h, d))
            for m in self.net:
                if isinstance(m, nn.Linear):
                    nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                    nn.init.zeros_(m.bias)

        def forward(self, x, t):
            if torch.is_tensor(t):
                tt = t.reshape(x.shape[0], 1).to(dtype=x.dtype, device=x.device)
            else:
                tt = torch.full((x.shape[0], 1), float(t), dtype=x.dtype, device=x.device)
            return self.net(torch.cat([x, tt], dim=1))

    D = len(panel) if args.full else n_hvg
    field = Field(D, hid)
    opt = torch.optim.AdamW(field.parameters(), lr=1e-4, weight_decay=1e-5)
    matcher = ExactOptimalTransportConditionalFlowMatcher(sigma=0.0)
    Zp_t = torch.from_numpy(Zp)
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

    # fixed return-eval sample + plain-shift baseline in the same space
    rng = np.random.default_rng(RUN_SEED)
    s_idx = rng.choice(len(Zp), size=min(3000, len(Zp)), replace=False)
    Xs = Zp_t[s_idx]
    m85 = {t: Zp[tp == t].mean(axis=0) for t in sorted(set(tp.tolist()))}
    m95 = {t: Zb[tb == t].mean(axis=0) if (tb == t).sum() else m85.get(t, np.zeros(D, np.float32))
           for t in m85}
    Xshift = np.stack([Zp[i] + (m95[str(tp[i])] - m85[str(tp[i])]) for i in s_idx]).astype(np.float32)
    Zb_eval = Zb[rng.choice(len(Zb), size=min(3000, len(Zb)), replace=False)]

    def return_metrics(Xret: np.ndarray) -> dict:
        d_pred = Xret.mean(axis=0) - Zp[s_idx].mean(axis=0)
        d_true = Zb_eval.mean(axis=0) - Zp[s_idx].mean(axis=0)
        cos = float(d_pred @ d_true / (np.linalg.norm(d_pred) * np.linalg.norm(d_true) + 1e-12))
        return {"energy": energy_distance(Xret, Zb_eval, RUN_SEED),
                "mean_delta_cosine": cos}

    base_m = return_metrics(Xshift)
    diag["baseline_shift"] = base_m
    best, best_state, bad = None, None, 0
    max_bad = 6 if args.full else (3 if args.smoke else 10)
    for step in range(1, steps + 1):
        field.train()
        i0 = torch.randperm(len(Zp_t))[:bs]
        i1 = torch.randperm(len(Zb_t))[:bs]
        t, xt, ut = matcher.sample_location_and_conditional_flow(Zp_t[i0], Zb_t[i1])
        loss = ((field(xt, t) - ut) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(field.parameters(), 1.0)
        opt.step()
        if step % eval_every == 0:
            field.eval()
            with torch.no_grad():
                Xr = integrate(Xs[:n_eval], 0.0, 1.0).numpy()
            m = return_metrics(Xr)
            key = (m["energy"], -m["mean_delta_cosine"])
            if best is None or key < (best["energy"], -best["mean_delta_cosine"]):
                best = m
                best_state = {k: v.cpu().clone() for k, v in field.state_dict().items()}
                bad = 0
            else:
                bad += 1
            if bad >= max_bad:
                break
            if cap_s is not None and time.time() - t00 > cap_s:
                diag["capped"] = True
                break
    diag["train_steps_done"] = step
    field.load_state_dict(best_state)
    torch.save(field.state_dict(), RUN / "intermediates" / "field_best.pt")
    with torch.no_grad():
        Xret = integrate(Xs[:n_eval], 0.0, 1.0).numpy()
    mret = return_metrics(Xret)
    diag["field_return"] = mret
    gate = bool(mret["energy"] < base_m["energy"]
                and mret["mean_delta_cosine"] > base_m["mean_delta_cosine"])
    diag["gate_pass"] = gate
    if args.full and gate:
        assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
        v4 = ad.read_h5ad(V0004)
        v4_names = [str(v) for v in v4.obs_names]
        base_names = [str(v) for v in base.obs_names]
        base_index = {n: i for i, n in enumerate(base_names)}
        assert all(n in base_index for n in v4_names)
        src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
        field.eval()
        Zpred = np.empty((N_CELLS, D), dtype=np.float32)
        with torch.no_grad():
            for a in range(0, N_CELLS, 1024):
                b = src_idx[a:a + 1024]
                Zpred[a:a + 1024] = integrate(Zb_t[b], 1.0, 2.0).numpy()
        Xout = np.clip(Zpred * sd + mu, 0.0, None).astype(np.float32)
        del Zpred
        cand_dir = RUN / "candidates" / "T1_val" / "v0022_g0_t1_d3_otcfm"
        cand_dir.mkdir(parents=True, exist_ok=True)
        out = cand_dir / "submission.h5ad"
        aa = ad.AnnData(X=np.ascontiguousarray(Xout), obs=v4.obs.copy(),
                        var=pd.DataFrame(index=panel))
        aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
        aa.uns["ve_g0_t1_d3"] = json.dumps({"atom_id": TASK_ID, "lane": "L1_OTCFM",
            "method": "otcfm_field_forecast", "parent": "v0004 recipe",
            "seed": RUN_SEED, "target_used": False}, sort_keys=True)
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
        mout = RUN / "metrics" / "scorer_L1.json"
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
        (RUN / "metrics" / "scorer_L1_slim.json").write_text(json.dumps(keep, indent=1))
        diag["local"] = keep
        diag["promoted"] = bool(keep["de_score"] > LOCAL_DE and keep["de_direction"] > LOCAL_DIR)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1, default=float))
    rep = {"gate_pass": gate, "field": mret, "baseline": base_m}
    if args.full and gate:
        rep["promoted"] = diag["promoted"]
        rep["local"] = diag["local"]
    print(json.dumps(rep, indent=1, default=float), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
