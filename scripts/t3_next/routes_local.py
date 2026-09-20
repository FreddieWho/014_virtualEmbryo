from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler,SplineTransformer
from sklearn.decomposition import PCA
from .common import indexed,dense,dump
from .algorithms import rank_rebuild,distinct_donor_map


def r1(c):
    outcomes=[]
    for version,lane in [('v0022','r1graph'),('v0023','r1sign')]:
        import anndata as ad
        row,p=indexed(version);a=ad.read_h5ad(p)
        if not np.array_equal(a.obs_names,c.parent.obs_names) or list(a.var_names)!=c.genes:raise ValueError('donor identity mismatch')
        donor=dense(a.X);out=rank_rebuild(c.x[c.rows],donor,c.gi)
        if not np.array_equal(np.sort(out,axis=0),np.sort(donor,axis=0)):raise ValueError('column multisets changed')
        n=int(np.count_nonzero(out!=donor));outcomes.append({'donor':version,'changed_entries':n,'status':'NO_OP' if n==0 else 'NONTRIVIAL','column_multisets_exact':True})
        if n:c.save(lane,out,parent_version=version)
    return c.finish('CANDIDATES_READY' if c.candidates else 'NO_OP' if all(x['status']=='NO_OP' for x in outcomes) else 'FAILED_DISASTER',outcomes=outcomes)


def confounds(c):
    cfg=c.cfg['r2'];cycle=[c.genes.index(g) for g in cfg['cell_cycle_symbols'] if g in c.genes]
    if not cycle:raise ValueError('no observed cell-cycle confound genes')
    keep=[j for j in range(len(c.genes)) if j!=c.gi and j not in cycle]
    z=np.column_stack([np.log1p(np.expm1(c.x).sum(1)),c.x[:,cycle].mean(1),c.coords])
    # Mature-state proxy estimated independently inside each type. This is not measured developmental time.
    pc=np.zeros((len(c.x),2))
    for t in np.unique(c.labels):
        ix=np.flatnonzero(c.labels==t)
        if len(ix)>=5:pc[ix]=PCA(2,svd_solver='randomized',random_state=c.cfg['seed']).fit_transform(c.x[ix][:,keep])
    dump(c.run/'CONFOUNDS.json',{'cycle_genes':[c.genes[j] for j in cycle],'maturity':'two within-type WT PCs, proxy only','spatial_columns':3})
    return np.column_stack([z,pc])


