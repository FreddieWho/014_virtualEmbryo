"""Read-only route diagnostics, no new candidate or GCN training."""
from pathlib import Path
import csv, hashlib, json
import anndata as ad
import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
out = {}
rows = {r['version']: r for r in csv.DictReader(open(ROOT/'submissions/INDEX.tsv'), delimiter='\t') if r['board']=='T3:gata4'}
hashes = {}
def matrix(version):
    r = rows[version]; p = ROOT/r['path']
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest == r['sha256']
    hashes[r['path']] = digest
    a = ad.read_h5ad(p)
    return a, a.X.toarray() if sparse.issparse(a.X) else np.asarray(a.X)
parent, base = matrix('v0009')
for old, new in [('v0022','v0026'), ('v0023','v0027'), ('v0032','v0033')]:
    _, x = matrix(old); a, y = matrix(new)
    d = y-x
    out[old+'_'+new] = {'changed_entries': int(np.count_nonzero(d)), 'rms': float(np.sqrt(np.mean(d.astype(float)**2))),
        'max_abs': float(np.abs(d).max()), 'changed_genes': a.var_names[np.any(d!=0,axis=0)].tolist(),
        'column_multisets_equal': bool(np.array_equal(np.sort(x,axis=0),np.sort(y,axis=0)))}
manifest_path = ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'
m = json.loads(manifest_path.read_text())
for rec in m['files'].values():
    p=ROOT/rec['path']; digest=hashlib.sha256(p.read_bytes()).hexdigest(); assert digest==rec['sha256']; hashes[rec['path']]=digest
a=ad.read_h5ad(ROOT/m['files']['expression']['path'])
x=a[:,parent.var_names].X; x=x.toarray() if sparse.issparse(x) else np.asarray(x)
cond=a.obs.condition.astype(str).to_numpy()
hold_path=ROOT/'artifacts/t3_next/T3-R6-OP2-20260921-v1/GENE_HOLDOUT.json'
s=json.loads(hold_path.read_text())
ctrl=x[cond=='ctrl'].mean(0)
effects={g:x[cond==g].mean(0)-ctrl for g in s['train_genes']+s['test_genes']}
mean_train=np.stack([effects[g] for g in s['train_genes']]).mean(0)
truth=np.stack([effects[g] for g in s['test_genes']])
out['r6_mean_control']={'train_genes':s['train_genes'],'test_genes':s['test_genes'],
    'mean_response_mse':float(np.mean((truth-mean_train)**2)), 'no_change_mse':float(np.mean(truth**2)),
    'recorded_graph_mse':s['graph_mse'], 'recorded_ridge_mse':s['ridge_mse'],
    'method':'Training-only unweighted mean perturbation response, no held-out labels used in prediction.',
    'obs_columns':list(a.obs.columns)}
if 'sample' in a.obs:
    samples=a.obs['sample'].astype(str).to_numpy()
    out['r6_sample_counts']={str(sam):{g:int(np.sum((samples==sam)&(cond==g))) for g in sorted(set(cond))} for sam in sorted(set(samples))}
out['parent_zero_fraction']=float(np.mean(base==0))
import torch
torch.set_num_threads(8)
genes=sorted(effects)
emb=np.load(ROOT/m['files']['embedding']['path'],allow_pickle=False)
names=emb['genes'].astype(str).tolist(); ii=[names.index(g) for g in genes+['Gata4']]
z=emb['embedding'][ii].astype(np.float32)
z=(z-z[:-1].mean(0))/np.maximum(z[:-1].std(0),1e-4)
adj=sparse.load_npz(ROOT/m['files']['adjacency']['path'])[ii][:,ii].toarray().astype(np.float32)
adj+=np.eye(len(ii),dtype=np.float32); adj/=np.maximum(adj.sum(1,keepdims=True),1e-8)
state=torch.load(ROOT/'artifacts/t3_next/T3-R6-OP2-20260921-v1/graph_final.pt',map_location='cpu',weights_only=True)
h=torch.nn.Linear(z.shape[1],32); last=torch.nn.Linear(32,500)
h.load_state_dict(state['h']); last.load_state_dict(state['out'])
with torch.no_grad():
    at=torch.from_numpy(adj); delta=last(at@torch.relu(h(at@torch.from_numpy(z)))).numpy()[-1]
gi=list(parent.var_names).index('Gata4')
out['r6_additive_diagnostic']={}
for alpha in [1.0,0.1,0.01]:
    cf=base+alpha*delta; cf[:,gi]=0; neg=cf<0
    out['r6_additive_diagnostic'][str(alpha)]={'negative_fraction':float(neg.mean()),
        'negative_entries_at_parent_zero':int(np.sum(neg&(base==0))),
        'negative_entries':int(neg.sum()), 'diagnostic_only_not_candidate':True}
out['input_sha256']=hashes
out['manifest_sha256']=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
out['holdout_receipt_sha256']=hashlib.sha256(hold_path.read_bytes()).hexdigest()
(Path(__file__).parent/'CHECKS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['input_sha256','r6_sample_counts']},ensure_ascii=False))
