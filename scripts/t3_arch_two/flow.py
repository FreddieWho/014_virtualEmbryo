"""WT-anchored conditional residual OT flow, not a CellFlow reproduction.

Every allowed source cell contributes to exact condition/sample OT endpoints.
Whole-gene holdouts are excluded from fitting. Final inference stays in log space.
"""
from pathlib import Path
import copy
import json
import os
import sys
import time

os.environ.setdefault('POT_BACKEND_DISABLE_TENSORFLOW', '1')
os.environ.setdefault('POT_BACKEND_DISABLE_JAX', '1')
import numpy as np
import torch
from torch import nn
from scipy.spatial.distance import cdist
from sklearn.linear_model import Ridge
from scripts.t3_priority_six.common import ROOT, sha, dump, dense, load_inputs

RUN = ROOT / 'artifacts/t3_arch_two_20261001'


class ResidualField(nn.Module):
    def __init__(self, genes, condition_dim, hidden=256):
        super().__init__()
        self.state = nn.Sequential(nn.Linear(2 * genes + 1, hidden), nn.SiLU(), nn.Linear(hidden, hidden), nn.SiLU())
        self.condition = nn.Sequential(nn.Linear(condition_dim, hidden), nn.SiLU(), nn.Linear(hidden, 2 * hidden))
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.SiLU(), nn.Linear(hidden, genes))
        self.register_buffer('support', torch.ones(genes))

    def forward(self, x, anchor, t, condition):
        h = self.state(torch.cat([x - anchor, anchor, t[:, None]], dim=1))
        gamma, beta = self.condition(condition).chunk(2, dim=1)
        g0, b0 = self.condition(torch.zeros_like(condition)).chunk(2, dim=1)
        # Analytic null: v(c=0) == 0 for every x and every time, also after training.
        return (self.head(h * (1 + gamma) + beta) - self.head(h * (1 + g0) + b0)) * self.support


@torch.no_grad()
def integrate(model, base, center, scale, embedding, steps, batch=512):
    model.eval()
    base = np.asarray(base, dtype=np.float32)
    center = np.broadcast_to(np.asarray(center, dtype=np.float32), base.shape)
    scale = np.asarray(scale, dtype=np.float32)
    results = []
    for first in range(0, len(base), batch):
        original = torch.from_numpy(base[first:first + batch].copy())
        mu = torch.from_numpy(center[first:first + batch].copy())
        sd = torch.from_numpy(scale)
        anchor = (original - mu) / sd
        x = anchor.clone()
        condition = torch.from_numpy(np.asarray(embedding, dtype=np.float32)).expand(len(x), -1)
        # Fixed midpoint RK2; projection is part of both source evaluation and target inference.
        for step in range(steps):
            t = torch.full((len(x),), step / steps)
            k1 = model(x, anchor, t, condition)
            mid = x + k1 / (2 * steps)
            k2 = model(mid, anchor, t + .5 / steps, condition)
            x = torch.maximum(x + k2 / steps, -mu / sd)
        results.append((mu + sd * x).clamp_min(0).numpy())
    result = np.concatenate(results)
    # Preserve bitwise identity for the exact control condition, without arithmetic roundoff.
    if not np.any(embedding):
        return base.copy()
    if not np.isfinite(result).all():
        raise ValueError('nonfinite integrated expression')
    return result


def arrays(source, emb):
    x = dense(source.X).astype(np.float32)
    conditions = source.obs.condition.astype(str).to_numpy()
    samples = source.obs['sample'].astype(str).to_numpy()
    genes = sorted(set(conditions) - {'ctrl'})
    return x, conditions, samples, genes, {g: emb[g] for g in genes}


