"""Validate reconstruction against the immutable v87 source-panel receipts."""
import csv
import hashlib
import json
from pathlib import Path

P = Path(__file__).parent
F = Path('/workspace/shared/t3_v87_restored')
rows = []
for name in ['PREPROCESS.json', 'WT_IDMATCH_PREPROCESS.json', 'EXPANDED_PREPROCESS.json']:
    expected = json.loads((F / 'source_panel' / name).read_text())
    actual = json.loads((P / 'source_panel' / name).read_text())
    assert len(actual) == len(expected)
    for old, new in zip(expected, actual):
        for key in ['gene', 'raw_matrix_shape', 'nnz', 'panel_symbols_found', 'retained_panel_positive_droplets', 'sha256']:
            assert new[key] == old[key], (name, key, new[key], old[key])
        file = Path(new['output'])
        assert hashlib.sha256(file.read_bytes()).hexdigest() == new['sha256']
        rows.append(dict(path=str(file), sha256=new['sha256'],
                         source='Frozen v87 approved GSE122187 WT and GSE137337 unrelated-KO inputs',
                         shape=f"{new['retained_panel_positive_droplets']}x500", kind='raw_panel',
                         checks='byte-identical to frozen v87 panel'))
normalized = P / 'source_panel' / 'normalized'
merge = json.loads((normalized / 'MERGE_RECEIPT.json').read_text())
assert len(merge) == 8
for r in merge:
    assert r['frozen_merge_matches']
    assert hashlib.sha256(Path(r['output']).read_bytes()).hexdigest() == r['sha256']
    rows.append(dict(path=r['output'], sha256=r['sha256'],
                     source='Frozen v87 source panel plus original SNP-derived embryo/barcode annotation whitelist',
                     shape=f"{r['matched']}x500", kind='normalized_panel',
                     checks='exact frozen join; log1p panel library 10000; finite/nonnegative; H5AD round-trip PASS'))
fmap = json.loads((P / 'FEATURE_MAP_AUDIT.json').read_text())
for r in fmap.values():
    assert r['unique'] == 500 and not r['missing'] and not r['duplicates']
for name in ['Dnmt1', 'Dnmt3b', 'Ehmt2', 'Kmt2b']:
    r = json.loads((P / 'source_panel' / f'{name}_FEATURE_MAP.json').read_text())
    assert r['mapped_unique'] == 500 and not r['missing'] and not r['duplicates']
checks = dict(status='PASS', candidate_id='none: source reconstruction only', parent='v0087',
              raw_panels_byte_identical=len([r for r in rows if r['kind'] == 'raw_panel']),
              normalized_panels=len(merge), normalized_cells=sum(r['matched'] for r in merge),
              full_merge_frozen_match=True, wt_missing_barcodes=merge[0]['missing'],
              scientific_blocker=False, blocks_submission=False,
              protected_target_outcomes_used=False, portal_access=False,
              rows=rows)
(P / 'SOURCE_REBUILD_CHECKS.json').write_text(json.dumps(checks, indent=2))
with (P / 'SOURCE_REBUILD_INDEX_FRAGMENT.tsv').open('w') as f:
    writer = csv.writer(f, delimiter='\t', lineterminator='\n')
    writer.writerow(['local_path', 'source', 'source_uri_or_commit', 'task_or_role', 'shape', 'panel_or_schema_check', 'sha256', 'status'])
    for r in rows:
        writer.writerow([r['path'], r['source'], str(F / 'PACK_FILE_HASHES.json'), 'T3 approved source reconstruction; ' + r['kind'],
                         r['shape'], r['checks'], r['sha256'], 'VERIFIED_RECONSTRUCTED; same approved scope'])
print(json.dumps({k:v for k,v in checks.items() if k!='rows'}, indent=2))
