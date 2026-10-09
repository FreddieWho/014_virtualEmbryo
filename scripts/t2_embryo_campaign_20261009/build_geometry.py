"""Geometry-only intervention on an explicitly hash-locked parent artifact."""
import argparse,json,hashlib,re
from pathlib import Path
import numpy as np
import anndata as ad
from scipy import sparse
from runtime import initialize
from geometry import interpolate_geometry,rms_radius

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--parent',required=True);p.add_argument('--parent-sha256',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();assert sha(a.parent)==a.parent_sha256,'Exact parent hash differs'
    outpath=Path(a.out)
    if outpath.exists():raise FileExistsError('Frozen artifact already exists')
    v,_=initialize(a.data);genes=v.panel('T2:embryo:val_interp');base=ad.read_h5ad(a.parent)
    assert list(base.var_names)==genes,'Parent panel order differs'
    L=v.load_stage('E7.25',genes);R=v.load_stage('E8.0',genes)
    assert 'celltype' in base.obs,'Need verified row labels for state transform'
    lookup={str(n):i for i,n in enumerate(L.obs_names)}
    source=[re.sub(r'__(?:r|dup)\d+$','',str(n)) for n in base.obs_names]
    assert all(n in lookup for n in source),'Cannot verify parent source rows in left stage'
    rows=np.array([lookup[n] for n in source]);lc=np.asarray(L.obsm['spatial_3D'])[rows,:3].astype(float)
    bc=np.asarray(base.obsm['spatial_3D'])[:,:3].astype(float)
    x=lc-lc.mean(0);y=bc-bc.mean(0);scale=float((x*y).sum()/(x*x).sum())
    residual=float(np.sqrt(np.mean(np.sum((y-scale*x)**2,axis=1)))/rms_radius(bc))
    assert scale>0 and residual<1e-5,f'Parent is not in left frame: residual={residual}'
    assert np.array_equal(np.asarray(base.obs.celltype.astype(str)),np.asarray(L.obs.celltype.astype(str))[rows]),'Source labels differ'

    coords,diag=interpolate_geometry(base.obsm['spatial_3D'],np.asarray(base.obs.celltype.astype(str)),L.obsm['spatial_3D'],np.asarray(L.obs.celltype.astype(str)),R.obsm['spatial_3D'],np.asarray(R.obs.celltype.astype(str)),1/3,target_rms=rms_radius(base.obsm['spatial_3D']))
    out=base.copy();out.obsm['spatial_3D']=coords.astype('float32')
    unchanged=(base.X-out.X).nnz==0 if sparse.issparse(base.X) else np.array_equal(np.asarray(base.X),np.asarray(out.X))
    assert unchanged and list(base.obs_names)==list(out.obs_names)
    prov={'mechanism':'proper-frame state-conditional Bures affine transport','parent_file':str(a.parent),'parent_sha256':a.parent_sha256,'expression_unchanged':unchanged,'rows_unchanged':True,'external_data':False,'protected_targets_read':False,'diagnostics':diag,'source_frame_check':{'scale':scale,'relative_rms_residual':residual,'all_row_names_and_labels_matched':True}}
    out.uns['campaign_geometry_provenance']=json.dumps(prov,sort_keys=True)
    outpath.parent.mkdir(parents=True,exist_ok=True);out.write_h5ad(outpath)
    ck=v.format_check(outpath,'T2:embryo:val_interp');result={'sha256':sha(outpath),'contract':ck,'provenance':prov};outpath.with_suffix('.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not ck['pass']:raise SystemExit(1)
if __name__=='__main__':main()
