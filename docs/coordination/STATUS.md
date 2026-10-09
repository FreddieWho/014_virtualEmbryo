> 2026-10-09 operator-transfer update: three authorized submissions are complete. Heart interpolation v0025 is promoted (official API66.7064); embryo numeric-high v0023 is63.0185 but project incumbent stays v0021 under±0.1; extra v0037 is48.86 UI, not promoted. Official T2 best-per-board mean60.2879, Human71/187. Today7/8 used; remaining1 unauthorized. Full precision/source distinctions: reports/SERVER_SCORE_REGISTRY.md#t2-operator-transfers-2026-10-09.

# 当前并行状态

接手先看 [`../ATOM_MAP.md`](../ATOM_MAP.md) 和 [`../../reports/README.md`](../../reports/README.md)。本文件是并行状态摘要，不是入门读物。2026-10-05 只加了这句导航，没有改下面的选集。

### 2026-10-09 门户合计确认与 per-task 对账关闭

用户确认门户 **Total 172.9**、per-task T1 58.9 / T2 60.3 / T3 53.7；registry 记 Human rank 71/187 @ 09:23:59Z。按现役相加 T1 v0092 58.89 + T2 选集均值 60.2770 + T3 v0088 53.69 = **172.857**，与门户合计在显示精度内一致。**此前记录的 per-task 对不上问题关闭**：根因是选集滞后而非门户口径未知——T1 门户 58.0 对应的是旧现役、T2 59.7 对应的是心插未换人时的选集。门户 T2 用各榜数值最高（embryo v0023 63.0185 + 心插 v0025 66.7064 + 外推 51.1388）/3 = 60.2879，与选集差 0.011 全部来自 ±0.1 带内的两处保留。T2 心插现役由 v0023 62.48 换为 **v0025 h_heart_copula 66.7064**（+4.23，最大单榜跃升）；外推 v0037 零保位移 48.86 REJECT；胚胎 v0023 63.0185 带内不换人。blocks_submission:false。

### 2026-10-09 导航刷新（coordinator 授权）

按 2026-10-08/09 已回填的服务器分刷新三份导航：T1 现役 v0092=58.89、T2 胚胎 v0021=63.0047、T3 v0088=53.69。门户确认合计最后一次读数仍是 171.4（2026-10-08T11:58Z，rank 61），早于 T1 与 T2 胚胎两次易主；现役相加推导 171.45，不是门户值。发现两处需裁决的账目缺口：(1) 门户 per-task 显示值 T1 58.0 / T2 59.7 与现役和 58.89 / 58.87 对不上，仅 T3 53.7 与 53.69 吻合，重读时须核对门户口径；(2) `AUDIT.md` 的数值最高只统计 `score_status=scored`，而 66 行用 `registered`（含 v0092/v0093/v0021），故 AUDIT 印出的 T1 57.99、T2 胚胎 62.89 低于现役——字段不一致而非分数缺失，未擅自改写 INDEX，待裁决。T3 提交额度：registry 记 2026-10-08 用尽当日 8/8 并声明无剩余授权；2026-10-09 T3 无提交记录，当日额度是否已重置未观测，标 OPEN 不宣称可用。blocks_submission:false。

### 2026-10-09 T3 本地重训与成分轴饱和判定

v0088 从公开代码完整重建：v0087/v0088 表达式哈希与 `state_emitter.joblib`/`generic_response.npz`/`expected_donor_rows.npy` 逐位复现，GO embedding 重建为逐字节相同，基线复合分与归档 summary 最大绝对差 0.0。据此 `PUBLIC_REBUILD_FOLLOWUP.md` 的"完整拟合未验证"限制可撤销，公开 clone 不再需要私有 cache。发射器成分轴 14 次迭代：最好变体 `propensity_penalty=0.2` 仅 +0.0034（噪声级），`de_skill` 在全部变体中变化恰为 0，三个轴（composition_clip / propensity_min_cells）为精确 no-op，检测比例轴曲率极陡。判定该轴饱和，**不建议提交任何变体**；T3 本地源侧指标不再是有效目标。服务器现役 v0088 不变。详见 reports/t3_rebuild_20261009/REPORT.md 与 autoresearch/loop-261009-1450/；blocks_submission:false。

### 2026-10-03 T2 新留阶段评价准备

两基础对照×三固定评分种子已完成；仅用E8.25/E8.75构建预测，E9.5留作评价。归一表达误差复制末阶段1.0优于时间均值位移1.16833。新前台循环目标10%或5%待用户确认，未初始化、未新增候选；详见 `reports/t2_holdout_setup_20261003/REPORT.md`；blocks_submission:false。

### 2026-10-03 T2 heart 外推本地优化

独立实验仓库 `artifacts/autoresearch/t2-extrap-20261003-v1/` 已完成目标并释放执行lease；1次实验，固定三种子本地中位数3.913→7.524≥6.0，全部护栏通过。仅尺度项改善且已饱和，表达与其他七项不变。v0029已回分并登记8项、REJECT，当前scale0.9配置关闭；仅尺度项比父版本恶化，局部目标完成不代表服务器改善。contract PASS、artifact不变，服务器现役不变。复盘 `reports/t2_scale_score_review_20261003/REPORT.md`；blocks_submission:false。

本文件是实时摘要。详细候选索引、服务器分数和科学/技术知识分别见权威文件，不在此重复维护完整历史。
人类快速入口是根目录 [`STATUS.md`](../../STATUS.md)；任务路线变更分别见 [`T1_TRACKING.md`](T1_TRACKING.md)、[`T2_TRACKING.md`](T2_TRACKING.md)、[`T3_TRACKING.md`](T3_TRACKING.md)。

