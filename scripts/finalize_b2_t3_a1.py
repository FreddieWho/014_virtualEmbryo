#!/usr/bin/env python3
"""Freeze the already-generated B2-T3-A1 artifacts without server submission."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATOM = "B2-T3-A1"
ATOM_ROOT = ROOT / "artifacts" / "atomic_batch2" / ATOM
LANES = {
    "L1_STRICT_WT_DIRECT": "v0006_b2_t3_a1_l1",
    "L2_GATA4_GATA6_CONDITION_AWARE": "v0007_b2_t3_a1_l2",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    config_text = """active_atom: B2-T3-A1
seed: 20260829
parent: submissions/scored/baseline-001/T3_gata4/submission.h5ad
external_model_input: infra/external_data/sanitized/T3/B2-T3-A1/EMTAB6967
metadata_only_fallback: E-MTAB-11763
lineage_gate: p_mesp1_lineage >= 0.5
max_final_lanes: 2
server_submission: false
stop_after_atom: true
L1_STRICT_WT_DIRECT:
  max_panel_fraction: 0.10
  target: Gata4
L2_GATA4_GATA6_CONDITION_AWARE:
  max_panel_fraction: 0.15
  target: Gata4_plus_Gata6_half_dose
"""
    (ATOM_ROOT / "config_resolved.yaml").write_text(config_text, encoding="utf-8")
    lane_results: dict[str, dict[str, object]] = {}
    for lane, version in LANES.items():
        lane_dir = ATOM_ROOT / "submissions" / "T3_gata4" / lane
        artifact = lane_dir / "prediction.h5ad"
        digest = sha256(artifact)
        score = json.loads((ATOM_ROOT / "metrics" / lane / "local_score.json").read_text(encoding="utf-8"))
        manifest = json.loads((lane_dir / "MANIFEST.json").read_text(encoding="utf-8"))
        manifest.update({
            "candidate_id": f"B2-T3-A1-{lane}-20260830",
            "artifact_sha256": digest,
            "local_score": score,
            "score_status": "score_pending",
            "decision": "HOLD_AS_COMPONENT",
            "decision_reason": "Local source-only diagnostic is not a Gata4 held-out score; implementation uses auditable local WT-only approximations of the two pinned methods.",
        })
        dump(lane_dir / "MANIFEST.json", manifest)
        canonical = ROOT / "submissions" / "candidates" / "T3_gata4" / version / "submission.h5ad"
        canonical.parent.mkdir(parents=True, exist_ok=True)
        if canonical.exists() and sha256(canonical) != digest:
            raise RuntimeError(f"refusing to overwrite a different canonical candidate: {canonical}")
        if not canonical.exists():
            shutil.copy2(artifact, canonical)
        if sha256(canonical) != digest:
            raise RuntimeError(f"canonical SHA mismatch: {canonical}")
        final_manifest = {
            "candidate_id": manifest["candidate_id"], "lane_id": lane, "board": "T3_gata4", "task": "T3",
            "submission_file": canonical.relative_to(ROOT).as_posix(), "sha256": digest,
            "n_obs": 7449, "n_vars": 500, "score_status": "score_pending", "server_submission": False,
        }
        dump(ATOM_ROOT / "final" / lane / "T3_gata4" / "MANIFEST.json", final_manifest)
        for filename in ("METHOD_DISCLOSURE.md", "config_resolved.yaml"):
            source = ATOM_ROOT / filename
            destination = lane_dir / filename
            shutil.copy2(source, destination)
        (lane_dir / "RESULT.md").write_text(
            f"# {lane}\n\n- contract: PASS\n- protected checks: PASS\n- local diagnostic: `metrics/local_score.json`\n- server status: `score_pending`; no server submission\n- decision: `HOLD_AS_COMPONENT`\n- artifact SHA256: `{digest}`\n",
            encoding="utf-8",
        )
        shutil.copy2(ATOM_ROOT / "run.log", lane_dir / "run.log")
        lane_results[lane] = {"manifest": manifest, "canonical": final_manifest, "sha256": digest}

    dump(ATOM_ROOT / "FINAL_SET_MANIFEST.json", {
        "atom_id": ATOM, "task": "T3", "server_submission": False,
        "candidates": [{"lane_id": lane, "board": "T3_gata4", "sha256": value["sha256"]} for lane, value in lane_results.items()],
    })
    root_manifest = json.loads((ATOM_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    root_manifest.update({"final_set_manifest": str((ATOM_ROOT / "FINAL_SET_MANIFEST.json").relative_to(ROOT)), "server_submission": False, "decision": "HOLD_AS_COMPONENT", "lanes": {lane: {"artifact": value["manifest"]["prediction"], "canonical": value["canonical"]["submission_file"], "sha256": value["sha256"], "status": "score_pending", "decision": "HOLD_AS_COMPONENT"} for lane, value in lane_results.items()}})
    dump(ATOM_ROOT / "MANIFEST.json", root_manifest)
    kill = json.loads((ATOM_ROOT / "kill_test" / "identity_score.json").read_text(encoding="utf-8"))
    kill_pipeline = json.loads((ATOM_ROOT / "kill_test" / "pipeline_score.json").read_text(encoding="utf-8"))
    result_text = f"""# B2-T3-A1 RESULT\n\n## 技术路线\n\n仅执行 active atom `B2-T3-A1`。以当前 T3 `wt_identity` 为 parent；对 sanitized E-MTAB-6967 WT 表达做固定 seed 的 stage×celltype 抽样；CellOracle-style state-wise WT regression 与 scTenifold-style global WT conditional network 形成两票；GSE52123 E12.5 WT GATA4 ChIP 仅作 promoter +/-5 kb directness；连续 lineage probability 以 0.5 为 gate。L1/L2 分别遵守 50/500 与 75/500 上限。\n\n## 结果/证据\n\n| lane | selected downstream | contract | protected | de_score | de_direction | severity_slope | status |\n|---|---:|---|---|---:|---:|---:|---|\n"""
    for lane, value in lane_results.items():
        score = value["manifest"]["local_score"]["metrics"]
        result_text += f"| {lane} | {len(value['manifest']['selected_downstream_genes'])} | PASS | PASS | {score['de_score']} | {score['de_direction']} | {score['severity_slope']} | score_pending |\n"
    result_text += f"""\nMab21l2 source-only diagnostic: identity `de_score={kill['metrics']['de_score']}`, `de_direction={kill['metrics']['de_direction']}`; pipeline `de_score={kill_pipeline['metrics']['de_score']}`, `de_direction={kill_pipeline['metrics']['de_direction']}`. This is a cross-perturbation diagnostic, not a Gata4 leaderboard score.\n\n## 结论\n\n两条候选均完成本地 contract/protected 检查，但结论为 `HOLD_AS_COMPONENT`：服务器未提交，分数仍为 `score_pending`；E-MTAB-11763 只有 metadata-only fallback；两个方法是有审计边界的本地实现而非上游包执行；不得宣称 leaderboard 或 Gata4 机制进步。\n"""
    (ATOM_ROOT / "RESULT.md").write_text(result_text, encoding="utf-8")
    (ATOM_ROOT / "config_resolved.yaml").write_text("""active_atom: B2-T3-A1\nseed: 20260829\nparent: submissions/scored/baseline-001/T3_gata4/submission.h5ad\nexternal_model_input: infra/external_data/sanitized/T3/B2-T3-A1/EMTAB6967\nmetadata_only_fallback: E-MTAB-11763\nlineage_gate: p_mesp1_lineage >= 0.5\nmax_final_lanes: 2\nserver_submission: false\nstop_after_atom: true\nL1_STRICT_WT_DIRECT:\n  max_panel_fraction: 0.10\n  target: Gata4\nL2_GATA4_GATA6_CONDITION_AWARE:\n  max_panel_fraction: 0.15\n  target: Gata4_plus_Gata6_half_dose\n""", encoding="utf-8")
    with (ATOM_ROOT / "run.log").open("a", encoding="utf-8") as handle:
        handle.write("finalized=2026-08-30\nserver_submission=false\n")
        for lane, value in lane_results.items():
            metrics = value["manifest"]["local_score"]["metrics"]
            handle.write(f"final_score {lane} de_score={metrics['de_score']} de_direction={metrics['de_direction']} severity_slope={metrics['severity_slope']}\n")
        handle.write(f"kill_test identity_de_score={kill['metrics']['de_score']} pipeline_de_score={kill_pipeline['metrics']['de_score']} identity_de_direction={kill['metrics']['de_direction']} pipeline_de_direction={kill_pipeline['metrics']['de_direction']}\n")
    for lane in lane_results:
        shutil.copy2(ATOM_ROOT / "run.log", ATOM_ROOT / "submissions" / "T3_gata4" / lane / "run.log")
    print(json.dumps({"atom": ATOM, "lanes": lane_results, "decision": "HOLD_AS_COMPONENT"}, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
