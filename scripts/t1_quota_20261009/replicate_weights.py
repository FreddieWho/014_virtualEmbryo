"""Two early and two late *libraries*, not four independent pairs."""
import numpy as np
from scipy.special import logit

IEG={'Fos','Fosb','Jun','Junb','Jund','Egr1','Egr2','Egr3','Atf3','Ier2','Ier3','Ier5','Dusp1','Zfp36','Klf2','Klf4','Klf6','Nr4a1','Hspa1a','Hspa1b','Hspa8','Hsph1','Btg2','Cyr61','Ccn1','Socs3','Gadd45b','Ppp1r15a','Mt1','Mt2'}

def uncertainty_weight(early,late,early_variance,late_variance,pooled=False):
    early=np.asarray(early,float);late=np.asarray(late,float)
    mu=late.mean(0)-early.mean(0)
    between=early.var(0,ddof=1)/2+late.var(0,ddof=1)/2
    within=(np.sum(early_variance,axis=0)+np.sum(late_variance,axis=0))/4
    agree=(late.min(0)>early.max(0))|(late.max(0)<early.min(0))
    variance=within if pooled else np.maximum(between,within)
    w=mu*mu/np.maximum(mu*mu+variance,1e-30)
    if not pooled:w*=agree
    return w,{'mean_effect':mu,'between_library_variance_of_mean':between,'within_library_variance_of_mean':within,'same_sign_all_cross_pairs':agree}

def estimate_weights(stats,cfg,pooled=False,permuted=False):
    genes=stats['genes'].astype(str);ng=len(genes);samples=sorted(set(k.split('|')[0] for k in stats.files if k.startswith('GSM')))
    early=[s for s in samples if 'E8_5' in s];late=[s for s in samples if 'E14_5' in s];assert len(early)==len(late)==2
    glob=np.array([x.startswith(('Hba','Hbb','mt-')) or x in IEG or x=='Malat1' for x in genes])
    def data(ss,g,k):return np.stack([stats[f'{s}|{g}|{k}'] for s in ss])
    def pooled_mean(g):
        ns=data(late,g,'n');ms=data(late,g,'mean');return (ns[:,None]*ms).sum(0)/max(ns.sum(),1)
    cm=np.maximum(pooled_mean('CM_V'),pooled_mean('CM_A'))
    result={};report={};rng=np.random.default_rng(cfg['control_seed'])
    for g in cfg['groups']:
        ns=data(samples,g,'n').astype(float);n8=data(early,g,'n').astype(float);n14=data(late,g,'n').astype(float)
        wd=np.ones(ng);wl=np.ones(ng)
        if ns.min()<cfg['minimum_cells_each_library']:
            result[g]=(wd,wl);report[g]={'status':'UNSUPPORTED_GROUP_EXACT_PARENT','minimum_library_cells':int(ns.min())};continue
        bad=glob.copy()
        if not g.startswith('CM'):
            mg=pooled_mean(g);bad|=(cm>4*np.maximum(mg,1e-3))&(cm>.3)
        mean8=(n8[:,None]*data(early,g,'mean')).sum(0)/n8.sum();mean14=(n14[:,None]*data(late,g,'mean')).sum(0)/n14.sum()
        eligible=stats['in_all_external']&~bad&((mean8>=cfg['minimum_mean_either_stage'])|(mean14>=cfg['minimum_mean_either_stage']))
        k8=data(early,g,'positive_count').astype(float);k14=data(late,g,'positive_count').astype(float)
        u8=logit((k8+.5)/(n8[:,None]+1));u14=logit((k14+.5)/(n14[:,None]+1))
        v8=1/(k8+.5)+1/(n8[:,None]-k8+.5);v14=1/(k14+.5)+1/(n14[:,None]-k14+.5)
        w,dd=uncertainty_weight(u8,u14,v8,v14,pooled);wd[eligible]=w[eligible]
        levok=eligible&(k8.min(0)>=cfg['minimum_positive_cells_each_library_for_level'])&(k14.min(0)>=cfg['minimum_positive_cells_each_library_for_level'])
        u8=data(early,g,'positive_mean');u14=data(late,g,'positive_mean');v8=data(early,g,'positive_var')/np.maximum(k8,1);v14=data(late,g,'positive_var')/np.maximum(k14,1)
        w,dl=uncertainty_weight(u8,u14,v8,v14,pooled);wl[levok]=w[levok]
        if permuted:
            ix=np.flatnonzero(eligible);wd[ix]=wd[rng.permutation(ix)]
            ix=np.flatnonzero(levok);wl[ix]=wl[rng.permutation(ix)]
        result[g]=(wd,wl)
        report[g]={'status':'FIT','minimum_library_cells':int(ns.min()),'detection_eligible_genes':int(eligible.sum()),'level_eligible_genes':int(levok.sum()),'detection_weight_quantiles':np.quantile(wd[eligible],[0,.1,.25,.5,.75,.9,1]).tolist() if eligible.any() else [],'level_weight_quantiles':np.quantile(wl[levok],[0,.1,.25,.5,.75,.9,1]).tolist() if levok.any() else [],'detection_disagreement_genes':int((eligible&~dd['same_sign_all_cross_pairs']).sum()),'level_disagreement_genes':int((levok&~dl['same_sign_all_cross_pairs']).sum()),'detection_between_exceeds_within':int((eligible&(dd['between_library_variance_of_mean']>dd['within_library_variance_of_mean'])).sum()),'level_between_exceeds_within':int((levok&(dl['between_library_variance_of_mean']>dl['within_library_variance_of_mean'])).sum())}
    return result,report
