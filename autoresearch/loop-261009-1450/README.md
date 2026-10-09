# T3 v0088 component iteration loop, 2026-10-09

Bounded autoresearch loop over the v0088 emitter's tunable components.
Metric: skill-weighted composite total for the conditional arm, 7 held-out
genotypes x 3 seeds, replicating the frozen `evaluate_source.py` weights
(de .30 / direction .25 / severity_abs .25 / mmd .12 / variogram .08).
Direction: higher_is_better.

## Layout

- `loop/results.tsv` — iteration ledger (baseline, 14 variants, verdicts)
- `loop/handoff.json` — machine-readable handoff
- `loop/variant.py` — isolated variant builder + evaluator driver
- `loop/summarize.py`, `loop/components.py`, `loop/score.py` — reporting
- `loop/make_eval_adapter.py`, `loop/EVALUATOR_PATH_ADAPTER.json` — path-only adapter receipt
- `variant_results/out_*.json` — per-variant full result payloads

## Method

Each variant copies the archived emitter into its own tree; the frozen
snapshots under `research/t3_20261008/` are never modified. Every variant
applies exactly one substitution, asserted with `count == 1`. The 84-embryo
response cache is emitter-independent and reused across variants.

The rebuilt model was verified byte-identical to the archived inference
assets before the loop started; see `reports/t3_rebuild_20261009/REPORT.md`.

## Result

Baseline 74.737588; best variant `propensity_penalty=0.2` at 74.740974
(+0.003386). `de_skill` is unchanged (+0.00000) across every penalty variant.
Three axes are exact no-ops. The axis is saturated; no variant is recommended
for submission.

## Reproducing

    python loop/variant.py --name <n> --axis <axis> --value <v>

Requires the rebuilt model at `/home/huyudi/vework/rebuilt_model` and the
normalized panels at `/home/huyudi/vework/prepared/source_panel`, both outside
the repository. Rebuild instructions are in `reports/t3_rebuild_20261009/REPORT.md`.