# AUDIT — project scoreboard (GENERATED, do not hand-edit)

Regenerate: `python scripts/generate_audit.py`. Sources: INDEX.tsv + LANE_VERDICTS.tsv + TODO.md.

## Server bests (numeric; selection follows ±0.1 TIE band, incumbent stays)
- T1:val: **52.5** (v0029 round2_n1stack)
- T2:heart:val_extrap: **50.64** (v0011 g0_t2_r2_shrink)
- T2:heart:val_interp: **61.52** (v0014 h_n2_lowamp_shared)
- T3:gata4: **47.93** (v0048 next_n2hurdle)

Score-pending rows: 38 (v0001/expression_midpoint_unscaled, v0007/t2_s3_l2_spateo, v0008/t2_s3_l2_spateo, v0006/t2_s3_l1_pycpd, v0007/t2_s3_l2_spateo, v0008/j1_fgw_assignment, v0008/b4_t2_r3_l1_damp050, v0009/b4_t2_r3_l2_time1333, v0010/b4_t2_r3_l3_popmix050, v0049/round2_n1stack, v0050/round2_n2orth, v0051/round2_n3occup, v0052/round2_o1logit, v0053/round2_o2geneshrink, v0054/three_r1agree, v0055/three_r2damp, v0056/three_r3diffuse, v0034/three_r1compose, v0035/three_r2joint, v0036/three_r3mix, v0011/e_n1_qbridge, v0012/e_n2_trend3, v0013/e_n3_substate2, v0014/e_o1_shrinkmerge, v0015/e_o2_scalmass, v0017/x_n1_lineage, v0018/x_n2_trend3, v0019/x_n3_compmix, v0020/x_o1_trendshrink, v0021/x_o2_shrinkcomp, v0016/h_n1_qbridge, v0017/h_n2_curve95, v0018/h_n3_cmjoin, v0019/h_o1_shrinkmerge, v0020/h_o2_libnorm, v0057/five_select_r2gene, v0058/five_select_r4spline, v0059/five_select_r3bag)
Boards without scored INDEX rows are omitted above; see reports/SERVER_SCORE_REGISTRY.md.

## Lane verdicts (106 rows in LANE_VERDICTS.tsv)
- SHIPPED: 46
- FAIL: 14
- VOID: 2
- PARKED: 4
- PENDING_SERVER: 29
- GATE_ONLY: 11
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
  - T2-H-N2-A2C: anatomical contrast added on top of the proven L2 bridge mean term degrades every distribution-side metric: nm
  - T2-E-I1-TCI: confidence-weighted intra-layer borrowing degrades nmmd 0.970091/0.901227 vs incumbent 0.036362 (+2567.9%/+237

## Current branch (from TODO.md)
- **当前执行分支**：等 T3 v0049–v0053 的服务器分数，优先 v0049。T1 选择已是 v0029=52.5，第二轮队列关闭。T2 没有未跑的已规划路线；低幅度空间项已评分且不晋级。

Full evidence: reports/LANE_VERDICTS.tsv (per-lane) → run RESULT.md → submissions/INDEX.tsv (scores).
