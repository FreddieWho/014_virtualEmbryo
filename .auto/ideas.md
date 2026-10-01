# Ideas backlog (T2 heart extrap autoresearch)

- Per-state adaptive shrinkage: C per state from |Δ|/SE (t-stat) instead of global C=1/2; try C in {0.5, 1.0, 2.0} mapped through w=t/(t+C). Untried structurally (only global C so far).
- Late-anchor blend: Δ = α(μ95−μ875) + (1−α)(μ95−μ825late), α in {0.25, 0.5, 0.75}; x_r1 is α=0 endpoint, baseline is α=1 endpoint — interior never tried.
- Magnitude-capped deltas: cap per-gene |Δ| at k×SE or quantile (e.g. 2×SE, p99); clip_frac currently 17–48% does the capping implicitly — explicit cap may preserve dir while cutting nmmd.
- Composition-only extrap: resample baseline rows to predicted E10.5 shares (log-linear share trend E8.25→E8.75→E9.5) with expression untouched — mirrors e_r1/h_r1 wins on interp boards, never tried on extrap.
- Variogram-targeted: variogram is weakest extrap skill (~0.07–0.10); try within-state covariance-preserving shift (add Δ to cell means, keep residuals) vs current mean-shift that collapses variance.
- Negative control (do NOT promote): spatial kNN smoothing — known local-win/server-loss; use only to validate that measure.sh reproduces the 0.2603 local-win signature.