<!-- ve-status:start -->
```yaml
schema: ve.parallel-status.v1
updated_at: "2026-10-09"
updated_by: coordinator

policy:
  competition_primary: true
  science_supporting_only: true
  science_gate_for_submission: false
  scored_artifacts_immutable: true
  update_mode: event_driven

workspace:
  integration_branch: master
  worktrees: pending_initial_commit

starter_pack:
  status: CLOSED_FOR_COMPETITION_BASELINE
  research_extension: OPEN_FOR_RESEARCH_EXTENSION
  closure_report: reports/STARTER_PACK_CLOSURE.md
batch1:
  status: CLOSED_FOR_REVIEW
  formal_atoms: 4
  final_artifacts: 16
  server_scored_artifacts: 16
  active_atom: null
  phase_report: reports/PHASE_REPORT_BATCH1_20260829.md
  release_changelog: reports/RELEASE_CHANGELOG_20260829.md
  next_action: "等待新的明确授权；不自动启动 B1-C1 或新的 atom"
batch3:
  status: COMPLETE
  routes_executed: 8
  active_atom: null
  phase_report: reports/PHASE_REPORT_BATCH3_20260904.md
  release_changelog: reports/RELEASE_CHANGELOG_BATCH3_20260904.md
  next_action: "已收口；后续见 batch4"
batch4:
  status: CLOSED_ARCHITECTURE_RESET_REQUIRED
  active_task: null
  completed: "B4-P0 + R1x3 + R2x3 (T1-R2 blocked data, T2-R3 closed unscored); closeout 2026-09-15, D-20260915-B4CLOSE-001"
  floor_parity: "FLOOR_PARITY_UNRESOLVED (T1 exact floor 47.0 == stratified 47.0; T3 exact floor 46.8 > wt_identity 45.3; both below official 50)"
  next_action: "Batch 4 closed; next architecture separate proposal (see reports/ARCHITECTURE_RESET_BRIEF.md)"
data:
  challenge_manifest: data/MANIFEST.tsv
  auxiliary_links: 7
  auxiliary_model_input: false

leaderboard:
  total: 172.9
  total_status: portal_confirmed_2026-10-09_user_transcribed
  per_task_basis: "T1 58.9 / T2 60.3 / T3 53.7, user-confirmed 2026-10-09; sum 172.9. registry records Human rank 71/187 at 2026-10-09T09:23:59Z."
  derived_total: 172.857
  derived_total_status: agrees_with_portal_at_display_precision
  T1: 58.89
  T2: 60.277
  T3: 53.69
  aggregate_basis: "172.9 is the portal-confirmed Total (user transcription 2026-10-09), per-task T1 58.9 / T2 60.3 / T3 53.7. Current board selections: T1 v0092 58.89 (backups v0093 58.22, v0091 57.99), T2 boards 63.0047 / 66.7064 / 51.12 (selection mean 60.2770), T3 v0088 53.69 (v0087 53.42 fallback). Selection sum 172.857 agrees with the portal Total at display precision."
  per_task_reconciliation: "RESOLVED 2026-10-09. Earlier UNRESOLVED flag (portal T1 58.0 / T2 59.7 vs selection sums) was caused by stale selections, not by an unknown portal basis. With T1 at v0092 58.89 and heart_interp promoted to v0025 66.7064, portal per-task matches selection at display precision. Portal T2 uses per-board NUMERIC HIGH: (embryo v0023 63.0185 + heart_interp v0025 66.7064 + extrap 51.1388)/3 = 60.2879 vs selection 60.2770; the 0.011 gap is entirely the two retained-in-band incumbents (embryo v0021 vs v0023, extrap v0030 vs v0032), both inside the ±0.1 rule."
  known_data_gap: "AUDIT.md Server bests under-reports because scripts/generate_audit.py:42 filters score_status=='scored' while 60+ INDEX rows use 'registered' (including v0092/v0093/v0021/v0025, all with real server scores). Field inconsistency, not missing scores. INDEX not rewritten pending coordinator ruling; SERVER_SCORE_REGISTRY.md remains authoritative for scores."
  evidence: reports/SERVER_SCORE_REGISTRY.md

tasks:
  T1:
    status: scored
    dependencies: []
    owner: coordinator
    branch: master
    worktree: current
    current_best: "candidate/T1_val/v0092_ot_gen_v51 (server 58.89, promoted 2026-10-09; v0093 v51_anchor_pergroup 58.22 and v0091 v51_anchor_auto 57.99 backups)"
    current_best_score: 58.89
    next_action: "late-anchor/OT 五 lane 回分完成（v0092=58.89 晋级 +0.90 vs v0091；v0093 58.22 / v0091 57.99 / v0090 53.43 / v0089 53.14；D-20261009-T1LATEANCHOR-001）；现役切到 v0092。混合族（~53.7）与 late-anchor 直用轴均已过平台，下一手需新机制；确认门户选集与 Total。"
    blocker: null
    owned_paths:
      - "submissions/candidates/T1_*"
      - "scripts/t1_temporal_model.py"
      - "tests/test_t1_temporal_model.py"
      - "scripts/t1_mass_residual.py"
      - "tests/test_t1_mass_residual.py"
      - "outputs/t1_model/"
      - "artifacts/atomic_batch1/B1-A3/"

  T2:
    status: active
    dependencies: []
    owner: coordinator
    branch: master
    worktree: current
    current_best: "per-board selection: embryo v0021 e3_scrna_copula 63.0047 + heart_interp v0025 h_heart_copula 66.7064 + heart_extrap v0030 x_r3_medlib09 51.12"
    current_best_score: 60.277
    current_best_score_basis: "board-mean (63.0047+66.7064+51.12)/3=60.2770. Heart interp promoted 2026-10-09 (v0025 copula, +1.6804 vs byte-exact H1 65.0260 and +4.23 vs prior selection v0023 62.48). Embryo retains v0021 under the ±0.1 rule (numeric-high v0023=63.0185, +0.0138). Portal per-task T2 = 60.3."
    next_action: "OPER-TRANSFER 三件已回分：心插 v0025=66.7064 晋级（最大单榜跃升）；胚胎 v0023=63.0185 带内不换人；外推 v0037 零保位移 48.86 REJECT。现役 = v0021 / v0025 / v0030。心插 v0025 与胚胎 v0021 同属 scRNA copula 族，作为优先方向；胚胎侧同族微调的边际收益应按 0.0138 差距估计。外推 existing-route 预算 2/2 已用尽。"
    blocker: null
    owned_paths:
      - "submissions/candidates/T2_*"
      - "scripts/t2_*"
      - "outputs/t2_*"

  T3:
    status: scored
    dependencies: []
    owner: coordinator
    branch: master
    worktree: current
    current_best: "candidate/T3_gata4/v0088_condhurdle; server 53.69, promoted 2026-10-08 (D-20261008-T3CONDHURDLE-001); v0087 53.42 fallback. v0089 resplam15unmask built and packaged, NOT scored, not submitted."
    current_best_score: 53.69
    active_atom: null
    next_action: "v0088 现役保持。2026-10-09 本地重训完整复现 v0087/v0088 表达式与三个推理产物（逐位），GO embedding 亦逐字节相同，PUBLIC_REBUILD_FOLLOWUP 的未验证拟合限制可撤销；基线复合分与归档 summary 差 0.0。发射器成分轴 14 次迭代判定饱和：最好 +0.0034，de_skill 全变体零变化，三个轴精确 no-op，检测比例轴曲率极陡；不建议提交任何变体。本地源侧指标不再是有效目标，下一手需服务器分仲裁（须重新授权）或改响应结构开新路线。reports/t3_rebuild_20261009/REPORT.md。"
    submission_budget: "OPEN/UNVERIFIED. Registry records 2026-10-08 v0088 consumed the separately authorized final one-attempt budget with portal daily T3 usage 8/8. 2026-10-09 has NO T3 submission; whether the daily counter reset was not observed. Do not claim budget availability without user confirmation."
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    owned_paths:
      - "submissions/candidates/T3_*"
      - "scripts/t3_shift_transfer.py"
      - "scripts/t3_signed_response.py"
      - "tests/test_t3_shift_transfer.py"
      - "tests/test_t3_signed_response.py"
      - "artifacts/atomic_batch1/B1-A2/"
      - "outputs/t3_shift_transfer/"

blockers:
  - id: SCIENCE-PROMOTION-001
    scope: science
    blocks_submission: false
    status: open
    reason: "已有 E9.5 组织限定 direct-perturbation context，但仍缺少足以支持 E8.75 state-specific scientific promotion 的独立 signed-family 证据"
    unblock_condition: "获得并验证 E8.0-E9.5 目标状态匹配的独立 signed-family 证据，或明确降低科学声明范围"
    owner: coordinator
  - id: T3-TOOLCHAIN-001
    scope: toolchain_and_external_data
    blocks_submission: false
    status: resolved
    reason: "CellOracle/scTenifoldKnk 方法及 CollecTRI/OmniPath 外部知识快照的本地部署曾缺少固定依赖/审计证据"
    resolution: "用户授权后，固定依赖与必要依赖已 hash-lock；genomepy/CellOracle import、CellOracle mm10 base-GRN 本地 loader、scTenifoldNet 1.4 与 scTenifoldKnk 1.1 source-version match、synthetic smoke、OmniPath/CollecTRI 内容级快照审计均通过；network_used=true；完整 CellOracle runtime 仍单独记录"
    unblock_condition: "若上游版本或快照更新，重新执行相同来源、许可证、schema、mapping、内容和 SHA256 审计"
    owner: coordinator
  - id: T3-S1-PRIOR-GATE-001
    scope: prior_gate_and_scientific_interpretation
    blocks_submission: false
    status: open
    reason: "prior/gate 为 HOLD_AS_COMPONENT；任一模型 family leave-one-out 都移除全部严格双 family consensus，且当前 prior adapter 尚未消费 panel-scoped CollecTRI/OmniPath 生成 beta-catenin sign"
    unblock_condition: "获得独立可重复的 family/stability 证据，并在单独授权的 S1B 路线中完成 panel-scoped snapshot 集成、验证和不确定性记录"
    owner: coordinator
  - id: T3-S1A-RUNTIME-001
    scope: toolchain_and_external_data
    blocks_submission: false
    status: resolved
    reason: "T3-S1A v5 在 exact E8.75 输入和 state join 通过后，CellOracle Gata6/Ctnnb1 的 full matrix simulate_shift 超过 bounded runtime window"
    resolution: "v6 保持 exact 输入、GRN、simulate_shift 参数和 scTenifold 参数不变；CellOracle target 改为独立 fork worker、原子 checkpoint、60 分钟/target 窗口。Gata4 real API PASS；Gata6/Ctnnb1 明确返回 base-GRN regulator 不适用；三条 scTenifold route 输出完成。"
    unblock_condition: "不适用；运行层阻塞已收口，剩余问题转入 T3-S1A-GATE-001"
    owner: coordinator
  - id: T3-S1A-GATE-001
    scope: scientific_validation_and_route_gate
    blocks_submission: false
    status: open
    status: open
    reason: "v7 exact input/state join PASS；S1B v3 已完成 full snapshot identity、external contextual integration、conflict audit 和 family-native LOFO；S1C target-compatible adapter/smoke 已通过方法边界；S1D v3 的三个 E9.5 context 仍非 E8.75 state-matched activity。进一步的 gate 可满足性审计判定旧 target-specific activity 要求与现行 firewall 不具备足够交集，biological activity 仍 NOT_VALIDATED，signed-family stability NOT_IDENTIFIABLE，四条 route 均 HOLD"
    unblock_condition: "获得 organizer/contract-owner 对合法 state-matched evidence 的书面许可，或正式建立新版本 claim/route gate；新版本必须保留 firewall、method、无泄漏和明确的 WT-context 语义，不得用 proxy、降采样或未等价替代解除旧 gate"
    owner: coordinator

leases: []
handoffs:
  - task: T1+T3
    atom: B4-P0-STATE-FLOOR-PARITY
    status: COMPLETE_FLOOR_PARITY_UNRESOLVED
    final_artifacts: 2
    candidate_ids: "T1:val v0009 b4p0_l0_exact_floor (47.0)；T3:gata4 v0008 b4p0_l0_exact_floor (46.8)；详见 submissions/INDEX.tsv"
    parents: "官方 floor 语义（无模型 parent）；参照 baseline-001 v0001"
    artifacts: "artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/；canonical 候选与 SHA256 以 submissions/INDEX.tsv 为准"
    checks: "protected checks 全 PASS（行身份/原始行序/表达与坐标逐值一致、重跑字节一致）；scorer smoke 仅链路验证；2/2 已人工上传并评分"
    risks: "官方 floor 行子集规则不公开；T1 两种不同子集规则同得 47.0（分层被排除）；剩余假设 pred n_obs 或 bundle 级差异；本地 smoke 不构成 leaderboard 预测"
    recommended_decision: "T3 v0008 晋级 board best（基准改 46.8）；T1 selection 不变；FLOOR_PARITY_UNRESOLVED 开启；Wave 1 待授权"
    blocker: "FLOOR_PARITY_UNRESOLVED; blocks_submission: false"
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；不自动上传；等待 Wave 1 授权"
  - task: T1
    atom: B4-P0-T1-FLOOR-PROBE2
    status: SCORED_N_OBS_EXCLUDED
    final_artifacts: 1
    candidate_ids: "T1:val v0010 b4p0_l0floor_n1706 (46.8)；详见 submissions/INDEX.tsv"
    parents: "官方 floor 语义（无模型 parent）；同一种子均匀抽样，n=1,706"
    artifacts: "artifacts/batch4/B4-P0-T1-FLOOR-PROBE2-20260904-v1/；SHA256 以 submissions/INDEX.tsv 为准"
    checks: "protected checks 全 PASS（1706 行、panel 顺序、逐值精确一致、重跑字节一致）；scorer smoke 仅链路验证；已人工上传并评分"
    risks: "官方 floor 构造仍不公开；本地 smoke 不构成 leaderboard 预测"
    recommended_decision: "n_obs 被排除；T1 selection 不变；Wave 1 可按 provisional-score 身份继续"
    blocker: "FLOOR_PARITY_UNRESOLVED; blocks_submission: false"
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；等待 Wave 1 授权"
  - task: T3
    atom: B4-T3-R1-GENOTYPE-ONLY-ABLATION
    status: SCORED_NEW_BOARD_BEST_TIED
    final_artifacts: 2
    candidate_ids: "T3:gata4 v0009 b4_t3_r1_l1_gata4_zero_all (46.95); v0010 b4_t3_r1_l2_gata4_zero_hard (46.95);详见 submissions/INDEX.tsv"
    parents: "v0008 exact floor (provisional); frozen B2-T3-A1 lineage_gate"
    artifacts: "artifacts/batch4/B4-T3-R1-GENOTYPE-ONLY-ABLATION-20260905-v1/；SHA256 以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract pass、坐标/行序/n_obs/Gata6未动逐位一致；10 子项已入库"
    risks: "L3 BLOCKED_CONDITION_NOT_CONFIRMED（非阻塞）；增益为构造效应，非机制证据"
    recommended_decision: "双 lane 并列晋级 board best；derived Total≈151.40 待确认"
    blocker: null
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；等待 Wave 2 或封板授权"
  - task: T1
    atom: B4-T1-R1-CONSERVATIVE-FAMILY
    status: SCORED_NO_PROMOTION
    final_artifacts: 4
    candidate_ids: "T1:val v0011 (47.58); v0012 (47.77); v0013 (47.85, family best); v0014 (46.90);详见 submissions/INDEX.tsv"
    parents: "v0004 recipe / v0009 pool / moscot mass"
    artifacts: "artifacts/batch4/B4-T1-R1-CONSERVATIVE-FAMILY-20260904-v1/；SHA256 以 submissions/INDEX.tsv 为准"
    checks: "L1/L2 contract PASS；L3/L4 FAIL_BY_DESIGN_ACCEPTED（obs-identity only）；16 子项已入库"
    risks: "v0014 低于 floor；本地 pseudo 分数偏高未兑现"
    recommended_decision: "v0004 留任；保守族晋级路线关闭"
    blocker: null
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；等待 Wave 2 或封板授权"
  - task: T2
    atom: B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE
    status: SCORED_THREE_PROMOTIONS
    final_artifacts: 4
    candidate_ids: "T2:embryo v0009 (61.79); v0010 (62.29 best); T2:heart v0012 (56.27 rej); v0013 (62.04 best);详见 submissions/INDEX.tsv"
    parents: "embryo v0002 scale; heart v0009 FGW; frozen brackets E7.25/E8.0 and E8.25/E8.75"
    artifacts: "artifacts/batch4/B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE-20260911-v1/；SHA256 以 submissions/INDEX.tsv 为准"
    checks: "L1双PASS、L2双FAIL_BY_DESIGN_ACCEPTED；字节确定；42子项中T2占32已入库"
    risks: "heart 60% clip已披露无collapse；本地pseudo循环性已声明"
    recommended_decision: "embryo v0010、heart v0013晋级selection；T2-R3另日起跑；机械组合run许可待评估"
    blocker: null
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；等待 Total 确认与 T2-R3 授权"
  - task: T3
    atom: B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR
    status: SCORED_ARCHITECTURE_RESET_REQUIRED
    final_artifacts: 2
    candidate_ids: "T3:gata4 v0011 (46.45); v0012 (46.47);详见 submissions/INDEX.tsv"
    parents: "v0008 exact floor; WT ladder E8.25/E8.75/E9.5; frozen p_mesp1"
    artifacts: "artifacts/batch4/B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR-20260911-v1/；SHA256 以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract PASS、逐位一致、字节确定；10子项已入库"
    risks: "仅5/33 states有方向；增益为构造效应"
    recommended_decision: "T3标ARCHITECTURE_RESET_REQUIRED；selection保持46.95；Batch4内不追加手工路线"
    blocker: "ARCHITECTURE_RESET_REQUIRED; blocks_submission: false"
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；等待 closeout"
  - task: T2
    atom: B4-T2-R1-FGW-ASSIGNMENT-REPAIR
    status: SCORED_TIED_NO_PROMOTION
    final_artifacts: 2
    candidate_ids: "T2:heart:val_interp v0010 b4_t2_r1_l1_globalmatch (57.3); v0011 b4_t2_r1_l2_globalmatch (57.31);详见 submissions/INDEX.tsv"
    parents: "v0007 t2_s3_l1_pycpd（与 v0009 相同 parent）；frozen FGW problem 4a957da5"
    artifacts: "artifacts/batch4/B4-T2-R1-FGW-ASSIGNMENT-REPAIR-20260904-v1/；SHA256 以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract pass、protected PASS、字节确定；本地 NFS/Moran/objective 全优但 board 打平；16 子项已入库"
    risks: "proxy 乐观偏差再添一例；两 lane 服务器不可区分（差 0.01）"
    recommended_decision: "TIE 不晋级，v0009 留任；关闭 FGW 离散化微调；Wave 1 其余待授权"
    blocker: null
    action: "分数已回填 registry/INDEX/DECISIONS/TRACKING；16 子项已入库；等待 Wave 1 其余授权"
  - task: T2
    atom: B1-A1
    status: complete
    final_artifacts: 6
    candidate_ids: "见 submissions/INDEX.tsv 与 docs/coordination/DECISIONS.md 的 D-20260827-001"
    parents: "embryo/extrap: baseline-001；heart interpolation: submission-002/v0002"
    artifacts: "六个路径与 SHA256 以 submissions/INDEX.tsv 为准"
    checks: "6/6 contract pass；X、obs/var order、空间 shape、15-NN 全通过；target_used=false；服务器分数 6/6 已登记"
    risks: "heart extrapolation 两条 lane 均低于 parent；不作因果声明"
    recommended_decision: "L1 按 board 保留；L2 作为同批已评分第二候选和审计备份保留"
    blocker: null
    action: "B1-A1 完成；后续转入经授权的新 atom"
  - task: T3
    atom: B1-A2
    status: diagnostic_hold
    final_artifacts: 2
    candidate_ids: "B1-A2-L1-T3_gata4, B1-A2-L2-T3_gata4；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T3_gata4/v0001"
    artifacts: "artifacts/atomic_batch1/B1-A2/final/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract/invariant pass；7,449×500；target_used=false；上传文件 SHA256 与索引一致；Mab21l2 self-check 与公开 proxy 已完成；服务器 2/2 已登记"
    risks: "两条 WT-only signed-response 路线均低于 baseline；L1=44.7，L2=44.0；self-check 与公开代理显示响应方向和分布损伤"
    recommended_decision: "保留两份不可变候选供失败诊断；不进入 B1-A3，不新增候选"
    blocker: null
    action: "B1-A2 失败原因已归档；保持 T3 diagnostic_hold，不新增候选"
  - task: T2
    atom: B1-A4
    status: complete
    final_artifacts: 6
    candidate_ids: "B1-A4 双 lane × 三 board；详见 submissions/INDEX.tsv"
    parents: "B1-A1 immediate parents；heart extrapolation 使用 baseline-001"
    artifacts: "artifacts/atomic_batch1/B1-A4/final/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "6/6 manifest/schema/invariant pass；X/layers/raw/obs replay、坐标、15-NN、SHA256 均通过；local public proxy 6/6 complete；服务器 6/6 scored；target_used=false"
    risks: "服务器结果为 embryo 59.3/59.2、heart interpolation 56.3/56.3、heart extrapolation 50.0/49.9；仅 heart interpolation 持平当前 best，其余低于当前 best"
    recommended_decision: "六份 scored artifact 保持不可变；不提升 B1-A4，不追加 C1 重复缩放或新的 T2 atom"
    blocker: null
    action: "B1-A4 评分已回填 reports/SERVER_SCORE_REGISTRY.md；维持当前 per-board selection，等待新的授权"
  - task: T1
    atom: B1-A3
    status: complete
    final_artifacts: 2
    candidate_ids: "B1-A3-L1_SHARED_UNRESOLVED-T1_val, B1-A3-L2_E95_EXPRESSION_PROBE-T1_val；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T1_val/v0001"
    artifacts: "artifacts/atomic_batch1/B1-A3/final/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract/protected checks pass；5,118×32,285；source-only partition coverage 100%；target_used=false；row replay exact"
    risks: "E8.5/E9.5 label vocabulary is not harmonised；L2 expression projection is a source-only hypothesis；locked full-panel local scorer timed out on L1；L2 attempt produced no result and was interrupted；no substitute scorer"
    recommended_decision: "L2=47.7 高于 L1=47.5，为 B1-A3 lane winner；两者均低于历史 v0004=48.5，保留两份 artifact 不可变"
    blocker: "local_scorer_incomplete; blocks_submission: false"
    action: "B1-A3 完成；新授权 atom 前不追加 T1 调参"
  - task: T3
    atom: B2-T3-A1
    status: HOLD_AS_COMPONENT
    final_artifacts: 2
    candidate_ids: "B2-T3-A1-L1_STRICT_WT_DIRECT-20260830, B2-T3-A1-L2_GATA4_GATA6_CONDITION_AWARE-20260830；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T3_gata4/v0001"
    artifacts: "artifacts/atomic_batch2/B2-T3-A1/；canonical candidate 与 SHA256 以 submissions/INDEX.tsv 为准"
    checks: "2/2 7,449×500 contract/protected PASS；Gata4/Gata6 lineage gate；target_used=false；每 lane 一次 local scorer；manual-upload package 已生成"
    risks: "E-MTAB-11763 为 metadata-only fallback；CellOracle/scTenifoldKnk 为本地可审计近似实现而非上游包执行；local 分数是 Mab21l2 source-only 诊断，不是 Gata4 leaderboard 分数"
    recommended_decision: "两条均保持 score_pending，不自动上传；作为独立 component 候选等待人工选择"
    blocker: null
    action: "停止在 B2-T3-A1；不启动下一个 atom，等待人工上传决定或新授权"
  - task: T3
    atom: B2-T3-A1 (scoring round)
    status: SCORED_TIED_BOARD_BEST
    final_artifacts: 2
    candidate_ids: "B2-T3-A1 v0006 (45.5) / v0007 (45.5)；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T3_gata4/v0001 (wt_identity 45.3)"
    artifacts: "submissions/candidates/T3_gata4/v0006_b2_t3_a1_l1/、v0007_b2_t3_a1_l2/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract/protected PASS（此前已记录）；服务器 45.5/45.5，并列新 board best，首次超过 wt_identity；derived T3=45.5/Total≈149.7 待服务器页面确认"
    risks: "两 lane 服务器无法区分（tie），不声称 lane 偏好；local source-only 诊断曾偏低（de_score 0.1884）与服务器 +0.2 并存，诊断不可作 leaderboard 预测；科学 gate 不变，leaderboard 增益不构成机制证据"
    recommended_decision: "并列晋级当前 selection；v0002–v0005 五条历史候选保持不可变淘汰记录"
    blocker: null
    action: "分数回填完成；科学 promotion gate 维持 CLOSED_AS_RESEARCH_COMPONENT，重开条件见收口报告 §6"
  - task: T3
    atom: T3-S1-PRIOR
    status: HOLD_AS_COMPONENT
    final_artifacts: 4
    candidate_ids: "none；本任务仅 prior/gate bundle，不生成候选"
    parents: "P0-LOCK；复用 immutable artifacts/atomic_batch2/B2-T3-A1"
    current_artifacts: "T3-S1-PRIOR MANIFEST SHA256 7ed19bda38b6362da1bb1051c865ca362cc33b53aa52bb831e32313c1447bc35；gate_report SHA256 69c1ffbd25039cb467865f2d7670c58dce58a7fe3efa48cba1e00195761f25e1；contract-preflight SHA256 67c38f32c4576b31a5b516495e046a7f0017d989217fe182ef9694bcec79c2a5；T3-S1B knowledge preflight SHA256 a41db892e852d9da794277eb8093c0bbfba7b52cc04d45bd4f93751dcda21632；stability preflight SHA256 3f96627ffa866c0ad17d51537f08c0ed7a36db8f06c4664f08b3fff6685213c8"
    current_checks: "5 个 current parent contract/registry SHA256、protected-field 和 round-trip PASS；实际 contract/interface tests 22 passed；deployment 与双源 snapshot audit PASS；directed integration preflight COMPONENT_PASS 但 candidate admission HOLD；scientific validation NOT_RUN；prior gate HOLD"
    historical_artifacts: "artifacts/tool_integration/T3-S1-PRIOR/；MANIFEST.json SHA256 30100e641107fc283dc0cb3275a9ec9205b989dae751f070cd87a2c9cb0a11b8；deployment_report.json SHA256 63d43571b85b5f711bedb460611ed671fd217b06f109ea45af8c79a52889ffa8；gate_report.json SHA256 4145bb01f7dfda28d0f80c8ad97ca50dc78c6a5ffe62b63fbecbe9b0bbaf32d5"
    historical_checks: "deployment PASS；genomepy/CellOracle import PASS；scTenifoldNet 1.4 与 scTenifoldKnk 1.1 source-version match；synthetic smoke PASS；CollecTRI 4,910 与 OmniPath 2,553 directed edges 内容级审计 PASS；接口测试 11 passed；输入锁定哈希全部匹配"
    risks: "gate HOLD_AS_COMPONENT；PASS_WITH_SENSITIVITY，移除任一 model family 后严格双 family consensus 全部消失；外部 edge 与现有模型族存在方向 discordance，且尚无 state-specific activity 验证；无 beta-catenin 生物学结论"
    recommended_decision: "contract 与外部 directed-evidence preflight 已闭合为可复用组件；仍不生成 H5AD/候选，不上传；若继续，单独激活 S1B state join、冲突处理和独立稳定性验证"
    blocker: "T3-S1-PRIOR-GATE-001; blocks_submission: false"
    action: "T3-S1-PRIOR 完成当前边界；最终 provenance-snapshot 版 contract-preflight、directed-evidence preflight 和 stability reinforcement 已写入；等待独立 stability 证据与 S1B 路线授权"
  - task: T3
    atom: T3-S1A-STATE-JOIN-20260901-v6
    status: BLOCKED
    final_artifacts: 5
    candidate_ids: "none；本 atom 仅执行 exact input/method/gate，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260831-v5；T3-S1-PRIOR immutable inputs"
    current_artifacts: "tool_execution.json SHA256 3dec70dc5bb9f1a4ffab747962768846ce650dc730c5ca1c5cc50e3b18c4d988；gate_report.v2.repaired.json SHA256 92560f5d2b5caf49b8a0160d2828fb7dcb4a591a859702c16d0a0ad03087481b；artifact_manifest.stable.json SHA256 ff0d8f323f2da369b26c5c9553ea9d230eb9804b88a7fe82cf06e4daeee16e30；route_artifact_repair.json SHA256 046c17369a51c043bb7fedb8ada8952a912501138710fa4cde9794ae75b6e03e；Gata4_votes.tsv SHA256 7d08cb82326b91c6ff5ceb2121026a3d8097f8174d36e8078a608a5eea6de724"
    current_checks: "exact input/state join PASS；Gata4 CellOracle real API PASS；Gata6/Ctnnb1 当前 base GRN 明确不适用；三条 scTenifold 输出完成；45 个接口/状态测试 PASS；py_compile PASS；修复后 hash-bound route audit PASS；全局 outcome/status BLOCKED，四路为 2 HOLD + 2 BLOCKED"
    risks: "state activity 为 NOT_VALIDATED；selected-gene/evidence-family stability 不可识别；v6 历史报告保留 Gata6/Ctnnb1 的实际 BLOCKED_TOOLCHAIN 标签；不能据此生成候选或宣称 leaderboard 改进"
    recommended_decision: "接受 v6 作为运行阻塞修复和审计组件；保持 candidate_generation/server_submission 关闭，后续单独解决 target-compatible GRN/applicability 与 state-specific activity/stability"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；等待下一项明确授权"
  - task: T3
    atom: T3-S1A-STATE-JOIN-20260901-v7
    status: HOLD_AS_COMPONENT
    final_artifacts: 8
    candidate_ids: "none；本 atom 仅完成 exact state-response/coverage 与 route gate 复核，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v6；T3-S1-PRIOR immutable inputs"
    current_artifacts: "tool_execution.json SHA256 368da3d484da99ef6227a7a8078b8fcc3c2c792377ea670fe985c678641eb15b；gate_report.v2.repaired.json SHA256 dfe522011bc3c198d30fc9f483f3b6e8842922c4f1f596713c7762c80095c8e5；artifact_manifest.stable.json SHA256 22d785ea59a85d13529db8896772ccdee5f79b95c4cd557bfabfff0897109db8；route_artifact_repair.json SHA256 6c2302c371cd3bf38cc96239a8847cb7bc22849fcb8e219fd79f1c8b2c129e3a；state_response_support.json SHA256 1bc9dfdb74ac386dbcd9de84919855199fb4c5ec384725cf3976f78ef964964c；Gata4_votes.tsv SHA256 8f0e3ba674b6bad13912905c66f3e37569e6edc8d624b0851fd2e121ff242578；Gata4_state_response.tsv SHA256 36588d3912264256469acbd868af8631af9595286d8d56460a92ea60884f56a2；Gata4_state_coverage.tsv SHA256 fd0c5a040753c3d7e4d4ea54ba0e5e7884dd3fdd202bfe5a00b2d74211ebd997；deployment manifest SHA256 8ee0fd511f8b03d4ea4e09bd9d1348beb7da49bec266640dd5fdacbcbc30a949"
    current_checks: "exact input/state join PASS；CellOracle PASS（Gata4=PASS，Gata6/Ctnnb1=NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT）；三条 scTenifold 输出均 PASS_UNSIGNED_RANK_ONLY；state-response support 为 NOT_IDENTIFIABLE（23 个 required mapped states 中 12 个通过、11 个 HOLD），claim=MODELLED_STATE_RESPONSE_ONLY，biological_activity=NOT_VALIDATED；GATA selected-gene stability PASS、BETA 因无适用 CellOracle target 保持不可识别；48 项接口/状态测试 PASS；py_compile PASS；223-file stable manifest 无 transient；hash-bound route audit PASS；全局 HOLD_AS_COMPONENT，四路均 HOLD"
    risks: "仍缺 biological activity 验证；Gata4 state response 只支持 modelled response，且存在映射碰撞与 11/23 mapped state 的 within-state sign stability 缺口；scTenifold 仅 unsigned rank evidence；Gata6/Ctnnb1 当前 base GRN 不适用；不能据此生成候选或宣称 leaderboard 改进"
    recommended_decision: "接受 v7 作为 applicability、state-response coverage 和 route-gate 审计组件；保持 candidate_generation/server_submission 关闭，后续仅在 target-compatible GRN 或独立 activity/stability 证据明确后复核"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；下一步处理可审计的 biological activity/stability 证据边界"
  - task: T3
    atom: T3-S1B-STATE-JOIN-20260901-v2
    status: HOLD_AS_COMPONENT
    final_artifacts: 27
    candidate_ids: "none；本 atom 仅完成 external contextual integration、conflict audit、LOFO 与四路 claim vector，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7"
    current_artifacts: "artifact_manifest.stable.json SHA256 239e5c474986cb54e70d5b1451330a20350be38fadaf7641c1e2177b2aea34ea；gate_report.v2.json SHA256 1d10e15b2be52eddd9693cbf84791e0ba66614359468c5708b844b96254f89f0；state_join_audit.json SHA256 0c5dc8bc03419e678b842ffa5dc82c2050626d795c77d0ff7e884d7d5f58e366；stability_s1b.json SHA256 19c32d6b65778a8696d1699055791f15e4ceab6e47679e8d88f8481f3de23c64；source_votes.tsv SHA256 fb26e8424a270f48a3fc7cbd6650e395edaedaea007a4cd3ebe499a4680c4a7e"
    current_checks: "parent 223-file stable manifest 与 CollecTRI/OmniPath full snapshot identity PASS；external raw 128、state-joined 5808、source 137148；external 全部 GLOBAL_CONTEXTUAL/SUPPORTING_KNOWLEDGE 且 activity_eligible=false；4/4 route HOLD、selected signed records=0；53 项回归测试 PASS；stable manifest 自校验 PASS"
    risks: "S1B 不是 biological activity validation；external evidence 不计为 independent signed family；9 个 external-state mapping collision 保留在 audit；Gata6/Ctnnb1 不会因 contextual evidence 恢复为 CellOracle-applicable；S1B v1 的封装失败 receipt 保留但不可复用"
    recommended_decision: "接受 v2 为可复用的 contextual/provenance 审计组件；保持 candidate_generation/server_submission 关闭，不写入 submissions/INDEX.tsv 或服务器 registry"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；下一步只处理独立 biological activity/stability 证据或另行授权 target-compatible GRN atom"
  - task: T3
    atom: T3-S1B-STATE-JOIN-20260901-v3
    status: HOLD_AS_COMPONENT
    final_artifacts: 27
    candidate_ids: "none；本 atom 仅完成 external contextual integration、conflict audit、LOFO 与 provenance lock，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7"
    current_artifacts: "artifact_manifest.stable.json SHA256 396b15d976e10700709c7628539dd2e9cac21b66612d9b72faa772921413744e；gate_report.v2.json SHA256 a4be63a1653353b238ce5cb29436cea834e438d9b2a3a3e85cb467d121d00e21；implementation SHA256 cd480790fa6cbf7e6618ec28675983143466788847e79e73040d63df7dfe9d8c；input_lock.json SHA256 7920f7f960cb298d5deabb6e30b298f16480b89b2054eae976514be51f519859"
    current_checks: "parent 223-file stable manifest 与 CollecTRI/OmniPath full snapshot identity PASS；external raw 128、state-joined 5808、source 137148；external 全部 GLOBAL_CONTEXTUAL/SUPPORTING_KNOWLEDGE 且 activity_eligible=false；4/4 route HOLD、selected signed records=0；53 项回归测试 PASS；独立 tester 5 S1B + 34 interface tests PASS；script/artifact/input lock SHA 一致；stable manifest 自校验 PASS"
    risks: "biological_activity_status=NOT_VALIDATED；signed-family stability=NOT_IDENTIFIABLE；external evidence 不计为 independent signed family；9 个 external-state mapping collision 保留在 audit；Git commit 锚点仍不可用"
    recommended_decision: "接受 v3 为当前可复用审计组件；保持 candidate_generation/server_submission 关闭，不写入 submissions/INDEX.tsv 或服务器 registry"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；下一步只处理独立 biological activity/stability 证据或另行授权 target-compatible GRN atom"
  - task: T3
    atom: T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1
    status: PASS_COMPONENT_HOLD
    final_artifacts: 11
    candidate_ids: "none；本 atom 仅构建 target-compatible TFdict adapter，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3"
    current_artifacts: "artifact_manifest.stable.json SHA256 6700b919cba382475cbd6a1c3bee0dd8af5271685285c18011c4e3bab8e8706c；augmented_tfdict.json SHA256 29ecc5bf4c4ff24ee5adf8c7ca6dfe14fb6026eb49678c9c3f8cdc9953785050"
    current_checks: "Gata4/Gata6/Ctnnb1 source membership 3/3 PASS；Gata6 18 个一跳 CollecTRI relation、Ctnnb1 1 个严格一跳 OmniPath relation；clean rerun payload 哈希一致；method_source_compatibility=PASS"
    risks: "仅证明接口/source membership；biological_activity=NOT_VALIDATED、state_specificity=NOT_EVALUATED、signed_family_stability=NOT_IDENTIFIABLE；不把外部 sign 注入 TFdict"
    recommended_decision: "接受为可复用方法组件；不直接进入 S1A/S1B biological gate，不生成候选、不上传"
    action: "等待 matched activity/stability 证据后另行授权 exact E8.75 full rerun"
  - task: T3
    atom: T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v2
    status: PASS_COMPONENT_HOLD
    final_artifacts: 7
    candidate_ids: "none；本 atom 仅执行 synthetic structural smoke，不生成候选"
    parents: "T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1"
    current_artifacts: "artifact_manifest.stable.json SHA256 806bf41acadfb9b5dc0d0b2329b36e1848b390231c573edcf8ec5e8e8ac0c817；target_results.json"
    current_checks: "真实 CellOracle 0.22.0 TFdict import/fit/simulate；Gata6/Ctnnb1 2/2 PASS；各 24×20、delta_x finite；runtime cache/config 写入 atom 内"
    risks: "synthetic fixture 无生物样本、sign、rank 或 state response；S1C-B/v1 Gata4 fixture 边界失败 receipt 保留且不可复用"
    recommended_decision: "接受 v2 为 source adapter smoke 组件；不作 activity 或模型效果证据"
    action: "不生成 H5AD/候选、不运行 scorer、不上传"
  - task: T3
    atom: T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1
    status: HOLD_INSUFFICIENT_MATCHED_ACTIVITY_EVIDENCE
    final_artifacts: 8
    candidate_ids: "none；本 atom 仅审计外部 perturbation context，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3"
    current_artifacts: "artifact_manifest.stable.json SHA256 9017b2db83c09a776c8c1620f8ca00c6740f3c1d288ed857d9635c1b30f42fdf；processed_effects.json；evidence_inventory.tsv"
    current_checks: "GSE156307 Gata4 E14.5 HS log2FC=-1.1839、5/5 方向一致；GSE255237 Gata6 E11.5 OFT log2FC=-0.3362、4/4 方向一致；metadata PASS；E8.75 matched activity NOT_IDENTIFIABLE；independent signed family=0"
    risks: "两个 processed 文件均为 off-target stage/tissue；GSE255237 存在系列设计与文件列数冲突；raw 未下载；不能迁移为 E8.75 sign/activity 或 server improvement"
    recommended_decision: "接受为 context-only 证据，保持全局 HOLD_AS_COMPONENT；不写入 challenge input、submissions/INDEX.tsv 或 server registry"
    action: "继续寻找 E8.0-E9.5 matched tissue/state 且至少两个 biological replicates 的 target-specific perturbation"
  - task: T3
    atom: T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3
    status: PASS_COMPONENT_HOLD
    final_artifacts: 7
    candidate_ids: "none；本 atom 仅执行 synthetic structural smoke，不生成候选"
    parents: "T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1"
    current_artifacts: "artifact_manifest.stable.json SHA256 7770e075838309af5d339506b02e7975459aa651deb8d10f4079f25fec9c822d；target_results.json"
    current_checks: "真实 CellOracle 0.22.0 TFdict import/fit/simulate；Gata6/Ctnnb1 2/2 PASS；各 24×20、delta_x finite；进程退出后 stable manifest 7/7 文件 bytes/SHA PASS；runtime cache/mpl/numba 与 SQLite sidecar 明确排除"
    risks: "synthetic fixture 无生物样本、sign、rank 或 state response；v1/v2 失败或不可复用 receipt 保留且不可作为当前版本"
    recommended_decision: "接受 v3 为 source adapter smoke 组件；不作 activity 或模型效果证据"
    action: "不生成 H5AD/候选、不运行 scorer、不上传"
  - task: T3
    atom: T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3
    status: HOLD_EXACT_STAGE_CONTEXTUAL_ACTIVITY_NOT_STATE_MATCHED
    final_artifacts: 14
    candidate_ids: "none；本 atom 仅审计 exact-stage 外部 perturbation context，不生成候选"
    parents: "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v2；T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3"
    current_artifacts: "artifact_manifest.stable.json SHA256 6c2806aa381f099e3db88f38a35278d4500e1aeb1f8de7fe3cfa20e2db487e0c；gate_report.json SHA256 3da93e810aadf90769eb8e2eac1fd1fd35b41d9a3737aa01350bb1187e9c2579；contract SHA256 3cafa6d040caec2110a304cb260ef0c4a574aed51292748aff2aa017e3fd8267"
    current_checks: "GSE5298/GSE9652/GSE78125 matrix gzip、45101x8/45101x11/35556x24 shape、GSM group identity、GPL1261/GPL6246 probe/Entrez mapping PASS；Gata4 two early families、Ctnnb1 one AHF family、Gata6 zero；4 targeted tests PASS；核心输出 deterministic rerun PASS"
    risks: "E9.5 AVC/pooled heart/AHF tissue context 不能外推为 E8.75 state-specific activity；Gata4/Ctnnb1 target probe expression 不作为 functional gate；无 state-specific signed gene set 或 independent signed-family stability；无 raw CEL；不能宣称候选或 leaderboard 改善"
    recommended_decision: "接受 v3 为 exact-stage contextual evidence 组件；v2 初步原子保留但不复用；不写入 challenge input、submissions/INDEX.tsv 或 server registry"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "继续寻找真正 E8.0-E9.5、目标状态匹配且可复现的 signed-family 证据；在此之前不启动 E8.75 全量推断"
  - task: T3
    atom: T3-S1-CLOSURE-20260902-v1
    status: CLOSED_AS_RESEARCH_COMPONENT
    final_artifacts: 1
    candidate_ids: "none；纯文档收口，无新计算"
    parents: "T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3；T3-S1C-A/v1；T3-S1C-B/v3；T3-S1D/v3"
    current_artifacts: "artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md"
    current_checks: "五组件证据链 SHA 抄录完毕；三条未满足硬条件（signed family<2、E8.75 activity NOT_IDENTIFIABLE、stability 未闭合）与最小解锁条件已写死；与同日 T3-S1C-GATE-SATISFIABILITY 的 UNSATISFIABLE_UNDER_FIREWALL 结论一致"
    risks: "无；不改变任何已登记分数与历史 artifact；T3 best 仍为 45.3"
    recommended_decision: "接受收口；重开条件见 CLOSURE_REPORT 第 6 节；执行资源切换 T1-PRE-HARMONIZE"
    blocker: null
    action: "不生成 H5AD/候选、不运行 scorer、不上传；blocks_submission: false"
  - task: T1
    atom: T1-PRE-HARMONIZE-20260902-v1
    status: STATE_GATE_PASS_AND_FULL_PANEL_SCORER_PASS
    final_artifacts: 15
    candidate_ids: "none；本 atom 只建立词表/crosswalk/验证链，不生成正式候选"
    parents: "P0-LOCK；parent candidate/T1_val/v0004_strict_pseudobulk_shift（只读，SHA 与 P0-LOCK 一致）"
    current_artifacts: "artifacts/tool_integration/T1-PRE-HARMONIZE-20260902-v1/；stable manifest SHA256 e2f2889081d8bfffffe3111eb8cd024882c98d3304519618a964518b74698413；实现脚本 scripts/t1_pre_harmonize.py SHA256 5c2fed4c3d5c941819170dcf21d08dd540d38abb07c52347ff530318120add75"
    current_checks: "28 个 union fine_state（11 SHARED_EXACT/7 SOURCE_ONLY/10 TARGET_ONLY）；crosswalk 前向 13/18 解析、5 UNRESOLVED，反向 3/10、7 UNRESOLVED，无强配；stability 预声明一次（非 exact 边 bootstrap 0.40-0.50 已如实记录）；source-only pseudo-holdout projection 经锁定 full-panel scorer 实测 exit 0、323s、meta 三项校验全过；15 项新测试+103 全量回归 PASS；未触 E10.5/E12.5"
    risks: "pseudo-holdout 分数（de_score 0.6226）只验证表示与验证链，不是 leaderboard preview；wrapper 首版 RSS 采样只覆盖 supervisor 进程（已修为进程树合计，后续运行生效）"
    recommended_decision: "接受为 T1-S2-MOSCOT-DECODER 的前置组件；T1-S2 需单独授权"
    blocker: null
    action: "不生成正式候选、不上传；等待 T1-S2 授权"
  - task: T1
    atom: T1-S2-MOSCOT-DECODER-20260902-v1
    status: SCORED_REJECTED
    final_artifacts: 44
    candidate_ids: "T1-S2 v0007 (L1_EMPIRICAL_RESIDUAL, server 44.9)、v0008 (L2_MODULE_SCDESIGN3, server 44.8)；submissions/INDEX.tsv 已回填 scored/registered"
    parents: "T1-PRE-HARMONIZE-20260902-v1；candidate/T1_val/v0004_strict_pseudobulk_shift"
    current_artifacts: "artifacts/tool_integration/T1-S2-MOSCOT-DECODER-20260902-v1/；stable manifest SHA256 前缀 461fb3378ce4f9dc；实现 scripts/t1_s2_moscot_decoder.py；v0007 SHA256 4297f3fd344d4592eaf2176caa7f28b03148993aa1bbbcc52c6156f0b121d866；v0008 SHA256 d664db404418fe8558dbe9a966352921c2498e74343318e0f8c9c08ff9774280"
    current_checks: "moscot 0.5.2 coupling converged（234 非零 transition，主通量 lineage 内）；mass 21 state 归一化+clip/收缩；alpha=1.0127 一次解析冻结；双 lane 5118×32285 contract PASS、protected checks 全 PASS；formal scorer pseudo-target E9.5 双 lane exit 0；17 测试 PASS、manifest 自校验 PASS；服务器 v0007=44.9、v0008=44.8（2026-09-03 回填 reports/SERVER_SCORE_REGISTRY.md）"
    risks: "pseudo-holdout parent 臂占优已获服务器印证：结构化 moscot 外推在 E10.5 未胜 strict shift（-3.6/-3.7），且低于 copy_last baseline 47.0；本地 pseudo-target 分数不构成 leaderboard 证据"
    recommended_decision: "REJECT 为 leaderboard 改进，T1-S2 路线关闭；两份候选保留不可变做失败诊断；T1 best 仍为 v0004=48.5，不追加 T1 调参"
    blocker: null
    action: "链关闭；执行资源转向 T2-S3-SHAPE-FIELD"
  - task: T2
    atom: T2-S3-SHAPE-FIELD-20260903-v1
    status: SCORED_PARTIAL_PROMOTION
    final_artifacts: 157
    candidate_ids: "embryo v0006(L1, server 59.7 rejected)/v0007(L2)、heart_interp v0007(L1, server 56.7 PROMOTED)/v0008(L2)、heart_extrap v0006/v0007（本地 REJECT 不上传）；INDEX.tsv 已回填"
    parents: "embryo/heart_interp: B1-A1-L1；heart_extrap: baseline-001-v0001"
    current_artifacts: "artifacts/tool_integration/T2-S3-SHAPE-FIELD-20260903-v1/；stable manifest SHA256 4ffef666e95f9046811346e1d940fde322de9dca53f06f7c4055a8a1051f8a76；实现 scripts/t2_s3_shape_field.py"
    current_checks: "6/6 候选 contract PASS、表达/obs/var/gene order hash 不变、RMS 回锁在 P0 容差内；holdout L1: H1/H2 全胜、H3/H4 全负；L2: 4/4 全负、heart_extrap kNN CATASTROPHIC；服务器（2026-09-03）：embryo 59.7（-0.4 rejected）、heart_interp 56.7（+0.4 new board best）；14 测试 PASS、manifest 自校验 PASS"
    risks: "embryo H1 全胜但服务器 -0.4，印证窄间隔 holdout 获益不保证 board 获益；derived T2≈55.8/Total≈149.6 待服务器页面确认，不得引用为服务器值"
    recommended_decision: "heart_interp 56.7 晋级当前 selection；embryo 保留 B1-A1 L1=60.1；4 条 REJECT 候选不可变保留不上传"
    blocker: null
    action: "已完成评分回填；下一方向 T2-J1 FGW assignment candidate"
  - task: T2
    atom: T2-J1-PROXY-20260903-v1
    status: J1_PROXY_PASS
    final_artifacts: 46
    candidate_ids: "none；条件 gate atom，不生成候选"
    parents: "B1-A4 结果引用；T2-S3-SHAPE-FIELD-20260903-v1（执行序）"
    current_artifacts: "artifacts/tool_integration/T2-J1-PROXY-20260903-v1/；stable manifest SHA256 b5e2abe2718f4708363df4189088071e29f6ad6d52007f22ffcb68565511b751；实现 scripts/t2_j1_proxy.py"
    current_checks: "FGW objective spec 先冻结（SHA256 4cf86109…）；2 独立 holdout 同向改善（NFS-like 0.012/0.015 vs random 0.137/0.172，64 随机无一更优）；label-only/scrambled-reference null 均差于 random；行序不变性 abs diff=0；14 测试 PASS、148 全量回归 PASS"
    risks: "heart holdout 逐位置 pearson 为负（参考跨 1.25 天、标签交集仅 5），heart 参考构建需审视；source-only 第 4 层证据，不构成 leaderboard 宣称"
    recommended_decision: "J1_PROXY_PASS；可另行授权 FGW assignment candidate（先审视 heart 参考）"
    blocker: null
    action: "不生成候选、不上传；等待授权"
  - task: T2
    atom: T2-J1-FGW-ASSIGNMENT-20260903-v1
    status: SCORED_PARTIAL_PROMOTION
    final_artifacts: 40
    candidate_ids: "T2:embryo:val_interp v0008 j1_fgw_assignment（HOLD_AS_COMPONENT）、T2:heart:val_interp v0009 j1_fgw_assignment（READY 弱置信）；详见 submissions/INDEX.tsv"
    parents: "embryo v0002 g1_formal_log_rms（60.1）；heart_interp v0007 t2_s3_l1_pycpd（56.7）；objective 继承 T2-J1-PROXY-20260903-v1 冻结 spec 4cf86109"
    artifacts: "artifacts/tool_integration/T2-J1-FGW-ASSIGNMENT-20260903-v1/；候选 SHA256 以 submissions/INDEX.tsv 为准（embryo 81442478…、heart 4f2e7552…）"
    checks: "heart 参考审视按预声明标准 PROCEED（跨度 0.50、标签交集 33、探针弱正 +0.0138）；全量 FGW 无子采样；column_argmax_margin_greedy_v1 双射 PASS（conflicts 72.2%/73.3%）；objective 同靶 embryo −12.2%、heart −26.6%；contract 2/2 PASS、protected 2/2 PASS（坐标/obs/var/kNN 图/表达 multiset 精确一致）；重跑字节一致；40 文件 manifest 自校验 PASS；14 新测试 + 162 全量回归 PASS"
    risks: "heart morans_I_agreement 同靶 0.7365→0.6743 变差（已声明）；embryo NFS 镜像 no_improvement 0.0312→0.0344 且 bracket 探针为负；训练期 pseudo-target 循环论证；本地证据非 leaderboard 证据"
    recommended_decision: "heart_interp v0009 READY_FOR_MANUAL_SUBMISSION（弱置信，是否消耗提交由用户决定，不自动上传）；embryo v0008 HOLD_AS_COMPONENT 不可变保留"
    blocker: null
    action: "服务器仲裁（2026-09-04 回填，行 2026-09-03 19:51）：heart_interp v0009=57.3（+0.6 vs v0007 56.7）晋级 board best 与当前 selection；embryo v0008 未上传保持 HOLD；derived T2≈55.97/Total≈149.8 待服务器页面确认；batch3 剩余 HX-DYNAMICS-KILLTEST"
  - task: T1
    atom: HX-DYNAMICS-KILLTEST-20260904-v1
    status: REJECT
    final_artifacts: 18
    candidate_ids: "none；kill test 只出 report，不生成候选"
    parents: "candidate/T1_val/v0004_strict_pseudobulk_shift（只读）；双臂复用 T1-PRE-HARMONIZE-20260902-v1 与 T1-S2-MOSCOT-DECODER-20260902-v1 冻结 artifact"
    artifacts: "artifacts/tool_integration/HX-DYNAMICS-KILLTEST-20260904-v1/；stable manifest 18 文件自校验 PASS；实现 scripts/hx_dynamics_killtest.py + scripts/hx_mioflow_worker.py"
    checks: "一次性固定部署 mioflow==0.1.14（wheel/sdist SHA256 核验、Yale 非商业许可披露、56 包依赖快照）；kill metric 定义先于运行写死（config 04:15 早于训练产物 05:06）；MIOFlow 一次训练 wall 2747s<7200s cap、库默认超参无搜索；三臂 L1：parent 1.1894 / moscot 0.6645 / mioflow 0.7475；12 新测试 + 174 全量回归 PASS"
    risks: "E9.5 是训练期 stage，holdout 只验证假设机制、非 leaderboard preview；mioflow 上游 growth_rate 导入损坏以 sys.modules 别名绕过（源码未改，已记录 deviation）"
    recommended_decision: "REJECT（预声明阈值未达成：未严格优于 moscot 臂）；moscot mass 质量不是 T1-S2 失败点，增长/死亡动力学方向关闭；不生成候选、不上传"
    blocker: null
    action: "kill test 收口；batch3 全部任务执行完毕；T1 无新授权前不追加 atom"
```
<!-- ve-status:end -->

