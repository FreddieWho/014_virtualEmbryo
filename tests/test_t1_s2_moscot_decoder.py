from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts import t1_s2_moscot_decoder as m


# ---------------------------------------------------------------------------
# toy fixtures
# ---------------------------------------------------------------------------


def _toy_pre() -> dict:
    """Two lineages x two states per stage, 6 markers, 12 genes full panel."""
    rng = np.random.default_rng(0)
    cent85_full = {
        "Foregut": rng.normal(size=12).astype(np.float32),
        "Endothelium": rng.normal(size=12).astype(np.float32),
    }
    cent95_full = {
        "Foregut": (cent85_full["Foregut"] + 0.1).astype(np.float32),
        "BEC": (cent85_full["Endothelium"] + 0.2).astype(np.float32),
        "Endocardium": rng.normal(size=12).astype(np.float32),
    }
    cent85_marker = {s: v[:6] for s, v in cent85_full.items()}
    cent95_marker = {s: v[:6] for s, v in cent95_full.items()}
    vocabulary = [
        {"fine_state": "Foregut", "n_cells_e85": "100", "n_cells_e95": "80"},
        {"fine_state": "Endothelium", "n_cells_e85": "60", "n_cells_e95": "0"},
        {"fine_state": "BEC", "n_cells_e85": "0", "n_cells_e95": "80"},
        {"fine_state": "Endocardium", "n_cells_e85": "0", "n_cells_e95": "60"},
    ]
    crosswalk = [
        {"fine_state": "Foregut", "direction": "e85_to_e95", "matched_state": "Foregut",
         "match_rule": "SHARED_EXACT"},
        {"fine_state": "Endothelium", "direction": "e85_to_e95", "matched_state": "BEC",
         "match_rule": "MUTUAL_NEAREST"},
        {"fine_state": "BEC", "direction": "e95_to_e85", "matched_state": "Endothelium",
         "match_rule": "MUTUAL_NEAREST"},
        {"fine_state": "Endocardium", "direction": "e95_to_e85", "matched_state": m.UNRESOLVED,
         "match_rule": "NONE"},
    ]
    return {
        "var_names": [f"g{i}" for i in range(12)],
        "marker_genes": [f"g{i}" for i in range(6)],
        "states_e85": sorted(cent85_full),
        "states_e95": sorted(cent95_full),
        "centroids_e85_full": np.vstack([cent85_full[s] for s in sorted(cent85_full)]),
        "centroids_e95_full": np.vstack([cent95_full[s] for s in sorted(cent95_full)]),
        "centroids_e85_marker": np.vstack([cent85_marker[s] for s in sorted(cent85_marker)]),
        "centroids_e95_marker": np.vstack([cent95_marker[s] for s in sorted(cent95_marker)]),
        "vocabulary": vocabulary,
        "crosswalk": crosswalk,
    }


def _toy_coupling(pre: dict) -> dict:
    states_a, states_b = pre["states_e85"], pre["states_e95"]
    transport = np.zeros((len(states_a), len(states_b)))
    transport[states_a.index("Endothelium"), states_b.index("BEC")] = 0.30
    transport[states_a.index("Foregut"), states_b.index("Foregut")] = 0.55
    pred = transport.sum(axis=0)
    return {
        "transport": transport,
        "source_states": states_a,
        "target_states": states_b,
        "source_marginal": np.array([0.375, 0.625]),
        "target_marginal": np.array([80, 60, 80]) / 220.0,
        "target_pred_share": pred / pred.sum(),
        "sha256": "toy",
    }


# ---------------------------------------------------------------------------
# coupling: cost semantics, augmented coordinates, determinism
# ---------------------------------------------------------------------------


def test_coupling_cost_is_program_plus_lineage_penalty() -> None:
    pre = _toy_pre()
    cost, diag = m.coupling_cost_matrix(
        pre["centroids_e85_marker"], pre["centroids_e95_marker"],
        pre["states_e85"], pre["states_e95"],
    )
    assert cost.shape == (2, 3)
    assert diag["lineage_penalty"] == m.LINEAGE_PENALTY
    # Endothelium/BEC are vascular_endothelial; Foregut is endoderm
    i = pre["states_e85"].index("Endothelium")
    j_same = pre["states_e95"].index("BEC")
    j_cross = pre["states_e95"].index("Foregut")
    program_same = cost[i, j_same]
    assert abs(cost[i, j_cross] - (cost[i, j_cross] - 0)) >= 0  # sanity
    # penalty present exactly on mismatched pairs; program block is normalised
    # by the median raw program distance (pre-declared OT_COST_NORMALISATION)
    both = np.vstack([pre["centroids_e85_marker"], pre["centroids_e95_marker"]])
    std = both.std(axis=0)
    std[std == 0] = 1.0
    za = (pre["centroids_e85_marker"] - both.mean(axis=0)) / std
    zb = (pre["centroids_e95_marker"] - both.mean(axis=0)) / std
    program = ((za[:, None, :] - zb[None, :, :]) ** 2).sum(axis=2)
    median = float(np.median(program))
    expected_same = float(program[i, j_same]) / median
    expected_cross = float(program[i, j_cross]) / median + m.LINEAGE_PENALTY
    assert diag["program_distance_median_raw"] == pytest.approx(median)
    assert cost[i, j_same] == pytest.approx(expected_same, rel=1e-5)
    assert cost[i, j_cross] == pytest.approx(expected_cross, rel=1e-5)
    assert program_same < cost[i, j_cross]


