# Component replay

Run from the repository root in the pinned environment, with an empty output directory. The command is identical for v0099 and v0100 except the frozen configuration and output directory. No refit is performed; the exact saved v0097 weights are hash-guarded.

```bash
flock /workspace/shared/virtualembryo-20261009/.heavy_compute.lock \
/workspace/shared/virtualembryo-20261009/venv/bin/python \
scripts/t1_quota_20261009/build_hurdle_components.py \
--v94 /workspace/scratch/7ec7e25db3f4/t1_v0094_delivery/t1_val__joint_carrier__v0094.h5ad \
--v96 submissions/candidates/T1_val/v0096_cp10k/r2/submission.h5ad \
--v97 submissions/candidates/T1_val/v0097_rephurdle_cp10k/submission.h5ad \
--raw-v97 artifacts/t1_quota_20261009/replicate_controls/unclosed/submission.h5ad \
--carrier /workspace/scratch/7ec7e25db3f4/t1_recovery_library/T1_v0051_carrier_recovered_20261009.npz \
--weights artifacts/t1_quota_20261009/replicate_controls/unclosed/WEIGHTS.npz \
--config configs/t1_quota_20261009/hurdle_component_v0099.json \
--outdir artifacts/t1_quota_20261009/v0099_replay
```

For v0100 replace both v0099 path components with v0100. Expected dense float32 expression SHA256:
- v0099: d4c9ebdc1eee8ece9c553fa47401b62634bb58f0c2213e088da0c6e733bc1d6e
- v0100: ee0bad8f8143cf18bc06628e6f5a8cdbd4245a7c3547169fe7d8fb65365ab0c9

The actual board validator command uses validate_candidate.py with the replay file, exact v0096 r2 parent/hash, artifacts/t1_quota_20261009/contract/SCORER_LOCK.json and a fresh report path. Full source metrics replay uses diagnose_candidate_set.py with hurdle_component_diagnostic_arms.json and official E9.5 RNA. The same released reference, all32,285 genes and all three frozen seeds must be retained.
