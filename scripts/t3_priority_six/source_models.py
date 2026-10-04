"""Real author Scouter/GEARS plus functional baselines, same entire-gene holdouts."""
from .common import *
import pandas as pd, torch, copy, shutil
from sklearn.linear_model import Ridge

def source_setup():
    source,parent,wt=load_inputs();source.X=sparse.csr_matrix(source.X)
    source.obs['original_condition']=source.obs.condition.astype(str)
    source.obs['condition']=source.obs.original_condition.map(lambda x:'ctrl' if x=='ctrl' else x+'+ctrl').astype('category')
    source.obs['cell_type']='adult_mouse_cardiac_fibroblast'
    source.var['gene_name']=source.var_names.astype(str)
    z=np.load(RUN/'GO_EMBEDDING.npz');emb=pd.DataFrame(z['embedding'],index=z['genes'])
    emb.loc['ctrl']=0.
    cfg=json.loads((RUN/'CONFIG.json').read_text());torch.manual_seed(SEED);np.random.seed(SEED);torch.set_num_threads(8)
    return source,parent,wt,emb,cfg

def truth_delta(source,genes):
    x=dense(source.X);labels=source.obs.original_condition.to_numpy();ctrl=x[labels=='ctrl'].mean(0)
    return np.array([x[labels==g].mean(0)-ctrl for g in genes]),ctrl

def immutable_eval(lane,pred,source,cfg,extras=None):
    truth,ctrl=truth_delta(source,cfg['split']['test']);train_truth,_=truth_delta(source,cfg['split']['train'])
    mean=train_truth.mean(0);controls={'identity':delta_metrics(np.zeros_like(truth),truth),'training_mean':delta_metrics(np.repeat(mean[None,:],len(truth),0),truth)}
    result={'test_genes':cfg['split']['test'],'training_genes':cfg['split']['train'],'validation_genes':cfg['split']['val'],'metrics':delta_metrics(pred,truth),'baselines':controls,'no_target_truth':True,'independent_animals':'NOT_ESTABLISHED','extras':extras}
    p=RUN/lane;p.mkdir(exist_ok=True);path=p/'HOLDOUT.json'
    assert not path.exists(),'Do not overwrite independent heldout evidence'
    np.save(p/'heldout_pred_delta.npy',pred);np.save(p/'heldout_true_delta.npy',truth);dump(path,result)
    print('HOLDOUT_COMPLETE',lane,result['metrics'],flush=True)

def functional_run():
    source,parent,wt,emb,cfg=source_setup();conditions=sum(cfg['split'].values(),[])
    def fit(genes):
        y,_=truth_delta(source,genes);return Ridge(alpha=10).fit(emb.loc[genes].values,y)
    model=fit(cfg['split']['train']);pred=model.predict(emb.loc[cfg['split']['test']])
    shuffled=emb.copy();perm=np.random.default_rng(SEED).permutation(cfg['split']['train'])
    shuffled.loc[cfg['split']['train']]=emb.loc[perm].values
    sham=Ridge(alpha=10).fit(shuffled.loc[cfg['split']['train']],truth_delta(source,cfg['split']['train'])[0])
    truth,ctrl=truth_delta(source,cfg['split']['test'])
    immutable_eval('r4_functional',pred,source,cfg,{'permuted_embedding':delta_metrics(sham.predict(emb.loc[cfg['split']['test']]),truth)})
    # Bilinear context uses each sample's control expression; no KO in context features.
    from sklearn.decomposition import PCA
    x=dense(source.X);labs=source.obs.original_condition.to_numpy();samples=source.obs['sample'].astype(str).to_numpy();ss=sorted(set(samples));control=np.array([x[(labs=='ctrl')&(samples==s)].mean(0) for s in ss])
    pca=PCA(min(8,len(ss)-1),random_state=SEED);context=pca.fit_transform(control)
    def features(e,c):return np.r_[e,c,np.outer(e,c).ravel()]
    def bilinear_fit(genes):
        xx=[];yy=[]
        for g in genes:
            for k,s in enumerate(ss):
                m=(labs==g)&(samples==s)
                if m.any():xx.append(features(emb.loc[g].values,context[k]));yy.append(x[m].mean(0)-control[k])
        return Ridge(alpha=10).fit(np.array(xx),np.array(yy))
    bm=bilinear_fit(cfg['split']['train']);bp=np.array([np.mean([bm.predict(features(emb.loc[g].values,c)[None,:])[0] for c in context],0) for g in cfg['split']['test']])
    dump(RUN/'r4_functional/BILINEAR_HOLDOUT.json',{'metrics':delta_metrics(bp,truth),'sample_context_dimension':context.shape[1],'samples':ss,'independent_animals':'NOT_ESTABLISHED'})
    final=fit(conditions);final_b=bilinear_fit(conditions)
    with (RUN/'r4_functional/models.pkl').open('wb') as f:pickle.dump({'linear':final,'bilinear':final_b,'context_pca':pca},f)
    baseline=dense(parent.X);gi=parent.var_names.get_loc('Gata4')
    for name,delta in [('r4_functional',final.predict(emb.loc[['Gata4']])[0]),('r4_bilinear',np.mean([final_b.predict(features(emb.loc['Gata4'].values,c)[None,:])[0] for c in context],0))]:
        # Delta comes from supervised log-expression; map the corresponding mean intensity ratio to MERFISH.
        controls=x[labs=='ctrl'];rate=mean_rate(controls,np.maximum(controls+delta,0))
        out=rate_decode(baseline,rate);out[:,gi]=0
        write_research(name,out,parent,{'source_cells':len(source),'perturbations':26,'heldout_receipt':sha(RUN/'r4_functional/HOLDOUT.json'),'representation':'GO128','target_validation':'NOT_RUN_NO_MATCHED_GATA4_TRUTH'})

