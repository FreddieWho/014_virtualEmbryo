from __future__ import annotations
import csv,hashlib,json,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import anndata as ad
from scipy import sparse
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
DESIGN=ROOT/'configs/t3_next/design.json'
MOTIF=ROOT/'infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN/mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet'
ATLAS=ROOT/'artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def dump(p,obj):
    def convert(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,Path):return str(x)
        raise TypeError(type(x).__name__)
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(obj,default=convert,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def dense(x):return np.asarray(x.toarray() if sparse.issparse(x) else x,dtype=np.float32)


def indexed(version):
    with (ROOT/'submissions/INDEX.tsv').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
    found=[r for r in rows if r['board']=='T3:gata4' and r['version']==version]
    if len(found)!=1:raise ValueError('ambiguous/missing version '+version)
    r=found[0];p=ROOT/r['path']
    if sha(p)!=r['sha256']:raise ValueError('parent SHA mismatch '+str(p))
    return r,p


class Context:
    def __init__(self,run,design=DESIGN):
        self.run=Path(run).resolve();self.run.mkdir(parents=True,exist_ok=False)
        self.started=time.time();self.design=Path(design);self.cfg=json.loads(self.design.read_text())
        self.row,self.parent_path=indexed('v0009');self.parent=ad.read_h5ad(self.parent_path)
        self.genes=list(self.parent.var_names.astype(str));self.gi=self.genes.index('Gata4')
        panel=(ROOT/'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
        if self.genes!=panel:raise ValueError('panel/order drift')
        self.wt_path=ROOT/'data/E8.75.h5ad'
        with (ROOT/'data/MANIFEST.tsv').open() as f:r=next(r for r in csv.DictReader(f,delimiter='\t') if r['path']=='data/E8.75.h5ad')
        if sha(self.wt_path)!=r['sha256']:raise ValueError('WT SHA mismatch')
        self.wt=ad.read_h5ad(self.wt_path)
        if not self.wt.obs_names.is_unique:raise ValueError('WT row ids not unique')
        self.rows=self.wt.obs_names.get_indexer(self.parent.obs_names)
        if (self.rows<0).any():raise ValueError('parent rows missing WT')
        self.x=dense(self.wt[:,self.genes].X);self.base=dense(self.parent.X)
        reconstructed=self.x[self.rows].copy();reconstructed[:,self.gi]=0
        if not np.array_equal(reconstructed,self.base):raise ValueError('WT-to-parent identity mismatch')
        self.labels=self.wt.obs.celltype.astype(str).to_numpy();self.plabels=self.labels[self.rows]
        self.coords=np.asarray(self.wt.obsm['spatial_3D'])[:,:3].astype(float)
        parent_coords=np.asarray(self.parent.obsm['spatial_3D'])
        source_coords=np.asarray(self.wt.obsm['spatial_3D'])[self.rows].astype(parent_coords.dtype)
        if not np.array_equal(parent_coords,source_coords):raise ValueError('WT coordinates mismatch after historical parent dtype conversion')
        # Distinct z bins provide a reproducible within-specimen spatial block split.
        z=self.coords[:,2];edges=np.quantile(z,[.25,.5,.75]);self.blocks=np.searchsorted(edges,z,side='right')
        if len(np.unique(self.blocks))<2:raise ValueError('no spatial split support')
        self.candidates=[]
        inputs={str(self.wt_path.relative_to(ROOT)):r['sha256'],self.row['path']:self.row['sha256'],str(self.design.relative_to(ROOT)):sha(self.design)}
        inputs.update({str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts/t3_next').glob('*.py'))})
        # Retain the exact implementation for this receipt even after later repairs.
        import shutil
        (self.run/'code').mkdir()
        for p in sorted((ROOT/'scripts/t3_next').glob('*.py')):shutil.copy2(p,self.run/'code'/p.name)
        shutil.copy2(self.design,self.run/'code/design.json')
        dump(self.run/'INPUT_LOCK.json',{'inputs':inputs,'identity_reproduced':True,'shape':self.base.shape,'block_counts':pd.Series(self.blocks).value_counts().to_dict(),'split_limit':'within-specimen spatial blocks, not biological replicates','seed':self.cfg['seed']})

    def finish(self,status,**extra):
        result={'status':status,'candidates':self.candidates,'wall_s':time.time()-self.started,'scientific_status':'NOT_IDENTIFIABLE','server_status':'NOT_SUBMITTED','server_scoring':'NOT_RUN','full_panel_local_scorer':'NOT_RUN_NO_MATCHED_GATA4_TARGET','blocks_submission':False,**extra}
        dump(self.run/'RESULT.json',result)
        print(json.dumps({'run':str(self.run),'status':status,'candidates':len(self.candidates),'wall_s':round(result['wall_s'],1)}),flush=True)
        return result

    def motif(self):
        mpath=MOTIF.parent.parent/'snapshot_manifest.json';m=json.loads(mpath.read_text())
        if sha(MOTIF)!=m['sha256']:raise ValueError('motif hash mismatch')
        d=pd.read_parquet(MOTIF)
        dump(self.run/'MOTIF_PERMIT.json',{'path':str(MOTIF.relative_to(ROOT)),'sha256':m['sha256'],'role':'WT motif topology only; no sign/outcome consumed','source_url':m['source_url'],'license':m['license'],'authorization':'six-route implementation; WT-only context model per docs/batch2/compliance/protected_windows.yaml','no_S1_gate_promotion':True})
        return d

    def save(self,lane,x,parent_version='v0009',extra=None):
        import fcntl
        lock_path=ROOT/'artifacts/t3_next/REGISTRATION.lock'
        lock_path.parent.mkdir(parents=True,exist_ok=True)
        with lock_path.open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            return self._save_locked(lane,x,parent_version,extra)

    def _save_locked(self,lane,x,parent_version='v0009',extra=None):
        x=np.asarray(x,dtype=np.float32)
        row,parent_path=indexed(parent_version);parent=ad.read_h5ad(parent_path)
        if not np.array_equal(parent.obs_names,self.parent.obs_names):raise ValueError('donor row order mismatch')
        checks=diagnostics(self.base,x,np.asarray(self.parent.obsm['spatial_3D']),self.gi,self.cfg)
        if np.array_equal(x,dense(parent.X)):
            checks['status']='NO_OP';dump(self.run/f'{lane}_CHECKS.json',checks);return None
        dump(self.run/f'{lane}_CHECKS.json',checks)
        if checks['status']!='PASS':return None
        with (ROOT/'submissions/INDEX.tsv').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
        versions=[int(r['version'][1:]) for r in rows if r['board']=='T3:gata4']
        folder=ROOT/'submissions/candidates/T3_gata4'
        versions += [int(p.name[1:5]) for p in folder.glob('v[0-9][0-9][0-9][0-9]_*')]
        version=f'v{max(versions)+1:04d}';method='next_'+lane
        out=folder/f'{version}_{method}'/'submission.h5ad'
        sys.path.insert(0,str(ROOT/'docs/batch3/interfaces'))
        from virtual_embryo_tools.contract_io import write_candidate_from_parent,validate_h5ad_contract
        write_candidate_from_parent(parent_path=parent_path,output_path=out,expression=x,row_names=list(parent.obs_names),normalization='log_normalized',parent_sha256=row['sha256'],metadata_updates={'ve_t3_next':json.dumps({'lane':lane,'run':str(self.run.relative_to(ROOT)),'design_sha256':sha(self.design),'parent':parent_version,'seed':self.cfg['seed'],'target_used':False},sort_keys=True)})
        report=validate_h5ad_contract(out,task='T3',board='gata4',scorer_lock=ROOT/'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',parent_path=parent_path,parent_sha256=row['sha256'])
        dump(self.run/f'{lane}_CONTRACT.json',report)
        if report['status']!='PASS':raise ValueError('contract failed; artifact retained unregistered: '+str(out))
        new=dict.fromkeys(rows[0].keys(),'');new.update(status='candidate',submission_group='T3-NEXT-'+lane.split('_')[0].upper(),board='T3:gata4',version=version,method=method,path=str(out.relative_to(ROOT)),n_cells=str(x.shape[0]),n_genes=str(x.shape[1]),seed=str(self.cfg['seed']),target_used='false',local_contract='pass',sha256=sha(out),score_status='score_pending',notes=f'parent={parent_version}; run={self.run.relative_to(ROOT)}; NOT_SUBMITTED; local structural checks only; scientific NOT_IDENTIFIABLE')
        with (ROOT/'submissions/INDEX.tsv').open('a') as f:csv.DictWriter(f,fieldnames=list(new),delimiter='\t',lineterminator='\n').writerow(new)
        info={'lane':lane,'version':version,'path':new['path'],'sha256':new['sha256'],'parent':parent_version,'portal_file':f't3_gata4__{lane}__{version}.h5ad','checks':checks,**(extra or {})};self.candidates.append(info)
        with (ROOT/'docs/coordination/T3_TRACKING.md').open('a') as f:f.write(f'\n{self.cfg["date"]}（{version} {lane}）：新建六路线候选，parent={parent_version}；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 {self.run.relative_to(ROOT)}/RESULT.json。\n')
        return info


def diagnostics(base,x,coords,gi,cfg):
    if x.shape!=base.shape or not np.isfinite(x).all() or (x<0).any():return {'status':'FAIL_SHAPE_OR_VALUES'}
    if np.any(x[:,gi]!=0):return {'status':'FAIL_GENOTYPE'}
    keep=np.arange(x.shape[1])!=gi
    libraries=np.expm1(x).sum(1)/np.maximum(np.expm1(base).sum(1),1e-8)
    vr=float(np.var(x[:,keep],axis=0).mean()/max(np.var(base[:,keep],axis=0).mean(),1e-8))
    _,nn=cKDTree(coords).query(coords,k=2);j=nn[:,1]
    local=float(np.mean((x[:,keep]-x[j][:,keep])**2)/max(float(np.mean((base[:,keep]-base[j][:,keep])**2)),1e-8))
    lo,hi=np.quantile(libraries,[.01,.99]);b=cfg['disaster_bounds']
    ok=lo>=b['cell_library_ratio_q01_min'] and hi<=b['cell_library_ratio_q99_max'] and b['variance_ratio_min']<=vr<=b['variance_ratio_max']
    return {'status':'PASS' if ok else 'FAIL_DISASTER','library_ratio_q01':float(lo),'library_ratio_q99':float(hi),'variance_ratio':vr,'neighbor_semivariance_ratio':local,'semivariance_role':'descriptive_only_not_server_variogram','changed_entries':int(np.count_nonzero(base!=x))}
