"""Audit relationship metadata and nominate sources; never builds a model prior."""
import csv,collections,gzip,hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/t3_data_intake_20260920';Q=ROOT/'infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata'
panel=set(json.loads((OUT/'panel_genes.json').read_text()));data=json.loads((Q/'connectomedb_mouse.json').read_text());rows=[]
for r in data:
 pair=r['LR_Pair'].split()
 if len(pair)!=2 or not set(pair)<=panel:continue
 url=re.search('href="([^"]+)"',r['Interaction_ID']).group(1);card=Q/'lr_cards'/url.rsplit('/',1)[1]
 pmids=[]
 if card.exists():
  soup=BeautifulSoup(card.read_text(),'html.parser')
  for a in soup.find_all('a',href=True):
   m=re.search(r'(?:pubmed.ncbi.nlm.nih.gov/|ncbi.nlm.nih.gov/pubmed/)(\d+)',a['href'])
   if m:pmids.append(m.group(1))
 # The AI_summary link is deliberately not evidence and is never followed.
 risk=any(g.upper().startswith(('WNT','RSPO','NODAL','GATA')) for g in pair)
 rows.append(dict(ligand=pair[0],receptor=pair[1],mapping_evidence=r['Evidence'],source_reference=url,pmids=';'.join(sorted(set(pmids))),source_card_status='DOWNLOADED' if card.exists() else 'MISSING',screen_status='HOLD_DEVELOPMENTAL_PATHWAY_REVIEW' if risk else 'HOLD_REFERENCE_CONTEXT_AND_LICENSE_REVIEW',target='NOT_PROVIDED_BY_LR_DATABASE',model_input='false'))
with (OUT/'R5_PANEL_LR_REVIEW.tsv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
tf=list(csv.DictReader((Q/'cellphonedb_transcription_factor.csv').open()));lr=list(csv.DictReader((Q/'cellphonedb_interactions.csv').open()))
r=dict(status='PARTIAL_RELATIONSHIP_RESOURCES_COLLECTED_NOT_APPROVED',model_input=False,connectomedb=dict(total_mouse_pairs=len(data),direct=sum(r['Evidence']=='Direct' for r in data),inferred=sum(r['Evidence']=='Inferred' for r in data),panel_pairs=len(rows),panel_direct=sum(r['mapping_evidence']=='Direct' for r in rows),cards_present=sum(r['source_card_status']=='DOWNLOADED' for r in rows),pairs_with_primary_links=sum(bool(r['pmids']) for r in rows),license='CONFLICT: downloads says MIT; terms distinguish database CC-BY-NC-4.0 from software MIT; no permissive interpretation adopted',ai_summary_used=False),cellphonedb=dict(lr_rows=len(lr),receptor_tf_rows=len(tf),receptor_tf_rows_with_pmid=sum('PMID' in r['Source'] for r in tf),species='human',orthology_audit='NOT_RUN',license='data license unresolved: website defaults CC-BY-NC-ND-4.0; software MIT is not a data license'),complete_approved_ligand_receptor_target_edges=0,limitations=['LR pairs do not specify downstream target genes','receptor-to-TF activation is not evidence of TF transcript response','per-reference target/phenocopy provenance still requires manual review','no trained NicheNet weights or aggregated target-response priors used'])
(OUT/'R5_RESOURCE_AUDIT.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r['connectomedb']));print(json.dumps(r['cellphonedb']))
brain=Q/'brain_features.tsv.gz'
if brain.exists():
 with gzip.open(brain,'rt') as f:features=list(csv.reader(f,delimiter='\t'))
 names={x[1] if len(x)>1 else x[0] for x in features};config=json.loads((Q/'brain_ucsc_combined.json').read_text())
 b=dict(status='BACKUP_METADATA_ONLY_NOT_APPROVED',source='perturbai/wholebrain_crispr_atlas; author-linked UCSC mirror',source_page='https://huggingface.co/datasets/perturbai/wholebrain_crispr_atlas',model_input=False,feature_count=len(features),panel_exact_symbol_overlap=len(panel&names),missing_panel_genes=sorted(panel-names),ucsc_cells=config['sampleCount'],matrix_bytes=config['fileVersions']['inMatrix']['size'],metadata_bytes=config['fileVersions']['inMeta']['size'],expression_downloaded=False,full_cell_metadata_downloaded=False,huggingface_download='FAILED_SSL_EOF',license='CC-BY-4.0 on author dataset card; web-verified',limitations='UCSC filtered release and HF 7.72M release are different denominators; brain context less matched than cardiac fibroblasts; huge matrix not acquired before cellwise firewall')
 (OUT/'BRAIN_METADATA_AUDIT.json').write_text(json.dumps(b,indent=2)+'\n');print('brain feature coverage',b['panel_exact_symbol_overlap'])
