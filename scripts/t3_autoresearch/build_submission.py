"""Emit the locked T3 response model as a complete, unscored upload candidate."""
from pathlib import Path
import csv
import fcntl
import hashlib
import io
import json
import re
import shutil
import sys
import zipfile

import anndata as ad
import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'docs/batch3/interfaces'))
from t3_next.source_roles import require_response_role
from t3_autoresearch import retained_model
from virtual_embryo_tools.contract_io import validate_h5ad_contract

RUN = ROOT / 'artifacts/t3_autoresearch_delivery_20261003'
REPORT = ROOT / 'reports/t3_autoresearch_delivery_20261003'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def tsv(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def main():
    RUN.mkdir(exist_ok=True)
    REPORT.mkdir(exist_ok=True)
    assert not (RUN / 'DELIVERY.json').exists(), 'Already delivered; never overwrite'
    assert not (REPORT / 'HANDOFF.json').exists(), 'Already handed off'
    final_path = ROOT / 'reports/t3_autoresearch_20261002/FINAL_CHECK.json'
    final = json.loads(final_path.read_text())
    model_path = ROOT / 'scripts/t3_autoresearch/retained_model.py'
    assert sha(model_path) == final['model_sha256']
    manifest_path = ROOT / 'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    require_response_role(manifest, ROOT, 'SIGNED_RESPONSE')
    source_path = ROOT / manifest['files']['expression']['path']
    assert sha(source_path) == manifest['files']['expression']['sha256']
    source = ad.read_h5ad(source_path)
    assert source.shape == (5454, 500) and source.obs.model_input.all()
    cfg = json.loads((ROOT / 'artifacts/autoresearch/t3-20261002-v1/PROVENANCE.json').read_text())
    genes = sum(cfg['split'].values(), [])
    labels = source.obs.condition.astype(str).to_numpy()
    assert set(labels) == set(genes) | {'ctrl'}
    x = source.X.toarray() if sparse.issparse(source.X) else np.asarray(source.X)
    ctrl = x[labels == 'ctrl'].mean(0)
    epath = ROOT / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert sha(epath) == cfg['embedding_sha256']
    emb = np.load(epath)
    ei = {g: i for i, g in enumerate(emb['genes'])}
    train = {'genes': np.array(genes), 'E': emb['embedding'][[ei[g] for g in genes]],
             'Y': np.array([x[labels == g].mean(0) - ctrl for g in genes])}
    query = {'genes': np.array(['Gata4']), 'E': emb['embedding'][[ei['Gata4']]]}
    delta = np.asarray(retained_model.predict(train, query), dtype=float)
    assert delta.shape == (1, 500) and np.isfinite(delta).all()
    saved_path = ROOT / 'reports/t3_autoresearch_20261002/POST_SELECTION_ARRAYS.npz'
    assert sha(saved_path) == final['arrays_sha256']
    np.testing.assert_allclose(delta, np.load(saved_path)['gata4_source_scale_prediction'], rtol=0, atol=1e-12)
    response_path = RUN / 'MODEL_RESPONSE.npy'
    if response_path.exists():
        np.testing.assert_array_equal(delta, np.load(response_path))
    else:
        np.save(response_path, delta)
    # No changes to the completed autoresearch metric/model/holdout checks.
    with (ROOT / 'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        index = ROOT / 'submissions/INDEX.tsv'
        with index.open() as f:
            reader = csv.DictReader(f, delimiter='\t')
            fields, rows = reader.fieldnames, list(reader)
        t3 = [r for r in rows if r['board'] == 'T3:gata4']
        parent_record = next(r for r in t3 if r['version'] == 'v0009')
        parent_path = ROOT / parent_record['path']
        assert sha(parent_path) == parent_record['sha256']
        parent = ad.read_h5ad(parent_path)
        panel = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
        assert parent.shape == (7449, 500)
        assert parent.var_names.tolist() == source.var_names.tolist() == panel
        base = parent.X.toarray() if sparse.issparse(parent.X) else np.asarray(parent.X)
        ko = panel.index('Gata4')
        assert np.all(base[:, ko] == 0)
        raw = base.astype(float) + delta
        prediction = np.maximum(raw, 0).astype('float32')
        prediction[:, ko] = 0
        assert np.isfinite(prediction).all() and np.all(prediction >= 0)
        assert np.any(prediction != base)
        # The internal carrier contract protects WT reference layers/raw too.
        # Predictions reside in X; these reference snapshots are not predictions.
        carrier = parent.copy()
        carrier.X = prediction
        carrier.uns['ve_contract'] = {'normalization': 'log_normalized',
            'source': 'locked source model log-expression delta added to v0009 WT carrier; clip at zero; Gata4 zero'}
        carrier.uns['t3_autoresearch'] = {'model_sha256': final['model_sha256'],
            'source_conditions': 26, 'source_cells': 5454, 'target_truth_used': False,
            'emission': 'max(WT_log_expression + model_delta, 0); Gata4=0',
            'transfer_validated': False,
            'layers_and_raw': 'immutable parent WT references; prediction is in X'}
        used = [int(r['version'][1:]) for r in t3]
        for p in (ROOT / 'submissions/candidates/T3_gata4').iterdir():
            match = re.match(r'v(\d+)_', p.name)
            if match:
                used.append(int(match.group(1)))
        version = f'v{max(used) + 1:04d}'
        folder = ROOT / f'submissions/candidates/T3_gata4/{version}_ar_complex'
        folder.mkdir(exist_ok=False)
        path = folder / 'submission.h5ad'
        carrier.write_h5ad(path, compression='gzip')
        contract = validate_h5ad_contract(path, task='T3', board='gata4',
            scorer_lock=ROOT / 'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',
            parent_path=parent_path, parent_sha256=parent_record['sha256'])
        dump(folder / 'contract.json', contract)
        assert contract['status'] == 'PASS', contract
        roundtrip = ad.read_h5ad(path)
        np.testing.assert_array_equal(roundtrip.X, prediction)
        np.testing.assert_array_equal(roundtrip.obsm['spatial_3D'], parent.obsm['spatial_3D'])
        assert roundtrip.obs_names.equals(parent.obs_names)
        assert np.all(roundtrip.X[:, ko] == 0)
        input_lock = {'model': {'path': str(model_path.relative_to(ROOT)), 'sha256': sha(model_path)},
                      'source': manifest['files']['expression'], 'source_manifest_sha256': sha(manifest_path),
                      'embedding_sha256': sha(epath), 'prior_final_check_sha256': sha(final_path),
                      'prediction_replay': 'PASS atol1e-12; complete26-condition inference'}
        dump(RUN / 'INPUT_LOCK.json', input_lock)
        downstream = np.arange(500) != ko
        diagnostics = {'shape': list(prediction.shape), 'all_source_conditions_used': len(genes),
            'full_model_replay': 'PASS', 'coordinates_preserved': True, 'Gata4_zero': True,
            'source_delta_l2': float(np.linalg.norm(delta)), 'source_delta_min': float(delta.min()),
            'source_delta_max': float(delta.max()), 'output_density': float(np.mean(prediction > 0)),
            'parent_density': float(np.mean(base > 0)),
            'activated_entries': int(np.sum((base == 0) & (prediction > 0))),
            'nonnegative_clipped_entries': int(np.sum(raw[:, downstream] < 0)),
            'changed_output_genes': int(np.any(prediction != base, axis=0).sum()),
            'mean_absolute_change': float(np.abs(prediction - base).mean()),
            'clipping_mean_response_error_max': float(np.max(np.abs(
                (prediction.astype(float) - base).mean(0)[downstream] - delta[0, downstream]))),
            'target_score': 'NOT_RUN_NO_LEGAL_TARGET_TRUTH',
            'limits': ['cross-domain additive log-scale transfer unvalidated',
                       'clipping changes negative mean effects; positive shifts activate zeros',
                       'source development improvement is not this H5AD target score'],
            'blocks_submission': False}
        dump(RUN / 'DIAGNOSTICS.json', diagnostics)
        short = f't3_gata4__ar_complex__{version}.h5ad'
        assert short == short.lower() and len(short) <= 50
        deliveries = ROOT / 'deliveries'
        deliveries.mkdir(exist_ok=True)
        direct = deliveries / short
        assert not direct.exists()
        shutil.copyfile(path, direct)
        digest = sha(path)
        assert sha(direct) == digest
        member = {'filename': short, 'bytes': path.stat().st_size, 'sha256': digest}
        mapping = {'filename': short, 'board': 'T3:gata4', 'version': version,
                   'canonical_path': str(path.relative_to(ROOT))}
        runs = {'filename': short, 'run_id': str(RUN.relative_to(ROOT)),
                'parent_version': 'v0009', 'candidate_version': version}
        evidence = {'filename': short, 'input_lock': str((RUN / 'INPUT_LOCK.json').relative_to(ROOT)),
                    'contract': str((folder / 'contract.json').relative_to(ROOT)),
                    'diagnostics': str((RUN / 'DIAGNOSTICS.json').relative_to(ROOT)),
                    'source_report': 'reports/t3_autoresearch_20261002/REPORT.md'}
        package = deliveries / 't3ar__t3__upload__20261003.zip'
        with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as z:
            z.write(path, short)
            for name, records in [('MANIFEST.tsv', [member]), ('UPLOAD_MANIFEST.tsv', [mapping]),
                                  ('RUN_ID_MAP.tsv', [runs]), ('EVIDENCE_MANIFEST_POINTERS.tsv', [evidence])]:
                z.writestr(name, tsv(records))
        with zipfile.ZipFile(package) as z:
            assert hashlib.sha256(z.read(short)).hexdigest() == digest
            assert len(z.namelist()) == 5
        record = dict(status='candidate', submission_group='T3-AUTORESEARCH-DELIVERY-20261003',
            board='T3:gata4', version=version, method='ar_specific_complex_log_residual',
            path=str(path.relative_to(ROOT)), n_cells=7449, n_genes=500, seed='none', target_used='false',
            local_contract='pass', sha256=digest, server_score='', score_status='score_pending',
            notes='parent=v0009; locked48-trial source model; full26-condition replay; additive log residual clipped at0; Gata4=0; READY_NOT_SUBMITTED; target transfer unvalidated; reports/t3_autoresearch_delivery_20261003/REPORT.md')
        with index.open('a') as f:
            csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n').writerow(record)
        with (ROOT / 'docs/coordination/T3_TRACKING.md').open('a') as f:
            f.write(f'\n- 2026-10-03｜T3 autoresearch补齐H5AD｜{version}，父v0009；锁定模型完整26条件推断重放，log残差加到完整7449×500 WT载体、截负及Gata4置零，坐标保留，contract PASS。已登记、未提交/未评分；源域20.31%不作为此H5AD目标分。D-20261003-T3ARDEL-001。\n')
        delivery = {'task': 'T3:gata4', 'status': 'READY_NOT_SUBMITTED', 'candidate_id': f'candidate/T3_gata4/{version}_ar_complex',
            'parent_candidate': 'candidate/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all',
            'index': 'submissions/INDEX.tsv', 'version': version, 'artifact': record['path'],
            'sha256': digest, 'contract_result': 'PASS', 'contract_report': evidence['contract'],
            'download_h5ad': str(direct.relative_to(ROOT)), 'zip': str(package.relative_to(ROOT)),
            'zip_sha256': sha(package), 'core_check': 'complete locked-model inference replay PASS',
            'risks': diagnostics['limits'], 'proposed_decision': 'manual upload exploratory candidate; incumbent unchanged until server return',
            'blocker': 'target-domain generalization unvalidated; blocks_submission:false', 'portal_upload': 'NOT_RUN'}
        dump(REPORT / 'HANDOFF.json', delivery)
        dump(RUN / 'DELIVERY.json', delivery)
    print(json.dumps(delivery, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
