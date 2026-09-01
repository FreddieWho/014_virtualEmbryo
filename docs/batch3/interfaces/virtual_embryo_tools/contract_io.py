from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import anndata as ad
import numpy as np
from scipy import sparse


_SCHEMA_VERSION = "ve.batch3.contract-report.v1"
_NORMALISATIONS = {
    "T1": "log1p_normalized",
    "T2": "log_normalized",
    "T3": "log_normalized",
}


def _fail_report(
    *,
    path: Path,
    task: str,
    board: str,
    errors: list[str],
    checks: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "status": "FAIL",
        "valid": False,
        "path": str(path),
        "task": str(task).upper(),
        "board": str(board).lower(),
        "checks": dict(checks or {}),
        "errors": list(errors),
        "warnings": [],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_root(scorer_lock: Path) -> Path:
    for candidate in (scorer_lock.parent, *scorer_lock.parents):
        if (candidate / "data" / "gene_panel" / "index.json").exists():
            return candidate
    raise ValueError(
        "could not locate repository root from scorer_lock; expected data/gene_panel/index.json"
    )


def _resolve_repo_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _canonical_gene_hash(genes: Sequence[str]) -> str:
    """Hash the canonical newline-joined panel representation used by index.json."""
    return hashlib.sha256("\n".join(str(gene) for gene in genes).encode("utf-8")).hexdigest()


def _load_board_definition(
    *,
    root: Path,
    lock: Mapping[str, Any],
    task: str,
    board: str,
) -> tuple[str, Mapping[str, Any], list[str], Path]:
    snapshot = lock.get("contract_snapshot", {})
    board_index_spec = snapshot.get("board_index", {})
    board_index_path = _resolve_repo_path(
        root, board_index_spec.get("path", "data/gene_panel/index.json")
    )
    if not board_index_path.exists():
        raise FileNotFoundError(f"board index does not exist: {board_index_path}")
    expected_index_hash = board_index_spec.get("sha256")
    if expected_index_hash and _sha256(board_index_path) != expected_index_hash:
        raise ValueError(
            "board index SHA256 does not match scorer lock: "
            f"{board_index_path}"
        )
    index = json.loads(board_index_path.read_text(encoding="utf-8"))
    task_upper = str(task).upper()
    board_lower = str(board).lower()
    key_candidates = [f"{task_upper}:{board_lower}", board_lower]
    key = next((candidate for candidate in key_candidates if candidate in index), None)
    if key is None:
        raise KeyError(f"no board definition for task={task_upper}, board={board_lower}")
    definition = index[key]
    if str(definition.get("task", task_upper)).upper() != task_upper:
        raise ValueError(f"board definition task mismatch for {key}")
    genes_file = definition.get("genes_file")
    if not genes_file:
        raise ValueError(f"board definition has no genes_file: {key}")
    genes_path = _resolve_repo_path(root / "data" / "gene_panel", genes_file)
    # The index stores panel file names relative to data/gene_panel.  Also accept
    # a repository-relative path for synthetic/test locks.
    if not genes_path.exists():
        genes_path = _resolve_repo_path(root, genes_file)
    if not genes_path.exists():
        raise FileNotFoundError(f"gene panel does not exist: {genes_path}")
    genes = [
        line.strip()
        for line in genes_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    declared_gene_hash = definition.get("genes_sha256")
    canonical_gene_hash = _canonical_gene_hash(genes)
    if declared_gene_hash and not canonical_gene_hash.startswith(str(declared_gene_hash)):
        raise ValueError(
            f"gene panel canonical SHA256 does not match index for {key}: "
            f"expected prefix={declared_gene_hash}, actual={canonical_gene_hash}"
        )
    return key, definition, genes, genes_path


def _matrix_content_hash(X: Any) -> str:
    """Hash matrix contents without changing the matrix or its sparse format."""
    digest = hashlib.sha256()
    shape = tuple(int(value) for value in getattr(X, "shape", ()))
    digest.update(repr(shape).encode("utf-8"))
    if sparse.issparse(X):
        csr = X.tocsr(copy=False)
        digest.update(b"sparse-csr")
        for values in (csr.data, csr.indices, csr.indptr):
            contiguous = np.ascontiguousarray(values)
            digest.update(str(contiguous.dtype).encode("ascii"))
            digest.update(contiguous.tobytes(order="C"))
    else:
        array = np.ascontiguousarray(np.asarray(X))
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _finite_nonnegative_check(X: Any) -> tuple[bool, bool, str]:
    if getattr(X, "ndim", None) != 2:
        return False, False, f"X must be a 2D cells x genes matrix, got ndim={getattr(X, 'ndim', None)}"
    values = X.data if sparse.issparse(X) else np.asarray(X)
    try:
        finite = bool(np.isfinite(values).all())
        nonnegative = bool((values >= 0).all())
    except (TypeError, ValueError) as exc:
        return False, False, f"X is not numeric: {exc}"
    return finite, nonnegative, ""


def _close_h5ad(handle: ad.AnnData) -> None:
    file = getattr(handle, "file", None)
    if file is not None and getattr(file, "isbacked", False):
        file.close()


def _expected_normalisation(task: str) -> str:
    try:
        return _NORMALISATIONS[str(task).upper()]
    except KeyError as exc:
        raise ValueError(f"unsupported task for normalisation contract: {task}") from exc


def _normalisation_check(candidate: ad.AnnData, *, task: str) -> dict[str, Any]:
    expected = _expected_normalisation(task)
    metadata = candidate.uns.get("ve_contract")
    if isinstance(metadata, Mapping) and metadata.get("normalization") == expected:
        return {
            "status": "PASS",
            "expected": expected,
            "evidence": "uns.ve_contract.normalization",
        }
    # Existing public parents predate this adapter.  Scanpy's log1p marker is
    # sufficient legacy evidence for the spatial panels, while new outputs
    # without an explicit marker are rejected below unless they are the locked
    # historical parent itself.
    if "log1p" in candidate.uns and task.upper() in {"T2", "T3"}:
        return {
            "status": "PASS_LEGACY_SCANPY_MARKER",
            "expected": expected,
            "evidence": "uns.log1p",
        }
    return {
        "status": "NOT_VERIFIED",
        "expected": expected,
        "evidence": None,
    }


def _dataframe_equal(left: Any, right: Any) -> bool:
    equals = getattr(left, "equals", None)
    return bool(equals(right)) if callable(equals) else False


def _raw_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return (
        tuple(str(gene) for gene in left.var_names)
        == tuple(str(gene) for gene in right.var_names)
        and _matrix_content_hash(left.X) == _matrix_content_hash(right.X)
    )


def _protected_parent_check(
    candidate: ad.AnnData,
    parent: ad.AnnData,
    *,
    require_spatial_identity: bool,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    candidate_cells = tuple(str(cell) for cell in candidate.obs_names)
    parent_cells = tuple(str(cell) for cell in parent.obs_names)
    checks: dict[str, Any] = {
        "obs_names_exact": candidate_cells == parent_cells,
        "obs_exact": _dataframe_equal(candidate.obs, parent.obs),
        "var_exact": _dataframe_equal(candidate.var, parent.var),
        "layers_keys_exact": sorted(candidate.layers.keys()) == sorted(parent.layers.keys()),
        "raw_exact": _raw_equal(candidate.raw, parent.raw),
    }
    if not checks["obs_names_exact"]:
        errors.append("candidate obs_names/order does not exactly match the locked parent")
    if not checks["obs_exact"]:
        errors.append("candidate obs metadata does not exactly match the locked parent")
    if not checks["var_exact"]:
        errors.append("candidate var metadata does not exactly match the locked parent")
    if not checks["layers_keys_exact"]:
        errors.append("candidate layers keys do not exactly match the locked parent")
    else:
        checks["layers_exact"] = all(
            _matrix_content_hash(candidate.layers[name])
            == _matrix_content_hash(parent.layers[name])
            for name in candidate.layers.keys()
        )
        if not checks["layers_exact"]:
            errors.append("candidate layers content changed relative to the locked parent")
    if not checks["raw_exact"]:
        errors.append("candidate raw content changed relative to the locked parent")
    if require_spatial_identity:
        candidate_coords = candidate.obsm.get("spatial_3D")
        parent_coords = parent.obsm.get("spatial_3D")
        checks["spatial_3D_exact"] = (
            candidate_coords is not None
            and parent_coords is not None
            and _matrix_content_hash(candidate_coords) == _matrix_content_hash(parent_coords)
        )
        if not checks["spatial_3D_exact"]:
            errors.append("T3 candidate spatial_3D changed relative to the locked parent")
    return checks, errors


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_h5ad_contract(
    path: Path,
    *,
    task: str,
    board: str,
    scorer_lock: Path,
    parent_path: Path | None = None,
    parent_sha256: str | None = None,
) -> Mapping[str, Any]:
    """Validate a candidate against the locked task/board contract.

    The implementation must verify shape, gene order, required obs/uns/obsm fields,
    normalisation assumptions and serialisation round-trip. It must not mutate input.
    """
    path = Path(path)
    scorer_lock = Path(scorer_lock)
    checks: dict[str, Any] = {}
    errors: list[str] = []
    task_upper = str(task).upper()
    board_lower = str(board).lower()

    if not path.exists():
        return _fail_report(
            path=path,
            task=task_upper,
            board=board_lower,
            errors=[f"candidate does not exist: {path}"],
        )
    if not scorer_lock.exists():
        return _fail_report(
            path=path,
            task=task_upper,
            board=board_lower,
            errors=[f"scorer lock does not exist: {scorer_lock}"],
        )
    if parent_path is None or parent_sha256 is None:
        return _fail_report(
            path=path,
            task=task_upper,
            board=board_lower,
            errors=[
                "parent_path and parent_sha256 are required for candidate contract validation"
            ],
        )

    try:
        lock = json.loads(scorer_lock.read_text(encoding="utf-8"))
        checks["scorer_lock"] = {
            "status": "PASS",
            "path": str(scorer_lock),
            "sha256": _sha256(scorer_lock),
        }
        root = _repo_root(scorer_lock)
        board_key, definition, expected_genes, genes_path = _load_board_definition(
            root=root, lock=lock, task=task_upper, board=board_lower
        )
        checks["board_definition"] = {
            "status": "PASS",
            "key": board_key,
            "genes_path": str(genes_path),
            "genes_sha256": _sha256(genes_path),
            "canonical_genes_sha256": _canonical_gene_hash(expected_genes),
            "index_declared_genes_sha256": definition.get("genes_sha256"),
        }
    except Exception as exc:  # return an auditable FAIL report, not a silent exception
        return _fail_report(
            path=path,
            task=task_upper,
            board=board_lower,
            errors=[f"contract metadata failure: {type(exc).__name__}: {exc}"],
            checks=checks,
        )

    candidate: ad.AnnData | None = None
    parent: ad.AnnData | None = None
    try:
        parent_path = Path(parent_path)
        if not parent_path.is_file():
            errors.append(f"locked parent does not exist: {parent_path}")
        elif _sha256(parent_path) != str(parent_sha256):
            errors.append("locked parent SHA256 does not match the supplied parent_sha256")
        else:
            parent = ad.read_h5ad(parent_path)
            checks["parent_binding"] = {
                "status": "PASS",
                "path": str(parent_path),
                "sha256": str(parent_sha256),
            }

        candidate = ad.read_h5ad(path)
        checks["shape"] = {
            "status": "PASS",
            "n_obs": int(candidate.n_obs),
            "n_vars": int(candidate.n_vars),
        }
        min_cells = definition.get("min_cells")
        max_cells = definition.get("max_cells")
        if min_cells is not None and candidate.n_obs < int(min_cells):
            errors.append(f"n_obs={candidate.n_obs} is below min_cells={min_cells}")
        if max_cells is not None and candidate.n_obs > int(max_cells):
            errors.append(f"n_obs={candidate.n_obs} exceeds max_cells={max_cells}")
        checks["cell_limits"] = {
            "status": "PASS" if not errors else "FAIL",
            "min_cells": min_cells,
            "max_cells": max_cells,
        }

        observed_genes = [str(gene) for gene in candidate.var_names]
        genes_ok = observed_genes == expected_genes
        checks["gene_order"] = {
            "status": "PASS" if genes_ok else "FAIL",
            "expected_count": len(expected_genes),
            "observed_count": len(observed_genes),
            "exact_order": genes_ok,
            "missing_head": [gene for gene in expected_genes if gene not in observed_genes][:10],
            "extra_head": [gene for gene in observed_genes if gene not in expected_genes][:10],
        }
        if len(set(observed_genes)) != len(observed_genes):
            errors.append("var_names contains duplicates")
        if not genes_ok:
            errors.append("var_names do not exactly match the locked board panel/order")
        if int(definition.get("n_genes", len(expected_genes))) != len(expected_genes):
            errors.append("board index n_genes disagrees with its gene panel file")
        if candidate.n_vars != len(expected_genes):
            errors.append(
                f"n_vars={candidate.n_vars} does not match locked panel size={len(expected_genes)}"
            )

        observed_cells = tuple(str(cell) for cell in candidate.obs_names)
        cells_unique = len(set(observed_cells)) == len(observed_cells)
        cells_nonempty = all(cell.strip() for cell in observed_cells)
        checks["cell_identity"] = {
            "status": "PASS" if cells_unique and cells_nonempty else "FAIL",
            "unique": cells_unique,
            "nonempty": cells_nonempty,
            "n_obs": len(observed_cells),
        }
        if not cells_unique:
            errors.append("obs_names contains duplicate cell identifiers")
        if not cells_nonempty:
            errors.append("obs_names contains an empty cell identifier")

        normalisation = _normalisation_check(candidate, task=task_upper)
        checks["normalisation"] = normalisation
        if normalisation["status"] == "NOT_VERIFIED":
            # A locked historical parent may be audited with the old public
            # contract, but any newly materialised path must carry explicit
            # normalization provenance.
            historical_parent = (
                parent_path is not None
                and candidate is not None
                and Path(path).resolve() == Path(parent_path).resolve()
                and bool(parent_sha256)
            )
            if historical_parent:
                checks["normalisation"]["status"] = "PASS_HISTORICAL_LOCKED_PARENT"
                checks["normalisation"]["evidence"] = "locked_parent_sha256_and_official_contract"
            else:
                errors.append(
                    "normalisation is not verifiable; provide uns.ve_contract.normalization "
                    f"={_expected_normalisation(task_upper)!r}"
                )

        finite, nonnegative, matrix_error = _finite_nonnegative_check(candidate.X)
        checks["expression"] = {
            "status": "PASS" if finite and nonnegative else "FAIL",
            "finite": finite,
            "nonnegative": nonnegative,
            "dtype": str(getattr(candidate.X, "dtype", "unknown")),
            "normalisation_assumption": "log-normalized nonnegative expression; no mutation performed",
        }
        if matrix_error:
            errors.append(matrix_error)
        elif not finite:
            errors.append("X contains NaN or infinite values")
        elif not nonnegative:
            errors.append("X contains negative values")

        required_obs = [str(name) for name in definition.get("obs_required", [])]
        missing_obs = [name for name in required_obs if name not in candidate.obs]
        checks["obs"] = {
            "status": "PASS" if not missing_obs else "FAIL",
            "required": required_obs,
            "missing": missing_obs,
        }
        if missing_obs:
            errors.append(f"missing required obs columns: {missing_obs}")

        required_uns = [str(name) for name in definition.get("uns_required", [])]
        missing_uns = [name for name in required_uns if name not in candidate.uns]
        checks["uns"] = {
            "status": "PASS" if not missing_uns else "FAIL",
            "required": required_uns,
            "missing": missing_uns,
        }
        if missing_uns:
            errors.append(f"missing required uns entries: {missing_uns}")

        required_obsm = [str(name) for name in definition.get("obsm_required", [])]
        missing_obsm = [name for name in required_obsm if name not in candidate.obsm]
        obsm_check: dict[str, Any] = {
            "status": "PASS" if not missing_obsm else "FAIL",
            "required": required_obsm,
            "missing": missing_obsm,
        }
        for name in required_obsm:
            if name not in candidate.obsm:
                continue
            coords = np.asarray(candidate.obsm[name])
            finite_coords = bool(coords.ndim == 2 and coords.shape[0] == candidate.n_obs
                                 and coords.shape[1] >= 3 and np.isfinite(coords[:, :3]).all())
            obsm_check[name] = {
                "shape": list(coords.shape),
                "finite_first_three": finite_coords,
            }
            if not finite_coords:
                errors.append(f"obsm[{name!r}] must be cells x >=3 with finite first three columns")
        checks["obsm"] = obsm_check
        if missing_obsm:
            errors.append(f"missing required obsm entries: {missing_obsm}")

        if not bool(definition.get("needs_coords", bool(required_obsm))) and "spatial_3D" in candidate.obsm:
            errors.append("T1-style board must not carry spatial_3D")
            checks["spatial_absence"] = {"status": "FAIL", "present": True}
        elif not bool(definition.get("needs_coords", bool(required_obsm))):
            checks["spatial_absence"] = {"status": "PASS", "present": False}

        if parent is not None:
            protected, protected_errors = _protected_parent_check(
                candidate,
                parent,
                require_spatial_identity=(task_upper == "T3"),
            )
            checks["protected_parent"] = {
                "status": "PASS" if not protected_errors else "FAIL",
                **protected,
            }
            errors.extend(protected_errors)

        before_matrix_hash = _matrix_content_hash(candidate.X)
        before_var_names = tuple(observed_genes)
        before_coords_hash = (
            _matrix_content_hash(candidate.obsm["spatial_3D"])
            if "spatial_3D" in candidate.obsm
            else None
        )
        with tempfile.TemporaryDirectory(prefix="ve-contract-") as temp_dir:
            roundtrip_path = Path(temp_dir) / "roundtrip.h5ad"
            candidate.write_h5ad(roundtrip_path)
            roundtrip = ad.read_h5ad(roundtrip_path)
            roundtrip_matrix_hash = _matrix_content_hash(roundtrip.X)
            roundtrip_coords_hash = (
                _matrix_content_hash(roundtrip.obsm["spatial_3D"])
                if "spatial_3D" in roundtrip.obsm
                else None
            )
            roundtrip_var_names = tuple(str(gene) for gene in roundtrip.var_names)
            roundtrip_ok = (
                roundtrip.shape == candidate.shape
                and roundtrip_var_names == before_var_names
                and roundtrip_matrix_hash == before_matrix_hash
                and roundtrip_coords_hash == before_coords_hash
            )
            _close_h5ad(roundtrip)
        checks["serialisation_round_trip"] = {
            "status": "PASS" if roundtrip_ok else "FAIL",
            "exact_matrix_content": roundtrip_matrix_hash == before_matrix_hash,
            "exact_var_names": roundtrip_var_names == before_var_names,
            "spatial_content_preserved": roundtrip_coords_hash == before_coords_hash,
        }
        if not roundtrip_ok:
            errors.append("H5AD serialisation round-trip changed contract content")
    except Exception as exc:
        errors.append(f"candidate read/validation failure: {type(exc).__name__}: {exc}")
    finally:
        if candidate is not None:
            _close_h5ad(candidate)
        if parent is not None:
            _close_h5ad(parent)

    status = "PASS" if not errors else "FAIL"
    return {
        "schema_version": _SCHEMA_VERSION,
        "status": status,
        "valid": status == "PASS",
        "path": str(path),
        "task": task_upper,
        "board": board_lower,
        "checks": checks,
        "errors": errors,
        "warnings": [],
    }


def write_candidate_from_parent(
    *,
    parent_path: Path,
    output_path: Path,
    expression: Any | None = None,
    spatial_3d: Any | None = None,
    metadata_updates: Mapping[str, Any] | None = None,
    row_names: Sequence[str] | None = None,
    normalization: str | None = None,
    parent_sha256: str | None = None,
) -> None:
    """Write the final H5AD through the single core contract path.

    ``row_names`` is required whenever replacement expression or coordinates
    are supplied.  This prevents a bare array with an unknown row order from
    being silently attached to parent cell identifiers.  ``normalization`` is
    required for legacy parents that do not carry an explicit contract marker.
    """
    parent_path = Path(parent_path)
    output_path = Path(output_path)
    if not parent_path.exists():
        raise FileNotFoundError(parent_path)
    if not parent_sha256:
        raise ValueError("parent_sha256 is required to write a candidate")
    if _sha256(parent_path) != str(parent_sha256):
        raise ValueError("parent_sha256 does not match parent_path")
    if output_path.exists():
        raise FileExistsError(
            f"refusing to overwrite existing artifact: {output_path}"
        )
    if parent_path.resolve() == output_path.resolve():
        raise ValueError("parent_path and output_path must be different")

    parent = ad.read_h5ad(parent_path)
    try:
        out = parent.copy()
        parent_row_names = tuple(str(cell) for cell in parent.obs_names)
        supplied_row_names = None if row_names is None else tuple(str(cell) for cell in row_names)
        if (expression is not None or spatial_3d is not None) and supplied_row_names is None:
            raise ValueError(
                "row_names must be supplied with expression or spatial_3d replacements"
            )
        if supplied_row_names is not None and supplied_row_names != parent_row_names:
            raise ValueError("row_names must exactly match the parent obs_names/order")

        expected_normalisation = None
        if normalization is not None:
            expected_normalisation = str(normalization)
            if expected_normalisation not in set(_NORMALISATIONS.values()):
                raise ValueError(
                    "normalization must be one of: "
                    + ", ".join(sorted(set(_NORMALISATIONS.values())))
                )
        inherited_contract = parent.uns.get("ve_contract")
        inherited_normalisation = (
            inherited_contract.get("normalization")
            if isinstance(inherited_contract, Mapping)
            else None
        )
        if expected_normalisation is not None:
            out.uns["ve_contract"] = {
                "schema": "ve.contract.v1",
                "normalization": expected_normalisation,
            }
        elif inherited_normalisation is None and "log1p" not in parent.uns:
            raise ValueError(
                "normalization must be supplied when parent has no verifiable normalization marker"
            )
        if expression is not None:
            if getattr(expression, "shape", None) != parent.shape:
                raise ValueError(
                    f"expression shape {getattr(expression, 'shape', None)} does not match parent {parent.shape}"
                )
            finite, nonnegative, message = _finite_nonnegative_check(expression)
            if message or not finite or not nonnegative:
                raise ValueError(message or "expression must be finite and non-negative")
            if sparse.issparse(expression):
                out.X = expression.astype(np.float32, copy=True)
            else:
                out.X = np.asarray(expression, dtype=np.float32).copy()

        if spatial_3d is not None:
            coords = np.asarray(spatial_3d)
            if coords.ndim != 2 or coords.shape[0] != parent.n_obs or coords.shape[1] < 3:
                raise ValueError(
                    "spatial_3d must have shape (parent.n_obs, >=3), "
                    f"got {coords.shape}"
                )
            if not np.isfinite(coords[:, :3]).all():
                raise ValueError("spatial_3d contains NaN or infinite values")
            out.obsm["spatial_3D"] = np.asarray(coords[:, :3], dtype=np.float32).copy()
        elif "spatial_3D" in out.obsm:
            inherited_coords = np.asarray(out.obsm["spatial_3D"])
            if (
                inherited_coords.ndim != 2
                or inherited_coords.shape[0] != parent.n_obs
                or inherited_coords.shape[1] < 3
                or not np.isfinite(inherited_coords[:, :3]).all()
            ):
                raise ValueError(
                    "parent spatial_3D must have shape (n_obs, >=3) with finite first three columns"
                )

        if metadata_updates is not None:
            if not isinstance(metadata_updates, Mapping):
                raise TypeError("metadata_updates must be a mapping")
            out.uns.update(dict(metadata_updates))

        finite, nonnegative, message = _finite_nonnegative_check(out.X)
        if message or not finite or not nonnegative:
            raise ValueError(message or "output expression must be finite and non-negative")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", suffix=".h5ad", dir=output_path.parent
        )
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            out.write_h5ad(temp_path)
            written = ad.read_h5ad(temp_path)
            try:
                if written.shape != parent.shape:
                    raise ValueError("written candidate shape changed during serialisation")
                if tuple(str(gene) for gene in written.var_names) != tuple(
                    str(gene) for gene in parent.var_names
                ):
                    raise ValueError("written candidate gene order changed during serialisation")
                finite, nonnegative, message = _finite_nonnegative_check(written.X)
                if message or not finite or not nonnegative:
                    raise ValueError(message or "written candidate expression is invalid")
                if "spatial_3D" in out.obsm:
                    if "spatial_3D" not in written.obsm:
                        raise ValueError("written candidate lost spatial_3D")
                    written_coords = np.asarray(written.obsm["spatial_3D"])
                    output_coords = np.asarray(out.obsm["spatial_3D"])
                    if written_coords.shape != output_coords.shape or not np.array_equal(
                        written_coords, output_coords
                    ):
                        raise ValueError("written candidate changed spatial_3D")
            finally:
                _close_h5ad(written)
            fd = os.open(temp_path, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            # A hard-link publication is atomic and no-clobber on the same
            # filesystem: unlike os.replace(), a racing writer cannot replace
            # an already published candidate.  The temporary file is created
            # in output_path.parent specifically to guarantee that property.
            try:
                os.link(temp_path, output_path)
            except FileExistsError as exc:
                raise FileExistsError(
                    f"refusing to overwrite existing artifact: {output_path}"
                ) from exc
            _fsync_directory(output_path.parent)
            temp_path.unlink()
            _fsync_directory(output_path.parent)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    finally:
        _close_h5ad(parent)
