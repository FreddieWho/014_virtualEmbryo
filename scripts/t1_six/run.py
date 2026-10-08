import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import argparse,json,pickle,sys,subprocess,traceback,time
from pathlib import Path
import numpy as np
import anndata as ad
from .common import Context,ROOT,OLD,dense,dump,sha,write_matrix,indexed
from .models import SHARED,PARENTS,SEVEN,core_model,fit,predict
from scripts.t1_three.models import components
from scripts.t1_three.ops import joint_donors,mixture_indices


def persist(p,m):
    with p.open('xb') as f:pickle.dump(m,f,protocol=5)


def score_file(input_path,out_path,seed):
    cmd=[sys.executable,'third_party/veckit/score_h5ad.py','--task','T1','--input',str(input_path),'--target',str(TARGET),'--reference',str(REFERENCE),'--seed',str(seed),'--out',str(out_path)]
    with (Path(out_path).parent/(Path(out_path).stem+'.log')).open('x') as log:
        proc=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'LD_LIBRARY_PATH':'/opt/anaconda3/lib','PYTHONPATH':str(ROOT/'third_party/veckit')})
        try:code=proc.wait(timeout=6*3600)
        except BaseException:
            proc.terminate()
            try:proc.wait(timeout=15)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
    if code:raise RuntimeError(Path(out_path).parent/(Path(out_path).stem+'.log'))


TARGET=None;REFERENCE=None


def build_plans(c,scope,folder,ta,tb,za,zb,locks):
    """Exact OT plans, displacement fields and consistency distances per common type (train cells only)."""
    from sklearn.preprocessing import StandardScaler
    import warnings
    P={};common=sorted(set(ta)&set(tb))
    for typ in common:
        aa=np.asarray(za[ta==typ],dtype=np.float64);bb=np.asarray(zb[tb==typ],dtype=np.float64)
        scaler=StandardScaler().fit(np.vstack([aa,bb]));a=scaler.transform(aa);b=scaler.transform(bb)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            from .ops import exact_plan,plan_fields,consistency_distances
            plan,info=exact_plan(a,b)
        d_early,d_late,row_t,col_s=plan_fields(plan,a,b)
        cons_e,cons_l=consistency_distances(plan,a,b)
        sigma=float(np.median(np.concatenate([cons_e,cons_l])))
        P[typ]={'scaler':scaler,'dim':int(a.shape[1]),'d_early':d_early.astype(np.float32),'d_late':d_late.astype(np.float32),'early_train_std':a.astype(np.float32),'late_train_std':b.astype(np.float32),'cons_early':cons_e,'cons_late':cons_l,'sigma':sigma,'plan_info':info}
        print('plan',scope,typ,a.shape,b.shape,'row_res %.1e'%info['row_residual'],flush=True)
    with (folder/'plans.pkl').open('xb') as f:pickle.dump(P,f,protocol=5)
    locks[str((folder/'plans.pkl').relative_to(ROOT))]=sha(folder/'plans.pkl')
    return P


