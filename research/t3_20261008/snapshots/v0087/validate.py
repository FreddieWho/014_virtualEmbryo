from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,anndata as ad
P=Path(__file__).parent;D=Path('/workspace/shared/virtual_embryo_data');w=ad.read_h5ad(D/'E9.5.h5ad');k=ad.read_h5ad(D/'E9.5_mab21l2_ko.h5ad');sec=pd.to_numeric(k.obs.section).to_numpy();gi=list(w.var_names).index('Mab21l2');results=[]
for fold in range(2):
 z=np.load(P/f'model_fold{fold}.npz');assert not np.intersect1d(z['WT_train'],z['WT_test']).size;assert not np.intersect1d(z['KO_train'],z['KO_test']).size;assert not np.intersect1d(np.unique(sec[z['KO_train']]),np.unique(sec[z['KO_test']])).size;assert len(z['features'])==250
 for f in sorted(P.glob(f'fold{fold}_*.h5ad')):
  a=ad.read_h5ad(f);assert a.shape==(7449,500);assert a.obs_names.is_unique;assert np.array_equal(a.var_names,w.var_names);assert np.isfinite(a.X).all() and (a.X>=0).all();assert (a.X[:,gi]==0).all();assert np.max(abs(np.expm1(a.X.astype(float)).sum(1)-10000))<.01;assert np.isfinite(a.obsm['spatial_3D']).all();assert np.array_equal(a.obsm['spatial_3D'],np.asarray(w.obsm['spatial_3D'])[z['base_indices']]);results.append(f.name)
 assert np.isclose(z['WT_proportions'].sum(),1) and np.isclose(z['KO_proportions'].sum(),1)
h=json.loads((P/'INPUT_HASHES.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in h.items());m=pd.read_csv(P/'metrics.csv');assert len(m)==32;assert np.isfinite(m.select_dtypes('number').to_numpy()).all();assert set(m.metric_panel)=={'full_panel','alignment_heldout_genes'}
result=dict(status='PASS',artifacts_checked=len(results),checks=['Disjoint WT cells','Disjoint KO cells and sections','WT training gene halves250','Unique generated row IDs despite duplicate source KO names','500 genes ordered','Finite nonnegative','Mab21l2 zero','Panel closure10000 tolerance0.01','Coordinate carrier equality','All input/source/protocol hashes unchanged','32 finite raw metric rows'],caveat='Local structure checks, not official portal contract or biological validation')
(P/'VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