def r2(c):
    cfg=c.cfg['r2'];motif=c.motif();direct=set(motif.loc[motif.Gata4>0,'gene_short_name'])
    activity_genes=[j for j,g in enumerate(c.genes) if g in direct and g!='Gata4' and g not in cfg['cell_cycle_symbols']]
    if len(activity_genes)<2:return c.finish('BLOCKED_ACTIVITY_COVERAGE',n_activity_genes=len(activity_genes))
    cov=confounds(c);score=np.full(len(c.x),np.nan);support=[]
    # Cross-fitted predictor of WT Gata4; marker target excluded and no KO rows read.
    for t in np.unique(c.labels):
        ix=np.flatnonzero(c.labels==t)
        if len(ix)<cfg['min_cells_per_type']:continue
        for fold in np.unique(c.blocks[ix]):
            train=ix[c.blocks[ix]!=fold];test=ix[c.blocks[ix]==fold]
            if len(train)<40 or not len(test):continue
            sx=StandardScaler().fit(c.x[train][:,activity_genes]);sz=StandardScaler().fit(cov[train])
            ztr=sz.transform(cov[train]);zte=sz.transform(cov[test])
            conf_y=Ridge(10).fit(ztr,c.x[train,c.gi]);yr=c.x[train,c.gi]-conf_y.predict(ztr)
            conf_x=Ridge(10).fit(ztr,sx.transform(c.x[train][:,activity_genes]))
            xr=sx.transform(c.x[train][:,activity_genes])-conf_x.predict(ztr)
            xt=sx.transform(c.x[test][:,activity_genes])-conf_x.predict(zte)
            model=Ridge(10).fit(xr,yr);score[test]=model.predict(xt)
    rng=np.random.default_rng(c.cfg['seed']);rec_ad=[];don_ad=[];rec_random=[];don_random=[]
    rowlookup={int(v):i for i,v in enumerate(c.rows)}
    maps=[]
    for t in np.unique(c.labels):
        for block in np.unique(c.blocks):
            pool=np.flatnonzero((c.labels==t)&(c.blocks==block)&np.isfinite(score))
            target=np.array([i for i in pool if int(i) in rowlookup],dtype=int)
            if len(pool)<20 or len(target)<4:continue
            low,high=np.quantile(score[pool],[cfg['donor_quantile'],cfg['recipient_quantile']])
            if high-low<1e-4:continue
            donors=pool[score[pool]<=low];rec=target[score[target]>=high]
            if len(donors)<5 or not len(rec):continue
            z=StandardScaler().fit_transform(cov[pool]);where={int(v):i for i,v in enumerate(pool)}
            tree=cKDTree(z);radius=float(np.quantile(tree.query(z,k=min(cfg['neighbor_k'],len(pool)))[0][:,-1],cfg['common_support_radius_quantile']))
            dtree=cKDTree(z[[where[int(v)] for v in donors]])
            dist,neigh=dtree.query(z[[where[int(v)] for v in target]],k=min(cfg['neighbor_k'],len(donors)))
            dmap=distinct_donor_map(target,donors,dist,neigh,c.x,c.gi,radius)
            available=np.array([v for v in target if int(v) in dmap],dtype=int)
            valid=[int(v) for v in rec if int(v) in dmap]
            if not valid:continue
            random_rec=rng.choice(available,len(valid),replace=False)
            for arm,recips in [('adaptive',valid),('random',random_rec)]:
                for v in recips:
                    outrow=rowlookup[int(v)];d=dmap[int(v)]
                    (rec_ad if arm=='adaptive' else rec_random).append(outrow);(don_ad if arm=='adaptive' else don_random).append(d)
                    maps.append({'arm':arm,'recipient_row':outrow,'donor_wt_row':d,'type':t,'block':int(block)})
            support.append({'type':t,'block':int(block),'pool':len(pool),'donors':len(donors),'adaptive_replaced':len(valid),'random_replaced':len(valid),'radius':radius})
    pd.DataFrame(maps).to_csv(c.run/'DONOR_MAP.tsv',sep='\t',index=False)
    dump(c.run/'SUPPORT.json',{'groups':support,'activity_genes':[c.genes[i] for i in activity_genes],'predicted_activity_sd':float(np.nanstd(score)),'activity_role':'observational cross-fit predictor, not causal activity','eligible_scored_wt':int(np.isfinite(score).sum())})
    if not rec_ad:return c.finish('BLOCKED_NO_SUPPORT',replaced=0)
    for lane,rr,dd in [('r2adapt',rec_ad,don_ad),('r2random',rec_random,don_random)]:
        if not np.array_equal(c.plabels[rr],c.labels[dd]):raise ValueError('cross-type donor')
        out=c.base.copy();out[rr]=c.x[dd];out[:,c.gi]=0
        if int(np.any(out!=c.base,axis=1).sum())!=len(rr):raise ValueError('nominal replacement count differs from actual changed cells')
        c.save(lane,out,extra={'replaced_cells':len(rr)})
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',matched_replacement_count=len(rec_ad),random_control_count=len(rec_random),limitations=['WT low activity is not KO','same-specimen spatial blocks','maturity inferred, not measured'])


def graph_from_motif(motif,genes,target='Gata4',depth=2,maxparents=6):
    """Frozen shortest-path layering: retain only edges from strictly earlier layers."""
    gindex={g:i for i,g in enumerate(genes)};scores={}
    for tf in [g for g in genes if g in motif.columns]:
        col=motif[['gene_short_name',tf]].groupby('gene_short_name')[tf].max()
        for gene,value in col[col>0].items():
            if gene in gindex and gene!=tf:scores[(gindex[tf],gindex[gene])]=float(value)
    root=gindex[target];dist={root:0}
    for d in range(depth):
        for (a,b) in sorted(scores):
            if dist.get(a)==d and b not in dist:dist[b]=d+1
    nodes=sorted((j for j in dist if j!=root),key=lambda j:(dist[j],genes[j]))
    parents={j:sorted([a for a,b in scores if b==j and a in dist and dist[a]<dist[j]],key=lambda a:(-scores[a,j],genes[a]))[:maxparents] for j in nodes}
    dropped=[{'source':genes[a],'target':genes[b],'reason':'outside_depth_or_nonforward_or_parent_cap'} for a,b in scores if b not in parents or a not in parents[b]]
    return parents,dropped


