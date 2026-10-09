"""Shared helpers for the box-local Virtual Embryo workflow (no held-out data is ever read)."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import anndata as ad
from scipy import sparse

VE = Path("/workspace/ve")
DATA = VE / "data"
INDEX = json.loads((DATA / "index.json").read_text())
PANEL_FILE = {k: DATA / v["genes_file"] for k, v in INDEX.items()}


_EXTRA_PANELS: dict[str, list[str]] = {}


def panel(board: str) -> list[str]:
    if board in _EXTRA_PANELS:
        return list(_EXTRA_PANELS[board])
    return [l.strip() for l in PANEL_FILE[board].read_text().splitlines() if l.strip()]


def register_board(key: str, genes: list[str], min_cells: int, max_cells: int, obsm_required=("spatial_3D",),
                   anchors: dict | None = None) -> None:
    """Register a board that is not (yet) in the downloaded index.json, e.g. a provisional test board."""
    _EXTRA_PANELS[key] = list(genes)
    INDEX[key] = {"key": key, "min_cells": int(min_cells), "max_cells": int(max_cells),
                  "obsm_required": list(obsm_required), "anchors": anchors or {}, "provisional": True}


def load_index(path) -> None:
    """Merge an official index.json (e.g. the 2026-10-20 one with test boards) and its panel files (same dir)."""
    path = Path(path); idx = json.loads(path.read_text())
    for k, v in idx.items():
        INDEX[k] = v; PANEL_FILE[k] = path.parent / v["genes_file"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_stage(name: str, genes: list[str] | None = None, dense=True, layer=None):
    """Load a released stage, reorder to `genes` (must all be present)."""
    a = ad.read_h5ad(DATA / f"{name}.h5ad")
    X = a.layers[layer] if layer else a.X
    if genes is not None:
        miss = [g for g in genes if g not in set(a.var_names)]
        if miss:
            raise ValueError(f"{name}: missing {len(miss)} panel genes e.g. {miss[:5]}")
        idx = a.var_names.get_indexer(genes)
        X = X[:, idx]
        var = a.var.iloc[idx].copy()
    else:
        var = a.var.copy()
    if dense:
        X = X.toarray() if sparse.issparse(X) else np.asarray(X)
        X = np.asarray(X, dtype=np.float32)
    else:
        X = X.astype(np.float32)
    a = ad.AnnData(X=X, obs=a.obs.copy(), var=var, obsm={k: np.asarray(v) for k, v in a.obsm.items()})
    return a


def make_submission(X, genes, coords=None, obs_names=None, uns=None) -> ad.AnnData:
    X = np.ascontiguousarray(X, dtype=np.float32)
    n = X.shape[0]
    import pandas as pd
    obs = pd.DataFrame(index=[str(s) for s in (obs_names if obs_names is not None else [f"c{i}" for i in range(n)])])
    if obs.index.duplicated().any():
        obs.index = [f"{s}_{i}" for i, s in enumerate(obs.index)]
    out = ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=list(genes)))
    if coords is not None:
        out.obsm["spatial_3D"] = np.ascontiguousarray(np.asarray(coords)[:, :3], dtype=np.float32)
    if uns:
        out.uns["ve_provenance"] = json.dumps(uns, default=str)
    return out


def format_check(path: Path, board: str) -> dict:
    """Mirror the portal format check: gene panel/order, finite, non-negative, cell range, obsm."""
    spec = INDEX[board]
    a = ad.read_h5ad(path, backed="r")
    res = {"board": board, "file": str(path), "n_obs": int(a.n_obs), "n_vars": int(a.n_vars)}
    errs = []
    genes = panel(board)
    if [str(g) for g in a.var_names] != genes:
        errs.append("var_names != board panel (order/content)")
    if not (spec["min_cells"] <= a.n_obs <= spec["max_cells"]):
        errs.append(f"n_obs {a.n_obs} outside [{spec['min_cells']},{spec['max_cells']}]")
    if not a.obs_names.is_unique:
        errs.append("obs_names not unique")
    # chunked X check
    mn, finite = np.inf, True
    for s in range(0, a.n_obs, 2000):
        blk = a.X[s:s + 2000]
        blk = blk.toarray() if sparse.issparse(blk) else np.asarray(blk)
        finite &= bool(np.isfinite(blk).all()); mn = min(mn, float(blk.min()))
    if not finite: errs.append("X has non-finite values")
    if mn < 0: errs.append(f"X has negative values (min {mn})")
    for k in spec["obsm_required"]:
        if k not in a.obsm:
            errs.append(f"missing obsm['{k}']")
        else:
            C = np.asarray(a.obsm[k])
            if C.ndim != 2 or C.shape[0] != a.n_obs or C.shape[1] < 3 or not np.isfinite(C).all():
                errs.append(f"obsm['{k}'] bad shape/values {C.shape}")
    a.file.close()
    res["size_mb"] = round(path.stat().st_size / 1e6, 1)
    if res["size_mb"] > 1200: errs.append("file > 1200 MB")
    res["errors"] = errs
    res["pass"] = not errs
    return res


import os as _os
if _os.environ.get("VE_INDEX_FILE"):
    load_index(_os.environ["VE_INDEX_FILE"])
if _os.environ.get("VE_EXTRA_INDEX_FILE"):
    for _k, _v in json.loads(Path(_os.environ["VE_EXTRA_INDEX_FILE"]).read_text()).items():
        register_board(_k, _v["genes"], _v["min_cells"], _v["max_cells"], _v.get("obsm_required", []), _v.get("anchors"))
