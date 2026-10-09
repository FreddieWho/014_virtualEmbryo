"""Build and parent-contract-validate a frozen source-tested T3 artifact."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import argparse,sys,json,hashlib,zipfile,shutil
from pathlib import Path
import numpy as np,anndata as ad,joblib
from campaign import REPO,ASSETS,sha,array_sha,write_json,emit,closed
sys.path.insert(0,str(REPO/'docs/batch3/interfaces'))
from virtual_embryo_tools.contract_io import validate_h5ad_contract

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--route',required=True);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--version',required=True);ap.add_argument('--lane',required=True);ap.add_argument('--replay',type=Path);a=ap.parse_args()
    parentpath=ASSETS/'v0088/t3_gata4__condhurdle__v0088.h5ad';assert sha(parentpath)=='d7944880d8f55974946dad4b2c22879582c03bce547ead312921b0fc39bdddc7'
    carrier=ad.read_h5ad(ASSETS/'inference/WT_carrier7449.h5ad');parent=ad.read_h5ad(parentpath)
    modelpath=a.run/'state_emitter.joblib';modelpath=modelpath if modelpath.exists() else ASSETS/'inference/state_emitter.joblib';model=joblib.load(modelpath)
    z=np.load(a.run/'deployment_response.npz');response={k:z[k] for k in z.files};pred,donor=emit(model,carrier.X,response,a.route)
    fallback=np.zeros(len(carrier),bool)
    if a.route=='anatomical':fallback=~response['support'][model.assign(carrier.X)];pred[fallback]=parent.X[fallback]
    closed(pred)
    if a.replay:
        artifact=ad.read_h5ad(a.replay);assert np.array_equal(pred,artifact.X);result=dict(status='PASS',expression_sha256=array_sha(pred),donor_sha256=array_sha(donor),max_mass_error=float(abs(np.expm1(pred.astype(float)).sum(1)-10000).max()),fresh_process=True);print(json.dumps(result,indent=2));return
    out=REPO/'submissions/candidates/T3_gata4'/f'v{a.version}_{a.lane}';out.mkdir(parents=True,exist_ok=False)
    result=json.loads((a.run/'RESULT.json').read_text());assert result['status']=='COMPLETE'
    artifact=parent.copy();artifact.X=pred;artifact.uns.clear();artifact.uns['ve_contract']={'normalization':'log_normalized','source':'Reviewed embryonic WT/KO source response; no protected target outcomes'}
    ledger=json.loads((REPO/'reports/t3_quota_20261009/SOURCE_LEDGER.json').read_text())
    artifact.uns['t3_campaign']={'candidate_id':'v'+a.version,'parent':'v0088','route':a.route,'source_ledger_json':json.dumps(ledger,sort_keys=True),'source_outcome_accessions':'GSE137337 E8.5 seven permitted KOs; GSE122187 E8.5 WT','target_truth_used':False,'RNA_knockout_forced':False,'normalization':'panel10000 log1p','source_local_delta':result['mean_delta'],'local_metrics_are_server_forecast':False,'source_genotype_exclusion':'all query KO embryos excluded from response aggregation; WT-only atlas','model_sha256':sha(modelpath),'response_sha256':sha(a.run/'deployment_response.npz'),'source_run_code_sha256':json.loads((a.run/'FROZEN.json').read_text())['code_sha256'],'source_ledger_sha256':sha(REPO/'reports/t3_quota_20261009/SOURCE_LEDGER.json'),'fallback_exact_parent_cells':int(fallback.sum()),'geometry':'all parent metadata, layers, raw and spatial coordinates preserved','limitations':'observational source-state associations and generic epigenetic developmental response, not identified target causal mechanism; platform/stage/cohort confounding'}
    file=out/'submission.h5ad';artifact.write_h5ad(file,compression='gzip');reload=ad.read_h5ad(file);assert np.array_equal(reload.X,pred)
    contract=validate_h5ad_contract(file,task='T3',board='gata4',scorer_lock=REPO/'reports/t3_quota_20261009/contract_context/SCORER_LOCK.json',parent_path=parentpath,parent_sha256=sha(parentpath));write_json(out/'contract.json',contract);assert contract['status']=='PASS',contract
    member=f't3_gata4__{a.lane}__v{a.version}.h5ad';assert len(member)<=50;delivery=REPO/'deliveries'/f't3{a.version}__t3__upload__20261009.zip';delivery.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(delivery,'x',compression=zipfile.ZIP_DEFLATED) as z:z.write(file,member)
    with zipfile.ZipFile(delivery) as z:assert z.testzip() is None;assert hashlib.sha256(z.read(member)).hexdigest()==sha(file)
    handoff=dict(task='T3:gata4',candidate_id='v'+a.version,parent='v0088',route=a.route,lane=a.lane,artifact_path=str(file),sha256=sha(file),expression_sha256=array_sha(pred),zip_path=str(delivery),zip_sha256=sha(delivery),upload_member=member,contract='PASS',shape=list(pred.shape),source_result=result,model_path=str(modelpath),response_path=str(a.run/'deployment_response.npz'),donor_unique=int(len(np.unique(donor))),donor_max_repeats=int(np.bincount(donor).max()),detection=float((pred>0).mean()),zero_to_positive=int(((carrier.X==0)&(pred>0)).sum()),positive_to_zero=int(((carrier.X>0)&(pred==0)).sum()),fallback_exact_parent_cells=int(fallback.sum()),max_mass_error=float(abs(np.expm1(pred.astype(float)).sum(1)-10000).max()),source_ledger_sha256=sha(REPO/'reports/t3_quota_20261009/SOURCE_LEDGER.json'),submitted=False,score_status='not_submitted',blocks_submission=False)
    write_json(out/'HANDOFF.json',handoff);write_json(REPO/'reports/t3_quota_20261009'/f'v{a.version}_HANDOFF.json',handoff);print(json.dumps(handoff,indent=2))
if __name__=='__main__':main()