def make_groups(x, labels, samples, genes, selected_samples, scale):
    import ot
    groups, receipt = [], []
    for sample in selected_samples:
        ctrl_rows = np.flatnonzero((samples == sample) & (labels == 'ctrl'))
        ctrl = x[ctrl_rows]
        center = ctrl.mean(0)
        for gene in genes:
            ko_rows = np.flatnonzero((samples == sample) & (labels == gene))
            ko = x[ko_rows]
            if min(len(ctrl), len(ko)) < 20:
                raise ValueError('insufficient allowed condition/sample cells')
            x0, x1 = (ctrl - center) / scale, (ko - center) / scale
            cost = cdist(x0, x1, metric='sqeuclidean') / x.shape[1]
            coupling = ot.emd(np.ones(len(ctrl)) / len(ctrl), np.ones(len(ko)) / len(ko), cost, numThreads=1)
            np.testing.assert_allclose(coupling.sum(1), 1 / len(ctrl), atol=1e-9)
            np.testing.assert_allclose(coupling.sum(0), 1 / len(ko), atol=1e-9)
            a, b = np.nonzero(coupling > 0)
            groups.append({'gene': gene, 'sample': sample, 'x0': torch.from_numpy(x0[a].copy()),
                           'x1': torch.from_numpy(x1[b].copy()), 'weight': torch.from_numpy(coupling[a, b].astype(np.float32))})
            receipt.append({'gene': gene, 'sample': sample, 'control_cells': len(ctrl), 'KO_cells': len(ko),
                            'edges': len(a), 'all_control_endpoints': len(set(a)) == len(ctrl),
                            'all_KO_endpoints': len(set(b)) == len(ko), 'OT_cost': float((coupling * cost).sum())})
    return groups, receipt


def fit(source, embeddings, genes, sample_names, cfg, directory, val_genes=None, epochs=None):
    sys.path.insert(0, str(ROOT / 'third_party/torchcfm'))
    from torchcfm.conditional_flow_matching import ConditionalFlowMatcher
    directory.mkdir(parents=True, exist_ok=False)
    seed = cfg['seed']
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    x = dense(source.X).astype(np.float32)
    labels = source.obs.condition.astype(str).to_numpy()
    samples = source.obs['sample'].astype(str).to_numpy()
    train_ctrl = (labels == 'ctrl') & np.isin(samples, sample_names)
    scale = np.maximum(x[train_ctrl].std(0), cfg['flow']['scale_floor']).astype(np.float32)
    selected = np.isin(labels, genes + ['ctrl']) & np.isin(samples, sample_names)
    counts = (x[selected] > 0).sum(0)
    support = np.sqrt(counts / (counts + cfg['flow']['source_support_prior'])).astype(np.float32)
    groups, receipt = make_groups(x, labels, samples, genes, sample_names, scale)
    model = ResidualField(x.shape[1], len(next(iter(embeddings.values()))), cfg['flow']['hidden'])
    model.support.copy_(torch.from_numpy(support))
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['flow']['learning_rate'], weight_decay=cfg['flow']['weight_decay'])
    matcher = ConditionalFlowMatcher(sigma=cfg['flow']['sigma'])
    dump(directory / 'FIT_INPUTS.json', {'genes': genes, 'samples': sample_names, 'selected_cells': int(selected.sum()),
          'training_condition_samples': receipt, 'every_OT_endpoint_used_each_epoch': True,
          'validation_genes': val_genes or [], 'tool': 'actual vendored TorchCFM ConditionalFlowMatcher',
          'supported_genes': int(np.count_nonzero(support))})
    best, best_epoch, best_value = None, 0, float('inf')
    history = []
    n_epochs = epochs or cfg['flow']['epochs']
    for epoch in range(1, n_epochs + 1):
        model.train()
        losses = []
        for gi in rng.permutation(len(groups)):
            group = groups[gi]
            order = rng.permutation(len(group['x0']))
            for first in range(0, len(order), cfg['flow']['batch_size']):
                ix = order[first:first + cfg['flow']['batch_size']]
                x0, x1 = group['x0'][ix], group['x1'][ix]
                weights = group['weight'][ix]
                weights = weights / weights.sum()
                t, xt, ut = matcher.sample_location_and_conditional_flow(x0, x1)
                condition = torch.from_numpy(embeddings[group['gene']]).expand(len(ix), -1)
                v = model(xt, x0, t, condition)
                fm = (((v - ut) ** 2).mean(1) * weights).sum()
                pred_mean = (v * weights[:, None]).sum(0)
                true_mean = (ut * weights[:, None]).sum(0)
                mean_loss = ((pred_mean - true_mean) ** 2).mean()
                corr_loss = 1 - torch.nn.functional.cosine_similarity(pred_mean[None], true_mean[None], dim=1)[0]
                loss = fm + cfg['flow']['delta_loss_weight'] * mean_loss + cfg['flow']['correlation_loss_weight'] * corr_loss
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.)
                optimizer.step()
                losses.append(float(loss.detach()))
        record = {'epoch': epoch, 'loss': float(np.mean(losses))}
        if val_genes and epoch % cfg['flow']['validation_interval'] == 0:
            metrics, _, _ = evaluate(model, scale, source, embeddings, val_genes, sample_names, cfg, baselines=False)
            value = float(np.mean([r['flow']['delta_mse'] for r in metrics]))
            record['validation_final_matrix_delta_mse'] = value
            if value < best_value:
                best, best_epoch, best_value = copy.deepcopy(model.state_dict()), epoch, value
        history.append(record)
        if epoch % 5 == 0:
            print('FLOW_EPOCH', directory.name, record, flush=True)
    if val_genes:
        if best is None:
            raise RuntimeError('no held-out checkpoint selection')
        model.load_state_dict(best)
    else:
        best_epoch = n_epochs
    torch.save({'state': model.state_dict(), 'scale': scale, 'epochs': best_epoch}, directory / 'model.pt')
    dump(directory / 'HISTORY.json', {'history': history, 'selected_epoch': best_epoch,
          'selection': 'whole-validation-gene final integrated matrix delta MSE' if val_genes else 'frozen refit epoch count'})
    return model, scale, best_epoch


