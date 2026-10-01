"""Build full-scope (5118 x 32285) T1 mix candidates + contract validation.

Lanes (frozen):
  L1 B_s1: 70/30 v0035-final x v0038-final, seed 20260921 (s2mix convention)
  L2 B_s2: 70/30 v0035-final x v0038-final, seed 20261023 (report-median-seed link)
  L3 C_s1: 70/30 v0036-final x v0038-final, seed 20260921
Construction mirrors server-winning s2mix exactly (stratified whole-row
mixture_indices, no-replacement draw per side, frozen seed), only the pair changes.
Parent for contract path: v0035 (seven precedent), row_names = parent obs_names,
obs inherited, donor types in predicted_celltype metadata + design JSON.

Reads (read-only): submissions/candidates finals, INDEX (for parent sha),
SCORER_LOCK, contract_io. Writes (new dirs only):
  artifacts/autoresearch/t1-20261002-v1/final_<lane>/submission.h5ad + CONTRACT.json
No INDEX/registry/coordination writes (coordinator scope).
"""
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import anndata as ad

sys.path.insert(0, "scripts/t1_three")
from ops import mixture_indices  # noqa

ROOT = Path(".").resolve()
OUTROOT = ROOT / "artifacts/autoresearch/t1-20261002-v1"
LOCK = ROOT / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
sys.path.insert(0, str(ROOT / "docs/batch3/interfaces"))
from virtual_embryo_tools.contract_io import (  # noqa
    write_candidate_from_parent,
    validate_h5ad_contract,
)

LANES = [
    ("L1", "35x38", "v0035_three_r2joint", "v0038_seven_n2covot", 0.7, 20260921, "v0049"),
    ("L2", "35x38", "v0035_three_r2joint", "v0038_seven_n2covot", 0.7, 20261023, "v0050"),
    ("L3", "36x38", "v0036_three_r3mix", "v0038_seven_n2covot", 0.7, 20260921, "v0051"),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(4 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dense(X):
    from scipy import sparse

    return np.asarray(X.toarray() if sparse.issparse(X) else X, dtype=np.float32)


def indexed(version):
    with open(ROOT / "submissions/INDEX.tsv") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    hits = [r for r in rows if r["board"] == "T1:val" and r["version"] == version]
    assert len(hits) == 1, version
    return hits[0]


def main():
    parent_row = indexed("v0035")
    parent_path = ROOT / parent_row["path"]
    assert sha(parent_path) == parent_row["sha256"], "parent drift — STOP"
    results = []
    for lane, pair, va, vb, frac, seed, proposed in LANES:
        t0 = time.time()
        pa = ad.read_h5ad(ROOT / "submissions/candidates/T1_val" / va / "submission.h5ad")
        pb = ad.read_h5ad(ROOT / "submissions/candidates/T1_val" / vb / "submission.h5ad")
        assert pa.shape == (5118, 32285) and pb.shape == (5118, 32285)
        assert (pa.obs_names == pb.obs_names).all()
        ta = pa.obs["celltype"].astype(str).to_numpy()
        tb = pb.obs["celltype"].astype(str).to_numpy()
        Xa, Xb = dense(pa.X), dense(pb.X)
        sides, rows = mixture_indices(ta, tb, frac, seed)
        A_from = int((sides == 0).sum())
        out = np.empty_like(Xa)
        pt = np.empty(len(out), dtype=object)
        ea = eb = 0
        for i, (s, r) in enumerate(zip(sides.tolist(), rows.tolist())):
            if s == 0:
                out[i] = Xa[r]
                pt[i] = ta[r]
                ea += 1
            else:
                out[i] = Xb[r]
                pt[i] = tb[r]
                eb += 1
        assert ea == A_from and eb == len(out) - A_from
        assert np.isfinite(out).all() and (out >= 0).all()
        # donor-origin audit: rows must come verbatim from scored finals
        d = OUTROOT / f"final_{lane}_{pair}_s{seed}"
        d.mkdir(parents=True, exist_ok=False)
        op = d / "submission.h5ad"
        design = {
            "lane": lane,
            "pair": pair,
            "fraction_A": frac,
            "seed": seed,
            "parents": [va, vb],
            "parent_for_contract": "v0035",
            "method": "stratified whole-row mixture (s2mix construction, new pair)",
            "target_used": False,
            "report_analog": "T1-7/T1-8 (median>=baseline, guardrail-clean)",
            "proposed_version": proposed + "_PROPOSED_pending_coordinator",
        }
        write_candidate_from_parent(
            parent_path=parent_path,
            output_path=op,
            expression=out,
            row_names=list(pa.obs_names),
            normalization="log1p_normalized",
            parent_sha256=parent_row["sha256"],
            metadata_updates={
                "predicted_celltype": np.asarray(pt, dtype=str),
                "row_identity_note": "synthetic output slots; whole donor rows from scored finals; donor types in predicted_celltype; recipient metadata inherited from v0035 slots",
                "ve_t1_armix": json.dumps(design, sort_keys=True),
            },
        )
        contract = validate_h5ad_contract(
            op,
            task="T1",
            board="val",
            scorer_lock=LOCK,
            parent_path=parent_path,
            parent_sha256=parent_row["sha256"],
        )
        (d / "CONTRACT.json").write_text(json.dumps(contract, indent=1, default=str))
        h = sha(op)
        n_diff_a = int((out != Xa).sum())
        dt = time.time() - t0
        status = contract.get("status")
        print(f"{lane} {pair} seed={seed}: sha={h[:12]}… status={status} "
              f"changed_entries={n_diff_a} wall={dt:.0f}s -> {op}")
        results.append({"lane": lane, "path": str(op.relative_to(ROOT)), "sha256": h,
                        "contract": status, "changed_entries": n_diff_a})
        del pa, pb, Xa, Xb, out
    (OUTROOT / "FINAL_BUILD.json").write_text(json.dumps(results, indent=1))
    bad = [r for r in results if r["contract"] != "PASS"]
    if bad:
        raise SystemExit(f"CONTRACT NOT PASS: {bad}")
    print("ALL 3 CONTRACT PASS")


if __name__ == "__main__":
    main()