## 人类快速阅读

| 任务 | 当前状态 | 当前最佳 | 下一动作 |
|---|---|---|---|
| T1 | active | v0004 strict pseudobulk shift，48.5 | HX-KILLTEST 已 REJECT（增长/死亡动力学方向关闭）；无新授权不追加 T1 atom |
| T2 | active | per-board selection（embryo 60.1 / heart_interp **57.3** / heart_extrap 50.5），服务器 T2 55.7 | J1-FGW heart_interp v0009 服务器 57.3（+0.6）晋级；余 HX-DYNAMICS-KILLTEST 实例化 |
| T3 | active（比赛）/ gate_blocked（科学） | B4-P0 v0008 exact floor 46.8（新 board best），服务器 T3 任务值 45.3 | exact floor 46.8 晋级；FLOOR_PARITY_UNRESOLVED；Wave 1 T3-R1 待授权，基准 46.8 |

Batch 1 已关闭为 `CLOSED_FOR_REVIEW`。综合评审报告为 `reports/PHASE_REPORT_BATCH1_20260829.md`；新 atom 需要新的明确授权。

当前科学阻塞只影响 scientific promotion，不影响比赛候选、上传和服务器反馈循环。

## 状态更新要求

coordinator 只在候选、检查、上传、评分、决策、阻塞或共享知识发生变化时更新本文件。agent 通过 handoff 提交更新，不直接并行编辑本文件。

