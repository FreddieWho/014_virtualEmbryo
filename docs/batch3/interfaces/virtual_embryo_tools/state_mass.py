from __future__ import annotations

from pathlib import Path
from typing import Mapping, Any


def forecast_state_mass(
    *,
    state_transition_path: Path,
    parent_state_probabilities: Mapping[str, float],
    output_path: Path,
    config: Mapping[str, Any],
) -> Path:
    """Convert coupling to normalised target state probabilities with shrinkage."""
    raise NotImplementedError
