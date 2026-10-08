"""Package the wave-2 t3_six2 candidates into one delivery zip (batch rule)."""
import csv, hashlib, io, json, zipfile
from pathlib import Path

ROOT = Path('/home/huyudi/014_virtualEmbryo')
OUT = ROOT / 'deliveries/t3six2__t3__upload__20261007.zip'

LANE = {
    'six2_o1_hnmf': 'hnmf', 'six2_o2_pnmf': 'pnmf', 'six2_o3_psb': 'psb',
    'six2_n1_qtl': 'qtl', 'six2_n2_dsign': 'dsign',
}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def tsv(rows, fields):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, delimiter='\t', lineterminator='\n')
    w.writeheader(); w.writerows(rows)
    return out.getvalue()


def main():
    if OUT.exists():
        raise FileExistsError('immutable delivery already exists')
    with (ROOT / 'submissions/INDEX.tsv').open() as f:
        idx = {r['path']: r for r in csv.DictReader(f, delimiter='\t')}
    members, mapping, runs, evidence = [], [], [], []
    for path, row in sorted(idx.items()):
        if row['board'] != 'T3:gata4' or not row['method'].startswith('six2_'):
            continue
        if row['score_status'] != 'score_pending' or row['local_contract'] != 'pass':
            continue
        route = row['method']
        lane = LANE[route]
        name = f"t3_gata4__{lane}__{row['version']}.h5ad"
        if len(name) > 50 or name != name.lower():
            raise ValueError('portal name contract: ' + name)
        full = ROOT / path
        if sha(full) != row['sha256']:
            raise ValueError('candidate drift: ' + path)
        folder = full.parent
        members.append({'filename': name, 'bytes': full.stat().st_size, 'sha256': row['sha256']})
        mapping.append({'filename': name, 'board': row['board'], 'version': row['version'], 'canonical_path': path})
        runs.append({'filename': name, 'run_id': 'reports/t3_six_routes_20261007', 'parent_version': 'v0048',
                     'candidate_version': row['version']})
        evidence.append({'filename': name, 'contract': str(folder / 'contract.json'),
                         'selection': f"reports/t3_six_routes_20261007/{route.split('six2_')[1]}/SELECTION.json",
                         'report': 'reports/t3_six_routes_20261007/REPORT.md'})
    if len(members) != 5:
        raise ValueError(f'expected 5 members, got {len(members)}')
    with zipfile.ZipFile(OUT, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as z:
        for m in mapping:
            z.write(ROOT / m['canonical_path'], m['filename'])
        for name, rows in [('MANIFEST.tsv', members), ('UPLOAD_MANIFEST.tsv', mapping),
                           ('RUN_ID_MAP.tsv', runs), ('EVIDENCE_MANIFEST_POINTERS.tsv', evidence)]:
            z.writestr(name, tsv(rows, list(rows[0])))
    with zipfile.ZipFile(OUT) as z:
        for m in members:
            if hashlib.sha256(z.read(m['filename'])).hexdigest() != m['sha256']:
                raise ValueError('package hash mismatch: ' + m['filename'])
        if z.testzip() is not None:
            raise ValueError('zip CRC failure')
    receipt = OUT.with_suffix('.zip.receipt.json')
    receipt.write_text(json.dumps({
        'status': 'READY_NOT_SUBMITTED', 'zip_path': str(OUT.relative_to(ROOT)),
        'zip_sha256': sha(OUT), 'members': len(members), 'portal_upload': 'NOT_RUN',
        'server_scores': 'NOT_RUN', 'run_dirs': ['reports/t3_six_routes_20261007'],
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'package': str(OUT), 'candidates': len(members), 'status': 'READY_NOT_SUBMITTED'}))


if __name__ == '__main__':
    main()
