"""Shared IO + deterministic machinery for T2 round2 lanes.

All functions are deterministic given the frozen seed. Nothing here reads any
target/truth file. Parents are hash-locked before use.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

REPO = Path(__file__).resolve().parents[2]
IFACE = REPO / "docs" / "batch3" / "interfaces"
for _p in (str(REPO), str(IFACE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONFIG_PATH = REPO / "configs" / "t2_round2" / "design_20260929.json"
SCORER_LOCK = REPO / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json"
BRIDGE_SEED = 20260904  # frozen seed of the v0010/v0013 mass plans (do not change)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dense(X) -> np.ndarray:
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def read_panel(rel: str) -> list[str]:
    return [l.strip() for l in (REPO / rel).read_text().splitlines() if l.strip()]


def load_stage(rel: str, panel: list[str], want_cm: bool = False):
    """Return (X float64 (n, len(panel)) in panel order, celltype str array,
    obs_names list, cm_celltype str array or None)."""
    a = ad.read_h5ad(REPO / rel, backed="r")
    vn = [str(v) for v in a.var_names]
    vidx = {g: i for i, g in enumerate(vn)}
    missing = [g for g in panel if g not in vidx]
    if missing:
        a.file.close()
        raise ValueError(f"{rel}: panel genes missing: {missing[:5]} (n={len(missing)})")
    pos = np.array([vidx[g] for g in panel], dtype=np.int64)
    X = dense(a.X[:, pos]).astype(np.float64)
    types = np.asarray(a.obs["celltype"].astype(str))
    names = [str(v) for v in a.obs_names]
    cm = np.asarray(a.obs["cm_celltype"].astype(str)) if (want_cm and "cm_celltype" in a.obs.columns) else None
    a.file.close()
    return X, types, names, cm


def load_parent(rel: str, expected_sha: str) -> ad.AnnData:
    path = REPO / rel
    actual = sha256(path)
    if actual != expected_sha:
        raise AssertionError(f"BLOCKED_INPUT: parent drift {rel}: {actual} != {expected_sha}")
    return ad.read_h5ad(path)


def verify_all_inputs(cfg: dict) -> dict:
    """Hash-lock every input file listed in the config before any build."""
    res: dict[str, str] = {}
    for b, bc in cfg["boards"].items():
        for key in ("parent", "bridge_parent", "shrink_parent"):
            if key in bc:
                res[f"{b}.{key}"] = sha256(REPO / bc[key])
                want = bc[f"{key}_sha256"]
                if res[f"{b}.{key}"] != want:
                    raise AssertionError(f"BLOCKED_INPUT: {b}.{key} drift")
        res[f"{b}.panel"] = sha256(REPO / bc["panel"])
        for sk, sp in bc["stages"].items():
            res[f"{b}.stage.{sk}"] = sha256(REPO / sp)
    return res


def shares(types: np.ndarray) -> dict[str, float]:
    n = len(types)
    return {s: float((types == s).sum()) / n for s in set(types.tolist())}


def means_vars_by_label(X: np.ndarray, labels: np.ndarray):
    """Return (means, vars, ns) dicts keyed by label, float64."""
    means: dict[str, np.ndarray] = {}
    varr: dict[str, np.ndarray] = {}
    ns: dict[str, int] = {}
    for s in np.unique(labels):
        m = X[labels == s]
        means[str(s)] = m.mean(axis=0).astype(np.float64)
        varr[str(s)] = m.var(axis=0).astype(np.float64)
        ns[str(s)] = int(len(m))
    return means, varr, ns


def mass_counts_bridge(pstates: list[str], pP: dict, pL: dict, pR: dict,
                       shared: set[str], lam: float, n: int):
    """Exact replica of B4-T2-R2 share rule + largest-remainder counts."""
    raw = {}
    for s in pstates:
        if s in shared:
            raw[s] = (1.0 - lam) * pL.get(s, 0.0) + lam * pR.get(s, 0.0)
        else:
            raw[s] = 0.5 * pP[s] + 0.5 * pL.get(s, 0.0)
    return counts_from_raw(raw, pstates, n)


def counts_from_raw(raw: dict[str, float], pstates: list[str], n: int):
    tot = sum(raw.values())
    if tot <= 0:
        raise ValueError("raw shares sum to zero")
    raw = {s: float(v) / tot for s, v in raw.items()}
    counts = {s: int(raw[s] * n) for s in pstates}
    deficit = n - sum(counts.values())
    rema = sorted(pstates, key=lambda s: (raw[s] * n - counts[s], s), reverse=True)
    for i in range(deficit):
        counts[rema[i % len(rema)]] += 1
    return counts, raw


def select_rows(ptypes: np.ndarray, counts: dict[str, int], seed: int) -> np.ndarray:
    """Exact replica of B4-T2-R2 deterministic per-state pool selection."""
    rng = np.random.default_rng(seed)
    pstates = sorted(set(ptypes.tolist()))
    chosen: list[int] = []
    for s in pstates:
        pool = np.flatnonzero(ptypes == s)
        k = int(counts[s])
        if k <= len(pool):
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=False)] if k < len(pool) else pool)
        else:
            sel = np.sort(pool[rng.choice(len(pool), size=k, replace=True)])
        chosen.extend(sel.tolist())
    return np.asarray(chosen, dtype=np.int64)


def dedup_names(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for nm in names:
        k = seen.get(nm, 0)
        out.append(nm if k == 0 else f"{nm}__dup{k}")
        seen[nm] = k + 1
    if len(set(out)) != len(out):
        raise AssertionError("dedup_names produced duplicate names")
    return out


def write_candidate(out_a: ad.AnnData, out: Path) -> str:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(str(out))
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    out_a.write_h5ad(tmp)
    Path(tmp).replace(out)
    return sha256(out)


def stamp_uns(out_a: ad.AnnData, *, normalization: str, provenance: dict) -> None:
    out_a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": normalization}
    out_a.uns["ve_t2_round2"] = json.dumps(provenance, sort_keys=True)


def fix_obsm(out_a: ad.AnnData) -> None:
    for k in list(out_a.obsm.keys()):
        if k == "spatial_3D":
            out_a.obsm[k] = np.ascontiguousarray(np.asarray(out_a.obsm[k])[:, :3], dtype=np.float32)
        else:
            out_a.obsm[k] = np.ascontiguousarray(np.asarray(out_a.obsm[k]), dtype=np.float32)


def contract_check(path: Path, *, board: str, parent_rel: str, parent_sha: str) -> dict:
    from virtual_embryo_tools import contract_io

    res = dict(contract_io.validate_h5ad_contract(
        Path(path), task="T2", board=board,
        scorer_lock=SCORER_LOCK,
        parent_path=REPO / parent_rel, parent_sha256=parent_sha))
    return res


def write_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


def source_row_ledger(path: Path, chosen: np.ndarray, parent_names: list[str], final_names: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "out_row": range(len(final_names)),
        "parent_row": chosen.tolist(),
        "parent_obs_name": [parent_names[i] for i in chosen],
        "out_obs_name": final_names,
    }).to_csv(path, sep="\t", index=False)
