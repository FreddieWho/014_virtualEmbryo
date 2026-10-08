# T2 heart extrapolation, 2026-10-08

v0036 endpoint-rank candidate finished at **50.47, REJECT**. Retain v0030 (51.12); v0032 remains numerical high (51.14), within the incumbent tie band. The authoritative score entry is [SERVER_SCORE_REGISTRY](../../reports/SERVER_SCORE_REGISTRY.md#t2-heart-extrap-endpoint-rank-v0036-score-return-20261008); this package does not create a second score registry.

The legacy v0030 binary/emitter was unavailable. The median09-library baseline is reconstructed, not a byte-exact or independently revalidated legacy v0030. All comparisons and transfer conclusions must retain that caveat.

## Distribution and installation

No H5AD, model pickle, cache or archive binaries are included. Python 3.12 with `pip install -r requirements.txt` supplies the recorded dependencies. Frozen scripts are exact historical source bytes, including obsolete workspace paths. Do not edit them and continue citing their original hashes. `portable.py`, `extract_endpoint.py`, and `run_historical.py` are separately identified publication adapters. Commands can run from any current directory; pass absolute paths to external inputs and outputs.

Input identities and acquisition methods: [PUBLIC_INPUTS.json](../../infra/bioinf-data-index/t2_heart_extra_20261008/PUBLIC_INPUTS.json). Use the official challenge data page's Download controls for T2/E8.75.h5ad and T2/E9.5.h5ad. An eligible authenticated challenge account may be required. These are not asserted to have public unauthenticated direct URLs. Development additionally requires E8.25_late.h5ad. No private storage link is needed or presented as public.

Download the original E14.5 file from the stable public URL in that manifest, verify its exact SHA256 and byte size, then recreate the small endpoint:

    python /PATH/TO/REPO/scripts/t2_heart_extra_20261008/extract_endpoint.py --source /DATA/E14.5_E1S3.MOSTA.h5ad --out /OUTPUT/endpoint_rebuild

This emits `e145_endpoint/E14.5_cm_enriched_panel_raw.h5ad` and a fresh permit binding its actual hash. Original historical endpoint hashes remain unchanged in the repository permit. The exact count/gene/marker selection is unchanged; original normalized X, regulons, clusters, embeddings, trajectories, coordinates and original uns are not copied. H5AD serialization can vary by installed version.

Rebuild the selected model and run inference without omitted weights:

    python /PATH/TO/REPO/scripts/t2_heart_extra_20261008/portable.py --inputs /DATA/OFFICIAL_T2 --endpoint /OUTPUT/endpoint_rebuild/e145_endpoint/E14.5_cm_enriched_panel_raw.h5ad --out /OUTPUT/rebuilt.h5ad

This bounded reproducibility refit rebuilds source medians and deterministic PCA/k-means endpoint microstates, not a new model-selection experiment. For an existing trusted frozen model, add `--model /DATA/endpoint_model.pkl`; its recorded hash is required before deserialization. Optional `--compare /DATA/original_submission.h5ad` verifies the original candidate hash, exact row IDs/genes/geometry and X within 2e-6. The candidate is comparison-only, never predictor input. Without that optional original binary, reconstruction is possible but independent exact-output comparison is unavailable. No byte-identical H5AD claim is made.

    python /PATH/TO/REPO/scripts/t2_heart_extra_20261008/test_portable.py

## Historical controls and scorer

Frozen microstate PCA/GO flows, signed graph-EB and permuted graph, Hermite endpoint/endfree/permuted endpoint, matched-drift/permuted endpoint, copy and reconstructed median baseline are all included. `run_historical.py` accepts `--inputs`, `--work`, `--module`, `--action`, optional `--endpoint`/`--partition` and `--repo`. It changes path literals in memory only. Build order for a historical development reproduction is flow, graph_velocity, endpoint_flow, endpoint_residual (action dev); then evaluate action split; then evaluate each lane. This is expensive and is not part of bounded package tests. Freeze choices before reserve evaluation; do not reinterpret retrospective selection as preregistration.

The evaluator uses the repository's `third_party/veckit/score_h5ad.py` and `scripts/t2_pseudo_holdout.py`; compare scorer SHA with the frozen SCORER_LOCK before rerunning. All 42 executed score-run JSONs and partition/seed manifests are preserved in [reports](../../reports/t2_heart_extra_20261008/evaluation). Their recorded absolute paths are historical provenance, not portable entrypoints. No new scoring was performed for publication.

## Cell-level payload exclusion

The public release omits dev/reserve cell IDs, endpoint selected-row ledgers and any final source-row ledger. Original hashes are listed in `reports/t2_heart_extra_20261008/EXCLUDED_CELL_TABLES.json`. These are data payloads, not required inputs to the selected v0036 portable refit/replay. The endpoint extractor derives selected rows from the hash-verified raw E14.5 source. The historical evaluation launcher deterministically regenerates dev/reserve IDs from the official stage inputs; reproducing individual historical score runs additionally requires those authorized inputs and the recorded environment. Aggregate 42-run results remain included.
