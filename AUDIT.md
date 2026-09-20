# AUDIT — project scoreboard (GENERATED, do not hand-edit)

Regenerate: `python scripts/generate_audit.py`. Sources: INDEX.tsv + LANE_VERDICTS.tsv + TODO.md.

## Server bests (numeric; selection follows ±0.1 TIE band, incumbent stays)
- T1:val: **48.54** (v0019 g0_t1_r5_c1)
- T2:heart:val_extrap: **50.64** (v0011 g0_t2_r2_shrink)
- T3:gata4: **46.95** (v0014 g0_t3_r2_gradeddose)

Score-pending rows: 9 (v0001/expression_midpoint_unscaled, v0007/t2_s3_l2_spateo, v0008/t2_s3_l2_spateo, v0006/t2_s3_l1_pycpd, v0007/t2_s3_l2_spateo, v0008/j1_fgw_assignment, v0008/b4_t2_r3_l1_damp050, v0009/b4_t2_r3_l2_time1333, v0010/b4_t2_r3_l3_popmix050)
Boards without scored INDEX rows are omitted above; see reports/SERVER_SCORE_REGISTRY.md.

## Lane verdicts (31 rows in LANE_VERDICTS.tsv)
- SHIPPED: 23
- FAIL: 5
- VOID: 1
- PARKED: 1
- GATE_ONLY: 1
- Closed lanes (one-line cause):
  - G1-T1-D1: return de 0.3585/dir 0.6243; var 0.086 collapse
  - G1-T1-D2: void step41 NaN; warmup NaN step88; null-gate concept only
  - G1-T1-D4: G1 de 0.4151/dir 0.5869 both < G0 0.566/0.6127
  - G1-T1-D5: energy 2.203 vs 0.265 (8x); TEST INVALID per audit (dead conditioning+unsatisfiable gate)
  - G1-T1-D5B: energy 7.23 vs 0.265 (27x); severe underfit divergence; baseline reproduced exact
  - G1-T1-D6: de 0.8868=tie (strict fail); dir 0.7921; var 0.26

## Current branch (from TODO.md)
- **当前执行分支**：T1-P2 待定（2026-09-20 起；结构整理三期已执行完；D4/D3/D1/D5/D6/D5b 门 FAIL 已关闭，D2 调参＋D5c 长训仍待用户定夺；GPU 保持关机）。

Full evidence: reports/LANE_VERDICTS.tsv (per-lane) → run RESULT.md → submissions/INDEX.tsv (scores).
