from pathlib import Path
import json, hashlib, gzip, pickle, sys
import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'artifacts/t3_priority_six_20260930'
REPORT = ROOT / 'reports/t3_priority_six_20260930'
GO = ROOT / 'infra/external_data/sanitized/T3/B2-T3-A1/GO'
SEED = 20260930

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def dump(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n');tmp.replace(path)

def dense(x):return x.toarray() if sparse.issparse(x) else np.asarray(x)

def load_inputs():
    import anndata as ad
    sys.path.insert(0,str(ROOT/'scripts'))
    from t3_next.source_roles import require_response_role
    manifest=json.loads((ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json').read_text())
    require_response_role(manifest,ROOT,'SIGNED_RESPONSE')
    p=manifest['files']['expression'];assert sha(ROOT/p['path'])==p['sha256']
    source=ad.read_h5ad(ROOT/p['path'])
    assert source.shape==(5454,500) and source.obs.model_input.all()
    parent_path=ROOT/'submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad'
    assert sha(parent_path)=='c6be65ec7d8c8a4b94bce936ff0cad985ac26f78c77ea3e4f68643f07076b088'
    parent=ad.read_h5ad(parent_path);wt=ad.read_h5ad(ROOT/'data/E8.75.h5ad')
    assert parent.shape==(7449,500) and parent.var_names.equals(source.var_names)
    return source,parent,wt

def go_sets():
    """Mouse GO positives with is_a/part_of closure; no perturbation measurements."""
    parents={};term=None
    for line in (GO/'go-basic.obo').read_text().splitlines():
        if line=='[Term]':term=None
        elif line.startswith('id: GO:'):term=line[4:];parents.setdefault(term,set())
        elif term and line.startswith('is_a: GO:'):parents[term].add(line.split()[1])
        elif term and line.startswith('relationship: part_of GO:'):parents[term].add(line.split()[2])
    cache={}
    def closure(t, trail=None):
        if t in cache:return cache[t]
        trail=set() if trail is None else trail
        if t in trail:return {t}
        v={t};trail=trail|{t}
        for p in parents.get(t,()):v.update(closure(p,trail))
        cache[t]=v;return v
    genes={}
    for name in ['MOUSE-mod.gaf.gz','MOUSE-uniprot.gaf.gz']:
        with gzip.open(GO/name,'rt') as f:
            for line in f:
                if line.startswith('!'):continue
                a=line.rstrip().split('\t')
                if len(a)<15 or 'NOT' in a[3].split('|'):continue
                genes.setdefault(a[2],set()).update(closure(a[4]))
    return genes

def prepare():
    RUN.mkdir(exist_ok=True,parents=True)
    source,parent,wt=load_inputs();conditions=sorted(set(source.obs.condition.astype(str))-{'ctrl'})
    assert len(conditions)==26
    order=np.random.default_rng(SEED).permutation(conditions).tolist()
    split={'train':order[9:],'val':order[6:9],'test':order[:6]}
    freeze={'schema':'ve.t3.priority-six.v1','seed':SEED,'source_cells':5454,'target_cells':7449,'genes':500,
      'source_manifest':'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json',
      'split':split,'split_unit':'entire perturbation gene; all cells and samples excluded together',
      'scouter':{'original_code':True,'embedding':'mouse GO is_a/part_of closure + SVD128; author-supported custom representation, NOT GenePT paper replication','epochs':40,'patience':5,'architecture':'author defaults 2048/512/64 -> 2048'},
      'gears':{'original_code':True,'epochs':20,'hidden_size':64,'go_graph':'mouse GO graph over complete panel + all26 perturbations + Gata4; original custom gene-set API','coexpression':'training conditions only'},
      'linear':{'ridge_alpha':10.,'bilinear':'GO embedding x WT sample-control PCA8 context'},
      'native':{'atlas_cells':68910,'selected_genes':2000,'alpha':10,'k':30,'propagation':3},
      'decoder':'paired source/native factual versus counterfactual count ratios, log1p target intensity; no E9.5 IQR multiplier',
      'limitations':['no matched Gata4 target truth','adult cardiac fibroblast to embryo transfer unvalidated','GO Scouter representation variant','source samples not established independent animals'],
      'controls':['WT identity','training perturbation mean','functional linear','GO identity/no edges for GEARS','permuted condition embeddings'],
      'final_refit':'after immutable holdout evaluation, train on all26 conditions; final predictions are not validation',
      'status':'DESIGN_FROZEN'}
    frozen=RUN/'CONFIG.json'
    if frozen.exists():assert json.loads(frozen.read_text())==freeze
    else:dump(frozen,freeze)
    genes=go_sets()
    wanted=list(dict.fromkeys(source.var_names.tolist()+conditions+['Gata4']))
    # Retain even missing ontology genes as explicit isolated nodes; do not drop cells.
    for g in wanted:genes.setdefault(g,set())
    all_terms=sorted(set().union(*(genes[g] for g in wanted)))
    tmap={t:i for i,t in enumerate(all_terms)}
    rr=[];cc=[]
    for i,g in enumerate(wanted):
        for t in sorted(genes[g]):rr.append(i);cc.append(tmap[t])
    mat=sparse.csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(wanted),len(all_terms)))
    from sklearn.decomposition import TruncatedSVD
    svd=TruncatedSVD(n_components=min(128,len(wanted)-1,len(all_terms)-1),random_state=SEED)
    embedding=svd.fit_transform(mat).astype('float32')
    norm=np.linalg.norm(embedding,axis=1,keepdims=True);embedding/=np.maximum(norm,1e-8)
    np.savez(RUN/'GO_EMBEDDING.npz',genes=wanted,embedding=embedding)
    with (RUN/'gene2go.pkl').open('wb') as f:pickle.dump({g:genes[g] for g in wanted},f)
    dump(RUN/'INPUT_LOCK.json',{'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json',ROOT/'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json',GO/'go-basic.obo',GO/'MOUSE-mod.gaf.gz',GO/'MOUSE-uniprot.gaf.gz',ROOT/'data/E8.75.h5ad']},'missing_go':[g for g in wanted if not genes[g]],'config_sha256':sha(frozen)})
    print('PREPARED',source.shape,parent.shape,split,flush=True)

