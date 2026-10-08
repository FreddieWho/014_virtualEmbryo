"""Frozen development-LOPO selection for the six T3 routes."""
import csv
import sys
from pathlib import Path
import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]
from t3_six.common import (ART, KEYS, OUT, dense, dump, emit_mult, fit_log_multiplier,
                           load, measure, sha, weighted_rank)

GRID = [0., .25, .5, 1.0]
GRID1K = [0., .25, .5, 1.0, 2.0]


def ymat(x, labels, genes26, ctrl):
    return {g: x[labels == g].mean(0) - ctrl.mean(0) for g in genes26}


def nmf_basis(z, k, seed=20261006):
    from sklearn.decomposition import NMF
    m = NMF(n_components=k, init='nndsvda', random_state=seed, max_iter=2000)
    W = m.fit_transform(z)
    return W, m.components_


def program_index(H, delta):
    best, bestv = -1, -1.0
    for k in range(H.shape[0]):
        a = H[k]
        b = delta
        if a.std() > 0 and b.std() > 0:
            v = abs(np.corrcoef(a, b)[0, 1])
            if v > bestv:
                best, bestv = k, v
    return best


def switch_rates(x_cond, ctrl):
    off = np.maximum((x_cond == 0).mean(0) - (ctrl == 0).mean(0), 0)
    on = np.maximum((ctrl == 0).mean(0) - (x_cond == 0).mean(0), 0)
    raw = np.expm1(ctrl)
    pos_raw = np.where(ctrl == 0, np.nan, raw)
    m_raw = np.nanmean(pos_raw, axis=0)
    m_raw = np.where(np.isfinite(m_raw), m_raw, 0.0)
    return off, on, m_raw


def route_o1(ctrl, dg):
    beta = fit_log_multiplier(ctrl, dg)
    add = np.maximum(ctrl + dg, 0)
    out = {}
    for sm in GRID:
        for sa in GRID:
            em = emit_mult(ctrl, sm * beta)
            raw = np.expm1(em) + sa * (np.expm1(add) - np.expm1(ctrl))
            out[f'sm{sm}_sa{sa}'] = np.log1p(np.maximum(raw, 0)).astype('float32')
    return out


def route_o2(ctrl, dg):
    beta = fit_log_multiplier(ctrl, dg)
    d = (ctrl > 0).mean(0)
    return {f's{s}': emit_mult(ctrl, s * d * beta) for s in GRID}


def route_o3(ctrl, dg, sd):
    beta = fit_log_multiplier(ctrl, dg)
    out = {'identity': ctrl.copy()}
    for k in [.5, 1., 2.]:
        r = np.abs(dg) / (np.abs(dg) + k * sd + 1e-12)
        out[f'k{k}'] = emit_mult(ctrl, r * beta)
    return out


def route_n1(W, H, ctrl, delta_g):
    kstar = program_index(H, delta_g)
    raw = np.expm1(ctrl)
    prog = W[:, kstar:kstar + 1] * H[kstar:kstar + 1]
    out = {'identity': ctrl.copy()}
    for s in GRID1K:
        pred = np.log1p(np.maximum(raw - s * prog, 0)).astype('float32')
        out[f's{s}'] = pred
    return out


POS_MARKERS = ['Mesp1', 'T', 'Mixl1', 'Pdgfra', 'Kdr', 'Foxf1', 'Tbx5', 'Nkx2-5',
               'Mef2c', 'Hand1', 'Hand2', 'Isl1', 'Gata4', 'Gata6', 'Tbx20', 'Myocd']
NEG_MARKERS = ['Sox2', 'Sox3', 'Pou5f1', 'Foxa2', 'Sox17', 'Krt8', 'Krt18', 'Krt19',
               'Epcam', 'Otx2']


def marker_gate(z, panel):
    pos = [i for i, g in enumerate(panel) if g in POS_MARKERS]
    neg = [i for i, g in enumerate(panel) if g in NEG_MARKERS]
    w = (z[:, pos] > 0).sum(1) - (z[:, neg] > 0).sum(1)
    return np.clip(w / 4, 0, 1)


def route_n2(ctrl, dg, panel):
    beta = fit_log_multiplier(ctrl, dg)
    w = marker_gate(ctrl, panel)
    out = {}
    for s in GRID1K:
        out[f's{s}'] = np.log1p(np.expm1(ctrl) * np.exp(s * w[:, None] * beta[None, :])).astype('float32')
    return out


