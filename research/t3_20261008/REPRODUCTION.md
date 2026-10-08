# Reproduction and limits

Python 3.12.14 and the recorded numerical dependency versions are in requirements.txt and snapshots/v0087/VERSIONS.json. Exact numerical replay may depend on BLAS/platform; CPU runs use two threads. No installation or training is performed by the tests below.

From this directory:

    python portable/test_lightweight.py
    python portable/replay.py --version v0087 --assets /path/to/trusted/v87/inference
    python portable/replay.py --version v0088 --assets /path/to/trusted/v88/inference

The first command needs no data or model. It verifies all included snapshot hashes and runs three synthetic suites plus v88 four-arm null/determinism/closure/own-gene controls in temporary copies. Both replay commands were tested against existing local caches on 2026-10-08 and exactly matched expression and donor indices. They are read-only and do not write predictions. Each asset directory must contain state_emitter.joblib, generic_response.npz, WT_carrier7449.h5ad and expected_donor_rows.npy. Expected SHA256 values are in the versioned inference/MANIFEST.json. All four are verified before unpickling. Only use trusted project assets; joblib is executable pickle format. No source KO or hidden target KO is needed at inference.

## What a fresh public clone cannot do

See PUBLIC_REBUILD_FOLLOWUP.md for verified public annotation reconstruction and dry-run-verified frozen fitting adapters. Full fitting and end-to-end GO rebuilding remain unverified.

The trained model, frozen response, untreated carrier and donor arrays are intentionally not published. No public download URL for those four exact fitted artifacts is established. Therefore this clone alone cannot reproduce exact v87/v88 predictions. The supported executable path is explicit user-provided hash-matching cached artifacts. No private Library link is offered as a public dependency. No expensive retraining or parameter export was performed for this release.

Public raw source manifests make the scientific source recoverable, but do not make a turnkey fresh retraining pipeline: the original publisher annotation extraction code is absent, but a verified replacement now reproduces all selected TSV hashes (see PUBLIC_REBUILD_FOLLOWUP.md); selected annotation TSVs are excluded as data; raw preprocessing scripts have recorded absolute paths; exact challenge WT/released-Mab data requires normal authorized access. Historical adult-Mab comparison arrays are also omitted. The recorded source reconstruction checks establish what was previously rebuilt, not a claim that this publication reran the full rebuild.

## Source reconstruction instructions

1. Inspect the allowlists/reviews in snapshots/v0087/external_sources. Preview public GEO acquisitions with:

       python snapshots/v0087/fetch_public_sources.py --destination /your/scratch/root

   Add --download only to acquire the reviewed hash-bound files. This helper handles GEO files only; use the explicit publisher workbook URLs from TASK_DATA_PERMIT.json separately and verify hashes. Selected annotation sheets are WT85_cells, Dnmt3a_cells, Kmt2a_cells, Kdm2b_cells, Dnmt1_cells, Dnmt3b_cells, G9a_cells and Kmt2b_cells. portable/rebuild_annotations.py now independently reproduces all exact annotation manifest hashes from those public supplements; see PUBLIC_REBUILD_FOLLOWUP.md. Do not train from unfiltered full workbooks.
2. Obtain E8.75 WT, E9.5 WT and released E9.5 Mab21l2 KO through the official challenge data page linked in OFFICIAL_RELEASED_INPUTS.json, verifying its hashes. Do not obtain protected Gata4/Ctnnb1 outcomes. All seven sources are E8.5 unrelated single KOs; a/b are technical partitions, not embryo replicates.
3. Historical preprocess_source.py → preprocess_wt_idmatch.py → preprocess_expanded.py → check_features.py build raw panel inputs; normalize_source_panels.py makes filtered log1p panel-total-10000 matrices. Only run adapted copies in a fresh scratch tree and record all path-only changes. Source WT barcode/embryo joins must preserve the known 690 missing WT exclusions. Nine raw-panel identity checks and eight normalized-panel hashes are retained in SOURCE_REBUILD_CHECKS.json.
4. Original frozen run_crossko7_hurdle_v2.py and deployment/export scripts explain the fitted prior; evaluate_source.py documents v88's frozen four-arm decision. These historical commands are evidence, not advertised location-independent entrypoints. Reconstruct missing metadata and explicitly bind input/output roots before any separately authorized full rerun.

For v0083–85, snapshots/v0083_v0085/code/reproduce.py accepts --repo, --wt, --source, --go and a fresh --out directory. It requires base commit eb464afa7ee53d5bed7078d65bfed4f03df675b2 and its original source-filter plans/dependencies. Source reconstruction scripts and GEO/GO manifests are retained. Historical original H5AD byte identity was not established; reconstructed array hashes are exact, new serialized H5AD bytes differ. This publication did not rerun the training-based v83–85 reproduction; its prior replay evidence is archived.
