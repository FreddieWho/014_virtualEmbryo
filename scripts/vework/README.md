# vework — validation / test-phase recipe harness (2026-10)

Human Team local builders for Virtual Embryo Challenge boards. Companion docs:
`reports/t1_late_anchor_20261008/`, `reports/TEST_PHASE_PLAN.md`.

- `t1ext/` — T1 late-anchor (GSE230531) and OT generative builders
- `t1_recipe.py`, `t1_mix.py`, `t2_recipes.py`, `t3_*.py` — board recipes
- `test_pipeline.py` + `configs/` — end-to-end dry-run / test packaging
- `bt_*.py`, `backtest.py`, `local_eval.py` — local proxies (see FAITHFULNESS.md)

Large artifacts (`*.h5ad`, GEO matrices) are not in git; reconstruct via local
`/workspace/ve/submit` and `ext/GSE230531` (SHA256SUMS under the late-anchor report).
