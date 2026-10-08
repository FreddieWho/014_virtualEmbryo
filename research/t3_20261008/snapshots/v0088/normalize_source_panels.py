"""Reconstruct frozen whitelisted panels without fitting or response evaluation.

Normalization and barcode/embryo join are extracted unchanged from the v87
run_crossko7_hurdle_v2.py preparation stage. Outputs use a fresh destination.
"""
import os
for name in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '2'
import hashlib
import json
from pathlib import Path
import anndata as ad
import numpy as np
import pandas as pd

P = Path(__file__).parent
A = Path('/workspace/shared/t3_developmental_sources/annotations')
O = P / 'source_panel' / 'normalized'
O.mkdir(parents=True, exist_ok=True)
FROZEN = Path('/workspace/shared/t3_v87_restored')
expected = {r['gene']: r for r in json.loads((FROZEN / 'crossko7_hurdle_v2_results/MERGE_RECEIPT.json').read_text())}

def norm(x):
    s=np.asarray(x.sum(1)).ravel();assert(s>0).all();return np.log1p(x.toarray()*10000/s[:,None]).astype('float32')

merge = []
for gene in ['WT','Dnmt3a','Kmt2a','Kdm2b','Dnmt1','Dnmt3b','Ehmt2','Kmt2b']:
    file = P / 'source_panel' / ('WT_idmatched_raw_panel.h5ad' if gene == 'WT' else gene + '_raw_panel.h5ad')
    a = ad.read_h5ad(file)
    obs = pd.read_csv(A / f'{"G9a" if gene == "Ehmt2" else gene}_E8.5_cell_annotations.tsv', sep='\t')
    assert obs.barcode.is_unique
    keep = obs.barcode.isin(a.obs_names)
    idx = a.obs_names.get_indexer(obs.loc[keep,'barcode'])
    sub = a[idx].copy()
    obs = obs.loc[keep].reset_index(drop=True)
    sub.obs = obs.set_index('barcode')
    z = norm(sub.X)
    row = dict(gene=gene, whitelist=len(keep), matched=int(keep.sum()), missing=int((~keep).sum()),
               embryos=obs.embryo.nunique(), sex_embryos=obs[['embryo','sex']].drop_duplicates().sex.value_counts().to_dict(),
               input_sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    for key in ['whitelist', 'matched', 'missing', 'embryos', 'sex_embryos']:
        assert row[key] == expected[gene][key], (gene, key, row[key], expected[gene][key])
    assert z.shape[1] == 500 and sub.var_names.is_unique
    assert np.isfinite(z).all() and (z >= 0).all()
    row['max_library_error'] = float(np.max(np.abs(np.expm1(z.astype(float)).sum(1) - 10000)))
    assert row['max_library_error'] < .02
    sub.X = z
    out = O / f'{gene}_whitelisted_panel10000.h5ad'
    assert not out.exists(), out
    sub.write_h5ad(out, compression='gzip')
    reread = ad.read_h5ad(out)
    assert np.array_equal(z, reread.X)
    assert sub.obs.equals(reread.obs) and sub.var_names.equals(reread.var_names)
    row.update(output=str(out), sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
               expression_array_sha256=hashlib.sha256(z.tobytes()).hexdigest(), frozen_merge_matches=True)
    merge.append(row)
    (O / 'MERGE_RECEIPT.json').write_text(json.dumps(merge, indent=2))
    print(json.dumps(row), flush=True)

receipt = dict(status='PASS', matched_cells=sum(r['matched'] for r in merge),
               genotype_count=len(merge), protected_target_outcomes_used=False,
               model_fit_or_evaluation_run=False, baseline_pack_modified=False,
               frozen_join_source=str(FROZEN / 'run_crossko7_hurdle_v2.py'),
               normalization='Identical v87 sparse panel closure to 10000 then log1p float32',
               reconstruction_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(O / 'RECONSTRUCTION_CHECKS.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt), flush=True)
