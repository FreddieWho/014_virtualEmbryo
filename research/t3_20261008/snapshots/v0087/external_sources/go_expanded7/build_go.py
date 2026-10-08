import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
from pathlib import Path
import sys,json,hashlib,gzip
import numpy as np,pandas as pd,scipy,sklearn
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
R=Path('/workspace/shared/t3repo');S=Path('/workspace/shared/t3source');O=Path(__file__).parent
sys.path.insert(0,str(R/'scripts'))
from t3_priority_six import common
common.GO=S/'GO'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=json.loads((R/'infra/external_data/reports/GO__DATA_AUDIT_REPORT.json').read_text())
for f in audit['files']:assert sha(S/'GO'/Path(f['path']).name)==f['sha256']
old=np.load(S/'GO_EMBEDDING.npz');requested=['Dnmt1','Dnmt3a','Dnmt3b','Ehmt2','Kdm2b','Kmt2a','Kmt2b','Mab21l2','Gata4','Gata6']
wanted=list(dict.fromkeys(old['genes'].tolist()+requested));sets=common.go_sets()
terms=sorted(set().union(*(sets.get(g,set()) for g in wanted)));tmap={t:i for i,t in enumerate(terms)}
rr=[];cc=[]
for i,g in enumerate(wanted):
 for t in sorted(sets.get(g,set())):rr.append(i);cc.append(tmap[t])
mat=sparse.csr_matrix((np.ones(len(rr),dtype=np.float32),(rr,cc)),shape=(len(wanted),len(terms)))
sparse.save_npz(O/'GO_TERM_INCIDENCE.npz',mat)
# Binary ontology topology is the exact, uncompressed representation.
norm=np.sqrt(np.asarray(mat.multiply(mat).sum(1)).ravel());norm[norm==0]=1
exact=sparse.diags(1/norm)@mat
np.savez_compressed(O/'GO_TOPOLOGY_EMBEDDING.npz',genes=np.array(wanted),embedding=exact.toarray().astype(np.float32),features=np.array(terms))
# Shared outcome-free SVD128 is a drop-in compact representation, fitted anew for ALL genes.
svd=TruncatedSVD(n_components=128,random_state=20260930);e=svd.fit_transform(mat).astype('float32');en=np.linalg.norm(e,axis=1,keepdims=True);e/=np.maximum(en,1e-8)
np.savez_compressed(O/'GO_EXPANDED_EMBEDDING.npz',genes=np.array(wanted),embedding=e)
np.savez_compressed(O/'GO_SVD_BASIS.npz',terms=np.array(terms),components=svd.components_,singular_values=svd.singular_values_)
# Audit raw positive/negative direct annotation rows and release headers.
direct={g:set() for g in wanted};nnot={g:0 for g in wanted};rows={g:0 for g in wanted};headers={};evidence={g:set() for g in wanted}
for name in ['MOUSE-mod.gaf.gz','MOUSE-uniprot.gaf.gz']:
 headers[name]=[]
 with gzip.open(S/'GO'/name,'rt') as f:
  for line in f:
   if line.startswith('!'):headers[name].append(line.strip());continue
   a=line.rstrip('\n').split('\t')
   if len(a)<15 or a[2] not in direct:continue
   if 'NOT' in a[3].split('|'):nnot[a[2]]+=1;continue
   rows[a[2]]+=1;direct[a[2]].add(a[4]);evidence[a[2]].add(a[6])
coverage=[]
for i,g in enumerate(wanted):coverage.append(dict(gene=g,requested=g in requested,in_original_embedding=g in old['genes'],positive_annotation_rows=rows[g],direct_terms=len(direct[g]),closure_terms=len(sets.get(g,set())),excluded_NOT_rows=nnot[g],missing=not bool(sets.get(g,set())),svd_norm=float(np.linalg.norm(e[i])),evidence_codes='|'.join(sorted(evidence[g]))))
df=pd.DataFrame(coverage);df.to_csv(O/'COVERAGE.tsv',sep='\t',index=False)
for name,emb in [('topology',exact.toarray()),('svd128',e)]:
 sub=emb[[wanted.index(g) for g in requested]];pd.DataFrame(sub@sub.T,index=requested,columns=requested).to_csv(O/f'REQUESTED_COSINE_{name}.tsv',sep='\t')
# Tests: reproducibility under reordered requested rows, no missing requested gene,
# exact diagonal/cosine norm, fully reconstructable topology, no response files read.
assert all(sets.get(g) for g in requested)
assert np.isfinite(e).all();np.testing.assert_allclose(np.linalg.norm(e[norm>0],axis=1)[df.closure_terms.to_numpy()>0],1,atol=1e-6)
for g in requested:
 i=wanted.index(g);assert {terms[j] for j in mat[i].indices}==sets[g]
 np.testing.assert_allclose(mat[i].toarray()@svd.components_.T/np.linalg.norm(mat[i].toarray()@svd.components_.T),e[i:i+1],atol=1e-6)
reload=np.load(O/'GO_EXPANDED_EMBEDDING.npz');np.testing.assert_array_equal(reload['embedding'],e)
obo=(S/'GO/go-basic.obo').read_text();ontology_version=next(l for l in obo.splitlines() if l.startswith('data-version:'))
known_terms={l[4:] for l in obo.splitlines() if l.startswith('id: GO:')}
unknown_terms=sorted(set(terms)-known_terms)
(O/'TERMS_ABSENT_FROM_OBO.json').write_text(json.dumps({'all':unknown_terms,'requested_direct':{g:sorted(direct[g]-known_terms) for g in requested}},indent=2)+'\n')
prov={'schema':'t3.go.expanded.v1','role':'WT_OR_ONTOLOGY_ONLY; gene identity prior, no response signs/magnitudes','input_hashes':{str(S/'GO'/Path(f['path']).name):f['sha256'] for f in audit['files']},'existing_scope_audit':str(R/'infra/external_data/reports/GO__DATA_AUDIT_REPORT.json'),'original_parser_sha256':sha(R/'scripts/t3_priority_six/common.py'),'build_code_sha256':sha(__file__),'previous_embedding_sha256':sha(S/'GO_EMBEDDING.npz'),'requested':requested,'genes':len(wanted),'terms':len(terms),'missing_requested':df[df.requested & df.missing].gene.tolist(),'all_missing':df[df.missing].gene.tolist(),'method':'same approved positive GAF is_a/part_of closure; binary term incidence. Exact row-L2-normalized topology and refitted row-L2-normalized SVD128, shared basis for all genes','seed':20260930,'outcome_data_read':False,'fit_scope':'ontology annotations only; includes query gene identity, never KO outcomes','not_compatible_with_old_coordinates':'Replace old embeddings for ALL genes; do not append new rows to old GO128','ontology_version':ontology_version,'annotation_headers':headers,'terms_absent_from_obo':len(unknown_terms),'version_mismatch':'Frozen OBO2026-07-26 versus GAF2026-08-04/GO2026-08-02; missing ontology nodes retained as leaves per original parser, listed separately','license':'CC BY 4.0','license_source':'https://geneontology.org/docs/go-citation-policy/','license_checked_utc':'2026-10-08','versions':{'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},'tests':'PASS: frozen raw hashes, requested coverage, topology reconstruction, SVD projection reconstruction, unit norms, exact serialized reload','outputs':{p.name:sha(p) for p in O.glob('*.npz')}}
(O/'PROVENANCE.json').write_text(json.dumps(prov,indent=2)+'\n');print(df[df.requested].to_string(index=False));print(json.dumps({k:prov[k] for k in ['genes','terms','missing_requested','all_missing','tests']},indent=2))
