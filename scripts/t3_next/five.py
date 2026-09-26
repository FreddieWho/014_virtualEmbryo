"""Execute the frozen three new routes and two optimizations, one route per run."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='8'
import argparse,json,signal,traceback,pickle
from pathlib import Path
import numpy as np
import anndata as ad
from scipy import sparse
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from .common import Context,ROOT,dump,dense,sha
from .source_roles import require_response_role
from .routes_extended import approved_manifest
from .routes_local import graph_from_motif,ConditionalModel
from .repair import mechanism_fit,mechanism_predict
from .repair_ops import decode_rate,calibrate_rate
from .algorithms import fit_graph_comparator
from .five_ops import quantile_response,bounded_add,latent_predict,shrink_weight,stability_weight

DESIGN=ROOT/'configs/t3_next/five_20260927.json'


def persist(c,name,obj):
    with (c.run/name).open('xb') as f:pickle.dump(obj,f,protocol=5)


def finish(c,**kw):
    return c.finish('CANDIDATES_READY' if c.candidates else 'COMPUTED_NO_CANDIDATE',**kw)


def type_baseline(y,types,train,test):
    fallback=y[train].mean(0)
    means={t:y[train&(types==t)].mean(0) for t in np.unique(types[train])}
    return np.stack([means.get(t,fallback) for t in types[test]])


def quantile_fit(c,train,cols):
    cfg=c.cfg['five'];depth=np.log1p(np.expm1(c.x[:,np.arange(500)!=c.gi]).sum(1))
    groups=[]
    for t in np.unique(c.labels):
        ix=np.flatnonzero(train&(c.labels==t))
        if len(ix)<cfg['min_type']:continue
        edges=np.unique(np.quantile(depth[ix],np.linspace(0,1,cfg['depth_bins']+1)[1:-1]))
        bins=np.searchsorted(edges,depth,side='right')
        for b in range(len(edges)+1):
            pool=ix[bins[ix]==b];a=c.x[pool,c.gi]
            if len(pool)<2*cfg['min_group']:continue
            low,high=np.quantile(a,[.25,.75])
            if high<=low:continue
            lo=pool[a<=low];hi=pool[a>=high]
            if min(len(lo),len(hi))<cfg['min_group']:continue
            groups.append({'type':t,'bin':b,'edges':edges,'low':low,'high':high,
                           'lo':c.x[lo][:,cols],'hi':c.x[hi][:,cols],
                           'n_low':len(lo),'n_high':len(hi)})
    return groups,depth


def n1quant(c):
    cfg=c.cfg['five'];motif=c.motif()
    targets=set(motif.loc[motif.Gata4>0,'gene_short_name'])
    cols=np.array([j for j,g in enumerate(c.genes) if g in targets and j!=c.gi])
    if len(cols)==0:raise ValueError('no direct motif targets')
    evaluations=[]
    for fold in np.unique(c.blocks):
        train=c.blocks!=fold;groups,depth=quantile_fit(c,train,cols);sq=bsq=0.;entries=0;covered=0
        for g in groups:
            ix=np.flatnonzero((~train)&(c.labels==g['type'])&(np.searchsorted(g['edges'],depth,side='right')==g['bin']))
            hi=ix[c.x[ix,c.gi]>=g['high']];lo=ix[c.x[ix,c.gi]<=g['low']]
            if min(len(hi),len(lo))<5:continue
            pred=quantile_response(c.x[hi][:,cols],g['hi'],g['lo'],cfg['quantile_strength'],cfg['rate_bound'])
            q=np.linspace(0,1,cfg['quantile_grid']);truth=np.quantile(c.x[lo][:,cols],q,axis=0)
            ps=np.quantile(pred,q,axis=0);bs=np.quantile(c.x[hi][:,cols],q,axis=0)
            sq+=float(np.sum((ps-truth)**2));bsq+=float(np.sum((bs-truth)**2));entries+=truth.size;covered+=len(hi)+len(lo)
        evaluations.append({'fold':int(fold),'quantile_mse':sq/entries if entries else None,'identity_quantile_mse':bsq/entries if entries else None,'quantile_entries':entries,'evaluated_cells':covered,'test_cells':int((~train).sum())})
        print('n1quant',evaluations[-1],flush=True)
    groups,depth=quantile_fit(c,np.ones(len(c.x),bool),cols);out=c.base.copy();active=[]
    for g in groups:
        ix=np.flatnonzero((c.plabels==g['type'])&(np.searchsorted(g['edges'],depth[c.rows],side='right')==g['bin'])&(c.x[c.rows,c.gi]>=g['high']))
        if not len(ix):continue
        out[np.ix_(ix,cols)]=quantile_response(c.base[np.ix_(ix,cols)],g['hi'],g['lo'],cfg['quantile_strength'],cfg['rate_bound'])
        active.extend(ix.tolist())
    persist(c,'quantile_model.pkl',{'groups':groups,'cols':cols,'strength':cfg['quantile_strength'],'bound':cfg['rate_bound']})
    dump(c.run/'EVALUATION.json',{'folds':evaluations,'targets':[c.genes[j] for j in cols],'eligible_recipient_cells':len(set(active)),'limit':'Held-block observational high-to-low distribution diagnostic, not KO prediction accuracy; unsupported groups unchanged'})
    c.save('n1quant',out,extra={'route_class':'NEW','negative_clip_fraction':0.})
    return finish(c,full_wt_cells=len(c.x),evaluation_folds=len(evaluations))


class Hurdle:
    """Ridge linear probability plus ridge conditional-positive log expression."""
    def fit(self,a,z,types,y,alpha):
        self.encoder=ConditionalModel('linear',alpha)
        # Reuse only the train-fitted feature encoder; probability is multi-output.
        self.encoder.fit(a,z,types,(y>0).astype(float))
        features=self.encoder.features(a,z,types);self.positive=[]
        for j in range(y.shape[1]):
            present=y[:,j]>0
            if present.sum()<3:self.positive.append(float(y[present,j].mean()) if present.any() else 0.)
            else:self.positive.append(Ridge(alpha).fit(features[present],y[present,j]))
        return self
    def predict(self,a,z,types):
        f=self.encoder.features(a,z,types)
        prob=np.clip(self.encoder.model.predict(f),0,1)
        pos=np.column_stack([np.full(len(f),m) if isinstance(m,float) else np.maximum(m.predict(f),0) for m in self.positive])
        return prob*pos,prob


def n2hurdle(c):
    cfg=c.cfg['five'];cols=np.flatnonzero(np.arange(500)!=c.gi)
    # Expression-derived covariates would leak response outcomes in reconstruction.
    z=c.coords;activity=c.x[:,[c.gi]];y=c.x[:,cols];evals=[]
    for fold in np.unique(c.blocks):
        train=c.blocks!=fold;test=~train
        m=Hurdle().fit(activity[train],z[train],c.labels[train],y[train],cfg['ridge_alpha'])
        pred,p=m.predict(activity[test],z[test],c.labels[test]);b=type_baseline(y,c.labels,train,test)
        bp=type_baseline((y>0).astype(float),c.labels,train,test)
        evals.append({'fold':int(fold),'mse':float(np.mean((pred-y[test])**2)),'type_mean_mse':float(np.mean((b-y[test])**2)),'brier':float(np.mean((p-(y[test]>0))**2)),'type_brier':float(np.mean((bp-(y[test]>0))**2)),'entries':int(y[test].size)})
        print('n2hurdle',evals[-1],flush=True)
    m=Hurdle().fit(activity,z,c.labels,y,cfg['ridge_alpha']);a=activity[c.rows];zr=z[c.rows]
    factual,_=m.predict(a,zr,c.plabels);cf,_=m.predict(np.zeros_like(a),zr,c.plabels)
    out=c.base.copy();out[:,cols]=bounded_add(c.base[:,cols],cf-factual,cfg['hurdle_strength'])
    persist(c,'hurdle_model.pkl',{'encoder':m.encoder,'positive':m.positive,'cols':cols})
    dump(c.run/'EVALUATION.json',{'folds':evals,'zero_to_positive_entries':int(np.sum((c.base==0)&(out>0))),'positive_to_zero_entries':int(np.sum((c.base>0)&(out==0))),'hypothetical_additive_negative_fraction_not_used':float(np.mean(c.base[:,cols]+np.clip(cfg['hurdle_strength']*(cf-factual),-np.log(2),np.log(2))<0)),'zero_intervention_identity':bool(np.array_equal(bounded_add(c.base[:,cols],factual-factual,cfg['hurdle_strength']),c.base[:,cols])),'negative_clip_fraction':0.,'probability_method':'bounded ridge linear probability, not logistic likelihood','limit':'Observed zeros mix biology and dropout; no causal identification'})
    c.save('n2hurdle',out,extra={'route_class':'NEW','output_operator':'positive log increment; negative raw-intensity attenuation; no output clipping','negative_clip_fraction':0.})
    return finish(c,full_wt_cells=len(c.x),evaluation_folds=len(evals))


def source(c):
    manifest=ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'
    review=require_response_role(json.loads(manifest.read_text()),ROOT,'SIGNED_RESPONSE')
    m=approved_manifest(manifest,['expression','embedding','adjacency'])
    if m.get('species')!='mouse' or any(m.get(k)!='WT_OR_ONTOLOGY_ONLY' for k in ['embedding_role','adjacency_role']):raise ValueError('source roles')
    a=ad.read_h5ad(ROOT/m['files']['expression']['path']);cond=a.obs.condition.astype(str).to_numpy();samples=a.obs['sample'].astype(str).to_numpy()
    if not set(cond)<=set(review['condition_allowlist']) or len(set(a.obs.cell_type))!=1:raise ValueError('source conditions/context')
    genes=sorted(set(cond)-{'ctrl'})
    if set(g.upper() for g in genes)&{'GATA4','GATA6','CTNNB1','MESP1'}:raise ValueError('protected target')
    if len(genes)<20:raise ValueError('insufficient conditions')
    ids=a.var_names.get_indexer(c.genes)
    if (ids<0).any():raise ValueError('missing panel')
    x=dense(a.X[:,ids]);sam=sorted(set(samples));controls=[];rates=[];effects=[];counts={}
    for s in sam:
        ctrl=x[(samples==s)&(cond=='ctrl')]
        if len(ctrl)<20:raise ValueError('too few controls')
        rr=[];ee=[];counts[s]={'ctrl':len(ctrl)}
        for g in genes:
            cells=x[(samples==s)&(cond==g)];counts[s][g]=len(cells)
            if len(cells)<20:raise ValueError('too few source cells')
            rr.append(calibrate_rate(ctrl,cells.mean(0),c.cfg['five']['rate_bound']))
            ee.append(cells.mean(0)-ctrl.mean(0))
        controls.append(ctrl);rates.append(rr);effects.append(ee)
    emb=np.load(ROOT/m['files']['embedding']['path'],allow_pickle=False);names=emb['genes'].astype(str).tolist()
    if len(set(names))!=len(names):raise ValueError('duplicate genes')
    ii=[names.index(g) for g in genes+['Gata4']];z=emb['embedding'][ii]
    adj=sparse.load_npz(ROOT/m['files']['adjacency']['path'])[ii][:,ii].toarray()
    if not np.isfinite(x).all() or (x<0).any() or not np.isfinite(z).all() or not np.isfinite(adj).all():raise ValueError('invalid source values')
    dump(c.run/'SOURCE_LOCK.json',{'manifest':str(manifest.relative_to(ROOT)),'manifest_sha256':sha(manifest),'files':m['files'],'cells':len(x),'conditions':genes,'samples':sam,'counts':counts,'role':'SIGNED_RESPONSE','policy':'T3_EXTERNAL_DATA_20260921'})
    return genes,sam,np.asarray(rates),np.asarray(effects),controls,z,adj


def graph_shrink(z,y,adj,train,test,c,tag):
    cfg=c.cfg['five'];rng=np.random.default_rng(c.cfg['seed']);splits=np.array_split(rng.permutation(train),cfg['inner_folds'])
    predictions=[];means=[];truth=[];inner=[]
    for fold,val in enumerate(splits):
        fit=np.setdiff1d(train,val)
        model=fit_graph_comparator(z,y,adj,fit,val,epochs=cfg['epochs'],seed=c.cfg['seed'])
        predictions.append(model['graph_prediction']);means.append(np.broadcast_to(y[fit].mean(0),(len(val),500)));truth.append(y[val])
        inner.append({'train':fit.tolist(),'test':val.tolist(),'state':model})
    w=shrink_weight(np.vstack(means),np.vstack(predictions),np.vstack(truth))
    model=fit_graph_comparator(z,y,adj,train,test,epochs=cfg['epochs'],seed=c.cfg['seed'])
    mean=y[train].mean(0);pred=mean+w*(model['graph_prediction']-mean)
    persist(c,tag+'.pkl',{'inner':inner,'weight':w,'model':model,'mean_rate':mean,'train':train,'test':test})
    return pred,{'weight':w,'raw_graph':model['graph_prediction']}


def source_route(c,route):
    cfg=c.cfg['five'];genes,sam,rates,effects,controls,z,adj=source(c);n=len(genes)
    if len(sam)!=2:raise ValueError('design expects two samples')
    folds=np.array_split(np.random.default_rng(c.cfg['seed']).permutation(n),cfg['gene_folds'])
    scenarios=[('pooled',[0,1],[0,1]),('sample0_to_1',[0],[1]),('sample1_to_0',[1],[0])]
    evaluations=[];summary={}
    for name,si,ti in scenarios:
        y=np.vstack([rates[si].mean(0),np.zeros((1,500))]);predictions={k:np.zeros((n,500)) for k in ['model','mean_rate','zero']}
        if route=='o2shrink':predictions['unshrunk_graph']=np.zeros((n,500))
        for fold,test in enumerate(folds):
            train=np.setdiff1d(np.arange(n),test)
            if route=='n3latent':
                pr,model=latent_predict(z,y,train,test,cfg['low_rank'],cfg['kernel_ridge']);persist(c,f'{name}_fold{fold}.pkl',model);extra={}
            else:pr,extra=graph_shrink(z,y,adj,train,test,c,f'{name}_fold{fold}')
            rr={'model':pr,'mean_rate':np.broadcast_to(y[train].mean(0),pr.shape),'zero':np.zeros_like(pr)}
            if route=='o2shrink':rr['unshrunk_graph']=extra.pop('raw_graph')
            truth=effects[ti][:,test].mean(0);record={'scenario':name,'fold':fold,'train_genes':[genes[j] for j in train],'test_genes':[genes[j] for j in test],**extra,'mse':{}}
            for key,rate in rr.items():
                rate=np.clip(rate,-cfg['rate_bound'],cfg['rate_bound'])
                pred=np.mean([np.stack([decode_rate(controls[s],r).mean(0)-controls[s].mean(0) for r in rate]) for s in ti],axis=0)
                predictions[key][test]=pred;record['mse'][key]=float(np.mean((pred-truth)**2))
            evaluations.append(record)
        truth=effects[ti].mean(0)
        summary[name]={key:float(np.mean((pr-truth)**2)) for key,pr in predictions.items()}
        np.savez_compressed(c.run/(name+'_oof.npz'),truth=truth,**predictions)
        print(route,name,summary[name],flush=True)
    y=np.vstack([rates.mean(0),np.zeros((1,500))]);train=np.arange(n);test=np.array([n])
    if route=='n3latent':
        rate,model=latent_predict(z,y,train,test,cfg['low_rank'],cfg['kernel_ridge']);persist(c,'final_model.pkl',model);extra={}
    else:rate,extra=graph_shrink(z,y,adj,train,test,c,'final_model');extra.pop('raw_graph')
    rate=np.clip(rate[0],-cfg['rate_bound'],cfg['rate_bound']);np.save(c.run/'target_rate.npy',rate)
    out=decode_rate(c.base,rate);out[:,c.gi]=0
    dump(c.run/'EVALUATION.json',{'folds':evaluations,'pooled_mse_by_scenario':summary,'final':extra,'full_source_cells':sum(sum(v.values()) for v in json.loads((c.run/'SOURCE_LOCK.json').read_text())['counts'].values()),'heldout_genes':n,'output_genes':500,'independent_biological_replicates':'NOT_ESTABLISHED','target_context_generalization':'NOT_VALIDATED','final_inference':'EXECUTED_REGARDLESS_OF_SCIENTIFIC_BASELINE_RANK','blocks_submission':False})
    c.save(route,out,extra={'route_class':'NEW' if route=='n3latent' else 'OPTIMIZATION','algorithm_parent':None if route=='n3latent' else 'v0035','negative_clip_fraction':0.,**extra})
    return finish(c,evaluation=summary,final=extra)


def o1stable(c):
    cfg=c.cfg['five'];motif=c.motif();parents,dropped=graph_from_motif(motif,c.genes,depth=c.cfg['r3']['max_depth'],maxparents=c.cfg['r3']['max_parents'])
    dump(c.run/'TOPOLOGY.json',{'parents':parents,'dropped':dropped})
    # Match the existing algorithm; size is held fixed under the intervention.
    z=np.column_stack([np.log1p(np.expm1(c.x).sum(1)),c.coords]);actual=c.x[c.rows];zp=z[c.rows];effects=[];evals=[]
    for fold in np.unique(c.blocks):
        train=c.blocks!=fold;test=~train;models=mechanism_fit(c,c.x,c.labels,z,parents,'linear',train)
        sq=bsq=0.;entries=0
        for ps,js,m in models:
            pred=m.predict(c.x[test][:,ps],z[test],c.labels[test]);truth=c.x[test][:,js]
            base=type_baseline(c.x[:,js],c.labels,train,test)
            sq+=float(np.sum((pred-truth)**2));bsq+=float(np.sum((base-truth)**2));entries+=truth.size
        cf=mechanism_predict(c,models,actual,zp,c.plabels);effects.append((cf-actual).mean(0))
        evals.append({'fold':int(fold),'mse':sq/entries,'type_baseline_mse':bsq/entries,'entries':entries})
        persist(c,f'fold{fold}.pkl',models);print('o1stable',evals[-1],flush=True)
    effects=np.asarray(effects);effects[:,c.gi]=0
    weights=stability_weight(effects,cfg['stability_prior']);weights[c.gi]=0
    models=mechanism_fit(c,c.x,c.labels,z,parents,'linear',np.ones(len(c.x),bool))
    identity=mechanism_predict(c,models,actual,zp,c.plabels,False)
    if not np.array_equal(identity,actual):raise ValueError('zero intervention not identity')
    cf=mechanism_predict(c,models,actual,zp,c.plabels);rate=np.zeros_like(cf,dtype=float);mask=c.base>0
    rate[mask]=np.log(np.maximum(np.expm1(cf[mask]),1e-20)/np.expm1(c.base[mask]))
    out=decode_rate(c.base,np.clip(rate,-cfg['rate_bound'],cfg['rate_bound'])*weights);out[:,c.gi]=0
    persist(c,'final_model.pkl',{'models':models,'weights':weights});np.savez_compressed(c.run/'stability.npz',effects=np.asarray(effects),weights=weights)
    dump(c.run/'EVALUATION.json',{'folds':evals,'modeled_genes':len(parents),'weights_nonzero':int(np.count_nonzero(weights)),'weights_max':float(weights.max()),'zero_intervention_identity':True,'limit':'Fold stability is sensitivity, not independent replication or causal validation. Existing R3 library-size covariate includes outcomes, so WT reconstruction is descriptive only.'})
    c.save('o1stable',out,extra={'route_class':'OPTIMIZATION','algorithm_parent':'v0036','negative_clip_fraction':0.})
    return finish(c,full_wt_cells=len(c.x),evaluation_folds=len(evals))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('route',choices=['n1quant','n2hurdle','n3latent','o1stable','o2shrink']);ap.add_argument('--run-dir',required=True,type=Path);args=ap.parse_args()
    if args.run_dir.exists():raise FileExistsError(args.run_dir)
    c=None
    def timeout(*_):raise TimeoutError('frozen 4h limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(4*3600)
    try:
        c=Context(args.run_dir,design=DESIGN)
        if args.route in ['n3latent','o2shrink']:source_route(c,args.route)
        else:globals()[args.route](c)
    except Exception as exc:
        dump(args.run_dir/'FAILURE.json',{'status':'FAILED_EXECUTION','error':str(exc),'traceback':traceback.format_exc(),'partial_candidates':c.candidates if c else []})
        raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
