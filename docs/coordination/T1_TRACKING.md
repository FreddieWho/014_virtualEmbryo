# T1 任务追踪：single-cell temporal

更新时间：2026-09-02

分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。本文件只做简短解释和路线选择。

## 当前状态

- 当前最高服务器分数：**48.5**
- 当前最佳：`candidate/T1_val/v0004_strict_pseudobulk_shift`
- 当前状态：`active`；`v0002` 已评分 45.9（-1.1）淘汰；v0004 取得 48.5，B1-A3 两条均低于该 best，v0006 仅为 B1-A3 lane winner；T1-S2 moscot 双 lane（v0007=44.9、v0008=44.8）服务器仲裁失败，均淘汰
- batch3 进展：`T1-PRE-HARMONIZE-20260902-v1` gate PASS；`T1-S2-MOSCOT-DECODER-20260902-v1` 已完成服务器探针并被拒绝为改进（结构化外推未胜 strict shift），链关闭
- 任务阻塞：无（full-panel scorer 可运行性已于 P0 解决并在 T1-PRE 实测 323s 跑通）；科学 promotion 阻塞不影响提交

## Top 3 路线

三条路线均已有服务器分数；B1-A3 两条均高于旧 baseline。

| 位次 | 路线 | 通俗说明 | 服务器分数 | 状态 |
|---|---|---|---:|---|
| 1 | `v0004_strict_pseudobulk_shift` | 去掉组成外推并采用严格的状态内 pseudobulk shift | **48.5** | 已评分，当前 best |
| 2 | `B1-A3 L2_E95_EXPRESSION_PROBE` | 用 source-only expression projection 分区，再从 T1 基线做完整父行 replay | **47.7** | 已评分，B1-A3 lane winner |
| 3 | `B1-A3 L1_SHARED_UNRESOLVED` | 用 shared label + unresolved 分区，再从 T1 基线做完整父行 replay | **47.5** | 已评分，B1-A3 scored backup |

## 变更记录

每次修改或分叉只写一句人话：改了什么、为什么、结果如何。

