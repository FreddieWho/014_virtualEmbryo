from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
from typing import Literal, Sequence


@dataclass(frozen=True)
class ArtifactRef:
    path: Path
    sha256: str
    role: str


@dataclass(frozen=True)
class ParentRef:
    task: str
    board: str
    candidate_id: str
    path: Path
    sha256: str
    scorer_snapshot: str


@dataclass(frozen=True)
class GateDecision:
    gate_id: str
    status: Literal["PASS", "FAIL", "HOLD", "BLOCKED", "NOT_EVALUATED"]
    evidence_paths: tuple[Path, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class SignedPriorRecord:
    target_gene: str
    condition_id: str
    stage: str
    state: str
    response_gene: str
    sign: Literal[-1, 0, 1]
    rank_score: float
    confidence: float | None
    lineage_gate: float
    dosage_fraction: float | None = None
    source_families: tuple[str, ...] = ()
    directness_score: float | None = None
    conflict_flag: bool = False
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.target_gene or not self.condition_id or not self.stage:
            raise ValueError("target_gene, condition_id, and stage are required")
        if not self.state or not self.response_gene:
            raise ValueError("state and response_gene are required")
        if self.sign not in (-1, 0, 1):
            raise ValueError("sign must be -1, 0, or 1")
        if not 0.0 <= self.rank_score <= 1.0:
            raise ValueError("rank_score must be in [0, 1]")
        if self.confidence is not None:
            if not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
                raise ValueError("confidence must be None or in [0, 1]")
        if not 0.0 <= self.lineage_gate <= 1.0:
            raise ValueError("lineage_gate must be in [0, 1]")
        if self.dosage_fraction is not None and not 0.0 <= self.dosage_fraction <= 1.0:
            raise ValueError("dosage_fraction must be None or in [0, 1]")
        if self.directness_score is not None and not 0.0 <= self.directness_score <= 1.0:
            raise ValueError("directness_score must be None or in [0, 1]")
        if self.conflict_flag and self.sign != 0:
            raise ValueError("conflicting records must have sign=0 in strict outputs")


@dataclass(frozen=True)
class TemporalCouplingResult:
    coupling_path: Path
    source_obs_path: Path
    target_obs_path: Path
    metadata_path: Path
    state_transition_path: Path


@dataclass(frozen=True)
class ShapeFieldResult:
    source_landmarks_path: Path
    predicted_landmarks_path: Path
    displacement_path: Path
    metadata_path: Path
    geometry_checks_path: Path
