"""Source-learned detection decoder; preserves each state's predicted count mean."""
from .common import *
from sklearn.linear_model import Ridge
from scipy.special import expit,logit

LANES=['r1_celloracle','r2_mass_only','r2_mass_expression','r3_activity','r4_functional','r4_bilinear','r5_scouter','r6_gears']

def fit_detection(source,genes):
    x=dense(source.X);labels=source.obs.condition.astype(str).to_numpy();control=x[labels=='ctrl'];p0=np.mean(control>0,0)
    xx=[];yy=[]
    for g in genes:
        cells=x[labels==g];rate=mean_rate(control,cells)
        p1=np.mean(cells>0,0)
        delta=logit(np.clip(p1,.001,.999))-logit(np.clip(p0,.001,.999))
        xx.append(rate);yy.append(delta)
    xx=np.array(xx);yy=np.array(yy)
    m=Ridge(alpha=10,fit_intercept=False).fit(xx.ravel()[:,None],yy.ravel())
    return m,xx,yy

def observation_decode(base,raw,labels,beta,seed=SEED):
    """Alter detection on a supported state, sample positives, retain predicted means.

    Exact identity at zero effect. All-zero states lack positive support and stay
    zero. No target KO is used. This is a cross-platform hypothesis, not a causal fit.
    """
    counts=np.expm1(base).astype('float64');desired=np.expm1(raw).astype('float64');out=desired.copy()
    for k,label in enumerate(sorted(set(labels))):
        rows=np.flatnonzero(labels==label);local=counts[rows];current=desired[rows];n=len(rows)
        p0=np.mean(local>0,0);rate=np.log((current.mean(0)+1e-3)/(local.mean(0)+1e-3))
        reference=np.clip(p0,1/(2*n+2),1-1/(2*n+2))
        p1=np.clip(p0+expit(logit(reference)+beta*rate)-reference,0,1)
        for j in np.flatnonzero((np.abs(rate)>1e-7)&(p0>0)):
            requested=max(1,min(n,int(np.rint(p1[j]*n))));column=current[:,j].copy()
            positive=np.flatnonzero(column>0);zero=np.flatnonzero(column==0)
            rng=np.random.default_rng(seed+k*1000+j)
            if len(positive)>requested:
                column[rng.choice(positive,len(positive)-requested,replace=False)]=0
            elif len(positive)<requested and len(zero):
                take=rng.choice(zero,min(requested-len(positive),len(zero)),replace=False)
                support=local[local[:,j]>0,j]
                column[take]=rng.choice(support,len(take),replace=True)
            target_sum=float(current[:,j].sum());actual=float(column.sum())
            if actual>0:column*=target_sum/actual
            out[rows,j]=column
    return np.log1p(out).astype('float32')

def run():
    import anndata as ad
    source,parent,wt=load_inputs();cfg=json.loads((RUN/'CONFIG.json').read_text())
    m,_,_=fit_detection(source,cfg['split']['train']);_,xt,yt=fit_detection(source,cfg['split']['test'])
    predicted=m.predict(xt.ravel()[:,None]).reshape(yt.shape)
    receipt={'role':'conditional decoder calibration using observed source intensity effects; NOT whole response-pipeline validation',
      'training_genes':cfg['split']['train'],'test_genes':cfg['split']['test'],'heldout_delta_logit_mse':float(np.mean((predicted-yt)**2)),'identity_delta_logit_mse':float(np.mean(yt**2)),'alpha':10,'fitted_train_slope':float(m.coef_[0]),'source_cells':5454,'target_truth_used':False,'zero_effect_is_identity':True,'all_zero_state_activation':'unsupported; stays zero'}
    final,_,_=fit_detection(source,sum(cfg['split'].values(),[]));beta=float(final.coef_[0]);receipt['final_all26_slope']=beta
    dump(RUN/'DETECTION_CALIBRATION.json',receipt)
    calibrated_native=None;selected=np.load(RUN/'r2_sampling_indices.npy')
    for lane in LANES:
        p=RUN/lane;result=json.loads((p/'RESULT.json').read_text());assert sha(p/'research.h5ad')==result['sha256']
        a=ad.read_h5ad(p/'research.h5ad');baseline=dense(parent.X)
        if lane=='r2_mass_only':out=dense(a.X).copy()
        elif lane=='r2_mass_expression':out=calibrated_native[selected]
        else:out=observation_decode(baseline,dense(a.X),parent.obs.celltype.astype(str).to_numpy(),beta)
        out[:,parent.var_names.get_loc('Gata4')]=0
        if lane=='r1_celloracle':calibrated_native=out.copy()
        a.X=out;a.uns['ve_contract']={'normalization':'log_normalized','source':'source-learned detection shift; within-state predicted intensity means preserved'}
        a.write_h5ad(p/'calibrated.h5ad',compression='gzip')
        original=dense(ad.read_h5ad(p/'research.h5ad').X)
        dump(p/'CALIBRATED.json',{'status':'FULL_CALIBRATED_TARGET_INFERENCE_COMPLETE','sha256':sha(p/'calibrated.h5ad'),'original_core_output_sha256':result['sha256'],'calibration_receipt_sha256':sha(RUN/'DETECTION_CALIBRATION.json'),'zero_entries_activated':int(np.sum((original==0)&(out>0))),'positive_entries_deactivated':int(np.sum((original>0)&(out==0))),'server_score':'NOT_RUN'})
        print('CALIBRATED_FULL_TARGET',lane,flush=True)

if __name__=='__main__':run()
