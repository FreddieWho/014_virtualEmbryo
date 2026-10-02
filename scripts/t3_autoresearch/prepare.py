"""Create a source-only T3 development benchmark; never read target KO truth."""
from pathlib import Path
import hashlib
import json
import sys

import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'artifacts/autoresearch/t3-20261002-v1'
sys.path.insert(0, str(ROOT / 'scripts'))
from t3_next.source_roles import require_response_role


def main():
    manifest_path = ROOT / 'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    require_response_role(manifest, ROOT, 'SIGNED_RESPONSE')
    source = ROOT / manifest['files']['expression']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['files']['expression']['sha256']
    embedding = ROOT / 'artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz'
    assert hashlib.sha256(embedding.read_bytes()).hexdigest() == 'acdb554d47989a4d8230fb8acc0fc7d20ec40e12086b56ef1715afb8fee11e0d'
    split = json.loads((ROOT / 'artifacts/t3_priority_six_20260930/CONFIG.json').read_text())['split']
    genes = split['train']
    a = ad.read_h5ad(source)
    a = a[a.obs.condition.astype(str).isin(['ctrl'] + genes)].copy()
    assert a.obs.model_input.all() and a.n_vars == 500
    x = a.X.toarray() if hasattr(a.X, 'toarray') else np.asarray(a.X)
    labels = a.obs.condition.astype(str).to_numpy()
    samples = a.obs['sample'].astype(str).to_numpy()
    ss = sorted(set(samples))
    ctrl = x[labels == 'ctrl'].mean(0)
    y = np.array([x[labels == g].mean(0) - ctrl for g in genes])
    n = np.array([np.sum(labels == g) for g in genes])
    sem2 = np.array([x[labels == g].var(0, ddof=1) / np.sum(labels == g) for g in genes])
    sample_ctrl = np.array([x[(labels == 'ctrl') & (samples == s)].mean(0) for s in ss])
    sample_y = np.array([[x[(labels == g) & (samples == s)].mean(0) - sample_ctrl[k] for k,s in enumerate(ss)] for g in genes])
    sample_n = np.array([[np.sum((labels == g) & (samples == s)) for s in ss] for g in genes])
    z = np.load(embedding)
    ix = {g:i for i,g in enumerate(z['genes'])}
    go = z['embedding'][[ix[g] for g in genes]]
    RUN.mkdir(parents=True, exist_ok=True)
    dest = RUN / 'development.npz'
    assert not dest.exists(), 'Frozen development data already exists'
    np.savez_compressed(dest, genes=genes, panel=a.var_names.to_numpy(dtype=str),
                        E=go, Y=y, N=n, SEM2=sem2, sample_Y=sample_y, sample_N=sample_n,
                        ctrl=ctrl, sample_ctrl=sample_ctrl)
    provenance = {'schema':'t3.autoresearch.source-lopo.v1', 'source_manifest':str(manifest_path.relative_to(ROOT)),
                  'source_sha256':manifest['files']['expression']['sha256'],
                  'embedding_sha256':hashlib.sha256(embedding.read_bytes()).hexdigest(),
                  'development_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
                  'split':split, 'scheme':'leave one of the original17 training perturbations out; all its cells and samples excluded',
                  'source_cells':len(a), 'output_genes':500, 'evaluation_precision':'float64 squared errors',
                  'metric':'100*(1-macro_MSE/baseline_MSE)', 'target':20,
                  'original_val_test':'excluded from optimization; historical test already examined in prior research, not pristine',
                  'limitations':['adult fibroblast, not embryo Gata4 validation','only17 development perturbations','adaptive CV overfitting risk','sample independence unknown']}
    (RUN / 'PROVENANCE.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps({'run':str(RUN),'cells':len(a),'genes':len(genes),'counts':n.tolist()}))


if __name__ == '__main__':
    main()
