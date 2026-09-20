"""Frozen T3 repair experiments: r6, r3 and r4. Never overwrite old runs."""
import argparse,json,signal,traceback
from pathlib import Path
import numpy as np
import anndata as ad
from scipy import sparse
from .common import ROOT,Context,dump,dense,sha
from .source_roles import require_response_role
from .routes_extended import approved_manifest,load_atlas,mapped_neighbors,atlas_group,WT_GROUPS
from .routes_local import ConditionalModel,graph_from_motif
from .algorithms import fit_graph_comparator
from .repair_ops import decode_rate,calibrate_rate,mean_ratio,residual_calibration,calibrated_transfer

DESIGN=ROOT/'configs/t3_next/repair_20260921.json'


def r6(c,manifest):
    import torch
    cfg=c.cfg['repair'];bound=cfg['rate_bound']
    review=require_response_role(json.loads(Path(manifest).read_text()),ROOT,'SIGNED_RESPONSE')
    m=approved_manifest(manifest,['expression','embedding','adjacency'])
    if m.get('species')!='mouse' or any(m.get(k)!='WT_OR_ONTOLOGY_ONLY' for k in ['embedding_role','adjacency_role']):
        raise ValueError('source species or representation role')
    dump(c.run/'SOURCE_LOCK.json',{'manifest':str(manifest),'sha256':sha(manifest),'files':m['files']})
    a=ad.read_h5ad(ROOT/m['files']['expression']['path'],backed='r')
    cond=a.obs.condition.astype(str).to_numpy();samples=a.obs['sample'].astype(str).to_numpy()
    if not set(cond)<=set(review['condition_allowlist']) or len(set(a.obs.cell_type))!=1:
        raise ValueError('unreviewed conditions or pooled contexts')
    genes=sorted(set(cond)-{'ctrl'})
    if set(g.upper() for g in genes)&{'GATA4','GATA6','CTNNB1','MESP1'}:raise ValueError('target labels')
    if len(genes)<20:raise ValueError('too few perturbation genes')
    ids=a.var_names.get_indexer(c.genes)
    if (ids<0).any():raise ValueError('panel missing')
    x=dense(a.X[:,ids]);a.file.close()
    if (x<0).any() or not np.isfinite(x).all():raise ValueError('invalid source expression')
    sam=sorted(set(samples));controls=[];rates=[];effects=[];targets=[];counts=[]
    for s in sam:
        control=x[(samples==s)&(cond=='ctrl')]
        if len(control)<20:raise ValueError('sample lacks controls')
        rr=[];ee=[];tt=[];count={}
        for g in genes:
            y=x[(samples==s)&(cond==g)]
            if len(y)<20:raise ValueError('sample/condition lacks cells')
            target=y.mean(0);tt.append(target);ee.append(target-control.mean(0))
            rr.append(calibrate_rate(control,target,bound,cfg['calibration_iterations']));count[g]=len(y)
        controls.append(control);rates.append(rr);effects.append(ee);targets.append(tt);counts.append(count)
    rates=np.asarray(rates);effects=np.asarray(effects);targets=np.asarray(targets)
    emb=np.load(ROOT/m['files']['embedding']['path'],allow_pickle=False);names=emb['genes'].astype(str).tolist()
    if len(set(names))!=len(names):raise ValueError('duplicate embedding genes')
    ii=[names.index(g) for g in genes+['Gata4']];z=emb['embedding'][ii]
    adj=sparse.load_npz(ROOT/m['files']['adjacency']['path'])[ii][:,ii].toarray()
    if not np.isfinite(z).all() or not np.isfinite(adj).all() or (adj<0).any():raise ValueError('invalid graph')
    rng=np.random.default_rng(cfg['fold_seed']);folds=np.array_split(rng.permutation(len(genes)),cfg['gene_folds'])
    permutation=rng.permutation(len(ii));shuffled=adj[permutation][:,permutation]
    scenarios=[('pooled',list(range(len(sam))),list(range(len(sam))))]
    scenarios += [(f'{s}_to_other',[i],[j for j in range(len(sam)) if j!=i]) for i,s in enumerate(sam)]
    if len(sam)<2:raise ValueError('sample transfer needs two source samples')
    metrics=[];all_predictions={}
    for scenario,train_samples,test_samples in scenarios:
        y=np.vstack([rates[train_samples].mean(0),np.zeros((1,500))])
        scenario_predictions={k:np.zeros((len(genes),500)) for k in cfg['r6_models']}
        for fold,te in enumerate(folds):
            tr=np.setdiff1d(np.arange(len(genes)),te)
            graph=fit_graph_comparator(z,y,adj,tr,te,epochs=cfg['r6_epochs'],seed=c.cfg['seed'])
            mlp=fit_graph_comparator(z,y,np.eye(len(ii)),tr,te,epochs=cfg['r6_epochs'],seed=c.cfg['seed'])
            null=fit_graph_comparator(z,y,shuffled,tr,te,epochs=cfg['r6_epochs'],seed=c.cfg['seed'])
            predictions={'zero':np.zeros((len(te),500)),'mean_rate':np.broadcast_to(y[tr].mean(0),(len(te),500)),
                         'ridge':graph['ridge_prediction'],'graph':graph['graph_prediction'],
                         'mlp':mlp['graph_prediction'],'shuffled_graph':null['graph_prediction']}
            truth=effects[test_samples][:,te].mean(0)
            avg_response=effects[train_samples][:,tr].mean((0,1))
            record={'scenario':scenario,'fold':fold,'train_genes':[genes[i] for i in tr],'test_genes':[genes[i] for i in te],'metrics':{}}
            for method in cfg['r6_models']:
                if method=='mean_response':pred=np.broadcast_to(avg_response,truth.shape)
                else:
                    rate=np.clip(predictions[method],-bound,bound)
                    pred=np.mean([np.stack([decode_rate(controls[s],r).mean(0)-controls[s].mean(0) for r in rate]) for s in test_samples],axis=0)
                scenario_predictions[method][te]=pred
                record['metrics'][method]={'mse':float(np.mean((pred-truth)**2)),
                    'per_gene_mse':np.mean((pred-truth)**2,axis=1).tolist(),
                    'direction_agreement':float(np.mean(np.sign(pred)==np.sign(truth)))}
            metrics.append(record)
            torch.save({'graph':graph,'mlp':mlp,'shuffled_graph':null},c.run/f'{scenario}_fold{fold}.pt')
        truth=effects[test_samples].mean(0)
        all_predictions[scenario]={k:float(np.mean((v-truth)**2)) for k,v in scenario_predictions.items()}
        print('r6 repair',scenario,all_predictions[scenario],flush=True)
    dump(c.run/'EVALUATION.json',{'folds':metrics,'pooled_mse_by_scenario':all_predictions,'samples':sam,'condition_counts':counts,
         'calibration_bound_fraction':float(np.mean(np.abs(rates)>bound-1e-6)),
         'zero_support_cells_not_activated':True,'independent_biological_replicates':'NOT_ESTABLISHED',
         'new_folds':'post-review fixed partition, reused source dataset; no hyperparameter search',
         'target_context_generalization':'NOT_VALIDATED'})
    summary=all_predictions['pooled']
    if summary['graph']>=summary['zero']:
        return c.finish('FAILED_SOURCE_ZERO_BASELINE',evaluation=all_predictions,target_inference='NOT_RUN_SOURCE_GATE')
    y=np.vstack([rates.mean(0),np.zeros((1,500))]);tr=np.arange(len(genes));te=np.array([len(genes)])
    final=fit_graph_comparator(z,y,adj,tr,te,epochs=cfg['r6_epochs'],seed=c.cfg['seed'])
    torch.save(final,c.run/'final_graph.pt')
    for lane,rate in [('r6meanfix',rates.mean((0,1))),('r6graphfix',final['graph_prediction'][0])]:
        rate=np.clip(rate,-bound,bound);out=decode_rate(c.base,rate);out[:,c.gi]=0
        c.save(lane,out,extra={'negative_clip_fraction':0.,'source_gene_specificity':'SUPPORTED_ONLY_IF_BEATS_MEAN_MLP_AND_SHUFFLE',
                             'decoder':'control-distribution-calibrated bounded raw-count multiplier; zeros preserved'})
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',evaluation=all_predictions,
                    graph_beats_all_nonzero_controls=all(summary['graph']<summary[k] for k in ['mean_response','mean_rate','ridge','mlp','shuffled_graph']))


