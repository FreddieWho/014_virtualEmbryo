#!/usr/bin/env python3
"""G1-T3-R6 CIPHER-style linear response: CellOracle cascade + lineage gate + t-shrink.

D2 OPT-B (reports/G1_T3_30ROUND_RESEARCH.md §3): CIPHER 2025 Δx=Σu, three changes:
(a) response applied full-strength only on cardiac-lineage cm states, 0.5x agnostic
    fallback on Peri/BW/Unknown (same upfront rule as R3/R4, recorded);
(b) u vector = CellOracle S1A-v7 REAL simulated Gata4 cascade (state-aggregated mean
    effect over 76 sim states; NO per-state namespace mapping — R4 recorded that lane
    BLOCKED on 76-vs-13 namespace mismatch, this design sidesteps it by aggregating);
(c) T1-R4 t-shrink w=|t|/(|t|+2) where t = mean_effect/(sd/sqrt(n_states)) per gene
    (reliability weight: consistent cascade direction across states survives, noisy dies).
Amplitude bridge (recorded, not tuned): shift_g = sign(mean_g) * min(0.15*rsd_g, cap_g)
    * rel_g * w_g, rel_g = |mean_g|/max|mean| (CellOracle raw effects are ~1e-4 scale,
    unusable raw; relative strength preserves ranking). Sign convention: CellOracle
    effect IS the KO direction (unlike R1 Pearson where shift=-sign(corr)).
Gata4 -> 0 (v0009 recipe). Frozen: v0009 obs_names/order, coords, panel, seeds.
Validation gate Step 0: identity reproduce v0009 (WT pull + Gata4 zero == v0009 bytes
for non-Gata4 cols) before any shift. Local proxy = DISASTER CHECK ONLY (R1 lesson).
Caps: single process, deterministic. No target KO data, no training.
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

TASK_ID = "G1-T3-R6-CIPHER"
BOARD = "T3:gata4"
RUN_SEED = 20260916
AMPL = 0.15
CAP_FRAC = 0.10
SHRINK_C = 2.0
PANEL = REPO / "data" / "gene_panel" / "T3__gata4.genes.txt"
E875 = REPO / "data" / "E8.75.h5ad"
E95WT = REPO / "data" / "E9.5_RNA.h5ad"
V0009 = REPO / "submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad"
V0009_SHA = "c6be65ec7d8c8a4b94bce936ff0cad985ac26f78c77ea3e4f68643f07076b088"
CELLO = (REPO / "artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/celloracle"
         / "Gata4_state_response.tsv")
N_CELLS = 7449
CARDIAC = {"vCM1", "vCM2", "aCM1", "aCM2", "aSHF", "pSHF", "OFT/RV-CM",
           "JCF/SV-CM", "FHF/JCF", "aPHM", "pPHM"}


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


def cipher_table(panel: list) -> pd.DataFrame:
    """Per-gene KO shift from CellOracle cascade + WT dispersion + t-shrink.

    Pure function of frozen inputs (deterministic)."""
    resp = pd.read_csv(CELLO, sep="\t", usecols=["response_gene", "effect"])
    assert len(resp) == 37924, f"cello row drift: {len(resp)}"
    stat = resp.groupby("response_gene")["effect"].agg(["mean", "std", "count"])
    maxabs = float(stat["mean"].abs().max())
    assert maxabs > 0
    # WT dispersion from E9.5 (B2-audited formula, same as R1-R4).
    w = ad.read_h5ad(E95WT, backed="r")
    var = [str(v) for v in w.var_names]
    need = [g for g in panel if g != "Gata4"]
    ci = [var.index(c) for c in need]
    X = w.X[:, ci]
    if sparse.issparse(X):
        X = X.toarray()
    X = np.asarray(X, dtype=np.float64)
    w.file.close()
    rows = []
    for j, gene in enumerate(need):
        st = stat.loc[gene] if gene in stat.index else None
        mean = float(st["mean"]) if st is not None else 0.0
        sd = float(st["std"]) if st is not None else 0.0
        n = int(st["count"]) if st is not None else 0
        if mean == 0.0 or n == 0:
            t = 0.0
        elif sd == 0.0:
            t = float("inf")
        else:
            t = mean / (sd / np.sqrt(n))
        shr = 1.0 if np.isinf(t) else abs(t) / (abs(t) + SHRINK_C)
        rel = abs(mean) / maxabs
        x = X[:, j]
        q1, q99 = np.quantile(x, [0.01, 0.99])
        rsd = float((np.quantile(x, 0.75) - np.quantile(x, 0.25)) / 1.349)
        amp = min(AMPL * rsd, CAP_FRAC * float(q99 - q1))
        shift = float(np.sign(mean)) * amp * rel * shr if mean != 0 else 0.0
        rows.append({"gene": gene, "cello_mean": mean, "cello_sd": sd,
                     "t": float(t) if np.isfinite(t) else 999.0,
                     "shrink_w": float(shr), "rel": float(rel),
                     "amplitude": float(amp), "shift": shift})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0018_g0_t3_r6_cipher")
    args = ap.parse_args()

    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T3_gata4").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED,
                  "rule": "cello-cascade u + cardiac-full/else-half + t-shrink C=2"}
    t00 = time.time()

    assert sha256(V0009) == V0009_SHA, "BLOCKED_INPUT: v0009 hash drift"
    diag["v0009_sha_ok"] = True
    assert CELLO.exists(), "BLOCKED_INPUT: cello product missing"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    gidx = {g: i for i, g in enumerate(panel)}
    assert len(panel) == 500 and "Gata4" in gidx

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
    # Step-0 gate: identity reproduce v0009 (WT pull + Gata4 zero == v0009).
    Xv = v9.X
    if sparse.issparse(Xv):
        Xv = Xv.toarray()
    Xv = np.asarray(Xv, dtype=np.float32)
    gi = gidx["Gata4"]
    others = [i for i in range(len(panel)) if i != gi]
    assert np.array_equal(Xout[:, others], Xv[:, others]), "non-Gata4 rows differ from v0009"
    assert (Xv[:, gi] == 0).all(), "v0009 Gata4 not all zero"
    diag["identity_repro_v0009"] = True

    cm = np.asarray(v9.obs["cm_celltype"].astype(str))
    assert set(np.unique(cm)) == {"Unknown", "pPHM", "vCM1", "aCM1", "aSHF", "vCM2",
                                  "OFT/RV-CM", "Peri/BW", "aPHM", "aCM2", "pSHF",
                                  "JCF/SV-CM", "FHF/JCF"}, "cm namespace drift"
    cardiac = np.isin(cm, list(CARDIAC))
    diag["cardiac_n"] = int(cardiac.sum())
    diag["fallback_n"] = int((~cardiac).sum())
    diag["cardiac_frac"] = float(cardiac.mean())

    tab = cipher_table(panel)
    tab2 = cipher_table(panel)
    pd.testing.assert_frame_equal(tab, tab2)
    diag["rerun_table_identical"] = True
    nz = tab[tab["shift"].abs() > 0]
    diag["n_shifted"] = int(len(nz))
    diag["top5"] = nz.reindex(nz["shift"].abs().sort_values(ascending=False).index)[
        ["gene", "shift", "shrink_w", "rel"]].head(5).to_dict("records")
    tab.to_csv(RUN / "intermediates" / "cipher_table.tsv", sep="\t", index=False)

    Xout[:, gi] = 0.0
    for _, r in tab.iterrows():
        s = float(r["shift"])
        if s == 0.0:
            continue
        j = gidx[r["gene"]]
        Xout[cardiac, j] = Xout[cardiac, j] + s
        Xout[~cardiac, j] = Xout[~cardiac, j] + 0.5 * s
    Xout = np.clip(Xout, 0.0, None)

    cand_dir = RUN / "candidates" / "T3_gata4" / args.out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=Xout, obs=v9.obs.copy(), var=pd.DataFrame(index=panel))
    a.obsm["spatial_3D"] = np.asarray(v9.obsm["spatial_3D"])
    for k in list(v9.layers.keys()):
        a.layers[k] = v9.layers[k].copy()
    if v9.raw is not None:
        a.raw = v9.raw.to_adata()
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log_normalized"}
    a.uns["ve_g0_t3_r6"] = json.dumps({"atom_id": TASK_ID, "lane": "L_A_CIPHER",
        "method": "cello_cascade_lineage_cipher_tshrink2", "parent": "v0009 rows",
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
    if hasattr(v9, "file"):
        v9.file.close()
    if hasattr(src, "file"):
        src.file.close()

    import subprocess
    mout = RUN / "metrics" / "scorer_L_A_CIPHER.json"
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
    (RUN / "metrics" / "scorer_L_A_CIPHER_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["no_regression"] = bool(keep["de_score"] >= 0.1700 and keep["de_direction"] >= 0.2400
                                 and (keep.get("severity_slope") or -9) >= -0.60)
    diag["beats_baseline"] = bool(keep["de_score"] > 0.1739 and keep["de_direction"] > 0.2444
                                  and (keep.get("severity_slope") or -9) > 0)
    diag["slope_improved"] = bool((keep.get("severity_slope") or -9) > -0.5368)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"identity_repro": True, "n_shifted": diag["n_shifted"],
                      "cardiac_frac": round(diag["cardiac_frac"], 4),
                      "beats_baseline": diag["beats_baseline"],
                      "slope_improved": diag["slope_improved"], "local": keep}, indent=1),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
