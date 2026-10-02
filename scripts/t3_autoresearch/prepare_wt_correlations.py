"""Approved WT-only within-state gene covariates; not causal KO effects."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
from scipy.io import mmread
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2]


def main():
    source=ROOT/'artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data'
    manifest=json.loads((source.parent/'MANIFEST.json').read_text())
    expected={f['path']:f['sha256'] for f in manifest['files']}
    hashes={}
    for name in ['state_input_counts.mtx','state_input_genes.tsv','metadata_cells_sanitized.tsv']:
        h=hashlib.sha256()
        with (source/name).open('rb') as f:
            for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
        hashes[name]=h.hexdigest()
        assert hashes[name]==expected['data/'+name]
    cfg=json.loads((ROOT/'artifacts/t3_priority_six_20260930/CONFIG.json').read_text())
    genes=sum(cfg['split'].values(),[])+['Gata4']
    panel=(ROOT/'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    names=pd.read_csv(source/'state_input_genes.tsv',sep='\t').gene.astype(str).tolist()
    meta=pd.read_csv(source/'metadata_cells_sanitized.tsv',sep='\t',dtype=str)
    assert len(meta)==68910 and (meta.stage=='E8.75').all()
    ix={g:i for i,g in enumerate(names)}
    chosen=list(dict.fromkeys(genes+panel))
    missing=[g for g in chosen if g not in ix]
    chosen=[g for g in chosen if g in ix]
    print('Reading full WT matrix for within-state covariance',flush=True)
    with threadpool_limits(limits=8):
        full=mmread(source/'state_input_counts.mtx').tocsr().astype('float32')
    assert full.shape==(27669,68910)
    total=np.asarray(full.sum(0)).ravel()
    x=full[[ix[g] for g in chosen]].toarray().T
    del full
    x=np.log1p(x*10000/np.maximum(total[:,None],1)).astype('float64')
    states=meta.state.to_numpy()
    within=x.copy()
    for state in sorted(set(states)):
        rows=states==state
        within[rows]-=within[rows].mean(0)
    meso=np.array([bool(re.search('mesench|mesoderm|cardio|endocard|epicard|sclerotome|dermomyotome|somitic',s.lower())) for s in states])
    arrays={}
    ci={g:i for i,g in enumerate(chosen)}
    for key,xx in [('global',x-x.mean(0)),('within_state',within),('mesoderm_within_state',within[meso])]:
        a=xx[:,[ci[g] for g in genes]]
        covariance=a.T@xx/max(len(xx)-1,1)
        corr=covariance/np.maximum(np.std(a,axis=0,ddof=1)[:,None]*np.std(xx,axis=0,ddof=1)[None,:],1e-8)
        matrix=np.zeros((len(genes),len(panel)))
        for j,g in enumerate(panel):
            if g in ci:matrix[:,j]=corr[:,ci[g]]
        arrays[key]=matrix.astype('float32')
    dest=ROOT/'artifacts/t3_autoresearch_features_20261002'
    out=dest/'WT_CORRELATIONS.npz'
    assert not out.exists()
    np.savez_compressed(out,genes=genes,panel=panel,**arrays)
    receipt={'role':'WT-only regulatory-context features; observational correlations, not identified causal response',
             'source_cells':len(meta),'mesoderm_cells':int(meso.sum()),'missing_genes':missing,
             'hashes':hashes,'features_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
             'heldout_KO_used':False,'normalization':'log1p CP10000; group-centered by state for within-state features'}
    (dest/'CORRELATION_PROVENANCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
