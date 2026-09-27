import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import argparse,json,signal,traceback
from pathlib import Path
import numpy as np
import anndata as ad
from scipy.special import logit
from .common import Context,ROOT,dense,dump,sha,save_model,read_model,diagnostics
from .models import old_hurdle,hurdle_effect,LogisticHurdle,orth_fit,orth_prediction,predict_saved
from .ops import occupancy_decode,gene_shrink
from scripts.t3_next.five import source,type_baseline
from scripts.t3_next.five_ops import bounded_add,latent_predict
from scripts.t3_next.repair_ops import decode_rate
from scripts.t3_next.algorithms import fit_graph_comparator

SHARED=ROOT/'artifacts/t3_round2/T3-ROUND2-20260928-v1/shared'
HMODEL=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v2/n2hurdle/hurdle_model.pkl'
GRATE=ROOT/'artifacts/t3_next/T3-FIVE-20260927-v1/o2shrink/target_rate.npy'


def prepare(c):
    saved=read_model(HMODEL);h=old_hurdle(saved);cols=saved['cols'];delta=hurdle_effect(h,c)
    hr=c.base.copy();hr[:,cols]=bounded_add(c.base[:,cols],delta,.25)
    rate=np.load(GRATE);gr=np.asarray(decode_rate(c.base,rate),dtype=np.float32);gr[:,c.gi]=0
    np.testing.assert_array_equal(hr,c.best);np.testing.assert_array_equal(gr,c.graph)
    hg=decode_rate(hr,rate);gh=gr.copy();gh[:,cols]=bounded_add(gr[:,cols],delta,.25)
    mean=np.log1p((np.expm1(hr.astype(float))+np.expm1(gr.astype(float)))/2)
    variants={'anchor':c.base,'H_only':hr,'G_only':gr,'G_after_H':hg,'H_after_G':gh,'raw_mean':mean}
    records={}
    for name,x in variants.items():
        x[:,c.gi]=0
        records[name]=diagnostics(c.best,np.asarray(x,dtype=np.float32),np.asarray(c.parent.obsm['spatial_3D']),c.gi,c.cfg)
    dh=(hr-c.base).astype(float);dg=(gr-c.base).astype(float);eps=c.cfg['round2']['effect_epsilon']
    cosine=float(np.sum(dh*dg)/max(np.linalg.norm(dh)*np.linalg.norm(dg),1e-15))
    dump(c.run/'COMPONENT_AUDIT.json',{'status':'PASS','H_exact_reproduction':True,'G_exact_reproduction':True,'model_files':{str(HMODEL.relative_to(ROOT)):sha(HMODEL),str(GRATE.relative_to(ROOT)):sha(GRATE)},'arms':records,'response_cosine':cosine,'both_changed_entries':int(np.sum((np.abs(dh)>eps)&(np.abs(dg)>eps))),'order_changed_entries':int(np.count_nonzero(np.asarray(hg,dtype=np.float32)!=gh)),'claim':'prediction changes, not independently measured error correlation; no hidden KO oracle','scientific_verdict':'INCONCLUSIVE_NEEDS_INDEPENDENT_TRUTH','blocks_submission':False})
    # Diagnostic outputs are explicit controls, not additional route candidates.
    np.savez_compressed(c.run/'ABLATIONS.npz',**{k:np.asarray(v,dtype=np.float32) for k,v in variants.items()})
    c.finish('COMPONENT_AUDIT_PASS',H='v0048',G='v0046')


def final(c,lane,model,evaluation):
    model['lane']=lane;save_model(c.run/'model.pkl',model)
    out=predict_saved(model,c);replay=predict_saved(read_model(c.run/'model.pkl'),c)
    np.testing.assert_array_equal(out,replay)
    dump(c.run/'MODEL_REPLAY.json',{'status':'PASS','shape':out.shape,'exact_equal':True,'model_sha256':sha(c.run/'model.pkl')})
    dump(c.run/'EVALUATION.json',evaluation)
    c.save(lane,out)
    return c.finish('CANDIDATES_READY' if c.candidates else 'COMPUTED_NO_CANDIDATE',route=lane,scientific_verdict='INCONCLUSIVE_NEEDS_INDEPENDENT_TRUTH',full_model_replay='PASS')


