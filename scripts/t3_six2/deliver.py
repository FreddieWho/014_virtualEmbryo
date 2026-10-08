"""Deliver one immutable candidate per selected wave-2 t3_six2 transform."""
import csv, fcntl, json, pickle, re, sys
from pathlib import Path
import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'docs/batch3/interfaces')]
from t3_six.common import dense, dump, emit_mult, fit_log_multiplier, load, sha
from virtual_embryo_tools.contract_io import validate_h5ad_contract

OUT = ROOT / 'reports/t3_six_routes_20261007'
SEED = 20261006

LANE = {
    'o1_hnmf': 'hnmf', 'o2_pnmf': 'pnmf', 'o3_psb': 'psb',
    'n1_qtl': 'qtl', 'n2_dsign': 'dsign', 'n3_pswap': 'pswap',
}


def route_emit(name, params, base, beta4, sd4, aux):
    if name == 'o1_hnmf':
        W, H = aux['nmf']
        kp = aux['kplus']
        prog = W[:, kp:kp + 1] * H[kp:kp + 1]
        out_nmf = np.log1p(np.maximum(np.expm1(base) - 0.25 * prog, 0))
        blend = 0.5 * base + 0.5 * out_nmf
        return blend.astype('float32')
    if name == 'o2_pnmf':
        W, H = aux['nmf']
        kp = aux['kplus']
        prog = W[:, kp:kp + 1] * H[kp:kp + 1]
        p, cols = aux['hurdle_prob'], aux['hurdle_cols']
        gate = np.zeros(base.shape)
        gate[:, cols] = p
        raw = np.expm1(base) - 0.25 * gate * prog
        return np.log1p(np.maximum(raw, 0)).astype('float32')
    if name == 'o3_psb':
        p, cols = aux['hurdle_prob'], aux['hurdle_cols']
        r = np.abs(aux['delta4']) / (np.abs(aux['delta4']) + 2.0 * sd4 + 1e-12)
        delta = np.zeros(base.shape)
        delta[:, cols] = 0.5 * p * r[cols][None, :] * beta4[cols][None, :]
        return np.log1p(np.expm1(base) * np.exp(delta)).astype('float32')
    if name == 'n1_qtl':
        from t3_next.five_ops import quantile_response
        s = float(params[1:])
        return np.asarray(quantile_response(base, aux['ctrl'], aux['donor_ko'], s, np.log(2.)), dtype='float32')
    if name == 'n2_dsign':
        s = float(params[1:])
        gate = aux['sign_gate']
        return emit_mult(base, s * gate * beta4)
    if name == 'n3_pswap':
        s = float(params[1:])
        W, H = aux['nmf']
        kp, km = aux['kplus'], aux['kminus']
        prog_plus = W[:, kp:kp + 1] * H[kp:kp + 1]
        prog_minus = W[:, km:km + 1] * H[km:km + 1]
        ratio = prog_plus.sum(1) / np.maximum(prog_minus.sum(1), 1e-12)
        raw = np.expm1(base) - s * prog_plus + s * ratio[:, None] * prog_minus
        return np.log1p(np.maximum(raw, 0)).astype('float32')
    raise ValueError(name)


