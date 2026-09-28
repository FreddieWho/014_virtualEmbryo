import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
import argparse,json,traceback,signal
from pathlib import Path
import numpy as np
from .common import Context,ROOT,dump,sha,save_model,read_model
from .models import restore,responses,apply,predict
from scripts.t3_next.five import Hurdle,source
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.repair_ops import decode_rate

SHARED=ROOT/'artifacts/t3_three/T3-THREE-20260929-v1/shared'
HPATH=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v2/n2hurdle/hurdle_model.pkl'
GPATH=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v1/o2shrink/target_rate.npy'


def prepare(c):
    cfg=c.cfg['three'];saved=read_model(HPATH);h=restore(saved);rate=np.load(GPATH);cols=saved['cols']
    # Existing trained source component remains subject to its current role checks.
    source(c)
    prior=json.loads((ROOT/'artifacts/t3_round2/T3-ROUND2-20260928-v1/shared/COMPONENT_AUDIT.json').read_text())
    for p,digest in prior['model_files'].items():assert sha(ROOT/p)==digest
    for folder in [HPATH.parent,GPATH.parent]:
        lock=json.loads((folder/'INPUT_LOCK.json').read_text())
        for name,digest in lock['inputs'].items():
            path=ROOT/name
            if name.startswith('scripts/t3_next/'):path=folder/'code'/Path(name).name
            if name.startswith('configs/t3_next/'):path=folder/'code/design.json'
            assert sha(path)==digest,(name,'old component lock drift')
    a=c.x[c.rows][:,[c.gi]];d,p,i=responses(h,a,np.zeros_like(a),c.coords[c.rows],c.plabels)
    rebuilt=c.base.copy();rebuilt[:,cols]=bounded_add(c.base[:,cols],d,cfg['hurdle_strength'])
    np.testing.assert_array_equal(rebuilt,c.best)
    g=np.asarray(decode_rate(c.base,rate),np.float32);g[:,c.gi]=0;np.testing.assert_array_equal(g,c.graph)
    np.savez_compressed(c.run/'TARGET_COMPONENTS.npz',delta=d,probability=p,intensity=i,rate=rate)
    dump(c.run/'COMPONENT_AUDIT.json',{'status':'PASS','H_exact':True,'G_exact':True,'shape':list(rebuilt.shape),'model_files':{str(p.relative_to(ROOT)):sha(p) for p in [HPATH,GPATH]},'midpoint_sum_maxabs':float(np.max(np.abs(d-p-i))),'source_review':'SOURCE_LOCK.json','legacy_unsubmitted_stack_not_used_for_selection':True})
    records=[];excluded=[];folds=[]
    for fold in np.unique(c.blocks):
        tr=c.blocks!=fold;te=~tr
        hm=Hurdle().fit(c.x[tr][:,[c.gi]],c.coords[tr],c.labels[tr],c.x[tr][:,cols],cfg['ridge_alpha'])
        save_model(c.run/f'fold{fold}.pkl',hm)
        pred,_=hm.predict(c.x[te][:,[c.gi]],c.coords[te],c.labels[te]);y=c.x[te][:,cols]
        folds.append({'fold':int(fold),'train_cells':int(tr.sum()),'test_cells':int(te.sum()),'response_entries':int(y.size),'factual_mse':float(np.mean((pred-y)**2))})
        for t in sorted(set(c.labels[te])):
            train=np.flatnonzero(tr&(c.labels==t));test=np.flatnonzero(te&(c.labels==t))
            if len(train)<cfg['local_min_train_type']:
                excluded.append({'fold':int(fold),'type':t,'reason':'train_type_below_80','test_cells':len(test)});continue
            low,high=np.quantile(c.x[train,c.gi],cfg['activity_quantiles'])
            lo=test[c.x[test,c.gi]<=low];hi=test[c.x[test,c.gi]>=high]
            if high<=low or min(len(lo),len(hi))<cfg['local_min_test_group']:
                excluded.append({'fold':int(fold),'type':t,'reason':'no_activity_separation_or_small_test_group','test_cells':len(test)});continue
            intervention=float(np.median(c.x[train[c.x[train,c.gi]<=low],c.gi]))
            aa=c.x[hi][:,[c.gi]];z=c.coords[hi];labels=c.labels[hi];raw=c.x[hi][:,cols]
            dd,pp,ii=responses(hm,aa,np.full_like(aa,intervention),z,labels)
            hh=np.asarray(bounded_add(raw,dd,cfg['hurdle_strength']),np.float32)
            arms={'identity':raw,'H':hh,'ungated_stack':decode_rate(hh,rate[cols])}
            for lane in cfg['lanes']:arms[lane]=apply(lane,raw,dd,pp,ii,z,labels,aa[:,0]>intervention,rate[cols],cfg)[0]
            truth=c.x[lo][:,cols].mean(0)
            mse={name:float(np.mean((out.mean(0)-truth)**2)) for name,out in arms.items()}
            records.append({'fold':int(fold),'type':t,'train_cells':len(train),'high_test_cells':len(hi),'low_test_cells':len(lo),'responses':len(cols),'intervention_activity':intervention,'mse':mse})
        print('fold complete',int(fold),flush=True)
    weighted={}
    if records:
        weights=np.array([r['high_test_cells']*r['responses'] for r in records])
        weighted={name:float(np.average([r['mse'][name] for r in records],weights=weights)) for name in records[0]['mse']}
    dump(c.run/'LOCAL_DIAGNOSTICS.json',{'status':'EXECUTED' if records else 'NOT_TESTABLE_NO_ELIGIBLE_GROUPS','full_WT_cells':len(c.x),'full_panel':500,'modeled_responses':len(cols),'factual_folds':folds,'eligible_groups':records,'excluded_groups':excluded,'weighted_mean_group_mse':weighted,'denominator':'high-group cells times 499 responses; not independent biological replicates','limit':'observational high-to-low WT groups, incomplete conditional coverage, confounded; NOT matched KO accuracy','target_KO_scorer':'NOT_RUN_NO_MATCHED_GATA4_TARGET'})
    c.finish('SHARED_COMPLETE',folds=4)


