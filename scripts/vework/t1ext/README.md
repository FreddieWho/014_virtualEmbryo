# T1 late-anchor route (2026-10-08)
1. `ext_prep.py`: GSE230531 allowed per-sample matrices → cell calling → log1p CP10k → T1 panel (`ext/proc/*.h5ad`, `QC.json`).
2. `label_means.py`: logistic-regression label transfer (competition coarse groups; 400 markers; held-out accuracy 0.92) → per (dataset, stage, group) mean/detection (`ext/proc/groups.npz`).
3. `anchor.py`: per-group external within-batch delta (E14.5−E8.5) with n-shrinkage and masks (ambient CM RNA in non-CM groups, Hb, IEG, Malat1, mt-). Log-time warp (supported by E16.5: CM_V slope 0.245 vs 0.242 predicted). Zero-preserving shift. Composition weights.
4. `bt_anchor.py`: E8.5→E9.5 backtest on released data only (`backtests/t1_anchor_e85_e95*.json`). Read relative to copy and a gene-permuted null: the local copy has a shared-reference artefact (dir ≈ 0.2).
5. `build_t1_late_anchor.py --name … --amp … --comp …`: builds the submission.
   - For the TEST phase (E12.5): `--carrier <E10.5 truth file> --t0 10.5 --t1 12.5` (warp 0.327).
   - The E14.5 anchor is then only 2 days past the target.
   - Before reuse, re-run `label_means.py` with E10.5 truth included in the comp labels.
