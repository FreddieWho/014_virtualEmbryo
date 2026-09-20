import hashlib
import json
import numpy as np
import pytest
from scripts.t3_next.source_roles import require_response_role, unsigned_response_shape


def test_shape_discards_independent_signs_and_scale():
    x = np.array([[1., -2., 3.], [0., 0., 0.]])
    np.testing.assert_allclose(unsigned_response_shape(x), unsigned_response_shape(x * [-4, 4, -4]))
    np.testing.assert_allclose(unsigned_response_shape(x)[1], 0)
    with pytest.raises(ValueError):
        unsigned_response_shape([[np.nan]])


def test_shape_permit_cannot_authorize_existing_signed_route(tmp_path):
    with pytest.raises(ValueError, match='does not authorize'):
        require_response_role({'allowed_response_role': 'RESPONSE_SHAPE_ONLY'}, tmp_path, 'SIGNED_RESPONSE')


def test_r6_rejects_shape_only_before_matrix_access(tmp_path, monkeypatch):
    import anndata
    from scripts.t3_next.routes_extended import r6
    def forbidden_read(*args, **kwargs):
        pytest.fail('external matrix opened before role approval')
    monkeypatch.setattr(anndata, 'read_h5ad', forbidden_read)
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps({'allowed_response_role': 'RESPONSE_SHAPE_ONLY'}))
    with pytest.raises(ValueError, match='does not authorize'):
        r6(None, path)


def test_written_scope_and_original_evidence_required(tmp_path):
    evidence = tmp_path / 'original.txt'
    evidence.write_text('SYNTHETIC TEST FIXTURE - not organizer approval')
    scope = {'task': 'T3:gata4', 'source_reference': 'test-source',
             'allowed_response_role': 'SIGNED_RESPONSE',
             'review_status': 'HUMAN_VERIFIED_WRITTEN_CONFIRMATION',
             'evidence': {'path': evidence.name, 'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()}}
    path = tmp_path / 'scope.json'
    path.write_text(json.dumps(scope))
    manifest = {k: scope[k] for k in ('task', 'source_reference', 'allowed_response_role')}
    manifest['organizer_clearance'] = {'status': 'WRITTEN_CONFIRMATION_PRESENT',
        'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    require_response_role(manifest, tmp_path, 'SIGNED_RESPONSE')
    manifest['source_reference'] = 'different-source'
    with pytest.raises(ValueError, match='scope mismatch'):
        require_response_role(manifest, tmp_path, 'SIGNED_RESPONSE')
    manifest['source_reference'] = 'test-source'
    evidence.write_text('changed')
    with pytest.raises(ValueError, match='evidence missing or hash mismatch'):
        require_response_role(manifest, tmp_path, 'SIGNED_RESPONSE')
