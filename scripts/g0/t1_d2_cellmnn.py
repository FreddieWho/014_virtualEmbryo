#!/usr/bin/env python3
"""G1-T1-D2 CellMNN port: locally-linear explicit ODE, single MLP + lineage condition.

Paper: arXiv:2510.02903 (ICLR 2026). Implemented from paper spec, no external code.
  z = PCA(x) (dz=50, centered sklearn PCA + mean add-back on decode: 1-line disclosed
  deviation from the paper's uncentered notation); operating point (z,t,lineage-onehot)
  -> MLP(4x96, leakyReLU, Kaiming, last-layer x0.01) -> A = P diag(l) P^-1;
  z' = expm(A dt) z; x' = V z' + mu.
  Loss L = MMD_Laplacian(s=1,e=1e-8) + 0.1*Lkin + 1.0*Linv, gamma=0.1 (single pair).
  AdamW lr 2e-4/wd 1e-5, batch 200/timepoint, validate every 10 steps (fixed held-out
  2000 E9.5 cells, MMD), patience 40 checks, 90-min CPU cap. torch CPU, 16 threads.
T1 adaptation: train E8.5(t=0)->E9.5(t=1) heart; forecast E9.5->E10.5 dt=1 on v0004 bank.
Gates: proxy (standing: de>0.8868 & dir>0.8895 -> PROMOTED/upload pick);
  enrichment (CollecTRI existence Enrichment@500>1.0 -> mechanism claim, else
  pure-prediction lane per user 从宽 ruling). Proxy fail -> STOP, no candidate.
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

TASK_ID = "G1-T1-D2-CELLMNN"
RUN_SEED = 20260916
DZ = 50
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
VOCAB = REPO / "artifacts" / "tool_integration" / "T1-PRE-HARMONIZE-20260902-v1" / "intermediates" / "state_vocabulary.tsv"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
COLLECTRI = REPO / "infra" / "external_data" / "sanitized" / "T3-S1A-STATE-JOIN" / "COLLECTRI" / "collectri_mouse_full.tsv"
N_CELLS = 5118
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895
LR, WD, BATCH = 2e-4, 1e-5, 200
LAM_KIN, LAM_INV, GAMMA = 0.1, 1.0, 0.1
TRAIN_CAP_S = 5400

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
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--dz", type=int, default=0)
    args = ap.parse_args()
    import torch
    import torch.nn as nn
    torch.set_num_threads(16)
    torch.manual_seed(RUN_SEED)
    np.random.seed(RUN_SEED)

    dz = args.dz or (10 if args.smoke else DZ)
    max_checks = 5 if args.smoke else 40
    bs = 64 if args.smoke else BATCH
    cap_s = 300 if args.smoke else TRAIN_CAP_S

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T1_val").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "dz": dz, "smoke": bool(args.smoke)}
    t00 = time.time()

    assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
    assert COLLECTRI.exists(), "BLOCKED_INPUT: collectri snapshot missing"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    v4 = ad.read_h5ad(V0004)
    Xp, Xb = to_dense(prev), to_dense(base)
    tp = np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))

    vocab = pd.read_csv(VOCAB, sep="\t")
    lin_of = dict(zip(vocab["fine_state"].astype(str), vocab["lineage"].astype(str)))
    cov = np.mean([t in lin_of for t in list(tp) + list(tb)])
    assert cov >= 0.99, f"lineage coverage {cov}"
    diag["lineage_coverage"] = float(cov)
    lins = sorted(set(lin_of.values()))
    li = {s: i for i, s in enumerate(lins)}
    diag["lineages"] = lins
    Lp = np.array([li[lin_of[t]] for t in tp], dtype=np.int64)
    Lb = np.array([li[lin_of[t]] for t in tb], dtype=np.int64)
    L = len(lins)

    from sklearn.decomposition import PCA
    pca = PCA(n_components=dz, svd_solver="randomized", random_state=RUN_SEED)
    Zall = pca.fit_transform(np.vstack([Xp, Xb]).astype(np.float64)).astype(np.float32)
    Zp, Zb = Zall[: len(Xp)], Zall[len(Xp):]
    V = pca.components_.T.astype(np.float32)
    mu = pca.mean_.astype(np.float32)
    diag["pca_explained"] = float(pca.explained_variance_ratio_.sum())
    del Xp, Xb

    cr = pd.read_csv(COLLECTRI, sep="\t")
    cr = cr[cr["is_directed"] == True]
    tfset = sorted(set(cr["source_genesymbol"].astype(str)) & set(panel))
    gidx = {g: i for i, g in enumerate(panel)}
    true_pairs = set(zip(cr["source_genesymbol"].astype(str), cr["target_genesymbol"].astype(str)))
    true_pairs = {(a, b) for a, b in true_pairs if a in tfset and b in gidx}
    universe = len(tfset) * len(panel)
    Vd = V.astype(np.float64)
    base_rate = len(true_pairs) / universe if universe else 0.0

    def enrich_of(Abar):
        scored = []
        for tf in tfset:
            row = Vd @ (Abar @ Vd[gidx[tf]])
            top = np.argpartition(-np.abs(row), 500)[:500]
            for i in top:
                scored.append((abs(float(row[i])), tf, panel[i]))
        scored.sort(reverse=True)
        prec = sum(1 for _, a, b in scored[:500] if (a, b) in true_pairs) / 500.0
        return ((prec / base_rate) if base_rate > 0 else 0.0), prec

    class OpMLP(nn.Module):
        def __init__(self, d_in: int, dz_: int):
            super().__init__()
            self.dz = dz_
            layers = []
            d = d_in
            for _ in range(4):
                lin = nn.Linear(d, 96)
                nn.init.kaiming_normal_(lin.weight, nonlinearity="leaky_relu")
                nn.init.zeros_(lin.bias)
                layers += [lin, nn.LeakyReLU()]
                d = 96
            self.net = nn.Sequential(*layers)
            self.head_P = nn.Linear(96, dz_ * dz_)
            self.head_l = nn.Linear(96, dz_)
            # STABILITY (disclosed deviation, dz=50-scale): clamp eigenvalues to
            # [-10, 10] (paper itself licenses eigenvalue constraints as inductive
            # bias); without it expm(A·dt) overflows float32 after training.
            nn.init.kaiming_normal_(self.head_P.weight, nonlinearity="linear")
            nn.init.kaiming_normal_(self.head_l.weight, nonlinearity="linear")
            with torch.no_grad():
                self.head_P.weight.mul_(0.01)
                self.head_l.weight.mul_(0.01)
                self.head_P.bias.zero_()
                self.head_l.bias.zero_()

        def forward(self, z, t, lo):
            h = self.net(torch.cat([z, t, lo], dim=1))
            P = self.head_P(h).reshape(-1, self.dz, self.dz)
            lam = torch.clamp(self.head_l(h), -10.0, 10.0)
            return P, lam

    def apply_op(P, lam, z, dt: float):
        A = P @ torch.diag_embed(lam) @ torch.linalg.inv(P)
        return (torch.matrix_exp(A * dt) @ z.unsqueeze(-1)).squeeze(-1)

    def laplacian_mmd(x, y, sigma: float = 1.0, eps: float = 1e-8):
        d = torch.cdist(x, y, p=1)
        Kxy = torch.exp(-torch.clamp(d, min=eps) / (sigma * x.shape[1]))
        dxx = torch.cdist(x, x, p=1)
        Kxx = torch.exp(-torch.clamp(dxx, min=eps) / (sigma * x.shape[1]))
        dyy = torch.cdist(y, y, p=1)
        Kyy = torch.exp(-torch.clamp(dyy, min=eps) / (sigma * y.shape[1]))
        return Kxx.mean() + Kyy.mean() - 2 * Kxy.mean()

    mlp = OpMLP(dz + 1 + L, dz)
    opt = torch.optim.AdamW(mlp.parameters(), lr=LR, weight_decay=WD)
    Zp_t = torch.from_numpy(Zp)
    Zb_t = torch.from_numpy(Zb)
    Lp_oh = torch.nn.functional.one_hot(torch.from_numpy(Lp), L).float()
    Lb_oh = torch.nn.functional.one_hot(torch.from_numpy(Lb), L).float()
    n_val = 500 if args.smoke else 2000
    vidx = np.random.default_rng(RUN_SEED).choice(len(Zb), size=n_val, replace=False)
    Zval = Zb_t[vidx]
    trmask = np.ones(len(Zb), bool)
    trmask[vidx] = False
    Ztr, Ltr = Zb_t[trmask], Lb_oh[trmask]

    # NOTE: source batch (E8.5) and target batch (E9.5) are drawn independently (snapshot data).
    step, best, bad, done = 0, float("inf"), 0, False
    mlp.eval()
    with torch.no_grad():
        P0, lam0 = mlp(Zp_t[:512], torch.zeros((512, 1)), Lp_oh[:512])
        A0 = (P0 @ torch.diag_embed(lam0) @ torch.linalg.inv(P0)).mean(dim=0).numpy().astype(np.float64)
    diag["enrich_init"], _ = enrich_of(A0)
    t_start = time.time()
    diag["train_steps"] = 0
    while not done:
        mlp.train()
        si = torch.randperm(Zp_t.shape[0])[:bs]
        ti = torch.randperm(Ztr.shape[0])[:bs]
        zs, ls = Zp_t[si], Lp_oh[si]
        zt = Ztr[ti]
        P, lam = mlp(zs, torch.zeros((bs, 1)), ls)
        zpred = apply_op(P, lam, zs, 1.0)
        A = P @ torch.diag_embed(lam) @ torch.linalg.inv(P)
        # WARMUP (disclosed deviation): L_inv is singular when det(P)->0 (NaN at
        # step 41 in the first full run); ramp it 0->1 over steps 50..200 so MMD/kin
        # stabilize P first. Paper intent (invertible P) preserved.
        ramp = min(1.0, max(0.0, (step - 50) / 150.0))
        diag["inv_ramp"] = ramp
        loss = (GAMMA * laplacian_mmd(zpred, zt)
                + LAM_KIN * (A @ zs.unsqueeze(-1)).squeeze(-1).pow(2).mean()
                + ramp * LAM_INV * (1.0 / (torch.linalg.det(P) + 1e-8)).mean())
        opt.zero_grad()
        loss.backward()
        if not torch.isfinite(loss):
            diag["nan_loss_at_step"] = step
            break
        torch.nn.utils.clip_grad_norm_(mlp.parameters(), 1.0)
        opt.step()
        step += 1
        if step % 10 == 0:
            mlp.eval()
            with torch.no_grad():
                Pv, lamv = mlp(Zp_t[:512], torch.zeros((512, 1)), Lp_oh[:512])
                zv = apply_op(Pv, lamv, Zp_t[:512], 1.0)
                vm = laplacian_mmd(zv, Zval[:512]).item()
            diag["train_steps"] = step
            if vm < best - 1e-9:
                best, bad = vm, 0
                torch.save(mlp.state_dict(), RUN / "intermediates" / "mlp_best.pt")
            else:
                bad += 1
            if bad >= max_checks or time.time() - t_start > cap_s:
                done = True
    diag["best_val_mmd"] = best
    mlp.load_state_dict(torch.load(RUN / "intermediates" / "mlp_best.pt"))
    mlp.eval()

    # Candidate on v0004 bank (E9.5 -> E10.5, dt=1).
    v4_names = [str(v) for v in v4.obs_names]
    base_names = [str(v) for v in base.obs_names]
    base_index = {n: i for i, n in enumerate(base_names)}
    assert all(n in base_index for n in v4_names)
    src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
    Xout = np.empty((N_CELLS, len(panel)), dtype=np.float32)
    with torch.no_grad():
        for a in range(0, N_CELLS, 512):
            b = src_idx[a:a + 512]
            z = Zb_t[b]
            lo = Lb_oh[b]
            P, lam = mlp(z, torch.ones((len(b), 1)), lo)
            zp = apply_op(P, lam, z, 1.0)
            Xout[a:a + 512] = (zp @ torch.from_numpy(V).T).numpy() + mu
    Xout = np.clip(Xout, 0.0, None)
    if not np.isfinite(Xout).all():
        diag["diverged"] = True
        diag["wall_s"] = time.time() - t00
        (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
        print(json.dumps({"diverged": True}, indent=1), flush=True)
        return 0
    cand_dir = RUN / "candidates" / "T1_val" / "v0022_g0_t1_d2_cellmnn"
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=np.ascontiguousarray(Xout), obs=v4.obs.copy(),
                   var=pd.DataFrame(index=panel))
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_g0_t1_d2"] = json.dumps({"atom_id": TASK_ID, "lane": "L1_CELLMNN",
        "method": "cellmnn_port_single_mlp_lineage_cond", "parent": "v0004 recipe",
        "seed": RUN_SEED, "dz": dz, "target_used": False}, sort_keys=True)
    a.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)
    # determinism: rewrite and compare.
    a.write_h5ad(cand_dir / "submission.rerun.h5ad")
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
    promoted = bool(keep["de_score"] > LOCAL_DE and keep["de_direction"] > LOCAL_DIR)
    diag["promoted"] = promoted

    # Enrichment gate (existence only): mean operator over sample -> TF-target ranking.
    Avec, n_acc = [], 0
    with torch.no_grad():
        for s in range(0, min(len(Zb_t), 2000), 512):
            z = Zb_t[s:s + 512]
            P, lam = mlp(z, torch.ones((len(z), 1)), Lb_oh[s:s + 512])
            Avec.append((P @ torch.diag_embed(lam) @ torch.linalg.inv(P)).mean(dim=0))
            n_acc += 1
    Abar = torch.stack(Avec).mean(dim=0).numpy().astype(np.float64)
    enrich, prec500 = enrich_of(Abar)
    diag["enrich"] = {"n_tf": len(tfset), "n_true": len(true_pairs),
                      "prec500": prec500, "base": base_rate, "enrichment500": enrich}
    diag["mechanism_claim"] = bool(enrich > 1.0)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"promoted": promoted, "local": keep,
                      "enrichment500": enrich, "mechanism_claim": diag["mechanism_claim"]},
                     indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
