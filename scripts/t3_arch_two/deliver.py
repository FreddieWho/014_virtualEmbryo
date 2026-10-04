"""Serial candidate registration and a single manual upload batch package."""
from pathlib import Path
import argparse
import csv
import fcntl
import hashlib
import io
import json
import shutil
import sys
import zipfile
import numpy as np
import anndata as ad
from scripts.t3_priority_six.common import ROOT, sha, dump

RUN = ROOT / 'artifacts/t3_arch_two_20261001'
PARENT = ROOT / 'submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad'
LANES = ['a_residual_flow', 'b_fate_mass_emit2']


def register(lane):
    sys.path.insert(0, str(ROOT / 'docs/batch3/interfaces'))
    from virtual_embryo_tools.contract_io import validate_h5ad_contract
    run = RUN / lane
    if (run / 'REGISTRATION.json').exists():
        raise FileExistsError('candidate already registered')
    result = json.loads((run / 'RESULT.json').read_text())
    if result['status'] != 'FULL_TARGET_INFERENCE_COMPLETE_RESEARCH':
        raise ValueError('incomplete core inference')
    if sha(run / 'research.h5ad') != result['sha256']:
        raise ValueError('research artifact changed')
    scoped_parent = PARENT
    scoped_sha = sha(PARENT)
    candidate = ad.read_h5ad(run / 'research.h5ad')
    if lane.startswith('b_fate_mass'):
        donor = np.load(run / 'DONOR_INDICES.npy')
        carrier = ad.read_h5ad(run / 'WT_CARRIER.h5ad')
        carrier.obs_names = candidate.obs_names.copy()
        carrier.uns['ve_contract'] = {'normalization': 'log_normalized', 'source': 'documented whole-vector measured WT donor carrier; v0009 row-count/panel lineage'}
        scoped_parent = run / 'resampled_WT_carrier.h5ad'
        carrier.write_h5ad(scoped_parent, compression='gzip')
        scoped_sha = sha(scoped_parent)
        np.testing.assert_array_equal(carrier.obsm['spatial_3D'], candidate.obsm['spatial_3D'])
        dump(run / 'CARRIER_LINEAGE.json', {'historical_parent': 'v0009', 'parent_sha256': sha(PARENT),
             'donor_indices_sha256': sha(run / 'DONOR_INDICES.npy'), 'scoped_parent_sha256': scoped_sha,
             'whole_expression_and_coordinates_sampled_together': True, 'official_fixed_row_correspondence_required': False,
             'donor_stages': 'E8.0/E8.75/E9.5 WT; explicit stage counts in POPULATION_DIAGNOSTICS.json',
             'donor_pool_offset_indices': True})
    with (ROOT / 'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        index = ROOT / 'submissions/INDEX.tsv'
        with index.open() as f:
            reader = csv.DictReader(f, delimiter='\t')
            fields, rows = reader.fieldnames, list(reader)
        version = 'v%04d' % (1 + max(int(r['version'][1:]) for r in rows if r['board'] == 'T3:gata4'))
        folder = ROOT / 'submissions/candidates/T3_gata4' / f'{version}_arch_{lane}'
        folder.mkdir(exist_ok=False)
        path = folder / 'submission.h5ad'
        shutil.copyfile(run / 'research.h5ad', path)
        contract = validate_h5ad_contract(path, task='T3', board='gata4',
                scorer_lock=ROOT / 'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',
                parent_path=scoped_parent, parent_sha256=scoped_sha)
        dump(folder / 'contract.json', contract)
        if contract['status'] != 'PASS':
            raise ValueError(contract)
        record = dict(status='candidate', submission_group='T3-ARCH-TWO-20261001', board='T3:gata4',
              version=version, method='arch_' + lane, path=str(path.relative_to(ROOT)), n_cells=7449,
              n_genes=500, seed=20261001, target_used='false', local_contract='pass', sha256=sha(path),
              server_score='', score_status='score_pending',
              notes=f'parent=v0009; scoped_parent={scoped_parent.relative_to(ROOT)}; run={run.relative_to(ROOT)}; READY_NOT_SUBMITTED; exploratory architecture, not validated target improvement; reports/t3_arch_two_execution_20261001/REPORT.md')
        with index.open('a') as f:
            csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n').writerow(record)
        with (ROOT / 'docs/coordination/T3_TRACKING.md').open('a') as f:
            f.write(f'\n- 2026-10-01｜T3-ARCH-TWO｜{version} {lane}｜父v0009，完整7449×500，contract PASS；未提交/未评分；新架构完整实跑、科学限制见执行报告；{record["path"]}；D-20261001-T3ARCH-002。\n')
    name = f't3_gata4__{"a_flow" if lane.startswith("a_") else "b_fate"}__{version}.h5ad'
    dump(run / 'REGISTRATION.json', {'status': 'READY_NOT_SUBMITTED', 'candidate': record,
          'portal_file': name, 'contract': str((folder / 'contract.json').relative_to(ROOT)),
          'core_result': str((run / 'RESULT.json').relative_to(ROOT))})
    print('REGISTERED', version, name, flush=True)


def tsv(items):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(items[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(items)
    return output.getvalue()


def package():
    receipts = [json.loads((RUN / lane / 'REGISTRATION.json').read_text()) for lane in LANES]
    members, mappings, run_ids, evidence = [], [], [], []
    for lane, receipt in zip(LANES, receipts):
        row, name = receipt['candidate'], receipt['portal_file']
        path = ROOT / row['path']
        assert name == name.lower() and len(name) <= 50 and sha(path) == row['sha256']
        members.append({'filename': name, 'bytes': path.stat().st_size, 'sha256': row['sha256']})
        mappings.append({'filename': name, 'board': 'T3:gata4', 'version': row['version'], 'canonical_path': row['path']})
        run_ids.append({'filename': name, 'run_id': f'artifacts/t3_arch_two_20261001/{lane}',
                        'parent_version': 'v0009', 'candidate_version': row['version']})
        evidence.append({'filename': name, 'input_lock': f'artifacts/t3_arch_two_20261001/{"A" if lane.startswith("a_") else "B"}_INPUT_LOCK.json',
                         'contract': receipt['contract'], 'core_result': receipt['core_result'],
                         'report': 'reports/t3_arch_two_execution_20261001/REPORT.md'})
    path = ROOT / 'deliveries/arch2__t3__upload__20261001.zip'
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for mapping in mappings:
            archive.write(ROOT / mapping['canonical_path'], mapping['filename'])
        for name, items in [('MANIFEST.tsv', members), ('UPLOAD_MANIFEST.tsv', mappings),
                            ('RUN_ID_MAP.tsv', run_ids), ('EVIDENCE_MANIFEST_POINTERS.tsv', evidence)]:
            archive.writestr(name, tsv(items))
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        for member in members:
            assert hashlib.sha256(archive.read(member['filename'])).hexdigest() == member['sha256']
    dump(RUN / 'DELIVERY.json', {'status': 'READY_NOT_SUBMITTED', 'zip': str(path.relative_to(ROOT)),
          'sha256': sha(path), 'members': members, 'portal_upload': 'NOT_RUN', 'server_scores': 'NOT_RUN'})
    print('PACKAGED', path, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=LANES + ['b_fate_mass', 'package'])
    args = parser.parse_args()
    package() if args.action == 'package' else register(args.action)
