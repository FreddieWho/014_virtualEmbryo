"""Build full-scope T1 winner-mix candidates — batch AR-T1-MIX2-20261003-v1.

Lanes (frozen; whole-row donor preservation; target_used=false):
  P1 mix3538even  35x38 frac0.5 seed20260921  (M5 analogue — the requested cheap lane)
  P2 mix3538evenb 35x38 frac0.5 seed20261023  (seed-pair partner: server row-luck read)
  P3 mix3638even  36x38 frac0.5 seed20260921  (variant of the server-best 36x38 pair)
  P4 mix3way      35/36/38 equal thirds seed20260921 (M4 analogue, three-pool mechanism)
  P5 mix3538f030  35x38 frac0.3 seed20260921  (weight extreme; best-mmd +1q report point)

P1/P2/P3/P5 construction = server-scored s2mix recipe verbatim (stratified whole-row
mixture_indices, no-replacement draw per side, frozen seed), only pair/fraction change.
P4 construction = report M4 generator (equal-thirds quotas, per-side per-type
largest-remainder allocation, single final permutation).
Contract parent = v0035 for every lane (seven precedent); donor shas re-verified
against submissions/INDEX.tsv before any build.
Writes (new dirs only): artifacts/autoresearch/t1-20261003-v1/final_<lane>/submission.h5ad + CONTRACT.json
No INDEX/registry/coordination writes (coordinator scope).
"""
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import anndata as ad

sys.path.insert(0, "scripts/t1_three")
from ops import mixture_indices, allocation  # noqa

ROOT = Path(".").resolve()
OUTROOT = ROOT / "artifacts/autoresearch/t1-20261003-v1"
LOCK = ROOT / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
sys.path.insert(0, str(ROOT / "docs/batch3/interfaces"))
from virtual_embryo_tools.contract_io import (  # noqa
    write_candidate_from_parent,
    validate_h5ad_contract,
)

CONTRACT_PARENT = "v0035"
DONORS = {"v0035": "v0035_three_r2joint", "v0036": "v0036_three_r3mix",
          "v0038": "v0038_seven_n2covot"}
