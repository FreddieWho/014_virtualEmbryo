#!/usr/bin/env python3
"""B4-T1-R1 conservative family: damp / popmix / mass-graft lanes on frozen parents.

Lanes (board T1:val, n_obs=5118, 32285 genes, seed 20260904 unless noted):
  L1_DAMP050   X = X_E9.5 + 0.5*Delta_c  (strict per-type shift via run_t1_shift)
  L2_POPMIX050 2559 exact copy-last rows + 2559 strict-shifted rows, disjoint pools
  L3_MASSGRAFT025 v0004 expression rows resampled to 0.75*E9.5 + 0.25*moscot shares
  L4_MASSGRAFT050 v0004 expression rows resampled to 0.50*E9.5 + 0.50*moscot shares

Frozen: v0004 (recipe weight=1/unmapped=zero/comp=none/damp=1/seed=20260822),
v0009 floor rows (pool universe), moscot shrunk mass, crosswalk (reference only).
No refit, no new states, no external data, no target data.
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

from scripts.t1_temporal_model import _load_board_input, _masked_means, run_t1_shift


def _contract_io():
    """Direct interface import (avoids the sklearn chain in t2_j1_fgw_assignment)."""
    iface = REPO / "docs" / "batch3" / "interfaces"
    if str(iface) not in sys.path:
        sys.path.insert(0, str(iface))
    from virtual_embryo_tools import contract_io
    return contract_io

TASK_ID = "B4-T1-R1-CONSERVATIVE-FAMILY"
BOARD = "T1:val"
RUN_SEED = 20260904
PANEL = REPO / "data" / "gene_panel" / "T1__val.genes.txt"
E85 = REPO / "data" / "E8.5_RNA.h5ad"
E95 = REPO / "data" / "E9.5_RNA.h5ad"
V0004 = REPO / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
V0004_SHA = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
V0009 = REPO / "artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/candidates/T1_val/L0_EXACT_FLOOR/submission.h5ad"
MASS_TSV = REPO / "artifacts/tool_integration/T1-S2-MOSCOT-DECODER-20260902-v1/intermediates/state_mass.tsv"
XWALK_TSV = REPO / "artifacts/tool_integration/T1-PRE-HARMONIZE-20260902-v1/intermediates/state_crosswalk.tsv"
NORMALIZATION = "log1p_normalized"
N_CELLS = 5118

LANES = ["L1_DAMP050", "L2_POPMIX050", "L3_MASSGRAFT025", "L4_MASSGRAFT050"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_parents() -> dict:
    out = {"v0004_sha_ok": sha256(V0004) == V0004_SHA, "v0004_sha": sha256(V0004)}
    if not out["v0004_sha_ok"]:
        raise RuntimeError("BLOCKED_INPUT: v0004 hash drift")
    out["v0009_sha"] = sha256(V0009)
    out["mass_sha"] = sha256(MASS_TSV)
    out["xwalk_sha"] = sha256(XWALK_TSV)
    mass = pd.read_csv(MASS_TSV, sep="\t")
    assert list(mass.columns)[:3] == ["board", "target_stage", "state"], mass.columns.tolist()
    mass = mass[mass["board"] == "T1:val"].copy()
    dup = mass["state"].astype(str)
    if dup.duplicated().any():
        raise RuntimeError("BLOCKED_INPUT: duplicate states in T1:val mass rows: "
                           + str(dup[dup.duplicated()].unique().tolist()))
    out["mass_states"] = sorted(dup.tolist())
    out["mass_board"] = "T1:val"
    return out


def pure_deltas() -> tuple[dict, list, object, object]:
    """Strict per-type Delta_c = mean(E9.5,c) - mean(E8.5,c), missing -> 0."""
    panel = [l.strip() for l in PANEL.read_text().splitlines() if l.strip()]
    prev = _load_board_input(E85, PANEL, needs_coords=False)
    base = _load_board_input(E95, PANEL, needs_coords=False)
    prev_means, _ = _masked_means(prev.X, np.asarray(prev.obs["celltype"].astype(str)))
    base_means, _ = _masked_means(base.X, np.asarray(base.obs["celltype"].astype(str)))
    template = next(iter(base_means.values()))
    zeros = np.zeros_like(template, dtype=np.float32)
    missing = []
    deltas = {}
    for ct in np.unique(np.asarray(base.obs["celltype"].astype(str))):
        ct = str(ct)
        if ct in prev_means:
            deltas[ct] = (base_means[ct] - prev_means[ct]).astype(np.float32)
        else:
            deltas[ct] = zeros.copy()
            missing.append(ct)
    print(json.dumps({"e95_only_types_delta_zero": missing}), flush=True)
    return deltas, panel, prev, base


def build_L1(run_dir: Path, diag: dict) -> Path:
    out = run_dir / "candidates" / "T1_val" / "L1_DAMP050" / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Parent fidelity gate: damp=1.0 must reproduce v0004 bytes.
    repro = run_dir / "intermediates" / "repro_damp100.h5ad"
    repro.parent.mkdir(parents=True, exist_ok=True)
    run_t1_shift(board="val", previous_path=E85, base_path=E95, output_path=repro,
                 n_cells=N_CELLS, seed=20260822, damp=1.0, celltype_weight=1.0,
                 unmapped_delta="zero", composition_extrap="none", overwrite=True)
    diag["repro_damp100_sha"] = sha256(repro)
    diag["repro_matches_v0004"] = diag["repro_damp100_sha"] == V0004_SHA
    if not diag["repro_matches_v0004"]:
        raise RuntimeError("BLOCKED_INPUT: damp=1.0 does not reproduce v0004; recipe drift")
    repro.unlink()
    run_t1_shift(board="val", previous_path=E85, base_path=E95, output_path=out,
                 n_cells=N_CELLS, seed=20260822, damp=0.5, celltype_weight=1.0,
                 unmapped_delta="zero", composition_extrap="none", overwrite=False)
    # Contract gate: new files must carry explicit normalization provenance
    # (legacy v0004 predates ve_contract). Expression bytes must not change.
    a = ad.read_h5ad(out)
    x_digest = hashlib.sha256(np.ascontiguousarray(a.X.toarray() if sparse.issparse(a.X) else np.asarray(a.X)).tobytes()).hexdigest()
    a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": NORMALIZATION}
    a.uns["ve_b4_t1_r1"] = json.dumps({
        "atom_id": TASK_ID, "lane": "L1_DAMP050", "method": "damp_0.5_strict_shift",
        "parent": "v0004 recipe", "seed": 20260822, "target_used": False}, sort_keys=True)
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    a.write_h5ad(tmp)
    Path(tmp).replace(out)
    b = ad.read_h5ad(out)
    bx = np.ascontiguousarray(b.X.toarray() if sparse.issparse(b.X) else np.asarray(b.X))
    assert hashlib.sha256(bx.tobytes()).hexdigest() == x_digest, "L1 expression changed by metadata patch"
    diag["ve_contract_added"] = True
    diag["expression_unchanged_by_patch"] = True
    return out


def build_L2(run_dir: Path, deltas: dict, panel: list, diag: dict) -> Path:
    out = run_dir / "candidates" / "T1_val" / "L2_POPMIX050" / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    f9 = ad.read_h5ad(V0009)
    names9 = [str(v) for v in f9.obs_names]
    types9 = np.asarray(f9.obs["celltype"].astype(str))
    n = len(names9)
    assert n == N_CELLS
    copy_pos = np.arange(2559)
    shift_pos = np.arange(2559, N_CELLS)
    X9 = f9.X.toarray() if sparse.issparse(f9.X) else np.asarray(f9.X, dtype=np.float32)
    Xnew = X9.copy()
    clip_pre = None
    for ct in np.unique(types9[shift_pos]):
        m = (types9 == ct) & (np.arange(n) >= 2559)
        Xnew[m] += deltas[str(ct)]
        if clip_pre is None:
            clip_pre = (Xnew[m] < 0)
    shifted = int(shift_pos.size)
    np.clip(Xnew, 0, None, out=Xnew)
    Xnew = Xnew.astype(np.float32)
    # consistency: rows also present in v0004 should carry v0004 expression
    f4 = ad.read_h5ad(V0004, backed="r")
    names4 = [str(v) for v in f4.obs_names]
    idx4 = {nm: i for i, nm in enumerate(names4)}
    overlap = [j for j in shift_pos if names9[j] in idx4]
    maxdiff = 0.0
    if overlap:
        X4 = f4.X.toarray() if sparse.issparse(f4.X) else np.asarray(f4.X)
        rows4 = np.array([idx4[names9[j]] for j in overlap])
        maxdiff = float(np.abs(X4[rows4] - Xnew[np.array(overlap)]).max())
        f4.file.close()
    else:
        f4.file.close()
    diag["shift_pool_overlap_v0004"] = len(overlap)
    diag["shift_pool_maxdiff_vs_v0004"] = maxdiff
    contract_io = _contract_io()
    contract_io.write_candidate_from_parent(
        parent_path=V0009, output_path=out, expression=Xnew,
        row_names=names9, normalization=NORMALIZATION,
        parent_sha256=sha256(V0009),
        metadata_updates={"ve_b4_t1_r1": json.dumps({
            "atom_id": TASK_ID, "lane": "L2_POPMIX050", "method": "popmix_50_copy_50_shift",
            "pool": "v0009_exact_floor_rows", "copy_n": 2559, "shift_n": shifted,
            "shift_rule": "pure_Delta_damp_1.0_clip0", "seed": RUN_SEED,
            "target_used": False}, sort_keys=True)},
    )
    diag["copy_rows"] = 2559
    diag["shift_rows"] = shifted
    return out


def graft_counts(p_e95: dict, p_mos: dict, states: list, total: int, w_mos: float) -> dict:
    raw = {}
    for s in states:
        pe = p_e95.get(s, 0.0)
        pm = p_mos.get(s, None)
        raw[s] = (1.0 - w_mos) * pe + w_mos * (pm if pm is not None else pe)
    counts = {s: int(v * total) for s, v in raw.items()}
    deficit = total - sum(counts.values())
    rema = sorted(states, key=lambda s: (raw[s] * total - counts[s], s), reverse=True)
    for i in range(deficit):
        counts[rema[i % len(rema)]] += 1
    assert sum(counts.values()) == total
    return counts


def build_graft(run_dir: Path, lane: str, w_mos: float, diag: dict) -> Path:
    out = run_dir / "candidates" / "T1_val" / lane / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    f4 = ad.read_h5ad(V0004)
    names4 = [str(v) for v in f4.obs_names]
    types4 = np.asarray(f4.obs["celltype"].astype(str))
    mass = pd.read_csv(MASS_TSV, sep="\t")
    mass = mass[mass["board"] == "T1:val"].copy()
    if mass["state"].astype(str).duplicated().any():
        raise RuntimeError("BLOCKED_INPUT: duplicate T1:val mass states")
    p_mos_raw = {str(r["state"]): float(r["shrunk_probability"]) for _, r in mass.iterrows()}
    states4 = sorted(set(types4.tolist()))
    in_bank = [s for s in p_mos_raw if s in set(states4)]
    dropped = sorted(set(p_mos_raw) - set(states4))
    renorm = sum(p_mos_raw[s] for s in in_bank)
    p_mos = {s: p_mos_raw[s] / renorm for s in in_bank}
    p_e95 = {s: float((types4 == s).sum()) / len(types4) for s in states4}
    counts = graft_counts(p_e95, p_mos, states4, N_CELLS, w_mos)
    rng = np.random.default_rng(RUN_SEED)
    order = np.argsort(np.asarray([states4.index(t) for t in types4]), kind="stable")
    chosen, plan_rows = [], []
    replaced = {}
    for s in states4:
        pool = np.flatnonzero(types4 == s)
        k = counts[s]
        if k <= len(pool):
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=False)] if k < len(pool)
                          else pool)
            wr = False
        else:
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=True)])
            wr = True
            replaced[s] = {"need": k, "have": int(len(pool))}
        chosen.extend(sel.tolist())
        plan_rows.append({"state": s, "e95_n": int((types4 == s).sum()),
                          "target_n": k, "with_replacement": wr,
                          "moscot_shrunk": p_mos.get(s, None)})
    chosen = np.asarray(chosen, dtype=np.int64)
    assert len(set(chosen.tolist())) == len(chosen) or replaced, "unexpected dup without replacement flag"
    names_new = [names4[i] for i in chosen]
    # Contract gate: obs_names must be unique. First occurrence keeps the source
    # name; later copies get deterministic __dup{k} suffixes. Traceability lives
    # in source_row_ledger (source_obs_name column keeps the original).
    seen: dict = {}
    out_names = []
    for nm in names_new:
        k = seen.get(nm, 0)
        out_names.append(nm if k == 0 else f"{nm}__dup{k}")
        seen[nm] = k + 1
    assert len(set(out_names)) == len(out_names)
    names_new = out_names
    diag[f"{lane}_dup_suffix_rows"] = int(sum(1 for n in out_names if "__dup" in n))
    X4 = f4.X.toarray() if sparse.issparse(f4.X) else np.asarray(f4.X, dtype=np.float32)
    Xnew = np.ascontiguousarray(X4[chosen].astype(np.float32))
    plan = pd.DataFrame(plan_rows)
    plan_path = run_dir / "intermediates" / "state_mass_plan.tsv"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    if lane == "L3_MASSGRAFT025":
        plan.to_csv(plan_path, sep="\t", index=False)
    diag[f"{lane}_dropped_mass_states"] = dropped
    diag[f"{lane}_with_replacement_states"] = replaced
    diag[f"{lane}_n_rows"] = int(len(chosen))
    # Graft lanes change the row multiset, so the core writer's row-identity gate
    # (row_names must equal parent obs_names/order) cannot apply. Construct from
    # v0004 by row indexing -- obs/var/uns follow the sampled rows, preserving
    # identities -- then mirror the writer's own guarantees explicitly below.
    import tempfile
    import os
    assert np.isfinite(Xnew).all() and (Xnew >= 0).all(), "graft X must be finite/nonneg"
    bank = f4[chosen].copy()
    assert [str(v) for v in bank.obs_names] == [n.split("__dup")[0] for n in names_new]
    bank.obs_names = names_new
    bank.X = np.ascontiguousarray(Xnew, dtype=np.float32)
    bank.obsm.clear()
    bank.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": NORMALIZATION}
    bank.uns["ve_b4_t1_r1"] = json.dumps({
        "atom_id": TASK_ID, "lane": lane, "method": f"mass_graft_{w_mos}",
        "bank": "v0004_strict_shift_rows", "bank_sha256": V0004_SHA,
        "sampling_seed": RUN_SEED, "row_multiset_changed": True,
        "writer_note": "row-indexed construction (writer row-identity gate N/A); "
                         "contract validated independently via validate_h5ad_contract",
        "target_used": False}, sort_keys=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"Output already exists: {out}")
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    bank.write_h5ad(tmp)
    Path(tmp).replace(out)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["verify", "build", "smoke"])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--lane", default=None)
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    if args.command == "verify":
        print(json.dumps(verify_parents(), indent=1, sort_keys=True))
    elif args.command == "smoke":
        d = verify_parents()
        deltas, panel, prev, base = pure_deltas()
        print(json.dumps({"parents_ok": True, "n_delta_types": len(deltas),
                          "panel_genes": len(panel), "mass_states": len(d["mass_states"])}, indent=1))
    elif args.command == "build":
        t0 = time.time()
        diag: dict = {"lane": args.lane, "t_start": t0}
        if args.lane == "L1_DAMP050":
            out = build_L1(run_dir, diag)
        elif args.lane == "L2_POPMIX050":
            deltas, panel, prev, base = pure_deltas()
            out = build_L2(run_dir, deltas, panel, diag)
        elif args.lane in ("L3_MASSGRAFT025", "L4_MASSGRAFT050"):
            w = 0.25 if args.lane == "L3_MASSGRAFT025" else 0.50
            out = build_graft(run_dir, args.lane, w, diag)
        else:
            raise ValueError("unknown lane")
        diag["output"] = str(out)
        diag["sha256"] = sha256(out)
        diag["wall_s"] = time.time() - t0
        (run_dir / "intermediates").mkdir(exist_ok=True)
        (run_dir / "intermediates" / f"diag_{args.lane}.json").write_text(json.dumps(diag, indent=1))
        print(json.dumps(diag, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