def matrix_metrics(pred, truth, ctrl):
    dp, dt = pred.mean(0) - ctrl.mean(0), truth.mean(0) - ctrl.mean(0)
    useful = np.abs(dt) > .01
    top = np.argsort(np.abs(dt))[-50:]
    ptop = np.argsort(np.abs(dp))[-50:]
    from scipy.stats import spearmanr
    bandwidth = np.median(cdist(ctrl, ctrl, 'sqeuclidean'))
    bandwidth = max(float(bandwidth), 1e-6)
    kernel = lambda a, b: np.exp(-cdist(a, b, 'sqeuclidean') / (2 * bandwidth))
    mmd = float(kernel(pred, pred).mean() + kernel(truth, truth).mean() - 2 * kernel(pred, truth).mean())
    cp, ct = np.cov(pred, rowvar=False), np.cov(truth, rowvar=False)
    upper = np.triu_indices(len(dp), 1)
    cp, ct = cp[upper], ct[upper]
    return {'delta_mse': float(np.mean((dp - dt) ** 2)),
            'delta_cosine': float(dp @ dt / (np.linalg.norm(dp) * np.linalg.norm(dt) + 1e-12)),
            'direction_nontrivial': float(np.mean(np.sign(dp[useful]) == np.sign(dt[useful]))) if useful.any() else None,
            'DE_abs_rank_spearman': float(spearmanr(np.abs(dp), np.abs(dt)).statistic),
            'DE_top50_overlap': len(set(top) & set(ptop)) / 50,
            'severity_slope_on_truth_top50': float(dp[top] @ dt[top] / (dt[top] @ dt[top] + 1e-12)),
            'mmd_biased_full_cells': mmd,
            'covariance_cosine': float(cp @ ct / (np.linalg.norm(cp) * np.linalg.norm(ct) + 1e-12)),
            'predicted_max_abs_log_mean_delta': float(np.max(np.abs(dp)))}


