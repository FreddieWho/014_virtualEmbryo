"""Frozen source-local T3 campaign: direct embryo detection-odds transport.
No protected target outcomes are loaded. Full gene-panel scoring; no reduced scorer.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[k]='2'
import argparse, copy, hashlib, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd, anndata as ad, joblib
from scipy.special import expit, logit
from threadpoolctl import threadpool_limits
threadpool_limits(2)
REPO=Path(__file__).resolve().parents[2]
ASSETS=Path(os.environ.get('T3_ASSETS','/workspace/shared/virtualembryo-20261009/t3-assets/v88'))
sys.path.insert(0,str(ASSETS)); sys.path.insert(0,str(REPO/'third_party/veckit'))
from emitter_v88 import emit as original_emit
from crossko import closed
from common import core_metrics as cm
GENES=['Dnmt3a','Kmt2a','Kdm2b','Dnmt1','Dnmt3b','Ehmt2','Kmt2b']
WEIGHTS={'de':.30,'direction':.25,'severity_abs':.25,'mmd':.12,'variogram':.08}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def array_sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def write_json(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def detection_logit(x): return logit(((x>0).sum(0)+.5)/(len(x)+1))
def odds_response(model,control,ko):
    response=model.summarize_response(control,ko)
    cl=model.assign(control);kl=model.assign(ko)
    _,cv=model.positive_quantiles(control,np.zeros((model.G,len(model.positive_q))))
    _,kv=model.positive_quantiles(ko,np.zeros((model.G,len(model.positive_q))))
    global_valid=cv&kv
    global_odds=detection_logit(ko)-detection_logit(control)
    for s in range(model.S):
        if not response['support'][s]:continue
        a=control[cl==s];b=ko[kl==s];lam=len(b)/(len(b)+50)
        rate=lam*(detection_logit(b)-detection_logit(a))+(1-lam)*global_odds
        rate[~global_valid]=0
        response['delta'][s,:,-1]=rate
    return response

def convert_odds(model,carrier,response):
    """Precompute carrier state detection deltas; same RNG donors as original emitter."""
    if not np.any(response['delta']):return response
    lab=model.assign(carrier);rng=np.random.default_rng(model.seed)
    mass=np.bincount(lab,minlength=model.S).astype(float)*np.exp(np.clip(response['composition'],-2,2));mass/=mass.sum()
    prob=mass[lab]/np.maximum(np.bincount(lab,minlength=model.S)[lab],1);prob/=prob.sum()
    ix=rng.choice(np.arange(len(carrier)),len(carrier),replace=True,p=prob)
    labels=lab[ix];r={k:v.copy() for k,v in response.items()}
    for s in range(model.S):
        rows=np.flatnonzero(labels==s)
        if not len(rows) or not r['support'][s]:continue
        p=(carrier[ix[rows]]>0).mean(0);eps=.5/(len(rows)+1)
        smooth=np.clip(p,eps,1-eps)
        change=expit(logit(smooth)+r['delta'][s,:,-1])-smooth
        change[r['delta'][s,:,-1]==0]=0
        r['delta'][s,:,-1]=np.clip(p+change,0,1)-p
    return r

def emit(model,base,response,route):
    if route=='odds':response=convert_odds(model,base,response)
    return original_emit(model,base,response,mode='combined',conditional=True)

def measure(p,t,c,seed):
    s,r2=cm.severity_slope(p,t,c)
    return dict(de=cm.de_score(p,t,c)['score'],direction=cm.de_direction(p,t,c),severity_abs=abs(s),severity_r2=r2,mmd=cm.mmd_unbiased(p,t,seed=seed),variogram=cm.variogram_score(p,t,seed=seed),mse=float(((p.mean(0,dtype=float)-t.mean(0,dtype=float))**2).mean()))

def load_inputs():
    receipts=json.loads((ASSETS/'source_panel/normalized/MERGE_RECEIPT.json').read_text());data={};checks=[]
    for r in receipts:
        f=ASSETS/'source_panel/normalized'/f"{r['gene']}_whitelisted_panel10000.h5ad"
        assert sha(f)==r['sha256'];a=ad.read_h5ad(f);assert array_sha(a.X)==r['expression_array_sha256'];closed(a.X)
        data[r['gene']]=a;checks.append(dict(gene=r['gene'],sha256=sha(f),cells=a.n_obs,embryos=a.obs.embryo.nunique()))
    manifest=json.loads((ASSETS/'inference/MANIFEST.json').read_text());assert sha(ASSETS/'inference/state_emitter.joblib')==manifest['files']['state_emitter.joblib'];assert sha(REPO/'third_party/veckit/common/core_metrics.py')==sha(ASSETS/'public_core/common/core_metrics.py');model=joblib.load(ASSETS/'inference/state_emitter.joblib')
    wt=data['WT'].X;wo=data['WT'].obs;rng=np.random.default_rng(711);controls={}
    for sex in wo.sex.unique():
        blocks=[]
        for e in wo.loc[wo.sex==sex,'embryo'].unique():
            ix=np.flatnonzero((wo.sex==sex)&(wo.embryo==e));blocks.append(wt[rng.choice(ix,500,replace=len(ix)<500)])
        controls[sex]=np.concatenate(blocks)
    return data,model,controls,checks

def build_responses(data,model,controls,out,route):
    original=np.load(ASSETS/'source_evaluation/embryo_responses.npz');meta=json.loads((ASSETS/'source_evaluation/embryo_responses.json').read_text())
    dest=out/'embryo_responses.npz'
    if dest.exists():raise FileExistsError('Use a fresh output directory: campaign caches are immutable and never implicitly reused')
    parts=[];newmeta=[]
    for g in GENES:
        a=data[g]
        for e in sorted(a.obs.embryo.unique()):
            m=np.asarray(a.obs.embryo==e);sex=a.obs.loc[m,'sex'].iloc[0]
            r=odds_response(model,controls[sex],a.X[m]) if route=='odds' else model.summarize_response(controls[sex],a.X[m])
            parts.append(r);newmeta.append(dict(gene=g,embryo=str(e),sex=str(sex)))
        print('RESPONSE',route,g,flush=True)
    assert newmeta==meta
    d={k:np.stack([r[k] for r in parts]) for k in ['delta','composition','support']}
    if route=='odds':
        assert np.array_equal(d['delta'][:,:,:,:-1],original['delta'][:,:,:,:-1])
        assert np.array_equal(d['composition'],original['composition']) and np.array_equal(d['support'],original['support'])
    np.savez_compressed(dest,**d);write_json(out/'response_fidelity.json',dict(positive_response_exact=route=='odds',composition_exact=route=='odds',support_exact=route=='odds',embryos=len(meta)))
    return d,meta

def aggregate(d,meta,exclude=None):
    train=[g for g in GENES if g!=exclude];r={}
    for k in ['delta','composition','support']:
        r[k]=np.mean([d[k][[i for i,m in enumerate(meta) if m['gene']==g]].mean(0) for g in train],axis=0)
    r['support']=r['support']>=.5
    return r

def evaluate(out,route):
    out.mkdir(parents=True,exist_ok=True)
    data,model,controls,checks=load_inputs();write_json(out/'INPUT_CHECKS.json',checks)
    d,meta=build_responses(data,model,controls,out,route)
    z=np.load(ASSETS/'source_evaluation/embryo_responses.npz');old={k:z[k] for k in z.files}
    write_json(out/'FROZEN.json',dict(route=route,code_sha256=sha(__file__),design_sha256=sha(REPO/'configs/t3_quota_20261009/DESIGN.json'),source_genes=GENES,heldout_rule='query excluded before response aggregation; no query KO data used in atlas or fit',WT_role='full source WT atlas and embryo-balanced sex-matched controls; all genotypes KO-only'))
    rows=[];anchors=[];rng=np.random.default_rng(241);crng=np.random.default_rng(9001)
    for query in GENES:
        a=data[query];obs=a.obs;truth=[];ceiling=[];control=[]
        for e in sorted(obs.embryo.unique())[1::2]:
            rr=np.flatnonzero(obs.embryo==e);chosen=rng.choice(rr,500,replace=len(rr)<500);truth.append(a.X[chosen]);left=np.setdiff1d(rr,chosen);assert len(left)>0;ceiling.append(a.X[crng.choice(left,500,replace=len(left)<500)])
            c=controls[obs.iloc[rr[0]].sex];control.append(c[rng.choice(len(c),500,replace=False)])
        truth=np.concatenate(truth);ceiling=np.concatenate(ceiling);ref=np.concatenate(control);base=ref[rng.choice(len(ref),7449,replace=True)].copy()
        response=aggregate(d,meta,query);baseline=aggregate(old,meta,query)
        candidate,ix=emit(model,base,response,route);v88,oldix=emit(model,base,baseline,'v88')
        scrambled=copy.deepcopy(response);perm=np.random.default_rng(4609).permutation(model.G);scrambled['delta']=scrambled['delta'][:,perm]
        null,_=emit(model,base,scrambled,route)
        preds={'wt_identity':base,'v88':v88,'candidate':candidate,'scrambled_response':null}
        for name,pred in preds.items():
            closed(pred);f=out/f'{query}_{name}.h5ad';ad.AnnData(pred,var=a.var.copy()).write_h5ad(f,compression='gzip');assert np.array_equal(ad.read_h5ad(f).X,pred)
        write_json(out/f'{query}_PREDICTIONS.json',dict(training_genes=[g for g in GENES if g!=query],heldout=query,hashes={n:array_sha(p) for n,p in preds.items()},donors_same_as_v88=bool(np.array_equal(ix,oldix)),donor_unique=int(len(np.unique(ix))),donor_max_repeats=int(np.bincount(ix).max()),detection={n:float((p>0).mean()) for n,p in preds.items()}))
        for seed in [0,1,2]:
            floor=measure(ref,truth,ref,seed);ceil=measure(ceiling,truth,ref,seed);anchors.append(dict(query=query,seed=seed,floor=floor,ceiling=ceil))
            for metric in WEIGHTS:
                gap=(floor[metric]-ceil[metric]) if metric in ['severity_abs','mmd','variogram'] else (ceil[metric]-floor[metric])
                assert np.isfinite(floor[metric]) and np.isfinite(ceil[metric]) and gap>1e-10, ('Invalid calibration anchor',query,seed,metric)
            for name,pred in preds.items():
                raw=measure(pred,truth,ref,seed);skills={m:100*cm.skill(raw[m],floor[m],ceil[m],lower_is_better=m in ['severity_abs','mmd','variogram']) for m in WEIGHTS};total=sum(WEIGHTS[m]*skills[m] for m in WEIGHTS)
                assert all(np.isfinite(raw[m]) and np.isfinite(skills[m]) for m in WEIGHTS)
                row=dict(query=query,seed=seed,model=name,total=total,**raw,**{m+'_skill':v for m,v in skills.items()});rows.append(row);print('METRIC',query,name,seed,total,flush=True)
            pd.DataFrame(rows).to_csv(out/'metrics.csv',index=False);write_json(out/'anchors.json',anchors)
    f=pd.DataFrame(rows);archived=pd.read_csv(ASSETS/'source_evaluation/metrics.csv');now=f[f.model=='v88'].sort_values(['query','seed']);oldbaseline=archived[archived.model=='conditional'].sort_values(['query','seed']);cols=['total']+list(WEIGHTS);assert np.max(np.abs(now[cols].to_numpy()-oldbaseline[cols].to_numpy()))<1e-10,'Baseline source metrics drift';f.groupby('model').mean(numeric_only=True).to_csv(out/'summary.csv');q=f.groupby(['query','model']).mean(numeric_only=True)
    delta=q.xs('candidate',level='model')-q.xs('v88',level='model')
    write_json(out/'RESULT.json',dict(status='COMPLETE',route=route,mean_delta=float(delta.total.mean()),wins=int((delta.total>0).sum()),per_genotype_delta=delta.total.to_dict(),component_delta={m:float(delta[m+'_skill'].mean()) for m in WEIGHTS},not_server_forecast=True))
    np.savez_compressed(out/'deployment_response.npz',**aggregate(d,meta))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--route',choices=['odds'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();evaluate(a.out,a.route)
