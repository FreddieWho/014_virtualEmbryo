# T3 v0089 — response-structure route, delivery 2026-10-09

## What this is

One candidate for `T3:gata4`, version `v0089`, method `resplam15unmask`, parent
`v0088 condhurdle` (server 53.69). Built, contract-checked and packaged; **not
scored and not submitted**.

The route changes exactly one thing: the response structure. The shrinkage
blend between the state-local and global quantile response moves from
`lam = nk/(nk+50)` to `lam = nk/(nk+15)`, and the `global_valid` gene mask is
removed so globally-sparse genes can respond. The emitter, WT atlas, state
assignment, quantile grid, seed (20260904), E8.75 stage, method/mode
(`mean_combined`, from the frozen source-side selection) and geometry are all
carried over unchanged.

## Why the response and not the emitter

The earlier emitter-parameter loop saturated at +0.003 with `de_skill` changing
by exactly 0.00000 across every variant. The reason is structural: the emitter
only redistributes already-activated cells to different rows, so it cannot
change which genes are detected together. DE lives in the response structure.
Moving the response moved `de_skill` by +0.354 for the first time.

## Local evidence

| | value |
|---|---:|
| incumbent v0088 composite | 74.737588 |
| v0089 composite | **74.936110** |
| delta | **+0.1985** |
| per-genotype wins | 4/7 |
| worst genotype | Dnmt1 −0.8551 |
| frozen v0088 decision gate | PASS |

Component deltas: de +0.354, direction +0.527, mmd +0.188, variogram +0.374,
severity_abs −0.368.

Harness fidelity: the response reimplementation reproduces the original
`embryo_responses` cache bit-exactly (delta, composition and support all
maxabs 0.0), so every delta is attributable to the substituted assumption.

## Contract checks

Roundtrip `X` exact; gene order exact; protected (unmasked) rows unchanged;
finite and non-negative; `spatial_3D` finite; panel closure max mass error
0.00346 < 0.02; shape 7449×500.

## Delivery

- zip: `deliveries/t3lam15__t3__upload__20261009.zip`
- member (portal Model name): `t3_gata4__resplam15__v0089.h5ad`
- artifact SHA256: `ddac99703587e2c35713dcf0e3eb09bb6a0dfff88298bb94548a08d1fa115f3a`
- zip member SHA256 verified against `submissions/INDEX.tsv`

`deliveries/` is gitignored, so the receipts are mirrored here for audit.

## Caveats

The local source-side composite is **not a server forecast**. v0086 improved
source-side and scored 49.34 on the server, below v0084's 49.55. T1 v0058 and
T2 v0035 are the same pattern. The gain here is also not uniform across
held-out genotypes.

T3 submission budget is unresolved: the registry records 2026-10-08 usage 8/8
with no further attempt authorized, 2026-10-09 had no T3 submission, and
whether the daily counter reset was not observed. Uploading requires explicit
user authorization. blocks_submission:false.

## Negative result recorded alongside

A genuinely different architecture — joint rank transport, replacing per-gene
marginal quantile fill with whole-profile rank transport — measured 62.668426,
i.e. −12.07 against the incumbent, with its control arm held at the frozen
74.412. The drop is therefore attributable to the transport operator rather
than the harness: this composite rewards marginal distributional calibration.

State-granularity (S≠8) and quantile-resolution (nq≠21) families fail closed as
response swaps because the response shape must match the refitted model's `S`
and `positive_q`. Testing them requires a full model refit; not executed.
