# Ideas backlog (T2 heart extrap autoresearch)

- Per-state adaptive shrinkage: C per state from |Δ|/SE (t-stat) instead of global C=1/2; try C in {0.5, 1.0, 2.0} mapped through w=t/(t+C). Untried structurally (only global C so far).
- Late-anchor blend: Δ = α(μ95−μ875) + (1−α)(μ95−μ825late), α in {0.25, 0.5, 0.75}; x_r1 is α=0 endpoint, baseline is α=1 endpoint — interior never tried.
- Magnitude-capped deltas: cap per-gene |Δ| at k×SE or quantile (e.g. 2×SE, p99); clip_frac currently 17–48% does the capping implicitly — explicit cap may preserve dir while cutting nmmd.
- Composition-only extrap: resample baseline rows to predicted E10.5 shares (log-linear share trend E8.25→E8.75→E9.5) with expression untouched — mirrors e_r1/h_r1 wins on interp boards, never tried on extrap.
- Variogram-targeted: variogram is weakest extrap skill (~0.07–0.10); try within-state covariance-preserving shift (add Δ to cell means, keep residuals) vs current mean-shift that collapses variance.
- Negative control (do NOT promote): spatial kNN smoothing — known local-win/server-loss; use only to validate that measure.sh reproduces the 0.2603 local-win signature.

## Status (2026-10-01, Route B pivot — variogram primary)

- Per-state adaptive shrinkage: TESTED iter8 (C=1 x n95/(n95+median)) → pinned 0.2466, CLOSED for DE; UNTESTED under variogram primary (shrink runs nudged variogram +0.003/+0.004 — below keep bar, not worth revisiting unless paired with composition).
- Late-anchor blend: CLOSED all primaries (monotonic inversion, 4 pts). Never revisit.
- Magnitude-capped deltas: CLOSED (exact no-op on DE). Under variogram primary: untested, but cap was a no-op on every metric except dir +0.002 — low priority.
- Composition-only: CLOSED for DE-primary (seed-fragile); REOPENED under Route B (variogram +0.008/+0.009 on BOTH seeds, guardrails pass) — iter10 tests 3rd seed for median verdict.
- Variogram-targeted covariance shift: SUPERSEDED — mean-shift already preserves within-state covariance by construction; the variogram gap is between-state structure, which composition (not covariance surgery) moves. Drop unless new evidence.
- Negative control: STILL UNRUN, still low value (harness validated 10/10 clean scores). Run only if scorer doubt ever arises.
- NEW under Route B: (a) shrink-expression x comp-resample combo under variogram primary (x_o2-analog scored variogram? UNRECORD — check iter9 score JSONs if retained; else rebuild with median rule); (b) trend-share exponent variants — REFUSED in advance (trend-form scan = proxy-tuning; log-linear stays frozen).

## T1 backlog (2026-10-02, report-proxy phase; de primary 0.5926, higher better)

- T1 luck-band probe (FIRST, diagnostic): bootstrap-within-report rows (same type counts, 3 seeds) — pure row-identity noise meter, no mechanism. If |Δde| ~0.02 on pure bootstrap, single-seed resampling keeps are meaningless -> 3-seed rule justified. Single-shot, no tuning.
- Plain per-type per-gene quantile extrap (Qpred = Q95tr + (Q95tr - Q85tr), factor 1.0 = 1day/1day, no time correction): T1 analogue of T2's champion marginal; structurally distinct from R1-B (no zero-splitting) and o1mass (no parametric form). Deterministic single-shot.
- QTE x joint-resample combo (only if QTE helps alone): marginal channel + composition channel, mirrors v0029-stack and T2 iter15/20 logic. 3 seeds.
- Winner-mix probe (single-shot 50/50 stratified report-level mix of v0035+v0038 report predictions): tests complementarity of dir-carrier vs mmd-carrier at local level. NOT a submission design (report-level mix only), diagnostic.
- Covariance-OT follow-ups (only if plain QTE fails AND luck band is tight): (a) OT map shrunk by per-type sampling variance (data-frozen t-shrink, mirrors T1-R5-C logic applied to transport maps not means); (b) OT in log-space vs linear — refused as scan unless (a) shows signal.
- REFUSED in advance: composition-strength scans (s1growth direction already lost), mean-shrink C scans (closed), 70/30<->50/50 mix-ratio scans (proxy-tuning), significance-gated QTE (T2 showed saturation; T1 n's even larger), quadratic time extrap (T2 overshoot; T1 intervals equal anyway).
- Web-retrieval note: 1 search done (temporal OT/pseudobulk benchmarks, thin). In-repo history (30+ scored lanes) dominates; further web only if covariance axis reopens.

## T1 terminal status (2026-10-02 — PAUSED, 0 keeps, see log `terminal` entry)
- Bootstrap luck probe: DONE (T1-1, discarded itself, band ±0.018, quantum 0.0185).
- Plain QTE marginal: DONE (T1-2, energy veto).
- QTE x whole-row projection: DONE (T1-3, catastrophic).
- Winner-ensemble 50/50 probe: DONE (T1-4, wash).
- All refused items above stand refused. Remaining leads: L-T1-1 full-scIMF lane, L-T1-2 full-pipeline on-manifold ensemble, L-T1-3 energy-veto doctrine. All need user authorization; none are loop-continuable.
- Web note (2026-10-02): 2 searches attempted (temporal OT/pseudobulk; scTimeBench/scIMF); backends flaky, nothing beyond P0-2 retrieval. In-repo 30+ lanes dominate evidence. No further web planned.
