import run as r
import json,numpy as np
from types import SimpleNamespace as NS
from backtest import Board
out=r.ROOT/'matched_shuffle';out.mkdir(exist_ok=False);g=r.V.panel(r.BOARD)
base,_=r.recipe.run_interp(NS(board=r.BOARD,left='E8.25_late:8.25',right='E9.5:9.5',target=8.75,n=5872,seed=20261008,label='celltype',carrier='left',C=2.,geometry='aniso',zero_preserve=False))
B=np.load(r.ROOT/'dev/global_B.npy');perm=np.random.default_rng(20261009).permutation(500);q=base.copy();q.X=r.reg(base.X,base.obs.celltype,B[np.ix_(perm,perm)],.75);check=r.audit(base,q);path=out/'matched_shuffle075.h5ad';q.write_h5ad(path)
result={'purpose':'Fixed winner-matched negative control AFTER choice frozen, not used to change selection','selection_sha256':r.sha(r.ROOT/'SELECTION.json'),'blend':.75,'shuffle_seed':20261009,'candidate_sha256':r.sha(path),'checks':check,'evaluations':[]}
T=r.V.load_stage('E8.75',g);L=r.V.load_stage('E8.25_late',g)
for seed in [0,1,2]:
 b=Board('T2',g,T,L,seed);raw=b.raw(q);sk=b.skills(raw);result['evaluations'].append({'seed':seed,'raw':raw,'skills':sk});(out/'RESULT.json').write_text(json.dumps(result,indent=2));print(seed,sk,flush=True)
