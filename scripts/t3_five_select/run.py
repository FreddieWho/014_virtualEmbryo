import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import argparse,json,traceback,sys,shutil
from pathlib import Path
import numpy as np
from .common import Context,ROOT,dump,sha,save_model,read_model,diagnostics,dense
from .models import train_all,predict
from scripts.t3_next.five import Hurdle,source
from scripts.t3_next.five_ops import bounded_add
from scripts.t3_next.repair_ops import decode_rate

HPATH=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v2/n2hurdle/hurdle_model.pkl'
GPATH=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v1/o2shrink/target_rate.npy'


def prepare(c):
    saved=read_model(HPATH);h=Hurdle();h.encoder=saved['encoder'];h.positive=saved['positive'];cols=saved['cols'];rate=np.load(GPATH)
    source(c)
    expected={HPATH:'f6037b5caf4d44f38c4210b80916f1a9387e386301fbc313746bf38e44860e23',GPATH:'b3c1fbd191bc73d51d579b52c556f0c3fff9b2b94bcd38e704d5d76a9b103839'}
    for p,digest in expected.items():assert sha(p)==digest
    for folder in [HPATH.parent,GPATH.parent]:
        lock=json.loads((folder/'INPUT_LOCK.json').read_text())
        for name,digest in lock['inputs'].items():
            p=ROOT/name
            if name.startswith('scripts/t3_next/'):p=folder/'code'/Path(name).name
            elif name.startswith('configs/t3_next/'):p=folder/'code/design.json'
            assert sha(p)==digest,(name,'source lock mismatch')
    a=c.x[c.rows][:,[c.gi]];z=c.coords[c.rows];t=c.plabels
    d=h.predict(np.zeros_like(a),z,t)[0]-h.predict(a,z,t)[0]
    rebuilt=c.base.copy();rebuilt[:,cols]=bounded_add(c.base[:,cols],d,c.cfg['hurdle_strength'])
    np.testing.assert_array_equal(rebuilt,c.best)
    rebuilt=np.asarray(decode_rate(c.base,rate),np.float32);rebuilt[:,c.gi]=0;np.testing.assert_array_equal(rebuilt,c.graph)
    dump(c.run/'COMPONENT_AUDIT.json',{'status':'PASS','H_exact':True,'G_exact':True,'model_files':{str(p.relative_to(ROOT)):digest for p,digest in expected.items()},'source_review':'SOURCE_LOCK.json'})
    return h,rate,cols


def evaluate(c,models,train_ids,block,cols):
    cfg=c.cfg;records=[];excluded=[];test=np.flatnonzero(c.blocks==block);factual={}
    for lane in ['r3bag','r4spline','r5local']:
        m=models[lane]['model'];a=c.x[test][:,[c.gi]];z=c.coords[test];t=c.labels[test]
        if isinstance(m,list):p=np.mean([v.predict(a,z,t)[0] for v in m],axis=0)
        elif lane=='r5local':p=m.predict(a,z,t,test)[0]
        else:p=m.predict(a,z,t)[0]
        factual[lane]=float(np.mean((p-c.x[test][:,cols])**2))
    for typ in sorted(set(c.labels[test])):
        train=train_ids[c.labels[train_ids]==typ];te=test[c.labels[test]==typ]
        reason=None
        if len(train)<cfg['min_train_type']:reason='train_type_below_80'
        else:
            low,high=np.quantile(c.x[train,c.gi],cfg['activity_quantiles']);lo=te[c.x[te,c.gi]<=low];hi=te[c.x[te,c.gi]>=high]
            if high<=low or min(len(lo),len(hi))<cfg['min_test_group']:reason='no_activity_separation_or_small_test_group'
        if reason:excluded.append({'type':typ,'reason':reason,'test_cells':len(te)});continue
        intervention=float(np.median(c.x[train[c.x[train,c.gi]<=low],c.gi]));a=c.x[hi][:,[c.gi]];b=np.full_like(a,intervention);z=c.coords[hi];t=c.labels[hi];base=c.x[hi][:,cols]
        truth=c.x[lo][:,cols].mean(0);arms={'identity':base}
        hm=dict(models['r1active'],lane='H');arms['H']=predict(hm,base,a,b,z,t,hi)
        for lane,m in models.items():arms[lane]=predict(m,base,a,b,z,t,hi)
        records.append({'type':typ,'train_cells':len(train),'high_cells':len(hi),'low_cells':len(lo),'responses':len(cols),'intervention':intervention,'mse':{lane:float(np.mean((out.mean(0)-truth)**2)) for lane,out in arms.items()}})
    weighted={}
    if records:
        weights=[r['high_cells']*r['responses'] for r in records]
        weighted={lane:float(np.average([r['mse'][lane] for r in records],weights=weights)) for lane in records[0]['mse']}
    return {'status':'EXECUTED' if records else 'NOT_TESTABLE_NO_ELIGIBLE_GROUPS','block':block,'train_cells':len(train_ids),'test_cells':len(test),'eligible_groups':records,'excluded_groups':excluded,'weighted_mean_group_mse':weighted,'factual_mse':factual,'denominator':'group means weighted by high-group cells times 499 response genes','limit':'observational single-specimen WT; not matched KO accuracy','target_KO_scorer':'NOT_RUN_NO_MATCHED_GATA4_TARGET'}


