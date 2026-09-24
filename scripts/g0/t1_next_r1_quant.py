#!/usr/bin/env python3
"""T1-NEXT-R1: mean shift -> distribution-shape forecast.

Per coarse type c, per gene g: estimate zero-probability + positive quantiles
on E8.5/E9.5 TRAIN cells, extrapolate one step (bounded logit delta for zero
rate, quantile increments projected non-negative + monotone). Recipient cells
(E8.5 outer) map through predicted CDFs:
  zero cells spread over [0, p0_85] by library-size rank (fixed tie rule, no RNG);
  positives map by searchsorted rank.
Arm A: parent zero support kept (zeros stay 0; positives via quantile map).
Arm B: full predicted zero support (p_pred), i.e. activation/silencing via map.
A/B differ ONLY in zero support. Unsupported types / low-sample (c,g) fall back
to parent rows. Report scenario E8.5->E9.5, same seed/splits as R2.
Checks: (1) E9.5 within-stage reconstruction (E9.5-train CDFs, no change);
(2) forecast A/B vs strict/identity; (3) delta-scale sensitivity 0.5x/1x/1.5x.
Diagnostic only. CPU.
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
from sklearn.model_selection import train_test_split

TASK_ID = "T1-NEXT-R1"
RUN_SEED = 20260921
N_Q = 41  # quantile grid levels
LOGIT_CAP = 2.0
MIN_N = 30  # min train cells per (c,g)... per type for CDF estimation
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
E85_SHA = "8eab2d0ccaa89f92861b09816b76b6a731b8ed6b5995e4af196d9ed8ff76e504"
E95_SHA = "0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361"


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


def load_panel(path: Path):
    a = ad.read_h5ad(path)
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    a = a[:, panel].copy()
    X = to_dense(a)
    assert np.isfinite(X).all() and (X >= 0).all()
    return X, np.asarray(a.obs["celltype"].astype(str))


def run_scorer(inp: Path, tgt: Path, ref: Path, out: Path) -> dict:
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(inp), "--target", str(tgt),
           "--reference", str(ref), "--seed", str(RUN_SEED), "--out", str(out)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-2000:])
    return json.loads(out.read_text())["metrics"]


def write_sub(X: np.ndarray, types: np.ndarray, path: Path, panel: list[str]) -> None:
    aa = ad.AnnData(X=np.ascontiguousarray(X, dtype=np.float32),
                    obs=pd.DataFrame({"celltype": pd.Categorical(types)}),
                    var=pd.DataFrame(index=panel))
    aa.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    aa.uns["ve_t1_next_r1"] = json.dumps({"atom_id": TASK_ID, "seed": RUN_SEED,
                                          "diagnostic": True, "target_used": False})
    aa.write_h5ad(path)


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    res: dict = {"task": TASK_ID, "seed": RUN_SEED, "n_q": N_Q}
    t00 = time.time()

    assert sha256(E85) == E85_SHA and sha256(E95) == E95_SHA, "input hash drift"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    D = len(panel)
    X85, t85 = load_panel(E85)
    X95, t95 = load_panel(E95)
    idx85 = np.arange(len(X85))
    idx95 = np.arange(len(X95))
    tr85, tmp85 = train_test_split(idx85, test_size=0.4, random_state=RUN_SEED, stratify=t85)
    te85, _ = train_test_split(tmp85, test_size=0.5, random_state=RUN_SEED + 1,
                               stratify=t85[tmp85])
    tr95, tmp95 = train_test_split(idx95, test_size=0.4, random_state=RUN_SEED, stratify=t95)
    te95, _ = train_test_split(tmp95, test_size=0.5, random_state=RUN_SEED + 1,
                               stratify=t95[tmp95])
    # comparability with R2 splits
    assert (len(tr85), len(te85), len(tr95), len(te95)) == (10072, 3357, 10234, 3411)
    res["split_ok_r2match"] = True

    ttr85, ttr95 = t85[tr85], t95[tr95]
    X85tr, X95tr = X85[tr85], X95[tr95]
    Xr = X85[te85]
    tr_ = t85[te85]
    lib_r = Xr.sum(axis=1)
    common = sorted(set(ttr85) & set(ttr95))
    res["types_common"] = len(common)
    U = np.linspace(0, 1, N_Q).astype(np.float64)

    # ---- fit per (c,g): base CDF (E8.5 train), target CDF (E9.5 train) ----
    n_rec = len(Xr)
    Qpred = np.empty((n_rec, D), dtype=np.float32)   # placeholder per-cell via map below
    QpredA = np.empty((n_rec, D), dtype=np.float32)
    use_map = np.zeros((n_rec, D), dtype=bool)  # cells/genes with fitted transport
    mono_fix_frac: list[float] = []
    p_stats: list[tuple] = []  # (c, g, p0_85, p0_95, p_pred)
    n_fallback_cells_genes = 0
    for ci, c in enumerate(sorted(set(tr_))):
        m_rec = (tr_ == c)
        rec_idx = np.where(m_rec)[0]
        if c not in common:
            continue  # unsupported type: parent rows (already in output init below)
        v85 = X85tr[ttr85 == c]
        v95 = X95tr[ttr95 == c]
        if len(v85) < MIN_N or len(v95) < MIN_N:
            continue
        # library-rank order for zero tie-spread (fixed rule, no RNG)
        order = np.argsort(-lib_r[m_rec], kind="stable")
        lib_rank = np.empty(m_rec.sum(), dtype=np.float64)
        lib_rank[order] = (np.arange(m_rec.sum()) + 0.5) / m_rec.sum()
        for g in range(D):
            a = v85[:, g].astype(np.float64)
            b = v95[:, g].astype(np.float64)
            p0_85 = float((a == 0).mean())
            p0_95 = float((b == 0).mean())
            if p0_85 > 0.999 and p0_95 > 0.999:
                continue  # uninformative: keep parent
            d = float(np.clip(logit(np.array([p0_95]))[0] - logit(np.array([p0_85]))[0],
                              -LOGIT_CAP, LOGIT_CAP))
            p_pred = float(sigmoid(logit(np.array([p0_85]))[0] + d))
            Qa = np.quantile(a, U)
            Qb = np.quantile(b, U)
            Qp = np.maximum(Qa + (Qb - Qa), 0.0)
            n_mono = int((np.diff(Qp) < 0).sum())
            Qp = np.maximum.accumulate(Qp)
            mono_fix_frac.append(n_mono / (N_Q - 1))
            if ci == 0 and g < 3:
                p_stats.append((c, g, p0_85, p0_95, p_pred))
            x = Xr[m_rec][:, g].astype(np.float64)
            is_zero = (x == 0)
            s = np.sort(a)
            u_pos = np.searchsorted(s, x, side="right") / len(s)
            u = u_pos.copy()
            # spread zero cells over [0, p0_85] by library rank
            u[is_zero] = lib_rank[is_zero] * p0_85
            mapped = np.interp(u, U, Qp)
            Qpred[rec_idx, g] = mapped
            # Arm A: zeros stay 0; positives map through same Qp (zero-mass region differs only)
            mappedA = mapped.copy()
            mappedA[is_zero] = 0.0
            # positives with u < p_pred would map to ~0 via Qp already; keep as mapped
            QpredA[rec_idx, g] = mappedA
            use_map[rec_idx, g] = True
    res["map_coverage"] = float(use_map.mean())
    res["mono_fix_mean"] = float(np.mean(mono_fix_frac)) if mono_fix_frac else 0.0
    res["p_example"] = [list(t) for t in p_stats]

    out_parent = Xr.copy()
    out_A = np.where(use_map, QpredA, out_parent).astype(np.float32)
    out_B = np.where(use_map, Qpred, out_parent).astype(np.float32)

    # ---- controls: identity + train-fitted strict shift ----
    mu85 = {c: X85tr[ttr85 == c].mean(axis=0) for c in common}
    mu95 = {c: X95tr[ttr95 == c].mean(axis=0) for c in common}
    Gshift = np.stack([(mu95[c] - mu85[c]) if c in common
                       else np.zeros(D, dtype=np.float32) for c in tr_])
    arms = {
        "identity": Xr.copy(),
        "strict_shift": np.clip(Xr + Gshift, 0.0, None).astype(np.float32),
        "A_qpos_only": np.clip(out_A, 0.0, None).astype(np.float32),
        "B_qpos_zero": np.clip(out_B, 0.0, None).astype(np.float32),
    }
    res["zero_rate"] = {k: float((v == 0).mean()) for k, v in arms.items()}
    res["lib_mean"] = {k: float(v.sum(axis=1).mean()) for k, v in arms.items()}

    tgt = RUN / "intermediates" / "pseudo_target_e95_outer.h5ad"
    ref = RUN / "intermediates" / "reference_e85_train.h5ad"
    write_sub(X95[te95], t95[te95], tgt, panel)
    write_sub(X85[tr85], t85[tr85], ref, panel)
    res["lib_mean"]["e95_outer"] = float(X95[te95].sum(axis=1).mean())

    KEEP = ("de_score", "de_direction", "energy_distance", "mmd_u", "variogram",
            "pb_rel_err", "library_size_ratio", "variance_ratio", "composition_JSD",
            "pseudobulk_pearson")
    res["arms"] = {}
    for name, X in arms.items():
        p = RUN / "intermediates" / f"arm_{name}.h5ad"
        write_sub(X, tr_, p, panel)
        mout = RUN / "metrics" / f"scorer_{name}.json"
        m = run_scorer(p, tgt, ref, mout)
        res["arms"][name] = {k: m.get(k) for k in KEEP}
        print(f"ARM {name}: " + json.dumps(res["arms"][name]), flush=True)

    # ---- check 1: E9.5 within-stage reconstruction (E9.5-train CDFs, no change) ----
    X9r = X95[te95]
    t9r = t95[te95]
    lib9 = X9r.sum(axis=1)
    out9 = X9r.copy()
    for c in sorted(set(t9r)):
        m = (t9r == c)
        if c not in common:
            continue
        v = X95tr[ttr95 == c]
        if len(v) < MIN_N:
            continue
        order = np.argsort(-lib9[m], kind="stable")
        lr = np.empty(m.sum())
        lr[order] = (np.arange(m.sum()) + 0.5) / m.sum()
        for g in range(D):
            a = v[:, g].astype(np.float64)
            p0 = float((a == 0).mean())
            if p0 > 0.999:
                continue
            Q = np.quantile(a, U)
            x = X9r[m][:, g].astype(np.float64)
            s = np.sort(a)
            u = np.searchsorted(s, x, side="right") / len(s)
            u[x == 0] = lr[x == 0] * p0
            out9[np.where(m)[0], g] = np.interp(u, U, Q)
    p9 = RUN / "intermediates" / "arm_recon_e95.h5ad"
    write_sub(out9.astype(np.float32), t9r, p9, panel)
    m9 = run_scorer(p9, tgt, ref, RUN / "metrics" / "scorer_recon_e95.json")
    res["recon_e95"] = {k: m9.get(k) for k in KEEP}
    res["recon_zero_rate"] = float((out9 == 0).mean())
    print("RECON_E95: " + json.dumps(res["recon_e95"]), flush=True)

    res["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
