# Public rebuild wiring: verified annotation recovery, 2026-10-08

## What changed and what was actually checked

The original workbook-to-annotation extraction script was not present in the restored source trees. portable/rebuild_annotations.py is a transparent replacement, not a recovered historical script. Both original Nature supplement workbooks were obtained from their stable publisher URLs and matched their existing permit SHA256. The replacement recreated all eight selected E8.5 annotation TSVs with exact historical byte hashes, including row order, sex and embryo assignment, collection stage, published composition-adjusted stage, and G9a→Ehmt2 mapping. No additional genotype or stage is admitted. Cell-level outputs and workbooks remain outside this Git patch.

Verification/annotation_rebuild.json contains only aggregate counts and hashes. All eight annotation files matched; no approximate equivalence claim is needed. Source workbook terms and competition permission remain distinct as documented in SOURCES_AND_PERMISSIONS.md. Script dependencies add openpyxl==3.1.5 (tested) to the original numerical environment.

portable/rebuild_inputs.py makes explicit path-only copies of five frozen preprocessing/normalization scripts. All five adapters were syntax checked at arbitrary paths; check_features was actually executed on existing admitted inputs and confirmed 500 unique panel positions, no missing genes and no duplicate mappings. Multi-GB raw count preprocessing was not rerun for this patch.

portable/rebuild_model.py verifies exact normalized-panel files and arrays, ontology embedding and official E8.75 WT, then prepares the unchanged historical deployment fitting prefix. The prefix stops before any deployment/scoring loop. Dry-run verification passed on existing caches. Full fitting was NOT executed: an --execute run remains an unverified downstream step and can be computationally expensive. There is no new model search, source comparison, local evaluation, server scoring or candidate registration in this patch.

## Public supplement acquisition and filtering

Run from research/t3_20261008, using a fresh scratch directory outside the repository. The public GEO helper creates t3_developmental_sources beneath its destination.

    python snapshots/v0087/fetch_public_sources.py --destination /scratch/t3 --download
    python portable/rebuild_annotations.py --workbooks /scratch/t3/workbooks --out /scratch/t3/t3_developmental_sources/annotations --download

The annotation command downloads only missing hash-bound workbook files. Existing mismatched files fail closed. It reads ONLY WT85_cells and the seven permitted single-KO cell sheets, then joins ONLY stage 85 from the matching embryo sheets. Embryo keys must be unique and cell/embryo sex must agree. WT is assigned published stage WT 85; KOs retain the publisher's Adjusted stage. Stage adjustment is descriptive and does not expand the chronological E8.5 allowlist.

Stable source URLs:

- https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-020-2552-x/MediaObjects/41586_2020_2552_MOESM4_ESM.xlsx
  SHA256 458a376158eee437b3dabe7be8d4a2ff893859ef646c7c90bb9c7d2cef52b574
- https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-020-2552-x/MediaObjects/41586_2020_2552_MOESM5_ESM.xlsx
  SHA256 0d8638513d0bbd30750949ba6993f0d2d358dd1948145c782c792ebe16e80dbe

All GEO count/feature URLs and hashes remain in TASK_DATA_PERMIT.json and TASK_DATA_PERMIT_v2.json. The shared DNMT3A feature file and DNMT1 feature file have distinct gzip hashes; do not interchange them. Released official challenge WT matrices must be obtained through the normal authorized data page, then verified using OFFICIAL_RELEASED_INPUTS.json. Hidden target outcomes are unnecessary and prohibited.

## Frozen input preparation

For each stage below, first omit --execute to inspect the adapter plan, then run with --execute when prepared. Use the same fresh output root across successive stages. Stages refuse a second run into a directory with their own existing receipt.

    python portable/rebuild_inputs.py --source-root /scratch/t3/t3_developmental_sources --official-root /scratch/t3/official --out /scratch/t3/prepared --stage preprocess_source --execute
    python portable/rebuild_inputs.py --source-root /scratch/t3/t3_developmental_sources --official-root /scratch/t3/official --out /scratch/t3/prepared --stage preprocess_wt_idmatch --execute
    python portable/rebuild_inputs.py --source-root /scratch/t3/t3_developmental_sources --official-root /scratch/t3/official --out /scratch/t3/prepared --stage preprocess_expanded --execute
    python portable/rebuild_inputs.py --source-root /scratch/t3/t3_developmental_sources --official-root /scratch/t3/official --out /scratch/t3/prepared --stage check_features --execute
    python portable/rebuild_inputs.py --source-root /scratch/t3/t3_developmental_sources --official-root /scratch/t3/official --out /scratch/t3/prepared --stage normalize_source_panels --execute

Each receipt records original/adapted code SHA256 and every path substitution. All historical scientific parameters remain unchanged. Normalization preserves original whitelist ordering and panel-total-10000 log1p float32 expression. The expected 690 missing WT barcodes remain excluded. Existing historical artifacts are never overwritten by this workflow.

## Frozen model rebuild plan

The following default command checks inputs and the historical fit prefix without fitting:

    python portable/rebuild_model.py --normalized /scratch/t3/prepared/source_panel/normalized --go /scratch/t3/go_expanded7/GO_EXPANDED_EMBEDDING.npz --wt /scratch/t3/official/E8.75.h5ad --out /scratch/t3/rebuilt_model

Adding --execute runs the one fixed historical fit, exports the same reduced inference model attributes, constructs the official WT sample with seed 20260904, and requires the historical v87 and v88 expression hashes to match. It writes a fresh REBUILD_MANIFEST.json and local inference assets; it does not create a scored H5AD or submission. Those reserialized binary files may differ from historical packet hashes, so the original cached-asset replay's strict historical-binary checks are intentionally not relaxed. Exact expression checks in the rebuild command are the test, not a claim of identical HDF5 metadata or protected parent geometry.

Remaining limits:

- The full fit and full raw preprocessing have not been rerun for publication. Exact input/array verification and prefix compilation pass, but do not establish full model reconstruction success.
- The frozen expanded GO embedding is still a hash-bound input. Archived ontology builders and source hashes describe its construction, but the original builder also requires the older embedding, base repository parser and matching raw GO release. This patch does not deliver an independently smoke-tested end-to-end GO rebuild. Public current GO URLs are mutable; exact frozen bytes may require an upstream archive or user cache.
- Requiring exact normalized H5AD hashes also protects embryo/sex metadata; a different HDF5 serialization fails closed even if expression is numerically equal. Such failure needs a separate metadata-aware audit rather than weakening the check.
- Adult v83–85 reconstruction also needs its original filtered barcode plan. Cell-level plans are deliberately omitted from Git; this follow-up does not reconstruct that adult-source plan.
- Raw inputs, workbooks, cell-level tables, model binaries, caches and private recovery links are excluded from the patch.
