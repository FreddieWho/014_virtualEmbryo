"""Real CellOracle full-atlas run, retains cell-level native layers."""
import os
from pathlib import Path
from .common import ROOT,RUN,dump,sha,SEED

def run():
    for key,name in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('MPLCONFIGDIR','mpl'),('NUMBA_CACHE_DIR','numba')]:
        path=RUN/'runtime'/name;path.mkdir(exist_ok=True,parents=True);os.environ[key]=str(path)
    import numpy as np,pandas as pd,anndata as ad,celloracle as co
    from scipy.io import mmread
    from sklearn.decomposition import TruncatedSVD
    p=RUN/'native';p.mkdir(exist_ok=True)
    if (p/'COMPLETE.json').exists():
        receipt=__import__('json').loads((p/'COMPLETE.json').read_text())
        for f,h in receipt['outputs'].items():assert sha(p/f)==h
        return
    d=ROOT/'artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data'
    import json
    manifest=json.loads((d.parent/'MANIFEST.json').read_text())
    expected={item['path']:item['sha256'] for item in manifest['files']}
    for name in ['state_input_counts.mtx','state_input_genes.tsv','metadata_cells_sanitized.tsv']:
        assert sha(d/name)==expected['data/'+name],f'WT atlas input hash mismatch: {name}'
    genes=pd.read_csv(d/'state_input_genes.tsv',sep='\t').gene.astype(str).tolist()
    meta=pd.read_csv(d/'metadata_cells_sanitized.tsv',sep='\t',dtype=str)
    assert len(meta)==68910 and (meta.stage=='E8.75').all()
    print('READ_FULL_ATLAS',flush=True)
    x=mmread(d/'state_input_counts.mtx').T.tocsr().astype('float32')
    assert x.shape==(68910,27669)
    z=x.copy();z.data=np.log1p(z.data);sq=z.copy();sq.data**=2
    variance=np.asarray(sq.mean(0)).ravel()-np.asarray(z.mean(0)).ravel()**2
    panel=(ROOT/'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    import sys;sys.path.insert(0,str(ROOT/'scripts'))
    from t3_s1a_state_join import POSITIVE_MARKERS,NEGATIVE_MARKERS,_load_locked_celloracle_base_grn
    chosen=list(dict.fromkeys(panel+list(POSITIVE_MARKERS)+list(NEGATIVE_MARKERS)+['Gata4','Gata6','Ctnnb1']))
    chosen=[g for g in chosen if g in genes]
    for i in np.argsort(-variance,kind='mergesort'):
        if genes[i] not in chosen:chosen.append(genes[i])
        if len(chosen)==2000:break
    gmap={g:i for i,g in enumerate(genes)};counts=x[:,[gmap[g] for g in chosen]]
    obs=meta[['state','sample']].copy();obs.index=meta.cell.astype(str)
    a=ad.AnnData(X=counts,obs=obs,var=pd.DataFrame(index=chosen))
    log=counts.copy();log.data=np.log1p(log.data)
    a.obsm['X_pca']=TruncatedSVD(30,random_state=SEED).fit_transform(log)
    base,base_receipt=_load_locked_celloracle_base_grn(co)
    assert 'Gata4' in base.columns
    oracle=co.Oracle();oracle.import_anndata_as_raw_count(adata=a,cluster_column_name='state',embedding_name='X_pca')
    oracle.import_TF_data(TF_info_matrix=base);oracle.perform_PCA(n_components=30)
    oracle.knn_imputation(k=30,n_pca_dims=20,n_jobs=1)
    print('FIT_FULL_STATE_GRNS',flush=True)
    oracle.fit_GRN_for_simulation(GRN_unit='cluster',alpha=10,use_cluster_specific_TFdict=False,verbose_level=0)
    print('SIMULATE_GATA4',flush=True)
    oracle.simulate_shift(perturb_condition={'Gata4':0.0},GRN_unit='cluster',n_propagation=3,ignore_warning=True,clip_delta_X=True)
    np.save(p/'factual.npy',np.asarray(oracle.adata.layers['imputed_count'],dtype='float32'))
    np.save(p/'delta.npy',np.asarray(oracle.adata.layers['delta_X'],dtype='float32'))
    dump(p/'genes.json',chosen);meta.to_csv(p/'metadata.tsv',sep='\t',index=False)
    import pickle
    with (p/'coefficients.pkl').open('wb') as f:pickle.dump(oracle.coef_matrix_per_cluster,f)
    dump(p/'COMPLETE.json',{'status':'FULL_NATIVE_PASS','CellOracle':co.__version__,'input_shape':list(x.shape),'method_shape':list(a.shape),'base_grn':base_receipt,'config_sha256':sha(RUN/'CONFIG.json'),'outputs':{f:sha(p/f) for f in ['factual.npy','delta.npy','genes.json','metadata.tsv','coefficients.pkl']}})
    print('FULL_NATIVE_PASS',flush=True)

if __name__=='__main__':run()
