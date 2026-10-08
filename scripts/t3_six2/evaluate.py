"""Wave-2 six-route frozen source-LOPO harness (t3_six2)."""
import csv
import sys
from pathlib import Path
import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]
from t3_six.common import (KEYS, dense, dump, emit_mult, fit_log_multiplier,
                           load, measure, sha, weighted_rank)

OUT = Path(__file__).resolve().parents[2] / 'reports/t3_six_routes_20261007'
GRID = [.25, .5, 1.0]
SEED = 20261006


def nmf_basis(z, k=16, seed=SEED):
    from sklearn.decomposition import NMF
    m = NMF(n_components=k, init='nndsvda', random_state=seed, max_iter=2000)
    W = m.fit_transform(z)
    return W, m.components_


def program_pair(H, delta):
    def corr(v):
        return [abs(np.corrcoef(H[k], v)[0, 1]) if H[k].std() > 0 and v.std() > 0 else 0.0
                for k in range(H.shape[0])]
    kplus = int(np.argmax(corr(delta)))
    cminus = corr(-delta)
    cminus[kplus] = -1.0
    kminus = int(np.argmax(cminus))
    return kplus, kminus


def donor_for(emb, ei, genes, query, exclude):
    sims = {d: float(emb['embedding'][ei[query]] @ emb['embedding'][ei[d]])
            for d in genes if d != query and d not in exclude and d != 'Gata4'}
    return max(sims, key=sims.get)


def route_o1(ctrl, dg, add_analog, nmf_analog):
    blend = 0.5 * add_analog + 0.5 * nmf_analog
    return {'blend': blend.astype('float32')}


def route_o2(ctrl, dg, W, H, kplus, density):
    prog = W[:, kplus:kplus + 1] * H[kplus:kplus + 1]
    raw = np.expm1(ctrl) - 0.25 * density[None, :] * prog
    return {'pnmf': np.log1p(np.maximum(raw, 0)).astype('float32')}


def route_o3(ctrl, dg, beta, sd, density):
    r = np.abs(dg) / (np.abs(dg) + 2.0 * sd + 1e-12)
    delta = 0.5 * density[None, :] * r[None, :] * beta[None, :]
    return {'psb': np.log1p(np.expm1(ctrl) * np.exp(delta)).astype('float32')}


def route_n1(ctrl, donor_ko):
    from t3_next.five_ops import quantile_response
    out = {'identity': ctrl.copy()}
    for s in GRID:
        out[f'q{s}'] = np.asarray(quantile_response(ctrl, ctrl, donor_ko, s, np.log(2.)), dtype='float32')
    return out


def route_n2(ctrl, dg, beta, donor_ko):
    donor_shift = donor_ko.mean(0, dtype=float) - ctrl.mean(0, dtype=float)
    gate = (np.sign(donor_shift) == np.sign(dg)).astype(float)
    out = {'identity': ctrl.copy()}
    for s in GRID:
        out[f'g{s}'] = emit_mult(ctrl, s * gate * beta)
    return out


def route_n3(ctrl, W, H, kplus, kminus):
    prog_plus = W[:, kplus:kplus + 1] * H[kplus:kplus + 1]
    prog_minus = W[:, kminus:kminus + 1] * H[kminus:kminus + 1]
    ratio = prog_plus.sum(1) / np.maximum(prog_minus.sum(1), 1e-12)
    out = {'identity': ctrl.copy()}
    for s in GRID:
        raw = np.expm1(ctrl) - s * prog_plus + s * ratio[:, None] * prog_minus
        out[f'p{s}'] = np.log1p(np.maximum(raw, 0)).astype('float32')
    return out


def _work(job):
    name, split, g, mname, pred, truth, ctrl = job
    r = measure(pred, truth, ctrl)
    return {'split': split, 'gene': g, 'method': mname, **r, '_route': name}


