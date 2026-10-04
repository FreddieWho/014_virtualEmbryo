"""Read-only numerical audit of existing T3 artifacts; no fitting or scoring."""
from pathlib import Path
import csv
import hashlib
import json
from collections import Counter
import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def dense(x):
    return np.asarray(x.toarray() if sparse.issparse(x) else x)


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def main():
    index = list(csv.DictReader((ROOT / 'submissions/INDEX.tsv').open(), delimiter='\t'))
    rows = [r for r in index if r['board'] == 'T3:gata4']
    byversion = {r['version']: r for r in rows}
    parent = ad.read_h5ad(ROOT / byversion['v0009']['path'])
    base = dense(parent.X)
    genes = parent.var_names.tolist()
    gi = genes.index('Gata4')
    keep = np.arange(len(genes)) != gi
    wt = ad.read_h5ad(ROOT / 'data/E8.75.h5ad')
    wi = wt.obs_names.get_indexer(parent.obs_names)
    if (wi < 0).any():
        raise ValueError('WT row identity missing')
    wx = dense(wt[:, genes].X)
    original = wx[wi]
    positive = original[:, gi] > 0
    result = {
        'scope': 'Existing artifacts only; no target truth, retraining, candidate or portal scoring.',
        'index_t3_rows': len(rows),
        'score_status_counts': dict(Counter(r['score_status'] for r in rows)),
        'input_hashes': {},
        'wt': {
            'full_cells': wt.n_obs,
            'carrier_cells': parent.n_obs,
            'carrier_zero_fraction': float(np.mean(base == 0)),
            'carrier_gata4_positive_cells': int(positive.sum()),
            'carrier_gata4_zero_cells': int((~positive).sum()),
            'full_gata4_positive_cells': int(np.count_nonzero(wx[:, gi])),
            'full_obs_columns': wt.obs.columns.tolist(),
            'carrier_original_types': dict(Counter(parent.obs['celltype'].astype(str))),
        },
        'scored_artifact_geometry': [],
        'representative_expression': [],
    }
    for col in ['sample', 'sample_id', 'embryo', 'embryo_id', 'batch']:
        if col in wt.obs:
            result['wt'][col + '_full'] = dict(Counter(wt.obs[col].astype(str)))
            result['wt'][col + '_carrier'] = dict(Counter(wt.obs.iloc[wi][col].astype(str)))
    versions = {'v0008', 'v0009', 'v0018', 'v0019', 'v0020', 'v0022', 'v0034', 'v0035', 'v0036', 'v0037', 'v0040', 'v0041', 'v0046', 'v0048', 'v0058'}
    for row in rows:
        if row['score_status'] != 'scored' and not (row['status'] == 'scored' and row['server_score']):
            continue
        path = ROOT / row['path']
        a = ad.read_h5ad(path, backed='r')
        identity = a.obs_names.equals(parent.obs_names)
        ordered = a.var_names.equals(parent.var_names)
        coordinates = np.array_equal(a.obsm['spatial_3D'], parent.obsm['spatial_3D'])
        result['scored_artifact_geometry'].append({
            'version': row['version'], 'cells': a.n_obs,
            'same_rows_and_order_v0009': identity,
            'same_genes_and_order_v0009': ordered,
            'same_coordinates_v0009': coordinates,
        })
        if row['version'] in versions and identity and ordered:
            x = dense(a.X[:])
            difference = x[:, keep].astype(float) - base[:, keep]
            delta = difference.mean(0)
            changed = difference != 0
            result['representative_expression'].append({
                'version': row['version'], 'downstream_changed_cells': int(np.any(changed, 1).sum()),
                'downstream_changed_genes': int(np.any(changed, 0).sum()),
                'downstream_changed_entries': int(changed.sum()),
                'downstream_changes_in_gata4_zero_cells': int(changed[~positive].sum()),
                'activated_zero_entries': int(((base[:, keep] == 0) & (x[:, keep] > 0)).sum()),
                'zero_fraction': float(np.mean(x == 0)),
                'downstream_mean_delta_l2': float(np.linalg.norm(delta)),
                'downstream_mean_delta_maxabs': float(np.max(np.abs(delta))),
                'downstream_mean_delta_ge_025': int(np.sum(np.abs(delta) >= .25)),
            })
            result['input_hashes'][row['path']] = sha(path)
        a.file.close()
    cp = ROOT / 'artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/celloracle/Gata4_state_response.tsv'
    response = pd.read_csv(cp, sep='\t')
    group = response.groupby('response_gene')['effect']
    means = group.mean()
    absmeans = group.apply(lambda a: float(np.mean(np.abs(a))))
    nonzero_both = group.apply(lambda a: bool((a > 0).any() and (a < 0).any()))
    result['celloracle_summary'] = {
        'rows': len(response), 'states': response['state'].nunique(),
        'genes': response['response_gene'].nunique(),
        'zero_state_gene_medians': int((response['effect'] == 0).sum()),
        'zero_state_gene_median_fraction': float((response['effect'] == 0).mean()),
        'genes_with_nonzero_mean_effect': int((means != 0).sum()),
        'genes_with_opposite_sign_states': int(nonzero_both.sum()),
        'genes_mean_absolute_over_absolute_mean_gt5': int(((absmeans > 0) & (absmeans > 5 * np.abs(means))).sum()),
        'effect_extraction': 'median within state; equal-weight mean across states in R6 adapter',
    }
    result['input_hashes'][str(cp.relative_to(ROOT))] = sha(cp)
    ep = ROOT / 'data/E9.5_RNA.h5ad'
    e95 = ad.read_h5ad(ep, backed='r')
    ex = dense(e95[:, [g for g in genes if g != 'Gata4']].X)
    iqr = np.quantile(ex, .75, axis=0) - np.quantile(ex, .25, axis=0)
    eg = np.asarray([g for g in genes if g != 'Gata4'])
    active = set(means[means != 0].index)
    suppressed = eg[(iqr == 0) & np.isin(eg, list(active))]
    result['wt_dispersion_cap'] = {
        'source_cells': e95.n_obs, 'examined_downstream_genes': len(eg),
        'zero_iqr_genes': int((iqr == 0).sum()),
        'celloracle_nonzero_effect_genes_suppressed_by_zero_iqr': len(suppressed),
        'suppressed_gene_examples': suppressed[:25].tolist(),
    }
    e95.file.close()
    sub = list(csv.DictReader((ROOT / 'reports/SERVER_SUBMETRIC_REGISTRY.tsv').open(), delimiter='\t'))
    t3 = [r for r in sub if r['board'] == 'T3:gata4']
    severity = [float(r['skill']) for r in t3 if r['metric'] == 'severity_slope']
    result['server_submetric_summary'] = {
        't3_rows': len(t3), 'versions': len(set(r['version'] for r in t3)),
        'severity_observations': len(severity), 'severity_distinct_skills': sorted(set(severity)),
        'source': 'reports/SERVER_SUBMETRIC_REGISTRY.tsv; user-reported server skills; not recomputed scores',
    }
    for p in ['submissions/INDEX.tsv', 'reports/SERVER_SUBMETRIC_REGISTRY.tsv', 'scripts/g0/t3_r6_cipher.py', 'scripts/g0/_t3_util.py', 'scripts/g0/t3_r8_knk.py', 'scripts/t3_s1a_state_join.py', 'scripts/t3_next/five.py', 'scripts/t3_next/five_ops.py', 'third_party/veckit/common/core_metrics.py']:
        result['input_hashes'][p] = sha(ROOT / p)
    (OUT / 'AUDIT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['input_hashes', 'scored_artifact_geometry']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
