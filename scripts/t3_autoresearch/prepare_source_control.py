"""Same approved220 OP2 control cells: full-gene WT features, no new KO labels."""
from pathlib import Path
import hashlib
import json
import sys
import anndata as ad
import numpy as np
from scipy import sparse

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from t3_next.source_roles import require_response_role


def main():
    manifest_path=ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'
    manifest=json.loads(manifest_path.read_text())
    review=require_response_role(manifest,ROOT,'SIGNED_RESPONSE')
    def checked(record):
        p=ROOT/record['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
        return p
    selected=ad.read_h5ad(checked(manifest['files']['expression']),backed='r')
    ctrl=selected.obs_names[selected.obs.condition.astype(str)=='ctrl'].tolist()
    assert len(ctrl)==220 and selected.obs.loc[ctrl,'model_input'].all()
    raw=ad.read_h5ad(checked(review['raw_source']),backed='r')
    assert raw.shape==(5454,32287) and set(raw.obs_names)==set(selected.obs_names)
    assert (raw.obs.loc[ctrl,'condition'].astype(str)=='ctrl').all()
    assert set(raw.obs.loc[ctrl,'sample'])=={'GSM8151756','GSM8151757'}
    # Explicit approved-control row slice before loading any raw expression.
    a=raw[ctrl,:].to_memory()
    raw.file.close();selected.file.close()
    symbols=a.var.gene_symbol.astype(str).to_numpy()
    cfg=json.loads((ROOT/'artifacts/t3_priority_six_20260930/CONFIG.json').read_text())
    genes=sum(cfg['split'].values(),[])+['Gata4']
    panel=(ROOT/'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    chosen=list(dict.fromkeys(genes+panel))
    counts=sparse.csr_matrix(a.X,dtype=float)
    total=np.asarray(counts.sum(1)).ravel()
    x=np.zeros((len(ctrl),len(chosen)))
    missing=[]
    for j,g in enumerate(chosen):
        ids=np.flatnonzero(symbols==g)
        if not len(ids):missing.append(g)
        else:x[:,j]=np.asarray(counts[:,ids].sum(1)).ravel()
    assert not missing, missing
    x=np.log1p(x*10000/np.maximum(total[:,None],1))
    ci={g:i for i,g in enumerate(chosen)}
    positions=[ci[g] for g in genes];outputs=[ci[g] for g in panel]
    centered=x-x.mean(0)
    sample_centered=x.copy()
    for sample in sorted(set(a.obs['sample'])):
        mask=a.obs['sample'].to_numpy()==sample
        sample_centered[mask]-=sample_centered[mask].mean(0)
    arrays={}
    for name,z in [('global',centered),('sample_centered',sample_centered)]:
        cov=z[:,positions].T@z[:,outputs]/(len(z)-1)
        sd=z.std(0,ddof=1)
        arrays[name]=cov/np.maximum(sd[positions,None]*sd[outputs][None,:],1e-8)
        arrays[name+'_linear_ko']=-x[:,positions].mean(0)[:,None]*cov/(sd[positions,None]**2+0.05)
    arrays['gene_mean']=x[:,positions].mean(0)
    arrays['gene_detection']=(x[:,positions]>0).mean(0)
    arrays['control_expression']=x[:,outputs]
    dest=ROOT/'artifacts/t3_autoresearch_features_20261002'
    out=dest/'SOURCE_CONTROL_FEATURES.npz'
    assert not out.exists()
    np.savez_compressed(out,genes=genes,panel=panel,control_ids=ctrl,**arrays)
    receipt={'role':'WT_OR_ONTOLOGY_ONLY; same220 already approved source controls; full gene features only',
             'source_review':manifest['compliance_review'],'raw_source':review['raw_source'],
             'selected_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
             'selection':'exact220 control obs_names from approved expression file; raw expression sliced before reading',
             'raw_cell_identity':'all5454 IDs identical to approved source; no additional source records authorized/read as model input',
             'source_controls':len(ctrl),'features_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
             'KO_expression_used_in_features':False,'heldout_target_truth_used':False,
             'limitations':['observational covariance, not identified causal response','220 controls, two samples, animal independence unknown']}
    (dest/'SOURCE_CONTROL_PROVENANCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
