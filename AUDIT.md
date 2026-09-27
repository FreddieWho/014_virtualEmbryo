# AUDIT — project scoreboard (GENERATED, do not hand-edit)

Regenerate: `python scripts/generate_audit.py`. Sources: INDEX.tsv + LANE_VERDICTS.tsv + TODO.md.

## Server bests (numeric; selection follows ±0.1 TIE band, incumbent stays)
- T1:val: **51.92** (v0024 five_n1density)
- T2:heart:val_extrap: **50.64** (v0011 g0_t2_r2_shrink)
- T3:gata4: **47.93** (v0048 next_n2hurdle)

Score-pending rows: 12 (v0001/expression_midpoint_unscaled, v0007/t2_s3_l2_spateo, v0008/t2_s3_l2_spateo, v0006/t2_s3_l1_pycpd, v0007/t2_s3_l2_spateo, v0008/j1_fgw_assignment, v0008/b4_t2_r3_l1_damp050, v0009/b4_t2_r3_l2_time1333, v0010/b4_t2_r3_l3_popmix050, v0037/next_r3splfix, v0040/next_r4panelfix, v0041/next_r4medfix)
Boards without scored INDEX rows are omitted above; see reports/SERVER_SCORE_REGISTRY.md.

## Lane verdicts (65 rows in LANE_VERDICTS.tsv)
- SHIPPED: 38
- FAIL: 12
- VOID: 2
- PARKED: 2
- PENDING_SERVER: 2
- GATE_ONLY: 9
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
  - T1-NEXT-R2: decoder damage confirmed (A energy 32x + var collapse) but residual repair only ties strict; no promotion path
  - T1-NEXT-R3: diagonal ties strict; lowrank loses (dir -0.05, energy +21%); two-point linear step is weak link
  - T1-NEXT-R4: module transport collapses (energy 6.79, lib 0.476); A/B identical; train fit already poor
  - T2-E-N1-SBL: pre-declared negation criterion fired: nmmd 0.395969 (L1 gated 127/498 genes) / 0.324687 (L2 ungated) vs do-no

## Current branch (from TODO.md)
- **当前执行分支**：T2 九路线 M0 已冻结（5% 判据 + 父版本 SHA 实核 + 已耗尽轴清单），M1 researcher 检索与设计定稿待启动；T3 八分回填完（v0048 47.93 新 best，Total 157.04；v0037/v0040/v0041 仍待分）；T1-NEXT 全收口（R1 v0023 50.82 selection 在位，R2/R3/R4/R5 诊断关闭，R6 PARKED）。分支详情见“T2 九路线”节与 DECISIONS D-20260927-T2M0FREEZE-001。

Full evidence: reports/LANE_VERDICTS.tsv (per-lane) → run RESULT.md → submissions/INDEX.tsv (scores).
