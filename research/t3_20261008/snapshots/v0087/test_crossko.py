import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import numpy as np,json
from pathlib import Path
from crossko import CrossKO
rng=np.random.default_rng(45);raw=rng.poisson(2,(120,12));wt=np.log1p(raw*10000/raw.sum(1)[:,None])
records=[dict(gene=g,sample_unit=g+str(e),unit_kind="synthetic",control=wt[:60],ko=wt[60:].copy()) for g in ['a','b','held'] for e in range(2)];priors={g:rng.normal(size=6) for g in ['a','b','held','new']}
m=CrossKO(states=3,min_cells=5).fit_atlas(wt).fit_interventions(records,priors,'held');p=m.predict('held');out,ix=m.emit(wt,p,mode='combined',locked_zero=0);assert out.shape==wt.shape and (out[:,0]==0).all();assert np.max(abs(np.expm1(out.astype(float)).sum(1)-10000))<.01
# Poison heldout outcomes: fitted coefficients and outputs must not change.
for r in records:
 if r['gene']=='held':r['ko'][:]=9999
m2=CrossKO(states=3,min_cells=5).fit_atlas(wt).fit_interventions(records,priors,'held');assert np.array_equal(m.coef,m2.coef);assert np.array_equal(out,m2.emit(wt,m2.predict('held'),mode='combined',locked_zero=0)[0]);assert 'held' not in m.training_genes
huge={**p,'delta':np.full_like(p['delta'],1e6)};assert np.isfinite(m.emit(wt,huge)[0]).all()
for method in ['nearest','mean','ridge']:assert np.isfinite(m.predict('new',method)['delta']).all()
try:m.predict('missing');raise AssertionError('Must reject missing prior')
except ValueError:pass
z=dict(status='PASS',scope='Synthetic implementation tests only; no biological validation',checks=['Heldout KO poisoning leaves fit/output byte-identical','Holdout gene omitted from training','Missing gene identity prior blocks prediction','Finite closure10000','Locked knockout zero','Composition/within joint output shapes','Three identity model controls'])
Path(__file__).with_name('CROSSKO_TESTS.json').write_text(json.dumps(z,indent=2));print(z)
