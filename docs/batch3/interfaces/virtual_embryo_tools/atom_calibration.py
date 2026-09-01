from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def derive_single_shrinkage(
    *,
    parent: Any,
    candidate_delta: Any,
    pseudo_holdout_metrics: Mapping[str, float],
    output_path: Path,
    config: Mapping[str, Any],
) -> float:
    """Derive one pre-registered analytical shrinkage coefficient; no grid search."""
    raise NotImplementedError
