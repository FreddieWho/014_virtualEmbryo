"""Lineage-conditioned neural competing risks and relative population mass.

All WT observations enter population charts and complete aggregate UOT counts.
Gata4 activity clamp is an observational intervention hypothesis. This is not
original DeepRUOT and does not infer absolute embryo birth/death rates.
"""
import os
os.environ.setdefault('POT_BACKEND_DISABLE_TENSORFLOW', '1')
os.environ.setdefault('POT_BACKEND_DISABLE_JAX', '1')
from pathlib import Path
import json
import time
import joblib
import numpy as np
import pandas as pd
import anndata as ad
import torch
from torch import nn
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from scipy.spatial.distance import cdist, jensenshannon
from scripts.t3_priority_six.common import ROOT, sha, dump, dense

RUN = ROOT / 'artifacts/t3_arch_two_20261001'
GRN = ROOT / 'infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN/mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet'


def lineage(name):
    if name == 'Unknown': return 'unknown'
    if name == 'NCC': return 'crest'
    if 'Brain' in name or 'brain' in name or 'Neural' in name or name == 'Hindbrain': return 'neural'
    if '-CM' in name or name in ['FHF', 'SHF', 'aPHM', 'pPHM', 'JCF', 'DMP']: return 'cardiac'
    if 'Endoth' in name or 'EndoMT' in name or name in ['Endo', 'Chamber-Endo', 'early-VEC', 'BEC']: return 'endothelial'
    if 'Endoderm' in name or 'FG' in name or 'gut' in name.lower() or name == 'Hepatocytes': return 'endoderm'
    if name in ['Peri', 'Proepi', 'ST']: return 'mesothelium'
    if 'CSE' in name or name in ['pSE', 'V-SE', 'SE']: return 'ectoderm'
    return 'mesoderm'


def quotas(shares, total):
    shares = np.maximum(np.asarray(shares, float), 0)
    if not np.isfinite(shares).all() or shares.sum() <= 0:
        raise ValueError('invalid population shares')
    values = shares / shares.sum() * total
    counts = np.floor(values).astype(int)
    order = np.argsort(-(values - counts), kind='stable')
    counts[order[:total - counts.sum()]] += 1
    return counts


def integer_donors(labels, shares, seed):
    labels = np.asarray(labels)
    original = np.bincount(labels, minlength=len(shares)) / len(labels)
    if np.allclose(original, shares, rtol=0, atol=1e-12):
        return np.arange(len(labels))
    counts = quotas(shares, len(labels))
    rng = np.random.default_rng(seed)
    rows = []
    for state, count in enumerate(counts):
        candidates = np.flatnonzero(labels == state)
        if count and not len(candidates):
            raise ValueError('state has no WT emission support')
        if count:
            rows.extend(rng.choice(candidates, count, replace=count > len(candidates)).tolist())
    return np.asarray(rows, int)


