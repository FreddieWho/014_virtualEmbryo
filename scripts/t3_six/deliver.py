"""Deliver one immutable candidate per selected T3 six-route transform."""
import csv, fcntl, hashlib, json, re, sys
from pathlib import Path
import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'docs/batch3/interfaces')]
from t3_six.common import (ART, OUT, dense, dump, emit_mult, fit_log_multiplier,
                           load, sha, weighted_rank)
from virtual_embryo_tools.contract_io import validate_h5ad_contract

def route_emit(name, params, base, delta4, beta4, sd4, aux):
    if name == 'o1_dual_form':
        sm = float(params.split('_')[0].replace('sm', ''))
        sa = float(params.split('_')[1].replace('sa', ''))
        em = emit_mult(base, sm * beta4)
        add = np.maximum(base + delta4, 0)
        raw = np.expm1(em) + sa * (np.expm1(add) - np.expm1(base))
        return np.log1p(np.maximum(raw, 0)).astype('float32')
    if name == 'o2_gate_mult':
        s = float(params[1:])
        p = aux['hurdle_prob']
        cols = aux['hurdle_cols']
        delta = np.zeros(base.shape)
        delta[:, cols] = s * p * beta4[cols][None, :]
        return np.log1p(np.expm1(base) * np.exp(delta)).astype('float32')
    if name == 'o3_shrunk_beta':
        k = float(params[1:])
        r = np.abs(delta4) / (np.abs(delta4) + k * sd4 + 1e-12)
        return emit_mult(base, r * beta4)
    if name == 'n1_nmf_ablation':
        s = float(params[1:])
        W, H = aux['nmf']
        return np.log1p(np.maximum(np.expm1(base) - s * (W[:, aux['n1_kstar']:aux['n1_kstar'] + 1] * H[aux['n1_kstar']:aux['n1_kstar'] + 1]), 0)).astype('float32')
    if name == 'n2_marker_gate':
        s = float(params[1:])
        w = aux['marker_w']
        return np.log1p(np.expm1(base) * np.exp(s * w[:, None] * beta4[None, :])).astype('float32')
    if name == 'n3_switch_emit':
        s = float(params[1:])
        off, on, m_raw = aux['switch']
        scaled = np.expm1(base) * (1 - s * off)
        fill = np.where(base == 0, s * on * m_raw, 0.0)
        return np.log1p(np.maximum(scaled + fill, 0)).astype('float32')
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

    # Embryo-side auxilaries
    wt = ad.read_h5ad(ROOT / 'data/E8.75.h5ad')
    panel = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    gi = panel.index('Gata4')
    with (ROOT / 'data/MANIFEST.tsv').open() as f:
        mcr = next(r for r in csv.DictReader(f, delimiter='\t') if r['path'] == 'data/E8.75.h5ad')
    assert sha(ROOT / 'data/E8.75.h5ad') == mcr['sha256']
    parent_meta = ad.read_h5ad(ROOT / 'submissions/candidates/T3_gata4/v0048_next_n2hurdle/submission.h5ad', backed='r')
    parent_rows = parent_meta.obs_names
    x_wt = dense(wt[:, panel].X)[wt.obs_names.get_indexer(parent_rows)]
    assert np.isfinite(x_wt).all()

    # v0048 base & hurdle probability gate
    parent_v48 = ad.read_h5ad(ROOT / 'submissions/candidates/T3_gata4/v0048_next_n2hurdle/submission.h5ad')
    base = dense(parent_v48.X)
    assert base[:, gi].sum() == 0

    # marker gate on embryo WT rows
    sys.path[:0] = [str(ROOT / 'scripts')]
    from t3_six.evaluate import marker_gate
    marker_w = marker_gate(x_wt, panel)

    # NMF for N1 on embryo WT
    from sklearn.decomposition import NMF
    m = NMF(n_components=16, init='nndsvda', random_state=20261006, max_iter=2000)
    W = m.fit_transform(np.expm1(x_wt))
    H = m.components_
    kstar = int(np.argmax([abs(np.corrcoef(H[k], delta4)[0, 1]) if H[k].std() > 0 and delta4.std() > 0 else 0.0 for k in range(H.shape[0])]))
    # switch rates from source Gata4 vs ctrl
    cond_da = None
    off, on, m_raw = None, None, None
    # Gata4 is not a source condition; use most GO-similar donor condition
    # (same trusted-donor rule as scripts/t3_autoresearch/retained_model.py).
    ep = ROOT / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    emb = np.load(ep)
    ei = {g: i for i, g in enumerate(emb['genes'])}
    sim = emb['embedding'] @ emb['embedding'][ei['Gata4']]
    donor = max((g for g in emb['genes'] if g in set(labels)), key=lambda g: sim[ei[g]])
    from t3_six.evaluate import switch_rates
    off, on, m_raw = switch_rates(x[labels == donor], ctrl)
    dump(OUT / 'n3_donor.json', {'donor_condition': donor, 'reason': 'Gata4 not a source condition; donor chosen by GO embedding similarity'})

    # hurdle probability for O2
    import pickle
    hp = ROOT / 'artifacts/t3_next/T3-FIVE-20260927-v2/n2hurdle/hurdle_model.pkl'
    with hp.open('rb') as fh:
        hmodel = pickle.load(fh)
    coords = np.asarray(wt.obsm['spatial_3D'])[:, :3].astype(float)[wt.obs_names.get_indexer(parent_rows)]
    import scripts.t3_next.routes_local as rl
    types = wt.obs.celltype.astype(str).to_numpy()[wt.obs_names.get_indexer(parent_rows)]
    a = x_wt[:, [gi]]
    feats = hmodel['encoder'].features(a, coords, types)
    prob = np.clip(hmodel['encoder'].model.predict(feats), 0, 1)

    aux = {'hurdle_prob': prob, 'hurdle_cols': np.asarray(hmodel['cols']), 'marker_w': marker_w, 'nmf': (W, H), 'n1_kstar': kstar,
           'switch': (off, on, m_raw)}

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

    routes = ['o1_dual_form', 'o2_gate_mult', 'o3_shrunk_beta', 'n1_nmf_ablation', 'n2_marker_gate', 'n3_switch_emit']
    with (ROOT / 'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for name in routes:
            sel_path = OUT / name / 'SELECTION.json'
            if not sel_path.exists():
                print('skip (no selection):', name); continue
            sel = json.loads(sel_path.read_text())
            params = sel['best_params']
            pred = route_emit(name, params, base, delta4, beta4, sd4, aux)
            pred[:, gi] = 0
            assert np.isfinite(pred).all() and (pred >= 0).all() and pred.shape == base.shape
            candidate = parent_v48.copy()
            candidate.X = pred
            candidate.uns['ve_contract'] = {'normalization': 'log_normalized',
                                            'source': f'v0048 base + t3_six {name} transform'}
            candidate.uns['t3_six'] = {'route': name, 'params': params, 'parent': 'v0048',
                                       'target_truth_used': False}
            ver = f'v{max(used) + 1:04d}'
            used.append(max(used) + 1)
            folder = ROOT / f'submissions/candidates/T3_gata4/{ver}_six_{name}'
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
            new.update(status='candidate', submission_group='T3-SIX-' + name.split('_')[0].upper(),
                       board='T3:gata4', version=ver, method=f'six_{name}',
                       path=str(path.relative_to(ROOT)), n_cells=str(pred.shape[0]), n_genes=str(pred.shape[1]),
                       seed='20261006', target_used='false', local_contract='pass',
                       sha256=sha(path), score_status='score_pending',
                       notes=f'parent=v0048; params={params}; source-LOPO selected; NOT_SUBMITTED/未评分; blocks_submission=false')
            with index.open('a') as f:
                csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n').writerow(new)
            print('delivered', ver, name, params, 'contract', contract['status'], flush=True)


if __name__ == '__main__':
    main()
