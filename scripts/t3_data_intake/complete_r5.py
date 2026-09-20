"""Materialize a manually reviewed, minimal SIGNOR topology allowlist.

No response values, source signs, scores or pretrained weights enter the model.
This is a cross-context hypothesis, not an experimentally verified complete chain.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'infra/external_data/quarantine/T3-R5-COMPLETION-20260920'
REPORT = ROOT / 'reports/t3_r5_completion_20260920'
OUT = ROOT / 'infra/external_data/sanitized/T3-R5-SIGNOR-MINIMAL-20260920'
SELECTED = [
    ('SIGNOR-107400', 'PDGFB', 'PDGFRB', '11331882', 'Ligand binding; independently checked PDGF-B/PDGFR-beta structural study PMC2895058; no embryonic response data'),
    ('SIGNOR-247979', 'PDGFRB', 'SRC', '15489898', 'Human lung adenocarcinoma cell detachment/anoikis; RTK signaling context, not embryonic cardiac knockout'),
    ('SIGNOR-235696', 'SRC', 'STAT1', '14978237', 'Human NCI-H292 epithelial cells; IFN-gamma/TPA signaling; different stimulus from PDGF'),
    ('SIGNOR-255237', 'STAT1', 'S100A10', '12645529', 'Human BEAS-2B and HeLa cells; p11 promoter GAS-site mutagenesis and STAT1 dominant negative; transcription, not protein-only activation'),
]


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')


def tsv(p, rows):
    with p.open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main():
    if OUT.exists():
        raise SystemExit('Refusing to overwrite existing sanitized package')
    source = RAW / 'signor_human.tsv'
    receipt = json.loads((REPORT / 'FETCH_RECEIPT4.json').read_text())['files'][0]
    assert sha(source) == receipt['sha256']
    records = list(csv.DictReader(source.open(), delimiter='\t'))
    by_id = {r['SIGNOR_ID']: r for r in records}
    assert len(by_id) == len(records), 'duplicate source IDs require explicit resolution'
    kept = []
    for sid, a, b, pmid, context in SELECTED:
        r = by_id[sid]
        assert (r['ENTITYA'], r['ENTITYB'], r['PMID'], r['TAX_ID']) == (a, b, pmid, '9606')
        kept.append(dict(source_id=sid, upstream=a, downstream=b, pmid=pmid,
                         mechanism=r['MECHANISM'], context_review=context,
                         decision='ALLOW_GENERIC_TOPOLOGY_ONLY', license='CC-BY-4.0'))
    # Freeze the selection decision before writing approved inputs.
    tsv(REPORT / 'EDGE_CONTEXT_REVIEW.tsv', kept)
    dump(REPORT / 'SELECTION_PLAN.json', {'selected_ids':[r[0] for r in SELECTED],
         'original_rows':len(records), 'unselected_rows':len(records)-len(SELECTED),
         'unselected_disposition':'NOT_USED_NOT_ASSERTED_FORBIDDEN',
         'rule':'only these individually reviewed generic non-target relationships; no full-network training'})
    mapping = []
    for human, mouse in [('PDGFB','Pdgfb'), ('PDGFRB','Pdgfrb'), ('SRC','Src'), ('STAT1','Stat1'), ('S100A10','S100a10')]:
        p = RAW / ('orthology_'+human+'.json')
        data = json.loads(p.read_text())['data']
        matches = [h for d in data for h in d['homologies'] if h['type']=='ortholog_one2one' and h['target']['species']=='mus_musculus']
        assert len(matches) == 1, 'ambiguous orthology: '+human
        h = matches[0]
        mapping.append(dict(human=human, mouse=mouse, human_id=h['source']['id'], mouse_id=h['target']['id'],
                            relation='ortholog_one2one', evidence=str(p.relative_to(ROOT)), sha256=sha(p)))
    tsv(REPORT / 'ORTHOLOGY.tsv', mapping)
    panel = json.loads((ROOT/'reports/t3_data_intake_20260920/panel_genes.json').read_text())
    assert all(g in panel for g in ['Pdgfb','Pdgfrb','S100a10'])
    # Src/Stat1 are mechanistic intermediates, not required measured output genes.
    OUT.mkdir(parents=True)
    refs = ';'.join('https://pubmed.ncbi.nlm.nih.gov/'+r[3]+'/' for r in SELECTED)
    tsv(OUT/'edges.tsv', [dict(ligand='Pdgfb', receptor='Pdgfrb', target='S100a10',
        source_reference=refs, license='CC-BY-4.0', target_phenocopy_free='true',
        chain='Pdgfb>Pdgfrb>Src>Stat1>S100a10', evidence_level='CROSS_CONTEXT_CURATED_TOPOLOGY_HYPOTHESIS')])
    # Minimal licensed relationship metadata only, with all source prose omitted.
    tsv(OUT/'source_edges.tsv', [{k:r[k] for k in ['source_id','upstream','downstream','pmid','mechanism','license']} for r in kept])
    (OUT/'ATTRIBUTION.md').write_text('''# Attribution and scope

SIGNOR 4.0, https://signor.uniroma2.it/, data license CC-BY-4.0:
https://signor.uniroma2.it/documentation/ and https://creativecommons.org/licenses/by/4.0/.
Retrieved 2026-09-20. Changes: selected four relationships, omitted source prose,
direction/strength/scores, mapped human genes to mouse one-to-one orthologues,
and collapsed one multi-step chain into ligand/receptor/target form.
Primary publications are cited per edge. Article copyrights are unchanged;
no article text, figures, numerical expression measurements or response vectors
are redistributed here. The derived relationship records retain CC-BY-4.0.

These edges describe different experimental contexts and do not establish that
PDGF induces S100a10 in the embryo. Coefficients must be learned from permitted
WT data only; the topology is an exploratory prior, not causal validation.
''')
    filter_receipt = dict(task='T3:gata4', status='PASS_SELECTED_TOPOLOGY_REVIEW',
        forbidden_records_remaining=0, scope='only four selected source edges and one collapsed topology row',
        original_sha256=sha(source), selected_ids=[r[0] for r in SELECTED],
        context_review=dict(path=str((REPORT/'EDGE_CONTEXT_REVIEW.tsv').relative_to(ROOT)), sha256=sha(REPORT/'EDGE_CONTEXT_REVIEW.tsv')),
        no_protected_target_genotype_or_stage_evidence=True,
        no_external_measured_response_values=True, no_pretrained_parameters=True,
        external_source_signs_and_weights='NOT_USED', complete_chain_experiment='NOT_ESTABLISHED',
        organizer_clearance='NOT_REQUIRED_FOR_THIS_GENERIC_NON_TARGET_TOPOLOGY_SCOPE',
        rationale='Local rules allow generic pathway knowledge; no Gata4/Gata6/Ctnnb1-specific edge or external expression training source is admitted')
    dump(REPORT/'FILTER_RECEIPT.json', filter_receipt)
    manifest = dict(task='T3:gata4', status='APPROVED_SANITIZED', forbidden_records_remaining=0,
        model_input=True, allowed_role='GENERIC_TOPOLOGY_ONLY_WT_FITTED_COEFFICIENTS',
        source_reference='https://signor.uniroma2.it/API/getHumanData.php', license='CC-BY-4.0',
        filter_receipt=dict(path=str((REPORT/'FILTER_RECEIPT.json').relative_to(ROOT)), sha256=sha(REPORT/'FILTER_RECEIPT.json')),
        files={'edges':dict(path=str((OUT/'edges.tsv').relative_to(ROOT)), sha256=sha(OUT/'edges.tsv'))},
        scientific_status='EXPLORATORY_CROSS_CONTEXT_PRIOR', r6_permission=False)
    dump(REPORT/'SOURCE_MANIFEST.json', manifest)
    print(json.dumps({'status':'R5_MINIMAL_SOURCE_READY','complete_topology_rows':1,'reviewed_source_edges':4,'model_scope':manifest['allowed_role']}))


if __name__ == '__main__':
    main()
