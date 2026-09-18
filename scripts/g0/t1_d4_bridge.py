#!/usr/bin/env python3
"""G1-T1-D4 bridge port: T2-R2 shared-endpoint anchoring -> T1 extrapolation.

D4 mechanism (DECISIONS D-20260917-T1P02-001): anchor E10.5 composition + per-type
shift with the T2-R2 bridge operator, NOT v0002-style unconstrained linear share
extrapolation (killed, -1.1: Foregut/pSHF pressed to bounds). Distinctions:
  (a) deltas at T1-PRE frozen fine-state resolution (biological states, not KMeans;
      R2's KMeans failure does not apply);
  (b) UNRESOLVED fine-states get delta 0 (no strong matching, T1-PRE rule);
  (c) composition via shrinkage-regularized share projection, growth shrunk toward
      no-change with FIXED k=0.25 (mirrors B4-L3, the only composition dose that ever
      helped at 47.85; fixed from precedent, no sweep, no pseudo-target fitting);
  (d) largest-remainder resampling (T2-R2 recipe), deterministic, with ledger.

Gate G (diagnostic, E8.5->E9.5 return, NOT candidates):
  G0 plain  = fine-state shift return, no resampling.
  G1 bridge = fine-state shift return + resample to exact E9.5 shares.
  PASS iff G1 de_score AND de_direction both strictly above G0 (composition signal).
  FAIL -> STOP, no candidates, verdict REJECT.

Lanes (only if gate passes):
  L1 v0022: fine-state deltas E9.5->E10.5 + shrunk shares (k=0.25) + resample v0004 bank.
  L2 v0023: fine-state deltas only, v0004 row multiset kept (composition ablation).
Local gate (standing rule): de>0.8868 AND dir>0.8895 -> PROMOTED.
Frozen: E8.5/E9.5 inputs, v0004 rows/sha, panel, T1-PRE crosswalk, seeds. No training.
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

TASK_ID = "G1-T1-D4-BRIDGE"
RUN_SEED = 20260916
SHRINK_K = 0.25  # fixed from B4-L3 precedent; no sweep
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
XWALK = REPO / "artifacts" / "tool_integration" / "T1-PRE-HARMONIZE-20260902-v1" / "intermediates" / "state_crosswalk.tsv"
N_CELLS = 5118
LOCAL_DE, LOCAL_DIR = 0.8868, 0.8895

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


def load_crosswalk():
    xw = pd.read_csv(XWALK, sep="\t")
    fwd, rev = {}, {}
    for _, r in xw.iterrows():
        d = str(r["direction"])
        s = str(r["fine_state"])
        m = str(r["matched_state"])
        hit = m != "UNRESOLVED"
        if d == "e85_to_e95":
            fwd[s] = m if hit else None
        elif d == "e95_to_e85":
            rev[s] = m if hit else None
    return fwd, rev


def state_means(X: np.ndarray, labels: np.ndarray):
    out = {}
    for s in sorted(set(labels.tolist())):
        out[s] = X[labels == s].mean(axis=0).astype(np.float32)
    return out


def fine_deltas(mean_to: dict, mean_from: dict, mapping: dict, panel_len: int):
    """delta[from_state] = mean_to[match] - mean_from[from_state]; None/unknown -> 0."""
    out, rows = {}, []
    for s in sorted(mean_from):
        m = mapping.get(s)
        if m is not None and m in mean_to:
            out[s] = (mean_to[m] - mean_from[s]).astype(np.float32)
            rows.append({"state": s, "match": m, "rule": "matched"})
        else:
            out[s] = np.zeros(panel_len, dtype=np.float32)
            rows.append({"state": s, "match": "UNRESOLVED", "rule": "zero"})
    return out, pd.DataFrame(rows)


def largest_remainder(shares: dict, total: int) -> dict:
    states = sorted(shares)
    raw = np.array([shares[s] * total for s in states])
    base = np.floor(raw).astype(int)
    rem = raw - base
    short = total - int(base.sum())
    order = sorted(range(len(states)), key=lambda i: (-rem[i], states[i]))
    for i in order[:short]:
        base[i] += 1
    return {s: int(base[i]) for i, s in enumerate(states)}


def resample_bank(pool_idx: dict, counts: dict, seed: int):
    rng = np.random.default_rng(seed)
    chosen, plan, replaced = [], [], {}
    for s in sorted(counts):
        pool = pool_idx[s]
        k = counts[s]
        if k <= 0:
            plan.append({"state": s, "have": int(len(pool)), "target_n": 0,
                         "with_replacement": False})
            continue
        if k <= len(pool):
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=False)] if k < len(pool) else pool)
            wr = False
        else:
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=True)])
            wr = True
            replaced[s] = {"need": int(k), "have": int(len(pool))}
        chosen.extend(sel.tolist())
        plan.append({"state": s, "have": int(len(pool)), "target_n": int(k),
                     "with_replacement": wr})
    return np.asarray(chosen, dtype=np.int64), pd.DataFrame(plan), replaced


def run_scorer(out: Path, lane: str, run_dir: Path) -> dict:
    import subprocess
    mout = run_dir / "metrics" / f"scorer_{lane}.json"
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
    (run_dir / "metrics" / f"scorer_{lane}_slim.json").write_text(json.dumps(keep, indent=1))
    return keep


def write_candidate(Xout: np.ndarray, obs, lane: str, method: str, extra_uns: dict,
                    run_dir: Path, out_version: str, resampled: bool):
    cand_dir = run_dir / "candidates" / "T1_val" / out_version
    cand_dir.mkdir(parents=True, exist_ok=True)
    out = cand_dir / "submission.h5ad"
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    a = ad.AnnData(X=np.ascontiguousarray(Xout, dtype=np.float32), obs=obs.copy(),
                   var=pd.DataFrame(index=panel))
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    meta = {"atom_id": TASK_ID, "lane": lane, "method": method,
            "parent": "v0004 recipe + T1-PRE crosswalk", "seed": RUN_SEED,
            "shrink_k": SHRINK_K, "target_used": False,
            "row_multiset_changed": bool(resampled)}
    meta.update(extra_uns)
    a.uns["ve_g0_t1_d4"] = json.dumps(meta, sort_keys=True)
    a.write_h5ad(out)
    cio = _contract_io()
    res = dict(cio.validate_h5ad_contract(
        out, task="T1", board="val",
        scorer_lock=REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json",
        parent_path=V0004, parent_sha256=V0004_SHA))
    return out, res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "candidates" / "T1_val").mkdir(parents=True, exist_ok=True)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED, "shrink_k": SHRINK_K}
    t00 = time.time()

    assert sha256(V0004) == V0004_SHA, "BLOCKED_INPUT: v0004 hash drift"
    diag["v0004_sha_ok"] = True
    diag["xwalk_sha"] = sha256(XWALK)
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    v4 = ad.read_h5ad(V0004)
    fwd, rev = load_crosswalk()
    Xp, Xb = to_dense(prev), to_dense(base)
    tp = np.asarray(prev.obs["celltype"].astype(str))
    tb = np.asarray(base.obs["celltype"].astype(str))
    m8, m9 = state_means(Xp, tp), state_means(Xb, tb)
    diag["n_fine_e85"] = len(m8)
    diag["n_fine_e95"] = len(m9)

    # ---- Gate G: E8.5 -> E9.5 return ----
    d85, dinfo = fine_deltas(m9, m8, fwd, len(panel))
    dinfo.to_csv(RUN / "intermediates" / "gate_delta_table.tsv", sep="\t", index=False)
    diag["gate_n_zero_delta"] = int((dinfo["rule"] == "zero").sum())
    d85b, _ = fine_deltas(m9, m8, fwd, len(panel))
    assert all(np.array_equal(d85[s], d85b[s]) for s in d85)
    diag["rerun_deltas_identical"] = True
    Xg0 = np.empty_like(Xp)
    for i, s in enumerate(tp):
        Xg0[i] = Xp[i] + d85.get(str(s), np.zeros(len(panel), dtype=np.float32))
    Xg0 = np.clip(Xg0, 0.0, None)
    obs85 = prev.obs.copy()
    out_g0, res_g0 = write_candidate(Xg0, obs85, "G0_PLAIN", "gate_return_plain", {},
                                     RUN, "gate_G0_plain", resampled=False)
    diag["gate_G0_contract"] = res_g0.get("status")
    # G1: resample shifted E8.5 rows to exact E9.5 fine-state shares.
    sh9 = {s: float((tb == s).sum()) / len(tb) for s in sorted(set(tb.tolist()))}
    cnt9 = largest_remainder(sh9, len(tp))
    pool85: dict = {}
    for s in sorted(set(tp.tolist())):
        pool85[s] = np.flatnonzero(tp == s)
    # shifted rows keep their source state for pooling (bridge recipe: shift then match)
    ch9, plan9, rep9 = resample_bank(pool85, {s: cnt9.get(s, 0) for s in pool85}, RUN_SEED)
    plan9.to_csv(RUN / "intermediates" / "gate_share_plan.tsv", sep="\t", index=False)
    Xg1 = Xg0[ch9]
    obs_g1 = obs85.iloc[ch9].copy()
    seen: dict = {}
    nm = []
    for n in obs_g1.index.astype(str):
        k = seen.get(n, 0)
        nm.append(n if k == 0 else f"{n}__dup{k}")
        seen[n] = k + 1
    obs_g1.index = nm
    out_g1, res_g1 = write_candidate(Xg1, obs_g1, "G1_BRIDGE", "gate_return_bridged", {},
                                     RUN, "gate_G1_bridge", resampled=True)
    diag["gate_G1_contract"] = res_g1.get("status")
    m0 = run_scorer(out_g0, "G0_PLAIN", RUN)
    m1 = run_scorer(out_g1, "G1_BRIDGE", RUN)
    diag["gate_G0"] = {"de": m0["de_score"], "dir": m0["de_direction"]}
    diag["gate_G1"] = {"de": m1["de_score"], "dir": m1["de_direction"]}
    gate_pass = bool(m1["de_score"] > m0["de_score"] and m1["de_direction"] > m0["de_direction"])
    diag["gate_pass"] = gate_pass
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"gate_pass": gate_pass, "G0": diag["gate_G0"],
                      "G1": diag["gate_G1"]}, indent=1), flush=True)
    if not gate_pass:
        print("GATE FAIL: composition anchoring shows no return signal; no candidates.", flush=True)
        return 0

    # ---- Lanes E9.5 -> E10.5 ----
    # delta for E9.5 fine-state S = mean95(S) - mean85(match(S)); UNRESOLVED -> 0
    d95, dinfo95 = {}, []
    for s in sorted(m9):
        m = rev.get(s)
        if m is not None and m in m8:
            d95[s] = (m9[s] - m8[m]).astype(np.float32)
            dinfo95.append({"state": s, "match": m, "rule": "matched"})
        else:
            d95[s] = np.zeros(len(panel), dtype=np.float32)
            dinfo95.append({"state": s, "match": "UNRESOLVED", "rule": "zero"})
    pd.DataFrame(dinfo95).to_csv(RUN / "intermediates" / "lane_delta_table.tsv", sep="\t", index=False)
    diag["lane_n_zero_delta"] = int(sum(1 for r in dinfo95 if r["rule"] == "zero"))
    v4_names = [str(v) for v in v4.obs_names]
    base_names = [str(v) for v in base.obs_names]
    base_index = {n: i for i, n in enumerate(base_names)}
    assert all(n in base_index for n in v4_names)
    src_idx = np.array([base_index[n] for n in v4_names], dtype=np.int64)
    t_src = tb[src_idx]
    Xout_full = np.empty((N_CELLS, len(panel)), dtype=np.float32)
    for j, si in enumerate(src_idx):
        Xout_full[j] = Xb[si] + d95.get(str(t_src[j]), np.zeros(len(panel), dtype=np.float32))
    Xout_full = np.clip(Xout_full, 0.0, None)

    # L2: deltas only, v0004 multiset kept.
    out_l2, res_l2 = write_candidate(Xout_full, v4.obs.copy(), "L2_DELTA_ONLY",
                                     "fine_state_bridge_deltas_no_resample", {},
                                     RUN, "v0023_g0_t1_d4_delta_only", resampled=False)
    diag["L2_contract"] = res_l2.get("status")
    assert res_l2.get("status") in ("PASS", "pass"), f"L2 contract: {res_l2}"

    # L1: + shrunk share projection, resample bank.
    N95, N85 = len(tb), len(tp)
    sh85 = {s: float((tp == s).sum()) / N85 for s in set(tp.tolist())}
    proj = {}
    for s in sorted(set(tb.tolist())):
        m = rev.get(s)
        g = 1.0
        if m is not None and m in sh85 and sh85[m] > 0:
            g = (float((tb == s).sum()) / N95) / sh85[m]
        proj[s] = float((tb == s).sum()) / N95 * (1.0 + (g - 1.0) * SHRINK_K)
    tot = sum(proj.values())
    proj = {s: v / tot for s, v in proj.items()}
    pd.DataFrame([{"state": s, "share_e95": float((tb == s).sum()) / N95,
                   "share_proj": proj[s]} for s in sorted(proj)]
                 ).to_csv(RUN / "intermediates" / "share_projection.tsv", sep="\t", index=False)
    cnt10 = largest_remainder(proj, N_CELLS)
    bank_pool: dict = {}
    bank_states = np.array([str(t) for t in t_src])
    for s in sorted(set(bank_states.tolist())):
        bank_pool[s] = np.flatnonzero(bank_states == s)
    ch10, plan10, rep10 = resample_bank(bank_pool, {s: cnt10.get(s, 0) for s in bank_pool}, RUN_SEED)
    plan10.to_csv(RUN / "intermediates" / "lane_share_plan.tsv", sep="\t", index=False)
    (RUN / "intermediates" / "source_row_ledger.tsv").write_text(
        "lane\tout_row\tbank_row\tsource_obs_name\tfine_state\n" + "".join(
            f"L1\t{j}\t{int(b)}\t{v4_names[b]}\t{bank_states[b]}\n"
            for j, b in enumerate(ch10)))
    diag["L1_with_replacement_states"] = rep10
    Xl1 = Xout_full[ch10]
    obs_l1 = v4.obs.iloc[ch10].copy()
    seen = {}
    nm = []
    for n in obs_l1.index.astype(str):
        k = seen.get(n, 0)
        nm.append(n if k == 0 else f"{n}__dup{k}")
        seen[n] = k + 1
    obs_l1.index = nm
    diag["L1_dup_rows"] = int(sum(1 for n in nm if "__dup" in n))
    out_l1, res_l1 = write_candidate(Xl1, obs_l1, "L1_BRIDGE_K025",
                                     "fine_state_bridge_deltas_shrunk_shares_k025", {},
                                     RUN, "v0022_g0_t1_d4_bridge", resampled=True)
    diag["L1_contract"] = res_l1.get("status")
    assert res_l1.get("status") in ("PASS", "pass", "pass_with_deviation",
                                    "PASS_WITH_DEVIATION"), f"L1 contract: {res_l1}"

    m2 = run_scorer(out_l2, "L2_DELTA_ONLY", RUN)
    m1s = run_scorer(out_l1, "L1_BRIDGE_K025", RUN)
    diag["L2"] = {"de": m2["de_score"], "dir": m2["de_direction"]}
    diag["L1"] = {"de": m1s["de_score"], "dir": m1s["de_direction"]}
    diag["L2_promoted"] = bool(m2["de_score"] > LOCAL_DE and m2["de_direction"] > LOCAL_DIR)
    diag["L1_promoted"] = bool(m1s["de_score"] > LOCAL_DE and m1s["de_direction"] > LOCAL_DIR)
    diag["L1_sha"] = sha256(out_l1)
    diag["L2_sha"] = sha256(out_l2)
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps({"L1_promoted": diag["L1_promoted"], "L2_promoted": diag["L2_promoted"],
                      "L1": diag["L1"], "L2": diag["L2"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
