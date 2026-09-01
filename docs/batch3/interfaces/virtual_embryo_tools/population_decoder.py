from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping


def decode_population(
    *,
    parent_data: Any,
    target_state_mass_path: Path,
    state_gene_delta_path: Path,
    mode: Literal["empirical_residual", "module_scdesign3"],
    output_dir: Path,
    config: Mapping[str, Any],
) -> Any:
    """Return expression rows while preserving the locked full gene space."""
    raise NotImplementedError