def mechanism_fit(c,x,types,z,parents,kind,train):
    groups={}
    for j,ps in parents.items():groups.setdefault(tuple(ps),[]).append(j)
    return [(list(ps),js,ConditionalModel(kind,c.cfg['r3']['ridge_alpha']).fit(x[train][:,ps],z[train],types[train],x[train][:,js])) for ps,js in groups.items()]


def mechanism_predict(c,models,actual,z,types,intervene=True):
    out=actual.copy()
    if intervene:out[:,c.gi]=0
    for ps,js,f in models:
        out[:,js]=mean_ratio(actual[:,js],f.predict(actual[:,ps],z,types),f.predict(out[:,ps],z,types),
                            c.cfg['repair']['r3_mean_floor'],c.cfg['repair']['rate_bound'])
    return out


def r3(c):
    motif=c.motif();cfg=c.cfg['r3'];parents,dropped=graph_from_motif(motif,c.genes,depth=cfg['max_depth'],maxparents=cfg['max_parents'])
    dump(c.run/'TOPOLOGY.json',{'parents':parents,'dropped':dropped})
    z=np.column_stack([np.log1p(np.expm1(c.x).sum(1)),c.coords]);alltrain=np.ones(len(c.x),bool)
    evals=[];actual=c.x[c.rows];zp=z[c.rows]
    for kind,lane in [('linear','r3linfix'),('bounded_spline','r3splfix')]:
        folds=[];effect_sign=[]
        for fold in sorted(set(c.blocks)):
            train=c.blocks!=fold;test=~train;models=mechanism_fit(c,c.x,c.labels,z,parents,kind,train)
            sq=0.;bsq=0.;n=0
            for ps,js,f in models:
                pred=f.predict(c.x[test][:,ps],z[test],c.labels[test]);y=c.x[test][:,js]
                means={t:c.x[train&(c.labels==t)][:,js].mean(0) for t in set(c.labels[train])}
                fallback=c.x[train][:,js].mean(0);base=np.stack([means.get(t,fallback) for t in c.labels[test]])
                sq+=np.sum((pred-y)**2);bsq+=np.sum((base-y)**2);n+=y.size
            cf=mechanism_predict(c,models,actual,zp,c.plabels);effect_sign.append(np.sign((cf-actual).mean(0)))
            folds.append({'fold':int(fold),'mse':float(sq/n),'baseline_mse':float(bsq/n),'entries':n})
            print('r3 repair',kind,'fold',fold,'MSE',sq/n,flush=True)
        models=mechanism_fit(c,c.x,c.labels,z,parents,kind,alltrain)
        identity=mechanism_predict(c,models,actual,zp,c.plabels,False)
        if not np.array_equal(identity,actual):raise ValueError('zero-intervention identity')
        out=mechanism_predict(c,models,actual,zp,c.plabels)
        info={'kind':kind,'folds':folds,'modeled_genes':len(parents),'negative_clip_fraction':float((out<0).mean()),
              'sign_consistent_gene_count':int(np.sum(np.all(np.asarray(effect_sign)==effect_sign[0],axis=0))),
              'zero_gata4_support_by_type':{t:float(np.mean(c.x[c.labels==t,c.gi]==0)) for t in sorted(set(c.labels))},
              'support_limit':'Observed zeros may be dropout; not causal KO support','zero_intervention_identity':True}
        evals.append(info);c.save(lane,out,extra={'negative_clip_fraction':0.,'zero_intervention_identity':True})
    dump(c.run/'EVALUATION.json',evals)
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',models=evals)


