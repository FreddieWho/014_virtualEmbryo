"""Metadata-only audit of existing 006 resources. Never loads expression values."""
import collections,csv,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/t3_data_intake_20260920'
P=Path('/home/huyudi/006/data/perturb_seq')
panel=json.loads((OUT/'panel_genes.json').read_text())
black=set()
for r in csv.DictReader((ROOT/'docs/batch2/compliance/target_leakage_blacklist.tsv').open(),delimiter='\t'):
 if r['category']!='metadata_pattern':black.update(r['symbol_or_pattern'].upper().split('|'))
summary={};keep=[];remove=[];locked=[]
for prefix in ['GSM2396857_dc_0hr','GSM2396856_dc_3hr']:
 d=P/'GSE90063'
 guidefile=d/(prefix+('_cbc_gbc_dict.csv.gz' if '0hr' in prefix else '_cbc_gbc_dict_lenient.csv.gz'))
 files=[guidefile,d/(prefix+'_genenames.csv.gz'),d/(prefix+'_cellnames.csv.gz')]
 for f in files:locked.append(dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),role='metadata_only'))
 with gzip.open(files[1],'rt') as f:genes=[r[1].split('_',1)[-1] for r in list(csv.reader(f))[1:]]
 with gzip.open(files[2],'rt') as f:cells=[r[1] for r in list(csv.reader(f))[1:]]
 bycell=collections.defaultdict(set)
 with gzip.open(guidefile,'rt') as f:
  for guide,barcodes in csv.reader(f):
   gene='ctrl' if 'MouseNTC' in guide else guide.split('_')[1]
   for cell in barcodes.split(','):bycell[cell.strip()].add(gene)
 count=collections.Counter();reasons=collections.Counter()
 for cell in cells:
  targets=bycell.get(cell,set());real=targets-{'ctrl'}
  if any(g.upper() in black for g in real):why='BLACKLIST_MEMBER'
  elif len(real)>1:why='MULTI_GENE'
  elif not targets:why='UNASSIGNED_NOT_A_CONTROL'
  else:why='METADATA_CANDIDATE_PENDING_MANUAL_PHENOCOPY_REVIEW'
  rec=dict(source='GSE90063',sample=prefix,cell=cell,condition=';'.join(sorted(targets)),reason=why,model_input='false')
  (keep if why.startswith('METADATA') else remove).append(rec);reasons[why]+=1
  if why.startswith('METADATA'):count[next(iter(real)) if real else 'ctrl']+=1
 summary[prefix]=dict(n_cells=len(cells),n_genes=len(genes),panel_exact_symbol_overlap=len(set(genes)&set(panel)),missing_panel_genes=sorted(set(panel)-set(genes)),single_gene_counts=dict(count),perturbations_ge20=sum(v>=20 for g,v in count.items() if g!='ctrl'),filter_reason_counts=dict(reasons),model_input=False,status='REJECT_CURRENT_R6_PANEL_COVERAGE',limitations='literal gene symbols before alias audit; metadata-candidate is not clearance; 3h uses lenient guide assignment; not trained')
for name,rows in [('planned_keep_samples.tsv',keep),('planned_remove_samples.tsv',remove)]:
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=['source','sample','cell','condition','reason','model_input'],delimiter='\t');w.writeheader();w.writerows(rows)
(OUT/'LOCAL_METADATA_AUDIT.json').write_text(json.dumps(dict(sources=summary,metadata_inputs=locked,expression_read=False),indent=2)+'\n')
for name,r in summary.items():print(name,r['n_cells'],r['panel_exact_symbol_overlap'],r['perturbations_ge20'],r['single_gene_counts'].get('ctrl',0))