def main():
    x, labels, ctrl, cfg, predict = load()
    genes26 = sum(cfg['split'].values(), [])
    delta4 = predict(genes26, 'Gata4')
    model_response = np.load(ROOT / 'artifacts/t3_autoresearch_delivery_20261003/MODEL_RESPONSE.npy').reshape(-1)
    np.testing.assert_allclose(delta4, model_response, atol=1e-12, rtol=0)
    beta4 = fit_log_multiplier(ctrl, delta4)
    Y = {g: x[labels == g].mean(0) - ctrl.mean(0) for g in genes26}
    sd4 = np.std(np.stack([Y[g] for g in genes26]), axis=0)

    # GO donor for delivery (same rule as wave-1 n3_donor)
    provenance = json.loads((ROOT / 'artifacts/autoresearch/t3-20261002-v1/PROVENANCE.json').read_text())
    ep = ROOT / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert sha(ep) == provenance['embedding_sha256']
    emb = np.load(ep)
    ei = {g: i for i, g in enumerate(emb['genes'])}
    sims = {d: float(emb['embedding'][ei['Gata4']] @ emb['embedding'][ei[d]])
            for d in genes26 if d != 'Gata4'}
    donor = max(sims, key=sims.get)
    donor_ko = x[labels == donor]
    dump(OUT / 'donor.json', {'donor_condition': donor, 'rule': 'GO embedding argmax over 26 conditions'})

    # donor sign gate for N2
    donor_shift = donor_ko.mean(0, dtype=float) - ctrl.mean(0, dtype=float)
    sign_gate = (np.sign(donor_shift) == np.sign(delta4)).astype(float)

    # embryo side
    panel = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    gi = panel.index('Gata4')
    with (ROOT / 'data/MANIFEST.tsv').open() as f:
        mcr = next(r for r in csv.DictReader(f, delimiter='\t') if r['path'] == 'data/E8.75.h5ad')
    assert sha(ROOT / 'data/E8.75.h5ad') == mcr['sha256']
    wt = ad.read_h5ad(ROOT / 'data/E8.75.h5ad')
    parent_v48 = ad.read_h5ad(ROOT / 'submissions/candidates/T3_gata4/v0048_next_n2hurdle/submission.h5ad')
    base = dense(parent_v48.X)
    assert base[:, gi].sum() == 0
    rows_idx = wt.obs_names.get_indexer(parent_v48.obs_names)
    x_wt = dense(wt[:, panel].X)[rows_idx]
    assert np.isfinite(x_wt).all()

    # embryo NMF (wave-1 N1 recipe: K=16 seed 20261006 on expm1(x_wt))
    from sklearn.decomposition import NMF
    m = NMF(n_components=16, init='nndsvda', random_state=SEED, max_iter=2000)
    W = m.fit_transform(np.expm1(x_wt))
    H = m.components_
    def corr_max(v):
        cs = [abs(np.corrcoef(H[k], v)[0, 1]) if H[k].std() > 0 and v.std() > 0 else 0.0 for k in range(H.shape[0])]
        return int(np.argmax(cs))
    kplus = corr_max(delta4)
    cs_minus = [abs(np.corrcoef(H[k], -delta4)[0, 1]) if H[k].std() > 0 and delta4.std() > 0 else 0.0 for k in range(H.shape[0])]
    cs_minus[kplus] = -1.0
    kminus = int(np.argmax(cs_minus))

    # hurdle probability gate (wave-1 O2 delivery gate)
    hp = ROOT / 'artifacts/t3_next/T3-FIVE-20260927-v2/n2hurdle/hurdle_model.pkl'
    with hp.open('rb') as fh:
        hmodel = pickle.load(fh)
    coords = np.asarray(wt.obsm['spatial_3D'])[:, :3].astype(float)[rows_idx]
    types = wt.obs.celltype.astype(str).to_numpy()[rows_idx]
    feats = hmodel['encoder'].features(x_wt[:, [gi]], coords, types)
    prob = np.clip(hmodel['encoder'].model.predict(feats), 0, 1)

    aux = {'hurdle_prob': prob, 'hurdle_cols': np.asarray(hmodel['cols']), 'nmf': (W, H),
           'kplus': kplus, 'kminus': kminus, 'ctrl': ctrl, 'donor_ko': donor_ko,
           'sign_gate': sign_gate, 'delta4': delta4}

    index = ROOT / 'submissions/INDEX.tsv'
    with index.open() as f:
        reader = csv.DictReader(f, delimiter='\t'); fields = reader.fieldnames; rows = list(reader)
    t3 = [r for r in rows if r['board'] == 'T3:gata4']
    v48 = next(r for r in t3 if r['version'] == 'v0048')
    parent_path = ROOT / v48['path']
    assert sha(parent_path) == v48['sha256']
    used = [int(r['version'][1:]) for r in t3]
    for p in (ROOT / 'submissions/candidates/T3_gata4').iterdir():
        m2 = re.match(r'v(\d+)_', p.name)
        if m2:
            used.append(int(m2.group(1)))

    routes = ['o1_hnmf', 'o2_pnmf', 'o3_psb', 'n1_qtl', 'n2_dsign', 'n3_pswap']
    with (ROOT / 'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for name in routes:
            sel_path = OUT / name / 'SELECTION.json'
            if not sel_path.exists():
                print('skip (no selection):', name); continue
            sel = json.loads(sel_path.read_text())
            params = sel['best_params']
            if params == 'identity':
                dump(OUT / name / 'SOURCE_CLOSED.json',
                     {'status': 'CLOSED_NO_POSITIVE_SIGNAL',
                      'reason': 'identity ranked best in frozen source LOPO; all strengths worse; no candidate delivered',
                      'mean_weighted_rank': sel['mean_weighted_rank']})
                print('skip (identity best, closed at source):', name); continue
            pred = route_emit(name, params, base, beta4, sd4, aux)
            pred[:, gi] = 0
            assert np.isfinite(pred).all() and (pred >= 0).all() and pred.shape == base.shape
            if np.array_equal(pred, base):
                dump(OUT / name / 'SOURCE_CLOSED.json',
                     {'status': 'CLOSED_NO_OP', 'reason': 'emission identical to parent; no candidate delivered'})
                print('skip (no-op emission):', name); continue
            candidate = parent_v48.copy()
            candidate.X = pred
            candidate.uns['ve_contract'] = {'normalization': 'log_normalized',
                                            'source': f'v0048 base + t3_six2 {name} transform'}
            candidate.uns['t3_six2'] = {'route': name, 'params': params, 'parent': 'v0048',
                                        'target_truth_used': False, 'donor': donor}
            ver = f'v{max(used) + 1:04d}'
            used.append(max(used) + 1)
            folder = ROOT / f'submissions/candidates/T3_gata4/{ver}_six2_{name}'
            folder.mkdir(exist_ok=False)
            path = folder / 'submission.h5ad'
            candidate.write_h5ad(path, compression='gzip')
            contract = validate_h5ad_contract(path, task='T3', board='gata4',
                                              scorer_lock=ROOT / 'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',
                                              parent_path=parent_path, parent_sha256=v48['sha256'])
            dump(folder / 'contract.json', contract)
            if contract['status'] != 'PASS':
                raise ValueError('contract fail ' + name)
            new = dict.fromkeys(fields, '')
            new.update(status='candidate', submission_group='T3-SIX2-' + name.split('_')[0].upper(),
                       board='T3:gata4', version=ver, method=f'six2_{name}',
                       path=str(path.relative_to(ROOT)), n_cells=str(pred.shape[0]), n_genes=str(pred.shape[1]),
                       seed=str(SEED), target_used='false', local_contract='pass',
                       sha256=sha(path), score_status='score_pending',
                       notes=f'parent=v0048; params={params}; wave2; NOT_SUBMITTED/未评分; blocks_submission=false')
            with index.open('a') as f:
                csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n').writerow(new)
            print('delivered', ver, name, params, 'contract', contract['status'], flush=True)


if __name__ == '__main__':
    main()
