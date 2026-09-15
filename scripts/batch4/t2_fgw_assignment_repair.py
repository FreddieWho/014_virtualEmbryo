#!/usr/bin/env python3
"""B4-T2-R1: replace greedy soft->hard discretization with global bipartite matching.

Frozen (same as T2-J1 v0009 generation; see scripts/t2_j1_proxy.py):
  alpha=0.5, square_loss, uniform marginals, POT PGD, max_iter=500, tol=1e-7,
  same PCA/reference construction, same seed 20260830, same parent
  (v0007 t2_s3_l1_pycpd), same expression row set, no geometry change.

Lanes (board T2:heart:val_interp, n=5872):
  L1_EPS005_GLOBALMATCH: reuse old eps=0.005 soft coupling, only assignment changes.
  L2_EPS002_GLOBALMATCH: fresh solve with eps=0.002, same global matching.

Matching rule (global_bipartite_match_v1): per position take coupling top-64
rows, sparse bipartite graph with edge cost -log(T+1e-12),
scipy.sparse.csgraph.min_weight_full_bipartite_matching; if no full matching,
one expansion to top-128; still failing -> BLOCKED_SOLVER (raise).

Layout: run_dir/lanes/<LANE>/{intermediates, candidates, metrics}/... reuses the
frozen batch3 writer + contract/checks/NFS/scorer commands per lane dir.

Never reads held-out target. target_used=False by construction.
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

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import min_weight_full_bipartite_matching

from scripts.t2_j1_fgw_assignment import (
    BOARD_SPECS,
    FGW_ALPHA,
    FGW_LOSS,
    FGW_MAX_ITER,
    FGW_SOLVER,
    FGW_TOL,
    KNN_K,
    N_REF,
    NORMALIZATION,
    PCA_COMPONENTS,
    PROXY_OBJECTIVE_SPEC,
    PROXY_OBJECTIVE_SPEC_SHA256,
    REG_K,
    SEED,
    VENV_PYTHON,
    _append_run_log,
    _contract_io,
    _effective_sources,
    _take_rows,
    _worker_env,
    fgw_loss,
    fgw_loss_permutation,
    sha256_file,
    validate_coupling,
    command_checks,
    command_contract,
    command_nfs_proxy,
    command_score,
)
from scripts.t2_s3_shape_field import (
    _write_json_atomic,
    _write_npz_atomic,
)

TASK_ID = "B4-T2-R1-FGW-ASSIGNMENT-REPAIR"
BOARD = "T2_heart_val_interp"
OLD_ATOM = REPO / "artifacts" / "tool_integration" / "T2-J1-FGW-ASSIGNMENT-20260903-v1"
OLD_HOLD = OLD_ATOM / "intermediates" / BOARD
EXPECTED_PROBLEM_SHA256 = "4a957da538d4f9f93e71eaddc78a6f83379fb5f0624524a5d4cc89641a34529e"
MATCH_RULE_ID = "global_bipartite_match_v1"

LANES = {
    "L1_EPS005_GLOBALMATCH": {"eps": 0.005, "version": "v0010",
                              "member": "t2_hrt_int__l1glob05__v0010.h5ad",
                              "method": "b4_t2_r1_l1_globalmatch"},
    "L2_EPS002_GLOBALMATCH": {"eps": 0.002, "version": "v0011",
                              "member": "t2_hrt_int__l2glob002__v0011.h5ad",
                              "method": "b4_t2_r1_l2_globalmatch"},
}


def lane_dir(run_dir: Path, lane: str) -> Path:
    return Path(run_dir) / "lanes" / lane


def cmd_stage(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    spec = BOARD_SPECS[BOARD]
    prob_src = OLD_HOLD / "problem.npz"
    assert sha256_file(prob_src) == EXPECTED_PROBLEM_SHA256, "frozen problem drift"
    audit = json.loads((OLD_ATOM / "metrics" / "reference_audit.json").read_text())
    assert audit.get("heart_verdict") == "PROCEED", audit.get("heart_verdict")
    staged = {}
    for lane in LANES:
        hold = lane_dir(run_dir, lane) / "intermediates" / BOARD
        hold.mkdir(parents=True, exist_ok=True)
        (hold / "problem.npz").write_bytes(prob_src.read_bytes())
        if LANES[lane]["eps"] == 0.005:
            (hold / "transport_plan.npz").write_bytes((OLD_HOLD / "transport_plan.npz").read_bytes())
            (hold / "solve_meta.json").write_bytes((OLD_HOLD / "solve_meta.json").read_bytes())
        met = lane_dir(run_dir, lane) / "metrics" / "reference_audit.json"
        met.parent.mkdir(parents=True, exist_ok=True)
        met.write_text((OLD_ATOM / "metrics" / "reference_audit.json").read_text())
        lock = lane_dir(run_dir, lane) / "inputs" / "input_lock.json"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text((OLD_ATOM / "inputs" / "input_lock.json").read_text())
        staged[lane] = {
            "problem_sha256": sha256_file(hold / "problem.npz"),
            "coupling": "copied-frozen-eps005" if (hold / "transport_plan.npz").exists() else "to-solve-eps002",
        }
    cfg = {
        "task": TASK_ID, "board": BOARD, "seed": SEED,
        "frozen": {"alpha": FGW_ALPHA, "loss": FGW_LOSS, "max_iter": FGW_MAX_ITER,
                   "tol": FGW_TOL, "solver": FGW_SOLVER, "pca": PCA_COMPONENTS,
                   "n_ref": N_REF, "reg_k": REG_K, "knn_k": KNN_K,
                   "problem_sha256": EXPECTED_PROBLEM_SHA256,
                   "parent_path": spec.parent_path, "parent_sha256": spec.parent_sha256,
                   "objective_spec_sha256": PROXY_OBJECTIVE_SPEC_SHA256},
        "lanes": {l: {"eps": v["eps"], "version": v["version"], "member": v["member"],
                      "method": v["method"]} for l, v in LANES.items()},
        "matching_rule": MATCH_RULE_ID,
        "staged": staged, "target_used": False,
    }
    (Path(run_dir) / "config_resolved.yaml").write_text(
        json.dumps(cfg, indent=1, sort_keys=True) + "\n")
    return cfg


def cmd_solve_l2(run_dir: Path) -> dict:
    """Fresh eps=0.002 solve in the frozen venv. Run under bg_run (minutes)."""
    hold = lane_dir(run_dir, "L2_EPS002_GLOBALMATCH") / "intermediates" / BOARD
    problem_path = hold / "problem.npz"
    coupling_path = hold / "transport_plan.npz"
    meta_path = hold / "solve_meta.json"
    assert sha256_file(problem_path) == EXPECTED_PROBLEM_SHA256
    if coupling_path.exists():
        raise FileExistsError("L2 coupling already solved")
    if not VENV_PYTHON.is_file():
        raise RuntimeError("missing tool interpreter")
    cmd = [str(VENV_PYTHON), str(Path(__file__).resolve()), "solve-l2-worker",
           "--run-dir", str(Path(run_dir).resolve()),
           "--problem", str(problem_path), "--coupling", str(coupling_path),
           "--meta", str(meta_path)]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                          env=_worker_env(), timeout=14400)
    if proc.returncode != 0:
        raise RuntimeError(f"L2 solve failed: {proc.stderr[-2000:]}")
    meta = json.loads(meta_path.read_text())
    assert meta.get("problem_sha256") == EXPECTED_PROBLEM_SHA256
    assert abs(meta.get("epsilon", -1) - 0.002) < 1e-12
    return {"step": "solve-l2", "epsilon": 0.002, "wall_seconds": meta.get("wall_seconds")}


def solve_l2_worker(problem: Path, coupling: Path, meta_path: Path) -> dict:
    from scripts.t2_j1_proxy import solve_fgw
    bundle = np.load(Path(problem))
    t0 = time.time()
    T, meta = solve_fgw(bundle["M"], bundle["C1"], bundle["C2"], bundle["p"], bundle["q"],
                        alpha=FGW_ALPHA, epsilon=0.002, max_iter=FGW_MAX_ITER, tol=FGW_TOL)
    meta.update({"schema": "ve.b4.t2-r1.solve-meta.v1", "atom": TASK_ID,
                 "lane": "L2_EPS002_GLOBALMATCH", "board": BOARD, "seed": SEED,
                 "epsilon": 0.002, "problem_sha256": sha256_file(Path(problem)),
                 "worker_wall_seconds": time.time() - t0})
    _write_npz_atomic(Path(coupling), T=T)
    _write_json_atomic(Path(meta_path), meta)
    return meta


def global_match(T: np.ndarray) -> tuple[np.ndarray, dict]:
    coupling = np.asarray(T, dtype=np.float64)
    n = coupling.shape[0]
    marginals = validate_coupling(coupling, n)
    order = np.argsort(-coupling, axis=0, kind="stable")
    top1 = order[0].astype(np.int64)
    top_mass = coupling[top1, np.arange(n)]
    topk_used = None
    placement = None
    col_idx = np.tile(np.arange(n), (128, 1))
    for k in (64, 128):
        rows_k = order[:k].astype(np.int64)
        costs = -np.log(coupling[rows_k, col_idx[:k]] + 1e-12)
        graph = sparse.csr_matrix(
            (costs.ravel(), (rows_k.ravel(), col_idx[:k].ravel())), shape=(n, n))
        try:
            row_ind, col_ind = min_weight_full_bipartite_matching(graph)
        except ValueError:
            continue
        if len(row_ind) == n and np.array_equal(np.sort(col_ind), np.arange(n)):
            placement = np.empty(n, dtype=np.int64)
            placement[col_ind] = row_ind
            topk_used = k
            break
    if placement is None:
        raise RuntimeError("BLOCKED_SOLVER: no full matching at top-64 nor top-128")
    if not np.array_equal(np.sort(placement), np.arange(n, dtype=np.int64)):
        raise AssertionError("matching is not a bijection")
    rank = np.empty(n, dtype=np.int64)
    for j in range(n):
        rank[j] = int(np.flatnonzero(order[:, j] == placement[j])[0])
    assigned_mass = coupling[placement, np.arange(n)]
    stats = {
        "rule": MATCH_RULE_ID, "n": n, "topk_used": topk_used,
        "top1_retention": float(np.mean(placement == top1)),
        "mass_captured": float(assigned_mass.sum()),
        "mass_top_sum": float(top_mass.sum()),
        "mass_capture_ratio": float(assigned_mass.sum() / top_mass.sum()),
        "total_assignment_cost": float((-np.log(assigned_mass + 1e-12)).sum()),
        "mean_rank_depth": float(rank.mean()), "max_rank_depth": int(rank.max()),
        "n_moved_vs_parent": int(np.sum(placement != np.arange(n))),
        "effective_sources": _effective_sources(coupling),
        "conflicts": int(np.sum(rank > 0)),
        **marginals,
    }
    return placement, stats


def cmd_match(run_dir: Path, lane: str) -> dict:
    hold = lane_dir(run_dir, lane) / "intermediates" / BOARD
    for f in ("transport_plan.npz", "solve_meta.json", "problem.npz"):
        if not (hold / f).is_file():
            raise FileNotFoundError(f"missing {hold / f}")
    meta = json.loads((hold / "solve_meta.json").read_text())
    if meta.get("problem_sha256") != sha256_file(hold / "problem.npz"):
        raise RuntimeError("stale coupling: problem changed since solve")
    if (hold / "assignment.npz").exists():
        raise FileExistsError("assignment exists; refusing to overwrite")
    t0 = time.time()
    T = np.load(hold / "transport_plan.npz")["T"]
    placement, stats = global_match(T)
    _write_npz_atomic(hold / "assignment.npz", placement=placement)
    spec = BOARD_SPECS[BOARD]
    import anndata as ad
    obs_names = [str(v) for v in ad.read_h5ad(REPO / spec.parent_path).obs_names]
    order = np.argsort(-np.asarray(T, dtype=np.float64), axis=0, kind="stable")
    lines = ["position_index\tposition_obs_name\tdonor_row_index\tdonor_obs_name\t"
             "coupling_mass\tcolumn_top_mass\tmargin\trank_depth\tconflict"]
    for j in range(len(placement)):
        row = int(placement[j])
        top = float(T[order[0, j], j])
        second = float(T[order[1, j], j])
        depth = int(np.flatnonzero(order[:, j] == row)[0])
        lines.append(f"{j}\t{obs_names[j]}\t{row}\t{obs_names[row]}\t{T[row, j]:.10e}\t"
                     f"{top:.10e}\t{top - second:.10e}\t{depth}\t{int(depth > 0)}")
    tmp = hold / "assignment.tsv.tmp"
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(hold / "assignment.tsv")
    bundle = np.load(hold / "problem.npz")
    ledger = {
        "schema": "ve.b4.t2-r1.assignment-meta.v1", "atom": TASK_ID, "lane": lane,
        "board": BOARD, "seed": SEED, "epsilon": LANES[lane]["eps"],
        "coupling_sha256": sha256_file(hold / "transport_plan.npz"),
        "problem_sha256": sha256_file(hold / "problem.npz"),
        "solve_meta": meta, "assignment": stats,
        "fgw_objective": {
            "soft_plan": fgw_loss(bundle["M"], bundle["C1"], bundle["C2"], T, FGW_ALPHA),
            "identity_parent_pairing": fgw_loss_permutation(
                bundle["M"], bundle["C1"], bundle["C2"], np.arange(len(placement)), FGW_ALPHA),
            "hard_assignment": fgw_loss_permutation(
                bundle["M"], bundle["C1"], bundle["C2"], placement, FGW_ALPHA),
        },
        "wall_seconds": time.time() - t0, "target_used": False,
    }
    _write_json_atomic(hold / "assignment_meta.json", ledger)
    (Path(run_dir) / "intermediates").mkdir(exist_ok=True)
    import shutil
    shutil.copy(hold / "assignment.tsv",
                Path(run_dir) / "intermediates" / f"assignment_{lane}.tsv")
    _append_run_log(lane_dir(run_dir, lane),
                    f"match {lane}: topk={stats['topk_used']} top1ret={stats['top1_retention']:.4f}")
    return {"step": "match", "lane": lane, **stats}


def cmd_generate(run_dir: Path, lane: str) -> dict:
    out = lane_dir(run_dir, lane)
    spec = BOARD_SPECS[BOARD]
    hold = out / "intermediates" / BOARD
    audit = json.loads((out / "metrics" / "reference_audit.json").read_text())
    if audit.get("heart_verdict") != "PROCEED":
        raise RuntimeError("heart gate not PROCEED")
    placement = np.load(hold / "assignment.npz")["placement"]
    assignment_meta = json.loads((hold / "assignment_meta.json").read_text())
    parent_path = REPO / spec.parent_path
    candidate_path = out / "candidates" / BOARD / "submission.h5ad"
    if candidate_path.exists():
        raise FileExistsError(f"refusing to overwrite {candidate_path}")
    import anndata as ad
    parent = ad.read_h5ad(parent_path)
    X_new = _take_rows(parent.X, placement)
    provenance = {
        "atom_id": TASK_ID, "lane": lane, "board": spec.slug,
        "official_board_key": f"T2:{spec.board_key}",
        "method": LANES[lane]["method"],
        "assignment_rule": MATCH_RULE_ID,
        "parent_submission": spec.parent_path, "parent_sha256": spec.parent_sha256,
        "objective_spec": str(PROXY_OBJECTIVE_SPEC.relative_to(REPO)),
        "objective_spec_sha256": PROXY_OBJECTIVE_SPEC_SHA256,
        "objective": f"entropic FGW (POT) alpha={FGW_ALPHA} epsilon={LANES[lane]['eps']} "
                     f"max_iter={FGW_MAX_ITER} tol={FGW_TOL} loss={FGW_LOSS} solver={FGW_SOLVER}",
        "reference": {"bracket": [spec.left_stage, spec.right_stage],
                      "time_weight": spec.time_weight, "n_ref_per_stage": N_REF, "reg_k": REG_K},
        "permutation_semantics": "only X rows permuted; obs/var/obsm/uns identical to parent",
        "topk_used": assignment_meta["assignment"]["topk_used"],
        "top1_retention": assignment_meta["assignment"]["top1_retention"],
        "n_moved_vs_parent": assignment_meta["assignment"]["n_moved_vs_parent"],
        "seed": SEED, "source_only": True, "target_used": False,
    }
    contract_io = _contract_io()
    contract_io.write_candidate_from_parent(
        parent_path=parent_path, output_path=candidate_path, expression=X_new,
        row_names=[str(n) for n in parent.obs_names], normalization=NORMALIZATION,
        parent_sha256=spec.parent_sha256,
        metadata_updates={"ve_b4_t2_r1_match": json.dumps(provenance, sort_keys=True)},
    )
    diag = {"schema": "ve.b4.t2-r1.generation-diagnostics.v1", "atom": TASK_ID, "lane": lane,
            "board": BOARD, "candidate_sha256": sha256_file(candidate_path),
            "model": {"n_obs_parent": int(parent.n_obs),
                      "n_obs_candidate": int(len(placement)), "n_vars": int(parent.n_vars)},
            "provenance": provenance, "target_used": False}
    _write_json_atomic(candidate_path.parent / "generation_diagnostics.json", diag)
    _append_run_log(out, f"generate {lane}: sha256={diag['candidate_sha256'][:16]}")
    return {"step": "generate", "lane": lane, "sha256": diag["candidate_sha256"]}


def cmd_lane(run_dir: Path, lane: str) -> dict:
    """match -> generate -> contract -> checks -> nfs -> score -> determinism."""
    out = {"lane": lane}
    out["match"] = cmd_match(run_dir, lane)
    out["generate"] = cmd_generate(run_dir, lane)
    ld = lane_dir(run_dir, lane)
    out["contract"] = command_contract(ld, board=BOARD)
    if out["contract"]["status"] != "pass":
        raise RuntimeError(f"contract not pass for {lane}")
    out["checks"] = command_checks(ld, board=BOARD)
    if out["checks"]["status"] != "PASS":
        raise RuntimeError(f"protected checks FAIL for {lane}")
    out["nfs"] = command_nfs_proxy(ld, board=BOARD)
    out["score"] = command_score(ld, board=BOARD)
    # B4 determinism: re-match + re-generate must be byte-identical
    hold = ld / "intermediates" / BOARD
    T = np.load(hold / "transport_plan.npz")["T"]
    placement2, _ = global_match(T)
    placement1 = np.load(hold / "assignment.npz")["placement"]
    if not np.array_equal(placement1, placement2):
        raise AssertionError("matching not deterministic")
    import anndata as ad
    spec = BOARD_SPECS[BOARD]
    parent = ad.read_h5ad(REPO / spec.parent_path)
    rerun = ld / "candidates" / BOARD / "determinism_rerun.h5ad"
    contract_io = _contract_io()
    meta = json.loads((hold / "assignment_meta.json").read_text())
    prov = json.loads((ld / "candidates" / BOARD / "generation_diagnostics.json").read_text())["provenance"]
    try:
        contract_io.write_candidate_from_parent(
            parent_path=REPO / spec.parent_path, output_path=rerun,
            expression=_take_rows(parent.X, placement2),
            row_names=[str(n) for n in parent.obs_names], normalization=NORMALIZATION,
            parent_sha256=spec.parent_sha256,
            metadata_updates={"ve_b4_t2_r1_match": json.dumps(prov, sort_keys=True)})
        det = {"match_identical": True,
               "h5ad_byte_identical": sha256_file(rerun) == sha256_file(
                   ld / "candidates" / BOARD / "submission.h5ad")}
    finally:
        if rerun.exists():
            rerun.unlink()
    if not det["h5ad_byte_identical"]:
        raise AssertionError("candidate bytes not deterministic")
    _write_json_atomic(ld / "metrics" / BOARD / "determinism_b4.json", det)
    out["determinism"] = det
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["stage", "solve-l2", "solve-l2-worker", "match", "lane"])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--lane", default=None)
    ap.add_argument("--problem", type=Path, default=None)
    ap.add_argument("--coupling", type=Path, default=None)
    ap.add_argument("--meta", type=Path, default=None)
    args = ap.parse_args(argv)
    if args.command == "stage":
        print(json.dumps(cmd_stage(args.run_dir), indent=1, sort_keys=True))
    elif args.command == "solve-l2":
        print(json.dumps(cmd_solve_l2(args.run_dir), indent=1, sort_keys=True))
    elif args.command == "solve-l2-worker":
        meta = solve_l2_worker(args.problem, args.coupling, args.meta)
        print(json.dumps({"ok": True, "epsilon": meta["epsilon"]}))
    elif args.command == "match":
        print(json.dumps(cmd_match(args.run_dir, args.lane), indent=1, sort_keys=True))
    elif args.command == "lane":
        print(json.dumps(cmd_lane(args.run_dir, args.lane), indent=1, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
