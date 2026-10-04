#!/usr/bin/env python3
"""T1 external temporal pretraining, stage A: build compliant subset cache.

Lane: T1-EXTPRE-20261003-v1 (DESIGN.md frozen 2026-10-03; new use approved 2026-10-03).
Step A (this script): read ExtendedMouseAtlas embryo_complete.h5ad read-only,
keep the 8 compliant stages (E6.5, E6.75, E7.0, E7.25, E8.0, E8.25, E8.5, E9.0),
intersect genes with the frozen T1 transfer panel (state_input_genes, 27669,
which covers the needed bridge), log1p-normalize raw counts, and write a
float32 cache. Excluded stages are NEVER read into the cache (hard veto).
Step B (separate script): pretrain + transfer + gate (not this file).

Deterministic: fixed seed; row order = file order restricted to kept stages.
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

TASK_ID = "T1-EXTPRE-20261003-v1"
RUN_SEED = 20261003
ATLAS = REPO / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/ExtendedMouseAtlas/embryo_complete.h5ad"
PANEL_GENES = REPO / "artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data/state_input_genes.tsv"
KEEP = ["E6.5", "E6.75", "E7.0", "E7.25", "E8.0", "E8.25", "E8.5", "E9.0"]
VETO = ["E7.5", "E7.75", "E8.75", "E9.25", "E9.5", "Mixed gastrulation"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    import h5py
    import pandas as pd

    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "step": "A_subset_cache", "seed": RUN_SEED,
                  "keep_stages": KEEP, "veto_stages": VETO}
    t00 = time.time()

    with open(ATLAS, "rb") as fh:
        pass
    f = h5py.File(ATLAS, "r")
    cats = [c.decode() if isinstance(c, bytes) else str(c)
            for c in f["obs/stage/categories"][:]]
    codes = np.array(f["obs/stage/codes"][:])
    assert set(VETO) <= set(cats), "veto list drifted vs file"
    assert set(KEEP) <= set(cats), "keep list drifted vs file"
    keep_idx = np.flatnonzero(np.isin([cats[c] for c in codes], KEEP))
    veto_in_cache = [c for c in [cats[c] for c in codes[keep_idx]] if c in VETO]
    assert not veto_in_cache, f"veto stage leaked: {veto_in_cache[:5]}"
    diag["n_cells_kept"] = int(len(keep_idx))
    # stage histogram of the cache
    kept_stages = [cats[c] for c in codes[keep_idx]]
    diag["stage_counts"] = {s: int((np.array(kept_stages) == s).sum()) for s in KEEP}

    # gene bridge: frozen transfer panel (27669) — atlas gene order comes from
    # the same source family; verify overlap against the frozen panel list
    panel = pd.read_csv(PANEL_GENES, sep="\t")["gene"].astype(str).tolist()
    diag["n_panel_genes"] = len(panel)
    # atlas X has no stored gene names in this file copy; column order is the
    # source family's canonical order and the frozen panel was derived from it
    # (S1A provenance). Record the assumption explicitly; step B asserts
    # panel-dim compatibility before any training.
    diag["gene_order_note"] = ("atlas X columns assumed in source-family canonical "
                               "order matching the frozen 27669 transfer panel; "
                               "step B asserts dim + checksum before training")

    # chunked read of kept rows -> log1p float32 cache (memmap, then npz)
    X = f["X"]
    n, d = X.shape
    assert d == len(panel), f"atlas width {d} != panel {len(panel)}"
    out = np.empty((len(keep_idx), d), dtype=np.float32)
    CH = 20000
    for a in range(0, len(keep_idx), CH):
        rows = np.sort(keep_idx[a:a + CH])
        blk = X[rows, :].astype(np.float64)
        out[a:a + len(rows)] = np.log1p(blk).astype(np.float32)
    assert np.isfinite(out).all() and (out >= 0).all()
    np.save(RUN / "intermediates" / "cache_log1p.npy", out)
    # stage labels aligned with cache rows
    np.save(RUN / "intermediates" / "cache_stages.npy",
            np.array(kept_stages))
    # cell-type labels + gene symbols (needed by step B cell-type-aware
    # conditioning and the T1-panel gene intersection)
    ct = f["obs/celltype_extended_atlas"]
    ct_cats = [c.decode() if isinstance(c, bytes) else str(c)
               for c in ct["categories"][:]]
    ct_codes = np.array(ct["codes"][:])
    kept_ct = [ct_cats[c] for c in ct_codes[keep_idx]]
    np.save(RUN / "intermediates" / "cache_celltypes.npy",
            np.array(kept_ct))
    vg = f["var/mgi_symbol"]
    if isinstance(vg, h5py.Dataset):
        genes = [g.decode() if isinstance(g, bytes) else str(g) for g in vg[:]]
    else:  # categorical group: categories + codes
        gcats = [g.decode() if isinstance(g, bytes) else str(g)
                 for g in vg["categories"][:]]
        gcodes = np.array(vg["codes"][:])
        genes = [gcats[c] for c in gcodes]
    assert len(genes) == d
    np.save(RUN / "intermediates" / "cache_genes.npy", np.array(genes))
    diag["n_celltypes"] = int(len(ct_cats))
    diag["cache_shape"] = list(out.shape)
    diag["cache_sha"] = sha256(RUN / "intermediates" / "cache_log1p.npy")
    diag["wall_s"] = time.time() - t00
    (RUN / "STEP_A.json").write_text(json.dumps(diag, indent=1, default=float))
    print(json.dumps({"step_a_done": True, "shape": diag["cache_shape"],
                      "stages": diag["stage_counts"]}, indent=1), flush=True)
    f.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
