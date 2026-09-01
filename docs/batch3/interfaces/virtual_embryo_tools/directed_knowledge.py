"""Fail-closed consumers for the locked T3 directed-knowledge snapshots.

This module intentionally stops at auditable edge/path evidence.  It does not
infer cell-state activity, choose a response top-k, or write an H5AD.  A valid
regulatory edge is converted to the ``KO - WT`` sign only for the narrow case
where the snapshot has one unambiguous consensus stimulation/inhibition label.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


REQUIRED_COLUMNS = (
    "source",
    "target",
    "source_genesymbol",
    "target_genesymbol",
    "is_directed",
    "is_stimulation",
    "is_inhibition",
    "consensus_direction",
    "consensus_stimulation",
    "consensus_inhibition",
)


def _bool(value: Any, *, field: str) -> bool:
    token = str(value).strip().lower()
    if token not in {"true", "false"}:
        raise ValueError(f"{field} must be True or False, got {value!r}")
    return token == "true"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _repo_root_from(path: Path) -> Path:
    for candidate in (path.parent, *path.parents):
        if (candidate / "data" / "gene_panel" / "index.json").exists():
            return candidate
    raise ValueError(
        "could not locate repository root; expected data/gene_panel/index.json"
    )


@dataclass(frozen=True)
class DirectedEdge:
    source: str
    target: str
    source_gene: str
    target_gene: str
    is_directed: bool
    is_stimulation: bool
    is_inhibition: bool
    consensus_direction: bool
    consensus_stimulation: bool
    consensus_inhibition: bool

    @property
    def regulation_sign(self) -> int | None:
        """Return +1 activation / -1 inhibition, or None if unresolved."""
        if not self.is_directed or not self.consensus_direction:
            return None
        if self.consensus_stimulation == self.consensus_inhibition:
            return None
        if self.consensus_stimulation and not self.is_stimulation:
            return None
        if self.consensus_inhibition and not self.is_inhibition:
            return None
        return 1 if self.consensus_stimulation else -1


@dataclass(frozen=True)
class AuditedSnapshot:
    manifest_path: Path
    data_path: Path
    source_name: str
    sha256: str
    row_count: int
    panel_path: Path
    panel_genes: frozenset[str]
    edges: tuple[DirectedEdge, ...]


def load_audited_snapshot(
    manifest_path: Path,
    *,
    repo_root: Path | None = None,
    expected_source_name: str | None = None,
    expected_dataset: str | None = None,
    expected_taxon_id: int | None = 10090,
) -> AuditedSnapshot:
    """Load one snapshot only after validating its manifest and row content."""
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "ve.external-knowledge-snapshot.v1":
        raise ValueError("unsupported external-knowledge snapshot schema")
    source_name = str(manifest.get("source_name", "")).strip()
    source_url = str(manifest.get("source_url", "")).strip()
    license_text = str(manifest.get("license", "")).strip()
    source_query = manifest.get("source_query")
    schema = manifest.get("schema")
    if not source_name or not source_url or not license_text:
        raise ValueError(
            "snapshot manifest must declare non-empty source_name, source_url, and license"
        )
    if not isinstance(source_query, Mapping):
        raise ValueError("snapshot manifest must declare source_query metadata")
    if not isinstance(schema, Mapping):
        raise ValueError("snapshot manifest must declare schema metadata")
    query_dataset = str(source_query.get("datasets", "")).strip()
    query_organisms = str(source_query.get("organisms", "")).strip()
    if not query_dataset or not query_organisms:
        raise ValueError("snapshot source_query must declare datasets and organisms")
    if expected_source_name is not None and source_name.casefold() != str(
        expected_source_name
    ).casefold():
        raise ValueError(
            f"snapshot source_name={source_name!r} does not match expected "
            f"{expected_source_name!r}"
        )
    if expected_dataset is not None and query_dataset.casefold() != str(
        expected_dataset
    ).casefold():
        raise ValueError(
            f"snapshot dataset={query_dataset!r} does not match expected "
            f"{expected_dataset!r}"
        )
    if expected_taxon_id is not None:
        expected_taxon = str(int(expected_taxon_id))
        if query_organisms != expected_taxon:
            raise ValueError(
                f"snapshot organisms={query_organisms!r} does not match expected "
                f"taxon {expected_taxon}"
            )
        if int(schema.get("organism_taxon_id", -1)) != int(expected_taxon_id):
            raise ValueError("snapshot schema organism_taxon_id does not match expected taxon")
    data_value = manifest.get("data_path")
    expected_bytes = manifest.get("bytes")
    expected_sha = manifest.get("sha256")
    if not data_value or expected_bytes is None or not expected_sha:
        raise ValueError("snapshot manifest must declare data_path, bytes, and sha256")
    data_path = (manifest_path.parent / str(data_value)).resolve()
    if manifest_path.parent.resolve() not in data_path.parents:
        raise ValueError("snapshot data_path escapes its manifest directory")
    if not data_path.is_file():
        raise FileNotFoundError(data_path)
    if data_path.stat().st_size != int(expected_bytes):
        raise ValueError("snapshot byte count does not match manifest")
    actual_sha = _sha256(data_path)
    if actual_sha != str(expected_sha):
        raise ValueError("snapshot SHA256 does not match manifest")

    root = Path(repo_root).resolve() if repo_root is not None else _repo_root_from(manifest_path)
    mapping = manifest.get("target_mapping", {})
    panel_reference = mapping.get("panel_reference")
    panel_count = int(mapping.get("panel_gene_count", 0))
    expected_overlap = int(mapping.get("edge_symbols_overlapping_panel", -1))
    expected_panel_sha = source_query.get("partners_panel_sha256")
    if not panel_reference or panel_count <= 0 or expected_overlap < 0:
        raise ValueError("snapshot target_mapping is incomplete")
    panel_path = _resolve(root, panel_reference)
    if not panel_path.is_file():
        raise FileNotFoundError(panel_path)
    if expected_panel_sha and _sha256(panel_path) != str(expected_panel_sha):
        raise ValueError("snapshot panel SHA256 does not match manifest")
    panel_genes = frozenset(
        line.strip()
        for line in panel_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    if len(panel_genes) != panel_count:
        raise ValueError("snapshot panel gene count does not match manifest")

    edges: list[DirectedEdge] = []
    with data_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise ValueError("snapshot TSV columns do not match the locked schema")
        for raw in reader:
            source_gene = str(raw["source_genesymbol"]).strip()
            target_gene = str(raw["target_genesymbol"]).strip()
            if not source_gene or not target_gene:
                raise ValueError("snapshot edge has an empty mapped gene symbol")
            edge = DirectedEdge(
                source=str(raw["source"]).strip(),
                target=str(raw["target"]).strip(),
                source_gene=source_gene,
                target_gene=target_gene,
                is_directed=_bool(raw["is_directed"], field="is_directed"),
                is_stimulation=_bool(raw["is_stimulation"], field="is_stimulation"),
                is_inhibition=_bool(raw["is_inhibition"], field="is_inhibition"),
                consensus_direction=_bool(raw["consensus_direction"], field="consensus_direction"),
                consensus_stimulation=_bool(raw["consensus_stimulation"], field="consensus_stimulation"),
                consensus_inhibition=_bool(raw["consensus_inhibition"], field="consensus_inhibition"),
            )
            if not edge.is_directed:
                raise ValueError("snapshot contains a non-directed edge")
            edges.append(edge)
    expected_rows = int(manifest.get("directed_edges", -1))
    if expected_rows != len(edges):
        raise ValueError("snapshot row count does not match manifest directed_edges")
    mapped_symbols = {
        symbol
        for edge in edges
        for symbol in (edge.source_gene, edge.target_gene)
        if symbol in panel_genes
    }
    if len(mapped_symbols) != expected_overlap:
        raise ValueError("snapshot panel overlap does not match manifest")
    return AuditedSnapshot(
        manifest_path=manifest_path,
        data_path=data_path,
        source_name=source_name,
        sha256=actual_sha,
        row_count=len(edges),
        panel_path=panel_path,
        panel_genes=panel_genes,
        edges=tuple(edges),
    )


def _ko_minus_wt_sign(edge: DirectedEdge) -> int | None:
    regulation = edge.regulation_sign
    return None if regulation is None else -regulation


def build_tf_edge_evidence(
    snapshot: AuditedSnapshot,
    *,
    target_gene: str,
) -> list[dict[str, Any]]:
    """Build edge-level TF evidence without assigning a state or amplitude."""
    target_key = str(target_gene).casefold()
    rows: list[dict[str, Any]] = []
    for edge in snapshot.edges:
        if edge.source_gene.casefold() != target_key:
            continue
        if edge.target_gene not in snapshot.panel_genes:
            continue
        response_sign = _ko_minus_wt_sign(edge)
        rows.append(
            {
                "source_name": snapshot.source_name,
                "target_gene": target_gene,
                "response_gene": edge.target_gene,
                "regulation_sign": edge.regulation_sign,
                "ko_minus_wt_sign": response_sign if response_sign is not None else 0,
                "conflict_flag": response_sign is None,
                "directness_score": 1.0 if response_sign is not None else 0.0,
                # Directness is an evidence-type indicator, not a calibrated
                # probability.  This adapter has no source-specific confidence
                # calibration, so never emit a misleading numeric 1.0.
                "confidence": None,
                "confidence_status": (
                    "UNCALIBRATED_EXTERNAL_EVIDENCE"
                    if response_sign is not None
                    else "UNRESOLVED_DIRECTION"
                ),
                "provenance": (
                    f"{snapshot.source_name}|{snapshot.data_path}|"
                    f"{edge.source_gene}->{edge.target_gene}|audited_directed_edge"
                ),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["response_gene"]),
            int(row["ko_minus_wt_sign"]),
            str(row["provenance"]),
        ),
    )


def build_directed_paths(
    snapshot: AuditedSnapshot,
    *,
    source_gene: str,
    max_hops: int = 2,
    max_paths: int = 5000,
) -> list[dict[str, Any]]:
    """Enumerate a deterministic, bounded directed path evidence table."""
    if max_hops < 1:
        raise ValueError("max_hops must be positive")
    if max_paths < 1:
        raise ValueError("max_paths must be positive")
    adjacency: dict[str, list[DirectedEdge]] = defaultdict(list)
    for edge in snapshot.edges:
        if edge.source_gene and edge.target_gene:
            adjacency[edge.source_gene.casefold()].append(edge)
    for edges in adjacency.values():
        edges.sort(key=lambda edge: (edge.target_gene.casefold(), edge.target_gene, edge.source, edge.target))

    queue: deque[tuple[str, tuple[DirectedEdge, ...], tuple[str, ...]]] = deque(
        [(str(source_gene).casefold(), (), (str(source_gene),))]
    )
    paths: list[dict[str, Any]] = []
    while queue and len(paths) < max_paths:
        node, edge_path, node_path = queue.popleft()
        if edge_path and node_path[-1] in snapshot.panel_genes:
            regulation_signs = [edge.regulation_sign for edge in edge_path]
            valid = all(sign in (-1, 1) for sign in regulation_signs)
            product = 1
            if valid:
                for sign in regulation_signs:
                    product *= int(sign)
            paths.append(
                {
                    "source_gene": source_gene,
                    "response_gene": node_path[-1],
                    "hops": len(edge_path),
                    "path_nodes": list(node_path),
                    "regulation_signs": regulation_signs,
                    "ko_minus_wt_sign": -product if valid else 0,
                    "conflict_flag": not valid,
                    "provenance": (
                        f"{snapshot.source_name}|{snapshot.data_path}|"
                        + "->".join(node_path)
                    ),
                }
            )
        if len(edge_path) >= max_hops:
            continue
        for edge in adjacency.get(node, ()):
            next_node = edge.target_gene.casefold()
            if next_node in {value.casefold() for value in node_path}:
                continue
            queue.append((next_node, edge_path + (edge,), node_path + (edge.target_gene,)))
    return sorted(
        paths,
        key=lambda row: (
            int(row["hops"]),
            str(row["response_gene"]),
            tuple(str(node) for node in row["path_nodes"]),
        ),
    )


def snapshot_summary(snapshot: AuditedSnapshot) -> dict[str, Any]:
    unresolved = sum(edge.regulation_sign is None for edge in snapshot.edges)
    return {
        "source_name": snapshot.source_name,
        "manifest": str(snapshot.manifest_path),
        "data_path": str(snapshot.data_path),
        "sha256": snapshot.sha256,
        "row_count": snapshot.row_count,
        "panel_gene_count": len(snapshot.panel_genes),
        "unresolved_direction_or_sign_edges": unresolved,
        "status": "AUDITED_PASS",
    }