def scouter_predict(model,embedding_index,x):
    model.network.eval();outputs=[]
    with torch.no_grad():
        for i in range(0,len(x),256):
            batch=torch.tensor(x[i:i+256],dtype=torch.float32)
            pert=torch.full((len(batch),1),int(embedding_index),dtype=torch.long)
            outputs.append(model.network(pert,batch).cpu().numpy())
    return np.concatenate(outputs)

def scouter_run():
    sys.path.insert(0,str(ROOT/'infra/toolchains/t3_priority_six/scouter'))
    from scouter import Scouter,ScouterData
    source,parent,wt,emb,cfg=source_setup()
    def make_data():
        data=ScouterData(source,emb,key_label='condition',key_var_genename='gene_name');data.setup_ad(slim=False)
        assert len(data.adata)==5454 and 'Gata4' in data.embd.index
        data.gene_ranks();data.get_dropout_non_zero_genes();return data
    data=make_data();labels=lambda g:[p+'+ctrl' for p in g]
    data.split_Train_Val_Test(val_conds=labels(cfg['split']['val']),test_conds=labels(cfg['split']['test']),seed=SEED)
    assert set(data.train_adata.obs.original_condition)-{'ctrl'}==set(cfg['split']['train'])
    model=Scouter(data,device='cpu');model.model_init()
    # Author trainer retains state_dict by reference. Snapshot copying fixes the
    # validation checkpoint without changing network, optimizer, losses or pairs.
    state_dict=model.network.state_dict
    model.network.state_dict=lambda *a,**kw:copy.deepcopy(state_dict(*a,**kw))
    model.train(n_epochs=40,patience=5)
    control=dense(source.X[source.obs.original_condition=='ctrl']);ctrl=control.mean(0)
    pred=np.array([scouter_predict(model,model.embd_idx_dict[g],control).mean(0)-ctrl for g in cfg['split']['test']])
    immutable_eval('r5_scouter',pred,source,cfg,{'representation_variant':'GO128, NOT paper GenePT1536'})
    permuted=np.random.default_rng(SEED).permutation(cfg['split']['test'])
    sham=np.array([scouter_predict(model,model.embd_idx_dict[g],control).mean(0)-ctrl for g in permuted])
    dump(RUN/'r5_scouter/CONDITION_SHUFFLE_INFERENCE.json',{'metrics':delta_metrics(sham,truth_delta(source,cfg['split']['test'])[0]),'permutation':permuted.tolist(),'scope':'condition permutation at inference; not a separately trained shuffled model'})
    torch.save(model.network.state_dict(),RUN/'r5_scouter/heldout_model.pt');dump(RUN/'r5_scouter/HISTORY.json',model.loss_history)
    # Fixed epoch count from validation only; no selection using test perturbations.
    best_epochs=int(np.argmin(model.loss_history['val_loss']))+1
    final_data=make_data();final_data.train_adata=final_data.adata.copy();final_data.val_adata=final_data.adata[:0].copy();final_data.test_adata=final_data.adata[:0].copy()
    final=Scouter(final_data,device='cpu');final.model_init();final.train(n_epochs=best_epochs,patience=best_epochs+1)
    torch.save(final.network.state_dict(),RUN/'r5_scouter/final_model.pt')
    # Predict all target cells after control-only platform scaling. Difference the zero-perturbation reference.
    px=dense(parent.X);rows=wt.obs_names.get_indexer(parent.obs_names);tx=dense(wt.X)[rows]
    scale=(np.expm1(control).mean(0)+1e-3)/(np.expm1(tx).mean(0)+1e-3)
    mapped=np.log1p(np.expm1(tx)*scale)
    factual=scouter_predict(final,final.embd_idx_dict['ctrl'],mapped)
    cf=scouter_predict(final,final.embd_idx_dict['Gata4'],mapped)
    rate=np.log((np.expm1(np.maximum(cf,0))+1e-3)/(np.expm1(np.maximum(factual,0))+1e-3))
    out=rate_decode(px,rate);out[:,parent.var_names.get_loc('Gata4')]=0
    np.savez(RUN/'r5_scouter/native_target_outputs.npz',factual=factual,counterfactual=cf)
    write_research('r5_scouter',out,parent,{'final_epochs':best_epochs,'source_cells':5454,'perturbations':26,'original_author_network_and_training':True,'embedding':'GO128 variant','zero_embedding_reference':'structural counterfactual; control output was not supervised by author BalancedDataset','heldout_receipt':sha(RUN/'r5_scouter/HOLDOUT.json')})