def n1stack(c):
    audit=json.loads((SHARED/'COMPONENT_AUDIT.json').read_text())
    for name,digest in audit['model_files'].items():assert sha(ROOT/name)==digest
    model={'hurdle':read_model(HMODEL),'rate':np.load(GRATE)}
    dump(c.run/'COMPONENT_LOCK.json',{'audit':str(SHARED/'COMPONENT_AUDIT.json'),'sha256':sha(SHARED/'COMPONENT_AUDIT.json'),'parents':['v0048','v0046'],'primary':'G_after_H','weights':'both original full strength; no post-audit tuning'})
    return final(c,'n1stack',model,audit)


def n2orth(c):
    cfg=c.cfg['round2'];cols=np.flatnonzero(np.arange(500)!=c.gi);evals=[]
    for fold in np.unique(c.blocks):
        tr=c.blocks!=fold;te=~tr
        m=orth_fit(c.x[tr],c.gi,c.coords[tr],c.labels[tr],c.blocks[tr],cfg,c.cfg['seed'])
        pred,base=orth_prediction(m,c.x[te,c.gi],c.coords[te],c.labels[te]);null,_=orth_prediction(m,c.x[te,c.gi],c.coords[te],c.labels[te],True);y=c.x[te][:,cols]
        evals.append({'fold':int(fold),'entries':int(y.size),'mse':float(np.mean((pred-y)**2)),'confounds_only_mse':float(np.mean((base-y)**2)),'shuffled_activity_mse':float(np.mean((null-y)**2)),'optimistic_WT_oracle_mse':float(np.minimum((pred-y)**2,(base-y)**2).mean()),'oracle_role':'evaluation-only lower bound; not KO truth, not used in fitting or inference'})
        save_model(c.run/f'fold{fold}.pkl',m);print('n2orth',evals[-1],flush=True)
    m=orth_fit(c.x,c.gi,c.coords,c.labels,c.blocks,cfg,c.cfg['seed'])
    return final(c,'n2orth',{'model':m},{'folds':evals,'full_WT_cells':len(c.x),'modeled_responses':499,'limit':'orthogonalization removes modeled confounds only; observational WT not KO causal identification'})


def o1logit(c):
    cfg=c.cfg['round2'];cols=np.flatnonzero(np.arange(500)!=c.gi);a=c.x[:,[c.gi]];y=c.x[:,cols];evals=[]
    for fold in np.unique(c.blocks):
        tr=c.blocks!=fold;te=~tr
        m=LogisticHurdle().fit(a[tr],c.coords[tr],c.labels[tr],y[tr],cfg)
        p,pos,oldp=m.components(a[te],c.coords[te],c.labels[te]);base=type_baseline(y,c.labels,tr,te)
        probs=(y[te]>0).astype(float);positive_mean=np.divide(y[tr].sum(0),(y[tr]>0).sum(0),out=np.zeros(499),where=(y[tr]>0).sum(0)>0)
        evals.append({'fold':int(fold),'entries':int(y[te].size),'logistic_mse':float(np.mean((p*pos-y[te])**2)),'old_hurdle_mse':float(np.mean((oldp*pos-y[te])**2)),'type_mean_mse':float(np.mean((base-y[te])**2)),'probability_only_mse':float(np.mean((p*positive_mean-y[te])**2)),'logistic_brier':float(np.mean((p-probs)**2)),'old_brier':float(np.mean((oldp-probs)**2))})
        save_model(c.run/f'fold{fold}.pkl',m);print('o1logit',evals[-1],flush=True)
    m=LogisticHurdle().fit(a,c.coords,c.labels,y,cfg)
    # Intervention component ablations, not WT predictive scores for KO.
    aa=a[c.rows];zz=c.coords[c.rows];pp,positive,_=m.components(aa,zz,c.plabels);cp,cpositive,_=m.components(np.zeros_like(aa),zz,c.plabels)
    np.savez_compressed(c.run/'COUNTERFACTUAL_COMPONENTS.npz',probability_only=(cp-pp)*positive,intensity_only=pp*(cpositive-positive),interaction=(cp-pp)*(cpositive-positive))
    return final(c,'o1logit',{'model':m},{'folds':evals,'full_WT_cells':len(c.x),'logistic_genes':499,'limit':'Bernoulli fit models observed detection, not biological absence versus dropout'})


