from __future__ import annotations
import csv,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import io,sparse
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from .common import ROOT,ATLAS,sha,dump,dense
from .routes_local import graph_from_motif,ConditionalModel
from .algorithms import signal_delta,forbidden_perturbation,gene_split,fit_graph_comparator

# Explicit broad anatomical vocabulary, not a claim that subtypes are equivalent.
WT_GROUPS={'Neural Tube':'neural','Forebrain':'neural','NCC':'crest','V-CM':'cardiac','IFT-CM':'cardiac','aPHM':'cardiac','pPHM':'cardiac','JCF':'cardiac','d-CSE':'ectoderm','V-CSE':'ectoderm','pSE':'ectoderm','Intra-Endoth-1':'endothelial','Intra-Endoth-2':'endothelial','HEM-Endoth':'endothelial','Endo':'endothelial','D-FG':'endoderm','a-FG':'endoderm','Lateral FG':'endoderm','Gut Endoderm':'endoderm','EXE-Endoderm':'endoderm','Hindgut':'endoderm','PAM-1':'mesoderm','PAM-2':'mesoderm','PAM-3':'mesoderm','PAM-4':'mesoderm','ExEM-1':'mesoderm','ExEM-2':'mesoderm','LPM':'mesoderm','SOM':'mesoderm','Allantois':'mesoderm','Peri':'mesothelium'}

def atlas_group(s):
    s=s.lower()
    if any(x in s for x in ['neural crest']):return 'crest'
    if any(x in s for x in ['cardiomyo','cardiopharyngeal','pharyngeal mesoderm']):return 'cardiac'
    if any(x in s for x in ['endotheli','endocard','endotome']):return 'endothelial'
    if any(x in s for x in ['endoderm','foregut','midgut','hindgut','gut tube','thyroid']):return 'endoderm'
    if any(x in s for x in ['mesotheli','epicard']):return 'mesothelium'
    if any(x in s for x in ['mesoderm','mesenchyme','somitic','sclerotome','dermomyotome','allantois','forelimb']):return 'mesoderm'
    if any(x in s for x in ['neural','brain','spinal','optic','floor plate','neurons']):return 'neural'
    if any(x in s for x in ['ectoderm','epiderm','placod','otic']):return 'ectoderm'
    return 'unmapped'


def mapped_neighbors(rna,wt,ag,wg,fitcols,wt_train,components,k,seed):
    """Group-restricted mapping fitted only on designated feature columns."""
    indices=np.full((len(wt),k),-1,int);scales={};diag=[]
    for group in sorted(set(wg)-{'unmapped'}):
        ar=np.flatnonzero(ag==group);wr=np.flatnonzero(wg==group);tr=np.flatnonzero((wg==group)&wt_train)
        if len(ar)<k or len(tr)<20:continue
        am=rna[ar].mean(0);asd=np.maximum(rna[ar].std(0),0.05);wm=wt[tr].mean(0);wsd=np.maximum(wt[tr].std(0),0.05)
        a=(rna[ar][:,fitcols]-am[fitcols])/asd[fitcols];w=(wt[wr][:,fitcols]-wm[fitcols])/wsd[fitcols]
        pc=PCA(n_components=min(components,len(fitcols),len(ar)-1),svd_solver='randomized',random_state=seed).fit(a)
        az=pc.transform(a);wz=pc.transform(w);tree=cKDTree(az)
        dist,idx=tree.query(wz,k=k,workers=8);indices[wr]=ar[idx]
        scales[group]=(am,asd,wm,wsd)
        diag.append({'group':group,'atlas_cells':len(ar),'wt_cells':len(wr),'median_distance':float(np.median(dist))})
    return indices,scales,diag


