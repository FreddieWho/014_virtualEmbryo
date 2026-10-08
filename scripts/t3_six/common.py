"""Shared frozen source-LOPO harness for the six T3 routes (t3_six)."""
from pathlib import Path
import csv, hashlib, json, sys
import anndata as ad
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'third_party/veckit')]
from t3_autoresearch import retained_model
from t3_next.source_roles import require_response_role
from common import core_metrics as cm

OUT = ROOT / 'reports/t3_six_routes_20261006'
ART = ROOT / 'artifacts/t3_six_routes_20261006'
KEYS = ['de_score', 'de_direction', 'severity_abs', 'mmd_u', 'variogram']
WEIGHTS = np.array([.30, .25, .25, .12, .08])

def dense(x):
    return x.toarray() if hasattr(x, 'toarray') else np.asarray(x)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(p, x):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def fit_log_multiplier(control, delta):
    raw = np.expm1(np.asarray(control, dtype=float))
    target = np.maximum(control.mean(0, dtype=float) + delta, 0)
    lo = np.full(control.shape[1], -np.log(2.)); hi = -lo
    for _ in range(40):
        mid = (lo + hi) / 2
        mean = np.log1p(raw * np.exp(mid)).mean(0)
        lo = np.where(mean < target, mid, lo)
        hi = np.where(mean < target, hi, mid)
    result = (lo + hi) / 2
    result[np.all(control == 0, axis=0)] = 0
    return result

def emit_mult(base, beta):
    return np.log1p(np.expm1(np.asarray(base, dtype=float)) * np.exp(beta)).astype('float32')

def measure(pred, truth, ctrl):
    severity, r2 = cm.severity_slope(pred, truth, ctrl)
    vals = [cm.de_score(pred, truth, ctrl)['score'], cm.de_direction(pred, truth, ctrl),
            abs(severity), cm.mmd_unbiased(pred, truth, seed=0), cm.variogram_score(pred, truth, seed=0)]
    return {**{k: float(v) if np.isfinite(v) else None for k, v in zip(KEYS, vals)},
            'severity_r2': float(r2) if np.isfinite(r2) else None,
            'mean_response_mse': float(np.mean((pred.mean(0, dtype=float) - truth.mean(0, dtype=float)) ** 2)),
            'density': float(np.mean(pred > 0))}

def load():
    manifest = json.loads((ROOT / 'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json').read_text())
    require_response_role(manifest, ROOT, 'SIGNED_RESPONSE')
    record = manifest['files']['expression']
    assert sha(ROOT / record['path']) == record['sha256']
    final = json.loads((ROOT / 'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text())
    assert sha(ROOT / 'scripts/t3_autoresearch/retained_model.py') == final['model_sha256']
    a = ad.read_h5ad(ROOT / record['path'])
    assert a.shape == (5454, 500) and a.obs.model_input.all()
    labels = a.obs.condition.astype(str).to_numpy()
    x = dense(a.X)
    ctrl = x[labels == 'ctrl']
    cfg = json.loads((ROOT / 'artifacts/autoresearch/t3-20261002-v1/PROVENANCE.json').read_text())
    ep = ROOT / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert sha(ep) == cfg['embedding_sha256']
    emb = np.load(ep)
    ei = {g: i for i, g in enumerate(emb['genes'])}
    def predict(genes, query):
        train = {'genes': np.array(genes),
                 'E': emb['embedding'][[ei[g] for g in genes]],
                 'Y': np.array([x[labels == g].mean(0) - ctrl.mean(0) for g in genes])}
        return retained_model.predict(train, {'genes': np.array([query]), 'E': emb['embedding'][[ei[query]]]})[0]
    return x, labels, ctrl, cfg, predict

def weighted_rank(rows_methods_values):
    """rows_methods_values: list per perturbation of {method: values aligned to KEYS}."""
    ranks = []
    for vals_by_method in rows_methods_values:
        names = list(vals_by_method)
        values = np.array([vals_by_method[n] for n in names], dtype=float)
        signs = np.array([-1, -1, 1, 1, 1])
        available = np.all(np.isfinite(values), axis=0)
        rank = np.column_stack([rankdata(values[:, j] * signs[j]) for j in np.flatnonzero(available)])
        ranks.append((names, rank @ (WEIGHTS[available] / WEIGHTS[available].sum())))
    names = ranks[0][0]
    avg = np.mean([r for _, r in ranks], axis=0)
    return names, avg
