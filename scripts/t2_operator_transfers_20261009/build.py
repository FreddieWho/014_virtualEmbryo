"""One-switch transfer of extrap source-library restoration to the E3 mean bridge.
Only released embryo inputs. Frozen source code is instrumented at two exact lines;
all original arithmetic before/after these locations is unchanged.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[k]='1'
from pathlib import Path
import sys,json,hashlib,types,argparse
import numpy as np
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];REPO=Path(os.environ.get('T2_TRANSFER_REPO',str(ROOT/'repo')));DATA=Path(os.environ.get('T2_EMBRYO_DATA','/workspace/shared/t2_campaign_data'))
sys.path.insert(0,str(REPO/'scripts/t2_embryo_campaign_20261009'))
from runtime import initialize
V,RUNTIME=initialize(DATA)
import t2_recipes as R
EXPECTED='e93d56f2130297f7c5b256e3e26fc072b8913766772b3ffcb2634f7a3fdbfdae'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def args(holdout=False):
 return NS(board='T2:embryo:val_interp',left='E6.75:6.75' if holdout else 'E7.25:7.25',right='E8.0:8.0',prev='E6.75:6.75',target=7.25 if holdout else 7.5,n=5000,seed=20261009 if holdout else 20261008,label='celltype',carrier='left' if holdout else 'baseline',base_n=5000,base_seed=20260821,bridge_seed=20260904,C=2.,geometry='logrms',zero_preserve=False)
def instrumented(a,restore=True,shuffle=False):
 code=(REPO/'scripts/vework/t2_recipes.py').read_text()
 anchor='    wmean = []\n'
 assert code.count(anchor)==1
 code=code.replace(anchor,'    source_X = X.copy()\n'+anchor)
 anchor='    out = make_submission(X, g, C2, names, prov)\n'
 assert code.count(anchor)==1
 replacement='''    touched = np.isin(lab, shared)
    lib0 = np.expm1(source_X).sum(1)
    if restore:
        E = np.expm1(X[touched]); lib1 = E.sum(1)
        target_lib = lib0[touched].copy()
        if shuffle:
            rng = np.random.default_rng(20261009)
            for state in shared:
                m = lab[touched] == state
                target_lib[m] = target_lib[m][rng.permutation(int(m.sum()))]
        E *= (target_lib / np.maximum(lib1, 1e-12))[:, None]
        X[touched] = np.log1p(E)
    diagnostics.update(source_X=source_X, touched=touched, source_library=lib0, unrounded_X=X.copy())
'''+anchor
 code=code.replace(anchor,replacement)
 mod=types.ModuleType('instrumented_recipes');mod.__file__=str(REPO/'scripts/vework/t2_recipes.py')
 diagnostics={};mod.__dict__.update(restore=restore,shuffle=shuffle,diagnostics=diagnostics)
 exec(compile(code,mod.__file__,'exec'),mod.__dict__)
 out,prov=mod.run_interp(a)
 return out,prov,diagnostics

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--holdout',action='store_true');a=ap.parse_args();dest=Path(a.out);dest.mkdir(parents=True,exist_ok=False)
 param=args(a.holdout);parent,pp=R.run_interp(param);parent.write_h5ad(dest/'parent.h5ad')
 if not a.holdout:assert sha(dest/'parent.h5ad')==EXPECTED,sha(dest/'parent.h5ad')
 identity,_,_=instrumented(param,False)
 assert np.array_equal(identity.X,parent.X) and np.array_equal(identity.obsm['spatial_3D'],parent.obsm['spatial_3D'])
 candidate,cp,d=instrumented(param);control,_,_=instrumented(param,True,True)
 t=d['touched'];got=np.expm1(candidate.X.astype(np.float64)).sum(1);rel=np.abs(got-d['source_library'])/np.maximum(d['source_library'],1e-12)
 assert np.max(rel[t])<1e-6
 assert np.array_equal(parent.X[~t],candidate.X[~t]);assert np.array_equal(parent.obsm['spatial_3D'],candidate.obsm['spatial_3D']);assert list(parent.obs_names)==list(candidate.obs_names)
 assert np.array_equal(parent.X==0,candidate.X==0)
 prov={'candidate_id':'v0023_e3_source_library' if not a.holdout else 'diagnostic_holdout','axis':'Restore each bridge-input carrier row own expm1 library after mean shift on shared states only','source_library':'baseline-carrier XB immediately before E3 mean bridge, not raw E7.25 and not endpoint quantiles','parent_sha256':sha(dest/'parent.h5ad'),'parent_identity':'byte-exact scored E3 (not original v0014)' if not a.holdout else 'released-stage plain-carrier holdout; exact three-stage parent unidentifiable','released_inputs':{n:sha(DATA/f'{n}.h5ad') for n in ['E6.75','E7.25','E8.0']},'source_commit':'9d30857b5e25610e40872e6f2cfce18941678eaa','recipe_sha256':sha(REPO/'scripts/vework/t2_recipes.py'),'runtime':RUNTIME,'threads':1,'protected_targets_read':False,'external_data':False,'touched_rows':int(t.sum()),'max_source_library_relative_error_float32':float(rel[t].max()),'max_source_library_relative_error_float64':float((np.abs(np.expm1(d['unrounded_X']).sum(1)[t]-d['source_library'][t])/np.maximum(d['source_library'][t],1e-12)).max()),'unchanged_geometry_rows_labels':True,'unchanged_orphans_and_zero_mask':True,'per_gene_marginals_preserved':False,'classifier_type_mass_preserved':False,'operator_off_exact_X':True,'mean_abs_change':float(np.abs(candidate.X-parent.X).mean())}
 candidate.uns['operator_transfer_provenance']=json.dumps(prov,sort_keys=True)
 name='candidate.h5ad' if a.holdout else 't2_emb_int__e3_libself__v0023.h5ad'
 candidate.write_h5ad(dest/name);control.write_h5ad(dest/'shuffle_control.h5ad')
 check=V.format_check(dest/name,param.board);assert check['pass']
 record={'artifact_path':str(dest/name),'sha256':sha(dest/name),'contract':check,'provenance':prov};(dest/'HANDOFF.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2),flush=True)
 if a.holdout:
  from backtest import Board
  g=V.panel(param.board);L=V.load_stage('E6.75',g);T=V.load_stage('E7.25',g)
  result={'fold':'E6.75+E8.0 -> E7.25','limit':'Plain carrier only; exact E3 three-stage matched holdout impossible without earlier released stage','proxy_not_server':True,'results':{}}
  for seed in [0,1,2]:
   B=Board('T2',g,T,L,seed=seed)
   for key,P in [('parent',parent),('source_library',candidate),('within_state_library_shuffle',control)]:
    raw=B.raw(P);skill=B.skills(raw);result['results'].setdefault(key,[]).append({'seed':seed,'raw':raw,'skill':skill});print(seed,key,skill,flush=True)
    (dest/'LOCAL_SCORES.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
