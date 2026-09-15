#!/usr/bin/env python3
"""B4-T1-R1 checks + local diagnostics for all four lanes.

Fail-fast order: validator + protected checks first, scorer last.
Writes: protected_checks/checks_<LANE>.json, source_row_ledger.tsv (per lane),
metrics/lane_comparison.tsv. No uploads, no INDEX edits.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
IFACE = REPO / "docs" / "batch3" / "interfaces"
if str(IFACE) not in sys.path:
    sys.path.insert(0, str(IFACE))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from virtual_embryo_tools import contract_io

RUN = REPO / "artifacts/batch4/B4-T1-R1-CONSERVATIVE-FAMILY-20260904-v1"
SEED = 20260904
PANEL = [l.strip() for l in (REPO / "data" / "gene_panel" / "T1__val.genes.txt").read_text().splitlines() if l.strip()]
SCORER_LOCK = REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0009 = REPO / "artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/candidates/T1_val/L0_EXACT_FLOOR/submission.h5ad"

LANES = ["L1_DAMP050", "L2_POPMIX050", "L3_MASSGRAFT025", "L4_MASSGRAFT050"]


def sha256(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_cand(lane: str) -> ad.AnnData:
    return ad.read_h5ad(RUN / "candidates" / "T1_val" / lane / "submission.h5ad")


def check_lane(lane: str, parent: Path, parent_sha: str) -> dict:
    t0 = time.time()
    cand_path = RUN / "candidates" / "T1_val" / lane / "submission.h5ad"
    rep = dict(contract_io.validate_h5ad_contract(
        cand_path, task="T1", board="val", scorer_lock=SCORER_LOCK,
        parent_path=parent, parent_sha256=parent_sha))
    status = rep.get("status")
    a = ad.read_h5ad(cand_path)
    checks = {
        "lane": lane, "contract_status": status,
        "n_obs": int(a.n_obs), "n_vars": int(a.n_vars),
        "n_obs_ok": a.n_obs == 5118, "n_vars_ok": a.n_vars == 32285,
        "gene_order_exact": [str(v) for v in a.var_names] == PANEL,
        "finite_nonneg": bool(np.isfinite(a.X.data if sparse.issparse(a.X) else np.asarray(a.X)).all()
                              and (np.asarray(a.X.data if sparse.issparse(a.X) else np.asarray(a.X)) >= 0).all()),
        "no_obsm": len(a.obsm.keys()) == 0,
        "obs_cols": list(a.obs.columns),
        "zero_fraction": float((np.asarray(a.X.data if sparse.issparse(a.X)
                                           else np.asarray(a.X)) == 0).mean()
                               if not sparse.issparse(a.X) else
                               (1.0 - float(a.X.nnz) / (a.n_obs * a.n_vars))),
        "sha256": sha256(cand_path),
        "wall_s": time.time() - t0,
    }
    lib = np.asarray(a.X.sum(axis=1)).ravel()
    checks["lib_mean"] = float(lib.mean())
    checks["lib_std"] = float(lib.std())
    # Graft lanes change the row multiset by pre-declared design (mass graft IS the
    # treatment; scored precedent v0005/v0006 likewise differ from their parent rows).
    # The only acceptable deviation is obs-identity vs the locked parent; every
    # server-contract dimension must still PASS.
    allowed = {"candidate obs_names/order does not exactly match the locked parent",
               "candidate obs metadata does not exactly match the locked parent"}
    errs = set(rep.get("errors", []))
    deviation = None
    if lane in ("L3_MASSGRAFT025", "L4_MASSGRAFT050") and errs and errs <= allowed:
        deviation = ("protected_parent obs-identity FAIL_BY_DESIGN: composition change is "
                     "the declared treatment; rows traceable via source_row_ledger; "
                     "server-contract dimensions all PASS")
    (RUN / "protected_checks").mkdir(exist_ok=True)
    (RUN / "protected_checks" / f"checks_{lane}.json").write_text(json.dumps(
        {"contract_report": rep, "protected": checks, "deviation": deviation}, indent=1, default=str))
    print(json.dumps(checks, indent=1), flush=True)
    if str(status).lower() != "pass":
        dev = (RUN / "protected_checks" / f"checks_{lane}.json")
        dev_note = json.loads(dev.read_text()).get("deviation")
        if not dev_note:
            raise RuntimeError(f"contract {status} for {lane}")
        print(f"{lane}: accepted deviation: {dev_note}", flush=True)
    for k in ("n_obs_ok", "n_vars_ok", "gene_order_exact", "finite_nonneg", "no_obsm"):
        if not checks[k]:
            raise RuntimeError(f"protected check {k} FAIL for {lane}")
    return checks


def build_ledgers() -> dict:
    """Re-derive source-row ledgers deterministically; assert names match candidates."""
    from scripts.batch4.t1_conservative_family import graft_counts  # noqa
    led = {}
    # L1: same rows as v0004 (same seed/shares)
    n4 = [str(v) for v in ad.read_h5ad(V0004, backed="r").obs_names]
    n1 = [str(v) for v in ad.read_h5ad(
        RUN / "candidates" / "T1_val" / "L1_DAMP050" / "submission.h5ad", backed="r").obs_names]
    assert n1 == n4, "L1 rows differ from v0004"
    led["L1_DAMP050"] = "identical_to_v0004_rows"
    # L2: v0009 order, first 2559 copy / rest shifted
    n9 = [str(v) for v in ad.read_h5ad(V0009, backed="r").obs_names]
    n2 = [str(v) for v in ad.read_h5ad(
        RUN / "candidates" / "T1_val" / "L2_POPMIX050" / "submission.h5ad", backed="r").obs_names]
    assert n2 == n9, "L2 rows differ from v0009"
    df2 = pd.DataFrame({"out_row": range(len(n2)), "source": ["v0009_copy"] * 2559 + ["v0009_shift"] * 2559,
                        "source_obs_name": n2, "source_file": "v0009_exact_floor"})
    df2.to_csv(RUN / "intermediates" / "source_row_ledger_L2.tsv", sep="\t", index=False)
    led["L2_POPMIX050"] = "v0009_order_2559_copy_2559_shift"
    # L3/L4: re-derive graft sampling, assert names match
    f4 = ad.read_h5ad(V0004, backed="r")
    names4 = [str(v) for v in f4.obs_names]
    types4 = np.asarray(f4.obs["celltype"].astype(str))
    f4.file.close()
    mass = pd.read_csv(REPO / "artifacts/tool_integration/T1-S2-MOSCOT-DECODER-20260902-v1/intermediates/state_mass.tsv", sep="\t")
    mass = mass[mass["board"] == "T1:val"]
    p_mos_raw = {str(r["state"]): float(r["shrunk_probability"]) for _, r in mass.iterrows()}
    states4 = sorted(set(types4.tolist()))
    in_bank = [s for s in p_mos_raw if s in set(states4)]
    renorm = sum(p_mos_raw[s] for s in in_bank)
    p_mos = {s: p_mos_raw[s] / renorm for s in in_bank}
    p_e95 = {s: float((types4 == s).sum()) / len(types4) for s in states4}
    for lane, w in (("L3_MASSGRAFT025", 0.25), ("L4_MASSGRAFT050", 0.50)):
        # Fresh stream per lane: build runs each lane in its own process.
        rng = np.random.default_rng(SEED)
        counts = graft_counts(p_e95, p_mos, states4, 5118, w)
        names_new, src_idx = [], []
        for s in states4:
            pool = np.flatnonzero(types4 == s)
            k = counts[s]
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=(k > len(pool)))])
            names_new.extend([names4[i] for i in sel])
            src_idx.extend(sel.tolist())
        seen: dict = {}
        out_names = []
        for nm in names_new:
            k = seen.get(nm, 0)
            out_names.append(nm if k == 0 else f"{nm}__dup{k}")
            seen[nm] = k + 1
        cand_names = [str(v) for v in ad.read_h5ad(
            RUN / "candidates" / "T1_val" / lane / "submission.h5ad", backed="r").obs_names]
        assert cand_names == out_names, f"{lane} ledger mismatch"
        pd.DataFrame({"out_row": range(len(out_names)), "source_v0004_row": src_idx,
                      "source_obs_name": names_new, "out_obs_name": out_names,
                      "source_file": "v0004_strict_shift"}).to_csv(
            RUN / "intermediates" / f"source_row_ledger_{lane}.tsv", sep="\t", index=False)
        led[lane] = f"graft_w{w}_rederived_names_match"
    (RUN / "intermediates" / "ledger_check.json").write_text(json.dumps(led, indent=1))
    print(json.dumps(led, indent=1), flush=True)
    return led


def run_scorer(lane: str) -> dict:
    cand = RUN / "candidates" / "T1_val" / lane / "submission.h5ad"
    out = RUN / "metrics" / f"scorer_{lane}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
           "python", "third_party/veckit/score_h5ad.py", "--task", "T1",
           "--input", str(cand), "--target", "data/E9.5_RNA.h5ad",
           "--reference", "data/E8.5_RNA.h5ad", "--seed", str(SEED), "--out", str(out)]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"scorer failed for {lane}: {r.stderr[-1500:]}")
    m = json.loads(out.read_text())["metrics"]
    keep = {k: m.get(k) for k in ("de_score", "de_direction", "energy_distance", "mmd_u",
                                  "variogram", "pb_rel_err", "library_size_ratio",
                                  "variance_ratio", "composition_JSD", "pseudobulk_pearson")}
    keep["wall_s"] = time.time() - t0
    (RUN / "metrics" / f"scorer_{lane}_slim.json").write_text(json.dumps(keep, indent=1))
    print(lane, json.dumps(keep, sort_keys=True), flush=True)
    return keep


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["checks", "ledgers", "scorer", "compare"])
    ap.add_argument("--lane", default=None)
    args = ap.parse_args()
    parents = {"L1_DAMP050": (V0004, "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd")}
    import hashlib
    h = hashlib.sha256()
    with open(V0009, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    parents["L2_POPMIX050"] = (V0009, h.hexdigest())
    parents["L3_MASSGRAFT025"] = (V0004, parents["L1_DAMP050"][1])
    parents["L4_MASSGRAFT050"] = (V0004, parents["L1_DAMP050"][1])
    if args.command == "checks":
        for lane in LANES:
            check_lane(lane, *parents[lane])
    elif args.command == "ledgers":
        build_ledgers()
    elif args.command == "scorer":
        run_scorer(args.lane)
    elif args.command == "compare":
        rows = []
        for lane in LANES:
            c = json.load(open(RUN / "protected_checks" / f"checks_{lane}.json"))["protected"]
            s = json.load(open(RUN / "metrics" / f"scorer_{lane}_slim.json"))
            rows.append({"lane": lane, "sha256": c["sha256"], "contract": c["contract_status"],
                         "zero_frac": round(c["zero_fraction"], 4), "lib_mean": round(c["lib_mean"], 3),
                         **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}})
        pd.DataFrame(rows).to_csv(RUN / "metrics" / "lane_comparison.tsv", sep="\t", index=False)
        print(pd.DataFrame(rows).to_string(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