### 2026-09-20 T3 R5/R6 补充准备

状态 PREPARATION_PARTIAL_QUARANTINE：新增4998细胞隔离派生集和500基因唯一映射；原R6增加signed用途门，shape-only数据不能进入方向学习。4项针对性测试通过。R5完整获批链仍0；R6剩23扰动待完整背景审查和书面确认，shape后继完整集成未完成，训练NOT_RUN。报告 `reports/t3_r56_readiness_20260920/REPORT.md`；未提交/未评分，blocks_submission: false。

### 2026-09-20 R5解阻、R6规则归因订正

R5最小输入已就绪并实际执行：4条SIGNOR源边/1条LRT，WT拟合，v0032/v0033（父v0009）contract PASS，PENDING_SERVER但未提交/未评分。交付 `deliveries/r5sig__t3__upload__20260920.zip`。仅该通用非目标拓扑获项目范围许可，不授权R6。R6仍隔离；shape-only和书面确认是内部严格解释，非官网统一条文。证据 `reports/t3_r5_completion_20260920/REPORT.md`、`R6_RULE_EXPLANATION.md`。selection不变，blocks_submission: false。

### 2026-09-21 R6首次执行收口

R6已完成整基因留出及最终训练/目标推断；图模型留出MSE优于两个对照，但r6ridge/r6graph负值33.61%/38.72%均超过1%，FAILED_DISASTER，0候选，未提交/未评分。R5 v0032/v0033仍待回分；best不变。 证据 `reports/t3_r6_execution_20260921/REPORT.md`；blocks_submission: false。

