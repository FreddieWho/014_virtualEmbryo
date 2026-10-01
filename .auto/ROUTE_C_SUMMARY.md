# Route C summary — broad algorithm sweep on T2 heart-extrapolation (2026-10-01)

Session: branch `autoresearch/t2-heart-extrap-20261001`, `.auto/log.jsonl` (28 entries).
Board: `T2:heart:val_extrap`, n_obs=25179, 500-gene panel. `target_used=false` throughout
(E10.5 never read). Scorer: frozen proxy spec (setting=heart, seed=20260916),
~15 s per score. All designs deterministic given their seed.

## 1. Frozen objective (declared before the sweep)

`COMPOSITE` = mean of 8 winsorized (±30%) relative gains vs the locked baseline across the
**same 8 skill channels the portal returns for this board** (de, dir, mmd_u, vario, d2, occ,
scale, nmmd), ×100. Baseline = 0.0 by construction. Definition + source-verified directions:
`.auto/composite_config.json`.
Diagnostic companion: `EXPR_COMPOSITE` = the 5 expression channels only (guards against
geometry artifacts, since the proxy target is an E9.5 cardiac *subset*).

**Directions were verified from scorer source docstrings** after an error was caught:
`variogram` is *lower-is-better* (`core_metrics.py:326`), the opposite of what the earlier
Route-B header assumed. Route B's "keep" (comp-only, vario 0.0832 vs baseline 0.0743) is
therefore a **degradation** and was withdrawn as an optimization result; server data
corroborates the corrected sign (comp cousin x_n3 vario skill 47.4 < shrink v0011 48.5).

**Proxy validity (calibration, 12 already-server-scored lanes):**
Spearman(composite, server board) = **0.538**. Extremes rank correctly (worst lane x_n1 has
the lowest composite; the top-2 server lanes are in the top-2 composites); the mid-band is
noisy (v0011 has the top server score but only +0.03). Local-only: never a promotion claim.

## 2. Sweep results (Route C)

| iter | algorithm / combination | composite | expr | verdict |
|---|---|---:|---:|---|
| 12 | **quantile trend extrapolation (QTE)** — per-gene per-state quantile functions extrapolated, cells rank-mapped | **+2.377** | +3.80 | keep |
| 13 | CORAL covariance alignment per state | −4.61 | −7.38 | discard |
| 14 | QTE with 3-node Lagrange (quadratic) in quantile space | −6.56 | −10.50 | discard (guardrail fail, var×3.3) |
| 15 | **QTE × compmix resample** (3 seeds) | **+3.464** | +6.07 | keep |
| 16 | low-rank SVD denoising of the mean-shift delta matrix | −1.38 | −2.21 | discard |
| 17 | FDR-gated QTE (BH 0.05) | +2.377 | +3.80 | no change (gate kept 2500/2500) |
| 18 | QTE in 30-PC space | −0.60 | −0.96 | discard |
| 19 | **time-normalized QTE** (shift × 4/3 = Δt_target/Δt_source) | +2.608 | +4.17 | record-only |
| 20 | **time-normalized QTE × compmix** (3 seeds) | **+3.913** | **+6.30** | **KEEP — champion** |
| 21 | log-linear share-trend composition × time-QTE (3 seeds) | +0.855 | **+11.48** | discard (guardrail fail; lead) |

Reference points: best previously-known local design = x_o2_shrinkcomp **+1.709**;
runner-up x_n3_compmix +0.931; frozen baseline 0.000.

## 3. Champion (pending nothing local)

- artifact: `artifacts/autoresearch/t2-extrap-20261001-v1/submission.iter20-qte-time-compmix.h5ad`
  (median seed 20261008; 3-seed composites {3.913, 4.0088, 3.6058}, **all beat the previous
  champion**, all guardrails pass)
- sha256: `dc811606fafdbbec69665d936bebefafae3121096f69dae0de4e58a09753a1af`
- mechanism: per-gene, per-state quantile-function extrapolation of the E9.5 marginal by
  4/3 × (Q9 − Q8), cells mapped through their own within-state rank probability; then the
  x_n3 composition plan resamples rows to the log-ratio-extrapolated E10.5 shares.
- channel profile (median seed): dir +6.0%, mmd_u +8.9%, nmmd +7.6%, de +5.6%, vario +3.5%,
  geometry ≈ flat.
- contract: FAIL with **exactly** the 4 frozen mass-lane exemption strings, zero other errors
  → `fail_by_design_accepted`, the same disposition under which x_n3 and x_o2 were submitted
  and scored. Evidence `CONTRACT_iter20.json`.
- NOT registered in `submissions/INDEX.tsv` (coordinator-owned); NOT uploaded; no server score.
  Standing rules apply: a portal read needs a coordinator INDEX row first.

## 4. Mechanism knowledge (transferable)

1. **The marginal is the lever; the mean is dead.** Seven consecutive mean-shift-family
   designs pin `de_score` at exactly 0.2466 (baseline Δ, cap, shrink C=1/C=2 f32/f64,
   adaptive, lateref, trend3, lineage, SVD-denoised). Only full-marginal (quantile) mapping
   moves the expression channels.
2. **Rank/quantile mapping preserves the copula and mass**: clip fraction 1.5% vs 17–24% for
   mean shifts. This is why vario, mmd_u and nmmd all improve at once.
3. **Gene space beats PC space beats covariance space.** CORAL on already-matched covariances
   only amplifies estimation noise (vario +55%).
4. **The two channels are complementary, not redundant**: the marginal channel carries de and
   vario; composition carries dir, mmd_u, nmmd (+4.9/+8.6/+7.3% combined vs +0.3/+4.9/+3.4%
   for marginals alone). Compounding works: 1.709 → 2.377 → 3.464 → 3.913.
5. **Higher-order extrapolation overshoots** (quadratic var×3.3); linear with the correct time
   scaling is the right order for this horizon. Significance gating is vacuous here (the
   temporal shift is ubiquitous, 2500/2500 pairs pass FDR 0.05).
6. **Expression headroom is ~2× the current champion** (+11.5 vs +6.3) but aggressive
   composition estimators break the companion channels (d2 −30%, scale −21%, systematically).
   The binding constraint has moved off expression.

## 5. Leads (not run)

- Geometry-preserving aggressive composition: cap each state's share change at the largest
  change observed between two consecutive real stages (data-frozen rule, not a scanned factor).
- Ensemble of champion variants on a shared row plan (all compmix lanes share rows per seed).
- Growth-trend geometry extrapolation (defensible only with a frozen rule; tuning geometry to
  the E9.5-subset proxy would be leakage).

## 6. Recommendation

The champion is the strongest local design this board has produced under a frozen objective
with a validated proxy ordering (ρ=0.54). Options for the user:
1. **Server read** (needs coordinator INDEX row + manual upload): the only way to test whether
   the composite's ordering transfers; x_n3/x_o2 precedents make the contract disposition
   routine. Historical caution: this board's proxy has never been promoted to a verified
   server predictor, and two of the three highest server lanes (v0011, x_r1) sit in the
   composite's mid/low band.
2. **Hold** the artifact as a research record and spend the next round on the
   geometry-preserving composition lead, which could plausibly reach expr +11 at champion-level
   companion channels.