def load_atlas(c,motif):
    manifest=json.loads((ATLAS/'MANIFEST.json').read_text());files={r['path']:r for r in manifest['files']}
    names=['data/state_input_counts.mtx','data/state_input_genes.tsv','data/metadata_cells_sanitized.tsv']
    for name in names:
        if sha(ATLAS/name)!=files[name]['sha256']:raise ValueError('atlas input hash mismatch '+name)
    meta=pd.read_csv(ATLAS/names[2],sep='\t');genes=pd.read_csv(ATLAS/names[1],sep='\t').gene.astype(str).tolist()
    if not (meta.stage=='E8.75').all():raise ValueError('atlas stage firewall')
    # Source v7's WT-only mask provenance is frozen in its original manifest/report.
    dump(c.run/'ATLAS_PERMIT.json',{'source_manifest':str((ATLAS/'MANIFEST.json').relative_to(ROOT)),'manifest_sha256':sha(ATLAS/'MANIFEST.json'),'input_hashes_verified':{n:files[n]['sha256'] for n in names},'exact_stage':'E8.75','cells':len(meta),'role':'WT-only representation and motif-context model; not signed evidence','authorizing_policy':'docs/batch2/compliance/protected_windows.yaml: allowed_default WT data','scientific_gate_unchanged':True})
    # Correct stale current-input index pointers only after byte verification.
    index=ROOT/'infra/bioinf-data-index/INDEX.tsv';text=index.read_text();lines=text.splitlines();header=lines[0].split('\t')
    for i,line in enumerate(lines[1:],1):
        r=dict(zip(header,line.split('\t')))
        if 'T3-S1A-STATE-JOIN-20260831-v5/data/' in r['local_path'] and Path(r['local_path']).name in [Path(n).name for n in names]:
            name='data/'+Path(r['local_path']).name;r['local_path']=str((ATLAS/name).relative_to(ROOT));r['sha256']=files[name]['sha256'];r['status']='sanitized_WT; current_v7_input_hash_verified_20260920; scientific_gate_unchanged';lines[i]='\t'.join(r[h] for h in header)
    index.write_text('\n'.join(lines)+'\n')
    summary=ROOT/'infra/bioinf-data-index/SUMMARY.md'
    note='\n## 2026-09-20 T3 新路线输入引用修正\n三个 exact E8.75 WT 当前输入索引由已清理 v5 改指实际存在的 `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data/`；三文件 SHA256 已按 v7 MANIFEST 实际重算通过。原始 MatrixMarket 是 genes×cells（27,669×68,910），建模时转置；不是新增外部数据，也不解除 S1 科学 gate。执行证据见 `artifacts/t3_next/` 的 r4/ATLAS_PERMIT.json。\n'
    if 'T3 新路线输入引用修正' not in summary.read_text():summary.open('a').write(note)
    aliases={'Bex3':'Ngfrap1','Ccn5':'Wisp2','Cemip2':'Tmem2','Cnmd':'Lect1','Selenop':'Sepp1'}
    lookup={g:i for i,g in enumerate(genes)};pg=[lookup.get(g,lookup.get(aliases.get(g,''),-1)) for g in c.genes]
    if min(pg)<0:raise ValueError('full panel alias coverage missing')
    print('r4 reading full 27,669 x 68,910 matrix',flush=True)
    counts=io.mmread(ATLAS/names[0]).tocsr().astype(np.float32)
    if counts.shape!=(len(genes),len(meta)):raise ValueError('atlas orientation mismatch')
    totals=np.asarray(counts.sum(0)).ravel();counts=counts.multiply(1e4/np.maximum(totals,1)).tocsr()
    direct=set(motif.loc[motif.Gata4>0,'gene_short_name']);candidates=[i for i,g in enumerate(genes) if g in direct and i not in pg]
    avg=np.asarray(counts[candidates].mean(1)).ravel();var=np.asarray(counts[candidates].power(2).mean(1)).ravel()-avg**2
    med=[candidates[i] for i in np.argsort(-var,kind='stable')[:c.cfg['r4']['max_offpanel_mediators']]]
    selected=pg+med;rna=counts[selected].T.toarray();np.log1p(rna,out=rna)
    del counts
    dump(c.run/'ATLAS_SELECTION.json',{'input_cells_used':len(meta),'input_genes_examined':len(genes),'matrix_orientation':'genes_by_cells','panel_aliases':aliases,'offpanel_mediators':[genes[i] for i in med],'selection':'WT normalized-count variance among Gata4 motif targets, fixed max64','full_panel':True,'no_cell_subsample':True})
    return rna,meta,np.array(c.genes+[genes[i] for i in med])