def occupancy_parameters(c,genes,samples):
    lock=json.loads((c.run/'SOURCE_LOCK.json').read_text());a=ad.read_h5ad(ROOT/lock['files']['expression']['path']);x=dense(a[:,c.genes].X);cond=a.obs.condition.astype(str).to_numpy();sam=a.obs['sample'].astype(str).to_numpy();params=[]
    cfg=c.cfg['round2']
    for s in samples:
        ctrl=x[(sam==s)&(cond=='ctrl')];p0=((ctrl>0).sum(0)+.5)/(len(ctrl)+1);m0=np.expm1(ctrl.astype(float)).sum(0)/np.maximum((ctrl>0).sum(0),1);rr=[]
        for g in genes:
            y=x[(sam==s)&(cond==g)];p=((y>0).sum(0)+.5)/(len(y)+1);mu=np.expm1(y.astype(float)).sum(0)/np.maximum((y>0).sum(0),1)
            rr.append(np.r_[np.clip(logit(p)-logit(p0),-cfg['logit_bound'],cfg['logit_bound']),np.clip(np.log((mu+.01)/(m0+.01)),-cfg['rate_bound'],cfg['rate_bound'])])
        params.append(rr)
    return np.asarray(params)


def fit_gene_shrink(c,z,y,adj,tr,te,tag):
    cfg=c.cfg['round2'];parts=np.array_split(np.random.default_rng(c.cfg['seed']).permutation(tr),cfg['inner_folds']);pp=[];mm=[];tt=[];inner=[]
    for val in parts:
        fit=np.setdiff1d(tr,val);m=fit_graph_comparator(z,y,adj,fit,val,epochs=cfg['source_epochs'],seed=c.cfg['seed']);pp.append(m['graph_prediction']);mm.append(np.broadcast_to(y[fit].mean(0),(len(val),500)));tt.append(y[val]);inner.append({'train':fit,'test':val,'model':m})
    w,scalar,tau=gene_shrink(np.vstack(mm),np.vstack(pp),np.vstack(tt),cfg['gene_shrink_prior_scale'])
    model=fit_graph_comparator(z,y,adj,tr,te,epochs=cfg['source_epochs'],seed=c.cfg['seed']);mean=y[tr].mean(0);graph=model['graph_prediction']
    save_model(c.run/(tag+'.pkl'),{'inner':inner,'final':model,'weights':w,'scalar':scalar,'tau':tau,'mean_rate':mean,'train':tr,'test':te})
    return {'model':mean+w*(graph-mean),'scalar_shrink':mean+scalar*(graph-mean),'raw_graph':graph,'mean':np.broadcast_to(mean,graph.shape),'zero':np.zeros_like(graph)},w


