"""Fresh-process replay and requirement audit of all six full-panel routes."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import argparse,csv,json,pickle,hashlib,zipfile,io,warnings
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import anndata as ad
from .common import ROOT,indexed,sha,dump,dense
from .models import predict,SHARED,cache,core_model,plans
from .ops import exact_plan,plan_fields,consistency_distances,stability_fractions,adaptive_sides,shrunk_cov
from scripts.t1_round2.ops import abundance_step

def table(rows):
    f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);return f.getvalue()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--zip',type=Path,required=True);args=ap.parse_args();cfg=json.loads((ROOT/'configs/t1_six/design_20261007.json').read_text());lanes=cfg['six']['lanes'];checks=[];members=[];mapping=[];runmap=[];pointers=[]
    assert len(lanes)==6 and [len(v) for v in cfg['six']['categories'].values()]==[3,3]
    assert json.loads((args.root/'BATCH_RESULT.json').read_text())['status']=='COMPLETED'
    for name,digest in json.loads((SHARED/'CACHE_LOCK.json').read_text()).items():assert sha(ROOT/name)==digest
    shared=json.loads((SHARED/'READY.json').read_text());assert len(shared['component_audit'])==4 and all(r['exact'] for r in shared['component_audit'])
    _,bp=indexed('v0035');base=ad.read_h5ad(bp);genes=list(base.var_names);sources=[];types=[];names=[]
    for stage in ['E8.5_RNA','E9.5_RNA']:
        a=ad.read_h5ad(ROOT/'data'/f'{stage}.h5ad');sources.append(dense(a.X[:,a.var_names.get_indexer(genes)]));types.append(a.obs.celltype.astype(str).to_numpy());names.append(a.obs_names);del a
    _,lp=indexed('v0023');legacy=dense(ad.read_h5ad(lp).X);rows=names[1].get_indexer(base.obs_names);assert (rows>=0).all()
    splits=np.load(args.root/lanes[0]/'SPLITS.npz');c=SimpleNamespace(xa=sources[0],xb=sources[1],ta=types[0],tb=types[1],rows=rows,legacy=legacy,te=[splits['report85'],splits['report95']],cfg=cfg,seed=cfg['seed'])
    hashes=set();verified={};science={}
    for lane in lanes:
        run=args.root/lane;r=json.loads((run/'RESULT.json').read_text());assert r['route']==lane and r['report_scorer']=='EXECUTED'
        score=json.loads((run/'SCORER.json').read_text());assert score['meta']['genes']==32285 and score['meta']['prediction_cells']==3357 and score['meta']['truth_cells']==3411
        assert json.loads((run/'SCORER_PROCESS.json').read_text())['exit_code']==0
        sp=np.load(run/'SPLITS.npz')
        for stage,n in [('85',16787),('95',17057)]:np.testing.assert_array_equal(np.sort(np.concatenate([sp[k+stage] for k in ['train','report','reserved']])),np.arange(n))
        for name,digest in json.loads((run/'INPUT_LOCK.json').read_text())['inputs'].items():
            p=ROOT/name
            for prefix,folder in [('scripts/t1_six/','code'),('scripts/t1_seven/','code_seven'),('scripts/t1_three/','code_three'),('scripts/t1_round2/','code_round2'),('scripts/t1_five/','code_legacy')]:
                if name.startswith(prefix):p=run/folder/Path(name).name
            if name.startswith('configs/t1_six/'):p=run/'code/design.json'
            if str(p) not in verified:verified[str(p)]=sha(p)
            assert verified[str(p)]==digest,(name,'input/code drift')
        for scope,future in [('report',False),('final',True)]:
            with (run/(scope+'_model.pkl')).open('rb') as f:m=pickle.load(f)
            # per-lane design snapshot (locked in INPUT_LOCK) is the correct fit-time reference;
            # the top-level design JSON may carry later descriptive amendments, disclosed in the report
            lane_cfg=json.loads((run/'code'/'design.json').read_text())['six']
            assert m['cfg']==lane_cfg and m['cache_lock']==sha(SHARED/'CACHE_LOCK.json') and sha(ROOT/m['parent_model'])==m['parent_model_sha256']
            aids=np.arange(len(c.xa)) if future else sp['train85'];bids=np.arange(len(c.xb)) if future else sp['train95'];np.testing.assert_array_equal(m['train_early'],aids);np.testing.assert_array_equal(m['train_late'],bids)
            za=cache(scope,'early_latent');zb=cache(scope,'late_latent');ta=c.ta[aids];tb=c.tb[bids]
            if lane=='ocovstab':
                src=ROOT/'artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot'/('REPORT_OPERATOR.json' if not future else 'FINAL_OPERATOR.json')
                distances=json.loads(src.read_text())
                med=float(np.median([float(v['projection_mean_distance']) for v in distances.values() if isinstance(v,dict) and 'projection_mean_distance' in v]));assert abs(med-m['reliability_median'])<1e-12
                assert m['reliability_source']==str(src.relative_to(ROOT))
                for typ,g in m['groups'].items():
                    expected=cfg['six']['ocovstab']['strength_stable'] if float(distances[typ]['projection_mean_distance'])<=med else cfg['six']['ocovstab']['strength_unstable']
                    assert g['strength']==expected,(typ,'strength rule')
                    aa=g['scaler'].transform(za[ta==typ,:g['dim']]);bb=g['scaler'].transform(zb[tb==typ,:g['dim']])
                    np.testing.assert_allclose(g['map']@shrunk_cov(aa,cfg['six']['ocovstab']['cov_shrink'])@g['map'].T,shrunk_cov(bb,cfg['six']['ocovstab']['cov_shrink']),rtol=1e-7,atol=1e-7)
            elif lane=='osoftcov':
                for typ,g in m['groups'].items():
                    aa32=za[ta==typ];bb32=zb[tb==typ]
                    np.testing.assert_allclose(g['step'],abundance_step(g['gmm'].predict_proba(np.asarray(aa32,dtype=np.float64)).sum(0),g['gmm'].predict_proba(np.asarray(bb32,dtype=np.float64)).sum(0),cfg['six']['osoftcov']['soft_prior'],cfg['six']['osoftcov']['soft_strength'],2.),rtol=1e-9)
                    assert g['gmm'].converged_
                    aa8=g['scaler'].transform(np.asarray(za[ta==typ,:8],dtype=np.float64));bb8=g['scaler'].transform(np.asarray(zb[tb==typ,:8],dtype=np.float64))
                    np.testing.assert_allclose(g['map']@shrunk_cov(aa8,cfg['six']['osoftcov']['cov_shrink'])@g['map'].T,shrunk_cov(bb8,cfg['six']['osoftcov']['cov_shrink']),rtol=1e-6,atol=1e-6)
            elif lane=='ostabmix':
                for typ,g in m['groups'].items():
                    np.testing.assert_array_equal(g['early_ids'],aids[ta==typ]);np.testing.assert_array_equal(g['late_ids'],bids[tb==typ])
                    fraction,sc,_=stability_fractions(c.xa[g['early_ids']],c.xb[g['late_ids']],cfg['six']['ostabmix']['stability_parts'],cfg['six']['ostabmix']['stability_required'],0.25,cfg['six']['ostabmix']['stability_seed'])
                    assert g['fraction']==fraction and abs(g['stability_score']-sc)<1e-12
                    assert g['fraction'] in (0.3,0.7)
            elif lane=='nconf':
                from .ops import conformal_radius
                for ti,typ in enumerate(sorted(m['groups'])):
                    g=m['groups'][typ]
                    aa=np.asarray(za[ta==typ,:8],dtype=np.float64);bb=np.asarray(zb[tb==typ,:8],dtype=np.float64)
                    perm=np.random.default_rng([cfg['seed'],1000+ti]).permutation(len(aa));half=max(10,len(aa)//2)
                    perm_b=np.random.default_rng([cfg['seed'],2000+ti]).permutation(len(bb))
                    r2=conformal_radius(aa[perm[:half]],bb[perm_b[:max(10,len(bb)//2)]],aa[perm[half:]],bb,cfg['six']['nconf']['conformal_alpha'],cfg['six']['nconf']['cov_shrink'],cfg['six']['nconf']['cov_strength'])
                    assert r2 is not None and abs(r2['radius']-g['radius'])<1e-12 and g['radius']>0
            elif lane in ('nwasser','nbidir'):
                P=plans(scope)
                for typ,g in P.items():
                    assert g['plan_info']['row_residual']<=1e-8 and g['plan_info']['col_residual']<=1e-8
                    aa=np.asarray(za[ta==typ],dtype=np.float64);bb=np.asarray(zb[tb==typ],dtype=np.float64)
                    from sklearn.preprocessing import StandardScaler
                    scaler=StandardScaler().fit(np.vstack([aa,bb]));a2=scaler.transform(aa);b2=scaler.transform(bb)
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        plan,_=exact_plan(a2,b2)
                    d_e,d_l,_,_=plan_fields(plan,a2,b2)
                    np.testing.assert_allclose(d_e,g['d_early'],rtol=1e-5,atol=1e-5)
                    np.testing.assert_allclose(d_l,g['d_late'],rtol=1e-5,atol=1e-5)
                    if lane=='nbidir':
                        ce,cl=consistency_distances(plan,a2,b2)
                        np.testing.assert_allclose(ce,g['cons_early'],rtol=1e-5,atol=1e-5);np.testing.assert_allclose(cl,g['cons_late'],rtol=1e-5,atol=1e-5)
                        assert abs(g['sigma']-float(np.median(np.concatenate([ce,cl]))))<1e-9
            replay,details=predict(m,c);path=run/('full_prediction.h5ad' if future else 'report_prediction.h5ad');actual=ad.read_h5ad(path)
            np.testing.assert_array_equal(replay,dense(actual.X));assert replay.shape==((5118,32285) if future else (3357,32285));assert np.isfinite(replay).all() and (replay>=0).all()
            assert list(actual.var_names)==genes
            if future:
                assert list(actual.obs_names)==list(base.obs_names);h=hashlib.sha256(replay.tobytes()).hexdigest();assert h not in hashes,'duplicate new route';hashes.add(h)
                for candidate in r['candidates']:
                    row,p=indexed(candidate['version']);assert candidate['sha256']==row['sha256'];a=ad.read_h5ad(p);np.testing.assert_array_equal(dense(a.X),replay);np.testing.assert_array_equal(a.uns['predicted_celltype'],details['predicted_types']);assert list(a.obs_names)==list(base.obs_names) and list(a.var_names)==genes
                    assert row['score_status']=='score_pending' and row['local_contract']=='pass';assert json.loads((run/'CONTRACT.json').read_text())['status']=='PASS';assert json.loads((run/'CHECKS.json').read_text())['status']=='PASS'
                    name=candidate['portal_file'];assert len(name)<=50 and name==name.lower();members.append({'filename':name,'bytes':p.stat().st_size,'sha256':sha(p)});mapping.append({'filename':name,'board':'T1:val','version':row['version'],'canonical_path':row['path']});runmap.append({'filename':name,'run_id':str(run),'parent_version':'v0035'});pointers.append({'filename':name,'result':str(run/'RESULT.json'),'contract':str(run/'CONTRACT.json')})
            del m,replay,actual
        checks.append({'lane':lane,'category':next(k for k,v in cfg['six']['categories'].items() if lane in v),'scorer':'FULL_32285_EXECUTED','report_and_final_replay':'PASS','fit_specific_checks':'PASS','training_split_and_code_hashes':'PASS','candidates':len(r['candidates'])});science[lane]=score['metrics'];print('ACCEPTED',lane,flush=True)
    args.zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.zip,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for row in mapping:z.write(ROOT/row['canonical_path'],row['filename'])
        for name,records in [('MANIFEST.tsv',members),('UPLOAD_MANIFEST.tsv',mapping),('RUN_ID_MAP.tsv',runmap),('EVIDENCE_MANIFEST_POINTERS.tsv',pointers)]:z.writestr(name,table(records))
    with zipfile.ZipFile(args.zip) as z:
        for row in members:
            with z.open(row['filename']) as f:
                h=hashlib.sha256()
                for block in iter(lambda:f.read(4<<20),b''):h.update(block)
            assert h.hexdigest()==row['sha256']
        assert z.testzip() is None
    args.report.mkdir(parents=True,exist_ok=True);dump(args.report/'VALIDATION.json',{'status':'PASS','requirements':{'three_optimization_combination':3,'three_new':3,'routes_executed':6,'full_panel_scorers':6},'routes':checks,'scored_parents_exact_reproductions':4,'archive_members':len(members),'archive_crc_sha':'PASS','validator_sha256':sha(Path(__file__)),'future_truth':'NOT_RUN_NO_E105_TRUTH'})
    dump(args.report/'METRICS.json',science);dump(args.zip.with_suffix('.receipt.json'),{'status':'READY_NOT_SUBMITTED','members':len(members),'zip_sha256':sha(args.zip),'zip_path':str(args.zip)});print('VALIDATION AND PACKAGE PASS',len(members),flush=True)
if __name__=='__main__':main()
