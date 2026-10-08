import argparse
p=argparse.ArgumentParser();p.add_argument("--repo",required=True);p.add_argument("--out",required=True);args=p.parse_args()
from pathlib import Path
import json,hashlib,sys
import anndata as ad
import numpy as np,pandas as pd
from scipy import sparse
ROOT=Path(args.repo).resolve();OUT=Path(args.out).resolve();Q=OUT/'quarantine'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Re-run original frozen filter with only output locations redirected.
(Q/'raw').mkdir(parents=True,exist_ok=True)
for p in (OUT/'raw').glob('*.h5'):
 q=Q/'raw'/p.name
 if not q.exists():q.symlink_to(p)
report=OUT/'filter_report';report.mkdir(exist_ok=True)
for name in ['fibro_planned_keep_samples.tsv','MATRIX_FETCH_RECEIPT.json','panel_genes.json']:
 (report/name).write_bytes((ROOT/'reports/t3_data_intake_20260920'/name).read_bytes())
script=(ROOT/'scripts/t3_data_intake/filter_fibro.py').read_text()
script=script.replace("ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/t3_data_intake_20260920';Q=ROOT/'infra/external_data/quarantine/T3-NEXT-R56-20260920'",f"ROOT=Path('{OUT}');OUT=Path('{report}');Q=Path('{Q}')")
exec(compile(script,str(ROOT/'scripts/t3_data_intake/filter_fibro.py'),'exec'),{})
raw=Q/'filtered/GSE261783_OP2_resting_provisional_raw.h5ad'
a=ad.read_h5ad(raw)
review=json.loads((ROOT/'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json').read_text())
assert set(a.obs.condition.astype(str))==set(review['condition_allowlist'])
assert set(a.obs['sample'].astype(str))=={'GSM8151756','GSM8151757'}
panel=json.loads((report/'panel_genes.json').read_text())
pos=[]
for gene in panel:
 ii=np.flatnonzero(a.var.gene_symbol.astype(str).to_numpy()==gene);assert len(ii)==1;pos.append(int(ii[0]))
full=a.X;total=np.asarray(full.sum(axis=1)).ravel();x=full[:,pos].toarray()
x=np.log1p(x.astype(np.float64)*10000/total[:,None]).astype(np.float32)
obs=a.obs.copy();obs['model_input']=True;obs['permit_status']='APPROVED_SANITIZED'
ad.AnnData(X=x,obs=obs,var=pd.DataFrame(index=panel),uns={'normalization':'log1p counts per 10000; denominator all 32287 retained gene features','source_review':'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json'}).write_h5ad(OUT/'expression.h5ad',compression='gzip')
assert x.shape==(5454,500)
expected=json.loads((ROOT/'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json').read_text())['files']['expression']['sha256']
r={'schema':'t3.source.reconstruction.v1','source_review':str(ROOT/'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json'),'source_review_sha256':sha(ROOT/'reports/t3_r56_launch_20260921/SOURCE_REVIEW.json'),'allowlist_exact_match':True,'raw_files_sha256_verified':True,'original_filter_code_sha256':sha(ROOT/'scripts/t3_data_intake/filter_fibro.py'),'original_prepare_code_sha256':sha(ROOT/'scripts/t3_data_intake/prepare_r6_20260921.py'),'filter_plan_sha256':sha(report/'fibro_planned_keep_samples.tsv'),'expression_path':str(OUT/'expression.h5ad'),'expression_sha256':sha(OUT/'expression.h5ad'),'original_expression_sha256':expected,'expression_byte_identical':sha(OUT/'expression.h5ad')==expected,'shape':list(x.shape),'condition_counts':a.obs.condition.value_counts().to_dict(),'no_target_ko_values_used':True}
(OUT/'RECONSTRUCTION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