def r4(c):
    motif=c.motif();rna,meta,genes=load_atlas(c,motif);cfg=c.cfg['r4'];ag=np.array([atlas_group(s) for s in meta.state]);wg=np.array([WT_GROUPS.get(s,'unmapped') for s in c.labels])
    hold=np.array([j for j in range(500) if j%cfg['held_gene_modulo']==0 and j!=c.gi]);fitcols=np.array([j for j in range(500) if j not in hold and j!=c.gi]);train=c.blocks!=0
    idx,scales,mapping=mapped_neighbors(rna,c.x,ag,wg,fitcols,train,cfg['mapping_components'],cfg['n_neighbors'],c.cfg['seed'])
    supported=idx[:,0]>=0;pred=np.zeros((len(c.x),len(hold)),np.float32);base=pred.copy()
    for group,(am,asd,wm,wsd) in scales.items():
        wr=np.flatnonzero((wg==group)&supported)
        rp=rna[idx[wr]][:,:,hold].mean(1);pred[wr]=(rp-am[hold])/asd[hold]*wsd[hold]+wm[hold]
        # Stronger baseline: training WT cell-type mean (same held-out genes).
        for t in set(c.labels[wr]):
            ttrain=train&(c.labels==t);rr=wr[c.labels[wr]==t]
            base[rr]=c.x[ttrain][:,hold].mean(0) if ttrain.any() else wm[hold]
    test=(~train)&supported;y=c.x[test][:,hold]
    metric={'mapped_fraction':float(supported[c.rows].mean()),'heldout_gene_count':len(hold),'heldout_spatial_cells':int(test.sum()),'mapping_mse':float(np.mean((pred[test]-y)**2)),'celltype_baseline_mse':float(np.mean((base[test]-y)**2)),'groups':mapping,'unmapped_wt_types':sorted(set(c.labels[~supported])),'no_hidden_target_used':True}
    dump(c.run/'MAPPING_GATE.json',metric)
    if metric['mapped_fraction']<cfg['min_crossmodal_supported_fraction'] or metric['mapping_mse']>=metric['celltype_baseline_mse']:
        return c.finish('FAILED_MAPPING_GATE',full_atlas_mapping='COMPLETED',counterfactual_models='NOT_RUN_GATE_FAILED',gate=metric)
    idx,scales,mapping=mapped_neighbors(rna,c.x,ag,wg,np.arange(500),np.ones(len(c.x),bool),cfg['mapping_components'],cfg['n_neighbors'],c.cfg['seed'])
    ri=c.rows[idx[c.rows,0]>=0];positions=np.flatnonzero(idx[c.rows,0]>=0);latent=rna[idx[ri]].mean(1)
    zrna=np.zeros((len(rna),1));zquery=np.zeros((len(latent),1));types=ag;qtypes=wg[ri]
    outcomes=[]
    for augmented,lane in [(False,'r4panel'),(True,'r4mediator')]:
        width=len(genes) if augmented else 500;gg=genes[:width].tolist();parents,dropped=graph_from_motif(motif,gg,depth=2,maxparents=6)
        original=latent[:,:width].copy();cf=original.copy();cf[:,c.gi]=0
        for j,ps in parents.items():
            f=ConditionalModel('linear',10).fit(rna[:,ps],zrna,types,rna[:,j]);cf[:,j]=original[:,j]+f.predict(cf[:,ps],zquery,qtypes)-f.predict(original[:,ps],zquery,qtypes)
        delta=cf[:,:500]-original[:,:500];out=c.base.copy()
        for group,(am,asd,wm,wsd) in scales.items():
            mask=qtypes==group;out[positions[mask]]+=delta[mask]*(wsd/asd[:500])
        out[:,c.gi]=0;clip=float((out<0).mean());np.maximum(out,0,out=out)
        info={'width':width,'modeled_nodes':len(parents),'unmodeled_edges':len(dropped),'clip_fraction':clip};outcomes.append(info)
        if clip<=c.cfg['disaster_bounds']['negative_clip_fraction_max']:c.save(lane,out,extra=info)
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',gate=metric,models=outcomes)


