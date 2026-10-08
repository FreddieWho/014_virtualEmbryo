# T3 reproduced submissions · 8 October 2026

This package contains the exact uploaded H5AD files for original IDs v0083–v0085, a portable CPU reproduction script, source/version receipts and focused tests. No raw training matrices, credentials or paid-compute dependencies are bundled.

## Results

- v0083 psb: **47.51**
- v0084 quantile transfer: **49.55**, a new T3 best, **+1.60** over the previous numerical best47.95
- v0085 donor-sign gate: **47.45**
- GitHub登记：**尚未完成，等待确认**。已确认的官网成绩、提交ID和待登记哈希见 REGISTRATION_PENDING.json；本包不声称远端登记已完成。

The separate new signed-rank learning experiment was negative and was not submitted. v0084's improvement comes from reproducing an existing completed route, not from that failed research experiment. Full metrics and uncertainty are in reports/.

v0084 improved DE recovery and distribution terms; its direction score was48.4. The overall gain does not establish a causal biological mechanism.

## Restore repository artifact paths

The ZIP contains artifacts/reproductions/20261008/v0083/submission.h5ad and the corresponding v0084/v0085 paths. After checking SHA256SUMS.txt, copying or extracting the artifacts/ tree into the project root restores the exact paths referenced by the repository INDEX. It does not replace source data or tracked code.

## Artifact identity

MANIFEST.json records the uploaded SHA256 and expression-array SHA256 for each original candidate ID. Historical unsubmitted files were absent; these are faithful frozen-recipe reconstructions, with historical hash recorded separately. No claim of byte identity to absent historical artifacts is made. Portable replay below checks exact equality to the **current submitted expression arrays**, independently of serialization metadata.

Keep artifacts/ files unchanged. They retain their immutable embedded cloud-compute provenance; external text manifests are sanitized. The initial temporary86–88 IDs are not part of this delivery.

## Reproduce the submitted arrays

Use Python3.12 and the project repository at base commit:

    eb464afa7ee53d5bed7078d65bfed4f03df675b2

From this package directory:

    python -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python code/reproduce.py --repo /path/to/project --wt /path/to/E8.75.h5ad --source /path/to/expression.h5ad --go /path/to/GO_EMBEDDING.npz --out ./replayed
    .venv/bin/python -m pytest -q tests

Use a new output directory. Reproduction is CPU-only, two BLAS threads, and verifies all three output expression hashes. It never reads hidden target outcomes or adjusts parameters to leaderboard scores. H5AD file hashes from replay differ because portable metadata differs from the exact submitted metadata; the immutable submitted files are bundled under artifacts/reproductions/20261008/.

### Inputs, intentionally not bundled

1. Official E8.75 WT MERFISH (24,826×500), available through the challenge's authenticated official data page. SHA256149ab6df7c99ad85046c8aebebcf0c43689b3720c59ffb7cc550edcf2f13a83c
2. Approved GSE261783 GSM8151756/GSM8151757 OP2 resting adult cardiac-fibroblast subset, original frozen barcode/condition allowlist, 5,454×500 including220 controls. Use the supplied source receipts and the project's source-review/permit. Do not replace it with unreviewed full-series data. The portable code verifies normalized expression bytes.
3. Frozen GO embedding, SHA256acdb554d47989a4d8230fb8acc0fc7d20ec40e12086b56ef1715afb8fee11e0d

If rebuilding these derived inputs, exact original public URLs and SHA locks are in sources/. Place the two original verified H5 matrices under SOURCE_DIR/raw, then run code/reconstruct.py --repo REPO --out SOURCE_DIR. Place the three exact GO files under SOURCE_DIR/GO, then run code/reconstruct_go.py --repo REPO --out SOURCE_DIR. Both scripts reuse the original project's reviewed filtering/ontology recipe. Access restrictions and current source-use permissions still apply. No network downloading is performed by these scripts.

## Research and code checks

reports/ includes WT-hurdle replay, released Mab21l2-only diagnostic, 546 matched-input signed-rank comparisons, paired perturbation-bootstrap intervals, and fixed donor-route checks. These are source/diagnostic results, not hidden-target measurements. Historical nine-gene holdouts had been used in prior project work and are not pristine. Two sample labels do not establish independent animals.

33 relevant project tests passed; one unrelated Torch graph test was not included because Torch was not installed. The four bundled validation regression tests exercise heldout-outcome isolation, donor exclusion and signed-program direction. A full NMF diagnostic remained blocked by an existing runtime contiguity error and is not represented as completed.

code/validation_repairs.patch contains experimental evaluator repairs only. To inspect/apply it on the base checkout, first copy code/validation.py to scripts/t3_six/validation.py, then git apply the patch. These validation fixes are **not changes to the original83–85 target delivery recipes** and are not required for replaying the submitted arrays. Do not overwrite historical evaluation reports when running a repaired evaluation harness.

## Integrity

SHA256SUMS.txt covers package contents. ZIP members were CRC-tested. See PACKAGE_CHECK.json beside the ZIP for archive checks. Full external-source disclosures are embedded in each submitted H5AD and summarized in sources/.
