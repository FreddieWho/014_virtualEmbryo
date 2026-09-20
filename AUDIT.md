# AUDIT — project scoreboard (GENERATED, do not hand-edit)

Regenerate: `python scripts/generate_audit.py`. Sources: INDEX.tsv + LANE_VERDICTS.tsv + TODO.md.

## Server bests (numeric; selection follows ±0.1 TIE band, incumbent stays)
- T1:val: **48.54** (v0019 g0_t1_r5_c1)
- T2:heart:val_extrap: **50.64** (v0011 g0_t2_r2_shrink)
- T3:gata4: **46.95** (v0014 g0_t3_r2_gradeddose)

Score-pending rows: 15 (v0001/expression_midpoint_unscaled, v0007/t2_s3_l2_spateo, v0008/t2_s3_l2_spateo, v0006/t2_s3_l1_pycpd, v0007/t2_s3_l2_spateo, v0008/j1_fgw_assignment, v0008/b4_t2_r3_l1_damp050, v0009/b4_t2_r3_l2_time1333, v0010/b4_t2_r3_l3_popmix050, v0034/next_r6meanfix, v0035/next_r6graphfix, v0036/next_r3linfix, v0037/next_r3splfix, v0040/next_r4panelfix, v0041/next_r4medfix)
Boards without scored INDEX rows are omitted above; see reports/SERVER_SCORE_REGISTRY.md.

## Lane verdicts (44 rows in LANE_VERDICTS.tsv)
- SHIPPED: 26
- FAIL: 8
- VOID: 2
- PARKED: 1
- PENDING_SERVER: 3
- GATE_ONLY: 4
- Closed lanes (one-line cause):
  - G1-T1-D1: return de 0.3585/dir 0.6243; var 0.086 collapse
  - G1-T1-D2: void step41 NaN; warmup NaN step88; null-gate concept only
  - G1-T1-D4: G1 de 0.4151/dir 0.5869 both < G0 0.566/0.6127
  - G1-T1-D5: energy 2.203 vs 0.265 (8x); TEST INVALID per audit (dead conditioning+unsatisfiable gate)
  - G1-T1-D5B: energy 7.23 vs 0.265 (27x); severe underfit divergence; baseline reproduced exact
  - G1-T1-D6: de 0.8868=tie (strict fail); dir 0.7921; var 0.26
  - T3-NEXT-R3: FAILED_DISASTER
  - T3-NEXT-R4: FAILED_MAPPING_GATE
  - T3-NEXT-R6: FAILED_DISASTER after gene holdout PASS; both outputs exceed negative clip bound
  - T3-REPAIR-R4-V1: withdrawn before delivery: inference omitted fitted calibration slopes

## Current branch (from TODO.md)
- **当前执行分支**：T3修复首批六候选已打包，等待回分；R6图优势未成立，R3/R4 WT门通过。R5扩链后续，selection不变。见 reports/t3_repairs_20260921/REPORT.md。

Full evidence: reports/LANE_VERDICTS.tsv (per-lane) → run RESULT.md → submissions/INDEX.tsv (scores).