def gears_infer(model,x,gene):
    from torch_geometric.data import Data,Batch
    output=[];model.best_model.eval()
    idx=-1 if gene=='ctrl' else model.node_map_pert[gene]
    with torch.no_grad():
        for start in range(0,len(x),32):
            graphs=[Data(x=torch.tensor(row[:,None],dtype=torch.float32),pert_idx=[idx]) for row in x[start:start+32]]
            batch=Batch.from_data_list(graphs);output.append(model.best_model(batch).cpu().numpy())
    return np.concatenate(output)

def gears_run():
    sys.path.insert(0,str(ROOT/'infra/toolchains/t3_priority_six/GEARS'))
    from gears import GEARS,PertData
    source,parent,wt,emb,cfg=source_setup();p=RUN/'r6_gears';p.mkdir(exist_ok=True)
    with (RUN/'gene2go.pkl').open('rb') as f:gene2go=pickle.load(f)
    gene2go={g:terms for g,terms in gene2go.items() if terms}
    # Custom mouse gene universe is the full target panel plus all input perturbations, including unseen Gata4.
    gene_set=sorted(gene2go);with_path=p/'gene_set.pkl'
    with with_path.open('wb') as f:pickle.dump(gene_set,f)
    for filename in ['gene2go_all.pkl','gene2go.pkl']:
        with (p/filename).open('wb') as f:pickle.dump(gene2go,f)
    # The author's custom graph builder writes ./data; isolate that relative cache.
    import os
    work=p/'work';(work/'data').mkdir(exist_ok=True,parents=True);os.chdir(work)
    data=PertData(str(p),gene_set_path=str(with_path),default_pert_graph=False)
    data.new_data_process(dataset_name='op2_complete',adata=source)
    assert len(data.adata)==5454 and 'Gata4' in data.node_map_pert
    labels=lambda genes:[g+'+ctrl' for g in genes]
    split={'train':['ctrl']+labels(cfg['split']['train']),'val':labels(cfg['split']['val']),'test':labels(cfg['split']['test'])}
    with (p/'split.pkl').open('wb') as f:pickle.dump(split,f)
    data.prepare_split(split='custom',seed=SEED,split_dict_path=str(p/'split.pkl'));data.train_gene_set_size=len(cfg['split']['train'])/26
    data.get_dataloader(batch_size=32,test_batch_size=64)
    control=dense(source.X[source.obs.original_condition=='ctrl']);ctrl=control.mean(0)
    model=GEARS(data,device='cpu')
    if (p/'HOLDOUT.json').exists():
        model.load_pretrained(str(p/'heldout_model'))
        print('RESUMED_LOCKED_HOLDOUT_MODEL',flush=True)
    else:
        model.model_initialize();model.train(epochs=20);model.save_model(str(p/'heldout_model'))
        pred=np.array([gears_infer(model,control,g).mean(0)-ctrl for g in cfg['split']['test']])
        immutable_eval('r6_gears',pred,source,cfg,{'graph_nodes':model.num_perts,'output_genes':model.num_genes,'original_model_and_loss':True,'custom_graph':'mouse GO, full panel and all perturbations; human default graph is not applicable'})
    # Inference ablation recorded separately; it is NOT a separately trained no-graph baseline.
    saved_sim=model.best_model.G_sim;saved_gene=model.best_model.G_coexpress
    saved_sim_weight=model.best_model.G_sim_weight;saved_gene_weight=model.best_model.G_coexpress_weight
    model.best_model.G_sim=torch.empty((2,0),dtype=torch.long);model.best_model.G_coexpress=torch.empty((2,0),dtype=torch.long)
    model.best_model.G_sim_weight=torch.empty(0);model.best_model.G_coexpress_weight=torch.empty(0)
    ablated=np.array([gears_infer(model,control,g).mean(0)-ctrl for g in cfg['split']['test']])
    dump(p/'NO_EDGE_INFERENCE_ABLATION.json',{'metrics':delta_metrics(ablated,truth_delta(source,cfg['split']['test'])[0]),'scope':'same fitted weights, removal at inference; NOT separately trained no-graph model'})
    model.best_model.G_sim=saved_sim;model.best_model.G_coexpress=saved_gene
    model.best_model.G_sim_weight=saved_sim_weight;model.best_model.G_coexpress_weight=saved_gene_weight
    # Train the same author model from scratch with self edges only. This is the
    # genuine no-neighbor control, distinct from the cheap inference ablation.
    diag_go=torch.arange(model.num_perts);diag_gene=torch.arange(model.num_genes)
    no_graph=GEARS(data,device='cpu')
    no_graph.model_initialize(G_go=torch.stack([diag_go,diag_go]),G_go_weight=torch.ones(model.num_perts),G_coexpress=torch.stack([diag_gene,diag_gene]),G_coexpress_weight=torch.ones(model.num_genes))
    no_graph.train(epochs=20);no_graph.save_model(str(p/'no_graph_model'))
    npred=np.array([gears_infer(no_graph,control,g).mean(0)-ctrl for g in cfg['split']['test']])
    dump(p/'NO_GRAPH_TRAINED_HOLDOUT.json',{'metrics':delta_metrics(npred,truth_delta(source,cfg['split']['test'])[0]),'scope':'independent author model fit, same training and validation conditions, self edges only'})
    # All26 final fit is prediction-only; heldout receipt is locked before fitting.
    all_conditions=labels(sum(cfg['split'].values(),[]));data.set2conditions={'train':['ctrl']+all_conditions,'val':all_conditions,'test':[]}
    data.train_gene_set_size=1.0
    data.get_dataloader(batch_size=32,test_batch_size=64);data.dataloader.pop('test_loader',None)
    final=GEARS(data,device='cpu');final.model_initialize();final.train(epochs=20);final.save_model(str(p/'final_model'))
    px=dense(parent.X);rows=wt.obs_names.get_indexer(parent.obs_names);tx=dense(wt.X)[rows]
    scale=(np.expm1(control).mean(0)+1e-3)/(np.expm1(tx).mean(0)+1e-3);mapped=np.log1p(np.expm1(tx)*scale)
    factual=gears_infer(final,mapped,'ctrl');cf=gears_infer(final,mapped,'Gata4')
    rate=np.log((np.expm1(np.maximum(cf,0))+1e-3)/(np.expm1(np.maximum(factual,0))+1e-3))
    out=rate_decode(px,rate);out[:,parent.var_names.get_loc('Gata4')]=0
    np.savez(p/'native_target_outputs.npz',factual=factual,counterfactual=cf)
    write_research('r6_gears',out,parent,{'source_cells':5454,'perturbations':26,'original_author_model':True,'final_validation':'training conditions only; final is not independent validation','heldout_receipt':sha(p/'HOLDOUT.json'),'cross_context_transfer':'author GEARS not designed for cross-celltype transfer; exploratory adapter'})

if __name__=='__main__':
    {'functional':functional_run,'scouter':scouter_run,'gears':gears_run}[sys.argv[1]]()
