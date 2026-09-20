"""Pre-matrix per-cell plan. Provisional retention never authorizes training."""
import collections,csv,gzip,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/t3_data_intake_20260920';Q=ROOT/'infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata'
black=set()
for r in csv.DictReader((ROOT/'docs/batch2/compliance/target_leakage_blacklist.tsv').open(),delimiter='\t'):
 if r['category']!='metadata_pattern':black.update(r['symbol_or_pattern'].upper().split('|'))
# Additional conservative developmental-signalling exclusions, without claiming equivalence.
extra={'SMAD2','SMAD3','SMAD4','TGFBR1'}
summary={};keep=[];remove=[];items=[]
for f in sorted(Q.glob('GSM81517*_protospacer_calls_per_cell.csv.gz')):
 sample=f.name.split('_')[0];meta=(Q/(sample+'_metadata.soft')).read_text()
 treatment=re.search(r'!Sample_characteristics_ch1 = treatment: (.*)',meta).group(1)
 selected=sample in {'GSM8151756','GSM8151757'}
 with gzip.open(f,'rt') as stream:rows=list(csv.DictReader(stream))
 counts=collections.Counter();reasons=collections.Counter()
 for r in rows:
  guides=r['feature_call'].split('|');genes={('ctrl' if g.startswith('NTC_') else 'Tgfbr1' if g.startswith('TGFbR_') else g.split('_')[0].capitalize()) for g in guides};real=genes-{'ctrl'}
  if any(g.upper() in black for g in real):reason='REMOVE_PROJECT_BLACKLIST'
  elif any(g.upper() in extra for g in real):reason='REMOVE_ADDITIONAL_DEVELOPMENTAL_SIGNALLING_RISK'
  elif len(real)>1 or int(r['num_features'])!=1:reason='REMOVE_MULTI_GUIDE_OR_MULTI_GENE'
  elif not selected:reason='NOT_SELECTED_STIMULATION_OR_BATCH_CONTEXT'
  elif len(real)==0 and genes!={'ctrl'}:reason='UNRESOLVED_CONTROL'
  else:reason='PROVISIONAL_KEEP_MANUAL_PHENOCOPY_REVIEW_PENDING'
  rec=dict(source='GSE261783',sample=sample,cell=r['cell_barcode'],condition=next(iter(real)) if len(real)==1 else ';'.join(sorted(genes)),guide=r['feature_call'],treatment=treatment,reason=reason,model_input='false')
  (keep if reason.startswith('PROVISIONAL') else remove).append(rec);reasons[reason]+=1
  if reason.startswith('PROVISIONAL'):counts[rec['condition']]+=1
 summary[sample]=dict(treatment=treatment,guide_assigned_cells=len(rows),selected=selected,provisional_counts=dict(counts),reason_counts=dict(reasons))
 if selected:
  for line in meta.splitlines():
   if line.startswith('!Sample_supplementary_file_') and line.endswith('_filtered_feature_bc_matrix.h5'):
    u=line.split(' = ',1)[1].replace('ftp://','https://');items.append(dict(name=u.rsplit('/',1)[1],url=u,max_bytes=700_000_000))
for name,rows in [('fibro_planned_keep_samples.tsv',keep),('fibro_planned_remove_samples.tsv',remove)]:
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=['source','sample','cell','condition','guide','treatment','reason','model_input'],delimiter='\t');w.writeheader();w.writerows(rows)
total=collections.Counter()
for x in summary.values():total.update(x['provisional_counts'])
receipt=dict(status='METADATA_SCREENED_QUARANTINE_ONLY',model_input=False,expression_read=False,source='GSE261783',age='8 weeks, paper methods',species='Mus musculus',selected_context='OP2 resting primary cardiac fibroblasts; two replicates',project_blacklist=sorted(black),additional_exclusions=sorted(extra),gene_counts=dict(total),genes_ge20=sum(n>=20 for g,n in total.items() if g!='ctrl'),samples=summary,remaining_blockers=['manual phenocopy review not complete','generic Perturb-seq task permission/use role unresolved','500 gene feature audit pending','no approved training manifest'])
(OUT/'FIBRO_METADATA_AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n');(OUT/'matrix_fetch_plan.json').write_text(json.dumps(items,indent=2)+'\n')
print('provisional retained',sum(total.values()),'genes>=20',receipt['genes_ge20'],'controls',total['ctrl']);print(dict(total))
