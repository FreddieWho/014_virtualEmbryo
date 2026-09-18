#!/usr/bin/env python3
"""G1-T3-R1 direct-target propagation: zeroing + conservative downstream shift.

B4 lesson: v0009 genotype zeroing +0.15 (only 1/500 genes move); delay lanes move nothing
in DE amplitude (de_score 38-39 weakest). This lane moves DE amplitude via HIGH-CONFIDENCE
direct Gata4 targets only: 17 panel genes with CellOracle motif score 1.0 (fixed set, no
tuning). Sign from E9.5 WT co-expression Pearson(Gata4, target) [fixed rule, recorded];
amplitude 0.15 * robust_SD_WT(gene), cap 10% WT range (B2-audited formula, global not
state-specific: same small-n lesson as T1-R2). shift = -sign(corr) * amplitude (KO removes
activation -> positive targets go DOWN). Gata4 -> 0 (v0009 recipe).
Frozen: v0009 obs_names/order (7449), coords, panel, seeds. No target KO data, no training.
Caps: single process, deterministic.
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

TASK_ID = "G1-T3-R1-DIRECTPROP"
BOARD = "T3:gata4"
RUN_SEED = 20260916
AMPL = 0.15
CAP_FRAC = 0.10
PANEL = REPO / "data" / "gene_panel" / "T3__gata4.genes.txt"
E875 = REPO / "data" / "E8.75.h5ad"
E95WT = REPO / "data" / "E9.5_RNA.h5ad"
V0009 = REPO / "submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad"
V0009_SHA = "c6be65ec7d8c8a4b94bce936ff0cad985ac26f78c77ea3e4f68643f07076b088"
GRN = REPO / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN/mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet"
N_CELLS = 7449


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


def target_table(panel: list) -> pd.DataFrame:
    """Fixed 17-gene direct-target set + WT stats. Pure function (deterministic)."""
    df = pd.read_parquet(GRN, columns=["gene_short_name", "Gata4"])
    sub = df[df["gene_short_name"].isin(panel)].copy().drop_duplicates("gene_short_name")
    tg = sub[sub["Gata4"] > 0]["gene_short_name"].tolist()
    tg = [g for g in tg if g != "Gata4"]
    # WT stats from E9.5 (need columns Gata4 + targets).
    cols = ["Gata4"] + tg
    w = ad.read_h5ad(E95WT, backed="r")
    var = [str(v) for v in w.var_names]
    ci = [var.index(c) for c in cols]
    X = w.X[:, ci]
    if sparse.issparse(X):
        X = X.toarray()
    X = np.asarray(X, dtype=np.float64)
    w.file.close()
    g = X[:, 0]
    rows = []
    for j, gene in enumerate(tg):
        x = X[:, 1 + j]
        r = float(np.corrcoef(g, x)[0, 1]) if np.std(g) > 0 and np.std(x) > 0 else 0.0
        q1, q99 = np.quantile(x, [0.01, 0.99])
        rsd = float((np.quantile(x, 0.75) - np.quantile(x, 0.25)) / 1.349)
        amp = AMPL * rsd
        cap = CAP_FRAC * float(q99 - q1)
        rows.append({"gene": gene, "motif": 1.0, "pearson_wt": r,
                     "sign": int(np.sign(r)) if r != 0 else 0,
                     "amplitude": float(min(amp, cap))})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0013_g0_t3_r1_directprop")
    args = ap.parse_args()

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T3_gata4").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED,
                  "rule": f"17 motif targets, sign=pearson, amp={AMPL}*rsd cap{CAP_FRAC}"}
    t00 = time.time()

    assert sha256(V0009) == V0009_SHA, "BLOCKED_INPUT: v0009 hash drift"
    diag["v0009_sha_ok"] = True
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    gidx = {g: i for i, g in enumerate(panel)}
    assert len(panel) == 500 and "Gata4" in gidx

    tab = target_table(panel)
    tab.to_csv(RUN / "intermediates" / "target_table.tsv", sep="\t", index=False)
    diag["n_targets"] = int(len(tab))
    tab2 = target_table(panel)
    pd.testing.assert_frame_equal(tab, tab2)
    diag["rerun_table_identical"] = True

    v9 = ad.read_h5ad(V0009)
    v9_names = [str(v) for v in v9.obs_names]
    assert len(v9_names) == N_CELLS and len(set(v9_names)) == N_CELLS
    src = ad.read_h5ad(E875)
    s_names = [str(v) for v in src.obs_names]
    s_index = {n: i for i, n in enumerate(s_names)}
    assert all(n in s_index for n in v9_names), "v0009 rows must come from E8.75"
    s_idx = np.array([s_index[n] for n in v9_names], dtype=np.int64)
    Xs = src.X[s_idx]
    if sparse.issparse(Xs):
        Xs = Xs.toarray()
    Xout = np.asarray(Xs, dtype=np.float32)
    # Row order check: our pull must equal v0009 expression except Gata4 col (zeroed there).
    Xv = v9.X
    if sparse.issparse(Xv):
        Xv = Xv.toarray()
    Xv = np.asarray(Xv, dtype=np.float32)
    gi = gidx["Gata4"]
    others = [i for i in range(len(panel)) if i != gi]
    assert np.array_equal(Xout[:, others], Xv[:, others]), "non-Gata4 rows differ from v0009"
    assert (Xv[:, gi] == 0).all(), "v0009 Gata4 not all zero"
    diag["rows_match_v0009_except_gata4"] = True

    Xout[:, gi] = 0.0
    for _, r in tab.iterrows():
        j = gidx[r["gene"]]
        s = int(r["sign"])
        if s == 0:
            continue
        Xout[:, j] = Xout[:, j] - s * float(r["amplitude"])
    Xout = np.clip(Xout, 0.0, None)

    cand_dir = RUN / "candidates" / "T3_gata4" / args.out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=Xout, obs=v9.obs.copy(), var=pd.DataFrame(index=panel))
    a.obsm["spatial_3D"] = np.asarray(v9.obsm["spatial_3D"])
    # T3 contract: layers + raw must match the locked parent verbatim.
    for k in list(v9.layers.keys()):
        a.layers[k] = v9.layers[k].copy()
    if v9.raw is not None:
        a.raw = v9.raw.to_adata()
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log_normalized"}
    a.uns["ve_g0_t3_r1"] = json.dumps({"atom_id": TASK_ID, "lane": "L_A_DIRECTPROP",
        "method": "zeroing_plus_17motif_target_shift", "parent": "v0009 recipe",
        "seed": RUN_SEED, "target_used": False}, sort_keys=True)
    a.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)

    cio = _contract_io()
    res = dict(cio.validate_h5ad_contract(
        out, task="T3", board="gata4",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0009, parent_sha256=V0009_SHA))
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
    diag["contract"] = res.get("status")
    diag["candidate_sha_final"] = sha256(out)
    v9.file.close() if hasattr(v9, "file") else None
    src.file.close() if hasattr(src, "file") else None

    import subprocess
    mout = RUN / "metrics" / "scorer_L_A_DIRECTPROP.json"
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T3",
           "--input", str(out), "--target", "data/E9.5_mab21l2_ko.h5ad",
           "--wt", "data/E9.5.h5ad", "--seed", str(RUN_SEED), "--out", str(mout)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-1500:])
    m = json.loads(mout.read_text())["metrics"]
    keep = {k: m.get(k) for k in ("de_score", "de_direction", "severity_slope", "mmd_u",
                                  "variogram", "energy_distance", "pb_rel_err",
                                  "library_size_ratio", "variance_ratio")}
    (RUN / "metrics" / "scorer_L_A_DIRECTPROP_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["beats_baseline"] = bool(keep["de_score"] > 0.1739 and keep["de_direction"] > 0.2444
                                  and (keep.get("severity_slope") or -9) > 0)
    diag["slope_improved"] = bool((keep.get("severity_slope") or -9) > -0.5368)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"beats_baseline": diag["beats_baseline"],
                      "slope_improved": diag["slope_improved"], "local": keep}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
