"""Prepare reviewed R6 inputs; never train a response predictor or make candidates."""
import csv
import gc
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/t3_r56_launch_20260921'
OUT = ROOT/'infra/external_data/sanitized/T3-R6-OP2-20260921'
RAW = ROOT/'infra/external_data/quarantine/T3-NEXT-R56-20260920/filtered/GSE261783_OP2_resting_provisional_raw.h5ad'
ATLAS = ROOT/'artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7'
POLICY = ROOT/'docs/coordination/T3_EXTERNAL_DATA_POLICY_20260921.md'
SOURCE = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE261783'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def bound(p):
    return {'path':str(p.relative_to(ROOT)), 'sha256':sha(p)}


def dump(p,x):
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')


def table(p,rows):
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)


def main():
    import anndata as ad
    import numpy as np
    import pandas as pd
    from scipy import io,sparse
    from scripts.t3_next.algorithms import gene_split
    from scripts.t3_next.source_roles import require_response_role
    if OUT.exists():raise SystemExit('Refusing to overwrite prior prepared inputs')
    REPORT.mkdir(exist_ok=True,parents=True)
    old=json.loads((ROOT/'reports/t3_data_intake_20260920/FIBRO_FILTER_RECEIPT.json').read_text())
    assert sha(RAW)==old['sha256']
    a=ad.read_h5ad(RAW,backed='r')
    obs=a.obs.copy();conditions=sorted(obs.condition.astype(str).unique())
    assert set(obs['sample'].astype(str))=={'GSM8151756','GSM8151757'}
    assert len(set(obs.cell_type.astype(str)))==1
    assert len(conditions)==27 and 'ctrl' in conditions
    assert not set(x.upper() for x in conditions)&{'GATA4','GATA6','CTNNB1','MESP1'}
    assert all(not any(c in x for c in ['+',';',',',' ']) for x in conditions)
    assert all(n>=20 for n in obs.condition.value_counts())
    review_rows=[]
    for g in conditions:
        rationale='Selected single-guide perturbation in 8-week adult mouse resting cardiac fibroblasts; source studies fibrotic activation, not an E8.75 embryonic target-knockout condition'
        if g in {'Chd4','Smarca4','Yy1'}:
            rationale+='; re-reviewed: prior cardiac-development/cofactor literature concerns different experiments and is not evidence that these adult fibroblast records phenocopy the held-out embryonic genotype'
        if g=='ctrl':rationale='Explicit non-targeting guide controls; ambiguous/unassigned cells were excluded by the original filter'
        review_rows.append(dict(condition=g,cells=int((obs.condition==g).sum()),classification='ALLOWED',
            scope='selected OP2 resting adult fibroblast records only',source_reference=SOURCE,reason=rationale))
    table(REPORT/'CONDITION_REVIEW.tsv',review_rows)
    review=dict(task='T3:gata4',source_reference=SOURCE,policy_version='T3_EXTERNAL_DATA_20260921',
        policy=bound(POLICY),review_status='COMPLETED',classification='ALLOWED',
        prohibited_records_remaining=0,allowed_response_roles=['SIGNED_RESPONSE','RESPONSE_SHAPE_ONLY'],
        condition_allowlist=conditions,license_status='PERMITTED',
        license='CC-BY-4.0; author-linked Zenodo doi:10.5281/zenodo.14794723',
        source_context_review='GSE261783 GSM8151756/57: single-gene CRISPR loss-of-function, resting OP2 cardiac fibroblasts isolated from 8-week mice; original publication doi:10.1038/s41467-025-66597-9. No selected protected embryonic genotype or equivalent phenotype evidence identified. This is a scoped evidence-based judgment, not proof of universal absence of phenocopy.',
        raw_source=bound(RAW),condition_review=bound(REPORT/'CONDITION_REVIEW.tsv'),
        previous_filter=bound(ROOT/'reports/t3_data_intake_20260920/FIBRO_FILTER_RECEIPT.json'),
        unselected_source_records='NOT_AUTHORIZED_BY_THIS_REVIEW; no blanket prohibited classification',
        organizer_clearance='NOT_REQUIRED_NO_SPECIFIC_UNRESOLVED_RULE_BOUNDARY_IDENTIFIED',
        scientific_limits=['adult fibroblast to embryo transfer unvalidated','replicate sample labels do not establish independent donors','no claim to identify Gata4 causal effects'])
    # Persist a new review and scope permit before reading raw expression values.
    dump(REPORT/'SOURCE_REVIEW.json',review)
    m=dict(task='T3:gata4',status='APPROVED_SANITIZED',source_reference=SOURCE,
        allowed_response_role='SIGNED_RESPONSE',compliance_review=bound(REPORT/'SOURCE_REVIEW.json'))
    require_response_role(m,ROOT,'SIGNED_RESPONSE')
    dump(REPORT/'RAW_PROCESSING_PERMIT.json',m|{'raw_source':bound(RAW),'allowed_operations':['normalize selected records','map fixed panel','build representation from separately permitted WT']})
    OUT.mkdir(parents=True)
    panel=json.loads((ROOT/'reports/t3_data_intake_20260920/panel_genes.json').read_text())
    positions=[]
    for gene in panel:
        ii=np.flatnonzero(a.var.gene_symbol.astype(str).to_numpy()==gene)
        assert len(ii)==1,gene
        positions.append(int(ii[0]))
    print('source approved; normalizing full-library counts before selecting 500 genes',flush=True)
    full=a.X[:,:]
    assert np.isfinite(full.data if sparse.issparse(full) else full).all()
    assert (full.data if sparse.issparse(full) else full).min()>=0
    total=np.asarray(full.sum(axis=1)).ravel();assert (total>0).all()
    x=full[:,positions].toarray() if sparse.issparse(full) else full[:,positions]
    x=np.log1p(x.astype(np.float64)*10000/total[:,None]).astype(np.float32)
    a.file.close();del full;gc.collect()
    obs['model_input']=True;obs['permit_status']='APPROVED_SANITIZED'
    ad.AnnData(X=x,obs=obs,var=pd.DataFrame(index=panel),uns={'normalization':'log1p counts per 10000; denominator all 32287 retained gene features',
        'source_review':str((REPORT/'SOURCE_REVIEW.json').relative_to(ROOT))}).write_h5ad(OUT/'expression.h5ad',compression='gzip')
    files={r['path']:r for r in json.loads((ATLAS/'MANIFEST.json').read_text())['files']}
    names=['data/state_input_counts.mtx','data/state_input_genes.tsv','data/metadata_cells_sanitized.tsv']
    for name in names:assert sha(ATLAS/name)==files[name]['sha256']
    meta=pd.read_csv(ATLAS/names[2],sep='\t');ag=pd.read_csv(ATLAS/names[1],sep='\t').gene.astype(str).tolist()
    assert (meta.stage=='E8.75').all()
    genes=sorted(set(conditions)-{'ctrl'})+['Gata4']
    assert len(set(genes))==len(genes) and all(ag.count(g)==1 for g in genes)
    print('building outcome-free profiles from all 68910 permitted WT atlas cells',flush=True)
    counts=io.mmread(ATLAS/names[0]).tocsr().astype(np.float32)
    assert counts.shape==(len(ag),len(meta))
    library=np.asarray(counts.sum(axis=0)).ravel();assert (library>0).all()
    z=counts[[ag.index(g) for g in genes]].toarray()
    del counts;gc.collect()
    z=np.log1p(z.astype(np.float64)*10000/library[None,:])
    labels=meta.celltype_extended_atlas.fillna('UNANNOTATED').astype(str).to_numpy()
    groups=sorted(set(labels));embedding=np.stack([z[:,labels==g].mean(axis=1) for g in groups],axis=1).astype(np.float32)
    np.savez_compressed(OUT/'embedding.npz',genes=np.array(genes),embedding=embedding,features=np.array(groups))
    norm=np.linalg.norm(embedding,axis=1);assert (norm>0).all()
    cosine=(embedding@embedding.T)/(norm[:,None]*norm[None,:]);np.fill_diagonal(cosine,0)
    adjacency=np.zeros_like(cosine)
    for i in range(len(genes)):
        nn=np.argsort(-cosine[i],kind='stable')[:5];adjacency[i,nn]=np.maximum(cosine[i,nn],0)
    adjacency=(adjacency+adjacency.T)/2;np.fill_diagonal(adjacency,1)
    sparse.save_npz(OUT/'adjacency.npz',sparse.csr_matrix(adjacency))
    graph_receipt=dict(role='WT_OR_ONTOLOGY_ONLY',source_manifest=bound(ATLAS/'MANIFEST.json'),
        inputs={name:bound(ATLAS/name) for name in names},cells=len(meta),genes=genes,features=groups,
        construction='All permitted exact-E8.75 WT cells; per-cell library normalization over all atlas genes; mean log expression for each pre-existing cell type; positive cosine top5 neighbors, symmetrized, self loops',
        perturbation_response_used=False,source_cell_subset=False)
    dump(REPORT/'GRAPH_PROVENANCE.json',graph_receipt)
    dump(REPORT/'FILTER_RECEIPT.json',dict(task='T3:gata4',forbidden_records_remaining=0,
        scope='selected 5454 cells, 26 perturbations plus explicit controls; not entire source',
        source_review=bound(REPORT/'SOURCE_REVIEW.json'),raw_source=bound(RAW),
        expression=bound(OUT/'expression.h5ad'),graph_provenance=bound(REPORT/'GRAPH_PROVENANCE.json')))
    m.update(forbidden_records_remaining=0,license='CC-BY-4.0',species='mouse',model_input=True,
        cell_type=str(obs.cell_type.iloc[0]),embedding_role='WT_OR_ONTOLOGY_ONLY',adjacency_role='WT_OR_ONTOLOGY_ONLY',
        filter_receipt=bound(REPORT/'FILTER_RECEIPT.json'),
        files={k:bound(OUT/n) for k,n in [('expression','expression.h5ad'),('embedding','embedding.npz'),('adjacency','adjacency.npz')]})
    dump(REPORT/'SOURCE_MANIFEST.json',m)
    from scripts.t3_next.routes_extended import approved_manifest
    approved_manifest(REPORT/'SOURCE_MANIFEST.json',['expression','embedding','adjacency'])
    require_response_role(m,ROOT,'SIGNED_RESPONSE')
    check=ad.read_h5ad(OUT/'expression.h5ad',backed='r')
    assert list(check.var_names)==panel and check.shape==(5454,500)
    check.file.close()
    cfg=json.loads((ROOT/'configs/t3_next/design.json').read_text())
    train,test=gene_split(genes[:-1],cfg['seed'])
    dump(REPORT/'READINESS.json',dict(status='READY_FOR_R6_TRAINING',cells=5454,perturbations=26,
        controls=int((obs.condition=='ctrl').sum()),panel_genes=500,embedding_shape=list(embedding.shape),
        adjacency_shape=list(adjacency.shape),planned_train_genes=train,planned_test_genes=test,
        source_manifest=bound(REPORT/'SOURCE_MANIFEST.json'),preparation_code=bound(Path(__file__)),
        predictor_training='NOT_RUN',gene_holdout_evaluation='NOT_RUN',target_inference='NOT_RUN',
        candidates='NOT_GENERATED',blocks_submission=False))
    print('READY_FOR_R6_TRAINING: 5454 cells / 26 perturbations / 500 genes; training NOT_RUN',flush=True)


if __name__=='__main__':main()
