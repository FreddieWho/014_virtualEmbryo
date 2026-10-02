"""Pure WT state features for perturbation genes, no KO outcomes or score input."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.io import mmread
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]


def main():
    d = ROOT / 'artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data'
    lock = json.loads((d.parent/'MANIFEST.json').read_text())
    expected = {r['path']:r['sha256'] for r in lock['files']}
    hashes = {}
    for name in ['state_input_counts.mtx','state_input_genes.tsv','metadata_cells_sanitized.tsv']:
        h=hashlib.sha256()
        with (d/name).open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
        hashes[name]=h.hexdigest()
        assert hashes[name]==expected['data/'+name]
    cfg=json.loads((ROOT/'artifacts/t3_priority_six_20260930/CONFIG.json').read_text())
    genes=sum(cfg['split'].values(),[])+['Gata4']
    names=pd.read_csv(d/'state_input_genes.tsv',sep='\t').gene.astype(str).tolist()
    meta=pd.read_csv(d/'metadata_cells_sanitized.tsv',sep='\t',dtype=str)
    assert len(meta)==68910 and (meta.stage=='E8.75').all()
    index={g:i for i,g in enumerate(names)}
    assert all(g in index for g in genes)
    print('Reading full approved WT matrix; retaining27 gene features',flush=True)
    with threadpool_limits(limits=8):
        full=mmread(d/'state_input_counts.mtx').tocsr().astype('float32')
    assert full.shape==(27669,68910)
    total=np.asarray(full.sum(0)).ravel()
    x=full[[index[g] for g in genes]].toarray().T
    del full
    x=np.log1p(x*10000/np.maximum(total[:,None],1))
    states=sorted(set(meta.state))
    means=np.array([x[meta.state.to_numpy()==s].mean(0) for s in states]).T
    detection=np.array([(x[meta.state.to_numpy()==s]>0).mean(0) for s in states]).T
    dest=ROOT/'artifacts/t3_autoresearch_features_20261002'
    dest.mkdir(exist_ok=True)
    assert not (dest/'WT_STATE_FEATURES.npz').exists()
    np.savez_compressed(dest/'WT_STATE_FEATURES.npz',genes=genes,states=states,means=means,detection=detection)
    record={'role':'WT-only gene expression/detection by state; gene features, not KO responses',
            'source_cells':len(meta),'hashes':hashes,'normalization':'log1p counts per10000 per cell',
            'features_sha256':hashlib.sha256((dest/'WT_STATE_FEATURES.npz').read_bytes()).hexdigest(),
            'protected_target_truth_used':False,'limitations':'embryo WT features for adult fibroblast source; observational only'}
    (dest/'PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))


if __name__=='__main__':main()
