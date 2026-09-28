"""Task-scoped inputs, immutable receipts and serial candidate registration."""
import csv,fcntl,hashlib,json,shutil,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import anndata as ad
from scipy import sparse
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'configs/t1_three/design_20260929.json'
OLD=ROOT/'artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1'
LOCK=ROOT/'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()


def dump(path,obj):
    def default(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,Path):return str(x)
        raise TypeError(str(type(x)))
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,default=default,ensure_ascii=False,allow_nan=False,indent=2)+'\n')


def dense(x):return np.asarray(x.toarray() if sparse.issparse(x) else x,dtype=np.float32)


def indexed(version):
    with (ROOT/'submissions/INDEX.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
    hits=[r for r in rows if r['board']=='T1:val' and r['version']==version]
    if len(hits)!=1:raise ValueError('ambiguous version')
    row=hits[0];p=ROOT/row['path']
    if sha(p)!=row['sha256']:raise ValueError('parent drift')
    return row,p


def write_matrix(path,x,types,genes,names=None):
    a=ad.AnnData(X=np.asarray(x,dtype=np.float32),obs=pd.DataFrame({'celltype':pd.Categorical(types)},index=names),var=pd.DataFrame(index=genes))
    a.uns['ve_contract']={'schema':'ve.contract.v1','normalization':'log1p_normalized'}
    a.write_h5ad(path,compression='gzip',compression_opts=1)


class Context:
    def __init__(self,run):
        self.run=Path(run).resolve();self.run.mkdir(parents=True,exist_ok=False);self.started=time.time()
        self.cfg=json.loads(CONFIG.read_text());self.genes=(ROOT/'data/gene_panel/T1__val.genes.txt').read_text().splitlines()
        self.row,self.parentpath=indexed('v0029');self.parent=ad.read_h5ad(self.parentpath);self.base=dense(self.parent.X)
        _,p=indexed('v0004');self.ancestor=ad.read_h5ad(p)
        self.sources=[];self.types=[];self.names=[];inputs={str(self.parentpath.relative_to(ROOT)):self.row['sha256'],str(p.relative_to(ROOT)):sha(p)}
        _,legacy=indexed('v0023');self.legacy=dense(ad.read_h5ad(legacy).X);inputs[str(legacy.relative_to(ROOT))]=sha(legacy)
        with (ROOT/'data/MANIFEST.tsv').open() as f:manifest={r['path']:r for r in csv.DictReader(f,delimiter='\t')}
        for name in ['E8.5_RNA','E9.5_RNA']:
            path=ROOT/'data'/(name+'.h5ad');digest=sha(path)
            if digest!=manifest[str(path.relative_to(ROOT))]['sha256']:raise ValueError('source drift')
            a=ad.read_h5ad(path);ix=a.var_names.get_indexer(self.genes)
            if (ix<0).any() or not a.obs_names.is_unique:raise ValueError('source identity')
            x=dense(a.X[:,ix])
            if (x<0).any() or not np.isfinite(x).all():raise ValueError('source values')
            self.sources.append(x);self.types.append(a.obs.celltype.astype(str).to_numpy());self.names.append(np.asarray(a.obs_names));inputs[str(path.relative_to(ROOT))]=digest
            del a
        self.xa,self.xb=self.sources;self.ta,self.tb=self.types
        if self.xa.shape!=(16787,32285) or self.xb.shape!=(17057,32285) or self.base.shape!=(5118,32285):raise ValueError('full shape')
        if list(self.parent.var_names)!=self.genes or not np.array_equal(self.ancestor.obs_names,self.parent.obs_names):raise ValueError('parent alignment')
        self.rows=pd.Index(self.names[1]).get_indexer(self.parent.obs_names)
        if (self.rows<0).any():raise ValueError('recipient rows')
        self.tr=[];self.te=[];self.reserved=[]
        for labels in self.types:
            tr,tmp=train_test_split(np.arange(len(labels)),test_size=.4,random_state=self.cfg['seed'],stratify=labels)
            te,res=train_test_split(tmp,test_size=.5,random_state=self.cfg['seed']+1,stratify=labels[tmp])
            self.tr.append(tr);self.te.append(te);self.reserved.append(res)
        if [len(v) for v in self.tr+self.te]!=[10072,10234,3357,3411]:raise ValueError('split drift')
        np.savez_compressed(self.run/'SPLITS.npz',train85=self.tr[0],train95=self.tr[1],report85=self.te[0],report95=self.te[1],reserved85=self.reserved[0],reserved95=self.reserved[1],recipient95=self.rows)
        sl=json.loads(LOCK.read_text())
        for f in sl['bundle_files']:
            if sha(ROOT/f['path'])!=f['sha256']:raise ValueError('scorer drift '+f['path'])
            inputs[f['path']]=f['sha256']
        (self.run/'code').mkdir()
        for p in sorted((ROOT/'scripts/t1_three').glob('*.py')):
            shutil.copy2(p,self.run/'code'/p.name);inputs[str(p.relative_to(ROOT))]=sha(p)
        shutil.copy2(CONFIG,self.run/'code/design.json');inputs[str(CONFIG.relative_to(ROOT))]=sha(CONFIG)
        (self.run/'code_legacy').mkdir()
        for p in sorted((ROOT/'scripts/t1_five').glob('*.py')):
            shutil.copy2(p,self.run/'code_legacy'/p.name);inputs[str(p.relative_to(ROOT))]=sha(p)
        (self.run/'code_round2').mkdir()
        for p in sorted((ROOT/'scripts/t1_round2').glob('*.py')):
            shutil.copy2(p,self.run/'code_round2'/p.name);inputs[str(p.relative_to(ROOT))]=sha(p)
        dump(self.run/'INPUT_LOCK.json',{'inputs':inputs,'target_used':False,'true_future_scoring':'NOT_RUN_NO_E105_TRUTH','full_shapes':[x.shape for x in self.sources],'split':'released-stage cell holdout, not embryo/time holdout'})
        self.candidates=[]

    def save(self,lane,out,model_path,predicted_types=None):
        out=np.asarray(out,dtype=np.float32)
        if out.shape!=self.base.shape or not np.isfinite(out).all() or (out<0).any():raise ValueError('output shape/values')
        raw=np.expm1(out).sum(1)/np.maximum(np.expm1(self.base).sum(1),1e-8);lo,hi=np.quantile(raw,[.01,.99]);vr=float(out.var(0).mean()/self.base.var(0).mean())
        cfg=self.cfg['engineering_gate'];ok=lo>=cfg['library_ratio_q01_min'] and hi<=cfg['library_ratio_q99_max'] and cfg['variance_ratio_min']<=vr<=cfg['variance_ratio_max']
        info={'status':'PASS' if ok else 'FAILED_ENGINEERING','library_ratio_q01':lo,'library_ratio_q99':hi,'variance_ratio':vr,'changed_entries':int(np.count_nonzero(out!=self.base)),'negative_clip_fraction':0.,'zero_rate':float(np.mean(out==0)),'full_genes':out.shape[1]}
        if np.array_equal(out,self.base):info['status']='NO_OP'
        dump(self.run/'CHECKS.json',info)
        if info['status']!='PASS':return None
        lockpath=ROOT/'artifacts/t1_five/REGISTRATION.lock';lockpath.parent.mkdir(exist_ok=True,parents=True)
        with lockpath.open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            with (ROOT/'submissions/INDEX.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
            folder=ROOT/'submissions/candidates/T1_val';versions=[int(r['version'][1:]) for r in rows if r['board']=='T1:val']+[int(p.name[1:5]) for p in folder.glob('v[0-9][0-9][0-9][0-9]_*')]
            version=f'v{max(versions)+1:04d}';path=folder/f'{version}_three_{lane}'/'submission.h5ad'
            sys.path.insert(0,str(ROOT/'docs/batch3/interfaces'))
            from virtual_embryo_tools.contract_io import write_candidate_from_parent,validate_h5ad_contract
            write_candidate_from_parent(parent_path=self.parentpath,output_path=path,expression=out,row_names=list(self.parent.obs_names),normalization='log1p_normalized',parent_sha256=self.row['sha256'],metadata_updates={'predicted_celltype':np.asarray(predicted_types,dtype=str) if predicted_types is not None else np.asarray(self.tb[self.rows],dtype=str),'row_identity_note':'synthetic output slots; expression donor indices in FINAL_OPERATOR.json; inherited obs annotations are recipient metadata, not predicted types','ve_t1_three':json.dumps({'lane':lane,'run':str(self.run.relative_to(ROOT)),'parent':'v0029','target_used':False,'design_sha256':sha(self.run/'code/design.json'),'model_sha256':sha(model_path)},sort_keys=True)})
            contract=validate_h5ad_contract(path,task='T1',board='val',scorer_lock=LOCK,parent_path=self.parentpath,parent_sha256=self.row['sha256']);dump(self.run/'CONTRACT.json',contract)
            if contract['status']!='PASS':raise ValueError('contract failed, artifact retained')
            row=dict.fromkeys(rows[0].keys(),'');row.update(status='candidate',submission_group='T1-THREE-20260929',board='T1:val',version=version,method='three_'+lane,path=str(path.relative_to(ROOT)),n_cells='5118',n_genes='32285',seed=str(self.cfg['seed']),target_used='false',local_contract='pass',sha256=sha(path),score_status='score_pending',notes=f'parent=v0029; run={self.run.relative_to(ROOT)}; NOT_SUBMITTED; report-scenario only; no E10.5 truth')
            with (ROOT/'submissions/INDEX.tsv').open('a') as f:csv.DictWriter(f,fieldnames=list(row),delimiter='\t',lineterminator='\n').writerow(row)
            candidate={'lane':lane,'version':version,'parent':'v0029','path':row['path'],'sha256':row['sha256'],'portal_file':f't1_val__{lane}__{version}.h5ad'};self.candidates.append(candidate)
            with (ROOT/'docs/coordination/T1_TRACKING.md').open('a') as f:f.write(f'\n- 2026-09-29 T1-THREE {lane} 新候选 {version}：完整5118×32285，parent=v0029，contract PASS，未提交/未评分；证据 {self.run.relative_to(ROOT)}/RESULT.json。\n')
        return candidate

    def finish(self,**extra):
        dump(self.run/'RESULT.json',{'status':'CANDIDATES_READY' if self.candidates else 'COMPUTED_NO_CANDIDATE','candidates':self.candidates,'wall_s':time.time()-self.started,'server_submission':'NOT_RUN','future_validation':'NOT_RUN_NO_E105_TRUTH','scientific_status':'EXPLORATORY_REPORT_SCENARIO','blocks_submission':False,**extra})