def approved_manifest(path,required):
    """Explicit manifest binds provenance claims and exact file bytes before reads."""
    m=json.loads(Path(path).read_text())
    if m.get('task')!='T3:gata4' or m.get('status')!='APPROVED_SANITIZED' or m.get('forbidden_records_remaining')!=0:raise ValueError('manifest not approved/sanitized for task')
    for key in required:
        r=m['files'][key];p=ROOT/r['path']
        if sha(p)!=r['sha256']:raise ValueError('source hash mismatch '+key)
    if not m.get('license') or not m.get('source_reference') or not m.get('filter_receipt'):raise ValueError('missing source/terms/filter provenance')
    receipt=ROOT/m['filter_receipt']['path']
    if sha(receipt)!=m['filter_receipt']['sha256']:raise ValueError('filter receipt mismatch')
    audit=json.loads(receipt.read_text())
    if audit.get('forbidden_records_remaining')!=0 or audit.get('task')!='T3:gata4':raise ValueError('filter receipt does not establish task-scoped zero forbidden records')
    return m


def r5(c,manifest=None):
    if not manifest:
        p=ROOT/'infra/external_data/sanitized/T3-S1A-STATE-JOIN/OMNIPATH/omnipath_mouse_full.tsv';d=pd.read_csv(p,sep='\t')
        required=c.cfg['r5']['required_edge_fields'];missing=[k for k in required if k not in d.columns]
        dump(c.run/'SOURCE_AUDIT.json',{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rows':len(d),'columns':d.columns.tolist(),'missing_required_edge_fields':missing,'reason':'generic interactions do not establish ligand/receptor roles or edge-level target-free provenance'})
        return c.finish('BLOCKED_PROVENANCE',intrinsic_model='NOT_RUN',signal_on_off='NOT_RUN',permutation_diagnostic='NOT_RUN',missing=missing)
    m=approved_manifest(manifest,['edges']);edges=pd.read_csv(ROOT/m['files']['edges']['path'],sep='\t')
    required=c.cfg['r5']['required_edge_fields']
    if not all(k in edges for k in required):raise ValueError('incomplete ligand receptor edge schema')
    if not edges.target_phenocopy_free.astype(str).str.lower().isin(['true','1']).all():raise ValueError('unresolved edge provenance')
    edges=edges[edges[['ligand','receptor','target']].isin(c.genes).all(axis=1)].copy()
    if edges.empty:return c.finish('BLOCKED_PANEL_COVERAGE')
    k=c.cfg['r5']['neighbors'];dist,nn=cKDTree(c.coords).query(c.coords,k=k+1,workers=8);nn=nn[:,1:];dist=dist[:,1:];sigma=max(float(np.median(dist)),1e-6)
    weights=np.exp(-dist/sigma);weights/=weights.sum(1,keepdims=True)
    w=sparse.csr_matrix((weights.ravel(),(np.repeat(np.arange(len(c.x)),k),nn.ravel())),shape=(len(c.x),len(c.x)))
    z=np.column_stack([c.coords,np.log1p(np.expm1(c.x).sum(1))]);intr=np.zeros_like(c.x);coeff=[]
    for lig in edges.ligand.unique():
        li=c.genes.index(lig);model=ConditionalModel('linear',10).fit(c.x[:,[c.gi]],z,c.labels,c.x[:,li])
        intr[:,li]=model.predict(np.zeros((len(c.x),1)),z,c.labels)-model.predict(c.x[:,[c.gi]],z,c.labels)
    for r in edges.itertuples():
        li,ri,ti=[c.genes.index(g) for g in [r.ligand,r.receptor,r.target]]
        exposure=(w@c.x[:,li])*c.x[:,ri]/max(float(c.x[:,ri].mean()),1e-8)
        model=Ridge(10).fit(np.column_stack([exposure,z]),c.x[:,ti]);coeff.append((li,ri,ti,float(model.coef_[0])))
    nd=signal_delta(c.x,intr,w,coeff);rng=np.random.default_rng(c.cfg['seed']);perm=signal_delta(c.x,intr[rng.permutation(len(intr))],w,coeff)
    permutation_difference=float(np.mean((nd-perm)**2));dump(c.run/'SIGNAL_DIAGNOSTICS.json',{'edge_count':len(edges),'permutation_mse':permutation_difference,'signal_rms':float(np.sqrt(np.mean(nd**2))),'coefficients':coeff,'signal_sigma':sigma})
    if permutation_difference<1e-12:return c.finish('FAILED_SIGNAL_SPECIFICITY')
    for lane,d in [('r5off',intr),('r5on',intr+nd)]:
        out=c.base+d[c.rows];out[:,c.gi]=0;clip=float((out<0).mean())
        if clip<=c.cfg['disaster_bounds']['negative_clip_fraction_max']:c.save(lane,np.maximum(out,0))
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER')


def r6(c,manifest=None):
    if not manifest:
        candidates=[p for p in (ROOT/'infra/external_data').rglob('*permit*.json') if 'quarantine' not in str(p)]
        dump(c.run/'DATA_READINESS.json',{'declared_data_source':'none','searched_permit_manifests':[str(p.relative_to(ROOT)) for p in candidates],'auxiliary_links':'data/external/INDEX.tsv has model_input=false; not consumed','official_training_perturbations':['Mab21l2'],'min_required':c.cfg['r6']['min_perturbation_genes'],'required_interface':['expression','embedding','adjacency','filter_receipt'],'scientific_training':'NOT_RUN'})
        return c.finish('BLOCKED_DATA_NOT_READY',ridge_training='NOT_RUN',graph_training='NOT_RUN',gene_heldout_evaluation='NOT_RUN',target_inference='NOT_RUN')
    import anndata as ad
    m=approved_manifest(manifest,['expression','embedding','adjacency']);a=ad.read_h5ad(ROOT/m['files']['expression']['path'],backed='r')
    if m.get('embedding_role')!='WT_OR_ONTOLOGY_ONLY' or m.get('adjacency_role')!='WT_OR_ONTOLOGY_ONLY':raise ValueError('outcome-free graph and embedding provenance not declared')
    # Inspect metadata before reading any expression. This runner never sanitizes quarantine itself.
    if not {'condition','cell_type'}<=set(a.obs):raise ValueError('source metadata missing')
    conditions=a.obs.condition.astype(str).to_numpy();celltypes=a.obs.cell_type.astype(str).to_numpy()
    if any(forbidden_perturbation(x) for x in conditions):raise ValueError('forbidden perturbation remains')
    if len(set(celltypes))!=1:raise ValueError('first experiment requires one declared training context; cross-context not silently pooled')
    if m.get('species')!='mouse':raise ValueError('requires pre-audited one-to-one mouse-symbol object; no inferred orthology')
    if not set(c.genes)<=set(a.var_names):raise ValueError('source lacks full output panel')
    ids=a.var_names.get_indexer(c.genes);x=dense(a.X[:,ids]);a.file.close()
    if not np.isfinite(x).all() or (x<0).any():raise ValueError('invalid processed expression')
    ctrl=conditions=='ctrl'
    if ctrl.sum()<c.cfg['r6']['min_cells_per_condition']:raise ValueError('insufficient control cells')
    genes=[g for g in sorted(set(conditions)-{'ctrl'}) if not any(x in g for x in ['+',';',',',' ']) and np.sum(conditions==g)>=c.cfg['r6']['min_cells_per_condition']]
    if len(genes)<c.cfg['r6']['min_perturbation_genes']:return c.finish('BLOCKED_DATA_NOT_READY',usable_perturbation_genes=len(genes))
    emb=np.load(ROOT/m['files']['embedding']['path'],allow_pickle=False);eg=emb['genes'].astype(str).tolist();lookup={g:i for i,g in enumerate(eg)}
    if len(lookup)!=len(eg) or emb['embedding'].shape[0]!=len(eg) or not np.isfinite(emb['embedding']).all():raise ValueError('invalid/ambiguous embedding identities or values')
    if not set(genes+['Gata4'])<=set(eg):raise ValueError('missing outcome-free gene embeddings')
    mean=x[ctrl].mean(0);effects=np.stack([x[conditions==g].mean(0)-mean for g in genes]);train_genes,test_genes=gene_split(genes,c.cfg['seed']);pos={g:i for i,g in enumerate(genes)}
    selected=genes+['Gata4'];ii=[lookup[g] for g in selected];z=emb['embedding'][ii];full_adj=sparse.load_npz(ROOT/m['files']['adjacency']['path'])
    if full_adj.shape!=(len(eg),len(eg)) or not np.isfinite(full_adj.data).all() or (full_adj.data<0).any():raise ValueError('invalid graph matrix')
    adj=full_adj[ii][:,ii].toarray()
    y=np.vstack([effects,np.zeros((1,500))]);tr=[pos[g] for g in train_genes];te=[pos[g] for g in test_genes]
    report=fit_graph_comparator(z,y,adj,tr,te,epochs=c.cfg['r6']['epochs'],seed=c.cfg['seed'])
    truth=effects[te];scores={'no_change_mse':float(np.mean(truth**2)),'ridge_mse':float(np.mean((truth-report['ridge_prediction'])**2)),'graph_mse':float(np.mean((truth-report['graph_prediction'])**2)),'train_genes':train_genes,'test_genes':test_genes,'training_steps':report['training_steps'],'source_context':str(celltypes[0]),'target_context_generalization':'NOT_VALIDATED','model':'custom explicit two-layer GCN, not GEARS/TxPert reproduction'}
    dump(c.run/'GENE_HOLDOUT.json',scores)
    import torch
    torch.save(report['state_dict'],c.run/'graph_holdout.pt')
    if scores['graph_mse']>=min(scores['ridge_mse'],scores['no_change_mse']):return c.finish('FAILED_GENE_HOLDOUT',evaluation=scores)
    # Fresh final model uses all eligible source genes, never held-out Gata4 outcomes.
    final=fit_graph_comparator(z,y,adj,np.arange(len(genes)),np.array([len(genes)]),epochs=c.cfg['r6']['epochs'],seed=c.cfg['seed'])
    for lane,delta in [('r6ridge',final['ridge_prediction'][0]),('r6graph',final['graph_prediction'][0])]:
        out=c.base+delta;out[:,c.gi]=0;clip=float((out<0).mean())
        if clip<=c.cfg['disaster_bounds']['negative_clip_fraction_max']:c.save(lane,np.maximum(out,0),extra={'transfer':'cross-context unvalidated; residual in declared shared log-normalized units'})
    torch.save(final['state_dict'],c.run/'graph_final.pt')
    return c.finish('CANDIDATES_READY' if c.candidates else 'FAILED_DISASTER',evaluation=scores)
