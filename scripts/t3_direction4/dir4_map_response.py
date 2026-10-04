#!/usr/bin/env python3
"""T3 direction-4: full-transcriptome intermediary mapping + paired response (T3-DIR4).

Design: artifacts/t3_direction4/T3-DIR4-20261001-v1/DESIGN.md
(frozen 2026-10-01; proposal reports/T3_NEXT_ROUTES_20260920.md section 6).

Pipeline (all pre-declared, single run, no sweep):
  1. Load v7 WT scRNA (log1p) + spatial parent v0009 (log1p, Gata4 already 0).
  2. Split 500 panel genes into alignment (450) / holdout-validation (50) by fixed seed.
     Holdout genes NEVER enter neighbor search (hard split = independence).
  3. Map each spatial cell -> RNA neighborhood: correlation distance on alignment
     genes, uniform average over k=30 neighbors (no temperature tuning).
  4. Gates (any fail -> STOP, no candidate):
     G1 holdout: mapping-predicted holdout values beat per-celltype-mean baseline
         (MAE, overall; per-celltype and per-sample-group reported).
     G2 lineage concentration: >=80% of mapping weight inside the same coarse
         lineage (explicit crosswalk table below; 'Unknown' cells excluded from
         the denominator and reported separately).
     G3 mediator identifiability: every propagated mediator needs consensus sign
         + within-state slope sign match + |slope| floor; failures are listed as
         unsupported and excluded (never silently kept).
  5. Perturbation operator (identical for both arms): Gata4 := 0 propagated two
     steps through signed CollecTRI edges (Gata4 -> mediators -> panel targets)
     with within-state observational slopes as amplitudes (DISCLOSED as
     observational, not causal; the paired design + G1 gate arbitrate).
     Arm A (control): mediators restricted to panel-internal TFs.
     Arm B (direction-4): all supported mediators (panel-external allowed).
  6. X_new = X_parent + delta_B in log1p space (MERFISH residual/scale preserved;
     response only). Gata4 column forced to parent values. Null check:
     mean|delta_B - delta_A| < 1e-6 -> STOP (no direction-4 increment).
  7. Contract validation + local diagnostics. No server claim. No upload.

Modes: --smoke (mechanics on subset, asserts, no contract/INDEX), full build.
Deterministic: fixed seeds; kNN/regression have no RNG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd
from scipy import sparse

TASK_ID = "T3-DIR4-MAPRESPONSE"
RUN_SEED = 20261001
HOLDOUT_SEED = 20261001
N_HOLDOUT = 50
KNN_K = 30
CONC_THRESHOLD = 0.80
SLOPE_FLOOR = 1e-3
EXPR_FLOOR = 0.05
MIN_STATE_N = 200
NULL_TOL = 1e-6

PANEL = REPO / "data" / "gene_panel" / "T3__gata4.genes.txt"
V7D = REPO / "artifacts" / "tool_integration" / "T3-S1A-STATE-JOIN-20260901-v7" / "data"
V7_MTX = V7D / "state_input_counts.mtx"
V7_GENES = V7D / "state_input_genes.tsv"
V7_META = V7D / "metadata_cells_sanitized.tsv"
V0009 = REPO / "submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad"
V0009_SHA = "c6be65ec7d8c8a4b94bce936ff0cad985ac26f78c77ea3e4f68643f07076b088"
COLLECTRI = REPO / "infra" / "external_data" / "sanitized" / "T3-S1A-STATE-JOIN" / "COLLECTRI" / "collectri_mouse_full.tsv"
N_CELLS = 7449
CAND_VERSION = "v0069"
CAND_DIRNAME = "v0069_t3_dir4_mediator"
CAND_LANE = "R1_MEDIATOR"

from scripts.t1_temporal_model import _load_board_input  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ----------------------------------------------------------------------------
# Coarse-lineage crosswalk (explicit, frozen, auditable).
# consulted in order: exact-token overrides -> keyword rules -> default.
# 'Unknown' spatial cells are unassignable by construction.
# ----------------------------------------------------------------------------
_TOKEN_OVERRIDE = {
    "peri": "cardiac",        # pericardial cells (mesodermal, heart-adjacent)
    "endotome": "blood_vascular",  # somite compartment fated to endothelium
    "v-cse": "blood_vascular",     # uncertain expansion; endothelial reading
    "d-cse": "blood_vascular",     # uncertain expansion; endothelial reading
}

_SHORT_TOKENS = {
    "cm": "cardiac", "jcf": "cardiac", "phm": "cardiac",
    "ncc": "neural", "cse": "blood_vascular",
    "fg": "endoderm", "foregut": "endoderm",
    "som": "mesoderm_other", "pam": "mesoderm_other", "lpm": "mesoderm_other",
    "exe": "extraembryonic", "ys": "extraembryonic",
    "emp": "blood_vascular", "mep": "blood_vascular", "pgc": "pluripotent",
}

_LONG_RULES = [  # (substring, group), first match wins
    ("epiblast", "pluripotent"), ("nmp", "pluripotent"),
    ("erythroid", "blood_vascular"), ("haemato", "blood_vascular"),
    ("blood", "blood_vascular"), ("megakaryocyte", "blood_vascular"),
    ("endothel", "blood_vascular"),
    ("allantois", "extraembryonic"), ("amniotic", "extraembryonic"),
    ("chorio", "extraembryonic"), ("yolk", "extraembryonic"),
    ("parietal", "extraembryonic"), ("visceral", "extraembryonic"),
    ("placenta", "extraembryonic"),
    ("endo", "endoderm"), ("gut", "endoderm"), ("thyroid", "endoderm"),
    ("cardio", "cardiac"), ("myocard", "cardiac"), ("epicardium", "cardiac"),
    ("endocardium", "cardiac"), ("pharyngeal mesoderm", "cardiac"),
    ("neur", "neural"), ("brain", "neural"), ("spinal", "neural"),
    ("cord", "neural"), ("optic", "neural"), ("vesicle", "neural"),
    ("crest", "neural"), ("tube", "neural"), ("midbrain", "neural"),
    ("otic", "neural"), ("placod", "neural"), ("floor plate", "neural"),
    ("cranial", "neural"),
    ("ectoderm", "epithelial"), ("epidermis", "epithelial"),
    ("surface", "epithelial"),
    ("mesoderm", "mesoderm_other"), ("mesenchyme", "mesoderm_other"),
    ("somit", "mesoderm_other"), ("sclerotome", "mesoderm_other"),
    ("dermomyotome", "mesoderm_other"), ("limb", "mesoderm_other"),
    ("kidney", "mesoderm_other"), ("forelimb", "mesoderm_other"),
]


def coarse_of(name: str) -> str | None:
    s = str(name).strip().lower()
    if s == "unknown":
        return None
    toks = set(re.split(r"[^a-z0-9]+", s)) - {""}
    for t in toks:
        if t in _TOKEN_OVERRIDE:
            return _TOKEN_OVERRIDE[t]
    for t in toks:
        if t in _SHORT_TOKENS:
            return _SHORT_TOKENS[t]
    for sub, grp in _LONG_RULES:
        if sub in s:
            return grp
    return "mesoderm_other"


def load_rna(subset_cells: int | None = None):
    import anndata as ad
    from scipy.io import mmread
    genes_df = pd.read_csv(V7_GENES, sep="\t")
    genes = genes_df["gene"].astype(str).tolist()
    meta = pd.read_csv(V7_META, sep="\t")
    if subset_cells is not None:
        rng = np.random.default_rng(RUN_SEED)
        idx = np.sort(rng.choice(len(meta), size=subset_cells, replace=False))
    else:
        idx = None
    m = mmread(str(V7_MTX)).tocsc()
    if idx is not None:
        m = m[:, idx]
        meta = meta.iloc[idx].reset_index(drop=True)
    X = m.T.tocsr()
    X.data = np.log1p(X.data).astype(np.float32)
    return X, genes, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--n-holdout", type=int, default=0)
    args = ap.parse_args()
    import anndata as ad
    smoke = bool(args.smoke)
    K = int(args.k or KNN_K)
    NH = int(args.n_holdout or N_HOLDOUT)

    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "smoke": smoke, "k": K,
                  "n_holdout": NH, "candidate_version": CAND_VERSION}
    t00 = time.time()

    assert sha256(V0009) == V0009_SHA, "BLOCKED_INPUT: v0009 hash drift"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    assert len(panel) == 500
    parent = ad.read_h5ad(V0009)
    assert parent.n_obs == N_CELLS and parent.n_vars == 500
    assert [str(v) for v in parent.var_names] == panel
    ctypes = np.asarray(parent.obs["celltype"].astype(str))
    Xp = np.asarray(parent.X.toarray() if sparse.issparse(parent.X) else parent.X,
                    dtype=np.float32)

    # ---- holdout split (hard: holdout genes never enter neighbor search)
    rng = np.random.default_rng(HOLDOUT_SEED)
    h_idx = np.sort(rng.choice(len(panel), size=NH, replace=False))
    holdout = [panel[i] for i in h_idx]
    align = [g for j, g in enumerate(panel) if j not in set(h_idx.tolist())]
    diag["holdout_genes"] = holdout

    # ---- RNA load
    Xr, genes_r, meta = load_rna(subset_cells=3000 if smoke else None)
    gidx = {g: i for i, g in enumerate(genes_r)}
    assert all(g in gidx for g in panel), "panel genes missing from v7"
    states = np.asarray(meta["state"].astype(str))
    samples = np.asarray(meta["sample"].astype(str))
    rna_coarse = np.array([coarse_of(s) or "mesoderm_other" for s in states])
    spat_coarse = np.array([coarse_of(t) for t in ctypes])
    diag["coarse_table_spatial"] = {t: coarse_of(t) for t in sorted(set(ctypes.tolist()))}

    ai = np.array([gidx[g] for g in align], dtype=np.int64)
    hi = np.array([gidx[g] for g in holdout], dtype=np.int64)
    A_r = Xr[:, ai].toarray().astype(np.float32)          # RNA alignment block
    H_r = Xr[:, hi].toarray().astype(np.float32)          # RNA holdout block
    A_s = Xp[:, [panel.index(g) for g in align]].astype(np.float32)
    H_s = Xp[:, h_idx].astype(np.float32)

    # ---- kNN mapping (correlation distance, uniform k-average; deterministic)
    def topk_neighbors(Aq: np.ndarray, K: int) -> np.ndarray:
        Aq_c = Aq - Aq.mean(axis=1, keepdims=True)
        Ar_c = A_r - A_r.mean(axis=1, keepdims=True)
        num = Aq_c @ Ar_c.T
        denom = (np.linalg.norm(Aq_c, axis=1, keepdims=True)
                 * np.linalg.norm(Ar_c, axis=1, keepdims=True).T + 1e-8)
        corr = num / denom
        part = np.argpartition(-corr, K - 1, axis=1)[:, :K]
        return part

    nbr = topk_neighbors(A_s, K)
    n_spat = A_s.shape[0]

    # ---- G2 lineage concentration
    same_w = 0.0
    tot_w = 0.0
    assignable = spat_coarse != None  # noqa: E711
    for i in range(n_spat):
        if spat_coarse[i] is None:
            continue
        same_w += float((rna_coarse[nbr[i]] == spat_coarse[i]).sum()) / K
        tot_w += 1.0
    conc = same_w / max(tot_w, 1.0)
    n_unknown = int((~assignable).sum())
    diag["lineage_concentration"] = float(conc)
    diag["n_unknown_spatial"] = n_unknown
    # neighbor sample diversity (reported; gene-holdout is the independence)
    samp_of_nbr = samples[nbr]
    n_samp_used = int(len(np.unique(samp_of_nbr)))
    diag["n_neighbor_samples"] = n_samp_used
    diag["gate_G2_pass"] = bool(conc >= CONC_THRESHOLD)

    # ---- G1 holdout validation (mapping vs per-celltype baseline)
    H_pred = H_r[nbr].mean(axis=1)
    base = np.zeros_like(H_s)
    for t in sorted(set(ctypes.tolist())):
        m = ctypes == t
        base[m] = H_s[m].mean(axis=0, keepdims=True)
    mae_map = float(np.abs(H_pred - H_s).mean())
    mae_base = float(np.abs(base - H_s).mean())
    diag["holdout_mae_map"] = mae_map
    diag["holdout_mae_baseline"] = mae_base
    per_ct, per_samp = {}, {}
    for t in sorted(set(ctypes.tolist())):
        m = ctypes == t
        per_ct[t] = {"map": float(np.abs(H_pred[m] - H_s[m]).mean()),
                     "base": float(np.abs(base[m] - H_s[m]).mean()),
                     "n": int(m.sum())}
    dom_samp = np.array([np.bincount(samp_of_nbr[i].astype(int)).argmax()
                         for i in range(n_spat)])
    for s in sorted(set(dom_samp.tolist())):
        m = dom_samp == s
        per_samp[f"rna_sample_{s}"] = {
            "map": float(np.abs(H_pred[m] - H_s[m]).mean()),
            "base": float(np.abs(base[m] - H_s[m]).mean()), "n": int(m.sum())}
    diag["holdout_per_celltype"] = per_ct
    diag["holdout_per_sample"] = per_samp
    diag["gate_G1_pass"] = bool(mae_map < mae_base)

    if smoke:
        assert np.isfinite(H_pred).all()
        assert diag["gate_G1_pass"] in (True, False)
        diag["wall_s"] = time.time() - t00
        (RUN / "SMOKE.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"smoke_ok": True, "G1": diag["gate_G1_pass"],
                          "G2": diag["gate_G2_pass"],
                          "mae_map": mae_map, "mae_base": mae_base,
                          "conc": float(conc)}, indent=1), flush=True)
        return 0

    if not (diag["gate_G1_pass"] and diag["gate_G2_pass"]):
        diag["wall_s"] = time.time() - t00
        diag["verdict"] = "STOP_no_candidate"
        (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"gate_pass": False, "G1": diag["gate_G1_pass"],
                          "G2": diag["gate_G2_pass"],
                          "note": "STOP, no candidate"}, indent=1), flush=True)
        return 0

    # ---- mediators: Gata4 direct CollecTRI targets, WT-selected (G3)
    cr = pd.read_csv(COLLECTRI, sep="\t")
    cr = cr[cr["is_directed"] == True]  # noqa: E712
    cr["tgt"] = cr["target_genesymbol"].astype(str)
    cr["src"] = cr["source_genesymbol"].astype(str)

    def consensus_sign(r) -> int:
        if bool(r["consensus_stimulation"]) and not bool(r["consensus_inhibition"]):
            return 1
        if bool(r["consensus_inhibition"]) and not bool(r["consensus_stimulation"]):
            return -1
        return 0

    cr["csign"] = cr.apply(consensus_sign, axis=1)
    rna_mean = np.asarray(Xr.mean(axis=0)).ravel()
    rna_mean_d = {g: float(rna_mean[gidx[g]]) for g in genes_r if g in gidx}
    g4_targets = cr[(cr["src"] == "Gata4") & (cr["csign"] != 0)]
    # within-state pooled slopes (demeaned per state, states with n>=MIN_STATE_N)
    states_u, state_n = np.unique(states, return_counts=True)
    big_states = [s for s, n in zip(states_u, state_n) if n >= MIN_STATE_N]
    diag["n_big_states"] = len(big_states)

    # columns needed: Gata4 + all distinct sources/targets among candidate edges
    med_cands = sorted({str(t) for t in g4_targets["tgt"]
                        if t in gidx and rna_mean_d.get(t, 0.0) > EXPR_FLOOR})

    def pooled_slope(xcols: np.ndarray, ycols: np.ndarray) -> np.ndarray:
        """Slope of each (x,y) col pair, states demeaned then pooled."""
        S = np.zeros((xcols.shape[1],), dtype=np.float64)
        return S  # placeholder replaced below (vectorized per-edge loop)

    # vectorized: build demeaned matrices for needed cols once
    need = sorted(set(["Gata4"] + med_cands
                      + [str(t) for t in cr[cr["src"].isin(med_cands)]["tgt"]
                         if t in gidx]))
    need_idx = np.array([gidx[g] for g in need], dtype=np.int64)
    need_pos = {g: j for j, g in enumerate(need)}
    Z = Xr[:, need_idx].toarray().astype(np.float64)
    Zdm = np.zeros_like(Z)
    for s in big_states:
        m = states == s
        Zdm[m] = Z[m] - Z[m].mean(axis=0, keepdims=True)
    use = np.isin(states, big_states)
    Zdm, Z = Zdm[use], Z[use]
    VV = (Zdm ** 2).sum(axis=0)

    def slope_of(a: str, b: str) -> float:
        j, k = need_pos[a], need_pos[b]
        v = VV[j]
        if v < 1e-12:
            return 0.0
        return float((Zdm[:, j] * Zdm[:, k]).sum() / v)

    supported, unsupported = {}, []
    for m in med_cands:
        erow = g4_targets[g4_targets["tgt"] == m].iloc[0]
        s = slope_of("Gata4", m)
        if int(erow["csign"]) == (1 if s > 0 else (-1 if s < 0 else 0)) and abs(s) > SLOPE_FLOOR:
            supported[m] = {"sign": int(erow["csign"]), "slope_G": s}
        else:
            unsupported.append({"gene": m, "sign_consensus": int(erow["csign"]),
                                "slope": s, "reason": "sign_mismatch_or_weak"})
    diag["n_mediators_supported"] = len(supported)
    diag["n_mediators_unsupported"] = len(unsupported)
    diag["unsupported"] = unsupported[:50]

    # mediator -> panel edges (consensus-signed, slope-checked)
    med2panel: dict[str, list] = {}
    for m in supported:
        sub = cr[(cr["src"] == m) & (cr["tgt"].isin(panel)) & (cr["csign"] != 0)]
        lst = []
        for _, r in sub.iterrows():
            g = str(r["tgt"])
            s = slope_of(m, g)
            if int(r["csign"]) == (1 if s > 0 else (-1 if s < 0 else 0)) and abs(s) > SLOPE_FLOOR:
                lst.append((g, s))
            else:
                unsupported.append({"gene": f"{m}->{g}", "sign_consensus": int(r["csign"]),
                                    "slope": s, "reason": "sign_mismatch_or_weak"})
        med2panel[m] = lst
    diag["n_med2panel_edges"] = int(sum(len(v) for v in med2panel.values()))
    panel_tfs = set([g for g in panel if g in set(cr["src"])])
    diag["gate_G3_note"] = ("all propagated mediators/edges consensus-signed with "
                            "slope floor; failures listed unsupported, never kept")

    # ---- propagation (identical operator, two representations)
    gi4_r = gidx["Gata4"]
    G4wt = np.asarray(Xr[:, gi4_r].toarray()).ravel().astype(np.float64)[np.asarray(
        [nbr[i] for i in range(n_spat)]).ravel()].reshape(n_spat, K).mean(axis=1)
    delta = {"A": np.zeros((n_spat, len(panel)), dtype=np.float64),
             "B": np.zeros((n_spat, len(panel)), dtype=np.float64)}
    pidx = {g: j for j, g in enumerate(panel)}
    for arm, allowed in (("A", lambda m: m in panel_tfs and m in panel),
                         ("B", lambda m: True)):
        D = delta[arm]
        for m, info in supported.items():
            if not allowed(m):
                continue
            dm = -info["slope_G"] * G4wt
            for g, s in med2panel.get(m, []):
                D[:, pidx[g]] += s * dm
    inc = float(np.abs(delta["B"] - delta["A"]).mean())
    diag["increment_mean_abs"] = inc
    diag["n_panel_tfs"] = len(panel_tfs)
    if inc < NULL_TOL:
        diag["wall_s"] = time.time() - t00
        diag["verdict"] = "STOP_null_increment"
        (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1, default=float))
        print(json.dumps({"gate_pass": False, "note": "STOP_null_increment",
                          "increment": inc}, indent=1), flush=True)
        return 0

    # ---- candidate (Arm B; Gata4 column forced to parent)
    Xout = np.clip(Xp.astype(np.float64) + delta["B"], 0.0, None).astype(np.float32)
    gi4_p = panel.index("Gata4")
    Xout[:, gi4_p] = Xp[:, gi4_p]
    assert np.isfinite(Xout).all()
    cand_dir = RUN / "candidates" / "T3_gata4" / f"{CAND_DIRNAME}"
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    if out.exists():
        raise FileExistsError(str(out))
    a = ad.AnnData(X=np.ascontiguousarray(Xout), obs=parent.obs.copy(),
                   var=pd.DataFrame(index=panel))
    a.obsm["spatial_3D"] = np.asarray(parent.obsm["spatial_3D"]).copy()
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_t3_dir4"] = json.dumps(
        {"atom_id": TASK_ID, "lane": CAND_LANE, "method": "fulltx_mediator_response",
         "parent": "v0009_b4_t3_r1_l1_gata4_zero_all", "parent_sha256": V0009_SHA,
         "seed": RUN_SEED, "k": K, "n_holdout": NH, "target_used": False},
        sort_keys=True)
    a.write_h5ad(out)
    diag["candidate_sha"] = sha256(out)
    a.write_h5ad(cand_dir / "submission.rerun.h5ad")
    assert sha256(cand_dir / "submission.rerun.h5ad") == diag["candidate_sha"]
    (cand_dir / "submission.rerun.h5ad").unlink()
    diag["rerun_bytes_identical"] = True
    assert np.array_equal(np.asarray(a.obsm["spatial_3D"]),
                          np.asarray(parent.obsm["spatial_3D"])), "coords changed"
    assert a.n_obs == N_CELLS

    cio_path = REPO / "docs" / "batch3" / "interfaces"
    if str(cio_path) not in sys.path:
        sys.path.insert(0, str(cio_path))
    from virtual_embryo_tools import contract_io
    res = dict(contract_io.validate_h5ad_contract(
        out, task="T3", board="gata4",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0009, parent_sha256=V0009_SHA))
    diag["contract"] = res.get("status")
    assert res.get("status") in ("PASS", "pass"), f"contract: {res}"

    diag["wall_s"] = time.time() - t00
    diag["verdict"] = "BUILT_score_pending"
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"built": True, "sha": diag["candidate_sha"],
                      "G1": diag["gate_G1_pass"], "G2": diag["gate_G2_pass"],
                      "n_med": len(supported), "increment": inc,
                      "contract": diag["contract"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
