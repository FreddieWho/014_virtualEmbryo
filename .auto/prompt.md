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
- **Primary**: `de_score` (0..1, higher is better) — the optimization target.
  Baseline (parent `submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad`): **0.2466**.
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

## What's Been Tried
- Baseline parent v0001 (locked): de 0.2466 / dir 0.4221 / nmmd 0.20513 / morans 0.8044 /
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
- NOISE DISCIPLINE (binding): resampling designs must report median of 3 seeds before keep; |Δde|<0.005 on deterministic designs = noise, re-run before keep; never add a knob to rescue a no-op axis.
- (Update this section as experiments accumulate: wins, insights, discards + why + revisit bar.)
