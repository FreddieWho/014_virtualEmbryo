"""Preserve maximal WT overlap under the frozen B state quotas; no refitting."""
import json
import csv
import io
import fcntl
import shutil
import numpy as np
import anndata as ad
from scripts.t3_arch_two.fate import RUN, ROOT, emit, lineage, sha, dump, dense, quotas
import joblib


def maximal_choices(parent_indices, parent_labels, all_labels, shares, seed):
    counts = quotas(shares, len(parent_indices))
    rng = np.random.default_rng(seed)
    choices = []
    for state, count in enumerate(counts):
        current = parent_indices[parent_labels == state]
        if len(current):
            if count <= len(current):
                selected = current if count == len(current) else rng.choice(current, count, replace=False)
            else:
                selected = np.r_[current, rng.choice(current, count - len(current), replace=True)]
        else:
            pool = np.flatnonzero(all_labels == state)
            if count and not len(pool): raise ValueError('no WT donor support')
            selected = rng.choice(pool, count, replace=count > len(pool)) if count else np.array([], int)
        choices.extend(selected.tolist())
    return np.asarray(choices, int)


def run():
    original = RUN / 'b_fate_mass'
    directory = RUN / 'b_fate_mass_emit2'; directory.mkdir(exist_ok=False)
    cfg = json.loads((RUN / 'CONFIG.json').read_text())
    paths = cfg['fate_mass']['WT_paths']
    panel = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    objects = [ad.read_h5ad(ROOT / p)[:, panel].copy() for p in paths]
    xs = [dense(a.X).astype(np.float32) for a in objects]
    saved = joblib.load(original / 'population_model.joblib'); c = saved['chart']
    labels = []
    for x, obj in zip(xs, objects):
        z = c['pca'].transform((x[:, c['chosen']] - c['mu']) / c['sd']) / c['zscale']
        group = np.array([lineage(s) for s in obj.obs.celltype.astype(str)])
        states = np.full(len(x), -1, int)
        for name in set(group):
            km, offset = c['fits'][name]; states[group == name] = km.predict(z[group == name]) + offset
        labels.append(states)
    parent_path = ROOT / 'submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad'
    parent = ad.read_h5ad(parent_path)
    indices = objects[1].obs_names.get_indexer(parent.obs_names)
    offsets = np.r_[0, np.cumsum([len(x) for x in xs])]
    parent_indices = indices + offsets[1]
    parent_labels = labels[1][indices]
    shares = np.load(original / 'STATE_PREDICTION.npz')['prediction']
    donors = maximal_choices(parent_indices, parent_labels, np.concatenate(labels), shares, cfg['seed'])
    expected = quotas(shares, len(parent))
    np.testing.assert_array_equal(np.bincount(np.concatenate(labels)[donors], minlength=len(shares)), expected)
    retained = len(set(donors) & set(parent_indices))
    maximal = int(np.minimum(expected, np.bincount(parent_labels, minlength=len(shares))).sum())
    assert retained == maximal
    # The frozen model currently emits only E8.75 states. Do not invent alternative-stage geometry.
    if not ((donors >= offsets[1]) & (donors < offsets[2])).all():
        raise ValueError('new-stage donor needs explicitly qualified emission')
    carrier = parent.copy(); carrier.obs_names = [f'fate_keep_{i:05d}' for i in range(len(parent))]
    carrier.X = xs[1][donors - offsets[1]].copy()
    carrier.obsm['spatial_3D'] = np.asarray(objects[1].obsm['spatial_3D'])[donors - offsets[1]].copy()
    carrier.uns = {'ve_contract': {'normalization': 'log_normalized', 'source': 'maximal-overlap whole-vector E8.75 WT donor carrier'}}
    carrier.write_h5ad(directory / 'WT_CARRIER.h5ad', compression='gzip')
    candidate = carrier.copy(); candidate.X[:, panel.index('Gata4')] = 0
    candidate.uns['t3_architecture'] = {'name': 'lineage-conditioned neural fate and relative mass',
        'core_model': str(original.relative_to(ROOT)), 'emission_fix': 'maximal WT overlap at identical frozen quotas'}
    candidate.write_h5ad(directory / 'research.h5ad', compression='gzip')
    np.save(directory / 'DONOR_INDICES.npy', donors); np.save(directory / 'DONOR_STAGES.npy', np.ones(len(donors), int))
    old_result = json.loads((original / 'RESULT.json').read_text())
    result = dict(old_result, sha256=sha(directory / 'research.h5ad'), WT_carrier_sha256=sha(directory / 'WT_CARRIER.h5ad'),
                  core_result=str((original / 'RESULT.json').relative_to(ROOT)), model_refit=False,
                  original_rows_retained=retained, minimal_replaced_rows=len(parent) - retained,
                  frozen_model_and_state_probabilities_unchanged=True)
    dump(directory / 'RESULT.json', result)
    dump(directory / 'EMISSION_FIX.json', {'old_unique_WT_donors': len(set(np.load(original / 'DONOR_INDICES.npy'))),
          'new_unique_WT_donors': retained, 'minimum_replacement': len(parent) - retained,
          'state_quotas_identical': True, 'old_artifact_preserved': True, 'scientific_claim_not_changed': True,
          'old_candidate': 'v0067', 'old_status': 'INVALIDATED_UNSUBMITTED',
          'reason': 'with-replacement redraw of entire upweighted states creates unnecessary within-state sampling noise'})
    old_receipt = json.loads((original / 'REGISTRATION.json').read_text())
    with (ROOT / 'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = ROOT / 'submissions/INDEX.tsv'
        with path.open() as f:
            reader = csv.DictReader(f, delimiter='\t'); fields, rows = reader.fieldnames, list(reader)
        for r in rows:
            if r['board'] == 'T3:gata4' and r['version'] == old_receipt['candidate']['version']:
                assert r['sha256'] == old_receipt['candidate']['sha256'] and not r['server_score']
                r['score_status'] = 'invalidated_unsubmitted'
                r['notes'] += '; WITHDRAWN_NO_UPLOAD: excess WT resampling noise; b_fate_mass_emit2 repairs emission without refitting'
        output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
        tmp = path.with_suffix('.tsv.tmp'); tmp.write_text(output.getvalue()); tmp.replace(path)
    print('EMISSION_FIXED', retained, len(parent) - retained, flush=True)


if __name__ == '__main__': run()