### 2026-09-21 R5回分收口

两候选总分及五子分已登记，文件SHA实核通过；两者与父版本同总分，signal on/off在回报精度下无差异。selection保持，R5回分队列清零；R6仍输出门槛失败，后继待设计。证据 `reports/SERVER_SCORE_REGISTRY.md#t3-next-r5-score-return-20260921`；blocks_submission: false。

### 2026-09-21 修复执行lease

coordinator owns scripts/t3_next/common.py、repair.py、repair_ops.py、configs/t3_next/repair_20260921.json、tests/t3_next/test_repairs.py及共享候选登记。用户授权开始修复；顺序R6→R3→R4，独立新run，旧结果不改。固定设计先于新训练；R1/R5组件以有效信号与新响应输入为后续前提。

### 2026-09-21 修复首批收口

R6/R3/R4修复运行完成，6候选v0034/v0035/v0036/v0037/v0040/v0041均contract PASS、未提交/未评分；v0038/v0039已撤回。R6图模型未胜过平均响应等强对照；R3四块与R4二十组WT评价通过。selection保持，等待新候选回分。 交付 `deliveries/r634fix__t3__upload__20260921.zip`；23项定向测试通过，六候选SHA/配置快照/坐标和组内差异核验通过。修复lease释放；科学限制blocks_submission: false。见 `reports/t3_repairs_20260921/REPORT.md`。

