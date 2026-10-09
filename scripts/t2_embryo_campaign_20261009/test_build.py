"""Synthetic-only engineering tests; never a biological validation."""
import tempfile, pathlib, shutil,sys,os
import numpy as np, anndata as ad, pandas as pd
from build import build

def test_matched():
    with tempfile.TemporaryDirectory(prefix='t2_synthetic_',dir='/tmp') as td:
        p=pathlib.Path(td)
        for f in ['index.json','T2__embryo__val_interp.genes.txt']:shutil.copy(pathlib.Path(os.environ.get('VE_DATA',str(pathlib.Path(__file__).resolve().parents[2]/'data')))/f,p/f)
        genes=(p/'T2__embryo__val_interp.genes.txt').read_text().splitlines();rng=np.random.default_rng(10)
        for i,n in enumerate(['E6.75','E7.25','E8.0']):
            X=rng.gamma(1.,.5+i*.1,(5200,len(genes))).astype('float32');X[rng.random(X.shape)<.3]=0
            a=ad.AnnData(X,obs=pd.DataFrame({'celltype':np.resize(['a','b','c'],5200)},index=[f'{n}_c{j}' for j in range(5200)]),var=pd.DataFrame(index=genes))
            a.obsm['spatial_3D']=rng.normal(size=(5200,3)).astype('float32');a.write_h5ad(p/f'{n}.h5ad')
        e,_,_=build(p,'e3_original');l,_,_=build(p,'legacy_weight');r,_,_=build(p,'raw_matched');r2,_,_=build(p,'raw_matched')
        for a in [l,r]:
            assert np.array_equal(a.obsm['spatial_3D'],e.obsm['spatial_3D'])
            assert list(a.obs_names)==list(e.obs_names)
            assert np.isfinite(a.X).all() and np.min(a.X)>=0 and a.shape==(5000,498)
        assert not np.array_equal(e.X,l.X),'Shrink definition must differ'
        assert not np.array_equal(l.X,r.X),'Carrier residual must differ'
        assert np.array_equal(r.X,r2.X),'Deterministic replay'
        print('PASS: shapes, finite, nonnegative, fixed geometry/rows, distinct weight and carrier, deterministic arrays. SYNTHETIC ONLY')
if __name__=='__main__':test_matched()
