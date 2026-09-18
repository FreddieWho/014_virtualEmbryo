"""Shared helpers for G1-T3 R7-R13 lanes (D8/D5/D4/D3/D6/D1/D7).

Frozen inputs: v0009 rows/order, E8.75 source, 500-gene panel, E9.5 WT stats,
S1A-v7 CellOracle cascade + scTenifoldKnk ranks. No target KO data, no training.
"""
from __future__ import annotations

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

TASK_PREFIX = "G1-T3"
RUN_SEED = 20260917
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
KNK = (REPO / "artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/sctenifold"
       / "Gata4_diffRegulation.tsv")
GRN = REPO / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN/mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet"
N_CELLS = 7449
CARDIAC = {"vCM1", "vCM2", "aCM1", "aCM2", "aSHF", "pSHF", "OFT/RV-CM",
           "JCF/SV-CM", "FHF/JCF", "aPHM", "pPHM"}
CM_EXPECTED = {"Unknown", "pPHM", "vCM1", "aCM1", "aSHF", "vCM2", "OFT/RV-CM",
               "Peri/BW", "aPHM", "aCM2", "pSHF", "JCF/SV-CM", "FHF/JCF"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_panel() -> tuple[list, dict]:
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    assert len(panel) == 500 and "Gata4" in panel
    return panel, {g: i for i, g in enumerate(panel)}


def load_base():
    """Verify v0009, pull WT rows, identity-check. Returns dict of arrays/frames."""
    assert sha256(V0009) == V0009_SHA, "BLOCKED_INPUT: v0009 hash drift"
    panel, gidx = load_panel()
    v9 = ad.read_h5ad(V0009)
    v9_names = [str(v) for v in v9.obs_names]
    assert len(v9_names) == N_CELLS and len(set(v9_names)) == N_CELLS
    src = ad.read_h5ad(E875)
    s_names = [str(v) for v in src.obs_names]
    s_index = {n: i for i, n in enumerate(s_names)}
    assert all(n in s_index for n in v9_names)
    s_idx = np.array([s_index[n] for n in v9_names], dtype=np.int64)
    Xs = src.X[s_idx]
    if sparse.issparse(Xs):
        Xs = Xs.toarray()
    Xout = np.asarray(Xs, dtype=np.float32)
    Xv = v9.X
    if sparse.issparse(Xv):
        Xv = Xv.toarray()
    Xv = np.asarray(Xv, dtype=np.float32)
    gi = gidx["Gata4"]
    others = [i for i in range(len(panel)) if i != gi]
    assert np.array_equal(Xout[:, others], Xv[:, others]), "rows differ from v0009"
    assert (Xv[:, gi] == 0).all(), "v0009 Gata4 not all zero"
    cm = np.asarray(v9.obs["cm_celltype"].astype(str))
    assert set(np.unique(cm)) == CM_EXPECTED, "cm namespace drift"
    return {"panel": panel, "gidx": gidx, "gi": gi, "v9": v9, "src": src,
            "Xout": Xout, "cm": cm, "cardiac": np.isin(cm, list(CARDIAC))}


def wt_dispersion(genes: list) -> dict:
    """B2-audited WT stats: {gene: (rsd, cap)} from E9.5."""
    w = ad.read_h5ad(E95WT, backed="r")
    var = [str(v) for v in w.var_names]
    ci = [var.index(c) for c in genes]
    X = w.X[:, ci]
    if sparse.issparse(X):
        X = X.toarray()
    X = np.asarray(X, dtype=np.float64)
    w.file.close()
    out = {}
    for j, gene in enumerate(genes):
        x = X[:, j]
        q1, q99 = np.quantile(x, [0.01, 0.99])
        rsd = float((np.quantile(x, 0.75) - np.quantile(x, 0.25)) / 1.349)
        out[gene] = (rsd, float(q99 - q1))
    return out


def cello_stat() -> pd.DataFrame:
    """Per-gene cascade stats over 76 sim states. Deterministic."""
    resp = pd.read_csv(CELLO, sep="\t", usecols=["response_gene", "effect", "sign"])
    assert len(resp) == 37924, f"cello row drift: {len(resp)}"
    g = resp.groupby("response_gene")
    stat = g["effect"].agg(["mean", "std", "count"])
    stat["sign_maj"] = g["sign"].agg(lambda s: float(np.sign(s.sum())) if s.sum() != 0 else 0.0)
    stat["agree"] = g["sign"].agg(lambda s: float(s.abs().mean()))
    return stat


def apply_lineage(Xout, gidx, shifts: dict, cardiac, fallback: float = 0.5):
    """shifts: {gene: signed full magnitude}. Cardiac full, rest fallback×."""
    for gene, s in shifts.items():
        if s == 0.0 or gene == "Gata4":
            continue
        j = gidx[gene]
        Xout[cardiac, j] = Xout[cardiac, j] + s
        Xout[~cardiac, j] = Xout[~cardiac, j] + fallback * s
    return Xout


def finalize(Xout, base, out_version: str, run_dir: Path, uns_val: dict,
             lane: str, extra_diag: dict) -> dict:
    """Zero Gata4, clip, write candidate, contract, local disaster-check score."""
    t00 = time.time()
    RUN = run_dir
    (RUN / "candidates" / "T3_gata4").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    panel, gidx, v9 = base["panel"], base["gidx"], base["v9"]
    Xout[:, gidx["Gata4"]] = 0.0
    Xout = np.clip(Xout, 0.0, None)
    cand_dir = RUN / "candidates" / "T3_gata4" / out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    a = ad.AnnData(X=Xout, obs=v9.obs.copy(), var=pd.DataFrame(index=panel))
    a.obsm["spatial_3D"] = np.asarray(v9.obsm["spatial_3D"])
    for k in list(v9.layers.keys()):
        a.layers[k] = v9.layers[k].copy()
    if v9.raw is not None:
        a.raw = v9.raw.to_adata()
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log_normalized"}
    a.uns[f"ve_{uns_val['atom_short']}"] = json.dumps(uns_val, sort_keys=True)
    a.write_h5ad(out)
    diag = {"seed": RUN_SEED, "lane": lane, "candidate_sha": sha256(out)}
    diag.update(extra_diag)
    iface = REPO / "docs" / "batch3" / "interfaces"
    if str(iface) not in sys.path:
        sys.path.insert(0, str(iface))
    from virtual_embryo_tools import contract_io
    res = dict(contract_io.validate_h5ad_contract(
        out, task="T3", board="gata4",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0009, parent_sha256=V0009_SHA))
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"
    diag["contract"] = res.get("status")
    diag["candidate_sha_final"] = sha256(out)
    mout = RUN / "metrics" / f"scorer_{lane}.json"
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
    (RUN / "metrics" / f"scorer_{lane}_slim.json").write_text(json.dumps(keep, indent=1))
    diag["local"] = keep
    diag["no_regression"] = bool(keep["de_score"] >= 0.1700 and keep["de_direction"] >= 0.2400
                                 and (keep.get("severity_slope") or -9) >= -0.60)
    diag["beats_baseline"] = bool(keep["de_score"] > 0.1739 and keep["de_direction"] > 0.2444
                                  and (keep.get("severity_slope") or -9) > 0)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"lane": lane, "sha": diag["candidate_sha_final"][:12],
                      "beats_baseline": diag["beats_baseline"],
                      "no_regression": diag["no_regression"], "local": keep}, indent=1),
          flush=True)
    return diag
