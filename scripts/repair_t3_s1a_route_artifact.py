#!/usr/bin/env python3
"""Create a stable post-run route report without changing scientific outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from t3_s1a_state_join import _write_artifact_manifest, sha256_file


def repair(output_dir: Path) -> dict[str, str]:
    output_dir = output_dir.resolve()
    source_report = output_dir / "metrics/gate_report.v2.json"
    if not source_report.is_file():
        raise FileNotFoundError(source_report)
    report = json.loads(source_report.read_text(encoding="utf-8"))
    if report.get("schema") != "gate_report.v2":
        raise ValueError("unexpected route gate schema")
    stable_manifest = _write_artifact_manifest(
        output_dir, manifest_name="artifact_manifest.stable.json"
    )
    stable_relative = stable_manifest.relative_to(output_dir).as_posix()
    stable_hash = sha256_file(stable_manifest)
    for route in report.get("routes", []):
        route["artifact_manifest_path"] = stable_relative
        route["artifact_manifest_sha256"] = stable_hash
    repaired_report = output_dir / "metrics/gate_report.v2.repaired.json"
    repaired_report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    repair_report = output_dir / "metrics/route_artifact_repair.json"
    repair_report.write_text(
        json.dumps(
            {
                "schema": "ve.t3.s1a-route-artifact-repair.v1",
                "task": "T3-S1A-STATE-JOIN",
                "reason": "The original artifact manifest captured transient SQLite -shm/-wal runtime files.",
                "scientific_outputs_changed": False,
                "source_gate_report": source_report.relative_to(output_dir).as_posix(),
                "source_gate_report_sha256": sha256_file(source_report),
                "stable_artifact_manifest": stable_relative,
                "stable_artifact_manifest_sha256": stable_hash,
                "repaired_gate_report": repaired_report.relative_to(output_dir).as_posix(),
                "repaired_gate_report_sha256": sha256_file(repaired_report),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "stable_manifest": str(stable_manifest),
        "repaired_gate_report": str(repaired_report),
        "repair_report": str(repair_report),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(repair(args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
