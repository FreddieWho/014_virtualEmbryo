"""Read-only acceptance: replay A, audit B quotas/donor vectors, locks and package."""
import json
import csv
import zipfile
import hashlib
import numpy as np
import torch
import anndata as ad
import joblib
from scripts.t3_priority_six.common import ROOT, sha, dump, dense
from scripts.t3_arch_two.flow import RUN, ResidualField, integrate
from scripts.t3_arch_two.fate import FateMass, quotas, lineage, bins, activity_values, predict


def main():
    torch.set_num_threads(8)
    checked = {}
    for name in ['A_INPUT_LOCK.json', 'B_INPUT_LOCK.json']:
        lock = json.loads((RUN / name).read_text())
        for path, expected in lock['sha256'].items():
            assert sha(ROOT / path) == expected, path
        checked[name] = 'PASS_UNCHANGED'
    arun = RUN / 'a_residual_flow'
    cfg = json.loads((RUN / 'CONFIG.json').read_text())
    saved = torch.load(arun / 'final_fit/model.pt', weights_only=False)
    z = np.load(ROOT / cfg['GO_embedding']); embedding = z['embedding'][np.flatnonzero(z['genes'] == 'Gata4')[0]]
    model = ResidualField(500, len(embedding), cfg['flow']['hidden']); model.load_state_dict(saved['state'])
    arrays = np.load(arun / 'TARGET_ARRAYS.npz')
    replay = integrate(model, arrays['factual'], arrays['center'], arrays['scale'], embedding, cfg['flow']['integration_steps'])
    panel = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    replay[:, panel.index('Gata4')] = 0
    np.testing.assert_allclose(replay, arrays['prediction'], atol=2e-6, rtol=0)
    checked['A_full_7449x500_model_replay'] = 'PASS'
    brun = RUN / 'b_fate_mass_emit2'; original = RUN / 'b_fate_mass'
    state = np.load(original / 'STATE_PREDICTION.npz')
    donors = np.load(brun / 'DONOR_INDICES.npy')
    middle = ad.read_h5ad(ROOT / 'data/E8.75.h5ad')[:, panel].copy()
    population = joblib.load(original / 'population_model.joblib')
    frame = population['chart']
    x = dense(middle.X).astype(np.float32)
    zz = frame['pca'].transform((x[:, frame['chosen']] - frame['mu']) / frame['sd']) / frame['zscale']
    labs = np.full(len(x), -1, int)
    groups = np.array([lineage(s) for s in middle.obs.celltype.astype(str)])
    for group in set(groups):
        km, offset = frame['fits'][group]; labs[groups == group] = km.predict(zz[groups == group]) + offset
    early = ad.read_h5ad(ROOT / 'data/E8.0.h5ad')[:, panel].copy()
    ex = dense(early.X).astype(np.float32)
    ez = frame['pca'].transform((ex[:, frame['chosen']] - frame['mu']) / frame['sd']) / frame['zscale']
    eg = np.array([lineage(s) for s in early.obs.celltype.astype(str)])
    el = np.full(len(ex), -1, int)
    for group in set(eg):
        km, offset = frame['fits'][group]; el[eg == group] = km.predict(ez[eg == group]) + offset
    source_bins = bins(ex, ez, el, activity_values(ex, population['activity']), 8., 64)
    records = []
    for group in sorted(set(frame['center_groups'])):
        destination = np.array([s for s in range(64) if frame['center_groups'][s] == group and np.any(labs == s)])
        if group == 'unknown' or not len(destination): continue
        mask = np.zeros(64, bool); mask[destination] = True
        records.extend(dict(r, duration=.75, destination_mask=mask) for r in source_bins if frame['center_groups'][r['state']] == group)
    fitted = FateMass(26, 64, population['cfg']['hidden'], population['cfg']['growth_bound'])
    fitted.load_state_dict(torch.load(original / 'model.pt', weights_only=True))
    pf, mf = predict(fitted, records); pk, mk = predict(fitted, records, knockout=True)
    reconstructed = state['WT'].copy()
    for group in sorted(set(frame['center_groups'])):
        ix = [i for i, r in enumerate(records) if frame['center_groups'][r['state']] == group]
        fraction = state['WT'][frame['center_groups'] == group].sum()
        if not ix or not fraction: continue
        weights = np.array([records[i]['count'] for i in ix], float); weights /= weights.sum()
        factual = (pf[ix] * (weights * mf[ix])[:, None]).sum(0)
        counter = (pk[ix] * (weights * mk[ix])[:, None]).sum(0)
        reconstructed += fraction * (counter - factual) / factual.sum()
    reconstructed = np.maximum(reconstructed, 0); reconstructed /= reconstructed.sum()
    np.testing.assert_allclose(reconstructed, state['prediction'], atol=2e-6, rtol=0)
    checked['B_full_neural_model_to_population_replay'] = 'PASS'
    rows = donors - 31671
    assert (rows >= 0).all() and (rows < len(middle)).all()
    np.testing.assert_array_equal(np.bincount(labs[rows], minlength=64), quotas(state['prediction'], 7449))
    reg = json.loads((brun / 'REGISTRATION.json').read_text()); candidate = ad.read_h5ad(ROOT / reg['candidate']['path'])
    full_donors = x[rows].copy(); full_donors[:, panel.index('Gata4')] = 0
    np.testing.assert_array_equal(candidate.X, full_donors)
    np.testing.assert_array_equal(candidate.obsm['spatial_3D'], np.asarray(middle.obsm['spatial_3D'])[rows])
    checked['B_full_quota_and_whole_vector_donor_trace'] = 'PASS'
    interval_model = FateMass(5, 4, 12, 3.)
    p, m = interval_model(torch.randn(3, 5), torch.tensor([0, 1, 3]), torch.ones(3, 4, dtype=torch.bool), torch.zeros(3))
    np.testing.assert_array_equal(p.detach().numpy(), np.eye(4)[[0, 1, 3]])
    np.testing.assert_array_equal(m.detach().numpy(), np.zeros(3))
    checked['B_zero_time_identity'] = 'PASS'
    with (ROOT / 'submissions/INDEX.tsv').open() as f:
        index = {(r['board'], r['version']): r for r in csv.DictReader(f, delimiter='\t')}
    receipt = json.loads((RUN / 'DELIVERY.json').read_text())
    assert sha(ROOT / receipt['zip']) == receipt['sha256']
    with zipfile.ZipFile(ROOT / receipt['zip']) as archive:
        assert archive.testzip() is None
        for member in receipt['members']:
            assert hashlib.sha256(archive.read(member['filename'])).hexdigest() == member['sha256']
    for lane in ['a_residual_flow', 'b_fate_mass_emit2']:
        r = json.loads((RUN / lane / 'REGISTRATION.json').read_text())
        row = index['T3:gata4', r['candidate']['version']]
        assert row['sha256'] == sha(ROOT / row['path'])
        assert row['score_status'] == 'score_pending' and not row['server_score']
        assert json.loads((ROOT / r['contract']).read_text())['status'] == 'PASS'
    assert index['T3:gata4', 'v0067']['score_status'] == 'invalidated_unsubmitted'
    checked['INDEX_contract_CRC_SHA256_and_withdrawal'] = 'PASS'
    dump(RUN / 'ACCEPTANCE.json', {'status': 'PASS_ENGINEERING_ONLY', 'checks': checked,
           'Gata4_truth_validation': 'NOT_RUN_NO_TRUTH', 'portal_operations': 'NOT_RUN',
           'scientific_qualification': 'NOT_ESTABLISHED; A source and B WT baseline failures retained'})
    print('ACCEPTANCE_PASS', checked)


if __name__ == '__main__': main()
