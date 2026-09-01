from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping
from .types import ShapeFieldResult


def fit_shape_field(
    *,
    source_points: Any,
    reference_points: Any,
    regime: Literal["interpolation", "extrapolation"],
    backend: Literal["pycpd", "spateo"],
    locked_rms: float,
    output_dir: Path,
    config: Mapping[str, Any],
) -> ShapeFieldResult:
    """Fit and serialise a local-frame field; do not write a final H5AD."""
    raise NotImplementedError