def execute(c,lane):
    audit=json.loads((SHARED/'COMPONENT_AUDIT.json').read_text());assert audit['status']=='PASS'
    for name,digest in audit['model_files'].items():assert sha(ROOT/name)==digest
    dump(c.run/'COMPONENT_LOCK.json',{'shared':str(SHARED.relative_to(ROOT)),'files':{str(p.relative_to(ROOT)):sha(p) for p in [SHARED/'COMPONENT_AUDIT.json',SHARED/'LOCAL_DIAGNOSTICS.json',SHARED/'SOURCE_LOCK.json',HPATH,GPATH]}})
    m={'lane':lane,'hurdle':read_model(HPATH),'rate':np.load(GPATH),'cols':np.flatnonzero(np.arange(500)!=c.gi),'cfg':c.cfg['three']}
    save_model(c.run/'model.pkl',m);out,details=predict(m,c);replay,_=predict(read_model(c.run/'model.pkl'),c)
    np.testing.assert_array_equal(out,replay)
    dump(c.run/'MODEL_REPLAY.json',{'status':'PASS','shape':list(out.shape),'model_sha256':sha(c.run/'model.pkl'),'exact_equal':True})
    dump(c.run/'OPERATOR.json',details)
    evaluation=json.loads((SHARED/'LOCAL_DIAGNOSTICS.json').read_text());dump(c.run/'EVALUATION.json',evaluation)
    candidate=c.save(lane,out)
    if candidate is None:raise RuntimeError('three submittable files required; engineering gate/no-op must be investigated')
    c.finish('CANDIDATES_READY',route=lane,full_model_replay='PASS',scientific_verdict='INCONCLUSIVE_NEEDS_MATCHED_KO_TRUTH')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('lane');ap.add_argument('--run-dir',type=Path,required=True);a=ap.parse_args();c=Context(a.run_dir)
    def timeout(*args):raise TimeoutError('frozen two-hour limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(int(c.cfg['three']['max_hours']*3600))
    try:
        if a.lane=='prepare':prepare(c)
        elif a.lane in c.cfg['three']['lanes']:execute(c,a.lane)
        else:raise ValueError(a.lane)
    except BaseException as e:
        dump(c.run/'FAILURE.json',{'error':repr(e),'traceback':traceback.format_exc(),'candidates':c.candidates});raise


if __name__=='__main__':main()
