"""Shared read-only helpers for the T1 report-proxy autoresearch loop.

Loop operates at REPORT level only (3357 E8.5-outer recipient rows -> E9.5-outer
pseudo-target, 32285 genes, frozen seed 20260921). Nothing here touches E10.5
truth, submissions/, INDEX, registry, or coordination docs.

Baseline (local-proxy reference, NOT a submission):
  artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad (= v0035 final
  design applied at report scope; report SCORER.json: de 0.5926 / dir 0.5852 /
  energy 0.14221 / mmd 0.00937 / vario 0.000398)
Target / reference (frozen, read-only):
  artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1/intermediates/pseudo_target_e95_outer.h5ad
  artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1/intermediates/reference_e85_train.h5ad
"""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import anndata as ad
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_REPORT = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad"
TARGET = ROOT / "artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1/intermediates/pseudo_target_e95_outer.h5ad"
REFERENCE = ROOT / "artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1/intermediates/reference_e85_train.h5ad"
CAND_TMP = ROOT / ".auto/t1_candidate.h5ad"

BASELINE_LOCAL = {"de_score": 0.5926, "de_direction": 0.5852, "energy_distance": 0.14221,
                  "mmd_u": 0.00937, "variogram": 0.000398}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(4 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dense(x):
    return np.asarray(x.toarray() if sparse.issparse(x) else x, dtype=np.float32)


def load_baseline_report():
    a = ad.read_h5ad(BASELINE_REPORT)
    return a, dense(a.X)


def load_target_types():
    t = ad.read_h5ad(TARGET)
    return t


def write_candidate(path, X, template):
    """Write report-scope candidate reusing template obs/var (row identity = report slots)."""
    X = np.asarray(X, dtype=np.float32)
    assert X.shape == template.shape, X.shape
    assert np.isfinite(X).all() and (X >= 0).all()
    b = ad.AnnData(X=X, obs=template.obs.copy(), var=template.var.copy())
    b.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
    b.uns["ve_t1_autoresearch"] = {"scope": "report_proxy_only",
                                    "target_used": False,
                                    "note": "temp iteration file, never a submission"}
    b.write_h5ad(path, compression="gzip", compression_opts=1)
