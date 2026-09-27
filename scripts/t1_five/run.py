"""Full-data fit, report-scenario scoring and final prediction for T1 five routes."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
import argparse,json,pickle,signal,subprocess,sys,traceback,time
from pathlib import Path
import numpy as np
import anndata as ad
from .common import Context,ROOT,OLD,CONFIG,sha,dump,dense,write_matrix
from .models import fit,predict,baseline

SHARED=ROOT/'artifacts/t1_five/T1-FIVE-20260927-v1/shared'


def save_model(path,model):
    with path.open('xb') as f:pickle.dump(model,f,protocol=5)


def prepare(c):
    a=c.xa[c.tr[0]];b=c.xb[c.tr[1]];ta=c.ta[c.tr[0]];tb=c.tb[c.tr[1]];x=c.xa[c.te[0]];types=c.ta[c.te[0]]
    old=ad.read_h5ad(OLD/'intermediates/arm_B_qpos_zero.h5ad');expected=dense(old.X)
    rebuilt=baseline(a,ta,b,tb,x,types,x)
    if not np.array_equal(rebuilt,expected):raise ValueError('report baseline mismatch, maxabs '+str(np.max(np.abs(rebuilt-expected))))
    # Verify the current server-selected prediction is precisely the inspected operator.
    full=baseline(c.xa,c.ta,c.xb,c.tb,c.xb[c.rows],c.tb[c.rows],dense(c.ancestor.X))
    if not np.array_equal(full,c.base):raise ValueError('v0023 baseline mismatch, maxabs '+str(np.max(np.abs(full-c.base))))
    target=OLD/'intermediates/pseudo_target_e95_outer.h5ad';reference=OLD/'intermediates/reference_e85_train.h5ad'
    for p,y in [(target,c.xb[c.te[1]]),(reference,a)]:
        d=ad.read_h5ad(p)
        if list(d.var_names)!=c.genes or not np.array_equal(dense(d.X),y):raise ValueError('reference/target cached mismatch')
    paths={'baseline':OLD/'intermediates/arm_B_qpos_zero.h5ad','target':target,'reference':reference,'baseline_scores':OLD/'metrics/scorer_B_qpos_zero.json'}
    dump(c.run/'READY.json',{'status':'PASS','report_baseline_exact':True,'final_v0023_exact':True,'paths':{k:{'path':str(v.relative_to(ROOT)),'sha256':sha(v)} for k,v in paths.items()},'scorer_seed':c.cfg['seed'],'full_panel':32285,'report_target_only_released_E95':True})
    c.finish(role='baseline identity audit; not a new candidate')
    print('READY: report baseline and full v0023 exactly reproduced',flush=True)


def score(c):
    ready=json.loads((SHARED/'READY.json').read_text())
    for f in ready['paths'].values():
        if sha(ROOT/f['path'])!=f['sha256']:raise ValueError('report inputs drift')
    p=c.run/'report_prediction.h5ad';out=c.run/'SCORER.json'
    cmd=[sys.executable,'third_party/veckit/score_h5ad.py','--task','T1','--input',str(p),'--target',str(ROOT/ready['paths']['target']['path']),'--reference',str(ROOT/ready['paths']['reference']['path']),'--seed',str(c.cfg['seed']),'--out',str(out)]
    with (c.run/'scorer.log').open('x') as log:
        proc=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'LD_LIBRARY_PATH':'/opt/anaconda3/lib','PYTHONPATH':str(ROOT/'third_party/veckit')})
        dump(c.run/'SCORER_PROCESS.json',{'pid':proc.pid,'command':cmd,'started':time.time(),'status':'RUNNING'})
        try:
            code=proc.wait(timeout=c.cfg['max_hours_per_route']*3600)
        except BaseException:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=15)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
    if code:raise RuntimeError('scorer failed: '+(c.run/'scorer.log').read_text()[-2000:])
    dump(c.run/'SCORER_PROCESS.json',{'pid':proc.pid,'command':cmd,'status':'COMPLETED','exit_code':code,'finished':time.time()})
    metrics=json.loads(out.read_text())['metrics'];base=json.loads((ROOT/ready['paths']['baseline_scores']['path']).read_text())['metrics']
    dump(c.run/'EVALUATION.json',{'model':metrics,'v0023_rule_same_split':base,'denominator':'all 32285 input genes; 3357 prediction cells, 3411 released E9.5 report targets; official scorer internal metrics retain locked defaults','scope':'cell-holdout report scenario; training saw other E9.5 cells, not independent future/embryo validation','future_E105_scoring':'NOT_RUN_NO_TRUTH'})
    print('scorer complete',c.run.name,flush=True)
    return metrics


def execute(c,lane):
    ready=json.loads((SHARED/'READY.json').read_text());dump(c.run/'REFERENCE_LOCK.json',ready)
    a=c.xa[c.tr[0]];b=c.xb[c.tr[1]];ta=c.ta[c.tr[0]];tb=c.tb[c.tr[1]]
    raw=c.xa[c.te[0]];types=c.ta[c.te[0]]
    fallback=dense(ad.read_h5ad(ROOT/ready['paths']['baseline']['path']).X)
    m=fit(a,ta,b,tb,lane,c.cfg,False);save_model(c.run/'report_model.pkl',m)
    query={t:a[ta==t].mean(0) for t in set(ta)}
    pred,details=predict(m,raw,types,fallback,query);dump(c.run/'REPORT_OPERATOR.json',details)
    if lane=='n3borrow':dump(c.run/'TYPE_HOLDOUT_REPORT.json',m['leave_type_out'])
    write_matrix(c.run/'report_prediction.h5ad',pred,types,c.genes)
    dump(c.run/'PROGRESS.json',{'stage':'REPORT_PREDICTION_COMPLETE','genes':pred.shape[1],'rows':pred.shape[0]})
    del a,b,m,pred,raw,fallback,query
    # The final fit and prediction never ingest scorer output or hidden future data.
    m=fit(c.xa,c.ta,c.xb,c.tb,lane,c.cfg,True);save_model(c.run/'final_model.pkl',m)
    query={t:c.xb[c.tb==t].mean(0) for t in set(c.tb)}
    pred,details=predict(m,c.xb[c.rows],c.tb[c.rows],c.base,query);dump(c.run/'FINAL_OPERATOR.json',details)
    if lane=='n3borrow':dump(c.run/'TYPE_HOLDOUT_FINAL.json',m['leave_type_out'])
    # Replay serialization on the complete prediction before registering anything.
    del m
    with (c.run/'final_model.pkl').open('rb') as f:reloaded=pickle.load(f)
    replay,_=predict(reloaded,c.xb[c.rows],c.tb[c.rows],c.base,query)
    if not np.array_equal(pred,replay):raise ValueError('serialized full-panel replay mismatch')
    dump(c.run/'MODEL_REPLAY.json',{'status':'PASS','full_shape':pred.shape,'exact_equal':True,'model_sha256':sha(c.run/'final_model.pkl')})
    c.save(lane,pred,c.run/'final_model.pkl')
    dump(c.run/'PROGRESS.json',{'stage':'FINAL_PREDICTION_COMPLETE_SCORER_PENDING','candidates':c.candidates})
    del reloaded,replay,pred,query
    metrics=score(c)
    c.finish(route=lane,full_source_shapes=[c.xa.shape,c.xb.shape],report_scorer='EXECUTED',model_replay='PASS',metrics=metrics)
    print('ROUTE COMPLETE',lane,[(v['version']) for v in c.candidates],flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('route',choices=['prepare','n1density','n2param','n3borrow','o1mass','o2rate']);ap.add_argument('--run-dir',type=Path,required=True);args=ap.parse_args()
    if args.run_dir.exists():raise FileExistsError(args.run_dir)
    c=None
    def timeout(*_):raise TimeoutError('fixed six-hour route bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(6*3600)
    try:
        c=Context(args.run_dir)
        if args.route=='prepare':prepare(c)
        else:execute(c,args.route)
    except Exception as e:
        dump(args.run_dir/'FAILURE.json',{'status':'FAILED_EXECUTION','error':str(e),'traceback':traceback.format_exc(),'partial_candidates':c.candidates if c else []})
        raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
