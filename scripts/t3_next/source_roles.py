"""Check source-use scope before reading any external expression matrix."""
import hashlib
import json
from pathlib import Path


def require_response_role(manifest, root, role):
    if role not in {'RESPONSE_SHAPE_ONLY', 'SIGNED_RESPONSE'}:
        raise ValueError('unknown response role')
    if manifest.get('allowed_response_role') != role:
        raise ValueError('source permit does not authorize ' + role)
    record = manifest.get('organizer_clearance', {})
    if record.get('status') != 'WRITTEN_CONFIRMATION_PRESENT':
        raise ValueError('written organizer confirmation missing')
    path = Path(root) / record.get('path', '')
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record.get('sha256'):
        raise ValueError('organizer confirmation missing or hash mismatch')
    scope = json.loads(path.read_text())
    if (scope.get('task') != manifest.get('task')
            or scope.get('source_reference') != manifest.get('source_reference')
            or scope.get('allowed_response_role') != role
            or scope.get('review_status') != 'HUMAN_VERIFIED_WRITTEN_CONFIRMATION'):
        raise ValueError('organizer confirmation scope mismatch')
    evidence = scope.get('evidence', {})
    evidence_path = Path(root) / evidence.get('path', '')
    if (not evidence_path.is_file()
            or hashlib.sha256(evidence_path.read_bytes()).hexdigest() != evidence.get('sha256')):
        raise ValueError('original written confirmation evidence missing or hash mismatch')


def unsigned_response_shape(delta):
    """Unit-L2 magnitude target; never preserves source response direction.

    Used only by the proposed shape-only successor, not the existing signed R6.
    Each row represents one source perturbation on the fixed output panel.
    """
    import numpy as np
    values = np.asarray(delta, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError('expected finite perturbation by gene matrix')
    magnitude = np.abs(values)
    norm = np.linalg.norm(magnitude, axis=1, keepdims=True)
    return np.divide(magnitude, norm, out=np.zeros_like(magnitude), where=norm > 0)