### 2026-09-21 T1新六路线提案

结合全部已登记技术家族及D5b最终失败receipt，发布 `reports/T1_NEXT_ROUTES_20260921.md`；仅metadata检查与方法文献检索，没有训练/候选/下载。T1现行选择不变；T3六个修复候选仍待上传回分，不受本次提案影响。

### 2026-09-27 T3 五路线执行 lease

用户授权 3 条新路线和 2 条既有路线优化。coordinator 独占 scripts/t3_next/five*.py、configs/t3_next/five_20260927.json、tests/t3_next/test_five.py、artifacts/t3_next/T3-FIVE-20260927-* 及本轮共享候选登记/文档。设计见 reports/T3_FIVE_DESIGN_20260927.md；全部完整数据运行，不覆盖旧候选。未上传/未评分，best 不变；blocks_submission: false。

### 2026-09-27 T3 五路线完成

三条新路线和两条优化均实现并全量运行；五个最终候选未提交/未评分，contract与模型逐值重放PASS，11测试通过。v0043/v0045撤回保留。交付 deliveries/five27__t3__upload__20260927.zip；统一报告 reports/t3_five_20260927/REPORT.md。现best不变，旧六修复候选仍待回分；本轮lease释放，blocks_submission: false。

### 2026-09-27 T1 三新两优化执行 lease