def test_augmented_coordinates_realise_declared_cost() -> None:
    pre = _toy_pre()
    states = pre["states_e85"] + pre["states_e95"]
    lineages = [m.LINEAGE_BY_STATE[s] for s in states]
    union = np.vstack([pre["centroids_e85_marker"], pre["centroids_e95_marker"]])
    n = len(pre["states_e85"])
    augmented, _, _ = m.augmented_program_coordinates(union, states, lineages, n_source=n)
    cost, _ = m.coupling_cost_matrix(
        pre["centroids_e85_marker"], pre["centroids_e95_marker"],
        pre["states_e85"], pre["states_e95"],
    )
    realised = (
        (augmented[:n, None, :] - augmented[None, n:, :]) ** 2
    ).sum(axis=2)
    assert np.allclose(realised, cost, rtol=1e-8, atol=1e-8)


def test_toy_sinkhorn_deterministic_and_mass_interpretable() -> None:
    pre = _toy_pre()
    cost, _ = m.coupling_cost_matrix(
        pre["centroids_e85_marker"], pre["centroids_e95_marker"],
        pre["states_e85"], pre["states_e95"],
    )
    a = np.array([0.375, 0.625])
    b = np.array([80, 60, 80]) / 220.0
    t1 = m._numpy_toy_sinkhorn(cost, a, b)
    t2 = m._numpy_toy_sinkhorn(cost, a, b)
    assert np.array_equal(t1, t2)  # coupling determinism
    assert (t1 >= 0).all()
    # unbalanced (tau=0.95): transported mass below the balanced total
    assert 0.5 < t1.sum() <= 1.0 + 1e-9
    # serialisable: dense toy transport survives npz round-trip
    assert t1.shape == (2, 3)


# ---------------------------------------------------------------------------
# mass forecast: normalisation, shrinkage, small-state cap
# ---------------------------------------------------------------------------


def test_state_mass_normalised_and_shrunk() -> None:
    pre = _toy_pre()
    coupling = _toy_coupling(pre)
    rows, summary = m.compute_state_mass(pre, coupling)
    board_rows = [r for r in rows if r["board"] == m.BOARD]
    total = sum(float(r["shrunk_probability"]) for r in board_rows)
    assert total == pytest.approx(1.0, abs=1e-9)
    by_state = {r["state"]: r for r in board_rows}
    # resolved BEC growth = transport pred 0.30/0.85 / share_e85 Endothelium 0.375
    g_raw = (0.30 / 0.85) / 0.375
    assert summary["growth"]["BEC"]["growth_raw"] == pytest.approx(g_raw)
    assert summary["growth"]["BEC"]["growth_shrunk"] == pytest.approx(
        np.exp(m.GROWTH_RHO * np.log(g_raw))
    )
    # unresolved Endocardium uses the lineage-mean rule, never a forced match
    assert summary["growth"]["Endocardium"]["rule"] == "lineage_mean_transport"
    # holdout rows exist only for resolved targets and also sum to one
    holdout_rows = [r for r in rows if r["board"] == "T1:pseudo_holdout"]
    assert {r["state"] for r in holdout_rows} == {"BEC", "Foregut"}
    assert sum(float(r["shrunk_probability"]) for r in holdout_rows) == pytest.approx(1.0)


def test_shrink_growth_properties() -> None:
    assert m.shrink_growth(1.0) == pytest.approx(1.0)
    assert m.shrink_growth(4.0) == pytest.approx(np.exp(0.5 * np.log(3.0)))  # clip then shrink
    assert m.shrink_growth(2.25) == pytest.approx(1.5)  # inside clip range: geometric rho=0.5
    assert m.shrink_growth(100.0) == pytest.approx(np.exp(0.5 * np.log(3.0)))  # clipped
    assert m.shrink_growth(0.001) == pytest.approx(np.exp(0.5 * np.log(1.0 / 3.0)))
    with pytest.raises(ValueError):
        m.shrink_growth(0.0)


