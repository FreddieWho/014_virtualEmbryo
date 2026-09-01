from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from .types import GateDecision


def evaluate_niche_proxy(
    *,
    expression: Any,
    coordinates: Any,
    states: Any,
    output_dir: Path,
    config: Mapping[str, Any],
) -> GateDecision:
    """Evaluate a source-only NFS-like objective. Must not generate a submission."""
    raise NotImplementedError