def source_route(c,lane):
    cfg=c.cfg['round2'];genes,samples,rates,effects,controls,z,adj=source(c);n=len(genes)
    params=occupancy_parameters(c,genes,samples) if lane=='n3occup' else rates
    folds=np.array_split(np.random.default_rng(c.cfg['seed']).permutation(n),cfg['source_folds']);evaluations=[];summary={}
    for name,train_samples,test_samples in [('pooled',[0,1],[0,1]),('sample0_to_1',[0],[1]),('sample1_to_0',[1],[0])]:
        y=np.vstack([params[train_samples].mean(0),np.zeros((1,params.shape[-1]))]);allpred={}
        for fold,te in enumerate(folds):
            tr=np.setdiff1d(np.arange(n),te)
            if lane=='o2geneshrink':arms,w=fit_gene_shrink(c,z,y,adj,tr,te,f'{name}_fold{fold}')
            else:
                pred,m=latent_predict(z,y,tr,te,cfg['latent_rank'],cfg['latent_alpha']);shuffled=y.copy();shuffled[tr]=y[np.random.default_rng(c.cfg['seed']+fold).permutation(tr)];null,nm=latent_predict(z,shuffled,tr,te,cfg['latent_rank'],cfg['latent_alpha'])
                arms={'model':pred,'mean':np.broadcast_to(y[tr].mean(0),pred.shape),'shuffled_conditions':null,'zero':np.zeros_like(pred)};save_model(c.run/f'{name}_fold{fold}.pkl',{'model':m,'shuffled_model':nm,'train':tr,'test':te})
            record={'scenario':name,'fold':fold,'train_genes':[genes[i] for i in tr],'test_genes':[genes[i] for i in te],'mse':{}};truth=effects[test_samples][:,te].mean(0)
            for method,par in arms.items():
                ps=[]
                for sample in test_samples:
                    ctrl=controls[sample];preds=[]
                    for vec in par:
                        if lane=='n3occup':
                            vec=np.r_[np.clip(vec[:500],-cfg['logit_bound'],cfg['logit_bound']),np.clip(vec[500:],-cfg['rate_bound'],cfg['rate_bound'])]
                            out=occupancy_decode(ctrl,vec,np.array(['ctrl']*len(ctrl)),cfg['sample_occupancy_strength'])
                        else:out=decode_rate(ctrl,np.clip(vec,-cfg['rate_bound'],cfg['rate_bound']))
                        preds.append(out.mean(0)-ctrl.mean(0))
                    ps.append(preds)
                pr=np.mean(ps,axis=0);allpred.setdefault(method,np.zeros((n,500)))[te]=pr;record['mse'][method]=float(np.mean((pr-truth)**2))
            evaluations.append(record)
        truth=effects[test_samples].mean(0);summary[name]={k:float(np.mean((pr-truth)**2)) for k,pr in allpred.items()};np.savez_compressed(c.run/(name+'_oof.npz'),truth=truth,**allpred);print(lane,name,summary[name],flush=True)
    y=np.vstack([params.mean(0),np.zeros((1,params.shape[-1]))]);tr=np.arange(n);te=np.array([n])
    if lane=='o2geneshrink':
        arms,w=fit_gene_shrink(c,z,y,adj,tr,te,'final_graph');model={'target_rate':np.clip(arms['model'][0],-cfg['rate_bound'],cfg['rate_bound']),'weights':w}
    else:
        p,m=latent_predict(z,y,tr,te,cfg['latent_rank'],cfg['latent_alpha']);model={'target_params':np.r_[np.clip(p[0,:500],-cfg['logit_bound'],cfg['logit_bound']),np.clip(p[0,500:],-cfg['rate_bound'],cfg['rate_bound'])],'fitted_model':m}
    return final(c,lane,model,{'folds':evaluations,'pooled_mse_by_scenario':summary,'source_cells':5454,'perturbation_genes':26,'full_output_genes':500,'independent_replicates':'NOT_ESTABLISHED','target_domain_validation':'NOT_AVAILABLE','phenocopy_filter_rechecked':True})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('route',choices=['prepare','n1stack','n2orth','n3occup','o1logit','o2geneshrink']);ap.add_argument('--run-dir',type=Path,required=True);a=ap.parse_args()
    if a.run_dir.exists():raise FileExistsError(a.run_dir)
    c=None
    def timeout(*_):raise TimeoutError('4h fixed wall bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(4*3600)
    try:
        c=Context(a.run_dir)
        if a.route=='prepare':prepare(c)
        else:
            assert json.loads((SHARED/'COMPONENT_AUDIT.json').read_text())['status']=='PASS'
            if a.route in ['n3occup','o2geneshrink']:source_route(c,a.route)
            else:globals()[a.route](c)
    except Exception as exc:
        dump(a.run_dir/'FAILURE.json',{'status':'FAILED_EXECUTION','error':str(exc),'traceback':traceback.format_exc(),'partial_candidates':c.candidates if c else []});raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
