"""Pseudobulk-first T1 mean extrapolation. Frozen alphas, no result-driven retuning."""
from __future__ import annotations
import csv, fcntl, hashlib, json, sys, time
from pathlib import Path
import anndata as ad
import numpy as np
import pandas as pd

ROOT = Path('/home/huyudi/014_virtualEmbryo')
sys.path.insert(0, str(ROOT / 'third_party' / 'veckit'))
sys.path.insert(0, str(ROOT / 'docs' / 'batch3' / 'interfaces'))
from common.core_metrics import _signed_overlap, de_direction, de_genes, pseudobulk
from virtual_embryo_tools.contract_io import validate_h5ad_contract, write_candidate_from_parent

CONFIG = ROOT / 'configs/t1_pbmean/design_20260929.json'
LOCK = ROOT / 'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json'
RUN = ROOT / 'artifacts/t1_pbmean/T1-PBMEAN-20260929-v1'
REGLOCK = ROOT / 'artifacts/t1_five/REGISTRATION.lock'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def dense_panel(path, genes):
    a = ad.read_h5ad(path)
    ix = a.var_names.get_indexer(genes)
    if (ix < 0).any() or not a.obs_names.is_unique:
        raise ValueError(f'source identity {path}')
    x = a.X[:, ix]
    x = np.asarray(x.toarray() if hasattr(x, 'toarray') else x, dtype=np.float32)
    if (x < 0).any() or not np.isfinite(x).all():
        raise ValueError(f'source values {path}')
    types = a.obs.celltype.astype(str).to_numpy()
    return x, types


def mean_of(x, idx=None):
    if idx is None:
        return x.mean(0)
    return x[idx].mean(0)


def type_means(x, types, idx, keys):
    sub_t = types[idx]
    sub_x = x[idx]
    out = {}
    for t in keys:
        m = sub_t == t
        if m.any():
            out[t] = sub_x[m].mean(0)
    return out


def mix_means(means, weights):
    acc = None
    wsum = 0.0
    for t, w in weights.items():
        if t not in means or w <= 0:
            continue
        acc = means[t] * w if acc is None else acc + means[t] * w
        wsum += w
    if acc is None or wsum <= 0:
        raise ValueError('empty mix')
    return acc / wsum


def spearman(a, b):
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def score_mean(pred_mean, ref_mean, up_t, dn_t, chance, true_x, ref_x):
    dp = pred_mean - ref_mean
    dt = pseudobulk(true_x) - ref_mean
    n_true = len(up_t) + len(dn_t)
    if n_true == 0 or np.std(dt) < 1e-12 or np.std(dp) < 1e-2 * np.std(dt):
        de = 0.0
        raw = 0.0
    else:
        raw, _ = _signed_overlap(dp, up_t, dn_t)
        de = float((raw - chance) / (1 - chance)) if chance < 1 else float('nan')
        raw = float(raw)
    pred = np.broadcast_to(pred_mean.astype(np.float32), (2, pred_mean.shape[0])).copy()
    direction = float(de_direction(pred, true_x, ref_x))
    return {'de_score': de, 'de_raw': raw, 'de_chance': float(chance), 'de_direction': direction, 'n_true': n_true}


def shift_to_mean(base, target_mean):
    current = base.mean(0)
    delta = target_mean - current
    shifted = base + delta
    neg = shifted < 0
    shifted = np.maximum(shifted, 0).astype(np.float32)
    achieved = shifted.mean(0)
    gap = achieved - target_mean
    return shifted, {
        'negative_fraction': float(neg.mean()),
        'genes_clipped': int(np.any(neg, axis=0).sum()),
        'mean_abs_gap': float(np.mean(np.abs(gap))),
        'max_abs_gap': float(np.max(np.abs(gap))),
    }


