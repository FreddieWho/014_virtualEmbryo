import hashlib
import json
import numpy as np
import pytest
from scripts.t3_next.source_roles import require_response_role, unsigned_response_shape


def bind(path, data):
    path.write_text(json.dumps(data))
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def make_permit(tmp_path, classification='ALLOWED'):
    policy=bind(tmp_path/'policy.json', {'test_fixture': True})
    review={'task':'T3:gata4', 'source_reference':'test-source',
        'policy_version':'T3_EXTERNAL_DATA_20260921', 'policy':policy,
        'review_status':'COMPLETED', 'classification':classification,
        'prohibited_records_remaining':0, 'allowed_response_roles':['SIGNED_RESPONSE'],
        'condition_allowlist':['ctrl','Rest'], 'license_status':'PERMITTED',
        'source_context_review':'Test fixture only; no actual source approval'}
    m={'task':'T3:gata4','status':'APPROVED_SANITIZED','allowed_response_role':'SIGNED_RESPONSE',
       'source_reference':'test-source','compliance_review':bind(tmp_path/'review.json',review)}
    return m,review


def test_allowed_source_needs_no_universal_organizer_letter(tmp_path):
    m,r=make_permit(tmp_path)
    assert require_response_role(m,tmp_path,'SIGNED_RESPONSE')['classification']=='ALLOWED'


@pytest.mark.parametrize('classification',['EXCLUDED','NEEDS_CLARIFICATION'])
def test_unresolved_or_excluded_review_not_authorized(tmp_path,classification):
    m,r=make_permit(tmp_path,classification)
    with pytest.raises(ValueError): require_response_role(m,tmp_path,'SIGNED_RESPONSE')


def test_known_protected_records_rejected_despite_allowed_label(tmp_path):
    m,r=make_permit(tmp_path);r['prohibited_records_remaining']=1
    m['compliance_review']=bind(tmp_path/'review.json',r)
    with pytest.raises(ValueError):require_response_role(m,tmp_path,'SIGNED_RESPONSE')


def test_review_scope_and_hash_required(tmp_path):
    m,r=make_permit(tmp_path);m['source_reference']='different-source'
    with pytest.raises(ValueError):require_response_role(m,tmp_path,'SIGNED_RESPONSE')
    m['source_reference']='test-source';(tmp_path/'review.json').write_text('{}')
    with pytest.raises(ValueError):require_response_role(m,tmp_path,'SIGNED_RESPONSE')


def test_r6_rejects_shape_only_before_matrix_access(tmp_path,monkeypatch):
    import anndata
    from scripts.t3_next.routes_extended import r6
    def forbidden_read(*args,**kwargs):pytest.fail('matrix read before approval')
    monkeypatch.setattr(anndata,'read_h5ad',forbidden_read)
    p=tmp_path/'manifest.json';p.write_text(json.dumps({'allowed_response_role':'RESPONSE_SHAPE_ONLY'}))
    with pytest.raises(ValueError):r6(None,p)


def test_shape_discards_sign_and_scale():
    x=np.array([[1.,-2.,3.],[0.,0.,0.]])
    np.testing.assert_allclose(unsigned_response_shape(x),unsigned_response_shape(x*[-4,4,-4]))
    with pytest.raises(ValueError):unsigned_response_shape([[np.nan]])
