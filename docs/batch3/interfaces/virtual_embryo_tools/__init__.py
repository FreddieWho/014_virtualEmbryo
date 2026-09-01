"""Reference interfaces for the Virtual Embryo tool-integration layer."""

from .contract_io import validate_h5ad_contract, write_candidate_from_parent
from .directed_knowledge import (
    AuditedSnapshot,
    DirectedEdge,
    build_directed_paths,
    build_tf_edge_evidence,
    load_audited_snapshot,
    snapshot_summary,
)
from .types import (
    ArtifactRef,
    ParentRef,
    GateDecision,
    SignedPriorRecord,
    TemporalCouplingResult,
    ShapeFieldResult,
)

__all__ = [
    "ArtifactRef",
    "ParentRef",
    "GateDecision",
    "SignedPriorRecord",
    "TemporalCouplingResult",
    "ShapeFieldResult",
    "validate_h5ad_contract",
    "write_candidate_from_parent",
    "DirectedEdge",
    "AuditedSnapshot",
    "load_audited_snapshot",
    "build_tf_edge_evidence",
    "build_directed_paths",
    "snapshot_summary",
]