def evaluate(model, scale, source, embeddings, genes, eval_samples, cfg, train_genes=None, train_samples=None, baselines=True):
    x = dense(source.X).astype(np.float32)
    labels = source.obs.condition.astype(str).to_numpy()
    samples = source.obs['sample'].astype(str).to_numpy()
    records, predictions, truths = [], {}, {}
    mean_delta, linear = None, None
    if baselines:
        deltas = []
        for gene in train_genes:
            ds = []
            for sample in train_samples:
                ctrl = x[(labels == 'ctrl') & (samples == sample)]
                ko = x[(labels == gene) & (samples == sample)]
                ds.append(ko.mean(0) - ctrl.mean(0))
            deltas.append(np.mean(ds, axis=0))
        mean_delta = np.mean(deltas, axis=0)
        linear = Ridge(alpha=10.).fit(np.array([embeddings[g] for g in train_genes]), deltas)
    for gene in genes:
        pred, truth, controls, shuffled, mean_preds, linear_preds = [], [], [], [], [], []
        other = train_genes[0] if train_genes else genes[(genes.index(gene) + 1) % len(genes)]
        for sample in eval_samples:
            ctrl = x[(labels == 'ctrl') & (samples == sample)]
            ko = x[(labels == gene) & (samples == sample)]
            pred.append(integrate(model, ctrl, ctrl.mean(0), scale, embeddings[gene], cfg['flow']['integration_steps']))
            truth.append(ko)
            controls.append(ctrl)
            if baselines:
                shuffled.append(integrate(model, ctrl, ctrl.mean(0), scale, embeddings[other], cfg['flow']['integration_steps']))
                mean_preds.append(np.maximum(ctrl + mean_delta, 0))
                linear_preds.append(np.maximum(ctrl + linear.predict(embeddings[gene][None])[0], 0))
        pred, truth, ctrl = np.vstack(pred), np.vstack(truth), np.vstack(controls)
        record = {'gene': gene, 'evaluation_samples': eval_samples, 'truth_cells': len(truth),
                  'flow': matrix_metrics(pred, truth, ctrl)}
        if baselines:
            record.update(WT=matrix_metrics(ctrl, truth, ctrl),
                          mean_perturbation=matrix_metrics(np.vstack(mean_preds), truth, ctrl),
                          functional_linear=matrix_metrics(np.vstack(linear_preds), truth, ctrl),
                          condition_mismatch=matrix_metrics(np.vstack(shuffled), truth, ctrl))
        records.append(record)
        predictions[gene], truths[gene] = pred, truth
    return records, predictions, truths


