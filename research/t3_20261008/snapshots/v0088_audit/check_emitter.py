import sys,json
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
ROOT=Path('/workspace/shared/t3_v87_restored');RUN=Path('/workspace/shared/t3_v88_optimization_20261008')
sys.path[:0]=[str(ROOT),str(RUN)]
from crossko_hurdle_v2 import CrossKOHurdle
from emitter_v88 import emit,detection_propensity
rng=np.random.default_rng(912)
c=rng.gamma(2,2,(240,8));c[rng.random(c.shape)<.35]=0;c[:,0]+=1
X=np.log1p(c/c.sum(1)[:,None]*10000).astype('float32')
m=CrossKOHurdle(states=3,min_cells=10).fit_atlas(X)
nul={'delta':np.zeros((3,8,22)), 'composition':np.zeros(3), 'support':np.ones(3,bool)}
report={}
for res,cond in [(0,0),(1,0),(0,1),(1,1)]:
 k=f'{res}{cond}';Y,ix=emit(m,X,nul,mode='combined',residual=res,conditional=cond)
 assert np.array_equal(Y,X) and np.array_equal(ix,np.arange(len(X)))
 r={key:v.copy() for key,v in nul.items()};r['delta'][:,1,:-1]=.15;r['delta'][:,1,-1]=.1;r['delta'][:,2,:-1]=-.2;r['delta'][:,2,-1]=-.1
 Y,ix=emit(m,X,r,mode='within',residual=res,conditional=cond)
 assert np.isfinite(Y).all() and (Y>=0).all();mass_error=float(abs(np.expm1(Y.astype(float)).sum(1)-10000).max());assert mass_error<.01
 # unchanged genes differ only by shared closure factor; zero pattern must stay exact.
 cols=[0,3,4,5,6,7];a=np.expm1(X[:,cols].astype(float));b=np.expm1(Y[:,cols].astype(float));assert np.array_equal(a==0,b==0)
 ratios=np.divide(b,a,out=np.full_like(a,np.nan),where=a>0);err=float(np.nanmax(np.nanmax(ratios,axis=1)-np.nanmin(ratios,axis=1)));assert err<2e-6
 Y2,ix2=emit(m,X,r,mode='within',residual=res,conditional=cond);assert np.array_equal(Y,Y2)
 report[k]={'null_exact':True,'deterministic':True,'row_mass_max_error':mass_error,'null_genes_shared_closure_spread':err}
lab=np.zeros(len(X),int);P=detection_propensity(m,X,lab)
XX=X.copy();XX[:,3]*=2 # retain binary labels for gene3, change own PC contribution only
PP=detection_propensity(m,XX,lab)
report['own_gene_subtraction_max_error']=float(abs(P[:,3]-PP[:,3]).max())
assert report['own_gene_subtraction_max_error']<1e-5
print(json.dumps(report,indent=2));Path('/workspace/shared/t3_v88_independent_audit/EMITTER_TESTS.json').write_text(json.dumps(report,indent=2))
