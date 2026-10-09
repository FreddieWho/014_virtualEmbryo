# Exact v0101 replay

Run from repository root with an empty output directory and verified input hashes in component_assay_v0101.json. The selected configuration distinguishes order prespecification from post-result component selection.

```bash
flock /workspace/shared/virtualembryo-20261009/.heavy_compute.lock \
/workspace/shared/virtualembryo-20261009/venv/bin/python \
scripts/t1_quota_20261009/compose_component_assay.py \
--v94 /workspace/scratch/7ec7e25db3f4/t1_v0094_delivery/t1_val__joint_carrier__v0094.h5ad \
--v98 submissions/candidates/T1_val/v0098_assayscale_cp10k/submission.h5ad \
--raw-v98 submissions/candidates/T1_val/v0098_assayscale_cp10k/preclosure.h5ad \
--component submissions/candidates/T1_val/v0099_detonly_cp10k/submission.h5ad \
--raw-component submissions/candidates/T1_val/v0099_detonly_cp10k/preclosure.h5ad \
--carrier /workspace/scratch/7ec7e25db3f4/t1_recovery_library/T1_v0051_carrier_recovered_20261009.npz \
--slopes submissions/candidates/T1_val/v0098_assayscale_cp10k/TARGET_SLOPES.npz \
--config configs/t1_quota_20261009/component_assay_v0101.json \
--outdir artifacts/t1_quota_20261009/v0101_replay
```

Expected dense float32 expression SHA256:07bf73d4b307e792cf53c1763f533e34c8a242717e8bab4836b77c6e4bff3aee.

Use validate_candidate.py against exact v0098 SHA7e7669328ecf951ddf2ed8a0f6a85979c1b7e2bf926eff352cfe6f9074e53567 and the same restored board scorer lock. Full source controls use diagnose_candidate_set.py with composition_diagnostic_arms.json and the complete official E9.5 RNA input.