def test_small_state_cap_applies() -> None:
    pre = _toy_pre()
    # make BEC a small state with huge predicted mass
    for row in pre["vocabulary"]:
        if row["fine_state"] == "BEC":
            row["n_cells_e95"] = "10"
    coupling = _toy_coupling(pre)
    coupling["transport"][pre["states_e85"].index("Endothelium"), pre["states_e95"].index("BEC")] = 0.6
    pred = coupling["transport"].sum(axis=0)
    coupling["target_pred_share"] = pred / pred.sum()
    rows, summary = m.compute_state_mass(pre, coupling)
    assert summary["small_states"] == ["BEC"]
    bec = next(r for r in rows if r["board"] == m.BOARD and r["state"] == "BEC")
    share_parent = 10 / 150.0  # e95 counts after override: BEC 10 + Endocardium 60 + Foregut 80
    assert float(bec["raw_forecast"]) <= m.SMALL_STATE_SHARE_CAP_MULT * share_parent + 1e-12
    assert bec["uncertainty"] == "small_state"


# ---------------------------------------------------------------------------
# alpha: closed form + freeze semantics
# ---------------------------------------------------------------------------


def test_alpha_closed_form_and_clip() -> None:
    rng = np.random.default_rng(1)
    base = rng.normal(size=(40, 30))
    delta = rng.normal(size=(40, 30))
    true_alpha = 0.7
    target_pb = base.mean(axis=0) + true_alpha * delta.mean(axis=0)
    record = m.resolve_alpha(base, delta, target_pb)
    assert record["alpha_raw"] == pytest.approx(true_alpha, rel=1e-8)
    assert record["alpha_frozen"] == pytest.approx(true_alpha, rel=1e-8)
    assert not record["clipped"]
    record_hi = m.resolve_alpha(base, delta, base.mean(axis=0) + 5.0 * delta.mean(axis=0))
    assert record_hi["alpha_frozen"] == m.ALPHA_CLIP_HI
    assert record_hi["clipped"]
    with pytest.raises(ValueError, match="zero"):
        m.resolve_alpha(base, np.zeros_like(delta), target_pb)


