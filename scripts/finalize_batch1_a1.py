#!/usr/bin/env python3
"""Record fixed public pseudo-holdout scores for the B1-A1 final set.

This utility never records a server submission ID or treats a public proxy
score as a leaderboard result. It only enriches the generated manifests and
creates the score-pending RESULT handoff.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ATOM_ID = "B1-A1"
EXPECTED_LANES = {"L1_FORMAL_LOG_RMS", "L2_ALL_STAGE_LOG_RMS_OLS"}
EXPECTED_BOARDS = {
    "T2_embryo_val_interp",
    "T2_heart_val_interp",
    "T2_heart_val_extrap",
}
PROXY_BY_BOARD = {
    "T2_embryo_val_interp": "T2_embryo_interp_proxy",
    "T2_heart_val_interp": "T2_heart_interp_proxy",
    "T2_heart_val_extrap": "T2_heart_extrap_proxy",
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + chr(10),
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _result_markdown(candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# B1-A1 RESULT",
        "",
        "## Status",
        "",
        "- status: SCORE_PENDING",
        "- overall decision: PER_BOARD",
        "- task: T2",
        "- final lanes: L1_FORMAL_LOG_RMS + L2_ALL_STAGE_LOG_RMS_OLS",
        "- boards: T2_embryo_val_interp / T2_heart_val_interp / T2_heart_val_extrap",
        "- final artifacts: 6",
        "- local public proxy scores: 6/6",
        "- server scores: 0/6",
        "- submission mode: manual_user_upload",
        "",
        "## Final candidates",
        "",
        "| Lane | Board | Candidate ID | SHA256 | Local scale_log_ratio | Local TSR | Server status | Decision |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for item in candidates:
        raw = item["local_metrics"]
        value = float(raw["scale_log_ratio"])
        lines.append(
            f"| {item['lane_id']} | {item['board']} | {item['candidate_id']} | "
            f"{item['sha256']} | {value:.6g} | {value:.6g} | score_pending | "
            "awaiting_server_score |"
        )
    lines.extend(
        [
            "",
            "Local values above are fixed public pseudo-holdout evidence only; they are not hidden-target or leaderboard scores.",
            "",
            "## Change",
            "",
            "L1 uses the prescribed piecewise log-RMS interpolation/last-slope extrapolation. L2 uses an equal-weight OLS trend over all observed stages. Both lanes change only the first three spatial coordinates by a positive uniform scale about the base centroid.",
            "",
            "## Protected checks",
            "",
            "| Candidate ID | X checksum | obs/var order | spatial shape | 15-NN check | Target used |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in candidates:
        checks = item["protected_checks"]
        lines.append(
            f"| {item['candidate_id']} | {checks['expression_checksum_unchanged']} | "
            f"{checks['obs_order_unchanged'] and checks['var_order_unchanged']} | "
            f"{checks['spatial_shape_unchanged']} | {checks['knn15_exact']} | "
            f"{checks['target_used']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "All six contract-valid artifacts remain ready for manual upload; the per-board winner is intentionally unresolved until both lane scores for that board are returned.",
            "",
            "## Only next action",
            "",
            "等待用户人工上传六个 artifact 并回填 submission ID、原始服务器分数和证据。",
            "",
        ]
    )
    return chr(10).join(lines)


def finalize(
    atom_root: Path = PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID,
) -> dict[str, Any]:
    atom_root = Path(atom_root)
    freeze_path = atom_root / "FINAL_SET_MANIFEST.json"
    freeze = _load_json(freeze_path)
    candidates = freeze.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 6:
        raise ValueError("B1-A1 freeze manifest must contain exactly six candidates")
    if {item["lane_id"] for item in candidates} != EXPECTED_LANES:
        raise ValueError("B1-A1 freeze manifest has an unexpected lane set")
    if {item["board"] for item in candidates} != EXPECTED_BOARDS:
        raise ValueError("B1-A1 freeze manifest has an unexpected board set")

    enriched: list[dict[str, Any]] = []
    for item in candidates:
        lane = str(item["lane_id"])
        board = str(item["board"])
        manifest_path = PROJECT_ROOT / str(item["manifest"])
        manifest = _load_json(manifest_path)
        score_path = atom_root / "metrics" / lane / board / "local_or_official.json"
        score = _load_json(score_path)
        raw_metrics = score.get("metrics")
        if not isinstance(raw_metrics, dict) or "scale_log_ratio" not in raw_metrics:
            raise ValueError(f"{score_path}: missing raw scale_log_ratio")
        manifest["primary_metrics"] = {
            "scale_log_ratio": float(raw_metrics["scale_log_ratio"]),
            "TSR": float(raw_metrics["scale_log_ratio"]),
            "source": "public_pseudo_holdout",
            "status": "COMPLETE",
        }
        manifest["score_status"] = "score_pending"
        manifest["local_score_source"] = "public_pseudo_holdout"
        manifest["local_score_file"] = str(
            score_path.resolve().relative_to(PROJECT_ROOT)
        )
        _write_json(manifest_path, manifest)

        score["status"] = "COMPLETE"
        score["score_type"] = "public_pseudo_holdout"
        score["server_score"] = False
        score["proxy_name"] = PROXY_BY_BOARD[board]
        score["target_used_for_generation"] = False
        _write_json(score_path, score)
        enriched.append(
            {
                "lane_id": lane,
                "board": board,
                "candidate_id": manifest["candidate_id"],
                "sha256": manifest["sha256"],
                "local_metrics": raw_metrics,
                "protected_checks": manifest["protected_checks"],
            }
        )

    freeze["local_score_status"] = "complete"
    freeze["local_score_count"] = 6
    freeze["score_status"] = "score_pending"
    _write_json(freeze_path, freeze)
    result_path = atom_root / "RESULT.md"
    result_path.write_text(_result_markdown(enriched), encoding="utf-8")
    return {
        "atom_id": ATOM_ID,
        "local_score_count": 6,
        "server_score_count": 0,
        "status": "SCORE_PENDING",
        "result": str(result_path.resolve()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--atom-root",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID,
    )
    args = parser.parse_args(argv)
    print(json.dumps(finalize(args.atom_root), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
