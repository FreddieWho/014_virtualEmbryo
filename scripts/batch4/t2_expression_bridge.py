#!/usr/bin/env python3
"""B4-T2-R2 interpolation expression bridge: L1 mean bridge, L2 mean+mass bridge.

Frozen: parent geometry/coordinates/assignment (row-indexed exact), no FGW rerun,
no rescaling. Expression shift in log1p space per shared state; unmatched states
keep parent. L2 resamples parent rows to interpolated shares (largest remainder,
deterministic), n_obs = parent. No target data, no external data.
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
IFACE = REPO / "docs" / "batch3" / "interfaces"
for p in (str(REPO), str(IFACE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from virtual_embryo_tools import contract_io

TASK_ID = "B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE"
SEED = 20260904
NORMALIZATION = "log1p_normalized"

BOARDS = {
    "embryo": {"key": "T2:embryo:val_interp", "left": "data/E7.25.h5ad", "right": "data/E8.0.h5ad",
               "lam": 1.0 / 3.0,
               "parent": "submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
               "psha": "392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4",
               "panel": "data/gene_panel/T2__embryo__val_interp.genes.txt", "n": 5000,
               "lanes": [("L1_MEAN_BRIDGE", "v0009", "b4_t2_r2_l1_mean_bridge"),
                         ("L2_MEAN_MASS_BRIDGE", "v0010", "b4_t2_r2_l2_mean_mass_bridge")]},
    "heart": {"key": "T2:heart:val_interp", "left": "data/E8.25_late.h5ad", "right": "data/E8.75.h5ad",
              "lam": 0.5,
              "parent": "submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad",
              "psha": "4f2e7552a4ff5a11191f8cf6f1e94393882d131aa76855e5da34faef3f43ac43",
              "panel": "data/gene_panel/T2__heart__val_interp.genes.txt", "n": 5872,
              "lanes": [("L1_MEAN_BRIDGE", "v0012", "b4_t2_r2_l1_mean_bridge"),
                        ("L2_MEAN_MASS_BRIDGE", "v0013", "b4_t2_r2_l2_mean_mass_bridge")]},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dense(X):
    return X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float64)


def means_by_type(Xd: np.ndarray, types: np.ndarray) -> dict:
    out = {}
    for ct in np.unique(types):
        out[str(ct)] = Xd[types == ct].mean(axis=0).astype(np.float64)
    return out


def verify() -> dict:
    res = {}
    for b, cfg in BOARDS.items():
        assert sha256(REPO / cfg["parent"]) == cfg["psha"], f"BLOCKED_INPUT: {b} parent drift"
        panel = [l.strip() for l in (REPO / cfg["panel"]).read_text().splitlines() if l.strip()]
        p = ad.read_h5ad(REPO / cfg["parent"], backed="r")
        pt = sorted(set(str(v) for v in p.obs["celltype"]))
        p.file.close()
        L = ad.read_h5ad(REPO / cfg["left"], backed="r")
        R = ad.read_h5ad(REPO / cfg["right"], backed="r")
        lt = set(str(v) for v in L.obs["celltype"])
        rt = set(str(v) for v in R.obs["celltype"])
        rvars = set(str(v) for v in R.var_names)
        L.file.close()
        R.file.close()
        shared = sorted(set(pt) & lt & rt)
        miss_r = sorted(set(pt) - rt)
        res[b] = {"parent_sha_ok": True, "parent_types": len(pt),
                  "panel_genes": len(panel), "panel_in_right": sum(1 for g in panel if g in rvars),
                  "shared_both": len(shared), "missing_right": miss_r,
                  "unmatched_policy": "keep_parent_no_shift"}
        assert res[b]["panel_in_right"] == len(panel), f"{b} panel not covered by right stage"
    print(json.dumps(res, indent=1))
    return res


def build_lane(run_dir: Path, board: str, lane: str, version: str, method: str) -> dict:
    t0 = time.time()
    cfg = BOARDS[board]
    lam = cfg["lam"]
    panel = [l.strip() for l in (REPO / cfg["panel"]).read_text().splitlines() if l.strip()]
    gi = {g: i for i, g in enumerate(panel)}

    def load_mat(path: str):
        a = ad.read_h5ad(REPO / path, backed="r")
        vn = [str(v) for v in a.var_names]
        pos = np.array([vn.index(g) for g in panel])
        X = a.X[:, pos]
        Xd = dense(X).astype(np.float64)
        types = np.asarray(a.obs["celltype"].astype(str))
        names = [str(v) for v in a.obs_names]
        a.file.close()
        return Xd, types, names

    XL, tL, _ = load_mat(cfg["left"])
    XR, tR, _ = load_mat(cfg["right"])
    mL, mR = means_by_type(XL, tL), means_by_type(XR, tR)
    pL = {s: float((tL == s).sum()) / len(tL) for s in set(tL.tolist())}
    pR = {s: float((tR == s).sum()) / len(tR) for s in set(tR.tolist())}

    P = ad.read_h5ad(REPO / cfg["parent"])
    pnames = [str(v) for v in P.obs_names]
    ptypes = np.asarray(P.obs["celltype"].astype(str))
    XP = dense(P.X).astype(np.float64)
    pstates = sorted(set(ptypes.tolist()))
    shared = sorted(set(pstates) & set(mL) & set(mR))

    muP = means_by_type(XP, ptypes)
    shift = {}
    for s in pstates:
        if s in shared:
            muT = (1.0 - lam) * mL[s] + lam * mR[s]
            shift[s] = (muT - muP[s]).astype(np.float64)
        else:
            shift[s] = np.zeros(XP.shape[1])
    X1 = XP.copy()
    for s in pstates:
        X1[ptypes == s] += shift[s]
    clip_frac = float((X1 < 0).mean())
    np.clip(X1, 0, None, out=X1)

    diag = {"board": board, "lane": lane, "lambda": lam, "shared_states": len(shared),
            "unmatched_states": sorted(set(pstates) - set(shared)),
            "clip_fraction": clip_frac, "mass_lane": lane.endswith("MASS_BRIDGE")}

    if lane.endswith("MASS_BRIDGE"):
        pP = {s: float((ptypes == s).sum()) / len(ptypes) for s in pstates}
        raw = {}
        for s in pstates:
            if s in shared:
                raw[s] = (1.0 - lam) * pL.get(s, 0.0) + lam * pR.get(s, 0.0)
            else:
                raw[s] = 0.5 * pP[s] + 0.5 * pL.get(s, 0.0)
        tot = sum(raw.values())
        raw = {s: v / tot for s, v in raw.items()}
        counts = {s: int(raw[s] * len(ptypes)) for s in pstates}
        deficit = len(ptypes) - sum(counts.values())
        rema = sorted(pstates, key=lambda s: (raw[s] * len(ptypes) - counts[s], s), reverse=True)
        for i in range(deficit):
            counts[rema[i % len(rema)]] += 1
        rng = np.random.default_rng(SEED)
        order = np.argsort(np.asarray([pstates.index(t) for t in ptypes]), kind="stable")
        # deterministic per-state pools in parent order
        chosen, plan = [], []
        replaced = {}
        for s in pstates:
            pool = np.flatnonzero(ptypes == s)
            k = counts[s]
            if k <= len(pool):
                sel = np.sort(pool[rng.choice(len(pool), size=k, replace=False)] if k < len(pool) else pool)
                wr = False
            else:
                sel = np.sort(pool[rng.choice(len(pool), size=k, replace=True)])
                wr = True
                replaced[s] = {"need": k, "have": int(len(pool))}
            chosen.extend(sel.tolist())
            plan.append({"state": s, "parent_n": int((ptypes == s).sum()), "target_n": k,
                         "with_replacement": wr})
        chosen = np.asarray(chosen, dtype=np.int64)
        X1 = np.ascontiguousarray(X1[chosen])
        coord_src_idx = chosen
        out_names = [pnames[i] for i in chosen]
        seen: dict = {}
        final_names = []
        for nm in out_names:
            k = seen.get(nm, 0)
            final_names.append(nm if k == 0 else f"{nm}__dup{k}")
            seen[nm] = k + 1
        assert len(set(final_names)) == len(final_names)
        diag["with_replacement"] = replaced
        diag["dup_suffix_rows"] = int(sum(1 for n in final_names if "__dup" in n))
        pd.DataFrame(plan).to_csv(run_dir / "intermediates" / f"mass_plan_{board}.tsv",
                                  sep="\t", index=False)
        pd.DataFrame({"out_row": range(len(final_names)), "parent_row": coord_src_idx.tolist(),
                      "parent_obs_name": out_names, "out_obs_name": final_names}
                     ).to_csv(run_dir / "intermediates" / f"source_row_ledger_{board}_{lane}.tsv",
                              sep="\t", index=False)
    else:
        final_names = pnames
        coord_src_idx = np.arange(len(pnames))
        pd.DataFrame({"out_row": range(len(pnames)), "parent_row": coord_src_idx.tolist(),
                      "parent_obs_name": pnames, "out_obs_name": pnames}
                     ).to_csv(run_dir / "intermediates" / f"source_row_ledger_{board}_{lane}.tsv",
                              sep="\t", index=False)

    X1 = np.ascontiguousarray(X1, dtype=np.float32)
    assert np.isfinite(X1).all() and (X1 >= 0).all()
    assert X1.shape == (cfg["n"], len(panel)), X1.shape

    # geometry + layers + raw: row-indexed exact from parent (slice base, replace X only)
    out_a = P[coord_src_idx].copy()
    out_a.obs_names = final_names
    out_a.X = X1
    for k in list(out_a.obsm.keys()):
        if k == "spatial_3D":
            out_a.obsm[k] = np.ascontiguousarray(np.asarray(out_a.obsm[k])[:, :3], dtype=np.float32)
        else:
            out_a.obsm[k] = np.ascontiguousarray(np.asarray(out_a.obsm[k]), dtype=np.float32)
    out_a.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": NORMALIZATION}
    out_a.uns["ve_b4_t2_r2"] = json.dumps({
        "atom_id": TASK_ID, "lane": lane, "board": cfg["key"], "method": method,
        "lambda": lam, "parent_sha256": cfg["psha"], "seed": SEED,
        "shared_states": len(shared), "target_used": False}, sort_keys=True)
    out = run_dir / "candidates" / board / lane / "submission.h5ad"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(str(out))
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(prefix="." + out.name + ".", suffix=".h5ad", dir=out.parent)
    os.close(fd)
    out_a.write_h5ad(tmp)
    Path(tmp).replace(out)
    diag.update({"output": str(out), "sha256": sha256(out), "n_obs": int(out_a.n_obs),
                 "wall_s": time.time() - t0})
    (run_dir / "intermediates").mkdir(exist_ok=True)
    (run_dir / "intermediates" / f"diag_{board}_{lane}.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps(diag, indent=1, sort_keys=True), flush=True)
    return diag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["verify", "build"])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--board", default=None)
    ap.add_argument("--lane", default=None)
    ap.add_argument("--version", default=None)
    ap.add_argument("--method", default=None)
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    if args.command == "verify":
        verify()
    else:
        build_lane(run_dir, args.board, args.lane, args.version, args.method)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