def main():
    started = time.time()
    if RUN.exists():
        raise FileExistsError(RUN)
    RUN.mkdir(parents=True)
    cfg = json.loads(CONFIG.read_text())
    (RUN / 'design.json').write_text(CONFIG.read_text())
    genes = (ROOT / 'data/gene_panel/T1__val.genes.txt').read_text().splitlines()
    splits = np.load(ROOT / cfg['split_source'])
    with (ROOT / 'submissions/INDEX.tsv').open() as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    parent_row = next(r for r in rows if r['board'] == 'T1:val' and r['version'] == cfg['parent'])
    parent_path = ROOT / parent_row['path']
    if sha(parent_path) != parent_row['sha256']:
        raise ValueError('parent drift')
    print('loading sources', flush=True)
    x85, t85 = dense_panel(ROOT / 'data/E8.5_RNA.h5ad', genes)
    x95, t95 = dense_panel(ROOT / 'data/E9.5_RNA.h5ad', genes)
    parent = ad.read_h5ad(parent_path)
    if list(parent.var_names) != genes or parent.n_obs != 5118:
        raise ValueError('parent alignment')
    base = np.asarray(parent.X.toarray() if hasattr(parent.X, 'toarray') else parent.X, dtype=np.float32)
    report_pred = ad.read_h5ad(ROOT / 'artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad')
    report_mean = pseudobulk(report_pred.X)
    tr85, tr95 = splits['train85'], splits['train95']
    te85, te95 = splits['report85'], splits['report95']
    true_report = x95[te95]
    ref_report = x85[te85]

    def predict(alpha, scheme, fit=True):
        i85 = tr85 if fit else np.arange(len(t85))
        i95 = tr95 if fit else np.arange(len(t95))
        if scheme == 'A_global':
            d = mean_of(x95, i95) - mean_of(x85, i85)
            anchor = mean_of(x95, i95) if not fit else mean_of(x85, te85)
            # transfer: E8.5 report + alpha * train delta. final: E9.5 full + alpha * full delta.
            if fit:
                return mean_of(x85, te85) + alpha * d, d
            return mean_of(x95, i95) + alpha * d, d
        keys = sorted(set(t85[i85]) & set(t95[i95]))
        m85 = type_means(x85, t85, i85, keys)
        m95 = type_means(x95, t95, i95, keys)
        late_only = sorted(set(t95[i95]) - set(t85[i85]))
        m95.update(type_means(x95, t95, i95, late_only))
        counts = pd.Series(t95[i95]).value_counts()
        weights = {t: float(counts.get(t, 0)) for t in set(keys) | set(late_only)}
        pred_types = {}
        for t in keys:
            pred_types[t] = m95[t] + alpha * (m95[t] - m85[t]) if not fit else m85[t] + alpha * (m95[t] - m85[t])
            if fit:
                # transfer uses E8.5 report type mean when available, else train anchor
                rep = t85[te85] == t
                anchor_t = x85[te85][rep].mean(0) if rep.any() else m85[t]
                pred_types[t] = anchor_t + alpha * (m95[t] - m85[t])
        for t in late_only:
            pred_types[t] = m95[t]
        if fit:
            # do not use report composition
            weights = {t: float((t95[tr95] == t).sum()) for t in pred_types}
        pred = mix_means(pred_types, weights)
        d = pred - (mean_of(x85, te85) if fit else mean_of(x95))
        return pred, d

    print('transfer diagnostics', flush=True)
    print('de gene call once', flush=True)
    up_t, dn_t, _ = de_genes(true_report, ref_report)
    ref_mean = pseudobulk(ref_report)
    pb_ref = pseudobulk(ref_report)
    c_up, _ = _signed_overlap(pb_ref, up_t, dn_t)
    c_dn, _ = _signed_overlap(-pb_ref, up_t, dn_t)
    chance = max(c_up, c_dn)
    head = score_mean(report_mean, ref_mean, up_t, dn_t, chance, true_report, ref_report)
    diagnostics = {'v0035_report_induced': head, 'arms': {}}
    observed = mean_of(x95, tr95) - mean_of(x85, tr85)
    for scheme in cfg['schemes']:
        for alpha in cfg['alphas']:
            pred, delta = predict(alpha, scheme, fit=True)
            sc = score_mean(pred, ref_mean, up_t, dn_t, chance, true_report, ref_report)
            sp = spearman(delta, observed)
            ratio = float(delta.std() / max(observed.std(), 1e-12))
            disaster = ratio < cfg['disaster']['min_delta_std_ratio'] or sp < cfg['disaster']['min_spearman_vs_observed_stage_delta']
            key = f'{scheme}_a{alpha}'
            diagnostics['arms'][key] = {**sc, 'spearman_vs_train_delta': sp, 'delta_std_ratio': ratio, 'disaster': disaster,
                                        'de_minus_head': None if head['de_score'] is None else sc['de_score'] - head['de_score'],
                                        'dir_minus_head': sc['de_direction'] - head['de_direction']}
            print(key, diagnostics['arms'][key], flush=True)
    dump(RUN / 'TRANSFER.json', diagnostics)

    print('building final clouds', flush=True)
    candidates = []
    final_means = {}
    for scheme in cfg['schemes']:
        for alpha in cfg['alphas']:
            pred, delta = predict(alpha, scheme, fit=False)
            observed_full = mean_of(x95) - mean_of(x85)
            sp = spearman(pred - mean_of(x95), observed_full)
            ratio = float((pred - mean_of(x95)).std() / max(observed_full.std(), 1e-12))
            disaster = ratio < cfg['disaster']['min_delta_std_ratio'] or sp < cfg['disaster']['min_spearman_vs_observed_stage_delta']
            key = f'{scheme}_a{alpha}'
            final_means[key] = {'spearman_vs_full_delta': sp, 'delta_std_ratio': ratio, 'disaster': disaster}
            if disaster:
                print('skip disaster', key, flush=True)
                continue
            shifted, gap = shift_to_mean(base, pred.astype(np.float32))
            final_means[key]['gap'] = gap
            lane = ('pba' if scheme == 'A_global' else 'pbb') + str(alpha).replace('.', '')
            candidates.append((lane, scheme, alpha, shifted, gap, sp))
    dump(RUN / 'FINAL_MEANS.json', final_means)

    lockpath = REGLOCK
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    written = []
    with lockpath.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with (ROOT / 'submissions/INDEX.tsv').open() as f:
            rows = list(csv.DictReader(f, delimiter='\t'))
        folder = ROOT / 'submissions/candidates/T1_val'
        versions = [int(r['version'][1:]) for r in rows if r['board'] == 'T1:val']
        versions += [int(p.name[1:5]) for p in folder.glob('v[0-9][0-9][0-9][0-9]_*')]
        next_version = max(versions) + 1
        for lane, scheme, alpha, shifted, gap, sp in candidates:
            version = f'v{next_version:04d}'
            next_version += 1
            path = folder / f'{version}_pbmean_{lane}' / 'submission.h5ad'
            write_candidate_from_parent(
                parent_path=parent_path,
                output_path=path,
                expression=shifted,
                row_names=list(parent.obs_names),
                normalization='log1p_normalized',
                parent_sha256=parent_row['sha256'],
                metadata_updates={
                    've_t1_pbmean': json.dumps({
                        'lane': lane, 'scheme': scheme, 'alpha': alpha, 'parent': cfg['parent'],
                        'run': str(RUN.relative_to(ROOT)), 'target_used': False,
                        'type_mix': cfg['type_mix'], 'design_sha256': sha(CONFIG),
                        'mean_abs_gap': gap['mean_abs_gap'], 'negative_fraction': gap['negative_fraction'],
                    }, sort_keys=True)
                },
            )
            contract = validate_h5ad_contract(path, task='T1', board='val', scorer_lock=LOCK, parent_path=parent_path, parent_sha256=parent_row['sha256'])
            dump(RUN / f'CONTRACT_{lane}.json', contract)
            if contract['status'] != 'PASS':
                print('contract failed', lane, flush=True)
                continue
            digest = sha(path)
            row = dict.fromkeys(rows[0].keys(), '')
            row.update(status='candidate', submission_group='T1-PBMEAN-20260929', board='T1:val', version=version,
                       method=f'pbmean_{lane}', path=str(path.relative_to(ROOT)), n_cells='5118', n_genes='32285',
                       seed=str(cfg['seed']), target_used='false', local_contract='pass', sha256=digest,
                       score_status='score_pending',
                       notes=f'parent={cfg["parent"]}; scheme={scheme}; alpha={alpha}; run={RUN.relative_to(ROOT)}; NOT_SUBMITTED; local transfer is not a stop; no E10.5 truth')
            with (ROOT / 'submissions/INDEX.tsv').open('a') as f:
                csv.DictWriter(f, fieldnames=list(row), delimiter='\t', lineterminator='\n').writerow(row)
            with (ROOT / 'docs/coordination/T1_TRACKING.md').open('a') as f:
                f.write(f'\n- 2026-09-29 T1-PBMEAN {lane} 新候选 {version}：在 v0035 上按冻结平均数外推平移，parent=v0035，contract PASS，未提交/未评分；证据 {RUN.relative_to(ROOT)}/RESULT.json。\n')
            written.append({'lane': lane, 'scheme': scheme, 'alpha': alpha, 'version': version, 'path': row['path'], 'sha256': digest, 'gap': gap, 'spearman': sp})
            print('wrote', version, lane, flush=True)
    dump(RUN / 'RESULT.json', {
        'status': 'CANDIDATES_READY' if written else 'COMPUTED_NO_CANDIDATE',
        'candidates': written,
        'wall_s': time.time() - started,
        'server_submission': 'NOT_RUN',
        'future_validation': 'NOT_RUN_NO_E105_TRUTH',
        'local_policy': 'slightly_weaker_than_v0035_allowed',
        'blocks_submission': False,
    })
    print('done', len(written), flush=True)


if __name__ == '__main__':
    main()
