# Autoresearch: T2 heart extrapolation (local proxy optimization)

## Objective
Optimize T2 heart-extrapolation candidates (board `T2:heart:val_extrap`, n_obs=25179,
500-gene panel) against the **local R1 proxy scorer only**. Server board score is NOT
available in the loop; local improvements are record-only and do NOT imply leaderboard
gains (proxy is known adversarial on spatial family and inverted on shrink family —
see What's Been Tried). No restriction to existing routes: continuing frozen routes or
opening new routes are both allowed (user authorized 2026-10-01). Goal is to push local
scores higher and surface ideas worth a later frozen design + contract + manual upload.

Target stage is E10.5 (never read any E10.5 truth; target_used=false always).
Prediction input stages allowed: `data/E8.25_late.h5ad`, `data/E8.75.h5ad`,
`data/E9.5.h5ad`. Proxy eval target/ref are prebuilt cardiac subsets under
`artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/` (proxy_target_e95_cardiac /
proxy_ref_e875_cardiac) — read-only.

## Metrics
- REPO POLICY OVERRIDE (2026-10-01): root .gitignore excludes `artifacts/` and `*.h5ad` from git (large binaries, keep locally). So KEEP = persist candidate + DIAG.json on DISK under `artifacts/autoresearch/...` (gitignored, survives locally) + record path+sha in `.auto/log.jsonl` (committed). NEVER `git add -f` binaries against the exclusion.
## Metrics
- **ROUTE C PRIMARY (2026-10-01, current)**: `COMPOSITE` — equal-weight mean of winsorized (±30%) relative gains across the **8 channels the portal actually returns for heart-extrap** (de, dir, mmd_u, vario, d2, occ, scale, nmmd). Frozen definition + source-verified directions in `.auto/composite_config.json`. Baseline = **0.0** by construction. Local champion to beat = **x_o2_shrinkcomp +1.709** (server 50.52); runner-up x_n3_compmix +0.931 (server 50.38).
  Keep bar: deterministic design composite **> +1.709** + guardrails; resampling design **3-seed median > +1.709** + all seeds guardrail-clean. Guardrails: de≥0.22, library_size_ratio≤2.0, variance_ratio∈[0.8,1.6], pb_rel_err≤0.65. Any violation = discard regardless of composite.
  Proxy validity (measured 2026-10-01 on 12 already-server-scored lanes): **Spearman(composite, server board) = 0.538**. Extremes rank correctly; mid-band noisy (v0011 has top server score but only +0.03). Local-only — never a promotion claim.
  Geometry caveat: d2/occ/scale are untouched by expression-only algorithms (3 of 8 channels ≈ 0 contribution), and scale_log_ratio against the proxy target is a subset artifact → tuning geometry to the proxy would be leakage. Only trend-extrapolated growth rules would be defensible; deferred.
- **DIRECTION CORRECTION (2026-10-01)**: the earlier Route-B header had `variogram` inverted. Scorer source (`core_metrics.py:326`) says **"Lower is better; 0 for a perfect match"**. Consequences: Route B "keep" (comp-only, vario 0.0832 vs baseline 0.0743) is a **degradation**, WITHDRAWN as an optimization result (artifact remains on disk as a research record, and is NOT a candidate for upload); iter11 flips — shrink moves variogram back toward baseline. All directions now verified from source docstrings (see log `correction_scan`).
- **Route A/B legacy primaries (closed)**: de_score (baseline 0.2466, higher) — exhausted, 0 standing keeps; variogram-as-primary — void (inverted).
  Best local to date: x_o2_shrinkcomp 0.2603 (+0.0137). Best server-numeric lane x_r1_lateref
  (v0022, 50.74) had local de 0.2466-holder range — local/server can disagree; keep both in ASI.
- **Secondary** (independent tradeoff monitors, log every run): `de_direction` (higher better,
  baseline 0.4221), `neighborhood_mmd` (**lower** better, baseline 0.20513),
  `morans_I_agreement` (higher, 0.8044), `variogram` (higher, 0.074261), `mmd_u` (lower, 0.10468),
  `energy_distance` (lower, 3.49285), `pseudobulk_pearson` (higher, 0.7913), `variance_ratio`
  (~1.0 ideal, 1.227), `_wall_s`.
- Local dual-gate reference (historical R1, now record-only, NOT a promotion gate):
  de_score > 0.2466 AND de_direction > 0.4221.

## How to Run
`./.auto/measure.sh [candidate.h5ad]` — scores one h5ad with the frozen extrap proxy spec
(setting=heart, seed=20260916, ~30s) and outputs `METRIC name=value` lines.
Default (no arg): scores `.auto/candidate.h5ad` if present, else the locked baseline parent.
Every generator script MUST write its output to `.auto/candidate.h5ad` (temp iteration file,
never a submission) then call measure.sh. Keep the script fast: single scorer run is fine
(~30s); do NOT run medians.

Scorer command (frozen, do not change flags):
`env LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH=third_party/veckit python third_party/veckit/score_h5ad.py --task T2 --setting heart --input <cand> --target artifacts/g0/.../proxy_target_e95_cardiac.h5ad --reference artifacts/g0/.../proxy_ref_e875_cardiac.h5ad --seed 20260916 --out <tmp>`

## Files in Scope
- `.auto/candidate.h5ad` — per-iteration temp output (overwrite freely, gitignored).
- `.auto/generate_*.py` — new generator scripts you create (e.g. `.auto/generate_delta_scale.py`).
  Reuse read-only helpers: `scripts/t2_round2/common.py` (`load_parent` hash-locked, `load_stage`,
  `means_vars_by_label`, `write_candidate`, `stamp_uns`, `fix_obsm`), `scripts/t2_round2/ops.py`
  (`shrink_weights`, `se_two_means`, `share_series_predict`), `scripts/t2_goal/run.py`
  (`GoalExtrapCtx`, `eng_gate`) — import, do NOT edit.
- `artifacts/autoresearch/t2-extrap-<date>-vN/` — only place for persisted promising outputs
  (copy of candidate + diag JSON). Never write elsewhere.
- `.auto/log.jsonl` (append-only results), `.auto/ideas.md` (backlog), `.auto/measure.sh`
  (may add instrumentation only, never change scorer flags/seed/target).

## Off Limits
- NEVER touch: `submissions/**` (INDEX.tsv, candidates/, scored/), `reports/SERVER_SCORE_REGISTRY.md`,
  `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, `reports/LANE_VERDICTS.tsv`, `docs/coordination/**`,
  `STATUS.md`, `TODO.md`, `DECISIONS.md`, `LEADS.md`, `configs/**`, `scripts/**` (existing files),
  `tests/**`, `data/**`, `third_party/**`, `deliveries/**`, any `*.h5ad` outside `.auto/` and
  `artifacts/autoresearch/`.
- NEVER read: any E10.5 truth, E7.5/E8.5 truth, or portal/server internals. target_used=false always.
- NEVER claim leaderboard improvement from local scores. Server-pending promotion requires a
  separate frozen design + contract + coordinator handoff — out of scope for the loop.
- No new pip/conda deps. CPU only. Each lane ≤4h/≤64GB inherited as iteration budget guideline.
- No `checks.sh` per user choice — correctness is advisory (eng_gate diag), not a keep-blocker.

## Constraints
- Every generator: deterministic given its seed (fixed RNG seed in file); finite/nonnegative
  float32 X; n_obs=25179, n_vars=500 panel order exact (`data/gene_panel/T2__heart__val_extrap.genes.txt`);
  obs_names unique/nonempty; obsm spatial_3D (n,3) float32 finite; uns ve_contract marker.
  Parent for geometry/rows is baseline-001 (`submissions/scored/baseline-001/T2_heart_val_extrap/`,
  sha256 `f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504`) — verify hash
  at load via `common.load_parent`.
- Primary metric is king: improved de_score → keep (copy candidate + generator into a new
  `artifacts/autoresearch/` dir and commit); worse/equal → discard (revert generator, keep log).
- Annotate every run with ASI: what mechanism you tried, delta formula, shrinkage C, clip frac,
  which states moved, why you think it helped/failed, and what to try next. Failures need heavy
  ASI — reverted code is gone, log is the only record.

## What's Been Tried- Baseline parent v0001 (locked): de 0.2466 / dir 0.4221 / nmmd 0.20513 / morans 0.8044 /
  variogram 0.074261. Server 50.53 (aggregate) — local/server link unproven.
- v0011 t-shrink C=2 (g0): local 0.2466/0.4183 (pinned-negative vs baseline) BUT server 50.64
  (+0.11, board best at the time). Lesson: local proxy INVERTED on shrink family — local loss can
  still win on server. Do NOT discard shrink ideas on local loss alone; log them.
- Spatial smoothing k07–k60 (v0012–v0016): local WIN (0.2603 > 0.2466) but ALL server losses
  (-0.21..-0.28). Lesson: proxy ADVERSARIAL on spatial family — local win predicts server loss.
  Family CLOSED for promotion, but still usable as negative control in the loop.
- x_n1_lineage (17 orphan→ancestor deltas): local de 0.2329 (-0.0137), server 48.17 REJECT.
  Lineage-mapped deltas don't move extrap board.
- x_n2_trend3 (E8.25-anchored 3-stage Δ=2v2−v1): local de 0.2466 (=), dir +0.009. Server lane
  family scored 50.38/50.52 range — no promotion.
- x_n3_compmix (composition trend extrap, log-ratio, ×2 cap): local de 0.2466 (=), dir +0.017,
  nmmd -2.6%. Combined with shrink as x_o2: local de 0.2603 (+0.0137, only lane over historical
  dual-gate) — local best to date, server 50.52 TIE.
- x_r1_lateref v0022 (Δ=μ95−μ825late on baseline): numeric server-highest 50.74 (+0.21/+0.10,
  TIE-highest backup, no promotion per no-co-promotion rule). Local de ~= holder.
- x_r2_shrinkc1 v0023 (baseline Δ × t-shrink C=1): server 50.03 REJECT.
- FGW ε 0.005→0.002 (L-002, non-grid): objective lower both holdouts, NFS only H2 better —
  frozen objective misaligned with metric in ε direction. "Better solve of same objective" is a
  dead axis on T2. Prefer structural mechanism changes over solver tuning.
- iter1 late-anchor blend α=0.5 (2026-10-01): de 0.2329 (-0.0137) → DISCARD. dir/variogram/morans ticked up but nmmd/energy/pb worsened.
- iter2 blend α=0.25: de 0.2192 (-0.0274) → DISCARD. Three points monotonic (α=1.0: 0.2466 > 0.5: 0.2329 > 0.25: 0.2192): late-anchor magnitude dose-dependently hurts local DE, yet α=0 (x_r1) holds server-high 50.74 — proxy/server inversion confirmed both directions. Anchor-blend axis CLOSED (α=0.75 skipped as predictable, no info gain).
- iter3 baseline Δ capped at 2×SE per gene: de EXACTLY 0.2466 → DISCARD (equal). 63.6% entries hit the cap yet primary unmoved: large-shift genes carry zero proxy-DE signal. K-scan refused as proxy-tuning; cap axis CLOSED.
- iter4/iter5 comp-only log-linear shares→t=10.5 (2026-10-01): seed ...002 de 0.274 (+0.0274, provisional keep) BUT seed ...003 de 0.2466 (=, discard). SAME counts, different rows → ±0.03 row-identity noise. iter4 win DOWNGRADED to seed luck. Residue: dir (+0.06) and nmmd (-0.03) improved under BOTH seeds — composition robustly helps direction/geometry, not DE. Comp-only CLOSED for DE-primary (seed-fragile); kept as dir/nmmd lever for any future non-DE design.
- iter6 baseline Δ × t-shrink C=1 float64: de EXACTLY 0.2466 → DISCARD. Approximates x_r2 (float32 C=1, server 50.03 REJECT, local unrecorded): local pinned, server mixed. Shrink family locally pinned across C=1/C=2 × f32/f64; C-scan refused.
- iter7 lateref α=0 (2026-10-01): de 0.2055 (-0.0411) → DISCARD as optimization, HEADLINE as knowledge. Four deterministic points strictly monotonic: local 0.2466/0.2329/0.2192/0.2055 vs server 50.53→50.74. Local proxy DECREASES in what the server rewards on this axis.
- iter8 adaptive shrink (C=1 × n95/(n95+median), data-frozen): de EXACTLY 0.2466 → DISCARD. Fourth deterministic pin; adaptivity adds nothing. Axis closed.
- iter9 x_o2-analog 3-seed median: {20260929: 0.2603 (reproduces history — harness valid), ...004: 0.2603, ...005: 0.2329} → median 0.2603 but min 0.2329 FAILS pre-committed bar (min3>baseline) → DISCARD, no bar-moving. Bimodal row-luck again. x_o2's historical local-best was partly seed luck (2/3 high mode = real but fragile).
- TERMINAL (2026-10-01, 9 iters, 0 standing keeps): DE-primary has ZERO live axes — deterministic pinned (4×: baseline/cap/shrink/adapt), anchor inverted (4 pts), all resampling seed-fragile ±0.03 (2 families). Deliverables: (1) inversion map, (2) luck-band quantification + 3-seed-median rule, (3) closed-axes ledger (anchor/cap/shrink/adapt × C/K-scan refusals). Do NOT run iter10+ on DE-primary without user pivot — that would be thrash. Open question for user: close loop, or pivot primary (user call only).
- ROUTE B (2026-10-01, user-authorized pivot; NEW PRIMARY, runs iter10+): primary = **variogram** (higher better), baseline **0.074261** (two independent measurements agree exactly: session iter0 + round2 parent — deterministic scorer, stable). JUSTIFICATION IS EXTERNAL: server registry calls variogram the extrap-board headroom (weakest skill 28–33 across scored lanes; v0008/v0010 lose on variogram 41.6/43.6 vs 47.7) — target chosen for server-side weakness BEFORE new runs, not because comp looked good locally. HARKING ACK: comp-family's Route-A variogram gains (+0.008/+0.009 both seeds) are then confirmatory, not selective; Route B iter10 does NOT independently prove 'comp is good'. de_score DEMOTED to guardrail monitor (not optimized). GUARDRAILS (anti-degeneracy, pre-committed): de>=0.22, nmmd<=0.22, energy<=4.0 on every scored seed. KEEP BAR: resampling → min3_vario>baseline AND median_vario>0.078 AND guardrails on all 3; deterministic → single run vario>0.078 + guardrails; |Δvario|<0.002 = noise. de-primary verdicts above stand untouched (no retroactive re-grading).
- NOISE DISCIPLINE (binding): resampling designs must report median of 3 seeds before keep; |Δde|<0.005 on deterministic designs = noise, re-run before keep; never add a knob to rescue a no-op axis.
- iter11 x_o2-analog full-metrics (Route B): vario {0.074691, 0.074481, 0.073566} → median 0.074481 (<0.078 bar), min < baseline → DISCARD. HEADLINE-2: shrink-expression ERASES comp variogram gain (same rows: 0.083 with baseline expression vs 0.0745 shrunk) — variogram rewards state separation, shrinkage removes it; server rewards the opposite (v0011/x_r1). Shrink-expression CLOSED under both primaries. de bimodality reproduced exactly (deterministic machinery ×2).
- ROUTE B STATUS (12 iters total, 1 standing keep): keep = comp-only log-linear (median vario 0.083151, on disk + DIAG). No disciplined follow-up remains — trend-form scan refused, damp/amplify server-rejected, negative control valueless. RECOMMEND PAUSE: propose comp-only for a future frozen lane only if user wants a dir/nmmd/vario non-DE design; never auto-submit.
- **ROUTE C (2026-10-01, sweep complete — see `.auto/ROUTE_C_SUMMARY.md`)**: CHAMPION = **time-normalized QTE x compmix, composite +3.913 / expr +6.302** (median of 3 seeds {3.913, 4.0088, 3.6058}, all seeds beat the previous champion, all guardrails pass). Artifact `artifacts/autoresearch/t2-extrap-20261001-v1/submission.iter20-qte-time-compmix.seed20260929.h5ad` (median-VALUE seed; sha `8bb6e470…`, full value in log; lowest seed also kept as `…seed20261008.h5ad` sha `dc811606…`); contract = 4 frozen mass exemptions (accepted precedent), NOT registered/uploaded. Previous champion was QTE x compmix +3.464; before this round the best known was x_o2 +1.709.
- Sweep (composite / expr): QTE +2.377/+3.80 · CORAL −4.61 · QTE-quadratic −6.56 · QTE×compmix +3.464/+6.07 · SVD-delta −1.38 · FDR-gated QTE (saturated) · PC-space QTE −0.60 · time-normalized QTE +2.608/+4.17 · time-QTE×compmix **+3.913/+6.30 (KEEP)** · share-trend composition × time-QTE +0.855/**+11.48** (guardrail fail, lead).
- Knowledge: mean-shift family is dead (de pinned at 0.2466 across 7 designs); the MARGINAL is the lever; rank mapping preserves the copula (clip 1.5% vs 17–24%); gene space > PC space > covariance space; two channels compound (1.709→2.377→3.464→3.913); expression headroom ≈2× champion but aggressive composition breaks companion channels.
- Next candidate lead: geometry-preserving aggressive composition (cap each state's share change at the largest observed consecutive-stage change — data-frozen rule, no scan).
- Historical calibration entry: objective = beat local composite champion +1.709 by trying many different algorithms/combinations (user-authorized broad sweep). Calibration table (all 12 server-scored lanes, local composite): x_o2 +1.709, x_n3 +0.931, v0011 +0.030, baseline 0.000, v0012 -0.035, v0016 -0.367, v0013 -0.534, x_r2 -0.769, x_o1 -1.274, x_n2 -1.523, x_r1 -3.183, x_n1 -7.971.
- (Update this section as experiments accumulate: wins, insights, discards + why + revisit bar.)
