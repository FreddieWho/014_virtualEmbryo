from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from .types import TemporalCouplingResult


def fit_temporal_coupling(
    *,
    source_repr: Any,
    target_repr: Any,
    source_states: Any,
    target_states: Any,
    output_dir: Path,
    config: Mapping[str, Any],
) -> TemporalCouplingResult:
    """Fit moscot/WOT/POT coupling and serialise standard artifacts."""
    raise NotImplementedError
