"""Metadata review and immediate quarantine filtering; never train or normalize."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/t3_r56_readiness_20260920'
SOURCE = ROOT / 'infra/external_data/quarantine/T3-NEXT-R56-20260920/filtered/GSE261783_OP2_resting_provisional_raw.h5ad'
OUTPUT = ROOT / 'infra/external_data/quarantine/T3-R56-READINESS-20260920/GSE261783_OP2_resting_review2_raw.h5ad'
EXCLUDE = {
    'Chd4': ('https://pmc.ncbi.nlm.nih.gov/articles/PMC9067406/', 'Direct GATA4/NKX2-5/TBX5 cardiac developmental complex; conservative risk exclusion, not a proven identical phenocopy'),
    'Smarca4': ('https://pmc.ncbi.nlm.nih.gov/articles/PMC3096875/', 'BRG1 dosage modulates cardiac developmental transcription factors; conservative risk exclusion'),
    'Yy1': ('https://pmc.ncbi.nlm.nih.gov/articles/PMC6048588/', 'Cardiac progenitor regulation and developmental conditional loss; conservative risk exclusion'),
}


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def tsv(path, rows, fields):
    with path.open('w') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main():
    import anndata as ad
    if OUTPUT.exists() or (REPORT / 'PREPARATION_RECEIPT.json').exists():
        raise SystemExit('Refusing to overwrite a prior run')
    REPORT.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    original = json.loads((ROOT / 'reports/t3_data_intake_20260920/FIBRO_FILTER_RECEIPT.json').read_text())
    assert sha(SOURCE) == original['sha256']
    a = ad.read_h5ad(SOURCE, backed='r')
    obs = a.obs.copy()
    counts = obs.condition.value_counts()
    review = []
    for gene, n in sorted(counts.items()):
        if gene == 'ctrl':
            status, ref, why = 'CONTROL_METADATA_ONLY', 'GSE261783', 'Explicit NTC assignment; not a perturbation'
        elif gene in EXCLUDE:
            ref, why = EXCLUDE[gene]
            status = 'EXCLUDE_CONSERVATIVE_CONTEXT_RISK'
        else:
            status, ref, why = 'HOLD_FULL_CONTEXT_REVIEW', 'GSE261783', 'Exact blacklist screen alone cannot establish absence of protected phenocopy'
        review.append(dict(gene=gene, cells=int(n), decision=status, source_reference=ref, reason=why, model_input='false'))
    tsv(REPORT / 'R6_CONDITION_REVIEW.tsv', review, list(review[0]))
    keep = ~obs.condition.isin(EXCLUDE)
    plan = [dict(cell=cell, condition=row.condition, sample=row['sample'], decision='KEEP_QUARANTINE' if keep.loc[cell] else 'REMOVE_CONTEXT_RISK') for cell, row in obs.iterrows()]
    tsv(REPORT / 'R6_CELL_FILTER_PLAN.tsv', plan, list(plan[0]))
    panel = json.loads((ROOT / 'reports/t3_data_intake_20260920/panel_genes.json').read_text())
    mapping = []
    for gene in panel:
        matches = a.var.index[a.var.gene_symbol == gene].tolist()
        assert len(matches) == 1, (gene, matches)
        mapping.append(dict(panel_symbol=gene, ensembl_id=matches[0]))
    tsv(REPORT / 'R6_PANEL_MAPPING.tsv', mapping, list(mapping[0]))
    # Only after the removal plan is durable, read the selected raw-count rows.
    filtered = a[keep.to_numpy(), :].to_memory()
    a.file.close()
    filtered.uns['readiness_review'] = 'SECOND_PASS_QUARANTINE_NOT_APPROVED'
    filtered.write_h5ad(OUTPUT, compression='gzip')
    check = ad.read_h5ad(OUTPUT, backed='r')
    assert not check.obs.condition.isin(EXCLUDE).any()
    assert check.n_obs == int(keep.sum()) and check.n_vars == 32287
    shape = list(check.shape)
    check.file.close()
    receipt = dict(status='PREPARATION_PARTIAL_QUARANTINE', task='T3:gata4', model_input=False,
        source=dict(path=str(SOURCE.relative_to(ROOT)), sha256=sha(SOURCE)),
        output=dict(path=str(OUTPUT.relative_to(ROOT)), sha256=sha(OUTPUT), shape=shape),
        removed_conditions=list(EXCLUDE), removed_cells=int((~keep).sum()),
        remaining_perturbations=int(len(counts)-1-len(EXCLUDE)), controls=int(counts['ctrl']),
        panel_unique_matches=len(mapping), full_phenocopy_review='PENDING', organizer_clearance='NOT_PRESENT',
        normalization='NOT_RUN', embedding='NOT_RUN', adjacency='NOT_RUN', training='NOT_RUN',
        r5_approved_complete_edges=0, blocks_submission=False,
        script_sha256=sha(Path(__file__)),
        review_sha256=sha(REPORT / 'R6_CONDITION_REVIEW.tsv'), plan_sha256=sha(REPORT / 'R6_CELL_FILTER_PLAN.tsv'))
    (REPORT / 'PREPARATION_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
