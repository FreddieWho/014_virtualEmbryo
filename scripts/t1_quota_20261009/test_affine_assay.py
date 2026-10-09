"""Frozen source-only positive-SD transportability assay; no target prediction."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json,sys,gc,resource,time
from pathlib import Path
import numpy as np,anndata as ad
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vework/t1ext'))
from label_means_const import COARSE
from replicate_weights import IEG
from build_cp10k import sha
GROUPS=sorted(set(COARSE.values()))

def moments(x):
    n=x.shape[0];k=np.asarray((x>0).sum(0)).ravel().astype(np.int32);s=np.asarray(x.astype(float).sum(0)).ravel();ss=np.asarray(x.astype(float).power(2).sum(0)).ravel();m=s/np.maximum(k,1);v=np.maximum((ss-s*s/np.maximum(k,1))/np.maximum(k-1,1),0)
    return {'n':n,'k':k,'mean':m,'var':v,'det':k/max(n,1)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--official85',required=True);p.add_argument('--official95',required=True);p.add_argument('--external-root',required=True);p.add_argument('--external95',required=True);p.add_argument('--config',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 t=time.time();cfg=json.loads(Path(a.config).read_text());out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if (out/'RESULT.json').exists():raise FileExistsError('Frozen assay already completed')
 source=ad.read_h5ad(a.official85);genes=np.asarray(source.var_names,dtype=str);lab=np.array([COARSE[x] for x in source.obs.celltype.astype(str)]);X=source.X.tocsr();official85={g:moments(X[lab==g]) for g in GROUPS}
 extpaths=sorted(Path(a.external_root).glob('*E8_5*.h5ad'));assert len(extpaths)==2
 have=np.ones(len(genes),bool)
 for path in extpaths+[Path(a.external95)]:
  obj=ad.read_h5ad(path,backed='r');assert np.array_equal(obj.var_names,genes);have&=obj.var.in_external.to_numpy();obj.file.close()
 train,test=train_test_split(np.arange(len(lab)),test_size=.3,random_state=cfg['seed'],stratify=lab)
 means=np.vstack([np.asarray(X[train[lab[train]==g]].mean(0)).ravel() for g in GROUPS]);bad=np.array([x.startswith(('mt-','Rpl','Rps','Hba','Hbb')) or x in IEG or x=='Malat1' for x in genes]);markers=set()
 for i,g in enumerate(GROUPS):
  score=means[i]-np.max(np.delete(means,i,axis=0),axis=0);score[~have|bad]=-np.inf;markers.update(np.argsort(-score,kind='stable')[:40].tolist())
 markers=np.array(sorted(markers));features=X[:,markers].toarray().astype(float);mu=features[train].mean(0);sd=features[train].std(0)+.001
 clf=LogisticRegression(C=.5,max_iter=1000,random_state=cfg['seed']).fit((features[train]-mu)/sd,lab[train]);assert clf.n_iter_.max()<1000
 accuracy=float(np.mean(clf.predict((features[test]-mu)/sd)==lab[test]));del X,features,source;gc.collect()
 ext={};coverage={};mapping={}
 for name,path in [('early1',extpaths[0]),('early2',extpaths[1]),('late95',Path(a.external95))]:
  obj=ad.read_h5ad(path);z=obj.X[:,markers].toarray().astype(float);prob=clf.predict_proba((z-mu)/sd);pred=clf.classes_[prob.argmax(1)];accepted=prob.max(1)>=.8;labels=np.where(accepted,pred,'LOWCONF')
  ext[name]={g:moments(obj.X[labels==g]) for g in GROUPS};coverage[name]={'total':obj.n_obs,'accepted':int(accepted.sum()),'by_state':{g:int((labels==g).sum()) for g in GROUPS},'probability_quantiles':np.quantile(prob.max(1),[0,.1,.5,.9,1]).tolist()};mapping[name]=labels;del obj,z,prob;gc.collect()
 obj=ad.read_h5ad(a.official95);lab95=np.array([COARSE[x] for x in obj.obs.celltype.astype(str)]);official95={g:moments(obj.X[lab95==g]) for g in GROUPS};del obj;gc.collect()
 saved={'genes':genes,'markers':markers,'classifier_coefficients':clf.coef_,'classifier_intercept':clf.intercept_,'classifier_classes':clf.classes_,'marker_mean':mu,'marker_sd':sd};results=[];rng=np.random.default_rng(cfg['seed'])
 for g in GROUPS:
  x=official85[g];a1=ext['early1'][g];a2=ext['early2'][g];y=ext['late95'][g];truth=official95[g]
  eligible=have&~bad&(x['k']>=10)&(a1['k']>=10)&(a2['k']>=10)
  if min(a1['n'],a2['n'])<20:eligible[:]=False
  me=(a1['mean']+a2['mean'])/2;ve=(a1['var']+a2['var'])/2+(a1['mean']-a2['mean'])**2/4;se=np.sqrt(ve);so=np.sqrt(x['var']);ne=np.minimum(x['k'],np.minimum(a1['k'],a2['k']));alpha=ne/(ne+50)
  b=np.ones(len(genes));b[eligible]=np.exp(alpha[eligible]*np.log(np.clip(so[eligible]/np.maximum(se[eligible],.05),.5,2)))
  intercept=np.zeros(len(genes));intercept[eligible]=alpha[eligible]*(x['mean'][eligible]-b[eligible]*me[eligible]);saved[g+'|slope']=b;saved[g+'|intercept']=intercept;saved[g+'|fit_eligible']=eligible
  evaluation=eligible&(y['k']>=10)&(truth['k']>=10);n=int(evaluation.sum())
  rec={'group':g,'fit_genes':int(eligible.sum()),'evaluated_genes':n,'external95_cells':y['n'],'official95_cells':truth['n'],'slope_quantiles':np.quantile(b[eligible],[0,.1,.5,.9,1]).tolist() if eligible.any() else []}
  if n>=100:
   ix=np.flatnonzero(eligible);shuffled=b.copy();shuffled[ix]=b[rng.permutation(ix)];ys=np.sqrt(y['var'][evaluation]);ts=np.sqrt(truth['var'][evaluation]);B=b[evaluation]
   rec.update(sd_error_unadjusted=float(np.median(np.abs(np.log((ys+.05)/(ts+.05))))),sd_error_adjusted=float(np.median(np.abs(np.log((B*ys+.05)/(ts+.05))))),sd_error_gene_permuted=float(np.median(np.abs(np.log((shuffled[evaluation]*ys+.05)/(ts+.05))))),positive_mean_mse_unadjusted=float(np.mean((y['mean'][evaluation]-truth['mean'][evaluation])**2)),positive_mean_mse_affine=float(np.mean((np.maximum(intercept[evaluation]+B*y['mean'][evaluation],0)-truth['mean'][evaluation])**2)),external95_detection_median=float(np.median(y['det'][evaluation])),official95_detection_median=float(np.median(truth['det'][evaluation])))
  results.append(rec)
 eligible_results=[r for r in results if 'sd_error_adjusted' in r];base=np.mean([r['sd_error_unadjusted'] for r in eligible_results]) if eligible_results else float('inf');adjust=np.mean([r['sd_error_adjusted'] for r in eligible_results]) if eligible_results else float('inf');shuf=np.mean([r['sd_error_gene_permuted'] for r in eligible_results]) if eligible_results else float('inf');wins=sum(r['sd_error_adjusted']<r['sd_error_unadjusted'] for r in eligible_results)
 passed=len(eligible_results)>=3 and adjust<=.95*base and wins>=np.ceil(2*len(eligible_results)/3) and adjust<shuf
 np.savez_compressed(out/'FITTED_E85_ONLY.npz',**saved)
 result={'status':'PASS_SOURCE_TRANSPORTABILITY_GATE' if passed else 'FAIL_CLOSE_WITHOUT_TARGET_CANDIDATE','fit_config':cfg,'classifier_e85_heldout_accuracy':accuracy,'classifier_fit_e95_used':False,'mapping_coverage':coverage,'state_results':results,'aggregate':{'evaluable_states':len(eligible_results),'winning_states':wins,'mean_median_log_sd_error_unadjusted':float(base),'mean_median_log_sd_error_adjusted':float(adjust),'mean_median_log_sd_error_gene_permuted':float(shuf),'relative_improvement':float(1-adjust/base)},'target_candidate_created':False,'limits':['Single pooled E9.5 whole-cell library versus official nuclei','Source label-confidence conditioning changes selected populations','Cross-study E9.5 performance does not establish E14.5 or future transfer','Affine intercept performance cannot alone justify slope-only temporal transfer'],'wall_seconds':time.time()-t,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 (out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
