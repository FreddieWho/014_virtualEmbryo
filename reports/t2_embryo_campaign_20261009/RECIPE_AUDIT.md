# Carrier recipe identity audit (2026-10-09)

Base revision: 29a8e1976665a66a7378892857c815f589720971. No protected target expression/labels read. Official public index and 498-gene panel freshly downloaded and SHA-matched historical source manifest.

## E3 is not an exact v0014 replay

- Original `scripts/t2_round2/run.py:InterpCtx.mean_shift_matrix` uses t = (mu_target - mu_baseline_parent)/SE to shrink the bridge correction.
- `scripts/vework/t2_recipes.py:run_interp` uses t = (mu_right - mu_left)/SE, including for its baseline carrier.
- Original original statistics use float64; vework stage matrices and stage-stat reductions use float32 before conversion.
- Original reads immutable parent h5ads, reuses original row names and full metadata; E3 rebuilds parents and changes names to source__rN.
- E1 versus E3 additionally changes base-pool restriction, selection seeds, orphan mass handling, and geometry RMS pool. It is not an expression-only ablation.

Therefore comparison with historical v0014 server score is observational unless the exact original parent is recovered and transformations freeze its relevant arrays. Never call E3 byte-faithful or treat its score difference as single-cause evidence.

## Prospective mechanism controls

1. For an exact scored parent, geometry-only intervention freezes X and labels/names exactly. Expression metric invariance is a control; geometry and neighborhood can change.
2. For reconstructed carrier, match rows, shares, seed and coordinates before comparing expression with/without baseline pseudobulk residual. Orphan states preserve baseline in both arms.
3. State-conditioned spatial interpolation needs explicit frame alignment before comparing anatomical centroids; each released embryo has its own arbitrary rigid frame.

Current blocker: official released E6.75/E7.25/E8.0 files absent from this executor; portal worker is restoring authentication with the user. No training or local stage metrics have run. Scientific uncertainty does not veto a compliant server experiment.

## Recovery resolution

The original scored E3 was reproduced byte-for-byte on official source data: SHA256 e93d56f2130297f7c5b256e3e26fc072b8913766772b3ffcb2634f7a3fdbfdae matches the historical reports/t1_late_anchor_20261008/MANIFEST.tsv. This resolves exact-parent attribution for E3-derived geometry candidates, but E3 remains distinct from the original v0014. Script reproduce_e3.py asserts the expected digest.

All three released source h5ads have now been restored through the authenticated official download flow and match the source index hashes. Released-stage holdout results are in holdout_geometry.json. No E7.5/E7.75 data were read.