用户授权本轮五路线完整实现/执行。coordinator独占 scripts/t1_five/、tests/t1_five/、configs/t1_five/、artifacts/t1_five/ 与 reports/t1_five_20260927/；共享候选登记串行。此前 R5/R3/R4 实际已按各RESULT关闭，旧摘要 in progress/NOT_RUN 滞后，不重开旧run。本轮以 v0023 为已评分基线，仅用已发布 E8.5/E9.5；设计 reports/T1_FIVE_DESIGN_20260927.md。未提交/未评分；blocks_submission: false。

### 2026-09-27 T1 五路线完成

3新+2优化全部全量执行，五候选v0024–v0028均contract PASS、完整模型独立逐值重放PASS，9测试通过。五条完整panel官方scorer已运行；局部n3borrow较有希望、两优化不胜基线，未做E10.5真值/服务器评分，best v0023=50.82保持。交付 deliveries/t1five__t1__upload__20260927.zip；报告 reports/t1_five_20260927/REPORT.md；本轮lease释放，blocks_submission: false。

### 2026-09-27 T2 验证 V1 与 M0 附录 B

全历史 31 条已评分 T2 候选的本地指标 vs 服务器分排名相关已实测（D-20260927-T2VALIDATE-001）：`neighborhood_mmd` 在 heart_interp（Spearman −0.559）与 extrap（−0.627）**有预测力**，在 **embryo 强反向（+0.833）**——M0 的 5% 规则把板最佳 v0010（62.29）判成 DEGRADE。embryo 板另有「表达字节相同、仅坐标 ×1.305 膨胀、服务器 +3.4 分而本地七项指标全零」的输入对，证明**服务器几何子分对绝对尺度敏感而本地镜像看不见**。`d2_shape` 在两个插值板均反向。

据此按用户批准追加 **M0 附录 B（D-20260927-T2M0APPXB-001，未回改 §3/§4）**：`neighborhood_mmd`+5% 在 heart_interp/extrap 维持；**embryo 停用 5% 三分类**，本地读数只记录不否决，改服务器仲裁优先；`mmd_u` 会签在 embryo 零信号且族内成对反向；`d2_shape` 不得单独作失败签名。

### 2026-09-27 T2 九路线裁决与 E-N1 SBL 关闭

9 条候选逐条裁决（D-20260927-T2M1VERDICT-001，追加 M1 §7）：执行 `E-N1 SBL`/`E-I1 TCI`/`H-N2 A2C`；条件执行 `X-N2`（须重定义占据度，MacKenzie mark-recapture 前提不满足）；待澄清 `X-I1`；保留为验证实验但**本轮不执行** `E-N2`+`H-I1`（原始目的已被 V1 在 31 条候选上达成，且两者被预测量均已证伪）；否决 `H-N1`/`X-N1`。

`E-N1 SBL` 已完整执行并**关闭**（D-20260927-T2EN1-002）：两臂 `nmmd` 0.396/0.325 对 do-nothing 0.031（差 10.4–12.7 倍），预声明否定判据触发，不补救。根因是**全局水平与场项间无幅度控制**，非过平滑、非图案复制。两项自我订正（`log1p(expm1)` 是恒等式而非 softplus，我首次诊断因此有误；设计 τ=0.5 与目标 stage E7.5 算术不一致，正确 0.6）均非结果导向调参。

**下一批待执行**：`E-I1 TCI` 与 `H-N2 A2C` 的设计冻结文档（须训练前落盘）。evidence: `artifacts/tool_integration/T2-E-N1-SBL-20260927-v1/RESULT.md`、`artifacts/gate/T2_VALIDATE_V1_LOCAL_VS_SERVER-20260927-v1/RESULT.md`；blocks_submission: false。

### 2026-09-28 T3 三新两优化（含高分叠加）执行lease

用户要求读取009 KIR kill-test经验并至少尝试一个高分组合。coordinator独占 scripts/t3_round2、configs/t3_round2、tests/t3_round2、artifacts/t3_round2、reports/t3_round2_20260928；共享候选登记串行。根据当前评分，baseline为v0048=47.93，次高v0046=47.65，旧机器摘要46.95已滞后。先精确复现组件并做消融，再执行完整五路线；不读取目标KO真值，不更新旧评分artifact。设计 reports/T3_ROUND2_DESIGN_20260928.md；blocks_submission: false。

### 2026-09-28 T3 ROUND2完成

已按009 KIR kill-test经验完成精确高分基线复现、组件/顺序与强基线/置乱消融；五路线真实全量执行，v0049–v0053 contract及独立重放PASS，13测试通过，包SHA/CRC通过。旧best摘要订正为已登记v0048=47.93，不是本轮新晋级。科学判定INCONCLUSIVE_NEEDS_INDEPENDENT_TRUTH；不把负结果改阈值挽救。报告 reports/t3_round2_20260928/REPORT.md；deliveries/t3r2__t3__upload__20260928.zip；lease释放，blocks_submission: false。

