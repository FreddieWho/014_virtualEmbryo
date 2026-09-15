#!/usr/bin/env python3
"""B4-T3-R2 developmental-axis repair: delay residual + genotype transform.

Direction from official WT ladder only (E8.25/E8.75/E9.5 heart):
  d1 = (mu875 - mu825)/0.5, d2 = (mu95 - mu875)/0.75  (per-day, log1p space)
Robust: same sign -> smaller abs (or median); opposite sign -> 0;
low-expression/low-n state-gene -> 0; unshared states -> 0 (pre-fixed);
Gata4/Gata6 excluded from temporal program.
Residual: Δdelay = -alpha*d, X' = X_WT + p*Δdelay (p = frozen p_mesp1),
caps: |delta| <= 0.25 * E8.75 state robust SD (1.4826*MAD), clip>=0.
Genotype (same as T3-R1 L3 spec): raw roundtrip (expm1 -> multiply -> log1p):
  Gata4 *= (1-p), Gata6 *= (1-0.5p). Stored space is log1p (marker); disclosed.
No KO truth, no external held-out, no server scores in construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

TASK_ID = "B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR"
V0008 = REPO / "submissions/candidates/T3_gata4/v0008_b4p0_l0_exact_floor/submission.h5ad"
V0008_SHA = "478786034343cc3ed1a604cd494ab2134751f4a1f4696204f9d105e404bdbef3"
GATE_TSV = REPO / "artifacts/atomic_batch2/B2-T3-A1/lineage_gate.tsv"
PANEL = [l.strip() for l in (REPO / "data" / "gene_panel" / "T3__gata4.genes.txt").read_text().splitlines() if l.strip()]
GI = {g: i for i, g in enumerate(PANEL)}
G4, G6 = GI["Gata4"], GI["Gata6"]
LANES = {"L1_DELAY025": 0.25, "L2_DELAY050": 0.50}
MIN_N = 20
MIN_MEAN = 0.05


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dense(X):
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def load_stage(path: str):
    a = ad.read_h5ad(REPO / path, backed="r")
    vn = [str(v) for v in a.var_names]
    pos = np.array([vn.index(g) for g in PANEL])
    X = dense(a.X[:, pos]).astype(np.float64)
    t = np.asarray(a.obs["celltype"].astype(str))
    a.file.close()
    return X, t


def means_mad(X, t):
    m, s = {}, {}
    for c in np.unique(t):
        v = X[t == c]
        m[str(c)] = v.mean(axis=0)
        mad = np.median(np.abs(v - np.median(v, axis=0)), axis=0)
        s[str(c)] = 1.4826 * mad
    return m, s


def verify() -> dict:
    assert sha256(V0008) == V0008_SHA, "BLOCKED_INPUT: v0008 drift"
    out = {"v0008_sha_ok": True, "gate_sha": sha256(GATE_TSV)}
    outs = {}
    for name, path in (("E8.25", "data/E8.25_late.h5ad"), ("E8.75", "data/E8.75.h5ad"),
                       ("E9.5", "data/E9.5.h5ad")):
        X, t = load_stage(path)
        outs[name] = (X, t)
    states = sorted(set(outs["E8.25"][1].tolist()) & set(outs["E8.75"][1].tolist()) & set(outs["E9.5"][1].tolist()))
    out["stages_n"] = {k: int(len(v[1])) for k, v in outs.items()}
    out["three_way_shared_states"] = len(states)
    out["shared_states"] = states
    print(json.dumps({k: v for k, v in out.items() if k != "shared_states"}, indent=1))
    print("shared:", len(states))
    return out


def build_direction():
    X25, t25 = load_stage("data/E8.25_late.h5ad")
    X75, t75 = load_stage("data/E8.75.h5ad")
    X95, t95 = load_stage("data/E9.5.h5ad")
    m25, _ = means_mad(X25, t25)
    m75, s75 = means_mad(X75, t75)
    m95, _ = means_mad(X95, t95)
    states = sorted(set(t25.tolist()) & set(t75.tolist()) & set(t95.tolist()))
    G = len(PANEL)
    D = {}
    rep = {"states": len(states), "agree": 0, "disagree_zeroed": 0, "lowexpr_zeroed": 0}
    for s in states:
        d1 = (m75[s] - m25[s]) / 0.5
        d2 = (m95[s] - m75[s]) / 0.75
        same = (np.sign(d1) == np.sign(d2)) & (d1 != 0) & (d2 != 0)
        mag = np.where(np.abs(d1) < np.abs(d2), d1, d2)
        robust = np.where(same, mag, 0.0)
        rep["agree"] += int(same.sum())
        rep["disagree_zeroed"] += int((~same).sum())
        n75 = int((t75 == s).sum())
        low = (m75[s] < MIN_MEAN) | (n75 < MIN_N)
        robust[low] = 0.0
        rep["lowexpr_zeroed"] += int(low.sum())
        robust[[G4, G6]] = 0.0
        D[s] = robust.astype(np.float64)
    cap = {s: 0.25 * s75[s] for s in states}
    return D, cap, rep, states


def build_lane(run_dir: Path, lane: str, alpha: float) -> dict:
    t0 = time.time()
    out = run_dir / "candidates" / "T3_gata4" / lane / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(str(out))
    D, cap, rep, states = build_direction()
    gate = pd.read_csv(GATE_TSV, sep="\t")
    pmap = {str(r["official_state"]): float(r["p_mesp1_lineage"]) for _, r in gate.iterrows()}
    a = ad.read_h5ad(V0008)
    var = [str(v) for v in a.var_names]
    assert var == PANEL, "panel order drift"
    types = np.asarray(a.obs["celltype"].astype(str))
    X = dense(a.X).astype(np.float64)
    p = np.array([pmap[t] for t in types])
    missing = sorted(set(types.tolist()) - set(pmap))
    assert not missing, f"states without gate: {missing}"
    n_genes = X.shape[1]
    Delta = np.zeros_like(X)
    mod_states = 0
    for s in sorted(set(types.tolist())):
        m = types == s
        if s in D:
            d = np.minimum(np.abs(D[s]), cap[s]) * np.sign(D[s])
            Delta[m] = -alpha * d
            if np.abs(d).sum() > 0:
                mod_states += 1
    X1 = X + p[:, None] * Delta
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)
    # genotype transform via raw roundtrip (stored space is log1p)
    R = np.expm1(np.clip(X1, 0, None))
    R[:, G4] *= (1.0 - p)
    R[:, G6] *= (1.0 - 0.5 * p)
    X2 = np.log1p(np.clip(R, 0, None)).astype(np.float32)
    assert np.isfinite(X2).all() and (X2 >= 0).all()
    coords_before = np.asarray(a.obsm["spatial_3D"])
    a.X = X2
    assert np.array_equal(np.asarray(a.obsm["spatial_3D"]), coords_before)
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_b4_t3_r2"] = json.dumps({
        "atom_id": TASK_ID, "lane": lane, "method": f"developmental_delay_{alpha}",
        "alpha_day_equiv": alpha, "parent": "v0008_exact_floor_provisional",
        "parent_sha256": V0008_SHA, "lineage": "frozen p_mesp1 (B2-T3-A1)",
        "genotype": "raw-roundtrip Gata4*(1-p), Gata6*(1-0.5p)",
        "target_used": False}, sort_keys=True)
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    a.write_h5ad(tmp)
    Path(tmp).replace(out)
    Xp = dense(ad.read_h5ad(V0008).X)
    diag = {"lane": lane, "alpha": alpha, "output": str(out), "sha256": sha256(out),
            "n_obs": 7449, "states_with_direction": mod_states,
            "direction_report": rep, "clip_fraction": clip_frac,
            "lib_ratio_vs_parent": float(X2.sum() / Xp.sum()),
            "var_ratio_vs_parent": float(X2.var() / Xp.var()),
            "frac_rows_modified": float((np.abs(X2 - Xp).sum(axis=1) > 0).mean()),
            "coords_exact": True, "wall_s": time.time() - t0}
    (run_dir / "intermediates").mkdir(exist_ok=True)
    (run_dir / "intermediates" / f"diag_{lane}.json").write_text(json.dumps(diag, indent=1))
    pd.DataFrame([{"state": s, "nonzero_genes": int((D[s] != 0).sum()),
                     "mean_abs_d": float(np.abs(D[s]).mean()),
                     "cap_hits": int((np.abs(D[s]) >= cap[s] - 1e-12).sum())}
                    for s in states]).to_csv(
        run_dir / "intermediates" / "temporal_direction.tsv", sep="\t", index=False)
    pd.DataFrame([{"celltype": t, "p_mesp1": pmap[t]} for t in sorted(set(types.tolist()))]).to_csv(
        run_dir / "intermediates" / "state_mapping.tsv", sep="\t", index=False)
    print(json.dumps({k: v for k, v in diag.items() if k != "direction_report"}, indent=1), flush=True)
    return diag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["verify", "build"])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--lane", default=None)
    args = ap.parse_args(argv)
    if args.command == "verify":
        verify()
    else:
        if args.lane not in ("L1_DELAY025", "L2_DELAY050"):
            raise ValueError("unknown lane")
        build_lane(Path(args.run_dir), args.lane, 0.25 if args.lane == "L1_DELAY025" else 0.50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