| 日期 | 版本/分叉 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-08-21 | `baseline-001/T1_val/v0001` | 无 | 先用 `copy_last` 建立 T1 合法提交底线。 | 服务器 `47.0`；保留 |
| 2026-08-22 | 追踪文档建立 | `v0001` | 把 T1 的已评分基线和两个待评分方向固定下来。 | 不改变模型；等待下一候选 |
| 2026-08-22 | `candidate/T1_val/v0002_shrunk_pseudobulk_shift` | `v0001` | 从 `copy_last` 分叉出收缩版 `pseudobulk_shift`：per-type Δ 与全局 Δ 各半混合、E9.5 独有类型回退全局 Δ、共有类型组成按 E8.5→E9.5 线性外推后定向抽样，其余 contract 不变。 | 本地 contract pass；上传评分 |
| 2026-08-24 | `submission-003/T1_val/v0002` | `v0001` | 服务器返回 45.9，比基线低 1.1 分；最可疑的是组成外推太激进（Foregut/pSHF 被压到下限），动到了占 30% 的分布项。 | 淘汰 v0002；保留 `copy_last` 为 best；评分快照存于 `submissions/scored/submission-003/` |
| 2026-08-24 | `candidate/T1_val/v0003_no_comp_extrap` | `v0001` | 从 `v0001` 分叉保守版：去掉组成外推，保留 per-type Δ 与全局 Δ 混合（w=0.5）+ E9.5 独有类型回退全局 Δ，其余不变。 | 服务器 46.2（-0.8）；淘汰 |
| 2026-08-24 | `candidate/T1_val/v0004_strict_pseudobulk_shift` | `v0001` | 从 `v0001` 分叉严格官方复刻：per-type Δ 纯、缺失类型 Δ=0、无组成外推。 | 服务器 48.5（+1.5）；当前 T1 best |
| 2026-08-28 | `B1-A3/T1_val/v0005_b1_a3_shared_unresolved` | `v0001` | 采用 exact shared label + `UNRESOLVED_STAGE_SPECIFIC` 的 source-only partition，按状态质量外推并做完整父行 residual replay。 | contract pass；服务器 47.5（+0.5），低于 v0004=48.5；保留为 scored backup |
| 2026-08-28 | `B1-A3/T1_val/v0006_b1_a3_e95_expression_probe` | `v0001` | 采用 E9.5 固定词表和全 panel cosine expression projection 冻结 E8.5 state assignment，再做同一质量外推与 residual replay。 | contract pass；服务器 47.7（+0.7），低于 v0004=48.5；保留为 B1-A3 lane winner |
| 2026-08-28 | B1-A3 本地评分尝试 | `v0005/v0006` | 对两条正式候选执行锁定的 full-panel scorer；L1 在 900 秒超时，L2 无结果且进程异常消失后中断。 | 不使用缩减/替代 scorer；服务器已回填 47.5/47.7，官方结果优先 |
| 2026-09-02 | `T1-PRE-HARMONIZE-20260902-v1` | `P0-LOCK` | 按 batch3 契约建立 E8.5↔E9.5 state 词表（28 个 union state，复用冻结官方 celltype 标签，未重聚类）与严格 crosswalk（marker cosine + mutual nearest centroid，低置信显式 UNRESOLVED 不强配），并用新长时 wrapper 对 source-only projection 实测跑通锁定 full-panel scorer。 | gate `STATE_GATE_PASS_AND_FULL_PANEL_SCORER_PASS`；scorer exit 0、323s、meta 三项校验全过；15 项新测试+103 全量回归 PASS；stable manifest `e2f2889081d8bfffffe3111eb8cd024882c98d3304519618a964518b74698413`；不生成候选、不上传；具备授权 T1-S2 的前置资格 |
| 2026-09-02/03 | `T1-S2-MOSCOT-DECODER-20260902-v1` | `T1-PRE-HARMONIZE-20260902-v1`、`candidate/T1_val/v0004_strict_pseudobulk_shift` | 用 moscot 0.5.2 TemporalProblem 在 state/program latent 求 E8.5→E9.5 coupling（converged，234 非零 transition），加 state-mass forecast（clip/收缩）与 state-specific mean delta，alpha=1.0127 一次解析冻结；L1 empirical residual replay 与 L2 module-wise scDesign3 1.6.0（39 组拟合）双 lane 各生成 5118×32285 E10.5 候选。 | 双 lane contract/protected 全 PASS；pseudo-holdout 三臂 parent 全面占优（de_score 0.6226 vs L1 0.4528 vs L2 0.4340）；**服务器探针仲裁：v0007=44.9、v0008=44.8，均低于 best 48.5 和 baseline 47.0，REJECT 为改进**，结构化外推路线关闭；候选保留不可变做诊断；17 测试 PASS、manifest 44 文件自校验 PASS |
| 2026-09-04 | `HX-DYNAMICS-KILLTEST-20260904-v1` | `candidate/T1_val/v0004_strict_pseudobulk_shift`（只读）；moscot 臂复用 `T1-S2-MOSCOT-DECODER-20260902-v1` 冻结质量 | 单假设 kill test：把 moscot 静态传输替换为 MIOFlow（pip `mioflow==0.1.14`，SDE+GrowthRateModel，带增长/死亡项，一次性部署隔离 venv `ve-hx-mioflow` 并 hash-lock 审计，Yale 非商业许可已披露），其余 T1-S2 管线组件全冻结；唯一 kill metric 为留 E9.5 holdout 的 per-state mass L1 误差（定义先于运行写死），双臂对照 strict-shift parent 与 moscot。 | 三臂 L1：parent 1.1894、moscot 0.6645、mioflow 0.7475——mioflow 优于 parent 但未优于 moscot，预声明阈值（须同时严格优于双臂）未达成 → **REJECT 并停止**；moscot 的 mass 质量不是 T1-S2 失败点，增长/死亡动力学方向关闭；不生成候选、不上传；12 新测试+174 全量回归 PASS；manifest 18 文件自校验 PASS |

