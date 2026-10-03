"""Frozen, full-matrix source comparison; never accesses embryo target truth."""
from pathlib import Path
import csv
import hashlib
import json
import sys

import anndata as ad
import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'third_party/veckit')]
from t3_autoresearch import retained_model
from t3_next.source_roles import require_response_role
from common import core_metrics as cm

OUT = ROOT / 'reports/t3_sparse_response_20261003'
RUN = ROOT / 'artifacts/t3_sparse_response_20261003'
WEIGHTS = np.array([.30, .25, .25, .12, .08])
KEYS = ['de_score', 'de_direction', 'severity_abs', 'mmd_u', 'variogram']

def dense(x):
    return x.toarray() if hasattr(x, 'toarray') else np.asarray(x)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(p, x):
    Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def fit_log_multiplier(control, delta):
    raw = np.expm1(np.asarray(control, dtype=float))
    target = np.maximum(control.mean(0, dtype=float) + delta, 0)
    lo = np.full(control.shape[1], -np.log(2.))
    hi = -lo
    for _ in range(40):
        mid = (lo + hi) / 2
        mean = np.log1p(raw * np.exp(mid)).mean(0)
        lower = mean < target
        lo = np.where(lower, mid, lo)
        hi = np.where(lower, hi, mid)
    result = (lo + hi) / 2
    result[np.all(control == 0, axis=0)] = 0
    return result

def emit(base, beta, strength):
    return np.log1p(np.expm1(np.asarray(base, dtype=float)) * np.exp(beta * strength)).astype('float32')

def measure(pred, truth, ctrl):
    severity, r2 = cm.severity_slope(pred, truth, ctrl)
    vals = [cm.de_score(pred, truth, ctrl)['score'], cm.de_direction(pred, truth, ctrl),
            abs(severity), cm.mmd_unbiased(pred, truth, seed=0), cm.variogram_score(pred, truth, seed=0)]
    return {**{k: float(v) if np.isfinite(v) else None for k,v in zip(KEYS, vals)},
            'severity_r2': float(r2) if np.isfinite(r2) else None,
            'mean_response_mse': float(np.mean((pred.mean(0, dtype=float)-truth.mean(0, dtype=float))**2)),
            'density': float(np.mean(pred > 0))}

def load():
    manifest = json.loads((ROOT / 'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json').read_text())
    require_response_role(manifest, ROOT, 'SIGNED_RESPONSE')
    record = manifest['files']['expression']
    assert sha(ROOT / record['path']) == record['sha256']
    final = json.loads((ROOT / 'reports/t3_autoresearch_20261002/FINAL_CHECK.json').read_text())
    assert sha(ROOT / 'scripts/t3_autoresearch/retained_model.py') == final['model_sha256']
    a = ad.read_h5ad(ROOT / record['path'])
    assert a.shape == (5454,500) and a.obs.model_input.all()
    labels = a.obs.condition.astype(str).to_numpy()
    x = dense(a.X)
    ctrl = x[labels == 'ctrl']
    cfg = json.loads((ROOT / 'artifacts/autoresearch/t3-20261002-v1/PROVENANCE.json').read_text())
    ep = ROOT / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert sha(ep) == cfg['embedding_sha256']
    emb = np.load(ep)
    ei = {g:i for i,g in enumerate(emb['genes'])}
    def predict(genes, query):
        train = {'genes':np.array(genes), 'E':emb['embedding'][[ei[g] for g in genes]],
                 'Y':np.array([x[labels == g].mean(0)-ctrl.mean(0) for g in genes])}
        return retained_model.predict(train, {'genes':np.array([query]),'E':emb['embedding'][[ei[query]]]})[0]
    return x, labels, ctrl, cfg, predict

def main():
    assert not (OUT / 'SELECTION.json').exists(), 'Immutable selection exists'
    x, labels, ctrl, cfg, predict = load()
    names = ['identity','additive','s025','s050','s100']
    strengths = {'s025':.25,'s050':.5,'s100':1.}
    rows = []
    ranks = []
    for g in cfg['split']['train']:
        delta = predict([h for h in cfg['split']['train'] if h != g], g)
        beta = fit_log_multiplier(ctrl, delta)
        predictions = {'identity':ctrl.copy(), 'additive':np.maximum(ctrl+delta,0).astype('float32')}
        predictions.update({k:emit(ctrl,beta,v) for k,v in strengths.items()})
        values = []
        for name in names:
            result = measure(predictions[name], x[labels == g], ctrl)
            rows.append({'split':'development_LOPO','gene':g,'method':name,**result})
            values.append([np.nan if result[k] is None else result[k] for k in KEYS])
        values = np.array(values)
        available = np.all(np.isfinite(values), axis=0)
        signed = values * np.array([-1,-1,1,1,1])
        rank = np.column_stack([rankdata(signed[:,j]) for j in np.flatnonzero(available)])
        ranks.append(rank @ (WEIGHTS[available]/WEIGHTS[available].sum()))
        print('development',g,flush=True)
    avg = np.mean(ranks, axis=0)
    chosen = min(strengths,key=lambda k:(avg[names.index(k)],strengths[k]))
    selection = {'method':chosen,'strength':strengths[chosen],
                 'mean_weighted_rank':dict(zip(names,avg.tolist())),
                 'better_than_both_controls':bool(avg[names.index(chosen)] < min(avg[:2])),
                 'selected_before_test':True,'target_truth_used':False,
                 'design_sha256':sha(OUT/'DESIGN.md')}
    dump(OUT/'SELECTION.json',selection)
    for g in cfg['split']['test']:
        delta = predict(cfg['split']['train'],g)
        beta = fit_log_multiplier(ctrl,delta)
        predictions = {'identity':ctrl.copy(),'additive':np.maximum(ctrl+delta,0).astype('float32'),chosen:emit(ctrl,beta,strengths[chosen])}
        for name,pred in predictions.items():
            rows.append({'split':'historical_test','gene':g,'method':name,**measure(pred,x[labels==g],ctrl)})
        print('historical_test',g,flush=True)
    with (OUT/'FULL_MATRIX_METRICS.tsv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
    delta = predict(sum(cfg['split'].values(),[]),'Gata4')
    np.testing.assert_allclose(delta,np.load(ROOT/'artifacts/t3_autoresearch_delivery_20261003/MODEL_RESPONSE.npy').reshape(-1),atol=1e-12,rtol=0)
    beta=fit_log_multiplier(ctrl,delta)
    np.save(RUN/'LOG_MULTIPLIER.npy',beta)
    summary={}
    for split in ['development_LOPO','historical_test']:
        summary[split]={}
        for method in names:
            rr=[r for r in rows if r['split']==split and r['method']==method]
            if rr:
                summary[split][method]={k:{'mean':float(np.mean(v)) if v else None,'n':len(v)} for k in KEYS+['mean_response_mse','density'] if (v:=[r[k] for r in rr if r[k] is not None]) or True}
    dump(OUT/'SUMMARY.json',summary)
    dump(OUT/'EVALUATION_COMPLETE.json',{'selection':selection,'multiplier_sha256':sha(RUN/'LOG_MULTIPLIER.npy'),'metrics_sha256':sha(OUT/'FULL_MATRIX_METRICS.tsv'),'status':'COMPLETE'})
    print(json.dumps(selection),flush=True)

if __name__=='__main__':
    main()