def prepare(c):
    global TARGET,REFERENCE
    locks={};audit=[]
    for lane in ['r2joint','r3mix']:
        for name in ['report_model.pkl','final_model.pkl','report_prediction.h5ad','SCORER.json']:
            path=PARENTS/lane/name;locks[str(path.relative_to(ROOT))]=sha(path)
        oldrun=PARENTS/lane
        for name,digest in json.loads((oldrun/'INPUT_LOCK.json').read_text())['inputs'].items():
            p=ROOT/name
            if name.startswith('scripts/t1_three/'):p=oldrun/'code'/Path(name).name
            elif name.startswith('scripts/t1_five/'):p=oldrun/'code_legacy'/Path(name).name
            elif name.startswith('scripts/t1_round2/'):p=oldrun/'code_round2'/Path(name).name
            elif name.startswith('configs/t1_three/'):p=oldrun/'code/design.json'
            assert sha(p)==digest,(name,'parent input drift')
    for name in ['report_model.pkl','report_prediction.h5ad','SCORER.json']:
        path=SEVEN/'n2covot'/name;locks[str(path.relative_to(ROOT))]=sha(path)
    prior=json.loads((ROOT/'artifacts/t1_three/T1-THREE-20260929-v1/shared/READY.json').read_text())
    for name in ['target','reference']:
        info=prior['paths'][name];assert sha(ROOT/info['path'])==info['sha256']
    TARGET=ROOT/prior['paths']['target']['path'];REFERENCE=ROOT/prior['paths']['reference']['path']
    for future in [False,True]:
        scope='final' if future else 'report';folder=c.run/scope;folder.mkdir();core=core_model(future)
        raw=c.xb[c.rows] if future else c.xa[c.te[0]];types=c.tb[c.rows] if future else c.ta[c.te[0]]
        fallback=c.legacy if future else dense(ad.read_h5ad(OLD/'intermediates/arm_B_qpos_zero.h5ad').X)
        mass,d,composition,density=components(core,raw,types,fallback);old=core['stack']['density'];z=old['svd'].transform(raw);weights=np.ones(len(raw))
        for typ,g in old['groups'].items():
            ix=np.flatnonzero(types==typ)
            if not len(ix):continue
            logits=g['classifier'].decision_function(g['scaler'].transform(z[ix]));logits-=np.median(logits);weights[ix]=np.exp(np.clip(logits,-old['cfg']['n1']['weight_log_cap'],old['cfg']['n1']['weight_log_cap']))
        donors=joint_donors(types,weights,composition);best=mass[donors];bt=types[donors]
        sides,rows=mixture_indices(types,types[composition],core['cfg']['three']['mixture_fraction_A'],core['cfg']['three']['mixture_seed']);backup=np.empty_like(best);backtypes=np.empty(len(best),dtype=types.dtype)
        for side,pool,pt in [(0,mass[d],types),(1,density[composition],types[composition])]:
            ix=sides==side;backup[ix]=pool[rows[ix]];backtypes[ix]=pt[rows[ix]]
        for version,lane,actual in [('v0035','r2joint',best),('v0036','r3mix',backup)]:
            p=indexed(version)[1] if future else PARENTS/lane/'report_prediction.h5ad';np.testing.assert_array_equal(actual,dense(ad.read_h5ad(p).X));audit.append({'version':version,'scope':scope,'exact':True,'shape':actual.shape})
        aids=np.arange(len(c.xa)) if future else c.tr[0];bids=np.arange(len(c.xb)) if future else c.tr[1]
        arrays={'mass':mass,'best':best,'backup':backup,'best_types':np.asarray(bt,dtype=str),'backup_types':np.asarray(backtypes,dtype=str),'best_donors':donors,'composition':composition,'weights':weights,'query_latent':z,'fallback':fallback,'early_latent':old['svd'].transform(c.xa[aids]),'late_latent':old['svd'].transform(c.xb[bids])}
        for name,array in arrays.items():p=folder/(name+'.npy');np.save(p,array);locks[str(p.relative_to(ROOT))]=sha(p)
        build_plans(c,scope,folder,ta=c.ta[aids],tb=c.tb[bids],za=arrays['early_latent'],zb=arrays['late_latent'],locks=locks)
        print('full parent reconstruction and cache PASS',scope,flush=True)
        del arrays,mass,best,backup,density,core,fallback,raw
    refs={};refs_folder=c.run/'shared'/'refs';refs_folder.mkdir(parents=True,exist_ok=True)
    for version,path in [('v0035',PARENTS/'r2joint'/'report_prediction.h5ad'),('v0036',PARENTS/'r3mix'/'report_prediction.h5ad'),('v0038',SEVEN/'n2covot'/'report_prediction.h5ad')]:
        score_file(path,refs_folder/(version+'.json'),c.cfg['seed'])
        d=json.loads((refs_folder/(version+'.json')).read_text());assert d['meta']['genes']==32285;refs[version]=d['metrics']
        print('reference rescored (current env)',version,refs[version],flush=True)
    dump(c.run/'READY.json',{'paths':prior['paths'],'current_best':'v0051','skeleton_parent':'v0035','component_audit':audit,'reference_rescore_current_env':refs,'science':'same released-stage report; no hidden future truth'})
    dump(c.run/'CACHE_LOCK.json',locks);c.finish(role='scored v0035/v0036 exact reconstruction, immutable full-panel cache and plans, same-env reference rescore')


