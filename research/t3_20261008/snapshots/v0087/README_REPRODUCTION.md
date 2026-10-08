# v0087 scored reproducibility packet

Actual T3 score53.42, promoted overv0084=49.55 (+3.87). Exact candidate and official receipt: v0087/. One source-trained generic model, no hidden target outcomes. Both newly authorized submissions have been spent. Do not upload diagnostic, old, or alternative files.

## 1. Portable exact inference, no downloads or KO data

Use Python3.12 and versions recorded in VERSIONS.json: numpy2.3.5, pandas2.2.3, scipy1.18.1, scikit-learn1.8.0, anndata0.11.4, plus joblib/h5py/threadpoolctl. Installing these dependencies is separate from running this packet; use a trusted package registry and your normal environment policy.

From the extracted packet root:

    python inference/replay.py

This loads only the hash-verified33KB state model,630KB frozen response,1.9MB WT carrier, and own emitter code. It does not load sourceKO matrices or a hidden target. It reproduces expression bit-for-bit with arraySHA256:

    2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98

Donor resampling indices also match exactly. The candidate H5AD itself is already in v0087/. Inference checks expression-array identity, not binary identity of a newly written HDF5 container across library/platform versions. Joblib is a pickle-format artifact: load only the hash-verified model from this trusted packet.

## 2. What is included

- One actual submitted v0087H5AD, its single-member uploadZIP, final contract, hashes and terminal portal receipt
- Lightweight inference model, WT-only7449-cell carrier, response, donor indices and replay test
- Complete new training/emitter/preprocessing/calibration/test code and frozen protocols; package versions
- Source reviews, task-scoped permits, accession URLs and checksums, selected original barcode/embryo TSV annotations and feature mapping
- Frozen ontology-only embeddings for historical3KO and expanded7KO comparisons (the final mean response does not depend on GO identity)
- Actual3KO,7KO, decoder-repair and released-Mab raw metrics, selection receipts, negative results, exact donor provenance and independent audit
- Frozen historical adultMab prediction and selected-parentv0084 artifact as reproducibility references, not upload candidates

Not included: ~4.3GB raw public count downloads, official fullWT/Mab input matrices, interim/VOID H5AD candidates, or the restrictive alternative Gata file. No secret credentials or account tokens are required by the replay.

## 3. Fetch and verify training inputs

The source permit JSON files in external_sources/ bind each allowedGEO matrix/archive to its URL, byte count andSHA256. Preview:

    python fetch_public_sources.py --destination /workspace/shared

To intentionally acquire those already reviewed public files, add --download. The helper will not silently reuse a hash-mismatched existing file and never fetches hidden challenge outcomes. Expect ~4.3GB compressed counts plus preprocessing working space.

Selected annotation TSVs in external_sources/annotations/ are already provided; copy them to /workspace/shared/t3_developmental_sources/annotations/. Copy source review/permit JSON files to that source folder, and the provided GSE137337_features.gz to /workspace/shared/t3_developmental_sources/. Copy ontology subfolders to /workspace/shared/t3_observation_reset/{go_expanded,go_expanded7}/.

Official released challenge inputs must be obtained through the normal authorized Download controls at https://virtualembryo.ai/challenge/data#download. Only E8.75WT, E9.5WT and releasedE9.5MabKO are needed. Filenames and hashes are in external_sources/OFFICIAL_RELEASED_INPUTS.json. Put them under /workspace/shared/virtual_embryo_data/. No Gata4/Ctnnb1 heldout measurements are needed or permitted.

## 4. Rebuild training and evaluation

The research scripts preserve their recorded absolute execution roots for auditability. A Linux environment can stage this extracted root at /workspace/shared/t3_state_response_20261008 and source inputs at the paths above. If another prefix is required, alter only these path constants and record that code-path change; model parameters/seeds remain frozen. The portable inference replay above does not require this staging.

Place the bundled public_core/common/ at /workspace/shared/t3repo/third_party/veckit/common/. The original run used CPU-only,2BLAS threads and<10GB RAM. First run:

    python preprocess_source.py
    python preprocess_wt_idmatch.py
    python preprocess_expanded.py
    python check_features.py
    python test_crossko.py
    python test_crossko_hurdle_v2.py
    python run_crossko7_hurdle_v2.py

WT_IDMATCH corrects legacy gene symbols by stableEnsembl identifiers; don't substitute the earlier symbol-onlyWT panel. Feature-map checks must show500unique panel positions with no duplicates. Real-cell/embryo joins must match the saved MERGE_RECEIPT, including690 missingWT barcode rows. The fullgenotype is excluded from fitting before evaluation. Same-sex WT controls are equal-weighted by biological embryo; never treat librarya/b as independent embryos.

For the original unconditional7KO comparator run run_crossko7.py. The3KO adaptive precursor is run_crossko.py with its own older ontology basis. The invalid hurdle-v1 is retained only as code/metric audit evidence; do not promote its output. Historical adultMab array is in reference/; place it at /workspace/shared/t3new_20261008/mab_anchored_v2.npy if rerunning those comparisons.

To replay the exact target/heldout-platform construction after training, run deploy_diagnostics.py, replay_deployment_provenance.py and calibrate_mab.py. These generate predictions before loadingMab truth and must not tune after seeing the outcome. Existing finalized files are immutable: run in a fresh output copy rather than overwriting this scored packet. finalize_v87.py is an archived packaging recipe requiring the recorded parent/scorer lock; it deliberately refuses an existingv0087 directory. Portable inference does not need that historical contract machinery.

## 5. Interpretation and next step

See FINAL_REPORT.md. New sourceLOKO direction~.574 and localMab weighted calibration57.25 supported the experiment, but those were not Gata forecasts. ActualGata53.42 gained mainlyseverity whileDE and distributionstructure worsened. Distance-OOD rows28.33% were included; no calibrated uncertainty claim. Gata4/Gata6 RNA was not mechanically zeroed orhalved. The result is a competition improvement, not identifiedGata4 biology. Further work requires a new task/authorization; no additional uploads are scheduled.
