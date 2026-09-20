"""Check source-use scope before reading any external expression matrix."""
import hashlib
import json
from pathlib import Path


def _bound_json(record, root):
    path = Path(root) / record.get('path', '')
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record.get('sha256'):
        raise ValueError('review/policy evidence missing or hash mismatch')
    return json.loads(path.read_text())


def require_response_role(manifest, root, role):
    """Task/source-scoped review, without a universal organizer-letter gate.

    An unresolved source must first get a new resolved review; setting ALLOWED
    on the manifest alone never overrides EXCLUDED/NEEDS_CLARIFICATION evidence.
    """
    if role not in {'RESPONSE_SHAPE_ONLY', 'SIGNED_RESPONSE'}:
        raise ValueError('unknown response role')
    if manifest.get('allowed_response_role') != role:
        raise ValueError('source permit does not authorize ' + role)
    if manifest.get('task') != 'T3:gata4' or manifest.get('status') != 'APPROVED_SANITIZED':
        raise ValueError('manifest not approved for task')
    review = _bound_json(manifest.get('compliance_review', {}), root)
    if (review.get('task') != manifest['task']
            or review.get('source_reference') != manifest.get('source_reference')
            or review.get('policy_version') != 'T3_EXTERNAL_DATA_20260921'
            or review.get('review_status') != 'COMPLETED'
            or review.get('classification') != 'ALLOWED'
            or type(review.get('prohibited_records_remaining')) is not int
            or review['prohibited_records_remaining'] != 0
            or role not in review.get('allowed_response_roles', [])
            or review.get('license_status') != 'PERMITTED'
            or not review.get('source_context_review')
            or not review.get('condition_allowlist')):
        raise ValueError('review does not establish permitted source, context and role')
    # Policy text need not be JSON, but its exact version must be hash-bound.
    policy = review.get('policy', {})
    path = Path(root) / policy.get('path', '')
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != policy.get('sha256'):
        raise ValueError('policy evidence missing or hash mismatch')
    return review


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
