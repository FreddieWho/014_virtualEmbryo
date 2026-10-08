import argparse
p=argparse.ArgumentParser();p.add_argument("--repo",required=True);p.add_argument("--out",required=True);args=p.parse_args()
from pathlib import Path
import sys,json,hashlib,pickle
import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
ROOT=Path(args.repo).resolve();OUT=Path(args.out).resolve()
sys.path.insert(0,str(ROOT/'scripts'))
from t3_priority_six import common
common.GO=OUT/'GO'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((ROOT/'infra/external_data/reports/GO__DATA_AUDIT_REPORT.json').read_text())
for f in audit['files']:assert sha(OUT/'GO'/Path(f['path']).name)==f['sha256']
panel=json.loads((ROOT/'reports/t3_data_intake_20260920/panel_genes.json').read_text())
conditions=sorted(set(json.loads((ROOT/'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json').read_text())['condition_allowlist'])-{'ctrl'})
genes=common.go_sets();wanted=list(dict.fromkeys(panel+conditions+['Gata4']))
for g in wanted:genes.setdefault(g,set())
all_terms=sorted(set().union(*(genes[g] for g in wanted)));tmap={t:i for i,t in enumerate(all_terms)};rr=[];cc=[]
for i,g in enumerate(wanted):
 for t in sorted(genes[g]):rr.append(i);cc.append(tmap[t])
mat=sparse.csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(wanted),len(all_terms)))
svd=TruncatedSVD(n_components=min(128,len(wanted)-1,len(all_terms)-1),random_state=20260930)
embedding=svd.fit_transform(mat).astype('float32');norm=np.linalg.norm(embedding,axis=1,keepdims=True);embedding/=np.maximum(norm,1e-8)
np.savez(OUT/'GO_EMBEDDING.npz',genes=wanted,embedding=embedding)
with (OUT/'gene2go.pkl').open('wb') as f:pickle.dump({g:genes[g] for g in wanted},f)
expected='acdb554d47989a4d8230fb8acc0fc7d20ec40e12086b56ef1715afb8fee11e0d'
import sklearn,scipy
r={'schema':'t3.go.reconstruction.v1','embedding_path':str(OUT/'GO_EMBEDDING.npz'),'sha256':sha(OUT/'GO_EMBEDDING.npz'),'expected_sha256':expected,'byte_identical':sha(OUT/'GO_EMBEDDING.npz')==expected,'all_frozen_go_input_hashes_match':True,'original_code_sha256':sha(ROOT/'scripts/t3_priority_six/common.py'),'embedding_shape':list(embedding.shape),'no_perturbation_outcomes':True,'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},'seed':20260930}
(OUT/'GO_RECONSTRUCTION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
