#!/usr/bin/env python3
"""B4-T3-R1 genotype-only ablation: L1 all-cell Gata4 zero, L2 hard-lineage zero.

L3 (Gata4 soft + Gata6 F/+) requires local authoritative confirmation that the
validation condition includes Gata6 F/+; the board index says target_ko=gata4
and OFFICIAL_SYNC lists only Gata4/β-catenin KO conditions -> L3 is
BLOCKED_CONDITION_NOT_CONFIRMED (no third lane substituted).

Parent: P0 exact wt_identity v0008 (provisional tag: floor parity unresolved).
Lineage: frozen B2-T3-A1 lineage_gate.tsv joined on obs celltype (official_state).
Zeroing Gata4=0 is domain-invariant (log1p(0)=0=raw 0). Coordinates/cell order/
n_obs bitwise exact; only the declared gene changes.
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

TASK_ID = "B4-T3-R1-GENOTYPE-ONLY-ABLATION"
BOARD = "T3:gata4"
V0008 = REPO / "submissions/candidates/T3_gata4/v0008_b4p0_l0_exact_floor/submission.h5ad"
V0008_SHA = "478786034343cc3ed1a604cd494ab2134751f4a1f4696204f9d105e404bdbef3"
GATE_TSV = REPO / "artifacts/atomic_batch2/B2-T3-A1/lineage_gate.tsv"
GATE_SHA = "from_disk_at_verify"
LANES = ["L1_GATA4_ZERO_ALL", "L2_GATA4_ZERO_HARD_LINEAGE"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify() -> dict:
    out = {"v0008_sha_ok": sha256(V0008) == V0008_SHA, "v0008_sha": sha256(V0008)}
    if not out["v0008_sha_ok"]:
        raise RuntimeError("BLOCKED_INPUT: v0008 hash drift")
    out["gate_sha"] = sha256(GATE_TSV)
    gate = pd.read_csv(GATE_TSV, sep="\t")
    out["gate_states"] = sorted(gate["official_state"].astype(str).tolist())
    a = ad.read_h5ad(V0008, backed="r")
    ctypes = sorted(set(str(v) for v in a.obs["celltype"]))
    a.file.close()
    out["parent_states"] = ctypes
    out["states_missing_gate"] = sorted(set(ctypes) - set(out["gate_states"]))
    if out["states_missing_gate"]:
        raise RuntimeError("BLOCKED_INPUT: parent states without lineage gate: "
                           + str(out["states_missing_gate"]))
    out["gata6_precheck"] = {
        "board_index_target_ko": "gata4",
        "official_conditions": "Gata4 KO and beta-catenin KO only (OFFICIAL_SYNC)",
        "gata6_f_plus_confirmed": False,
        "verdict": "BLOCKED_CONDITION_NOT_CONFIRMED",
    }
    return out


def build_lane(run_dir: Path, lane: str) -> dict:
    t0 = time.time()
    out = run_dir / "candidates" / "T3_gata4" / lane / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(str(out))
    gate = pd.read_csv(GATE_TSV, sep="\t")
    pmap = {str(r["official_state"]): float(r["p_mesp1_lineage"]) for _, r in gate.iterrows()}
    a = ad.read_h5ad(V0008)
    var = [str(v) for v in a.var_names]
    gi4, gi6 = var.index("Gata4"), var.index("Gata6")
    types = np.asarray(a.obs["celltype"].astype(str))
    p = np.array([pmap[t] for t in types])
    if lane == "L1_GATA4_ZERO_ALL":
        mask = np.ones(len(types), dtype=bool)
    else:
        mask = p >= 0.5
    X = a.X.toarray() if sparse.issparse(a.X) else np.asarray(a.X)
    X = np.ascontiguousarray(X, dtype=np.float32)
    g4_before = X[:, gi4].copy()
    n_changed = int(mask.sum())
    frac_nonzero_changed = float((g4_before[mask] != 0).mean()) if n_changed else 0.0
    X[mask, gi4] = 0.0
    # non-target exactness
    keep = np.ones(X.shape[1], dtype=bool)
    keep[gi4] = False
    X0 = a.X.toarray() if sparse.issparse(a.X) else np.asarray(a.X)
    assert np.array_equal(np.asarray(X0)[:, keep], X[:, keep]), "non-target gene changed"
    assert np.array_equal(np.asarray(X0)[:, gi6], X[:, gi6]), "Gata6 changed"
    assert np.isfinite(X).all() and (X >= 0).all()
    coords_before = np.asarray(a.obsm["spatial_3D"])
    a.X = X
    assert np.array_equal(np.asarray(a.obsm["spatial_3D"]), coords_before), "coords changed"
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    a.uns["ve_b4_t3_r1"] = json.dumps({
        "atom_id": TASK_ID, "lane": lane, "method": "gata4_zero_all" if lane.startswith("L1") else "gata4_zero_hard_lineage",
        "parent": "v0008_exact_floor_provisional", "parent_sha256": V0008_SHA,
        "lineage_gate": "p_mesp1_lineage>=0.5 (frozen B2-T3-A1)", "gata6_untouched": True,
        "target_used": False}, sort_keys=True)
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    a.write_h5ad(tmp)
    Path(tmp).replace(out)
    diag = {"lane": lane, "output": str(out), "sha256": sha256(out),
            "n_cells": int(a.n_obs), "n_changed": n_changed,
            "frac_nonzero_changed": frac_nonzero_changed,
            "gata4_col_sum_before": float(g4_before.sum()),
            "gata4_col_sum_after": float(X[:, gi4].sum()),
            "coords_exact": True, "n_obs_exact": a.n_obs == 7449,
            "wall_s": time.time() - t0}
    (run_dir / "intermediates").mkdir(exist_ok=True)
    (run_dir / "intermediates" / f"diag_{lane}.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps(diag, indent=1, sort_keys=True), flush=True)
    return diag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["verify", "build"])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--lane", default=None)
    args = ap.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify(), indent=1, sort_keys=True))
    else:
        if args.lane == "L3_GATA4_ZERO_SOFT_GATA6":
            raise RuntimeError("BLOCKED_CONDITION_NOT_CONFIRMED: Gata6 F/+ not confirmed; refusing substitute lane")
        build_lane(Path(args.run_dir), args.lane)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