def run(c):
    h,rate,cols=prepare(c);ids=np.flatnonzero(np.isin(c.blocks,c.cfg['train_blocks']))
    localh=Hurdle().fit(c.x[ids][:,[c.gi]],c.coords[ids],c.labels[ids],c.x[ids][:,cols],c.cfg['ridge_alpha'])
    models=train_all(c,ids,localh,rate,cols,c.run/'local_models')
    dev=evaluate(c,models,ids,c.cfg['development_block'],cols);dump(c.run/'DEVELOPMENT.json',dev)
    scores=dev['weighted_mean_group_mse'];families=c.cfg['selection'];rank={}
    for family in ['source','learned']:
        lanes=families[family+'_family'];rank[family]=sorted(lanes,key=lambda lane:(scores.get(lane,float('inf')),lanes.index(lane)))
    selected=rank['source'][:1]+rank['learned'][:2]
    dump(c.run/'SELECTED.json',{'selected':selected,'rankings':rank,'design_sha256':sha(c.run/'code/design.json'),'development_sha256':sha(c.run/'DEVELOPMENT.json'),'audit_opened':False,'criterion':families['criterion'],'development_status':dev['status']})
    selection_sha=sha(c.run/'SELECTED.json');print('selection locked',selected,flush=True)
    audit=evaluate(c,models,ids,c.cfg['audit_block'],cols);audit['selection_sha256_before_open']=selection_sha;dump(c.run/'AUDIT_BLOCK.json',audit)
    del models,localh
    full=train_all(c,np.arange(len(c.x)),h,rate,cols,c.run/'full_models')
    outputs={};evidence={}
    import anndata as ad,csv
    sys.path.insert(0,str(ROOT/'docs/batch3/interfaces'))
    from virtual_embryo_tools.contract_io import write_candidate_from_parent,validate_h5ad_contract
    with (ROOT/'submissions/INDEX.tsv').open() as f:oldrows=[r for r in csv.DictReader(f,delimiter='\t') if r['board']=='T3:gata4']
    # Compare each old candidate once while retaining only five compact output arrays.
    for lane,m in full.items():
        folder=c.run/lane;folder.mkdir();a=c.x[c.rows][:,[c.gi]];out=c.base.copy();out[:,cols]=predict(m,c.base[:,cols],a,np.zeros_like(a),c.coords[c.rows],c.plabels,c.rows);out[:,c.gi]=0
        replay=c.base.copy();replay[:,cols]=predict(read_model(c.run/'full_models'/f'{lane}.pkl'),c.base[:,cols],a,np.zeros_like(a),c.coords[c.rows],c.plabels,c.rows)
        np.testing.assert_array_equal(out,replay);np.save(folder/'prediction.npy',out);outputs[lane]=out
        checks=diagnostics(c.best,out,np.asarray(c.parent.obsm['spatial_3D']),c.gi,c.cfg);checks['noop_best']=bool(np.array_equal(out,c.best));checks['duplicates']=[]
        path=folder/'research.h5ad'
        write_candidate_from_parent(parent_path=c.bestpath,output_path=path,expression=out,row_names=list(c.parent.obs_names),normalization='log_normalized',parent_sha256=c.bestrow['sha256'],metadata_updates={'ve_t3_five_select':json.dumps({'lane':lane,'model_sha256':sha(c.run/'full_models'/f'{lane}.pkl'),'target_used':False,'registration':'research only unless indexed'})})
        contract=validate_h5ad_contract(path,task='T3',board='gata4',scorer_lock=ROOT/'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',parent_path=c.bestpath,parent_sha256=c.bestrow['sha256']);dump(folder/'CONTRACT.json',contract)
        checks.update(model_replay='PASS',contract=contract['status'],shape=list(out.shape),research_sha256=sha(path));evidence[lane]=checks
        print('full inference complete',lane,flush=True)
    for row in oldrows:
        old=ad.read_h5ad(ROOT/row['path']);x=dense(old.X)
        for lane,out in outputs.items():
            if np.array_equal(out,x) and list(old.obs_names)==list(c.parent.obs_names) and list(old.var_names)==c.genes:evidence[lane]['duplicates'].append(row['version'])
    for i,lane in enumerate(c.cfg['lanes']):
        for other in c.cfg['lanes'][:i]:
            if np.array_equal(outputs[lane],outputs[other]):evidence[lane]['duplicates'].append(other)
    eligible={lane:r['status']=='PASS' and r['contract']=='PASS' and not r['noop_best'] and not r['duplicates'] for lane,r in evidence.items()}
    final=[]
    for family,n in [('source',1),('learned',2)]:
        valid=[lane for lane in rank[family] if eligible[lane]]
        if len(valid)<n:raise RuntimeError(f'Insufficient engineering-eligible {family} routes; no parameter rescue')
        final+=valid[:n]
    assert sha(c.run/'SELECTED.json')==selection_sha
    dump(c.run/'FINAL_SELECTION.json',{'selected':final,'preaudit_selection':selected,'selection_sha256':selection_sha,'engineering_eligibility':eligible,'audit_did_not_change_selection':True})
    for lane,r in evidence.items():dump(c.run/lane/'CHECKS.json',r)
    for lane in final:
        child=Context(c.run/lane/'registered');shutil.copy2(c.run/'full_models'/f'{lane}.pkl',child.run/'model.pkl')
        dump(child.run/'PARENT_RUN_LOCK.json',{'run':str(c.run.relative_to(ROOT)),'files':{str(p.relative_to(ROOT)):sha(p) for p in [c.run/'SELECTED.json',c.run/'FINAL_SELECTION.json',c.run/'AUDIT_BLOCK.json',c.run/'COMPONENT_AUDIT.json',c.run/lane/'CHECKS.json']}})
        candidate=child.save(lane,outputs[lane]);assert candidate is not None
        child.finish('CANDIDATE_READY');c.candidates.append(candidate)
    return c.finish('FIVE_EXECUTED_THREE_READY',routes=evidence,selected=final,selection_sha256=selection_sha,development='DEVELOPMENT.json',audit='AUDIT_BLOCK.json')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);args=ap.parse_args();c=Context(args.run)
    try:run(c)
    except BaseException as e:
        dump(c.run/'FAILURE.json',{'status':'FAILED','error':str(e),'traceback':traceback.format_exc(),'blocks_submission':False});raise
if __name__=='__main__':main()