def run():
    started = time.time()
    cfg = json.loads((RUN / 'CONFIG.json').read_text())
    torch.set_num_threads(8)
    source, parent, wt = load_inputs()
    assert wt.var_names.equals(parent.var_names)
    old_lock = json.loads((ROOT / 'artifacts/t3_priority_six_20260930/INPUT_LOCK.json').read_text())
    for path, expected in old_lock['inputs'].items():
        if sha(ROOT / path) != expected:
            raise ValueError('input changed: ' + path)
    review = json.loads((ROOT / 'reports/t3_priority_six_20260930/SOURCE_REVIEW.json').read_text())
    for path, expected in review['files'].items():
        if sha(ROOT / path) != expected:
            raise ValueError('ontology representation changed: ' + path)
    locked_paths = [cfg['source_manifest'], cfg['GO_embedding'], cfg['source_split'],
                    'infra/external_data/sanitized/T3-R6-OP2-20260921/expression.h5ad',
                    'data/E8.75.h5ad', 'third_party/torchcfm/torchcfm/conditional_flow_matching.py',
                    'third_party/torchcfm/LICENSE', 'artifacts/t3_arch_two_20261001/CONFIG.json',
                    'scripts/t3_arch_two/flow.py']
    dump(RUN / 'A_INPUT_LOCK.json', {'before_training': True, 'sha256': {p: sha(ROOT / p) for p in locked_paths},
          'GO_source_review': 'reports/t3_priority_six_20260930/SOURCE_REVIEW.json',
          'response_review': 'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json',
          'new_external_expression_data': False})
    z = np.load(ROOT / cfg['GO_embedding'])
    embeddings = dict(zip(z['genes'].astype(str), z['embedding']))
    old = json.loads((ROOT / cfg['source_split']).read_text())
    split = old['split']
    samples = sorted(set(source.obs['sample'].astype(str)))
    directory = RUN / 'a_residual_flow'
    directory.mkdir(parents=True, exist_ok=False)
    train, val, test = split['train'], split['val'], split['test']
    assert not (set(train) & (set(val) | set(test)))
    model, scale, epochs = fit(source, embeddings, train, samples, cfg, directory / 'holdout_fit', val_genes=val)
    scores, preds, truth = evaluate(model, scale, source, embeddings, test, samples, cfg, train, samples)
    # These receipts are saved before any final refit on the held-out genes.
    dump(directory / 'HOLDOUT.json', {'split': split, 'checkpoint_epochs': epochs, 'records': scores,
          'fitted_test_genes': [], 'historical_holdout_previously_examined': True,
          'limitation': 'internal whole-gene benchmark; not pristine external validation and not independent animals'})
    np.savez_compressed(directory / 'HOLDOUT_MATRICES.npz', **{f'{g}_pred': v for g, v in preds.items()}, **{f'{g}_truth': v for g, v in truth.items()})
    cross = []
    for i in range(2):
        m, sd, _ = fit(source, embeddings, train, [samples[i]], cfg, directory / f'cross_sample{i}', epochs=epochs)
        rr, _, _ = evaluate(m, sd, source, embeddings, test, [samples[1 - i]], cfg, train, [samples[i]])
        cross.append({'training_sample': samples[i], 'test_sample': samples[1 - i], 'records': rr})
    dump(directory / 'CROSS_SAMPLE.json', {'scenarios': cross, 'animal_independence': 'UNKNOWN'})
    all_genes = sorted(set(source.obs.condition.astype(str)) - {'ctrl'})
    model, scale, _ = fit(source, embeddings, all_genes, samples, cfg, directory / 'final_fit', epochs=epochs)
    ix = wt.obs_names.get_indexer(parent.obs_names)
    assert (ix >= 0).all()
    factual = dense(wt.X[ix]).astype(np.float32)
    full_wt = dense(wt.X).astype(np.float32)
    wt_types = wt.obs.celltype.astype(str).to_numpy()
    types = parent.obs.celltype.astype(str).to_numpy()
    centers = {t: full_wt[wt_types == t].mean(0) for t in set(types)}
    center = np.stack([centers[t] for t in types])
    result = integrate(model, factual, center, scale, embeddings['Gata4'], cfg['flow']['integration_steps'])
    identity = integrate(model, factual, center, scale, np.zeros_like(embeddings['Gata4']), cfg['flow']['integration_steps'])
    np.testing.assert_array_equal(identity, factual)
    gi = parent.var_names.get_loc('Gata4')
    result[:, gi] = 0.
    candidate = parent.copy()
    candidate.X = result
    candidate.uns = {'ve_contract': {'normalization': 'log_normalized'},
                     't3_architecture': {'name': 'WT-anchored conditional residual OT flow',
                     'implementation': 'custom; actual TorchCFM sampler, not original CellFlow reproduction',
                     'config_sha256': sha(RUN / 'CONFIG.json')}}
    candidate.write_h5ad(directory / 'research.h5ad', compression='gzip')
    np.savez_compressed(directory / 'TARGET_ARRAYS.npz', factual=factual, prediction=result, center=center, scale=scale)
    delta = result.mean(0) - factual.mean(0)
    changed = np.abs(result - factual) > 1e-6
    changed[:, gi] = False
    dump(directory / 'RESULT.json', {'status': 'FULL_TARGET_INFERENCE_COMPLETE_RESEARCH', 'shape': list(result.shape),
          'sha256': sha(directory / 'research.h5ad'), 'all_7449_cells_inferred': True,
          'downstream_changed_cells': int(changed.any(1).sum()), 'downstream_changed_genes': int(changed.any(0).sum()),
          'zero_RNA_downstream_changed_cells': int(changed[factual[:, gi] == 0].any(1).sum()),
          'identity_exact': True, 'source_log_space_final_matrix_validation': 'COMPLETED',
          'selected_epochs': epochs, 'max_abs_log_mean_delta': float(np.max(np.abs(np.delete(delta, gi)))),
          'wall_seconds': time.time() - started, 'Gata4_truth_validation': 'NOT_RUN_NO_TRUTH', 'server_score': 'NOT_RUN'})
    print('FLOW_COMPLETE', directory, flush=True)


if __name__ == '__main__':
    run()
