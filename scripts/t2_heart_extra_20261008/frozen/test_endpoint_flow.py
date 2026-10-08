import numpy as np,pandas as pd,anndata as ad
from scipy.stats import rankdata
import endpoint_flow as ef

def fixture():
 rng=np.random.default_rng(789);raw=rng.gamma(1,1,(12,500));x=np.log1p(raw/raw.sum(1,keepdims=True)*10000).astype('float32')
 a=ad.AnnData(x,obs=pd.DataFrame({'celltype':['V-CM']*4+['A-CM']*4+['Peri']*4},index=[str(i) for i in range(12)]));a.obsm['spatial_3D']=rng.normal(size=(12,3));common=np.arange(0,500,2)
 ranks=(rankdata(rng.normal(size=(3,250)),axis=1)-1)/249
 m={'median_deltas':{'V-CM':rng.normal(0,.1,500),'Peri':rng.normal(0,.1,500)},'endpoint':{'common_indices':common,'endpoint_ranks':ranks},'early_time':8.75,'late_time':9.5,'target_time':10.5,'endpoint_time':14.5}
 return a,m

def test_conservation():
 a,m=fixture();base=ef.recipe(a,m['median_deltas']);common=m['endpoint']['common_indices'];other=np.setdiff1d(np.arange(500),common)
 for mode in ['endpoint','endfree','endperm']:
  x,audit=ef.predict(a,m,mode)
  assert np.isfinite(x).all() and x.min()>=0
  assert np.array_equal(x[:,other],base[:,other]);assert np.array_equal(x[8:],base[8:])
  np.testing.assert_allclose(np.expm1(x.astype(float)).sum(1),np.expm1(base.astype(float)).sum(1),rtol=1e-6)
  np.testing.assert_array_equal(x,ef.predict(a,m,mode)[0])
  assert audit['eligible_cm_rows']==8 and abs(audit['endpoint_weight']-.104)<1e-12
  assert abs(audit['source_delta_coefficient']-.64/.75)<1e-12
  assert audit['external_gene_missing_not_changed'] and audit['non_cm_recipe_exact']

def test_endfree_orphan_identity():
 a,m=fixture();x,_=ef.predict(a,m,'endfree');np.testing.assert_allclose(x[4:8],a.X[4:8],rtol=1e-6,atol=1e-6)

def test_zero_horizon_identity():
 a,m=fixture();m['target_time']=m['late_time'];m['median_deltas']={};x,_=ef.predict(a,m,'endpoint');np.testing.assert_allclose(x,a.X,rtol=1e-6,atol=1e-6)

def test_cardiac_orphan_is_not_frozen():
 a,m=fixture();x,_=ef.predict(a,m,'endpoint');assert np.max(np.abs(x[4:8]-a.X[4:8]))>1e-3

if __name__=='__main__':
 test_conservation();test_endfree_orphan_identity();test_zero_horizon_identity();test_cardiac_orphan_is_not_frozen();print('4 synthetic endpoint operator tests PASS; these are not biological validation metrics')