def score(c):
    ready=json.loads((SHARED/'READY.json').read_text())
    target=ROOT/ready['paths']['target']['path'];reference=ROOT/ready['paths']['reference']['path']
    cmd=[sys.executable,'third_party/veckit/score_h5ad.py','--task','T1','--input',str(c.run/'report_prediction.h5ad'),'--target',str(target),'--reference',str(reference),'--seed',str(c.cfg['seed']),'--out',str(c.run/'SCORER.json')]
    with (c.run/'scorer.log').open('x') as log:
        proc=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'LD_LIBRARY_PATH':'/opt/anaconda3/lib','PYTHONPATH':str(ROOT/'third_party/veckit')});dump(c.run/'SCORER_PROCESS.json',{'pid':proc.pid,'command':cmd,'status':'RUNNING'})
        try:code=proc.wait(timeout=c.cfg['max_hours_per_route']*3600)
        except BaseException:
            proc.terminate()
            try:proc.wait(timeout=15)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
    dump(c.run/'SCORER_PROCESS.json',{'pid':proc.pid,'command':cmd,'exit_code':code,'status':'COMPLETED' if code==0 else 'FAILED'})
    if code:raise RuntimeError((c.run/'scorer.log').read_text()[-1800:])
    d=json.loads((c.run/'SCORER.json').read_text());assert d['meta']['genes']==32285
    dump(c.run/'EVALUATION.json',{'model':d['metrics'],'reference_same_env':ready['reference_rescore_current_env'],'scope':'all 32285 input genes, official internal defaults; repeatedly used cell holdout, not future validation; references re-scored under the current env for same-env comparison'})
    return d['metrics']


def execute(c,lane):
    lock=json.loads((SHARED/'CACHE_LOCK.json').read_text())
    for name,digest in lock.items():assert sha(ROOT/name)==digest,(name,'frozen cache drift')
    dump(c.run/'COMPONENT_LOCK.json',lock)
    for future in [False,True]:
        tag='final' if future else 'report';m=fit(c,lane,future);persist(c.run/(tag+'_model.pkl'),m);out,details=predict(m,c);dump(c.run/(tag.upper()+'_OPERATOR.json'),details)
        if future:
            with (c.run/'final_model.pkl').open('rb') as f:reloaded=pickle.load(f)
            replay,replay_details=predict(reloaded,c);np.testing.assert_array_equal(out,replay);dump(c.run/'MODEL_REPLAY.json',{'status':'PASS','exact_equal':True,'full_shape':out.shape,'model_sha256':sha(c.run/'final_model.pkl')});del replay,reloaded
            # Keep a complete research output even when engineering gates reject registration.
            write_matrix(c.run/'full_prediction.h5ad',out,details['predicted_types'],c.genes,list(c.parent.obs_names))
            c.save(lane,out,c.run/'final_model.pkl',details['predicted_types'])
        else:write_matrix(c.run/'report_prediction.h5ad',out,details['predicted_types'],c.genes)
        del m,out
        dump(c.run/'PROGRESS.json',{'stage':tag.upper()+'_COMPLETE'})
    metrics=score(c);c.finish(route=lane,report_scorer='EXECUTED',model_replay='PASS',metrics=metrics,full_source_shapes=[c.xa.shape,c.xb.shape]);print('COMPLETE',lane,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('lane');ap.add_argument('--run-dir',type=Path,required=True);a=ap.parse_args();c=Context(a.run_dir)
    try:
        if a.lane=='prepare':prepare(c)
        elif a.lane in c.cfg['six']['lanes']:execute(c,a.lane)
        else:raise ValueError(a.lane)
    except BaseException as e:dump(c.run/'FAILURE.json',{'error':repr(e),'traceback':traceback.format_exc(),'candidates':c.candidates});raise
if __name__=='__main__':main()
