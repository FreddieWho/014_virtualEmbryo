# AUDIT — project scoreboard (GENERATED, do not hand-edit)

Regenerate: `python scripts/generate_audit.py`. Sources: INDEX.tsv + LANE_VERDICTS.tsv + TODO.md.

## Server bests (numeric; selection follows ±0.1 TIE band, incumbent stays)
- T1:val: **57.99** (v0091 v51_anchor_auto)
- T2:embryo:val_interp: **62.89** (v0014 e_o1_shrinkmerge)
- T2:heart:val_extrap: **51.14** (v0032 x_r5_tshrink09)
- T2:heart:val_interp: **62.48** (v0023 h_aniso50)
- T3:gata4: **53.74** (v0089 resplam15unmask)

Score-pending rows: 6 (v0001/expression_midpoint_unscaled, v0007/t2_s3_l2_spateo, v0008/t2_s3_l2_spateo, v0006/t2_s3_l1_pycpd, v0007/t2_s3_l2_spateo, v0008/j1_fgw_assignment)
Boards without scored INDEX rows are omitted above; see reports/SERVER_SCORE_REGISTRY.md.

## Lane verdicts (198 rows in LANE_VERDICTS.tsv)
- PASS: 6
- SHIPPED: 155
- FAIL: 18
- VOID: 3
- PARKED: 4
- GATE_ONLY: 12
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
  - T3-SIX-20260930-r2: NULL_STATE_MASS_RESPONSE; identity mass, no random pseudo-effect
  - T3-ARCH-B-EMIT1-20261001: withdrawn before upload: extra within-state sampling noise; model unchanged in repair
  - T3-AR-DELIVERY-DRAFT-v0069: Unregistered serialization draft: parent layers/raw missing; X valid and unchanged in repaired delivery
  - T3-DIR6-RIDGE-GEARS-20261002: GEARS mse 0.05747 vs no-change 0.05545 vs ridge 0.05729; dual-gate fail, upgrade closed
  - T1-EXTPRE-20261003: G-return de 0.0189/dir 0.1412 vs standing 0.8868/0.8895; no E10.5 candidate

## Current branch (from TODO.md)
- **当前执行分支**：T1 选择 **v0051=53.92**（AR-MIX/AR-MIX2 八 lane INDEX 补登记完成；v0054 53.98 TIE 备份，v0049 53.72 高备份）；T2 选择胚胎 62.89 / 心脏插值 62.36 / 外推 v0030=51.12（HOLDOUT10 新 best，D-20261003-T2H10SCORE-001；Route C 全 REJECT，v0029 scale 探针 REJECT，v0031 crosswalk REJECT 关闭）；T2 留阶段 10% 新循环已冻结开跑（`artifacts/t2_holdout_10pct_20261003-v1/`，目标归一中位数 ≤0.90，reserve NOT_RUN）；第一轮 15 运行收敛封存，最佳 run10＝0.92868（差 0.029）；HOLDOUT10 五 lane 全部回分：v0030=51.12 现役，v0032 51.14/v0034 51.02 TIE 备份，v0031/v0033 REJECT；T2 待分清零；T3 选择 v0048=47.93（v0070 45.80 REJECT）。待办：① INDEX 回填缺口清零（T1 v0049–v0056 canonical 落盘＋SHA＋contract 全齐）；② 重读门户确认合计（推导 160.64，确认仍 156.06）；③ organizer 答复；④ T1 新用途批准。T2 待分 0（五 lane 全结）。T2 几何新机制第一刀已跑完：心脏插值 RMS 锁定各向异性为 HEART_ONLY_CONTINUE，胚胎因谱差 0.030 关闭（D-20261007-T2GEOM-001/002）。随后用户再给 3 个新预算，四件已回分：心脏插值现役改为 v0023=62.48，v0024/v0035/v0018 REJECT（D-20261007-T2GEOM4SCORE-001）。T1-SIX 六路线已回分：v0058＝53.85 带内 TIE 不晋级（−0.07 vs v0051），其余 5 件 REJECT，T1 待分清零（D-20261007-T1SIXSCORE-001）。

Full evidence: reports/LANE_VERDICTS.tsv (per-lane) → run RESULT.md → submissions/INDEX.tsv (scores).
