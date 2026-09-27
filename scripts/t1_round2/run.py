"""Complete immutable batch runs with locked full-panel official scoring."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
import argparse,json,pickle,subprocess,sys,time,traceback,signal
from pathlib import Path
import numpy as np
import anndata as ad
from .common import Context,ROOT,OLD,sha,dump,dense,write_matrix,indexed
from .models import fit,predict,load_old,OLD as PREVIOUS
from scripts.t1_five.models import predict as old_predict

SHARED=ROOT/'artifacts/t1_round2/T1-ROUND2-20260928-v1/shared'


def model_save(p,m):
    with p.open('xb') as f:pickle.dump(m,f,protocol=5)


def lock_components(c):
    files={}
    for lane in ['n1density','o1mass']:
        for name in ['report_model.pkl','final_model.pkl','report_prediction.h5ad','SCORER.json']:
            p=ROOT/PREVIOUS/lane/name;files[str(p.relative_to(ROOT))]=sha(p)
    dump(c.run/'COMPONENT_LOCK.json',files)
    return files


def prepare(c):
    locks=lock_components(c);records=[]
    for lane,ver in [('n1density','v0024'),('o1mass','v0027')]:
        # Validate the immutable input/code snapshots of the actual fitted component.
        oldrun=ROOT/PREVIOUS/lane;oldlock=json.loads((oldrun/'INPUT_LOCK.json').read_text())
        for name,digest in oldlock['inputs'].items():
            p=ROOT/name
            if name.startswith('scripts/t1_five/'):p=oldrun/'code'/Path(name).name
            elif name.startswith('configs/t1_five/'):p=oldrun/'code/design.json'
            if sha(p)!=digest:raise ValueError('old component input drift '+name)
        for future in [False,True]:
            raw=c.xb[c.rows] if future else c.xa[c.te[0]];types=c.tb[c.rows] if future else c.ta[c.te[0]]
            fallback=c.legacy if future else dense(ad.read_h5ad(OLD/'intermediates/arm_B_qpos_zero.h5ad').X)
            actual=ad.read_h5ad(indexed(ver)[1] if future else oldrun/'report_prediction.h5ad')
            model=load_old(lane,future);pred,_=old_predict(model,raw,types,fallback)
            np.testing.assert_array_equal(pred,dense(actual.X));records.append({'component':ver,'future':future,'exact':True,'shape':list(pred.shape)})
    prior=json.loads((ROOT/PREVIOUS/'shared/READY.json').read_text())
    for x in prior['paths'].values():assert sha(ROOT/x['path'])==x['sha256']
    p=ROOT/PREVIOUS/'n1density/SCORER.json';prior['paths']['baseline_scores']={'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
    prior.update(components_exact=records,current_best='v0024',second_component='v0027',component_lock=locks)
    dump(c.run/'READY.json',prior);c.finish(role='actual scored component exact reproduction')
    print('COMPONENT AUDIT PASS',flush=True)


def score(c):
    ready=json.loads((SHARED/'READY.json').read_text())
    for f in ready['paths'].values():assert sha(ROOT/f['path'])==f['sha256']
    cmd=[sys.executable,'third_party/veckit/score_h5ad.py','--task','T1','--input',str(c.run/'report_prediction.h5ad'),'--target',str(ROOT/ready['paths']['target']['path']),'--reference',str(ROOT/ready['paths']['reference']['path']),'--seed',str(c.cfg['seed']),'--out',str(c.run/'SCORER.json')]
    with (c.run/'scorer.log').open('x') as log:
        proc=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'LD_LIBRARY_PATH':'/opt/anaconda3/lib','PYTHONPATH':str(ROOT/'third_party/veckit')})
        dump(c.run/'SCORER_PROCESS.json',{'pid':proc.pid,'command':cmd,'status':'RUNNING'})
        try:code=proc.wait(timeout=c.cfg['max_hours_per_route']*3600)
        except BaseException:
            proc.terminate()
            try:proc.wait(timeout=15)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
    dump(c.run/'SCORER_PROCESS.json',{'pid':proc.pid,'command':cmd,'exit_code':code,'status':'COMPLETED' if code==0 else 'FAILED'})
    if code:raise RuntimeError((c.run/'scorer.log').read_text()[-2000:])
    metrics=json.loads((c.run/'SCORER.json').read_text())['metrics']
    dump(c.run/'EVALUATION.json',{'model':metrics,'v0024_same_split':json.loads((ROOT/PREVIOUS/'n1density/SCORER.json').read_text())['metrics'],'v0027_same_split':json.loads((ROOT/PREVIOUS/'o1mass/SCORER.json').read_text())['metrics'],'scope':'all 32285 input genes; official internal metric defaults; released stage cell holdout repeatedly used; not future or embryo validation'})
    return metrics


def execute(c,lane):
    ready=json.loads((SHARED/'READY.json').read_text());dump(c.run/'REFERENCE_LOCK.json',ready)
    locks=lock_components(c)
    if locks!=ready['component_lock']:raise ValueError('component drift')
    fallback=dense(ad.read_h5ad(OLD/'intermediates/arm_B_qpos_zero.h5ad').X)
    m=fit(c.xa[c.tr[0]],c.ta[c.tr[0]],c.xb[c.tr[1]],c.tb[c.tr[1]],lane,c.cfg,False);model_save(c.run/'report_model.pkl',m)
    pred,details=predict(m,c.xa[c.te[0]],c.ta[c.te[0]],fallback)
    dump(c.run/'REPORT_OPERATOR.json',details);write_matrix(c.run/'report_prediction.h5ad',pred,details['predicted_types'],c.genes)
    del m,pred,fallback
    dump(c.run/'PROGRESS.json',{'stage':'REPORT_FIT_COMPLETE'})
    m=fit(c.xa,c.ta,c.xb,c.tb,lane,c.cfg,True);model_save(c.run/'final_model.pkl',m)
    pred,details=predict(m,c.xb[c.rows],c.tb[c.rows],c.legacy);dump(c.run/'FINAL_OPERATOR.json',details)
    del m
    with (c.run/'final_model.pkl').open('rb') as f:m=pickle.load(f)
    replay,_=predict(m,c.xb[c.rows],c.tb[c.rows],c.legacy);np.testing.assert_array_equal(pred,replay)
    dump(c.run/'MODEL_REPLAY.json',{'status':'PASS','exact_equal':True,'full_shape':pred.shape,'model_sha256':sha(c.run/'final_model.pkl')})
    c.save(lane,pred,c.run/'final_model.pkl',details['predicted_types']);del m,pred,replay
    dump(c.run/'PROGRESS.json',{'stage':'FINAL_COMPLETE_SCORER_PENDING'})
    metrics=score(c);c.finish(route=lane,report_scorer='EXECUTED',model_replay='PASS',metrics=metrics,full_source_shapes=[c.xa.shape,c.xb.shape])
    print('COMPLETE',lane,c.candidates,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('lane');ap.add_argument('--run-dir',type=Path,required=True);a=ap.parse_args()
    c=Context(a.run_dir)
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('frozen six hour limit')));signal.alarm(int(c.cfg['max_hours_per_route']*3600))
    try:
        if a.lane=='prepare':prepare(c)
        elif a.lane in c.cfg['round2']['lanes']:execute(c,a.lane)
        else:raise ValueError(a.lane)
    except BaseException as e:
        dump(c.run/'FAILURE.json',{'error':repr(e),'traceback':traceback.format_exc(),'candidates':c.candidates});raise


if __name__=='__main__':main()
