"""Path-only adapters for archived input rebuilding. Dry-run by default."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
STAGES=['preprocess_source','preprocess_wt_idmatch','preprocess_expanded','check_features','normalize_source_panels']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--official-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--stage',choices=STAGES,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--evidence-root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
 r=a.evidence_root.resolve();src=r/'snapshots/v0088'/f'{a.stage}.py';code=src.read_text();digest=hashlib.sha256(src.read_bytes()).hexdigest();inventory=json.loads((r/'SNAPSHOT_INVENTORY.json').read_text());assert next(x['sha256'] for x in inventory if x['path']==str(src.relative_to(r)))==digest
 replacements={'/workspace/shared/t3_developmental_sources':str(a.source_root.resolve()),'/workspace/shared/virtual_embryo_data':str(a.official_root.resolve()),'/workspace/shared/t3_v87_restored':str(r/'snapshots/v0087')}
 changes=[]
 for before,after in replacements.items():
  n=code.count(before)
  if n:code=code.replace(before,after);changes.append({'from':before,'to':after,'occurrences':n})
 compile(code,str(src),'exec');receipt={'stage':a.stage,'original_code_sha256':digest,'adapted_code_sha256':hashlib.sha256(code.encode()).hexdigest(),'path_only_substitutions':changes,'execute':a.execute,'output_root':str(a.out.resolve())}
 if not a.execute:print(json.dumps(receipt,indent=2));return
 a.out.mkdir(parents=True,exist_ok=True)
 # No silent overwrite of a prior stage execution/output.
 log=a.out/f'{a.stage}_PATH_ADAPTER.json'
 if log.exists():p.error('This stage already ran here; use a new scratch directory')
 script=a.out/f'{a.stage}.py';script.write_text(code);log.write_text(json.dumps(receipt,indent=2)+'\n')
 subprocess.run([sys.executable,str(script)],check=True,cwd=a.out)
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
