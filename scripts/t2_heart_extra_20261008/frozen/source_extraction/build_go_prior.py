from pathlib import Path
import csv,gzip,hashlib,json,collections
ROOT=Path('/workspace/shared/t2_external_sources_20261008'); OUT=ROOT/'go_topology';OUT.mkdir(exist_ok=True)
SRC=Path('/workspace/shared/t3source/GO'); panelpath=Path('/workspace/shared/virtual_embryo_data/T2__heart__val_extrap.genes.txt'); genes=panelpath.read_text().splitlines(); gene_set=set(genes)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'go-basic.obo':'b08d45b268b8c24ccb2513dbbbc7d4df9f6521c099b413f79eb31e06e0fa3bcc','MOUSE-uniprot.gaf.gz':'ea07d1a19adad445da59b2d8c48e7f7678827b09c12cc056f3faf7a1f88068b8'}
for n,h in expected.items():assert sha(SRC/n)==h
assert len(genes)==500 and len(gene_set)==500
terms={}
for block in (SRC/'go-basic.obo').read_text().split('[Term]')[1:]:
 d={'parents':[]}
 for line in block.splitlines():
  if line.startswith('id: '): d['id']=line[4:]
  elif line.startswith('name: '):d['name']=line[6:]
  elif line.startswith('namespace: '):d['namespace']=line[11:]
  elif line.startswith('is_a: '): d['parents'].append(line.split()[1])
  elif line.startswith('relationship: part_of '):d['parents'].append(line.split()[2])
  elif line=='is_obsolete: true':d['obsolete']=True
 if 'id' in d and not d.get('obsolete'):terms[d['id']]=d
rows=[];reasons=collections.Counter(); headers=[]
for line in gzip.open(SRC/'MOUSE-uniprot.gaf.gz','rt'):
 if line.startswith('!'):headers.append(line.strip());continue
 x=line.rstrip('\n').split('\t')
 if len(x)!=17:reasons['malformed']+=1;continue
 if x[2] not in gene_set:reasons['not_exact_panel_symbol']+=1;continue
 if x[6]!='IEA' or x[5]!='GO_REF:0000002' or x[14]!='InterPro' or not x[7].startswith('InterPro:'):reasons['not_interpro_sequence_signature']+=1;continue
 if 'NOT' in x[3].split('|'):reasons['negative_annotation']+=1;continue
 if x[12]!='taxon:10090':reasons['not_exact_mouse']+=1;continue
 if x[15]:reasons['context_extension']+=1;continue
 if x[4] not in terms:reasons['absent_or_obsolete_term']+=1;continue
 rows.append(x)
direct={g:set() for g in genes}
for x in rows:direct[x[2]].add(x[4])
def ancestors(t):
 seen=set(); todo=[t]
 while todo:
  q=todo.pop()
  if q in seen or q not in terms:continue
  seen.add(q);todo.extend(terms[q]['parents'])
 return seen
expanded={g:set().union(*(ancestors(t) for t in ts)) if ts else set() for g,ts in direct.items()}
term2gene=collections.defaultdict(list)
for g,ts in expanded.items():
 for t in ts:term2gene[t].append(g)
modules={t:sorted(gs) for t,gs in sorted(term2gene.items()) if 2<=len(gs)<=100}
with (OUT/'panel_gene_go_interpro.json').open('w') as f:json.dump({'genes':genes,'direct_gene_to_go':{g:sorted(v) for g,v in direct.items()},'ancestor_gene_to_go':{g:sorted(v) for g,v in expanded.items()},'modules':modules,'term_metadata':{t:terms[t] for t in term2gene}},f,indent=2)
with (OUT/'panel_gene_go_interpro_evidence.tsv').open('w') as f:
 w=csv.writer(f,delimiter='\t');w.writerow(['database','id','gene','relation','go_id','reference','evidence','with_from','aspect','name','synonyms','type','taxon','date','assigned_by','extension','product_form']);w.writerows(rows)
with (OUT/'module_membership.tsv').open('w') as f:
 w=csv.writer(f,delimiter='\t');w.writerow(['go_id','go_name','namespace','n_panel_genes','genes'])
 for t,gs in modules.items():w.writerow([t,terms[t]['name'],terms[t]['namespace'],len(gs),','.join(gs)])
(OUT/'panel_genes.txt').write_text('\n'.join(genes)+'\n')
permit={'task':'T2:heart:val_extrap','date':'2026-10-08','status':'ALLOW_GENERIC_SEQUENCE_ONTOLOGY_TOPOLOGY_ONLY','model_input_allowed':True,'role':'Unsigned gene-module membership and function topology only; not expression, velocities, lineage probabilities, timing, target proportions, scale or perturbation effect weights','source_files':[{'path':str(SRC/n),'sha256':h,'source_url':'https://current.geneontology.org/'+('ontology/' if n.endswith('.obo') else 'annotations/')+n} for n,h in expected.items()],'ontology_release':'2026-07-26','gaf_headers':headers,'license':'CC BY 4.0','license_url':'https://geneontology.org/docs/go-citation-policy/','rules_url':'https://virtualembryo.ai/challenge/rules','rules_basis':'Section 10 external public data permitted with licensing/disclosure; artifact contains generic sequence-signature function assertions only, no measured held-out-stage records or pretrained checkpoints. This is a new T2-scoped audit, not reuse of the T3 permit.','filters':['Exact official 500-gene panel symbol only','mouse taxon:10090 only','IEA AND GO_REF:0000002 AND assigned_by InterPro AND InterPro signature','No NOT qualifier; no context extension; no obsolete/missing ontology terms','Only is_a and part_of ontology propagation; no sign/regulates relationship','Modules retain 2-100 panel genes; filtering uses panel membership only, no expression or target observations'],'excluded':['All experimental/perturbation/expression-pattern GO evidence','All Ensembl orthology transfers, IBA, ARBA, UniRule and other non-InterPro inference','All T3 embeddings, learned weights, knockout-derived representations','All measured embryo data and all time-resolved priors'],'limitations':['GO functions do not establish developmental direction or a future cell state','InterPro annotations are sequence-homology function knowledge, not proof of cardiac-stage-specific activity','This prior is not a full organism/heart lineage graph','Must disclose original resources, frozen versions, filters and derived artifact hashes in method summary'],'rows_retained':len(rows),'direct_unique_gene_go_edges':sum(map(len,direct.values())),'genes_covered':sum(bool(v) for v in direct.values()),'modules':len(modules),'filtered_counts':dict(reasons),'panel_source_path':str(panelpath),'panel_sha256':sha(panelpath),'output_files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'T2_DATA_PERMIT.json']}
(OUT/'T2_DATA_PERMIT.json').write_text(json.dumps(permit,indent=2)+'\n');print(json.dumps({k:permit[k] for k in ['status','rows_retained','direct_unique_gene_go_edges','genes_covered','modules']},indent=2));print('permit',sha(OUT/'T2_DATA_PERMIT.json'))