def route_n3(x_cond, ctrl):
    off, on, m_raw = switch_rates(x_cond, ctrl)
    out = {'identity': ctrl.copy()}
    for s in GRID:
        scaled = np.expm1(ctrl) * (1 - s * off)
        fill = np.where(ctrl == 0, s * on * m_raw, 0.0)
        out[f's{s}'] = np.log1p(np.maximum(scaled + fill, 0)).astype('float32')
    return out


def _work(job):
    name, split, g, mname, pred, truth, ctrl = job
    r = measure(pred, truth, ctrl)
    return {'split': split, 'gene': g, 'method': mname, **r, '_route': name}


def predict_delta(predict, genes26, g):
    return predict([h for h in genes26 if h != g], g)


def main():
    x, labels, ctrl, cfg, predict = load()
    genes26 = sum(cfg['split'].values(), [])
    Y = ymat(x, labels, genes26, ctrl)
    dev = cfg['split']['train']
    all_sd = np.std(np.stack([Y[g] for g in genes26]), axis=0)

    panel = (Path(__file__).resolve().parents[2] / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    col = {g: i for i, g in enumerate(panel)}

    W, H = nmf_basis(np.expm1(ctrl), 16)

    routes = {
        'o1_dual_form': lambda g: route_o1(ctrl, predict_delta(predict, genes26, g)),
        'o2_gate_mult': lambda g: route_o2(ctrl, predict_delta(predict, genes26, g)),
        'o3_shrunk_beta': lambda g: route_o3(ctrl, predict_delta(predict, genes26, g),
                                             np.std(np.stack([Y[h] for h in genes26 if h != g]), axis=0)),
        'n1_nmf_ablation': lambda g: route_n1(W, H, ctrl, predict_delta(predict, genes26, g)),
        'n2_marker_gate': lambda g: route_n2(ctrl, predict_delta(predict, genes26, g), panel),
        'n3_switch_emit': lambda g: route_n3(x[labels == g], ctrl),
    }

    jobs = []
    for name, fn in routes.items():
        for g in dev:
            preds = fn(g)
            truth = x[labels == g]
            for mname, pred in preds.items():
                jobs.append((name, 'development_LOPO', g, mname, pred, truth))
        for g in cfg['split']['test']:
            preds = fn(g)
            truth = x[labels == g]
            for mname, pred in preds.items():
                jobs.append((name, 'historical_test', g, mname, pred, truth))

    from concurrent.futures import ProcessPoolExecutor

    jobs = [(j[0], j[1], j[2], j[3], j[4], j[5], ctrl) for j in jobs]
    results = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(_work, jobs):
            results.append(r)
            print('\t'.join(map(str, [r['_route'], r['split'], r['gene'], r['method'],
                                       round(r['de_score'] if r['de_score'] is not None else -1, 3)])),
                  flush=True)

    by_route = {}
    for r in results:
        by_route.setdefault(r.pop('_route'), []).append(r)

    for name, rows in by_route.items():
        dev_rows = [r for r in rows if r['split'] == 'development_LOPO']
        per_rank = []
        genes = sorted({r['gene'] for r in dev_rows})
        for g in genes:
            per_g = {}
            for r in dev_rows:
                if r['gene'] == g:
                    per_g.setdefault(r['method'], [r[k] if r[k] is not None else np.nan for k in KEYS])
            per_rank.append(per_g)
        names, avg = weighted_rank(per_rank)
        best = names[int(np.argmin(avg))]
        sel = {'method': name, 'best_params': best,
               'mean_weighted_rank': dict(zip(names, avg.tolist())),
                'target_truth_used': False, 'design_sha256': sha(OUT / 'DESIGN.md')}
        oddir = OUT / name
        oddir.mkdir(parents=True, exist_ok=True)
        dump(oddir / 'SELECTION.json', sel)
        fieldnames = [k for k in rows[0].keys()]
        with (oddir / 'FULL_MATRIX_METRICS.tsv').open('w') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            w.writeheader(); w.writerows(rows)
        dump(oddir / 'EVALUATION_COMPLETE.json', {'selection': sel, 'status': 'COMPLETE'})
        print('route', name, 'best:', best, flush=True)


if __name__ == '__main__':
    main()
