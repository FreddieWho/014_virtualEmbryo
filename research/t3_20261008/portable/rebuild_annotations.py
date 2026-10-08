"""Rebuild only admitted E8.5 annotation TSVs from hash-bound public supplements.

Transparent replacement; original annotation extraction script was not recovered.
Downloads and outputs remain local user-controlled data, never repository content.
"""
import argparse,hashlib,json,urllib.request
from pathlib import Path
import pandas as pd
BASE='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-020-2552-x/MediaObjects/'
SOURCES={
 'Sup_Tab_1_nature.xlsx':('41586_2020_2552_MOESM4_ESM.xlsx','458a376158eee437b3dabe7be8d4a2ff893859ef646c7c90bb9c7d2cef52b574'),
 'Sup_Tab_2_nature.xlsx':('41586_2020_2552_MOESM5_ESM.xlsx','0d8638513d0bbd30750949ba6993f0d2d358dd1948145c782c792ebe16e80dbe')}
GENES=['WT','Dnmt3a','Kmt2a','Kdm2b','Dnmt1','Dnmt3b','G9a','Kmt2b']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workbooks',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--download',action='store_true');p.add_argument('--evidence-root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
 a.workbooks.mkdir(parents=True,exist_ok=True)
 for name,(suffix,digest) in SOURCES.items():
  f=a.workbooks/name
  if not f.exists():
   if not a.download:p.error(f'Missing {name}; provide cache or use --download')
   temp=f.with_suffix('.part')
   with urllib.request.urlopen(BASE+suffix,timeout=120) as r,temp.open('wb') as w:
    while chunk:=r.read(1048576):w.write(chunk)
   assert sha(temp)==digest,('Unexpected public supplement hash',name);temp.replace(f)
  assert sha(f)==digest,('Workbook hash mismatch',name)
 a.out.mkdir(parents=True,exist_ok=False)
 expected={}
 for name in ['TASK_DATA_PERMIT.json','ANNOTATION_PERMIT_v2.json']:
  for r in json.loads((a.evidence_root/'snapshots/v0087/external_sources'/name).read_text())['files']:
   expected[Path(r['file']).name]=r['sha256']
 report=[]
 for label in GENES:
  gene='Ehmt2' if label=='G9a' else label
  cells=pd.read_excel(a.workbooks/'Sup_Tab_2_nature.xlsx',sheet_name='WT85_cells' if label=='WT' else label+'_cells')
  embryos=pd.read_excel(a.workbooks/'Sup_Tab_1_nature.xlsx',sheet_name=label+'_embryos');embryos=embryos[embryos.Stage==85]
  assert embryos.Embryo.is_unique
  cells=cells.rename(columns={'BC':'barcode','Embryo':'embryo','EmbryoID':'embryo','Sex':'sex','Cell state':'cell_state','CellState':'cell_state','Lineage':'lineage','E/X':'embryonic_compartment'})
  cols=['barcode','embryo','sex','cell_state','lineage','embryonic_compartment'];cells=cells[cols].copy()
  assert cells.barcode.is_unique and set(cells.embryo)<=set(embryos.Embryo)
  meta=embryos.set_index('Embryo');assert (cells.sex==cells.embryo.map(meta.Sex)).all()
  cells['genotype']=gene
  if label in ['Dnmt1','Dnmt3b','G9a','Kmt2b']:cells['source_genotype_label']=label
  cells['collection_stage']='E8.5';cells['biological_replicate']=gene+'_E8.5_'+cells.embryo
  cells['published_composition_adjusted_stage']='WT 85' if label=='WT' else cells.embryo.map(meta['Adjusted stage'])
  assert not cells.isna().any().any()
  f=a.out/f'{label}_E8.5_cell_annotations.tsv';cells.to_csv(f,sep='\t',index=False)
  digest=sha(f);assert digest==expected[f.name],('Reconstructed annotation mismatch',f.name,digest,expected[f.name])
  report.append(dict(file=f.name,sha256=digest,cells=len(cells),embryos=cells.embryo.nunique(),exact_historical_bytes=True))
 result=dict(status='PASS',replacement_derivation=True,source_workbook_hashes={n:h for n,(_,h) in SOURCES.items()},admitted_conditions=GENES,outputs=report)
 (a.out/'ANNOTATION_REBUILD_CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
