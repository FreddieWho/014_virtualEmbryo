from __future__ import annotations

import csv
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pytest

from scripts import t1_pre_harmonize as m


def _write_toy_stage(path: Path, labels: list[str], X: np.ndarray, genes: list[str]) -> None:
    import pandas as pd

    adata = ad.AnnData(
        X=np.asarray(X, dtype=np.float32),
        obs=pd.DataFrame({"celltype": pd.Categorical(labels)}),
        var=pd.DataFrame(index=pd.Index(genes)),
    )
    adata.write_h5ad(path)


def _toy_centroids() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Two shared states, one cleanly mutual pair, one one-way pair."""
    cent_e85 = {
        "Foregut": np.array([1.0, 0.0, 0.0, 0.5]),
        "Endothelium": np.array([0.0, 1.0, 0.1, 0.0]),
        "RV-CM": np.array([0.0, 0.1, 1.0, 0.0]),
        "EXEM": np.array([0.2, 0.2, 0.2, 1.0]),
    }
    cent_e95 = {
        "Foregut": np.array([0.9, 0.05, 0.0, 0.5]),
        "BEC": np.array([0.0, 0.95, 0.05, 0.0]),
        "Endocardium": np.array([0.0, 0.9, 0.2, 0.1]),  # nearest of Endothelium? no: BEC wins
        "V-CM": np.array([0.0, 0.1, 0.95, 0.0]),
    }
    return cent_e85, cent_e95


def test_vocabulary_schema_and_stage_presence() -> None:
    rows = m.vocabulary_rows(
        {"Foregut": 10, "Endothelium": 4}, {"Foregut": 8, "Endocardium": 2}
    )
    assert [r["fine_state"] for r in rows] == ["Endocardium", "Endothelium", "Foregut"]
    by_state = {r["fine_state"]: r for r in rows}
    assert by_state["Foregut"]["vocabulary_status"] == "SHARED_EXACT"
    assert by_state["Foregut"]["stage_presence"] == "both"
    assert by_state["Endothelium"]["vocabulary_status"] == "SOURCE_ONLY"
    assert by_state["Endocardium"]["vocabulary_status"] == "TARGET_ONLY"
    assert by_state["Endocardium"]["lineage"] == "vascular_endothelial"
    assert by_state["Endocardium"]["state_family"] == "endocardium"
    for row in rows:
        assert set(m.VOCABULARY_TSV_FIELDS) <= set(row)
        assert float(row["share_e85"]) >= 0.0
        assert float(row["share_e95"]) >= 0.0


def test_vocabulary_fails_closed_on_unknown_label() -> None:
    with pytest.raises(ValueError, match="pre-declared hierarchy"):
        m.vocabulary_rows({"TotallyUnknownState": 3}, {})


def test_hierarchy_covers_all_released_labels() -> None:
    # the released E8.5/E9.5 label union must never hit the fail-closed path
    released = {
        "Foregut", "pSHF", "Surface Ectoderm", "OFT/RV-CM", "Endothelium", "JCF",
        "IFT-CM", "Paraxial Mesoderm", "EXEM", "aSHF", "Neural Tube", "Pericardium",
        "AVC-CM", "RV-CM", "LV-CM", "SV-CM", "NCC", "Blood", "Endocardium", "pPHM",
        "Hepatocyte", "V-CM", "Proepicardium", "ST", "NCC-derived", "BEC",
        "Epithelium", "aPHM",
    }
    assert released <= set(m.STATE_HIERARCHY)


def test_crosswalk_shared_exact_and_mutual_nearest() -> None:
    cent_e85, cent_e95 = _toy_centroids()
    rows = m.build_crosswalk_rows(
        cent_e85,
        cent_e95,
        {s: 10 for s in cent_e85},
        {s: 10 for s in cent_e95},
    )
    by_key = {(r["fine_state"], r["direction"]): r for r in rows}
    foregut = by_key[("Foregut", "e85_to_e95")]
    assert foregut["match_rule"] == "SHARED_EXACT"
    assert foregut["matched_state"] == "Foregut"
    assert foregut["confidence"] == "HIGH"
    endo = by_key[("Endothelium", "e85_to_e95")]
    assert endo["match_rule"] == "MUTUAL_NEAREST"
    assert endo["matched_state"] == "BEC"
    rvcm = by_key[("RV-CM", "e85_to_e95")]
    assert rvcm["matched_state"] == "V-CM"
    assert rvcm["mutual_nearest"] == "True"


def test_crosswalk_unresolved_when_not_mutual() -> None:
    # Endocardium is closer to Endothelium than to anything else, but
    # Endothelium's own best match is BEC -> Endocardium stays UNRESOLVED.
    cent_e85, cent_e95 = _toy_centroids()
    rows = m.build_crosswalk_rows(
        cent_e85,
        cent_e95,
        {s: 10 for s in cent_e85},
        {s: 10 for s in cent_e95},
    )
    by_key = {(r["fine_state"], r["direction"]): r for r in rows}
    endocardium = by_key[("Endocardium", "e95_to_e85")]
    assert endocardium["matched_state"] == m.UNRESOLVED
    assert endocardium["match_rule"] == "NONE"
    assert endocardium["confidence"] == "LOW"
    assert "UNRESOLVED" in endocardium["resolution_reason"]


def test_crosswalk_unresolved_below_tau_even_when_mutual() -> None:
    cent_e85 = {"EXEM": np.array([1.0, 0.0, 0.0])}
    cent_e95 = {"ST": np.array([0.6, 0.8, 0.0])}  # cosine = 0.6 < tau 0.70
    rows = m.build_crosswalk_rows(cent_e85, cent_e95, {"EXEM": 10}, {"ST": 10})
    forward = [r for r in rows if r["direction"] == "e85_to_e95"][0]
    assert forward["mutual_nearest"] == "True"
    assert forward["matched_state"] == m.UNRESOLVED
    assert forward["confidence"] == "LOW"
    assert "below tau" in forward["resolution_reason"]


def test_crosswalk_is_deterministic(tmp_path: Path) -> None:
    cent_e85, cent_e95 = _toy_centroids()
    counts_a = {s: 10 for s in cent_e85}
    counts_b = {s: 10 for s in cent_e95}
    payloads = []
    for _ in range(2):
        rows = m.build_crosswalk_rows(cent_e85, cent_e95, counts_a, counts_b)
        path = tmp_path / "cw.tsv"
        m._write_tsv_atomic(path, rows, m.CROSSWALK_TSV_FIELDS)
        payloads.append(path.read_bytes())
    assert payloads[0] == payloads[1]


def test_bootstrap_recovery_is_deterministic() -> None:
    rng = np.random.default_rng(0)
    labels_e85 = np.array(["Foregut"] * 20 + ["Endothelium"] * 20)
    labels_e95 = np.array(["Foregut"] * 20 + ["BEC"] * 20)
    marker_e85 = np.vstack(
        [rng.normal(loc=[2, 0], scale=0.1, size=(20, 2)), rng.normal(loc=[0, 2], scale=0.1, size=(20, 2))]
    )
    marker_e95 = np.vstack(
        [rng.normal(loc=[2, 0], scale=0.1, size=(20, 2)), rng.normal(loc=[0, 2], scale=0.1, size=(20, 2))]
    )
    first = m.bootstrap_crosswalk_stability(
        marker_e85, labels_e85, marker_e95, labels_e95, rounds=3, seed=123
    )
    second = m.bootstrap_crosswalk_stability(
        marker_e85, labels_e85, marker_e95, labels_e95, rounds=3, seed=123
    )
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    # cleanly separated clusters: both shared-exact-free edges recover every round
    assert first["min_recovery"] == 1.0


def test_projection_replays_cells_with_state_delta_and_clips(tmp_path: Path) -> None:
    genes = ["G1", "G2", "G3"]
    labels = ["Foregut", "Foregut", "Endothelium", "EXEM"]
    X = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 0.2, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    source = tmp_path / "e85.h5ad"
    _write_toy_stage(source, labels, X, genes)
    crosswalk = [
        {
            "fine_state": "Foregut",
            "direction": "e85_to_e95",
            "matched_state": "Foregut",
            "match_rule": "SHARED_EXACT",
        }
    ]
    cent_e85 = {
        "Foregut": np.array([1.0, 0.1, 0.0], dtype=np.float32),
        "Endothelium": np.array([0.0, 1.0, 0.0], dtype=np.float32),
        "EXEM": np.array([0.0, 0.0, 1.0], dtype=np.float32),
    }
    cent_e95 = {
        "Foregut": np.array([2.0, 0.1, 0.0], dtype=np.float32),
        "Endocardium": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    }
    out_path = tmp_path / "projection.h5ad"
    result = m.run_projection(
        source_path=source,
        crosswalk_rows=crosswalk,
        centroids_full_e85=cent_e85,
        centroids_full_e95=cent_e95,
        output_path=out_path,
        counts_e85={"Foregut": 2, "Endothelium": 1, "EXEM": 1},
        counts_e95={"Foregut": 5, "Endocardium": 5},
        n_cells=4,
        seed=m.SEED,
    )
    assert result["n_obs"] == 4
    out = ad.read_h5ad(out_path)
    pred = np.asarray(out.X)
    assert (pred >= 0).all(), "projection must stay non-negative"
    assert set(out.obs["projection_rule"]) <= {
        "matched_state_delta",
        "unresolved_global_delta",
    }
    assert not out.obsm, "T1 outputs must not carry obsm"
    # Foregut matched: delta = [+1, 0, 0] -> every Foregut cell gains exactly 1 on G1
    fg = np.asarray(out.obs["celltype"].astype(str)) == "Foregut"
    assert np.allclose(pred[fg][:, 0] - np.asarray([1.0, 1.0]), 1.0)
    assert result["output_sha256"] == m.sha256_file(out_path)


def test_projection_refuses_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "exists.h5ad"
    _write_toy_stage(target, ["Foregut"], np.ones((1, 1), dtype=np.float32), ["G1"])
    with pytest.raises(FileExistsError):
        m.run_projection(
            source_path=target,
            crosswalk_rows=[],
            centroids_full_e85={"Foregut": np.zeros(1, dtype=np.float32)},
            centroids_full_e95={"Foregut": np.zeros(1, dtype=np.float32)},
            output_path=target,
            n_cells=1,
        )


def test_manifest_roundtrip_and_tamper_detection(tmp_path: Path) -> None:
    out_dir = tmp_path / "atom"
    (out_dir / "metrics").mkdir(parents=True)
    (out_dir / "intermediates").mkdir()
    (out_dir / "metrics" / "state_stability.json").write_text('{"a": 1}\n', encoding="utf-8")
    (out_dir / "intermediates" / "state_vocabulary.tsv").write_text("x\n", encoding="utf-8")
    (out_dir / "run.log").write_text("live\n", encoding="utf-8")
    manifest = m.write_manifest(out_dir, exclude=("run.log",))
    assert manifest["self_verify"]["ok"]
    paths = {f["path"] for f in manifest["files"]}
    assert "run.log" not in paths
    assert "metrics/state_stability.json" in paths
    for entry in manifest["files"]:
        assert entry["bytes"] == entry["size"]
        assert len(entry["sha256"]) == 64
    verification = m.verify_manifest(out_dir)
    assert verification["ok"]
    (out_dir / "intermediates" / "state_vocabulary.tsv").write_text("tampered\n", encoding="utf-8")
    verification = m.verify_manifest(out_dir)
    assert not verification["ok"]
    assert verification["mismatches"] == ["intermediates/state_vocabulary.tsv"]


def test_scorer_collect_reports_not_launched(tmp_path: Path) -> None:
    record = m.scorer_collect(tmp_path)
    assert record["status"] == "NOT_LAUNCHED"


def test_scorer_collect_completes_from_rc_and_output(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics"
    metrics.mkdir(parents=True)
    out_tmp = metrics / "scorer_output.tmp.json"
    out_tmp.write_text(
        json.dumps(
            {
                "meta": {"genes": m.EXPECTED_GENES, "truth_cells": m.EXPECTED_TRUTH_CELLS, "prediction_cells": 4},
                "metrics": {"de_score": 0.5},
            }
        ),
        encoding="utf-8",
    )
    rc_file = metrics / "scorer.rc"
    rc_file.write_text("0", encoding="utf-8")
    record = {
        "schema": "ve.t1.pre-harmonize-scorer-run.v1",
        "status": "RUNNING",
        "pid": 99999999,  # dead pid; rc file takes precedence
        "log_path": str(tmp_path / "scorer_run.log"),
        "out_tmp": str(out_tmp),
        "out_final": str(metrics / "scorer_output.json"),
        "rc_file": str(rc_file),
        "started_monotonic": 0.0,
        "rss_samples": [],
        "peak_rss_bytes": None,
    }
    m._write_json_atomic(metrics / "scorer_run.json", record)
    collected = m.scorer_collect(tmp_path)
    assert collected["status"] == "DONE"
    assert collected["exit_code"] == 0
    assert collected["result_checks"]["genes_match"]
    assert collected["result_checks"]["truth_cells_match"]
    assert (metrics / "scorer_output.json").is_file()
    assert collected["result_sha256"] == m.sha256_file(metrics / "scorer_output.json")


def test_scorer_collect_marks_failed_without_rc(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics"
    metrics.mkdir(parents=True)
    record = {
        "schema": "ve.t1.pre-harmonize-scorer-run.v1",
        "status": "RUNNING",
        "pid": 99999999,
        "log_path": str(tmp_path / "scorer_run.log"),
        "out_tmp": str(metrics / "scorer_output.tmp.json"),
        "out_final": str(metrics / "scorer_output.json"),
        "rc_file": str(metrics / "scorer.rc"),
        "started_monotonic": 0.0,
        "rss_samples": [],
    }
    m._write_json_atomic(metrics / "scorer_run.json", record)
    collected = m.scorer_collect(tmp_path)
    assert collected["status"] == "FAILED"
    assert "without an rc file" in collected["failure_reason"]


def test_small_state_sensitivity_flags_below_threshold() -> None:
    result = m.small_state_sensitivity(
        {"Foregut": 100, "NCC": 10}, {"Foregut": 100, "NCC": 47}, [], min_cells=50
    )
    assert result["states_below_threshold"] == ["NCC", "NCC"]
    assert result["n_states_below"] == 2
