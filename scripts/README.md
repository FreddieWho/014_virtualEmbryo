# T2 baseline runner

`t2_baseline.py` is the local, board-aware implementation of the two T2 reference baselines:

- `copy_last`: copy the `--base` cells and their `spatial_3D` unchanged;
- `pseudobulk_shift`: estimate a per-`celltype` expression shift from `--previous` to `--base`, then add it to the real `--base` cells.
- `pseudobulk_shift_row_norm`: the same shift with an explicit row-wise
  log1p library-size normalization to 10,000; diagnostic only.

The runner aligns inputs to the official T2 panel. It accepts the 500-gene early-embryo release and drops only genes outside the official 498-gene board. It fails closed on missing genes, negative/non-finite expression, missing/invalid `spatial_3D`, missing cell types, and an unsafe dense-memory estimate.

Examples:

```bash
env LD_LIBRARY_PATH=/opt/anaconda3/lib python3 scripts/t2_baseline.py \
  --task embryo --method pseudobulk_shift \
  --previous data/E7.25.h5ad --base data/E8.0.h5ad \
  --output outputs/t2_baseline/embryo_shift_E8.0.h5ad

env LD_LIBRARY_PATH=/opt/anaconda3/lib python3 scripts/t2_baseline.py \
  --task heart --method pseudobulk_shift \
  --previous data/E8.75.h5ad --base data/E9.5.h5ad \
  --output outputs/t2_baseline/heart_shift_E9.5.h5ad
```

The generated train-stage files are engineering/pseudo-holdout artifacts. They are not submissions and do not contain hidden validation truth.

## B1-A1 dual-lane G1 scale runner

## Submission preparation

`t2_g1_scale.py` implements the bounded B1-A1 experiment. It generates the two
fixed source-only lanes (`L1_FORMAL_LOG_RMS` and `L2_ALL_STAGE_LOG_RMS_OLS`)
across `T2_embryo_val_interp`, `T2_heart_val_interp`, and
`T2_heart_val_extrap`, producing six final artifacts plus per-artifact and
final-set manifests. It changes only the first three coordinates by a positive
uniform scale about the base centroid; no target coordinates are read.

```bash
PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/t2_g1_scale.py \
  --output-root artifacts/atomic_batch1/B1-A1
```

The final files are ready for manual upload only. The runner never submits to
the online board. Up to four complete source-only diagnostic attempts may be
kept separately under the B1-A1 exploration directory, but they are not
submission candidates or scored artifacts.

`prepare_t2_submission.py` makes a board-valid candidate from a generated T2
prediction by deterministic, celltype-stratified sampling. It does not read a
target or modify expression/coordinates. Use the board's exact setting and keep
the emitted `uns["ve_submission_prep"]` metadata with the candidate:

```bash
PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/prepare_t2_submission.py \
  --task embryo --setting interp \
  --input outputs/t2_baseline/embryo_shift_E7.25.h5ad \
  --output submissions/candidates/T2_embryo_val_interp/v0001_pseudobulk_shift/submission.h5ad \
  --n-cells 5000 --seed 20260821
```

T1/T3 floor candidates use the released reference stages only:

```bash
PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/prepare_t1_t3_submission.py \
  --task T1 --board val --input data/E9.5_RNA.h5ad \
  --output submissions/candidates/T1_val/v0001_copy_last/submission.h5ad --n-cells 5118 --seed 20260821

PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/prepare_t1_t3_submission.py \
  --task T3 --board gata4 --input data/E8.75.h5ad \
  --output submissions/candidates/T3_gata4/v0001_wt_identity/submission.h5ad --n-cells 7449 --seed 20260821
```

## T3 shift-transfer candidates

`t3_shift_transfer.py` transfers the public Mab21l2 KO response from E9.5 to
the immutable v0001 WT E8.75 scaffold. It validates `.X` against
`layers["counts"]` on the released 10,000-library log1p scale and never reads
the held-out Gata4 KO. The two reproducible presets are:

- `official_norm`: full global response, `damp=1`, then row-wise 10,000
  library-size restoration;
- `conservative`: ten-bin count-depth matching, `damp=0.5`, source-gene
  masking, 50 positive/50 negative response genes, and Gata4 zeroing.

```bash
PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/t3_shift_transfer.py \
  --variant official_norm --train-wt data/E9.5.h5ad \
  --train-ko data/E9.5_mab21l2_ko.h5ad \
  --carrier submissions/scored/baseline-001/T3_gata4/submission.h5ad \
  --output submissions/candidates/T3_gata4/v0002_shift_transfer_norm/submission.h5ad \
  --summary outputs/t3_shift_transfer/v0002/diagnostics.json

PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/t3_shift_transfer.py \
  --variant conservative --train-wt data/E9.5.h5ad \
  --train-ko data/E9.5_mab21l2_ko.h5ad \
  --carrier submissions/scored/baseline-001/T3_gata4/submission.h5ad \
  --output submissions/candidates/T3_gata4/v0003_shift_transfer_shrunk/submission.h5ad \
  --summary outputs/t3_shift_transfer/v0003/diagnostics.json
```

