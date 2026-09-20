# T3 R5/R6 data intake

This folder collects and filters input candidates. It does not grant training permission.
Read `docs/batch2/compliance/DATA_FIREWALL_SPEC.md`, the task contracts, and current task permit first.

The 2026-09-20 run is documented in `reports/t3_data_intake_20260920/REPORT.md`.
Source URLs, errors, dates, file sizes and SHA256 are saved in the numbered fetch plans/receipts.
All acquired data live under `infra/external_data/quarantine/T3-NEXT-R56-20260920/`.

- `fetch.py`: fetch a predeclared JSON plan into quarantine, with a per-file size cap and receipt. Existing files are read from cache and hashed. Metadata stages precede matrix acquisition. Do not treat HTTP success as source approval.
- `audit_local.py`: reads only the local Dixit guide/cell/gene metadata, creates cell eligibility plans and measures literal panel overlap. It does not read expression matrices.
- `audit_fibro_metadata.py`: freezes two unstimulated OP2 samples, parses single-guide metadata, removes project blacklist and extra developmental-signalling risks. Retained rows remain provisional.
- `filter_fibro.py`: validates source hashes and selects only predeclared cell columns from the two 10x matrices. Outputs raw counts with original Ensembl IDs; no normalization or learned representation. Existing output is protected from overwrite. Its input/output receipts deliberately remain NOT_APPROVED.
- `audit_resources.py`: collects relationship schema, source references, and panel overlap; does not turn receptor-to-TF activity into a transcript target or use AI-generated reference summaries.

Use `LD_LIBRARY_PATH=/opt/anaconda3/lib OPENBLAS_NUM_THREADS=4` for the AnnData filter in this environment. Do not run the whole sequence in an existing receipt directory: metadata plans and reports are outputs. Use a separately versioned run for new inputs or policy changes.

Validation was an actual row/feature/blacklist/output structure check, recorded in FILTER_VALIDATION.json. No scientific model, clustering, pseudobulk or expression-based source selection was performed. The first symbol-indexing failure is preserved in FILTER_ATTEMPT1.json; original gene IDs resolve duplicate symbols without merging counts. Human-to-mouse orthology, full phenocopy review, final model input preparation and organizer/use-role clearance are not implied by the successful structural filter.