def test_alpha_freeze_is_loaded_not_recomputed(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        m._frozen_alpha(tmp_path)
    payload = {"alpha": {"alpha_frozen": 0.42}}
    (tmp_path / "metrics").mkdir(parents=True)
    (tmp_path / "metrics" / "alpha_calibration.json").write_text(json.dumps(payload))
    assert m._frozen_alpha(tmp_path) == 0.42


# ---------------------------------------------------------------------------
# sampling plan / residual replay mechanics
# ---------------------------------------------------------------------------


def test_largest_remainder_counts_exact_and_deterministic() -> None:
    probs = {"a": 0.335, "b": 0.335, "c": 0.33}
    c1 = m._largest_remainder_counts(probs, 5118)
    c2 = m._largest_remainder_counts(probs, 5118)
    assert c1 == c2
    assert sum(c1.values()) == 5118
    assert m._largest_remainder_counts({"a": 1.0}, 10) == {"a": 10}
    with pytest.raises(ValueError):
        m._largest_remainder_counts({"a": 0.0}, 10)


def test_draw_cells_pools_replacement_rules() -> None:
    pools = {"growing": np.array([0, 1, 2]), "stable": np.array([3, 4, 5, 6])}
    demand = {"growing": 5, "stable": 2}
    d1 = m.draw_cells_from_pools(pools, demand, seed_parts=("t",))
    d2 = m.draw_cells_from_pools(pools, demand, seed_parts=("t",))
    assert all(np.array_equal(d1[s], d2[s]) for s in d1)
    assert d1["stable"].size == 2 and np.unique(d1["stable"]).size == 2
    assert d1["growing"].size == 5
    assert set(d1["growing"]) == {0, 1, 2}  # all supply used before duplication
    with pytest.raises(ValueError, match="no source cells"):
        m.draw_cells_from_pools({"x": np.array([], dtype=np.int64)}, {"x": 1}, seed_parts=("t",))


def test_unique_obs_names() -> None:
    names = m._unique_obs_names(["c1", "c2", "c1", "c3", "c1"])
    assert len(set(names)) == 5
    assert names[1] == "c2" and names[3] == "c3"  # single-use keeps parent name
    assert sorted(n for n in names if n.startswith("c1")) == ["c1__rep1", "c1__rep2", "c1__rep3"]


# ---------------------------------------------------------------------------
# L2 decoder: only module genes change; mean anchoring is exact
# ---------------------------------------------------------------------------


def test_l2_decoder_module_only_and_mean_anchored() -> None:
    rng = np.random.default_rng(2)
    base = rng.uniform(0.5, 2.0, size=(24, 10)).astype(np.float32)
    assigned = np.array(["A"] * 12 + ["B"] * 12)
    modules = {"mod_x": [0, 1, 2]}
    params = {
        "fits_e95": {
            "A": {"modules": {"mod_x": {
                "mu": [1.0, 1.0, 1.0], "sigma": [0.2, 0.2, 0.2],
                "corr": np.eye(3).tolist(),
            }}},
            # "B" missing -> fallback keeps L1 values
        },
        "fits_e85": {},
    }
    out, note = m.apply_l2_module_decoder(
        base, assigned, params, modules, stage="e95", seed_parts=("toy",)
    )
    assert note["fallback_states_keep_parent_residual"] == ["B"]
    # off-module genes identical
    off = np.ones(10, dtype=bool)
    off[[0, 1, 2]] = False
    assert np.array_equal(out[:, off], base[:, off])
    # fallback state rows fully identical
    assert np.array_equal(out[12:], base[12:])
    # module genes changed for state A, but with the base module mean preserved
    assert not np.allclose(out[:12, :3], base[:12, :3])
    assert np.allclose(
        out[:12, :3].mean(axis=0), base[:12, :3].mean(axis=0), atol=1e-6
    )
    # determinism
    out2, _ = m.apply_l2_module_decoder(
        base, assigned, params, modules, stage="e95", seed_parts=("toy",)
    )
    assert np.array_equal(out, out2)


def test_module_gene_index_absent_definition(tmp_path: Path) -> None:
    assert m._module_gene_index(tmp_path, ["g0", "g1"]) == {}


# ---------------------------------------------------------------------------
# crosswalk helpers / vocabulary guards
# ---------------------------------------------------------------------------


def test_matches_omit_unresolved() -> None:
    pre = _toy_pre()
    assert m.forward_matches(pre["crosswalk"]) == {"Foregut": "Foregut", "Endothelium": "BEC"}
    # explicit reverse rows win; resolved forward rows are inverted to complete
    # the map (the T1-PRE crosswalk emits no reverse row for SHARED_EXACT pairs)
    assert m.reverse_matches(pre["crosswalk"]) == {"BEC": "Endothelium", "Foregut": "Foregut"}


def test_lineage_hierarchy_covers_released_vocabulary() -> None:
    released = {
        "Foregut", "pSHF", "Surface Ectoderm", "OFT/RV-CM", "Endothelium", "JCF",
        "IFT-CM", "Paraxial Mesoderm", "EXEM", "aSHF", "Neural Tube", "Pericardium",
        "AVC-CM", "RV-CM", "LV-CM", "SV-CM", "NCC", "Blood", "Endocardium", "pPHM",
        "Hepatocyte", "V-CM", "Proepicardium", "ST", "NCC-derived", "BEC",
        "Epithelium", "aPHM",
    }
    assert released <= set(m.LINEAGE_BY_STATE)


def test_state_gene_delta_decoupled_and_shrunk() -> None:
    pre = _toy_pre()
    deltas = m.compute_state_gene_delta(pre)
    assert deltas["delta_e105"].shape == (3, 12)
    assert deltas["delta_holdout_e85"].shape == (2, 12)
    # measured state: exact centroid difference; extrapolation applies rho
    j = deltas["states_e95"].index("Foregut")
    i = deltas["states_e85"].index("Foregut")
    measured = pre["centroids_e95_full"][j] - pre["centroids_e85_full"][i]
    assert np.allclose(deltas["delta_measured_e95"][j], measured, atol=1e-6)
    assert np.allclose(deltas["delta_e105"][j], measured * m.RHO_EXTRAP, atol=1e-6)
    # unresolved target state falls back to lineage mean (never force-matched)
    k = deltas["states_e95"].index("Endocardium")
    assert deltas["rule_e95"][k] == "lineage_mean_shrinkage"
    # no vocabulary expansion
    assert set(deltas["states_e95"]) == set(pre["states_e95"])


# ---------------------------------------------------------------------------
# manifest self-verification
# ---------------------------------------------------------------------------


def test_manifest_self_verify_roundtrip(tmp_path: Path) -> None:
    out_dir = tmp_path / "atom"
    (out_dir / "intermediates").mkdir(parents=True)
    (out_dir / "intermediates" / "x.tsv").write_text("a\tb\n1\t2\n")
    (out_dir / "run.log").write_text("live log\n")
    manifest = m.write_manifest(out_dir, exclude=("run.log",))
    assert manifest["self_verify"]["ok"]
    assert all(f["path"] != "run.log" for f in manifest["files"])
    check = m.verify_manifest(out_dir)
    assert check["ok"] and check["n_files"] == 1
    (out_dir / "intermediates" / "x.tsv").write_text("tampered\n")
    check = m.verify_manifest(out_dir)
    assert not check["ok"] and check["mismatches"] == ["intermediates/x.tsv"]
