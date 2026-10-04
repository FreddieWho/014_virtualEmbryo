"""Full target inference for native expression, state mass, and independent activity."""
from .common import *
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

ALIASES={'Bex3':'Ngfrap1','Ccn5':'Wisp2','Cemip2':'Tmem2','Cnmd':'Lect1','Selenop':'Sepp1'}

def sample_mass(states,target_mass,seed=SEED):
    """Integer state quotas, with exact identity when the predicted mass is WT."""
    n=len(states);expected=np.asarray(target_mass)*n;quota=np.floor(expected).astype(int)
    left=n-quota.sum();order=np.argsort(-(expected-quota),kind='mergesort');quota[order[:left]]+=1
    rng=np.random.default_rng(seed);selected=[]
    for state,wanted in enumerate(quota):
        rows=np.flatnonzero(states==state)
        if not len(rows):assert wanted==0;continue
        if wanted<=len(rows):selected.extend(rows if wanted==len(rows) else rng.choice(rows,wanted,replace=False))
        else:selected.extend(rows);selected.extend(rng.choice(rows,wanted-len(rows),replace=True))
    result=np.sort(np.array(selected,dtype=int));assert len(result)==n
    return result

def run():
    source,parent,wt=load_inputs();p=RUN/'native'
    receipt=json.loads((p/'COMPLETE.json').read_text())
    for f,h in receipt['outputs'].items():assert sha(p/f)==h
    native_genes=json.loads((p/'genes.json').read_text());gmap={g:i for i,g in enumerate(native_genes)}
    panel=parent.var_names.tolist();available=[gmap.get(g,gmap.get(ALIASES.get(g,''),-1)) for g in panel]
    mapped=np.array(available)>=0;ids=np.array(available)[mapped]
    f=np.load(p/'factual.npy',mmap_mode='r');d=np.load(p/'delta.npy',mmap_mode='r')
    factual=np.log1p(np.maximum(f[:,ids],0));cf=np.log1p(np.maximum(f[:,ids]+d[:,ids],0))
    # Gene-wise quantile scaling uses only factual WT values, never a target KO.
    ax=dense(wt.X).astype('float32');px=dense(parent.X).astype('float32');gi=panel.index('Gata4')
    rows=wt.obs_names.get_indexer(parent.obs_names);assert (rows>=0).all()
    factors=np.maximum(np.std(factual,axis=0),.05);tmean=ax[:,mapped].mean(0);tsd=np.maximum(ax[:,mapped].std(0),.05)
    # The deleted marker itself must not create a spurious fate transition.
    geometry=np.array([g!='Gata4' for g,b in zip(panel,mapped) if b])
    standard=((factual-factual.mean(0))/factors)[:,geometry]
    pca=PCA(32,random_state=SEED);pca.fit(standard);latent=pca.transform(standard)
    target=pca.transform(((ax[:,mapped]-tmean)/tsd)[:,geometry])
    nn=NearestNeighbors(n_neighbors=5,n_jobs=8).fit(latent)
    full_distance,full_nearest=nn.kneighbors(target)
    distance,nearest=full_distance[rows],full_nearest[rows];weights=1/(distance+1e-3);weights/=weights.sum(1,keepdims=True)
    # Each target cell receives its matched native cell ratios, not a state median.
    lograte=np.log((np.maximum(f[:,ids]+d[:,ids],0)+1e-3)/(np.maximum(f[:,ids],0)+1e-3))
    rate=np.zeros_like(px);rate[:,mapped]=(lograte[nearest]*weights[:,:,None]).sum(1)
    native=rate_decode(px,rate);native[:,gi]=0
    np.save(RUN/'native_rate.npy',rate)
    evidence={'native_receipt':sha(p/'COMPLETE.json'),'mapped_genes':int(mapped.sum()),'unmapped_genes':[g for g,b in zip(panel,mapped) if not b],'mapping':'WT standardization, PCA32, inverse-distance five native neighbors; cell-level count ratio','decoder':'unit native effect; no IQR scaling; observed zeros preserved','scientific_status':'EXPLORATORY_CROSS_PLATFORM','training_cells':68910}
    write_research('r1_celloracle',native,parent,evidence)
    # Legacy released adapter remains an immutable, named comparison.
    dump(RUN/'r1_celloracle/CONTROLS.json',{'WT_identity':'parent v0009','old_adapter':'scored legacy artifacts are read-only; no historical scores reinterpreted','direct_decoder_without_tool':'identity (rate=0)','same_decoder_identity_max_error':float(np.max(np.abs(rate_decode(px,np.zeros_like(px))-px)))})
    meta=pd.read_csv(p/'metadata.tsv',sep='\t',dtype=str);states=meta.state.to_numpy()
    states_order=sorted(set(states));smap={s:i for i,s in enumerate(states_order)};state_ids=np.array([smap[s] for s in states])
    # A native knockout changes where cells land on the WT state manifold.
    cf_latent=pca.transform(((cf-factual.mean(0))/factors)[:,geometry])
    native_nn=NearestNeighbors(n_neighbors=1,n_jobs=8).fit(latent)
    moved=native_nn.kneighbors(cf_latent,return_distance=False).ravel()
    moved[np.all(cf_latent==latent,axis=1)]=np.flatnonzero(np.all(cf_latent==latent,axis=1))
    transitions=np.zeros((len(states_order),len(states_order)))
    np.add.at(transitions,(state_ids,state_ids[moved]),1)
    transitions/=np.maximum(transitions.sum(1,keepdims=True),1)
    parent_states=state_ids[nearest[:,0]]
    mass0=np.bincount(parent_states,minlength=len(states_order)).astype(float)/len(px)
    mass1=mass0@transitions
    # If a desired destination has no target carrier support, redistribute among supported destinations.
    supported=mass0>0;unsupported_mass=float(mass1[~supported].sum());mass1[~supported]=0;mass1/=mass1.sum()
    selected=sample_mass(parent_states,mass1)
    np.save(RUN/'r2_sampling_indices.npy',selected);np.save(RUN/'r2_transition.npy',transitions)
    dump(RUN/'STATE_MASS.json',{'states':states_order,'wt':mass0.tolist(),'ko':mass1.tolist(),'unrepresented_destination_mass':unsupported_mass,'state_changes_native_cells':int(np.sum(state_ids!=state_ids[moved])),'hypothesis':'expression displacement on WT manifold proxies changes in state occupancy, not survival measurement'})
    write_research('r2_mass_only',px[selected],parent,{'mode':'mass only','state_mass_receipt':sha(RUN/'STATE_MASS.json')},selected)
    write_research('r2_mass_expression',native[selected],parent,{'mode':'mass plus native expression','state_mass_receipt':sha(RUN/'STATE_MASS.json')},selected)
    run_activity(ax,px,wt,parent,rows,gi,states[full_nearest[:,0]])