def r4(c):
    motif=c.motif();rna,meta,genes=load_atlas(c,motif);cfg=c.cfg['r4'];rep=c.cfg['repair']
    ag=np.array([atlas_group(s) for s in meta.state]);wg=np.array([WT_GROUPS.get(s,'unmapped') for s in c.labels])
    evals=[];total=base_total=0.;count=0;gene_fold_better=[];coverage=[]
    for gf in range(rep['r4_gene_folds']):
        hold=np.array([j for j in range(500) if j%rep['r4_gene_folds']==gf and j!=c.gi])
        fitcols=np.array([j for j in range(500) if j not in hold and j!=c.gi]);gs=gb=0.
        for fold in sorted(set(c.blocks)):
            train=c.blocks!=fold;test=~train
            idx,scales,diag=mapped_neighbors(rna,c.x,ag,wg,fitcols,train,cfg['mapping_components'],cfg['n_neighbors'],c.cfg['seed'])
            supported=idx[:,0]>=0;raw=np.zeros((len(c.x),len(hold)))
            raw[supported]=rna[idx[supported]][:,:,hold].mean(1)
            pred,base,coeff=residual_calibration(raw,c.x[:,hold],c.labels,train,rep['r4_calibration_ridge'])
            pred[~supported]=base[~supported]
            sq=float(np.sum((pred[test]-c.x[test][:,hold])**2));bsq=float(np.sum((base[test]-c.x[test][:,hold])**2));n=int(test.sum()*len(hold))
            coverage.append(float(supported[c.rows].mean()));total+=sq;base_total+=bsq;count+=n;gs+=sq;gb+=bsq
            evals.append({'gene_fold':gf,'spatial_fold':int(fold),'mse':sq/n,'baseline_mse':bsq/n,'entries':n,
                          'coverage':coverage[-1],'held_genes':[c.genes[i] for i in hold],
                          'per_type':{t:{'cells':int(np.sum(test&(c.labels==t))),
                              'mse':float(np.mean((pred[test&(c.labels==t)]-c.x[test&(c.labels==t)][:,hold])**2)),
                              'baseline_mse':float(np.mean((base[test&(c.labels==t)]-c.x[test&(c.labels==t)][:,hold])**2))} for t in sorted(set(c.labels[test]))}})
            print('r4 repair gene/block',gf,int(fold),'MSE',sq/n,'baseline',bsq/n,flush=True)
        gene_fold_better.append(gs<gb)
    gate={'mse':total/count,'baseline_mse':base_total/count,'gene_folds_improved':sum(gene_fold_better),'min_coverage':min(coverage),'folds':evals,'all_test_cells_included':True,'heldout_panel_genes':499}
    dump(c.run/'MAPPING_GATE.json',gate)
    if total>=base_total or sum(gene_fold_better)<3 or min(coverage)<cfg['min_crossmodal_supported_fraction']:
        return c.finish('FAILED_MAPPING_GATE',gate=gate,counterfactual_models='NOT_RUN_GATE_FAILED')
    idx,scales,_=mapped_neighbors(rna,c.x,ag,wg,np.arange(500),np.ones(len(c.x),bool),cfg['mapping_components'],cfg['n_neighbors'],c.cfg['seed'])
    supported=idx[c.rows,0]>=0;positions=np.flatnonzero(supported);ri=c.rows[supported]
    latent=rna[idx[ri]].mean(1);zr=np.zeros((len(rna),1));zq=np.zeros((len(ri),1))
    all_supported=idx[:,0]>=0;raw=np.zeros_like(c.x)
    raw[all_supported]=rna[idx[all_supported]][:,:,:500].mean(1)
    mapped,_,coeff=residual_calibration(raw,c.x,c.labels,np.ones(len(c.x),bool),rep['r4_calibration_ridge'])
    slopes=np.stack([coeff[str(t)] for t in c.plabels[supported]])
    dump(c.run/'FINAL_CALIBRATION.json',{'slopes_by_type':coeff,'role':'same train-fitted slope used for intervention response transfer','all_WT_training':True})
    for augmented,lane in [(False,'r4panelFix'.lower()),(True,'r4medfix')]:
        width=len(genes) if augmented else 500;parents,_=graph_from_motif(motif,genes[:width].tolist(),depth=2,maxparents=6)
        models=mechanism_fit(c,rna[:,:width],ag,zr,parents,'linear',np.ones(len(rna),bool))
        original=latent[:,:width];cf=mechanism_predict(c,models,original,zq,wg[ri])
        # Transfer the atlas change through the learned MERFISH calibration,
        # then preserve each cell's observed residual with a bounded ratio.
        out=c.base.copy();out[positions]=calibrated_transfer(c.base[positions],mapped[ri],cf[:,:500]-original[:,:500],slopes,rep['r3_mean_floor'],rep['rate_bound']);out[:,c.gi]=0
        c.save(lane,out,extra={'mapping_gate':'PASS','negative_clip_fraction':0.,'width':width,'unmapped_keep_parent':int((~supported).sum())})
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',gate=gate)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('route',choices=['r6','r3','r4']);ap.add_argument('--run-dir',type=Path,required=True)
    ap.add_argument('--source-manifest',type=Path,default=ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json');args=ap.parse_args()
    if args.run_dir.exists():raise FileExistsError(args.run_dir)
    c=None
    def timeout(*_):raise TimeoutError('fixed 8h wall bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(8*3600)
    try:
        c=Context(args.run_dir,design=DESIGN)
        globals()[args.route](c,**({'manifest':args.source_manifest} if args.route=='r6' else {}))
    except Exception as exc:
        dump(args.run_dir/'FAILURE.json',{'status':'FAILED_EXECUTION','error':str(exc),'traceback':traceback.format_exc(),'partial_candidates':c.candidates if c else []})
        raise
    finally:signal.alarm(0)


if __name__=='__main__':main()