# (lane, pair-label, donor versions, frac or None for 3way, seed, proposed version)
LANES = [
    ("P1", "35x38even", ["v0035", "v0038"], 0.5, 20260921, "v0052"),
    ("P2", "35x38evenb", ["v0035", "v0038"], 0.5, 20261023, "v0053"),
    ("P3", "36x38even", ["v0036", "v0038"], 0.5, 20260921, "v0054"),
    ("P4", "3way", ["v0035", "v0036", "v0038"], None, 20260921, "v0055"),
    ("P5", "35x38f030", ["v0035", "v0038"], 0.3, 20260921, "v0056"),
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
    assert len(hits) == 1, f"INDEX row {version}: {len(hits)} hits"
    return hits[0]


def three_way_indices(types_list, quotas, seed):
    """Mirror .auto/generate_t1_3way.py exactly (equal-thirds report generator)."""
    n = int(sum(quotas))
    rng = np.random.default_rng(seed)
    rows, side_ids = [], []
    for side, (t, q) in enumerate(zip(types_list, quotas)):
        for tt, k in allocation(t, q).items():
            chosen = rng.permutation(np.flatnonzero(t == tt))[: int(k)]
            rows.extend(chosen.tolist())
            side_ids.extend([side] * len(chosen))
    order = rng.permutation(n)
    return np.asarray(side_ids)[order], np.asarray(rows)[order]


def main():
    parent_row = indexed(CONTRACT_PARENT)
    parent_path = ROOT / parent_row["path"]
    assert sha(parent_path) == parent_row["sha256"], "contract parent drift — STOP"
    donor_meta = {}
    for v in ("v0035", "v0036", "v0038"):
        r = indexed(v)
        p = ROOT / r["path"]
        assert p.exists(), p
        assert sha(p) == r["sha256"], f"donor {v} sha drift — STOP"
        donor_meta[v] = {"row": r, "path": p}
    results = []
    for lane, pair, vers, frac, seed, proposed in LANES:
        t0 = time.time()
        ann = {v: ad.read_h5ad(donor_meta[v]["path"]) for v in vers}
        for v in vers:
            assert ann[v].shape == (5118, 32285), (v, ann[v].shape)
        base = ann[vers[0]]
        assert all((base.obs_names == ann[v].obs_names).all() for v in vers), "slot drift"
        types = [ann[v].obs["celltype"].astype(str).to_numpy() for v in vers]
        Xs = [dense(ann[v].X) for v in vers]
        n = base.shape[0]
        if frac is None:
            base_q = n // 3
            quotas = [base_q, base_q, base_q]
            for i in range(n - 3 * base_q):
                quotas[i] += 1
            sides, rows = three_way_indices(types, quotas, seed)
        else:
            sides, rows = mixture_indices(types[0], types[1], frac, seed)
            quotas = None
        counts = [int((sides == k).sum()) for k in range(len(vers))]
        out = np.empty_like(Xs[0])
        pt = np.empty(n, dtype=object)
        for i, (s, r) in enumerate(zip(sides.tolist(), rows.tolist())):
            out[i] = Xs[s][r]
            pt[i] = types[s][r]
        assert np.isfinite(out).all() and (out >= 0).all()
        rngc = np.random.default_rng(0)
        for i in rngc.integers(0, n, size=300):
            assert np.array_equal(out[int(i)], Xs[int(sides[int(i)])][int(rows[int(i)])])
        d = OUTROOT / f"final_{lane}_{pair}_s{seed}"
        d.mkdir(parents=True, exist_ok=False)
        op = d / "submission.h5ad"
        design = {
            "batch": "AR-T1-MIX2-20261003-v1",
            "lane": lane,
            "pair": pair,
            "donors": vers,
            "fraction_first_donor": frac,
            "quotas": quotas,
            "seed": seed,
            "side_counts": counts,
            "contract_parent": CONTRACT_PARENT,
            "method": "stratified whole-row mixture (s2mix construction); P4 = equal-thirds three-pool",
            "target_used": False,
            "report_analog": {
                "P1": "T1-12 f0.5 3-seed median de +1q (M5)",
                "P2": "T1-12 seed-pair partner (server row-luck read)",
                "P3": "server pair 36x38 at 70/30 = v0051 53.92 (current T1 best)",
                "P4": "T1-11 three-way 3-seed median pin (M4)",
                "P5": "T1-15 f0.3 3-seed median pin; best report mmd of the +1q points (M6)",
            }[lane],
            "proposed_version": proposed + "_PROPOSED_pending_coordinator",
        }
        write_candidate_from_parent(
            parent_path=parent_path,
            output_path=op,
            expression=out,
            row_names=list(base.obs_names),
            normalization="log1p_normalized",
            parent_sha256=parent_row["sha256"],
            metadata_updates={
                "predicted_celltype": np.asarray(pt, dtype=str),
                "row_identity_note": "synthetic output slots; whole donor rows from scored finals; donor types in predicted_celltype; recipient metadata inherited from v0035 slots",
                "ve_t1_armix2": json.dumps(design, sort_keys=True),
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
        changed = int((out != Xs[0]).sum())
        dt = time.time() - t0
        print(f"{lane} {pair} seed={seed}: sha={h[:12]}… status={contract.get('status')} "
              f"side_counts={counts} changed_vs_first={changed} wall={dt:.0f}s -> {op}", flush=True)
        results.append({"lane": lane, "pair": pair, "seed": seed, "path": str(op.relative_to(ROOT)),
                        "sha256": h, "contract": contract.get("status"),
                        "side_counts": counts, "changed_vs_first_donor": changed,
                        "proposed_version": proposed})
        del ann, Xs, out, base
    (OUTROOT / "FINAL_BUILD_v2.json").write_text(json.dumps(results, indent=1))
    bad = [r for r in results if r["contract"] != "PASS"]
    if bad:
        raise SystemExit(f"CONTRACT NOT PASS: {bad}")
    print(f"ALL {len(results)} CONTRACT PASS")


if __name__ == "__main__":
    main()