def rate_decode(x, rate):
    """Nonnegative observed-intensity decoder, exact identity for zero effect."""
    return np.log1p(np.expm1(x)*np.exp(np.clip(rate,-30,30))).astype('float32')

def mean_rate(factual,counterfactual):
    f=np.maximum(np.asarray(factual),0);c=np.maximum(np.asarray(counterfactual),0)
    return np.log((np.expm1(c).mean(0)+1e-3)/(np.expm1(f).mean(0)+1e-3))

def write_research(lane, out, parent, evidence, indices=None):
    import anndata as ad
    p=RUN/lane;p.mkdir(exist_ok=True)
    assert out.shape==(7449,500) and np.isfinite(out).all() and out.min()>=0
    a=parent.copy() if indices is None else parent[indices].copy()
    if indices is not None:a.obs_names=[f'{lane}_{i:05}' for i in range(len(indices))]
    a.X=out.astype('float32');a.uns={'t3_priority_six':{'lane':lane,'config_sha256':sha(RUN/'CONFIG.json')}}
    a.write_h5ad(p/'research.h5ad',compression='gzip')
    dump(p/'RESULT.json',dict(evidence,task='T3:gata4',status='FULL_TARGET_INFERENCE_COMPLETE_RESEARCH',shape=list(a.shape),sha256=sha(p/'research.h5ad'),server_score='NOT_RUN',target_validation='NOT_RUN_NO_MATCHED_GATA4_TRUTH'))
    print('TARGET_COMPLETE',lane,flush=True)

def delta_metrics(pred, truth):
    pred=np.asarray(pred);truth=np.asarray(truth)
    return {'delta_mse':float(np.mean((pred-truth)**2)),
      'delta_cosine':float(np.sum(pred*truth)/(np.linalg.norm(pred)*np.linalg.norm(truth)+1e-12)),
      'direction_accuracy_nontrivial':float(np.mean(np.sign(pred[np.abs(truth)>.05])==np.sign(truth[np.abs(truth)>.05]))) if (np.abs(truth)>.05).any() else None,
      'n_conditions':int(len(truth)),'n_output_genes':int(truth.shape[-1])}

if __name__=='__main__':prepare()
