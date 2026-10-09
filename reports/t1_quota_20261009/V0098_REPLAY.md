# Frozen v0098 replay

Run from the repository root with the pinned environment. Use an empty output directory. The exclusive shared memory lock is mandatory for the build/refit. Replace paths only with byte-verified copies of the receipts in AFFINE_INPUT_IDENTITY.json and V0098_BUILD.json.

```bash
flock /workspace/shared/virtualembryo-20261009/.heavy_compute.lock \
/workspace/shared/virtualembryo-20261009/venv/bin/python \
scripts/t1_quota_20261009/build_assay_displacement.py \
--v94 /workspace/scratch/7ec7e25db3f4/t1_v0094_delivery/t1_val__joint_carrier__v0094.h5ad \
--v96 submissions/candidates/T1_val/v0096_cp10k/r2/submission.h5ad \
--carrier /workspace/scratch/7ec7e25db3f4/t1_recovery_library/T1_v0051_carrier_recovered_20261009.npz \
--stats artifacts/t1_quota_20261009/source_support/REPLICATE_STATS_UNICODE.npz \
--model artifacts/t1_quota_20261009/affine_assay/FITTED_E85_ONLY.npz \
--assay-result artifacts/t1_quota_20261009/affine_assay/RESULT.json \
--config configs/t1_quota_20261009/assay_displacement_v0098.json \
--outdir artifacts/t1_quota_20261009/v0098_replay
```

Expected dense float32 expression SHA256: e93f9feb4b9e4c9e32f8cc56b9a2f583cf308938b2fe08076375a64f98a3e83f. Metadata/file serialization may depend on runtime, so compare the immutable submission file SHA separately.

The source slope/classifier fit can be replayed with test_affine_assay.py using official E8.5/E9.5 inputs, `--external-root artifacts/t1_quota_20261009/inputs/external_processed`, `--external95 artifacts/t1_quota_20261009/inputs/e95_assay/audit/GSM5820434_panel_log1p.h5ad`, `--config configs/t1_quota_20261009/affine_assay.json`, and a fresh `--out`. E9.5 expression/labels are used only after the E8.5 fit for the diagnostic; its measured-panel availability metadata is used earlier.
