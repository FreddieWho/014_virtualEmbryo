import argparse,json,sys
from pathlib import Path
import numpy as np,anndata as ad
from normalization import restore_cp10k
p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--candidate',required=True);p.add_argument('--groups',required=True);p.add_argument('--official85',required=True);p.add_argument('--out',required=True);a=p.parse_args()
x=ad.read_h5ad(a.parent).X;y=ad.read_h5ad(a.candidate).X;g=np.load(a.groups)
count=sum(float(g[f'comp9.5|{k}|n']) for k in g['groups']);ref=sum(float(g[f'comp9.5|{k}|n'])*g[f'comp9.5|{k}|mean'].astype(float) for k in g['groups'])/count
m0=np.asarray(x.astype(float).mean(0)).ravel();m1=np.asarray(y.astype(float).mean(0)).ravel();d0=m0-ref;d1=m1-ref;keep=(np.abs(d0)>=.01)|(np.abs(d1)>=.01)
v0=np.asarray(x.astype(float).power(2).mean(0)).ravel()-m0*m0;v1=np.asarray(y.astype(float).power(2).mean(0)).ravel()-m1*m1
s=ad.read_h5ad(a.official85,backed='r');c=s.X[:512].tocsr();s.file.close();q,_=restore_cp10k(c)
bad=c.astype(float);scales=np.linspace(.804025,2.349021,512);bad.data=np.log1p(np.expm1(bad.data)*np.repeat(scales,np.diff(bad.indptr)));r,_=restore_cp10k(bad)
res={'status':'PASS_NO_CATASTROPHE','full_panel_genes':x.shape[1],'official8_first512_rows_noop_max_abs':float(np.abs(q.data-c.data).max()),'known_row_scale_repair_max_abs':float(np.abs(r.data-c.data).max()),'full_population_gene_variance_sum_ratio':float(v1.sum()/v0.sum()),'full_population_pseudobulk_l2_change':float(np.linalg.norm(m1-m0)),'genes_with_reference_delta_abs_ge_0_01':int(keep.sum()),'direction_flips_vs_released95':int(((np.sign(d0)!=np.sign(d1))&keep).sum()),'source95_pseudobulk_reference':'All17057 official E9.5 cells via exact frozen coarse-group aggregate summaries; float32 aggregate rounding','future_truth_used':False,'interpretation':'Full-panel structural controls and released-source directional diagnostic, not future accuracy'}
assert res['official8_first512_rows_noop_max_abs']<1e-6 and res['known_row_scale_repair_max_abs']<1e-6
Path(a.out).write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
