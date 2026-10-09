"""Replay immutable v0095 expression from persisted minimal inputs, without refitting.
Usage: python replay_persisted_v95.py --root /path/to/unpacked/code_and_source --parent PARENT.h5ad --output NEWDIR [--template-only]
No external network, download, candidate upload, or registry write is performed.
"""
import os
os.environ.update({k:'1' for k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']})
import argparse, gc, hashlib, importlib.util, json
from pathlib import Path
import anndata as ad
import numpy as np

def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def expect(p,h):
 actual=sha(p)
 if actual != h:raise ValueError(f'Input drift: {p}: {actual} != {h}')
def xsha(a):
 h=hashlib.sha256()
 for s in range(0,len(a),128):h.update(np.ascontiguousarray(a[s:s+128],dtype=np.float32).tobytes())
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--template-only',action='store_true');a=ap.parse_args()
 r=a.root;c=r/'candidate_v0095';m=json.loads((c/'MANIFEST.json').read_text())
 a.output.mkdir(parents=True,exist_ok=False)
 sourcepath=r/'audit/GSM5820434_panel_log1p.h5ad';expect(sourcepath,'1a9a89b2a170b21ffa6f2073f0b98542f7b79203e6cebef2c36e0e9b85113c09')
 op=r/'copula_restore.py';expect(op,'57293de8027a347b345471922001e0b2a847528cae0ca1416183d3c6c5efa55c')
 for name in ['source_donor_rows.npy','source_donor_barcodes.npy','states.npy','trust_genes.npy']:expect(c/name,m['files'][name]['sha256'])
 source=ad.read_h5ad(sourcepath);donors=np.load(c/'source_donor_rows.npy');states=np.load(c/'states.npy');trust=np.load(c/'trust_genes.npy');barcodes=np.load(c/'source_donor_barcodes.npy')
 assert np.array_equal(barcodes,np.array([str(source.obs_names[i]) if i>=0 else 'FALLBACK' for i in donors]))
 T=np.lib.format.open_memmap(a.output/'paired_template.npy',mode='w+',dtype='float32',shape=tuple(m['shape']));T[:]=0
 rows=np.flatnonzero(donors>=0);selected=source.X[donors[rows]].tocsr()
 for start in range(0,T.shape[1],256):
  cols=np.arange(start,min(start+256,T.shape[1]));cols=cols[trust[cols]]
  if len(cols):T[np.ix_(rows,cols)]=selected[:,cols].toarray()
 T.flush();expect(a.output/'paired_template.npy',m['files']['paired_template.npy']['sha256'])
 result={'template_sha256':sha(a.output/'paired_template.npy'),'template_exact':True}
 if not a.template_only:
  expect(a.parent,m['parent']['sha256']);base=ad.read_h5ad(a.parent);assert list(base.var_names)==list(source.var_names)
  P=np.lib.format.open_memmap(a.output/'parent.npy',mode='w+',dtype='float32',shape=base.shape)
  for s in range(0,len(base),128):P[s:s+128]=base.X[s:s+128].toarray()
  P.flush();expect(a.output/'parent.npy',m['files']['parent.npy']['sha256']);del source,selected,base;gc.collect()
  spec=importlib.util.spec_from_file_location('frozen_copula_restore',op);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  pred,diag=mod.restore(P,T,states,blend=.5,block_size=256,seed=20261009)
  assert xsha(pred)==m['candidate']['expression_sha256'];np.save(a.output/'prediction.npy',pred);expect(a.output/'prediction.npy',m['files']['prediction.npy']['sha256'])
  result.update({'prediction_npy_sha256':sha(a.output/'prediction.npy'),'expression_sha256':xsha(pred),'prediction_exact':True})
 (a.output/'REPLAY_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
