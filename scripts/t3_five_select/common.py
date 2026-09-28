import csv,fcntl,json,pickle,shutil,time
from pathlib import Path
import numpy as np
import anndata as ad
from scripts.t3_next.common import ROOT,Context as PreviousContext,indexed,dense,sha,dump,diagnostics

DESIGN=ROOT/'configs/t3_five_select/design_20260929.json'


def save_model(path,obj):
    with Path(path).open('xb') as f:pickle.dump(obj,f,protocol=5)


def read_model(path):
    with Path(path).open('rb') as f:return pickle.load(f)


class Context(PreviousContext):
    def __init__(self,run):
        super().__init__(run,design=DESIGN)
        self.bestrow,self.bestpath=indexed('v0048');self.bestad=ad.read_h5ad(self.bestpath);self.best=dense(self.bestad.X)
        self.grow,self.gpath=indexed('v0046');g=ad.read_h5ad(self.gpath);self.graph=dense(g.X)
        for a in [self.bestad,g]:
            if not np.array_equal(a.obs_names,self.parent.obs_names) or list(a.var_names)!=self.genes or not np.array_equal(a.obsm['spatial_3D'],self.parent.obsm['spatial_3D']):raise ValueError('scored parent alignment')
        lock=json.loads((self.run/'INPUT_LOCK.json').read_text())
        lock['inputs'].update({self.bestrow['path']:self.bestrow['sha256'],self.grow['path']:self.grow['sha256']})
        (self.run/'code_five_select').mkdir()
        for p in sorted((ROOT/'scripts/t3_five_select').glob('*.py')):
            shutil.copy2(p,self.run/'code_five_select'/p.name);lock['inputs'][str(p.relative_to(ROOT))]=sha(p)
        lock.update(scored_best='v0048',second_scored_parent='v0046',carrier='v0009')
        dump(self.run/'INPUT_LOCK.json',lock)

    def save(self,lane,x,extra=None):
        x=np.asarray(x,dtype=np.float32)
        checks=diagnostics(self.best,x,np.asarray(self.parent.obsm['spatial_3D']),self.gi,self.cfg)
        if np.array_equal(x,self.best):checks['status']='NO_OP'
        dump(self.run/f'{lane}_CHECKS.json',checks)
        if checks['status']!='PASS':return None
        with (ROOT/'artifacts/t3_next/REGISTRATION.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            with (ROOT/'submissions/INDEX.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
            folder=ROOT/'submissions/candidates/T3_gata4'
            versions=[int(r['version'][1:]) for r in rows if r['board']=='T3:gata4']+[int(p.name[1:5]) for p in folder.glob('v[0-9][0-9][0-9][0-9]_*')]
            version=f'v{max(versions)+1:04d}';path=folder/f'{version}_five_select_{lane}'/'submission.h5ad'
            import sys
            sys.path.insert(0,str(ROOT/'docs/batch3/interfaces'))
            from virtual_embryo_tools.contract_io import write_candidate_from_parent,validate_h5ad_contract
            write_candidate_from_parent(parent_path=self.bestpath,output_path=path,expression=x,row_names=list(self.parent.obs_names),normalization='log_normalized',parent_sha256=self.bestrow['sha256'],metadata_updates={'ve_t3_five_select':json.dumps({'lane':lane,'run':str(self.run.relative_to(ROOT)),'parent':'v0048','carrier':'v0009','target_used':False,'design_sha256':sha(self.run/'code/design.json'),'model_sha256':sha(self.run/'model.pkl')},sort_keys=True)})
            contract=validate_h5ad_contract(path,task='T3',board='gata4',scorer_lock=ROOT/'artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json',parent_path=self.bestpath,parent_sha256=self.bestrow['sha256']);dump(self.run/f'{lane}_CONTRACT.json',contract)
            if contract['status']!='PASS':raise ValueError('contract failure')
            row=dict.fromkeys(rows[0],'');row.update(status='candidate',submission_group='T3-FIVE-SELECT-20260929',board='T3:gata4',version=version,method='five_select_'+lane,path=str(path.relative_to(ROOT)),n_cells='7449',n_genes='500',seed=str(self.cfg['seed']),target_used='false',local_contract='pass',sha256=sha(path),score_status='score_pending',notes=f'parent=v0048; carrier=v0009; run={self.run.relative_to(ROOT)}; NOT_SUBMITTED; full local execution, no Gata4 KO truth')
            with (ROOT/'submissions/INDEX.tsv').open('a') as f:csv.DictWriter(f,fieldnames=list(row),delimiter='\t',lineterminator='\n').writerow(row)
            info={'lane':lane,'version':version,'path':row['path'],'sha256':row['sha256'],'parent':'v0048','portal_file':f't3_gata4__{lane}__{version}.h5ad','checks':checks,**(extra or {})};self.candidates.append(info)
            with (ROOT/'docs/coordination/T3_TRACKING.md').open('a') as f:f.write(f'\n- 2026-09-29 T3-FIVE-SELECT {lane} 新候选 {version}，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 {self.run.relative_to(ROOT)}/RESULT.json。\n')
        return info
