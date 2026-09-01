from __future__ import annotations

from pathlib import Path
from .types import ParentRef


def load_locked_parent(registry_path: Path, *, task: str, board: str) -> ParentRef:
    """Load a verified immutable parent and re-check its SHA256."""
    raise NotImplementedError
