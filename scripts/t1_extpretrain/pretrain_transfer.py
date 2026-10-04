#!/usr/bin/env python3
"""T1 external temporal pretraining, step B: pretrain + transfer + gates.

Lane: T1-EXTPRE-20261003-v1 (DESIGN.md frozen 2026-10-03). Input: step-A cache
(217,553 cells x 27,669 genes, log1p, 8 compliant stages only).
Pre-declared run parameters (frozen pre-run, recorded in RESULT.json, not tuned):
  SEED=20261003; G = intersection(atlas genes, T1 panel) ~25,801, T1-panel order
  PCA_D=512, PCA subsample=40,000 atlas cells (seeded)
  COARSE groups = 6 (cardiac, neural, endoderm, blood_vascular, mesoderm_other,
    extraembryonic); atlas celltype->coarse keyword crosswalk + official
    fine_state->lineage->coarse via T1-PRE-HARMONIZE vocabulary (frozen files)
  Pretrain: Ridge alpha=1.0, input [z(512), pair-onehot(7), group-onehot(6)]
    -> delta z; target = per (pair, group) mean delta (cell's own group/pair)
  Transfer: Ridge alpha=1.0 correction on [z(512), lineage-onehot(10)] ->
    residual vs official E8.5->E9.5 per-lineage mean deltas (train split only)
  Local gates: G-return 2,000 held-out E8.5 cells -> scorer vs E9.5/E8.5,
    standing dual gate de>0.8868 AND dir>0.8895; fail -> STOP, no E10.5
  E10.5: parent = staged v0051 (AR-MIX L3, sha pinned); forecast bank rows in
    G-latent with operator conditioned on last atlas pair (E8.5->E9.0);
    non-G genes inherit v0051 values; clip>=0; 70/30 row mixture (p=0.7 parent,
    SEED); contract + scorer + same dual gate; pass -> INDEX-ready package note
Modes: --smoke (subsampled mechanics, no scorer), full run.
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

TASK_ID = "T1-EXTPRE-20261003-v1"
SEED = 20261003
PCA_D = 512
PCA_N = 40000
ALPHA = 1.0
HOLDOUT_N = 2000
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895
MIX_P = 0.7
PAIR_FOR_FORECAST = ("E8.5", "E9.0")  # last atlas pair (temporal-nearest)
CAND_VERSION = "v0052"
RUNDIR = REPO / "artifacts/t1_extpretrain/T1-EXTPRE-20261003-v1"
PANEL = REPO / "data/gene_panel/T1__val.genes.txt"
E85 = REPO / "data/E8.5_RNA.h5ad"
E95 = REPO / "data/E9.5_RNA.h5ad"
VOCAB = REPO / "artifacts/tool_integration/T1-PRE-HARMONIZE-20260902-v1/intermediates/state_vocabulary.tsv"
PARENT = REPO / "artifacts/autoresearch/t1-20261002-v1/final_L3_36x38_s20260921/submission.h5ad"
PARENT_SHA = "9615510fdaf6e6103bd65389950aba10b447e88dc81bf5da83d288aea018c97f"
PAIRS = [("E6.5", "E6.75"), ("E6.75", "E7.0"), ("E7.0", "E7.25"), ("E7.25", "E8.0"),
         ("E8.0", "E8.25"), ("E8.25", "E8.5"), ("E8.5", "E9.0")]
GROUPS = ["cardiac", "neural", "endoderm", "blood_vascular", "mesoderm_other",
          "extraembryonic"]
LINEAGE2GROUP = {
    "cardiac_mesoderm": "cardiac", "pericardial_mesoderm": "cardiac",
    "neuroectoderm": "neural", "neural_crest": "neural", "ectoderm": "neural",
    "endoderm": "endoderm",
    "hematopoietic": "blood_vascular", "vascular_endothelial": "blood_vascular",
    "paraxial_mesoderm": "mesoderm_other",
    "extraembryonic_mesoderm": "extraembryonic",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atlas_coarse(name: str) -> str:
    s = str(name).strip().lower()
    if any(k in s for k in ("cardio", "myocard", "epicardium", "endocardium",
                            "pharyngeal mesoderm", "heart")):
        return "cardiac"
    if any(k in s for k in ("neur", "brain", "spinal", "cord", "optic", "crest",
                            "tube", "midbrain", "otic", "placod", "floor plate",
                            "epiblast", "ectoderm", "forebrain", "hindbrain")):
        return "neural"
    if any(k in s for k in ("endo", "gut", "foregut", "hindgut", "midgut",
                            "thyroid", "pharyngeal endoderm")):
        return "endoderm"
    if any(k in s for k in ("erythr", "haemato", "blood", "megakary", "endothel",
                            "endothelium")):
        return "blood_vascular"
    if any(k in s for k in ("allantois", "amniotic", "chorio", "yolk", "parietal",
                            "visceral", "exs", "extraembryonic")):
        return "extraembryonic"
    return "mesoderm_other"


from scripts.t1_temporal_model import _load_board_input  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    import anndata as ad
    from scipy import sparse
    from sklearn.decomposition import PCA
    from sklearn.linear_model import Ridge

    smoke = bool(args.smoke)
    RUN = Path(args.run_dir).resolve()
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "candidates" / "T1_val").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "step": "B_pretrain_transfer", "seed": SEED,
                  "smoke": smoke, "pca_d": PCA_D, "pca_n": PCA_N, "alpha": ALPHA,
                  "holdout_n": HOLDOUT_N, "mix_p": MIX_P,
                  "pair_for_forecast": list(PAIR_FOR_FORECAST),
                  "candidate_version": CAND_VERSION}
    t00 = time.time()

    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    assert len(panel) == 32285
    # ---- step-A cache
    cache = np.load(RUN / "intermediates" / "cache_log1p.npy", mmap_mode="r")
    cache_genes = [str(g) for g in np.load(RUN / "intermediates" / "cache_genes.npy")]
    cache_stages = [str(s) for s in np.load(RUN / "intermediates" / "cache_stages.npy")]
    cache_ct = [str(c) for c in np.load(RUN / "intermediates" / "cache_celltypes.npy")]
    assert cache.shape[0] == len(cache_stages) == len(cache_ct)
    gpos_cache = {g: i for i, g in enumerate(cache_genes)}
    G = [g for g in panel if g in gpos_cache]
    diag["n_G"] = len(G)
    assert len(G) > 25000, f"intersection too small: {len(G)}"
    cidx = np.array([gpos_cache[g] for g in G], dtype=np.int64)

    # ---- official E8.5/E9.5 (log1p already; verified step-A design note)
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    Xp = np.asarray(prev.X.toarray() if sparse.issparse(prev.X) else prev.X, dtype=np.float32)
    Xb = np.asarray(base.X.toarray() if sparse.issparse(base.X) else base.X, dtype=np.float32)
    pidx = {g: i for i, g in enumerate(panel)}
    gidx_official = np.array([pidx[g] for g in G], dtype=np.int64)
    Xp_G, Xb_G = Xp[:, gidx_official], Xb[:, gidx_official]
    tp = np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))
    vocab = pd.read_csv(VOCAB, sep="\t")
    lin_of = dict(zip(vocab["fine_state"].astype(str), vocab["lineage"].astype(str)))
    cov = float(np.mean([t in lin_of for t in list(tp) + list(tb)]))
    assert cov >= 0.99, f"lineage coverage {cov}"
    lins = sorted(set(lin_of.values()))
    lidx = {s: i for i, s in enumerate(lins)}
    Lp = np.array([lidx[lin_of[t]] for t in tp])
    Lb = np.array([lidx[lin_of[t]] for t in tb])

    # ---- PCA on atlas subsample (G block)
    rng = np.random.default_rng(SEED)
    n_cache = cache.shape[0]
    sub = np.sort(rng.choice(n_cache, size=min(PCA_N, n_cache), replace=False))
    Xsub = np.empty((len(sub), len(G)), dtype=np.float32)
    for a in range(0, len(sub), 4000):
        rows = sub[a:a + 4000]
        Xsub[a:a + len(rows)] = np.asarray(cache[rows][:, cidx])
    pca = PCA(n_components=PCA_D, svd_solver="randomized", random_state=SEED)
    pca.fit(Xsub.astype(np.float64))
    V = pca.components_.astype(np.float32)          # (d, n_G)
    mu = pca.mean_.astype(np.float32)               # (n_G,)
    diag["pca_explained"] = float(pca.explained_variance_ratio_.sum())
    del Xsub

    def z_of(XG: np.ndarray) -> np.ndarray:
        return ((XG.astype(np.float64) - mu) @ V.T).astype(np.float32)

    # ---- atlas latent for all kept cells (chunked)
    Z = np.empty((n_cache, PCA_D), dtype=np.float32)
    CH = 20000
    for a in range(0, n_cache, CH):
        blk = np.empty((min(CH, n_cache - a), len(G)), dtype=np.float32)
        rows = np.arange(a, a + blk.shape[0])
        blk[:] = np.asarray(cache[rows][:, cidx])
        Z[a:a + blk.shape[0]] = z_of(blk)
    stage_arr = np.array(cache_stages)
    ct_arr = np.array([atlas_coarse(c) for c in cache_ct])
    gidx = {g: i for i, g in enumerate(GROUPS)}
    ct_onehot = np.zeros((len(ct_arr), len(GROUPS)), dtype=np.float32)
    ct_onehot[np.arange(len(ct_arr)), [gidx[c] for c in ct_arr]] = 1.0

    # ---- pretrain ridge: per-cell rows, target = group/pair mean delta
    pair_idx = {p: i for i, p in enumerate(PAIRS)}
    Z_next_mean = {}
    for p in PAIRS:
        m_from, m_to = stage_arr == p[0], stage_arr == p[1]
        for gname in GROUPS:
            mf = m_from & (ct_arr == gname)
            mt = m_to & (ct_arr == gname)
            if mf.sum() < 32 or mt.sum() < 32:
                Z_next_mean[(p, gname)] = None
                continue
            Z_next_mean[(p, gname)] = (Z[mt].mean(axis=0) - Z[mf].mean(axis=0))
    keep_rows = []
    y_rows = []
    ctx_rows = []
    for p in PAIRS:
        m_from = stage_arr == p[0]
        for gname in GROUPS:
            key = (p, gname)
            if Z_next_mean.get(key) is None:
                continue
            rows = np.flatnonzero(m_from & (ct_arr == gname))
            keep_rows.append(rows)
            y_rows.append(np.repeat(Z_next_mean[key][None, :], len(rows), axis=0))
            po = np.zeros(len(PAIRS), dtype=np.float32)
            po[pair_idx[p]] = 1.0
            ctx = np.concatenate([po, np.eye(len(GROUPS), dtype=np.float32)[gidx[gname]]])
            ctx_rows.append(np.repeat(ctx[None, :], len(rows), axis=0))
    R = np.concatenate(keep_rows)
    Y = np.concatenate(y_rows).astype(np.float64)
    C = np.concatenate(ctx_rows)
    F_pre = np.concatenate([Z[R].astype(np.float64), C], axis=1)
    pre = Ridge(alpha=ALPHA, solver="cholesky")
    pre.fit(F_pre, Y)
    diag["pretrain_rows"] = int(len(R))
    pred_tr = pre.predict(F_pre)
    diag["pretrain_fit_mse"] = float(np.mean((pred_tr - Y) ** 2))
    del F_pre, Y, C, keep_rows, y_rows, ctx_rows

    def pre_delta(z: np.ndarray, pair: tuple, group_onehot: np.ndarray) -> np.ndarray:
        po = np.zeros((len(z), len(PAIRS)), dtype=np.float64)
        po[:, pair_idx[pair]] = 1.0
        return pre.predict(np.concatenate([z.astype(np.float64), po,
                                           group_onehot.astype(np.float64)], axis=1))

    # ---- official latent + transfer correction (train split = all official)
    Zp, Zb = z_of(Xp_G), z_of(Xb_G)
    L_one = np.eye(len(lins), dtype=np.float64)
    R_off = []
    Y_off = []
    for li, lname in enumerate(lins):
        mp, mb = Lp == li, Lb == li
        if mp.sum() < 32 or mb.sum() < 32:
            continue
        dz_off = Zb[mb].mean(axis=0) - Zp[mp].mean(axis=0)
        go = np.eye(len(GROUPS), dtype=np.float64)[gidx[LINEAGE2GROUP[lname]]]
        dz_pre = pre_delta(Zp[mp].mean(axis=0, keepdims=True), PAIR_FOR_FORECAST,
                           go[None, :])[0]
        resid = dz_off - dz_pre
        R_off.append(np.concatenate([Zp[mp].astype(np.float64),
                                     np.repeat(L_one[li][None, :], mp.sum(), axis=0)], axis=1))
        Y_off.append(np.repeat(resid[None, :], mp.sum(), axis=0))
    corr = Ridge(alpha=ALPHA, solver="cholesky")
    corr.fit(np.concatenate(R_off), np.concatenate(Y_off))
    diag["transfer_lineages"] = int(len(R_off))

    def transfer_delta(z: np.ndarray, Ls: np.ndarray) -> np.ndarray:
        go = np.zeros((len(z), len(GROUPS)), dtype=np.float64)
        for li, lname in enumerate(lins):
            m = Ls == li
            if m.any():
                go[m] = np.eye(len(GROUPS), dtype=np.float64)[gidx[LINEAGE2GROUP[lname]]]
        dpre = pre_delta(z, PAIR_FOR_FORECAST, go)
        F = np.concatenate([z.astype(np.float64),
                            np.eye(len(lins), dtype=np.float64)[Ls]], axis=1)
        return dpre + corr.predict(F)

    # ---- G-return local gate
    vidx = np.sort(rng.choice(len(Zp), size=HOLDOUT_N, replace=False))
    tr_mask = np.ones(len(Zp), bool)
    tr_mask[vidx] = False
    # refit correction WITHOUT held-out (leakage guard; disclosed)
    R_off2, Y_off2 = [], []
    for li, lname in enumerate(lins):
        mp = (Lp == li) & tr_mask
        mb = Lb == li
        if mp.sum() < 32 or mb.sum() < 32:
            continue
        dz_off = Zb[mb].mean(axis=0) - Zp[mp].mean(axis=0)
        go = np.eye(len(GROUPS), dtype=np.float64)[gidx[LINEAGE2GROUP[lname]]]
        dz_pre = pre_delta(Zp[mp].mean(axis=0, keepdims=True), PAIR_FOR_FORECAST,
                           go[None, :])[0]
        R_off2.append(np.concatenate([Zp[mp].astype(np.float64),
                                      np.repeat(L_one[li][None, :], mp.sum(), axis=0)], axis=1))
        Y_off2.append(np.repeat((dz_off - dz_pre)[None, :], mp.sum(), axis=0))
    corr2 = Ridge(alpha=ALPHA, solver="cholesky")
    corr2.fit(np.concatenate(R_off2), np.concatenate(Y_off2))

    def transfer_delta2(z, Ls):
        go = np.zeros((len(z), len(GROUPS)), dtype=np.float64)
        for li, lname in enumerate(lins):
            m = Ls == li
            if m.any():
                go[m] = np.eye(len(GROUPS), dtype=np.float64)[gidx[LINEAGE2GROUP[lname]]]
        dpre = pre_delta(z, PAIR_FOR_FORECAST, go)
        F = np.concatenate([z.astype(np.float64),
                            np.eye(len(lins), dtype=np.float64)[Ls]], axis=1)
        return dpre + corr2.predict(F)

    zv = Zp[vidx] + transfer_delta2(Zp[vidx], Lp[vidx])
    Xret_G = np.clip(zv.astype(np.float64) @ V + mu, 0.0, None).astype(np.float32)
    # full panel for the scorer: non-G genes inherit official E8.5 held-out values
    Xret = Xp[vidx].copy()
    Xret[:, gidx_official] = Xret_G
    assert np.isfinite(Xret).all()

    if smoke:
        diag["wall_s"] = time.time() - t00
        (RUN / "SMOKE_B.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": True, "n_G": diag["n_G"],
                          "pca_explained": diag["pca_explained"],
                          "pretrain_rows": diag["pretrain_rows"]}, indent=1), flush=True)
        return 0

    # return candidate is diagnostic-only (held-out E8.5 cells, not parent rows):
    # scorer only, no parent contract. Full contract applies to the E10.5 candidate.
    ret_dir = RUN / "candidates" / "T1_val" / "gate_return"
    ret_dir.mkdir(parents=True, exist_ok=True)
    out_ret = ret_dir / "submission.h5ad"
    a = ad.AnnData(X=np.ascontiguousarray(Xret), obs=prev.obs.iloc[np.asarray(vidx)].copy(),
                   var=pd.DataFrame(index=panel))
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_t1_extpre"] = json.dumps({"atom_id": TASK_ID, "lane": "G_RETURN",
        "method": "extpretrain_return", "seed": SEED, "target_used": False}, sort_keys=True)
    a.write_h5ad(out_ret)
    diag["return_contract"] = "SKIPPED_DIAGNOSTIC_ONLY"

    import subprocess
    mout = RUN / "intermediates" / "scorer_return.json"
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(out_ret), "--target", "data/E9.5_RNA.h5ad",
           "--reference", "data/E8.5_RNA.h5ad", "--seed", str(SEED), "--out", str(mout)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("scorer failed: " + r.stderr[-1500:])
    m = json.loads(mout.read_text())["metrics"]
    keep_keys = ("de_score", "de_direction", "energy_distance", "mmd_u", "variogram",
                 "pb_rel_err", "library_size_ratio", "variance_ratio",
                 "composition_JSD", "pseudobulk_pearson")
    diag["return_local"] = {k: m.get(k) for k in keep_keys}
    gate1 = bool(m["de_score"] > LOCAL_DE and m["de_direction"] > LOCAL_DIR)
    diag["gate_G_return_pass"] = gate1
    print(json.dumps({"gate_G_return": gate1, "local": diag["return_local"]}, indent=1), flush=True)
    if not gate1:
        diag["verdict"] = "STOP_gate1"
        diag["wall_s"] = time.time() - t00
        (RUN / "RESULT_B.json").write_text(json.dumps(diag, indent=1, default=float))
        return 0

    # ---- E10.5 forecast from v0051 bank (G-latent) + 70/30 mixture
    assert sha256(PARENT) == PARENT_SHA, "BLOCKED_INPUT: parent v0051 drift"
    v5 = ad.read_h5ad(PARENT)
    assert [str(v) for v in v5.var_names] == panel
    X5 = np.asarray(v5.X.toarray() if sparse.issparse(v5.X) else v5.X, dtype=np.float32)
    t5 = np.asarray(v5.obs["celltype"].astype(str))
    cov5 = float(np.mean([t in lin_of for t in t5]))
    assert cov5 >= 0.99, f"parent lineage coverage {cov5}"
    L5 = np.array([lidx[lin_of[t]] for t in t5])
    X5_G = X5[:, gidx_official]
    Z5 = z_of(X5_G)
    dz5 = transfer_delta(Z5, L5)
    Zf = Z5 + dz5
    Xf_G = np.clip(Zf.astype(np.float64) @ V + mu, 0.0, None).astype(np.float32)
    Xf = X5.copy()
    Xf[:, gidx_official] = Xf_G
    # 70/30 row mixture with parent v0051 (frozen seed)
    side = rng.random(len(X5)) < MIX_P
    Xnew = np.where(side[:, None], X5, Xf).astype(np.float32)
    cand_dir = RUN / "candidates" / "T1_val" / f"{CAND_VERSION}_t1_extpre"
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    if out.exists():
        raise FileExistsError(str(out))
    ca = ad.AnnData(X=np.ascontiguousarray(Xnew), obs=v5.obs.copy(),
                    var=pd.DataFrame(index=panel))
    ca.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    ca.uns["ve_t1_extpre"] = json.dumps({"atom_id": TASK_ID, "lane": "L1_EXTPRE",
        "method": "extpretrain_forecast_mix", "parent": "v0051 AR-MIX L3",
        "parent_sha256": PARENT_SHA, "seed": SEED, "mix_p": MIX_P,
        "pair_for_forecast": list(PAIR_FOR_FORECAST), "target_used": False}, sort_keys=True)
    ca.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)
    ca.write_h5ad(cand_dir / "submission.rerun.h5ad")
    assert sha256(cand_dir / "submission.rerun.h5ad") == diag["candidate_sha"]
    (cand_dir / "submission.rerun.h5ad").unlink()
    diag["rerun_bytes_identical"] = True
    cio_path = REPO / "docs" / "batch3" / "interfaces"
    if str(cio_path) not in sys.path:
        sys.path.insert(0, str(cio_path))
    from virtual_embryo_tools import contract_io
    res2 = dict(contract_io.validate_h5ad_contract(
        out, task="T1", board="val",
        scorer_lock=REPO / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json",
        parent_path=PARENT, parent_sha256=PARENT_SHA))
    diag["contract"] = res2.get("status")
    assert res2.get("status") in ("PASS", "pass"), f"contract: {res2}"
    mout2 = RUN / "intermediates" / "scorer_L1.json"
    cmd2 = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
            "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
            "--input", str(out), "--target", "data/E9.5_RNA.h5ad",
            "--reference", "data/E8.5_RNA.h5ad", "--seed", str(SEED), "--out", str(mout2)]
    r2 = subprocess.run(cmd2, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r2.returncode != 0:
        raise RuntimeError("scorer failed: " + r2.stderr[-1500:])
    m2 = json.loads(mout2.read_text())["metrics"]
    diag["local"] = {k: m2.get(k) for k in keep_keys}
    gate2 = bool(m2["de_score"] > LOCAL_DE and m2["de_direction"] > LOCAL_DIR)
    diag["gate_candidate_pass"] = gate2
    diag["promoted_local"] = gate2
    diag["verdict"] = "GATE2_PASS_package" if gate2 else "STOP_gate2"
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT_B.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"built": True, "gate2": gate2, "sha": diag["candidate_sha"],
                      "local": diag["local"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