### 2026-09-27 T2 两条存活路线执行收口（不提交）

`E-I1 TCI`（embryo）与 `H-N2 A2C`（heart_interp）已完整执行，**均失败**，裁决 `RECOMMEND_NO_SUBMISSION`（D-20260927-T2ROUTES-EXEC-001）。两条的几何/行序/组成重采样**逐字节复现**现役版本，恶化全部来自表达项：`neighborhood_mmd` 相对现役劣化 **+78~97%**（heart）与 **+2379~2568%**（embryo），四个分布侧指标同向变差；桥移植经校验精确（`bridge_only` 复现 v0013 到 1.5e-07）。候选作为不可变诊断物留在 `artifacts/`，**不进 submissions/INDEX、不打包、无上传**。

**三次尝试的合并发现**：给已被服务器验证的低空间方差均值场叠加「学出来的空间对比度」会摧毁分布，劣化幅度与对比度相对全局水平的幅度同向；把对比度定标到 sd=1 本身即病灶（`E-N1 SBL` 改用层内 sd 亦未解决）。已登记 LEADS **L-008** 作为前置问题（对比度幅度须由数据决定），**未执行**；在解决它之前不应再开任何「均值场 + 加性空间项」的 lane。evidence: `reports/T2_ROUTES_EXEC_CLOSURE_20260927.md`；blocks_submission: false。

### 2026-09-28 T1 第二轮执行lease

coordinator独占 scripts/t1_round2、configs/t1_round2、tests/t1_round2、artifacts/t1_round2、reports/t1_round2_20260928；复用旧代码只读，候选串行登记。三新两优化含v0024+v0027实际组合；设计 reports/T1_ROUND2_DESIGN_20260928.md。当前权威best=v0024 51.92，上方旧T1摘要待本批收口同步。blocks_submission:false。

### 2026-09-28 T1 ROUND2完成

v0029–v0033三新两优化均完成全量计算与完整panel本地评分，含v0024+v0027真实组合。16测试、五模型独立重放/拟合参数核对、contract、ZIP校验PASS。v0030本地最有利但未提交/未评分；best v0024=51.92保持。reports/t1_round2_20260928/REPORT.md；lease释放。E10.5/E12.5真值NOT_RUN，blocks_submission:false。

### 2026-09-29 状态同步

上面几段是当时的交接，不是现在的选择。2026-09-28 三批分数已经回填：T1 v0029=52.5 晋级，v0030=52.49 不并列晋级；T3 修复 v0037/v0040/v0041 已评分且不晋级，best 仍是 v0048=47.93；T2 v0014/v0015=61.52，不晋级。门户确认合计仍是 156.06。158.72 只是现役相加，不得写成门户总分。当前待分只剩 T3 v0049–v0053。给人读的教训见根目录 REVIEW.md。

### 2026-09-29 T2 三新两优化 × 三 board 执行 lease

用户授权 T2 三个子任务各 5 候选（3 新路线 + 2 既有优化/合并，共 15 件）。coordinator 独占 scripts/t2_round2、configs/t2_round2、tests/t2_round2、artifacts/t2_round2、reports/t2_round2_20260929；共享候选登记串行。设计已跑前冻结：reports/T2_ROUND2_DESIGN_20260929.md + configs/t2_round2/design_20260929.json；版本 embryo v0011–v0015、heart v0016–v0020、extrap v0017–v0021。不开均值场+空间对比 lane（L-008 未解）；embryo 本地指标只记录不否决（M0 附录 B）。未提交/未评分，best 不变；blocks_submission: false。

### 2026-09-29 T2 ROUND2 完成

15 候选全部全量建成：新路线=分位数桥（T1 机制移植）、三阶段趋势/曲率（E6.75/E8.25/E9.5 首次入相应 board）、组成粒度（子状态/cm 联合/组成趋势外推）、谱系映射 delta（17 零位移类型）；优化=×t 收缩、×G1 尺度回锁、+文库重标定、趋势×收缩、v0011×组成趋势。15 测试、contract 10 PASS+5 FAIL_BY_DESIGN_ACCEPTED（R2 同四类）、工程门 15/15、字节重放 15/15、v0011 组件逐值复现、质量计划逐名复现、ZIP SHA/CRC PASS。heart 无 5% nmmd 旗帜（h_n1 本地最强）；x_o2 唯一过历史 R1 局部双门（已声明方向不可靠）。交付 deliveries/t2r2__t2__upload__20260929.zip；报告 reports/t2_round2_20260929/REPORT.md；决策 D-20260929-T2ROUND2-001；INDEX/LANE_VERDICTS/TRACKING 已登记。15 件未提交/未评分，三 board best 不变（62.29/62.04/50.53）；lease 释放，blocks_submission: false。

### 2026-09-29 T3 三候选执行lease

coordinator独占scripts/t3_three、configs/t3_three、tests/t3_three、artifacts/t3_three、reports/t3_three_20260929，共享候选登记串行；消费冻结高分H/G，三条响应算子实际执行。设计reports/T3_THREE_DESIGN_20260929.md；v0049–v0053仍未回分，best v0048保持；blocks_submission:false。

### 2026-09-29 T3 三候选完成

v0054–v0056完整推断及四块WT条件诊断完成，12测试、独立重放、contract、旧候选去重、三个直接h5ad与ZIP校验PASS；reports/t3_three_20260929/REPORT.md。未提交/未评分；best v0048=47.93保持。科学INCONCLUSIVE，匹配KO评分NOT_RUN，lease释放，blocks_submission:false。

### 2026-09-29 T1 三候选执行lease

coordinator独占scripts/t1_three、configs/t1_three、tests/t1_three、artifacts/t1_three、reports/t1_three_20260929；设计reports/T1_THREE_DESIGN_20260929.md。用户授权本轮三路线，复用已评分v0029/v0030实际组合；best v0029=52.50保持。磁盘已恢复，原项目执行；blocks_submission:false。

### 2026-09-29 T1 三候选完成

v0034–v0036全量推断和完整panel本地scorer完成，13测试、独立重放/整行身份/contract/ZIP通过。提交包deliveries/t1three__t1__upload__20260929.zip；reports/t1_three_20260929/REPORT.md。优先v0035本地信号，三个未提交/未评分；best v0029=52.50保持。磁盘恢复后全部在正式项目执行，lease释放，blocks_submission:false。

### 2026-09-29 T3 五路线选三执行 lease
coordinator 独占 scripts/t3_five_select、configs/t3_five_select、tests/t3_five_select、artifacts/t3_five_select、reports/t3_five_select_20260929；共享登记串行。五条实际运行，开发块固定选一条来源组合及两条新模型，名单锁定后审计；仅三条登记入包。设计 reports/T3_FIVE_SELECT_DESIGN_20260929.md。旧 v0049–v0056 未回分，best v0048 保持；blocks_submission:false。

### 2026-09-29 T3 五路线选三完成
五条全量运行，事前开发块选中v0057–v0059三件，审计未改名单；五条contract/重放/去重、6测试与独立进程14项验收通过。单包deliveries/t3five3__t3__upload__20260929.zip；reports/t3_five_select_20260929/REPORT.md。三个未提交/未评分，best v0048=47.93保持。仅WT少量组诊断，匹配KO scorer NOT_RUN，科学NOT_IDENTIFIABLE；lease释放，blocks_submission:false。

### 2026-09-30 T1 七路线执行 lease
coordinator独占scripts/t1_seven、configs/t1_seven、tests/t1_seven、artifacts/t1_seven、reports/t1_seven_20260930；共享登记串行。按用户要求3新＋2失败优化＋2成功优化，设计reports/T1_SEVEN_DESIGN_20260930.md。当前best v0035=53.43，T1旧项已全部回分。完整32285列实际推断及本地scorer，科学限制blocks_submission:false。

### 2026-09-30 T1 七路线完成
3新＋2失败优化＋2成功优化全部全量执行，七次完整panel本地scorer与14矩阵独立重放通过，8测试通过。候选v0037、v0038、v0039、v0040、v0042、v0041、v0043未提交/未评分，best v0035=53.43保持；reports/t1_seven_20260930/REPORT.md；deliveries/t1seven__t1__upload__20260930.zip。未来真值NOT_RUN，科学EXPLORATORY_LOCAL；lease释放，blocks_submission:false。

### 2026-09-30 T1十一条回分完成
v0037–v0047回填完成，v0038晋级53.55，v0043同分备份；11身份哈希通过，44子项齐全，T1待分清零。均值平移家族不再推荐，未重训/未生成候选/未操作portal。D-20260930-T1SCORE-001；reports/t1_score_review_20260930/REPORT.md；blocks_submission:false。

### 2026-10-07 T1 六路线执行 lease
T1 agent 独占 scripts/t1_six、configs/t1_six、tests/t1_six、artifacts/t1_six、reports/t1_six_20261007；共享登记串行（t1_three/t1_seven 冻结产物只读）。用户 /goal 授权：3 条既有路线优化/结合（混合只作载体带新组件）＋3 条全新路线（本轮检索优先）；设计 reports/T1_SIX_DESIGN_20261007.md，参数冻结 configs/t1_six/design_20261007.json。当前 best v0051=53.92 保持；完整 32285 列实际推断及本地 scorer，科学限制 blocks_submission:false。

### 2026-10-07 T1 六路线完成
3 条优化/结合＋3 条全新全部全量执行，六次完整 panel 本地 scorer 与独立进程重放通过，13 测试通过。候选 v0057（osoftcov）/v0058（ostabmix）/v0059（nconf）/v0060（nbidir）/v0061（ocovstab）/v0062（nwasser）未提交/未评分，best v0051=53.92 保持；本地信号 ostabmix de 改善、nbidir 取舍，其余全劣；reports/t1_six_20261007/REPORT.md；deliveries/t1six__t1__upload__20261007.zip READY_NOT_SUBMITTED。未来真值 NOT_RUN，科学 EXPLORATORY_LOCAL；lease 释放，blocks_submission:false。
