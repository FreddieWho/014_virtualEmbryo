from __future__ import annotations

import pytest

from scripts.t3_s1c_source_adapter_smoke import (
    FIXTURE_GENES,
    _artifact_manifest,
    fixture_tfdict,
)


def test_fixture_restricts_regulators_to_fixture_and_removes_self_edges():
    prior = {gene: ["Gata6", "Ctnnb1", gene, "Outside"] for gene in FIXTURE_GENES}
    fixture = fixture_tfdict(prior)
    assert all("Outside" not in values for values in fixture.values())
    assert all(gene not in values for gene, values in fixture.items())
    assert set(fixture) == set(FIXTURE_GENES)


def test_fixture_fails_closed_when_prior_lacks_a_required_gene():
    prior = {gene: [] for gene in FIXTURE_GENES[:-1]}
    with pytest.raises(ValueError, match="missing from prior TFdict"):
        fixture_tfdict(prior)


def test_stable_manifest_excludes_runtime_caches_and_sqlite_sidecars(tmp_path):
    (tmp_path / "RESULT.md").write_text("stable\n", encoding="utf-8")
    (tmp_path / "deployment/runtime/config/genomepy/genomepy.yaml").parent.mkdir(parents=True)
    (tmp_path / "deployment/runtime/config/genomepy/genomepy.yaml").write_text("config\n", encoding="utf-8")
    for relative in (
        "deployment/runtime/cache/genomepy/0.16.4/cache.db",
        "deployment/runtime/cache/genomepy/0.16.4/cache.db-shm",
        "deployment/runtime/cache/genomepy/0.16.4/cache.db-wal",
        "deployment/runtime/mpl/font.cache",
        "deployment/runtime/numba/compiled.cache",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"volatile")

    manifest = _artifact_manifest(tmp_path)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "RESULT.md" in paths
    assert "deployment/runtime/config/genomepy/genomepy.yaml" in paths
    assert not any(path.startswith("deployment/runtime/cache/") for path in paths)
    assert not any(path.startswith("deployment/runtime/mpl/") for path in paths)
    assert not any(path.startswith("deployment/runtime/numba/") for path in paths)