def fit_activity(early, panel, seed):
    if sha(GRN) != '32de319419199f53bbdbf7c8545394a70052c7d14918d59b54c96593000dea40':
        raise ValueError('promoter motif prior changed')
    prior = pd.read_parquet(GRN, columns=['gene_short_name', 'Gata4'])
    targets = set(prior.loc[prior.Gata4 > 0, 'gene_short_name'].astype(str))
    gi = panel.index('Gata4')
    candidate = np.array([j for j, g in enumerate(panel) if g in targets and j != gi])
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(early))
    fit, test = order[len(order) // 5:], order[:len(order) // 5]
    mu, sd = early[fit].mean(0), np.maximum(early[fit].std(0), .25)
    x, y = (early[fit] - mu) / sd, early[fit, gi]
    corr = (x * (y - y.mean())[:, None]).mean(0)
    chosen = candidate[np.argsort(-np.abs(corr[candidate]), kind='stable')[:20]]
    if len(chosen) < 10: raise ValueError('insufficient panel Gata4 motif targets')
    model = Ridge(alpha=10.).fit(x[:, chosen], y)
    yp = model.predict(((early[test] - mu) / sd)[:, chosen])
    mse, baseline = float(np.mean((yp - early[test, gi]) ** 2)), float(np.var(early[test, gi]))
    raw = model.predict(((early - mu) / sd)[:, chosen])
    low, high = np.quantile(raw, [.01, .99])
    if high <= low: raise ValueError('noninformative Gata4 functional proxy')
    return {'model': model, 'mu': mu, 'sd': sd, 'chosen': chosen, 'low': low, 'range': high - low}, {
        'signature_genes': [panel[j] for j in chosen], 'excluded_from_fate_PCA_and_OT_cost': True,
        'WT_holdout_cells': len(test), 'WT_proxy_mse': mse, 'WT_mean_mse': baseline,
        'functional_loss_reference': float(low), 'calibration': 'E8.0 WT only',
        'evidence_limit': 'RNA reconstruction proxy; neither protein activity nor KO causality validated'}


def activity_values(x, model):
    raw = model['model'].predict(((x - model['mu']) / model['sd'])[:, model['chosen']])
    return np.maximum((raw - model['low']) / model['range'], 0).astype(np.float32)


def chart(xs, groups, activity, activity_model, selected_stages, cfg):
    chosen = [j for j in range(xs[0].shape[1]) if j not in set(activity_model['chosen'])]
    chosen.remove(cfg['Gata4_index'])
    training = np.concatenate([xs[i][:, chosen] for i in selected_stages])
    mu, sd = training.mean(0), np.maximum(training.std(0), .25)
    pca = PCA(n_components=cfg['pca_components'], svd_solver='randomized', random_state=cfg['seed'])
    projected = pca.fit_transform((training - mu) / sd)
    zscale = np.maximum(projected.std(0), .1)
    zs = [(pca.transform((x[:, chosen] - mu) / sd) / zscale).astype(np.float32) for x in xs]
    vocabulary = sorted(set().union(*(set(groups[i]) for i in selected_stages)))
    combined_groups = np.concatenate([groups[i] for i in selected_stages])
    sizes = np.array([(combined_groups == g).sum() for g in vocabulary])
    allocation = quotas(np.sqrt(sizes), cfg['states'] - 2 * len(vocabulary)) + 2
    fits, centers, center_groups, start = {}, [], [], 0
    pooled_z = np.concatenate([zs[i] for i in selected_stages])
    for group, count in zip(vocabulary, allocation):
        model = KMeans(n_clusters=int(count), random_state=cfg['seed'], n_init=1, max_iter=100)
        model.fit(pooled_z[combined_groups == group])
        fits[group] = (model, start)
        centers.extend(model.cluster_centers_)
        center_groups.extend([group] * count)
        start += int(count)
    labels = []
    for z, g in zip(zs, groups):
        lab = np.full(len(z), -1, int)
        for name in set(g):
            if name not in fits:
                continue
            model, offset = fits[name]
            lab[g == name] = model.predict(z[g == name]) + offset
        labels.append(lab)
    return {'mu': mu, 'sd': sd, 'chosen': chosen, 'pca': pca, 'zscale': zscale, 'fits': fits,
            'centers': np.array(centers), 'center_groups': np.array(center_groups)}, zs, labels


def bins(x, z, labels, act, t, k):
    records = []
    for state in range(k):
        rows = np.flatnonzero(labels == state)
        if not len(rows): continue
        order = rows[np.argsort(act[rows], kind='stable')]
        for part in np.array_split(order, min(4, len(order))):
            records.append({'state': state, 'count': len(part), 'activity': float(act[part].mean()),
                 'z': z[part].mean(0), 'x': x[part].mean(0),
                 'feature': np.r_[z[part].mean(0), act[part].mean(), t - 8.0].astype(np.float32)})
    return records


def teachers(xs, zs, labels, activities, c, stage_pairs, cfg, directory):
    import ot
    k, cg = len(c['centers']), c['center_groups']
    all_records, receipts, plans = [], [], {}
    times = cfg['times']
    for i, j in stage_pairs:
        src = bins(xs[i], zs[i], labels[i], activities[i], times[i], k)
        for group in sorted(set(cg)):
            subset = [r for r in src if cg[r['state']] == group]
            dst = np.array([s for s in range(k) if cg[s] == group and np.any(labels[j] == s)])
            if group == 'unknown' or not subset or not len(dst):
                receipts.append({'from': times[i], 'to': times[j], 'lineage': group, 'status': 'NO_COMPARABLE_ENDPOINT_TEACHER',
                                 'source_cells': sum(r['count'] for r in subset), 'target_cells': int(sum((labels[j] == s).sum() for s in dst))})
                continue
            a = np.array([r['count'] for r in subset], float); a /= a.sum()
            b = np.array([(labels[j] == s).sum() for s in dst], float); b /= b.sum()
            dstz = np.array([zs[j][labels[j] == s].mean(0) for s in dst])
            cost = cdist(np.array([r['z'] for r in subset]), dstz, 'sqeuclidean')
            cost /= max(float(np.median(cost)), 1e-6)
            plan = ot.unbalanced.sinkhorn_unbalanced(a, b, cost, cfg['sinkhorn_entropy'], cfg['mass_relaxation'],
                    method='sinkhorn_stabilized', numItermax=2000, stopThr=1e-9)
            if not np.isfinite(plan).all() or (plan.sum(1) <= 0).any():
                raise ValueError('unbalanced transport failed')
            relative_log_mass = np.log(plan.sum(1) / a)
            relative_log_mass -= float(relative_log_mass @ a)
            key = f'{i}_{j}_{group}'
            plans[key] = plan
            for row, record in enumerate(subset):
                p = np.zeros(k, np.float32); p[dst] = plan[row] / plan[row].sum()
                mask = np.zeros(k, bool); mask[dst] = True
                all_records.append(dict(record, probability=p, destination_mask=mask,
                    log_mass=float(relative_log_mass[row]), duration=times[j] - times[i],
                    fit_weight=record['count'] / len(xs[i]), from_stage=i, to_stage=j))
            receipts.append({'from': times[i], 'to': times[j], 'lineage': group, 'status': 'FULL_AGGREGATE_UOT_COMPLETE',
                 'source_cells': sum(r['count'] for r in subset), 'target_cells': int(sum((labels[j] == s).sum() for s in dst)),
                 'source_activity_bins': len(subset), 'destination_states': len(dst), 'OT_mass': float(plan.sum()),
                 'physical_growth_identified': False})
    if not all_records: raise ValueError('no temporal teachers')
    dump(directory / 'TRANSPORT_RECEIPT.json', {'intervals': receipts, 'cells_per_stage': [len(x) for x in xs],
          'all_cells_used_for_charts_and_population_counts': True, 'cell_level_exact_OT': False,
          'declared_model': 'complete aggregate UOT; four activity strata per state, no random cell subset'})
    np.savez_compressed(directory / 'TRANSPORT_PLANS.npz', **plans)
    return all_records


class FateMass(nn.Module):
    def __init__(self, features, states, hidden, growth_bound):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(features, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.fates = nn.Linear(hidden, states)
        self.exit = nn.Linear(hidden, 1)
        self.growth = nn.Linear(hidden, 1)
        self.bound = growth_bound

    def forward(self, features, state, mask, duration):
        h = self.body(features)
        fate = torch.softmax(self.fates(h).masked_fill(~mask, -1e9), dim=1)
        rate = torch.nn.functional.softplus(self.exit(h)[:, 0])
        stayed = torch.exp(-rate * duration)
        identity = torch.nn.functional.one_hot(state, fate.shape[1]).float()
        probability = stayed[:, None] * identity + (1 - stayed[:, None]) * fate
        log_mass = torch.tanh(self.growth(h)[:, 0]) * self.bound * duration
        return probability, log_mass


def fit_model(records, cfg, directory):
    torch.manual_seed(cfg['seed'])
    features = torch.from_numpy(np.stack([r['feature'] for r in records]))
    states = torch.tensor([r['state'] for r in records])
    mask = torch.from_numpy(np.stack([r['destination_mask'] for r in records]))
    duration = torch.tensor([r['duration'] for r in records], dtype=torch.float32)
    truth_p = torch.from_numpy(np.stack([r['probability'] for r in records]))
    truth_m = torch.tensor([r['log_mass'] for r in records], dtype=torch.float32)
    weight = torch.tensor([r['fit_weight'] for r in records], dtype=torch.float32); weight /= weight.sum()
    model = FateMass(features.shape[1], truth_p.shape[1], cfg['hidden'], cfg['growth_bound'])
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['learning_rate'], weight_decay=cfg['regularization_weight'])
    history = []
    for epoch in range(1, cfg['epochs'] + 1):
        p, m = model(features, states, mask, duration)
        ce = -(truth_p * p.clamp_min(1e-9).log()).sum(1)
        mass_loss = (m - truth_m) ** 2
        loss = (weight * (ce + cfg['mass_loss_weight'] * mass_loss)).sum()
        optimizer.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
        optimizer.step()
        if epoch % 200 == 0:
            record = {'epoch': epoch, 'loss': float(loss.detach()), 'mass_mse': float((weight * mass_loss).sum().detach())}
            history.append(record); print('FATE_EPOCH', directory.name, record, flush=True)
    torch.save(model.state_dict(), directory / 'model.pt')
    dump(directory / 'HISTORY.json', {'history': history, 'epochs': cfg['epochs'], 'teacher_bins': len(records), 'hyperparameter_search': False})
    return model


@torch.no_grad()
def predict(model, records, duration=None, knockout=False):
    features = np.stack([r['feature'] for r in records]).copy()
    if knockout: features[:, -2] = 0
    d = torch.tensor([duration if duration is not None else r['duration'] for r in records], dtype=torch.float32)
    p, m = model(torch.from_numpy(features), torch.tensor([r['state'] for r in records]),
                 torch.from_numpy(np.stack([r['destination_mask'] for r in records])), d)
    return p.numpy(), np.exp(m.numpy())


def middle_evaluation(xs, groups, activities, am, cfg, directory):
    directory.mkdir()
    c, zs, labels = chart(xs, groups, activities, am, [0, 2], cfg)
    records = teachers(xs, zs, labels, activities, c, [(0, 2)], cfg, directory)
    model = fit_model(records, cfg, directory)
    probability, mass = predict(model, records, duration=.75)
    predicted = np.zeros(cfg['states']); group_reports = []
    for group in sorted(set(c['center_groups'])):
        ix = [i for i, r in enumerate(records) if c['center_groups'][r['state']] == group]
        target = labels[1][groups[1] == group]
        if not ix or not len(target) or (target < 0).any():
            group_reports.append({'lineage': group, 'status': 'NOT_EVALUABLE_NO_MATCHED_ENDPOINTS', 'middle_cells': len(target)})
            continue
        weights = np.array([records[i]['count'] for i in ix], float); weights /= weights.sum()
        # Interpolate actual corner expression centroids, never use middle expression in prediction.
        future_means = {s: xs[2][labels[2] == s].mean(0) for s in np.unique(labels[2]) if s >= 0}
        state_points, point_weights = [], []
        for weight, i in zip(weights, ix):
            for dest in np.flatnonzero(probability[i] > 1e-7):
                # Retention uses the current centroid; no later-stage support is fabricated.
                terminal = future_means.get(dest, records[i]['x'])
                midx = .5 * records[i]['x'] + .5 * terminal
                zp = c['pca'].transform(((midx[c['chosen']] - c['mu']) / c['sd'])[None]) / c['zscale']
                km, offset = c['fits'][group]
                state_points.append(int(km.predict(zp)[0] + offset))
                point_weights.append(weight * mass[i] * probability[i, dest])
        predicted_group = np.bincount(state_points, weights=point_weights, minlength=cfg['states'])
        predicted_group /= predicted_group.sum()
        truth = np.bincount(target, minlength=cfg['states']) / len(target)
        early = np.bincount(labels[0][groups[0] == group], minlength=cfg['states']); early = early / early.sum()
        late = np.bincount(labels[2][groups[2] == group], minlength=cfg['states']); late = late / late.sum()
        linear = (early + late) / 2
        predicted += predicted_group * len(target) / len(xs[1])
        group_reports.append({'lineage': group, 'status': 'WT_MIDPOINT_EVALUATED', 'middle_cells': len(target),
                 'neural_JS': float(jensenshannon(predicted_group, truth) ** 2),
                 'early_copy_JS': float(jensenshannon(early, truth) ** 2),
                 'linear_share_interpolation_JS': float(jensenshannon(linear, truth) ** 2)})
    covered = sum(r['middle_cells'] for r in group_reports if r['status'] == 'WT_MIDPOINT_EVALUATED')
    dump(directory / 'EVALUATION.json', {'middle_time_not_used_for_PCA_chart_activity_or_model_fitting': True,
         'middle_cells_total': len(xs[1]), 'covered_middle_cells': covered, 'coverage': covered / len(xs[1]),
         'groups': group_reports, 'scope': 'WT lineage-conditioned midpoint state distribution, not Gata4 intervention validation'})
    return group_reports


def emit(xs, objects, labels, chart_, shares, parent, seed):
    k = len(shares)
    wt_mid = objects[1]
    parent_rows = wt_mid.obs_names.get_indexer(parent.obs_names)
    if (parent_rows < 0).any(): raise ValueError('parent WT correspondence missing')
    parent_states = labels[1][parent_rows]
    original = np.bincount(parent_states, minlength=k) / len(parent)
    quota = quotas(shares, len(parent))
    offsets = np.r_[0, np.cumsum([len(x) for x in xs])]
    rng = np.random.default_rng(seed)
    choices, sources = [], []
    if np.allclose(shares, original, atol=1e-12, rtol=0):
        choices = (parent_rows + offsets[1]).tolist()
        sources = [1] * len(choices)
    else:
        for state, count in enumerate(quota):
            if not count: continue
            preferred = parent_rows[parent_states == state]
            source = 1
            if len(preferred):
                candidates = preferred
            else:
                candidates = np.flatnonzero(labels[1] == state)
                if not len(candidates):
                    for alternative in [0, 2]:
                        candidates = np.flatnonzero(labels[alternative] == state)
                        if len(candidates): source = alternative; break
            if not len(candidates): raise ValueError('predicted state lacks any actual WT donor')
            selected = rng.choice(candidates, count, replace=count > len(candidates))
            choices.extend((selected + offsets[source]).tolist()); sources.extend([source] * count)
    # Carrier is a documented mixture of whole measured WT vectors, not a column-wise reconstruction.
    carrier = parent.copy()
    carrier.obs_names = [f'fate_{i:05d}' for i in range(len(choices))]
    xpool = np.vstack(xs)
    coords = []
    middle_coords = np.asarray(objects[1].obsm['spatial_3D'])[:, :3]
    reference_center = np.median(middle_coords, axis=0)
    reference_scale = np.maximum(np.quantile(middle_coords, .75, axis=0) - np.quantile(middle_coords, .25, axis=0), 1e-8)
    for i, obj in enumerate(objects):
        xyz = np.asarray(obj.obsm['spatial_3D'])[:, :3].copy()
        if i != 1:
            center = np.median(xyz, axis=0)
            scale = np.maximum(np.quantile(xyz, .75, axis=0) - np.quantile(xyz, .25, axis=0), 1e-8)
            xyz = (xyz - center) / scale * reference_scale + reference_center
        coords.append(xyz)
    carrier.X = xpool[np.array(choices)].astype(np.float32)
    carrier.obsm['spatial_3D'] = np.vstack(coords)[np.array(choices)]
    carrier.uns = {'ve_contract': {'normalization': 'log_normalized', 'source': 'whole-vector WT donor carrier with logged donor stages'}}
    return carrier, np.array(choices), np.array(sources), parent_states


def run():
    started = time.time()
    if not (RUN / 'a_residual_flow/REGISTRATION.json').exists(): raise RuntimeError('complete A before starting B')
    base = json.loads((RUN / 'CONFIG.json').read_text())
    extra = json.loads((RUN / 'B_CONFIG.json').read_text())
    cfg = dict(base['fate_mass'], **{k: extra[k] for k in ['growth_bound', 'mass_loss_weight', 'regularization_weight']}, seed=base['seed'])
    torch.set_num_threads(8)
    directory = RUN / 'b_fate_mass'; directory.mkdir(exist_ok=False)
    panel = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    cfg['Gata4_index'] = panel.index('Gata4')
    paths = cfg['WT_paths']
    objects = [ad.read_h5ad(ROOT / p)[:, panel].copy() for p in paths]
    xs = [dense(o.X).astype(np.float32) for o in objects]
    if any(not np.isfinite(x).all() or x.min() < 0 for x in xs): raise ValueError('invalid WT expression')
    groups = [np.array([lineage(s) for s in o.obs.celltype.astype(str)]) for o in objects]
    locked = paths + ['artifacts/t3_arch_two_20261001/CONFIG.json', 'artifacts/t3_arch_two_20261001/B_CONFIG.json',
                     'scripts/t3_arch_two/fate.py', str(GRN.relative_to(ROOT))]
    dump(RUN / 'B_INPUT_LOCK.json', {'before_B_training': True, 'sha256': {p: sha(ROOT / p) for p in locked},
          'WT_cells': [len(x) for x in xs], 'total_WT_cells': sum(len(x) for x in xs),
          'new_external_expression_data': False, 'no_Mab21l2_or_Gata4_KO_records_read': True,
          'source_scope': 'existing official WT MERFISH plus existing reviewed mouse promoter motif topology',
          'absolute_census_available': False})
    am, activity_receipt = fit_activity(xs[0], panel, cfg['seed'])
    acts = [activity_values(x, am) for x in xs]
    dump(directory / 'ACTIVITY_PROXY.json', dict(activity_receipt,
          quantiles_per_stage=[np.quantile(a, [0, .5, .9, .99, 1]).tolist() for a in acts]))
    print('FATE_FULL_WT_INPUT', [len(x) for x in xs], flush=True)
    middle_evaluation(xs, groups, acts, am, cfg, directory / 'WT_middle_holdout')
    c, zs, labels = chart(xs, groups, acts, am, [0, 1, 2], cfg)
    records = teachers(xs, zs, labels, acts, c, [(0, 1), (1, 2)], cfg, directory)
    model = fit_model(records, cfg, directory)
    joblib.dump({'chart': c, 'activity': am, 'cfg': cfg}, directory / 'population_model.joblib')
    first = [r for r in records if r['from_stage'] == 0 and r['to_stage'] == 1]
    pf, mf = predict(model, first)
    pk, mk = predict(model, first, knockout=True)
    parent_path = ROOT / 'submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad'
    parent = ad.read_h5ad(parent_path)
    ip = objects[1].obs_names.get_indexer(parent.obs_names)
    if (ip < 0).any(): raise ValueError('target parent alignment')
    parent_labels = labels[1][ip]
    observed = np.bincount(parent_labels, minlength=cfg['states']) / len(parent)
    prediction = observed.copy()
    mass_only = observed.copy()
    transition_only = observed.copy()
    coverage = []
    for group in sorted(set(c['center_groups'])):
        ix = [i for i, r in enumerate(first) if c['center_groups'][r['state']] == group]
        states = c['center_groups'] == group
        target_share = observed[states].sum()
        if not ix or not target_share:
            coverage.append({'lineage': group, 'status': 'WT_SHARES_HELD_NO_COMPARABLE_TEACHER', 'target_share': float(target_share)})
            continue
        weight = np.array([first[i]['count'] for i in ix], float); weight /= weight.sum()
        factual = (pf[ix] * (weight * mf[ix])[:, None]).sum(0)
        counter = (pk[ix] * (weight * mk[ix])[:, None]).sum(0)
        mass_counter = (pf[ix] * (weight * mk[ix])[:, None]).sum(0)
        fate_counter = (pk[ix] * (weight * mf[ix])[:, None]).sum(0)
        normalizer = factual.sum()
        # Additive density residual avoids division by a nearly absent WT destination.
        prediction += target_share * (counter - factual) / normalizer
        mass_only += target_share * (mass_counter - factual) / normalizer
        transition_only += target_share * (fate_counter - factual) / normalizer
        coverage.append({'lineage': group, 'status': 'GATA4_ACTIVITY_CLAMP_HYPOTHESIS', 'target_share': float(target_share),
               'relative_lineage_mass_factor': float(counter.sum() / normalizer),
               'weighted_activity_before': float(weight @ np.array([first[i]['activity'] for i in ix]))})
    negative_mass = float(-prediction[prediction < 0].sum())
    prediction = np.maximum(prediction, 0); prediction /= prediction.sum()
    for values in [mass_only, transition_only]:
        np.maximum(values, 0, out=values); values /= values.sum()
    carrier, donors, donor_stages, parent_labels = emit(xs, objects, labels, c, prediction, parent, cfg['seed'])
    carrier.write_h5ad(directory / 'WT_CARRIER.h5ad', compression='gzip')
    candidate = carrier.copy(); candidate.X[:, cfg['Gata4_index']] = 0.
    candidate.uns['t3_architecture'] = {'name': 'lineage-conditioned neural competing-risk fate and relative mass',
        'intervention': 'Gata4 promoter-target RNA proxy clamp; observational hypothesis',
        'implementation': 'custom aggregate UOT, not original DeepRUOT', 'config_sha256': sha(RUN / 'B_CONFIG.json')}
    candidate.write_h5ad(directory / 'research.h5ad', compression='gzip')
    np.save(directory / 'DONOR_INDICES.npy', donors)
    np.save(directory / 'DONOR_STAGES.npy', donor_stages)
    np.savez_compressed(directory / 'STATE_PREDICTION.npz', WT=observed, prediction=prediction,
          mass_only=mass_only, transition_only=transition_only, center_groups=c['center_groups'])
    dump(directory / 'POPULATION_DIAGNOSTICS.json', {'lineages': coverage, 'negative_density_mass_projected': negative_mass,
          'state_L1': float(np.abs(prediction - observed).sum()),
          'mass_only_L1': float(np.abs(mass_only - observed).sum()),
          'transition_only_L1': float(np.abs(transition_only - observed).sum()),
          'donor_stage_counts': {str(cfg['times'][i]): int((donor_stages == i).sum()) for i in range(3)},
          'unsupported_target_fraction': float(sum(r['target_share'] for r in coverage if r['status'].startswith('WT_'))),
          'coordinate_frame': 'E8.75 native; other donor stages affine median/IQR mapped to E8.75, no target KO geometry',
          'Mab21l2_validation': extra['Mab21l2_validation']})
    # Identity evidence uses measured WT carrier rows; equal shares must never create random differences.
    test_labels = np.array([0, 1, 1, 2, 2, 2]); test_shares = np.bincount(test_labels) / len(test_labels)
    np.testing.assert_array_equal(integer_donors(test_labels, test_shares, cfg['seed']), np.arange(len(test_labels)))
    dump(directory / 'RESULT.json', {'status': 'FULL_TARGET_INFERENCE_COMPLETE_RESEARCH', 'shape': list(candidate.shape),
          'sha256': sha(directory / 'research.h5ad'), 'WT_carrier_sha256': sha(directory / 'WT_CARRIER.h5ad'),
          'identity_share_resampling_exact': True, 'full_target_cells': len(candidate),
          'all_WT_cells_in_population_inputs': sum(len(x) for x in xs), 'states': cfg['states'],
          'core_algorithm': 'complete declared aggregate UOT plus learned nonlinear transition and relative mass heads',
          'original_DeepRUOT': False, 'state_L1': float(np.abs(prediction - observed).sum()),
          'WT_validation': 'COMPLETED_WITH_EXPLICIT_LINEAGE_COVERAGE',
          'Gata4_truth_validation': 'NOT_RUN_NO_TRUTH', 'intervention_maturity': 'OBSERVATIONAL_HYPOTHESIS',
          'wall_seconds': time.time() - started, 'server_score': 'NOT_RUN'})
    print('FATE_COMPLETE', directory, flush=True)


if __name__ == '__main__':
    run()