Both outputs are candidates until a server score is returned; they must stay
`score_pending` and must not be described as improvements beforehand.

## T1 temporal candidate

`t1_temporal_model.py` builds the T1 expression-shift candidate from the released
E8.5/E9.5 RNA stages only: per-celltype pseudobulk shift (the official
`pseudobulk_shift` route) with fixed shrinkage toward the global delta
(`--celltype-weight`), a global-delta fallback for cell types missing from the
earlier stage (`--unmapped-delta`), and optional one-day composition
extrapolation for the deterministic down-sampling (`--composition-extrap`).
It never reads the held-out target. Strict official-reference behaviour is
recovered with `--celltype-weight 1.0 --unmapped-delta zero --composition-extrap none`.

```bash
PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib python scripts/t1_temporal_model.py \
  --board val --previous data/E8.5_RNA.h5ad --base data/E9.5_RNA.h5ad \
  --output submissions/candidates/T1_val/v0002_shrunk_pseudobulk_shift/submission.h5ad \
  --n-cells 5118 --seed 20260822 --damp 1.0 --celltype-weight 0.5 \
  --unmapped-delta global --composition-extrap linear \
  --diagnostics-out outputs/t1_model/v0002_diagnostics.json

## B1-A3 dual-lane mass/residual runner
`t1_mass_residual.py` freezes a source-only cross-stage state partition and
replays complete rows from the immutable scored T1 baseline. The two formal
lanes are `L1_SHARED_UNRESOLVED` (exact shared labels plus an unresolved
bucket) and `L2_E95_EXPRESSION_PROBE` (E9.5 label vocabulary with a full-panel
cosine expression projection for E8.5). It does not read the held-out target,
does not add per-gene noise, and never uploads automatically.

The B1-A3 output is generated once per lane under
`artifacts/atomic_batch1/B1-A3/`; the corresponding submission files are
registered in `submissions/INDEX.tsv` and remain `score_pending` until manual
server scoring.
```

## Official T2 controls

`t2_controls.py` reproduces the three public T2 audit controls:

- `ctrl_scale_ref`: multiply reference expression by `2.0`;
- `ctrl_squashed_ref`: transform reference coordinates around their centroid by `(4.0, 1.0, 0.25)`;
- `ctrl_random_cube`: retain reference expression and draw coordinates uniformly inside the target bounding box.

The last control reads the target only for its coordinate bounds and is marked
`audit_only` in `obsm`-independent `uns["ve_control"]` metadata. It is not a
valid model or a candidate for selection. Example:

```bash
env LD_LIBRARY_PATH=/opt/anaconda3/lib python3 scripts/t2_controls.py \
  --task embryo --control ctrl_random_cube \
  --reference data/E7.25.h5ad --target outputs/t2_pseudo_holdouts/T2_embryo_interp_proxy/score_slice/target.h5ad \
  --output outputs/t2_controls/embryo_ctrl_random_cube.h5ad
```

## Separated heart interpolation diagnostics

`t2_expression_model.py` implements the exploratory expression-only shrinkage
candidate. It mixes a celltype-specific source shift with a pooled source
shift (`celltype_weight=0.5` here) and carries `spatial_3D` unchanged. The
current heart data have only two non-target stages and no `sample_id`, so the
weight is fixed rather than source-only selected and aggregation is recorded
as cell-weighted pooled. For competition candidates, the optional
`--target-library-size 10000` restores the released log1p library-size scale
after the shift; this is a score-oriented normalization, not a target fit.

`t2_geometry_model.py` implements the low-capacity geometry candidate: an
identity-rotation isotropic scale plus source-only celltype centroid
displacement. It changes only `spatial_3D`; expression and observation rows
remain unchanged. Oracle target geometry is never used by either runner.

## Configured pseudo-holdouts

The starter-pack proxies can be generated without exposing the target stage to the predictor:

```bash
env LD_LIBRARY_PATH=/opt/anaconda3/lib python3 scripts/t2_pseudo_holdout.py \
  --proxy T2_heart_interp_proxy \
  --output outputs/t2_pseudo_holdouts/T2_heart_interp_proxy/prediction.h5ad \
  --score-dir outputs/t2_pseudo_holdouts/T2_heart_interp_proxy/score_slice
```

The script records the training stages, carrier stage, signed damp, limitation, board limits, sampling strategy, seed, and an exact offline `veckit` command in `score_slice/manifest.json`. It uses fixed-seed `celltype`-stratified sampling by default; pass `--sampling-strategy first` only for legacy comparison. The `copy_last` floor can be generated with `--method copy_last` in the same command. `pseudobulk_shift_row_norm` is intended to diagnose scale mismatch in extrapolation; it is not an official baseline.

For post-hoc geometry attribution, `t2_geometry_attribution.py` replaces only `spatial_3D` and marks the result as oracle geometry. Such variants are diagnostic only and must not be used as predictions.