def activity_feature(x,weights,output_index):
    w=weights.copy();w[output_index]=0
    return x@w/(np.linalg.norm(w)+1e-8)

def run_activity(ax,px,wt,parent,rows,gi,assigned_states):
    """Regulon features exclude the predicted gene exactly; WT crossfit evaluates reconstruction only."""
    with (RUN/'native/coefficients.pkl').open('rb') as f:coefs=pickle.load(f)
    panel=parent.var_names.tolist();state_weights={}
    for state,matrix in coefs.items():
        # CellOracle propagation is delta.dot(coef): rows are TF sources.
        if 'Gata4' not in matrix.index:continue
        column=matrix.loc['Gata4'];w=np.zeros(500)
        for j,g in enumerate(panel):
            name=g if g in column.index else ALIASES.get(g,'')
            if name in column.index:w[j]=float(column.loc[name])
        w[gi]=0;state_weights[str(state)]=w
    assert any(np.count_nonzero(w)>1 for w in state_weights.values()),'Gata4 independent regulon unavailable'
    rate=np.zeros_like(px);audit=[];unsupported=[]
    for state in sorted(set(assigned_states)):
        ids=np.flatnonzero(assigned_states==state);positions=np.flatnonzero(assigned_states[rows]==state)
        w=state_weights.get(state,np.zeros(500))
        if len(ids)<10 or np.count_nonzero(w)<2:
            unsupported.append({'state':state,'WT_cells':len(ids),'target_cells':len(positions)});continue
        local=ax[ids];z=(local-local.mean(0))/np.maximum(local.std(0),.1)
        local_map={row:k for k,row in enumerate(ids)};target_local=np.array([local_map[rows[k]] for k in positions],dtype=int)
        fold=np.arange(len(ids))%5;train=fold!=0;test=~train
        for j in range(500):
            if j==gi:continue
            activity=activity_feature(z,w,j);reference=float(np.quantile(activity,.01))
            features=np.column_stack([activity,activity**2])
            model=Ridge(alpha=10).fit(features[train],local[train,j])
            pred=model.predict(features[test]);baseline=np.full(test.sum(),local[train,j].mean())
            audit.append({'state':state,'gene':panel[j],'activity_mse':float(np.mean((pred-local[test,j])**2)),'mean_mse':float(np.mean((baseline-local[test,j])**2)),'WT_cells':len(ids)})
            model=Ridge(alpha=10).fit(features,local[:,j])
            if len(positions):
                cf=np.column_stack([np.full(len(positions),reference),np.full(len(positions),reference**2)])
                rate[positions,j]=model.predict(cf)-model.predict(features[target_local])
    out=rate_decode(px,rate);out[:,gi]=0
    np.savez(RUN/'r3_regulon_weights.npz',**state_weights);np.save(RUN/'r3_activity_rate.npy',rate)
    dump(RUN/'ACTIVITY_AUDIT.json',{'diagnostic':'state-specific WT reconstruction holdout; NOT KO validation; rows are not independent animals','per_state_gene':audit,'state_regulon_nonzero':{s:int(np.count_nonzero(w)) for s,w in state_weights.items()},'unsupported_states':unsupported,'no_output_gene_in_its_activity':True,'inactive_reference':'predeclared state-specific WT activity 1st percentile; unvalidated functional loss scale','existing_RNA_control':'v0048 n2hurdle is the scored comparator; RNA baseline is not refit or relabelled'})
    write_research('r3_activity',out,parent,{'activity_audit':sha(RUN/'ACTIVITY_AUDIT.json'),'source_KO_validation':'NOT_IDENTIFIABLE_FOR_GATA4_REGULON_FROM_THIS_SOURCE','scientific_status':'OBSERVATIONAL_COUNTERFACTUAL_HYPOTHESIS'})

if __name__=='__main__':run()
