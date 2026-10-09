# T2 embryo campaign, 2026-10-09

## Identity and scope

Started from main 29a8e1976665a66a7378892857c815f589720971 in a clean clone. Only E7.5 embryo validation candidates; no heart/T1/T3 submissions. No protected E7.5/E7.75 measurements were read. No paid compute. Official E6.75/E7.25/E8.0 input hashes match the historical intake manifest; official panel is exactly 498 genes.

Historical E3 was rebuilt byte-for-byte (e93d56f2…dbfdae), checked against `reports/t1_late_anchor_20261008/MANIFEST.tsv`. It is distinct from the original v0014: the later recipe computes shrinkage weights from a different numerator. Both identities are preserved. `reproduce_e3.py` asserts the original E3 file digest.

## Frozen candidates

Canonical candidate identities belong in `submissions/INDEX.tsv`, updated by the coordinator; the V00xx handoffs here are audit/delivery documents. Server scores belong exclusively in `reports/SERVER_SCORE_REGISTRY.md`.

- v0019: E3 expression/rows fixed; state-conditioned Gaussian Bures geometry after proper frame registration. Final parent RMS locked. Seven missing endpoint states use fallback. Independently audited, byte-replayed.
- v0020: E3 expression/rows fixed; normalize right endpoint shape RMS, rigidly align, and use an actual-point shape mixture at fixed lambda 1/3. Capacity-constrained assignment yields 1117 distinct right donors, no donor reuse. Exact parent RMS locked. The old generic `diagnostics.mechanism` text says displacement, but `support=mixture` and the actual implementation use complete endpoint points, not interpolated points.
- v0021: E3 geometry fixed; independent E7.25 scRNA rank-Gaussian partial-correlation prior reorders existing gene values within states. Every state/gene sorted value vector is exactly preserved, including all zeros. Dependence changes, not expression units or marginal means.

No frozen artifact is overwritten. Intermediate prototypes and rejected engineering variants remain under `artifacts/t2_embryo_campaign_20261009`.

## Local evidence and limits

All released-stage comparisons use E6.75 + E8.0 → E7.25, fixed prediction seed 20261009 and scorer seeds 0/1/2. This is not the E7.5 server task and not a hard screening gate. The three-stage E3 expression recipe cannot be validly reconstructed on this fold without an earlier released stage, so local geometry interventions use a matched simple left bridge. No pseudo-target was used to construct that carrier.

- Bures improves local normalized D2 but harms occupancy and neighborhood; pair-shuffling makes neighborhood far worse. This demonstrates preserved coupling matters, but does not prove the geometry works on the target.
- Actual-point shape mixture avoids novel Gaussian support but does not show a local total gain. The unnormalized-size mixture is retained as an implementation diagnostic, not a chosen candidate.
- External Geo-seq programme transfer has detectable signal against gene-shuffle controls, but global row remapping damages native coupling. One predeclared local displacement constraint uses the source-state 15-neighbor scale; no amplitude sweep was performed. Final proposed form permutes coordinates within state, preserves X/obs/layers, and retains the exact coordinate multiset.
- External scRNA copula local total is 51.757 versus unchanged 51.530 and gene-shuffle 49.955; internal covariance is stronger at 52.339. Therefore external is not claimed to be best. The external sample is independent E7.25, the same stage as the official pseudo-target, so this is not a strict all-source temporal exclusion test.

Finite-index subsampling can make shape metrics change under a pure coordinate permutation even though the full geometry distribution is identical. Likewise fixed per-gene marginals do not fix MMD or variogram, which measure joint gene dependence. Do not promise numerical invariance beyond directly checked arrays.

## External sources

- GSE65924: three E7.0 epiblast Geo-seq pool replicates; transfer cross-replicate stable AP/PD rank weights, never raw FPKM values or idealized physical 3D coordinates. 480/498 panel genes overlap. Pool composition and single-cell distributions are different.
- GSE278981/GSM8559288: independently processed E7.25 PE725 10x counts, 6173 cells before fixed source QC / 5799 after. Explicit same-symbol feature summation precedes exact 498-gene selection. Only this sample's matrix/features/barcodes are used; E7.5 files and joint atlas/imputation models are excluded.
- GSE171588 and Harland joint/imputed products remain excluded; they are never candidate inputs.
- GEO open reuse terms apply; no unsupported CC-BY/CC0 claim.

## Reproduction

Interpreter used: `/workspace/shared/t2venv/bin/python`. Set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1. `runtime.py` adapts only the original helper's data directory, leaving recipe code unchanged. Each CLI accepts `--data`; no secrets or authenticated download URLs are embedded.

Core commands: reproduce_e3.py; build_geometry.py with the asserted E3 parent digest; run_external.py --support mixture --arms internal --external /not_used; run_copula.py; run_rewire.py --locality. The `--fold --score` flags evaluate only released E7.25. Per-run JSON and log outputs record metrics, provenance, and controls.

Copula reproducibility is locked to OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1. Independent same-environment reconstruction is exact. A two-thread run changed 1709/2490000 entries (0.0686%), mean absolute difference 0.00295019 and maximum 7.12952: rank selection discretely amplifies numerical tie differences. This is not described as uniformly tiny error; use the frozen artifact or the locked environment.

## Final close

All four candidates are terminal scored; v0021 retained. Read FINAL_REPORT.md and authoritative score registry for the completed budget and score evidence. No additional model experiments/submissions continue.