## 下一步

`B1-A3` 已完成服务器评分：L1=47.5，L2=47.7。L2 为 B1-A3 lane winner，但全局 T1 best 是先前 v0004=48.5；两条 B1-A3 均保留为不可变 scored candidates。

2026-09-02：`T1-PRE-HARMONIZE-20260902-v1` 完成并通过 gate，产物见 `artifacts/tool_integration/T1-PRE-HARMONIZE-20260902-v1/`。注意 T1-PRE 的 pseudo-holdout 分数（de_score 0.6226）只验证表示与验证链，是 source-only 训练期阶段的检查，**不是 leaderboard preview**；两条非 exact marker 边 bootstrap recovery 仅 0.40–0.50，T1-S2 应把非 exact 边当软证据、UNRESOLVED 用收缩/全局回退。

2026-09-03：`T1-S2-MOSCOT-DECODER-20260902-v1` 完成，产物见 `artifacts/tool_integration/T1-S2-MOSCOT-DECODER-20260902-v1/`。候选 v0007（L1 empirical residual）与 v0008（L2 module scDesign3）已经服务器探针仲裁：**v0007=44.9、v0008=44.8，均低于 best 48.5（-3.6/-3.7）且低于 baseline 47.0，REJECT 为 leaderboard 改进** —— 服务器证据回答了 pseudo-holdout 无法回答的问题（结构化 moscot 外推 vs strict shift 延伸），答案为否定，T1-S2 路线关闭，两份候选保留不可变做失败诊断。当前 best 仍为 v0004=48.5。T1 暂不追加调参；执行资源转向 `T2-S3-SHAPE-FIELD`。

2026-09-04：`HX-DYNAMICS-KILLTEST-20260904-v1` 完成，产物见 `artifacts/tool_integration/HX-DYNAMICS-KILLTEST-20260904-v1/`。唯一假设（增长/死亡+随机动力学改善 state-mass 外推）在预声明 kill metric 上未同时优于双臂（mioflow 0.7475 vs moscot 0.6645 vs parent 1.1894）→ **REJECT**：moscot 的 state-mass 预测本身已显著优于 strict-shift，T1-S2 的失败不在 mass 环节，增长/死亡动力学方向关闭。batch3 全部任务执行完毕；T1 无新授权前不追加 atom。

2026-09-04（batch4）：`B4-P0-STATE-FLOOR-PARITY` 完成并评分。T1 exact-floor 候选 v0009（`b4p0_l0_exact_floor`，均匀抽样 seed 20260904、原始行序、零表达变换、不用 celltype）服务器 **47.0**，与分层版 baseline-001 v0001 完全相同 → celltype 分层被排除为 floor 差距（-3.0 vs 官方 50）的原因；`FLOOR_PARITY_UNRESOLVED` 开启，剩余主假设为 pred n_obs 或 bundle 级差异。当前 best 不变：v0004=48.5。产物 `artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/`。下一步：Wave 1 `B4-T1-R1-CONSERVATIVE-FAMILY` 待授权。

2026-09-04（夜）：B4-P0 补充探针 v0010（`b4p0_l0floor_n1706`，n=1,706，同一种子均匀抽样、原始行序、零变换）服务器 **46.8**（-0.2 vs v0009=47.0）→ **n_obs 假设被排除**，FLOOR_PARITY_UNRESOLVED 维持；T1 best 仍为 v0004=48.5。产物 `artifacts/batch4/B4-P0-T1-FLOOR-PROBE2-20260904-v1/`。下一步：Wave 1 `B4-T1-R1-CONSERVATIVE-FAMILY` 待授权（provisional-score 身份）。
