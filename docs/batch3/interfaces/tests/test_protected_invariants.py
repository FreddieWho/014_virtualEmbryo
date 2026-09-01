"""Acceptance-test templates to be adapted to the existing repository."""

import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_parent_artifact_is_immutable(parent_path: Path, locked_sha256: str) -> None:
    """Reusable assertion for project-specific parent fixtures."""
    assert sha256(parent_path) == locked_sha256


def test_parent_hash_helper(tmp_path: Path) -> None:
    parent = tmp_path / "parent.bin"
    parent.write_bytes(b"immutable-parent")
    assert_parent_artifact_is_immutable(parent, sha256(parent))


# Task-specific tests that the implementing agent must add:
# - T1: full gene order, state-mass sum, residual covariance preservation.
# - T2: X/obs/var equality, locked RMS, local-frame invariance, kNN overlap.
# - T3: KO-WT sign convention, Mesp1 gate, WT background preservation.