class ConditionalModel:
    def __init__(self,kind,alpha=10):self.kind=kind;self.alpha=alpha
    def fit(self,p,z,types,y):
        self.scaler=StandardScaler().fit(p);self.zscale=StandardScaler().fit(z);self.types=sorted(set(types));self.knots=None
        if self.kind=='bounded_spline':
            self.minimum=np.min(p,0);self.maximum=np.max(p,0)
            self.spline=SplineTransformer(n_knots=3,degree=2,knots='quantile',extrapolation='constant',include_bias=False).fit(p)
        self.model=Ridge(self.alpha).fit(self.features(p,z,types),y);return self
    def features(self,p,z,types):
        ps=self.scaler.transform(p) if self.kind=='linear' else self.spline.transform(p)
        one=np.column_stack([types==t for t in self.types]).astype(float)
        interactions=(ps[:,:,None]*one[:,None,:]).reshape(len(p),-1)
        return np.column_stack([ps,self.zscale.transform(z),one,interactions])
    def predict(self,p,z,types):return self.model.predict(self.features(p,z,types))


def r3(c):
    motif=c.motif();cfg=c.cfg['r3'];parents,dropped=graph_from_motif(motif,c.genes,depth=cfg['max_depth'],maxparents=cfg['max_parents'])
    dump(c.run/'TOPOLOGY.json',{'parents':{c.genes[k]:[c.genes[j] for j in v] for k,v in parents.items()},'unmodeled_edges':dropped,'rule':'shortest-path DAG; motif only no causal sign'})
    if not parents:return c.finish('BLOCKED_TOPOLOGY')
    # Context fixed before and after intervention, including original library size.
    z=np.column_stack([np.log1p(np.expm1(c.x).sum(1)),c.coords]);train=c.blocks!=0;test=~train
    results=[]
    for kind,lane in [('linear','r3linear'),('bounded_spline','r3spline')]:
        predictions=[];baseline=[];truth=[];models={};groups={}
        for j,ps in parents.items():groups.setdefault(tuple(ps),[]).append(j)
        for group_i,(ps_tuple,js) in enumerate(groups.items()):
            ps=list(ps_tuple)
            model=ConditionalModel(kind,cfg['ridge_alpha']).fit(c.x[train][:,ps],z[train],c.labels[train],c.x[train][:,js])
            predictions.extend(model.predict(c.x[test][:,ps],z[test],c.labels[test]).T);truth.extend(c.x[test][:,js].T)
            means={t:c.x[train&(c.labels==t)][:,js].mean(0) for t in set(c.labels[train])}
            fallback=c.x[train][:,js].mean(0)
            baseline.extend(np.stack([means.get(t,fallback) for t in c.labels[test]]).T)
            models[ps_tuple]=(js,ConditionalModel(kind,cfg['ridge_alpha']).fit(c.x[:,ps],z,c.labels,c.x[:,js]))
            if (group_i+1)%10==0:print(f'r3 {kind}: fitted {group_i+1}/{len(groups)} predictor groups ({len(parents)} nodes, full WT)',flush=True)
        pred=np.array(predictions);y=np.array(truth);b=np.array(baseline)
        actual=c.x[c.rows].copy();out=actual.copy();out[:,c.gi]=0;identity=actual.copy();zp=z[c.rows]
        for ps_tuple,(js,f) in models.items():
            ps=list(ps_tuple);actual_pred=f.predict(actual[:,ps],zp,c.plabels)
            out[:,js]=actual[:,js]+f.predict(out[:,ps],zp,c.plabels)-actual_pred
            identity[:,js]=actual[:,js]+f.predict(actual[:,ps],zp,c.plabels)-actual_pred
        if not np.allclose(identity,actual,atol=1e-6):raise ValueError('zero intervention identity failed')
        clip=float((out<0).mean());np.maximum(out,0,out=out)
        result={'model':kind,'modeled_genes':len(parents),'heldout_mse':float(np.mean((pred-y)**2)),'type_baseline_mse':float(np.mean((b-y)**2)),'negative_clip_fraction':clip,'zero_intervention_identity':True,'source_ko_validation':'NOT_APPLICABLE: Mab21l2 has no motif TF regulator entry','zero_input_support':'extrapolation; nonlinear uses constant boundary, not validated KO'};results.append(result)
        if clip<=c.cfg['disaster_bounds']['negative_clip_fraction_max']:c.save(lane,out,extra=result)
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',models=results,full_500_output=True)