def main():
    x, labels, ctrl, cfg, predict = load()
    genes26 = sum(cfg['split'].values(), [])
    dev = cfg['split']['train']
    Y = {g: x[labels == g].mean(0) - ctrl.mean(0) for g in genes26}
    all_sd = np.std(np.stack([Y[g] for g in genes26]), axis=0)
    density = (ctrl > 0).mean(0)

    import json
    provenance = json.loads((Path(__file__).resolve().parents[2] /
                             'artifacts/autoresearch/t3-20261002-v1/PROVENANCE.json').read_text())
    ep = Path(__file__).resolve().parents[2] / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert sha(ep) == provenance['embedding_sha256']
    emb = np.load(ep)
    ei = {g: i for i, g in enumerate(emb['genes'])}

    W, H = nmf_basis(np.expm1(ctrl))

    routes = {}
    for g in dev:
        dg = predict([h for h in genes26 if h != g], g)
        beta = fit_log_multiplier(ctrl, dg)
        kplus, kminus = program_pair(H, dg)
        donor = donor_for(emb, ei, genes26, g, exclude=())
        donor_ko = x[labels == donor]
        add_analog = np.maximum(ctrl + dg, 0)
        nmf_raw = np.expm1(ctrl) - 0.25 * (W[:, kplus:kplus + 1] * H[kplus:kplus + 1])
        nmf_analog = np.log1p(np.maximum(nmf_raw, 0))
        routes.setdefault('o1_hnmf', []).append((g, route_o1(ctrl, dg, add_analog, nmf_analog)))
        routes.setdefault('o2_pnmf', []).append((g, route_o2(ctrl, dg, W, H, kplus, density)))
        routes.setdefault('o3_psb', []).append((g, route_o3(ctrl, dg, beta, all_sd, density)))
        routes.setdefault('n1_qtl', []).append((g, route_n1(ctrl, donor_ko)))
        routes.setdefault('n2_dsign', []).append((g, route_n2(ctrl, dg, beta, donor_ko)))
        routes.setdefault('n3_pswap', []).append((g, route_n3(ctrl, W, H, kplus, kminus)))

    jobs = []
    for name, per_g in routes.items():
        for g, preds in per_g:
            truth = x[labels == g]
            for mname, pred in preds.items():
                jobs.append((name, 'development_LOPO', g, mname, pred, truth, ctrl))
    for g in cfg['split']['test']:
        dg = predict([h for h in genes26 if h != g], g)
        beta = fit_log_multiplier(ctrl, dg)
        kplus, kminus = program_pair(H, dg)
        donor = donor_for(emb, ei, genes26, g, exclude=())
        donor_ko = x[labels == donor]
        add_analog = np.maximum(ctrl + dg, 0)
        nmf_raw = np.expm1(ctrl) - 0.25 * (W[:, kplus:kplus + 1] * H[kplus:kplus + 1])
        nmf_analog = np.log1p(np.maximum(nmf_raw, 0))
        for mname, pred in route_o1(ctrl, dg, add_analog, nmf_analog).items():
            jobs.append(('o1_hnmf', 'historical_test', g, mname, pred, x[labels == g], ctrl))
        for mname, pred in route_o2(ctrl, dg, W, H, kplus, density).items():
            jobs.append(('o2_pnmf', 'historical_test', g, mname, pred, x[labels == g], ctrl))
        for mname, pred in route_o3(ctrl, dg, beta, all_sd, density).items():
            jobs.append(('o3_psb', 'historical_test', g, mname, pred, x[labels == g], ctrl))
        for mname, pred in route_n1(ctrl, donor_ko).items():
            jobs.append(('n1_qtl', 'historical_test', g, mname, pred, x[labels == g], ctrl))
        for mname, pred in route_n2(ctrl, dg, beta, donor_ko).items():
            jobs.append(('n2_dsign', 'historical_test', g, mname, pred, x[labels == g], ctrl))
        for mname, pred in route_n3(ctrl, W, H, kplus, kminus).items():
            jobs.append(('n3_pswap', 'historical_test', g, mname, pred, x[labels == g], ctrl))

    from concurrent.futures import ProcessPoolExecutor
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(_work, jobs):
            results.append(r)
            print('\t'.join(map(str, [r['_route'], r['split'], r['gene'], r['method'],
                                      round(r['de_score'] if r['de_score'] is not None else -1, 3)])), flush=True)

    by_route = {}
    for r in results:
        by_route.setdefault(r.pop('_route'), []).append(r)

    for name, rows in by_route.items():
        dev_rows = [r for r in rows if r['split'] == 'development_LOPO']
        per_rank = []
        for g in sorted({r['gene'] for r in dev_rows}):
            per_g = {}
            for r in dev_rows:
                if r['gene'] == g:
                    per_g.setdefault(r['method'], [r[k] if r[k] is not None else np.nan for k in KEYS])
            per_rank.append(per_g)
        names, avg = weighted_rank(per_rank)
        best = names[int(np.argmin(avg))]
        sel = {'method': name, 'best_params': best,
               'mean_weighted_rank': dict(zip(names, avg.tolist())),
               'diagnosis_only': name in ('o1_hnmf', 'o2_pnmf', 'o3_psb'),
               'target_truth_used': False, 'design_sha256': sha(OUT / 'DESIGN.md')}
        oddir = OUT / name
        oddir.mkdir(parents=True, exist_ok=True)
        dump(oddir / 'SELECTION.json', sel)
        fieldnames = list(rows[0].keys())
        with (oddir / 'FULL_MATRIX_METRICS.tsv').open('w') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            w.writeheader(); w.writerows(rows)
        dump(oddir / 'EVALUATION_COMPLETE.json', {'selection': sel, 'status': 'COMPLETE'})
        print('route', name, 'best:', best, flush=True)


if __name__ == '__main__':
    main()
