最新 T1 事件（2026-09-30）：十一条回分已登记；v0038/v0043同为53.55（较旧best+0.12），v0038现役、v0043同分备份；T1待分清零，均值平移四臂不晋级。[复盘](reports/t1_score_review_20260930/REPORT.md)。

最新 T3 事件（2026-09-29）：五路线完整运行，事前规则选v0057–v0059三个h5ad入包；6测试和独立进程14项验收通过，未提交/未评分，best仍v0048=47.93。[报告](reports/t3_five_select_20260929/REPORT.md)；[三文件上传包](deliveries/t3five3__t3__upload__20260929.zip)。

# Virtual Embryo 项目状态

更新时间：2026-09-30

最新事件（2026-09-30 T1回分）：T1 v0038登记为现役53.55，v0043精确同分备份；其余九件不晋级。完整分数见[权威登记](reports/SERVER_SCORE_REGISTRY.md#t1-seven-pbmean-score-return-20260930)。推导合计160.07，尚未获得门户新Total。

## 第一部分：给人读的进展

**已完成什么。** T1十一件回分全部入库。协方差输运和双模型混合各比旧best高0.12；两条失败优化未超过共同骨架，平均数平移四臂均明显退步。

**正在做什么。** T1待分已清零，复盘已完成。下一步核对门户选集及Total，其他任务队列以各自权威登记为准。

**卡在哪里。** 网页上一次确认的三个任务合计仍是 **156.06**。按现在各榜现役相加是 160.07，但这不是网页已经返回的合计，不能当成官方总分。心脏往后推的那一项，单独最高是 50.64，合计里用的仍是 50.53，差 0.11，还没对上。另外，我们自己交的“什么都不做”复制件并不是 50 分，所以不能把“超过 50”直接说成已经稳定超过官方的什么都不做。

**准备怎么解决。** 重读一次门户网页，把确认过的合计从 156.06 更新到现在。不再交已经更差的阻尼和基因臂。心脏外推那 0.11 的差额，需要在网页上对，不能在这里猜。

```

2026/9/29
ROADMAP  [##############-] 14/15 节点（N8 仍未正式裁决）
本周投入  科学问题 ████████░░ 80%   基础设施 ██░░░░░░░░ 20%

偏离程度  中
偏离位置  原定“先选方向或封板”的节点一直没有正式裁决，后面的工作是直接做上去的。
         160.07 只是现役相加，不是网页确认的合计。
建议      重读网页上的合计（推导值 160.07 待确认）；在此之前不要开新的大路线。
```

## 第二部分：给 agent 的接手信息

- 活跃事项：T1本批十一件已回分并复盘；待门户选集和Total确认。
- 当前选择：T1 v0038=53.55（v0043同分备份）；T2 62.89 / 62.36 / 合计仍用外推 50.53；T3 v0048=47.93。
- 核心文件：`submissions/INDEX.tsv`、`reports/SERVER_SCORE_REGISTRY.md`、`REVIEW.md`。
- 最近T1决策：`D-20260930-T1SCORE-001`。其他任务见各自追踪和决策记录。
- 下一步：用户重读门户网页，确认合计与外推选集。不自动开新路线。
- 未闭合：门户合计仍是 156.06；160.07 只是推导值。外推 50.64 与合计里的 50.53 差 0.11，需重读门户。外推 v0017 本次没回分。

---

## 比赛细节（以下为本项目原有 STATUS 内容）

完整分数不在本文件重复维护：候选文件与哈希看 [`submissions/INDEX.tsv`](submissions/INDEX.tsv)，服务器分数看 [`reports/SERVER_SCORE_REGISTRY.md`](reports/SERVER_SCORE_REGISTRY.md)，任务细节看 [`docs/coordination/`](docs/coordination/) 下的三个追踪文档。

## 总体状态

- 比赛优先；starter_pack 已关闭为 `CLOSED_FOR_COMPETITION_BASELINE`。
- 当前aggregate：**158.14**（2026-09-28用户回分登记，51.92+58.29+47.93；见SERVER_SCORE_REGISTRY.md，非本轮新成绩）。
- 任务分数摘要（T1已更新；其他分项历史快照，以registry为准）：T1 **51.92**（v0024，2026-09-28），T2 **58.29**（derived，与 156.06 自洽；board 62.29 / 62.04 / 50.53），T3 **46.95**（v0009/v0010 并列）。
- 科学 promotion 仍开放，但 `blocks_submission: false`。
- 仓库已于 2026-09-02 完成首次推送：`github.com/FreddieWho/014_virtualEmbryo` main 分支（commit `cde3c9c`，251 个代码/文档/配置文件；`data/`、`artifacts/`、`outputs/` 等大文件按 `.gitignore` 排除）。

## Batch 1 收尾

- 状态：`CLOSED_FOR_REVIEW`；4 个正式 atom 已完成，共 16 个最终候选并全部获得服务器分数登记。
- B1-A1 为局部有效路线；B1-A2、B1-A3、B1-A4 均不替换当前 best；B1-C1 按条件不需要执行。
- 综合评审报告：[`reports/PHASE_REPORT_BATCH1_20260829.md`](reports/PHASE_REPORT_BATCH1_20260829.md)
- 收尾变更日志：[`reports/RELEASE_CHANGELOG_20260829.md`](reports/RELEASE_CHANGELOG_20260829.md)
- 新 atom 或新提交前需要明确授权。

## Batch 3 收尾

- 状态：`COMPLETE`（2026-09-04）；8 条路线全部执行完毕，无 active atom。
- 净收益：T2 heart_interp 56.3 → 57.3（+1.0）；moscot、MIOFlow、spateo lane 三条方向关闭；T3-S1 链证据环境锁死收口；FGW 留有后手（LEADS L-002）。
- 综合评审报告：[`reports/PHASE_REPORT_BATCH3_20260904.md`](reports/PHASE_REPORT_BATCH3_20260904.md)
- 收尾变更日志：[`reports/RELEASE_CHANGELOG_BATCH3_20260904.md`](reports/RELEASE_CHANGELOG_BATCH3_20260904.md)
- 新 atom 或新提交前需要明确授权。

## 各任务评分最高的 Top 3 路线

### T1 — single-cell temporal

1. `v0038_seven_n2covot`：**53.55**，现役；较旧best +0.12。
2. `v0043_seven_s2mix`：**53.55**，精确同分备份，不并列晋级。
3. `v0035_three_r2joint`：**53.43**，保留为历史高分参照。

同批精确同分按用户供给列表顺序登记，非上传先后证据。历史见[T1_TRACKING.md](docs/coordination/T1_TRACKING.md)，复盘见[报告](reports/t1_score_review_20260930/REPORT.md)。

### T2 — spatial-temporal

1. 当前 per-board selection：B1-A1 L1 embryo 60.15 + T2-J1 v0009 `j1_fgw_assignment` heart_interp **57.25** + baseline heart extrap 50.53；T2 board 均值 55.98、Total **151.2**（均为 2026-09-04 服务器确认；子项见 SUBMETRIC_REGISTRY）。
2. B1-A1 `L1_FORMAL_LOG_RMS`：raw scores 60.1/56.3/50.2；heart extrap 低于 baseline 50.5。
3. B1-A1 `L2_ALL_STAGE_LOG_RMS_OLS`：raw scores 59.9/55.3/49.8，已评分 backup。

Batch3 `T2-J1-FGW-ASSIGNMENT-20260903-v1`：heart_interp v0009 服务器 **57.3（+0.6 vs v0007 56.7）** 晋级 board best（2026-09-04 回填）；embryo_interp v0008 未上传，保持 `HOLD_AS_COMPONENT` 不可变。

详情：[T2_TRACKING.md](docs/coordination/T2_TRACKING.md)

### T3 — gene perturbation

1. B2-T3-A1 `L1_STRICT_WT_DIRECT`（v0006）：**45.5**，已评分，并列当前 best（2026-09-04 回填）。
2. B2-T3-A1 `L2_GATA4_GATA6_CONDITION_AWARE`（v0007）：**45.5**，已评分，并列当前 best。
3. `wt_identity`（v0001）：**45.3**，已评分，历史 best（被并列超越 0.2）。

两条新候选是其五次尝试（v0002–v0005 及 baseline 之后）里首次超过 `wt_identity` 的结果；并列说明服务器无法区分 lane，不声称偏好。derived T3=45.5、derived Total≈149.7 待服务器页面确认。

Batch2 `B2-T3-A1` 已生成两条未评分候选：L1 `v0006`（49 个下游基因 + Gata4）和 L2 `v0007`（73 个下游基因 + Gata4/Gata6 half-dose）。二者 contract/protected 均 PASS；本地 Mab21l2 source-only 诊断不等于 Gata4 或服务器分数，状态保持 `score_pending`、结论 `HOLD_AS_COMPONENT`，不自动上传。

Batch3 `T3-S1-PRIOR` 已形成 prior/gate bundle：31,458 条 state×gene 记录，L1/L2 非零分别为 2,050/5,125；用户授权后的本地方法部署与 CollecTRI/OmniPath panel-scoped 内容审计均为 `PASS`。正式分析前的 5 个 current parent contract/registry SHA256、protected-field/round-trip 复核和实际 22 项接口测试均已闭合；directed-evidence 组件为 `COMPONENT_PASS`，但 candidate admission 仍 `HOLD`，这些预检不等于 state-specific activity validation。β-catenin 相关 prior 仍显式为 `sign=0/EXTERNAL_KNOWLEDGE_AUDITED_NOT_INTEGRATED`，S1 prior 未消费 state-joined evidence。prior/gate 仍为 `HOLD_AS_COMPONENT`，原因是 stability sensitivity；不进入 H5AD 或候选生成。

T3-S1A v7 已完成 exact E8.75 input/state join、显式 target applicability、Gata4 CellOracle real API、三条 scTenifold 输出、full-matrix state-response/coverage 审计和 hash-bound route audit；随后 S1B v3 已完成 full CollecTRI/OmniPath identity、external contextual integration、冲突归零审计、family-native LOFO 与实现脚本 SHA 绑定。经用户授权继续后，S1C-A/v1 已用原生 CellOracle `TFdict` 构建 Gata6/Ctnnb1 target-compatible adapter，S1C-B/v3 在真实 CellOracle 0.22.0 上完成 2/2 synthetic fit/simulate smoke 并通过进程退出后的 stable manifest 自校验；S1D/v3 又获得 GSE5298/GSE9652 两个 Gata4 与 GSE78125 一个 Ctnnb1 的 E9.5 exact-stage、组织限定 processed perturbation context，并完成 sample/mapping/effect provenance。

**2026-09-02 收口**：T3-S1 链已正式收口为 `CLOSED_AS_RESEARCH_COMPONENT`（[`artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md`](artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md)）。同日独立的 gate 可满足性审计（`T3-S1C-GATE-SATISFIABILITY-20260902-v1`）判定 `UNSATISFIABLE_UNDER_FIREWALL`，两条结论一致：signed family<2、E8.75 state-matched activity 公开不可得、stability 未闭合，且 E8.5–E9.0 窗口目标扰动数据属 target leakage，gate 在当前 firewall 下结构性不可达。候选生成、scorer、上传保持关闭，`blocks_submission: false`；重开条件见收口报告。执行资源已切换至 batch3 `T1-PRE-HARMONIZE`。

详情：[T3_TRACKING.md](docs/coordination/T3_TRACKING.md)

## 下一步总览

| 任务 | 下一步 | 提交前硬要求 |
|---|---|---|
| T1 | v0038=53.55现役，v0043同分备份；Top3第三为v0035 | 十一件全部scored，T1待分清零；均值平移四臂不晋级 |
| T2 | B4-T2-R2 四 lane：embryo v0009=**61.79**（+1.64）晋级、v0010=**62.29**（+2.14）新 best；heart v0013=**62.04**（+4.79）新 best、v0012=56.27（-0.98）淘汰；两 board 均 L2>L1。T2-R3 三 lane 按用户决定关闭不评分 | selection：embryo v0010 + heart v0013 + extrap baseline；Total 153.7 已确认 |
| T3 | best v0048=47.93；五路线全量完成，选v0057–v0059三件入包，未提交/未评分 | 旧v0049–v0056待分；匹配KO评分NOT_RUN；blocks_submission:false |

## 更新规则

每次新版本、参数修改或路线分叉，都要在对应任务追踪文档的“变更记录”追加一行，用一句通俗话说明：

> 把什么改成什么；为什么改；结果是什么；保留还是淘汰。

根目录本文件只在当前 best、Top 3、任务状态或下一步发生变化时更新。服务器分数返回后，先更新 `reports/SERVER_SCORE_REGISTRY.md`，再同步本文件和对应任务文档。

- 2026-09-20 T3 R5/R6：已补第二次隔离过滤与用途门；尚未获准训练。下一步为剩余扰动/信号链审查、书面用途确认及shape版完整集成，见 [准备报告](reports/t3_r56_readiness_20260920/REPORT.md)。既有best与待评分队列不变。

- 2026-09-20 T3更新：R5已补齐最小信号链并生成v0032/v0033，合约PASS，未提交/未评分；[交付包](deliveries/r5sig__t3__upload__20260920.zip)。R6仍待审查，书面确认/shape-only为项目内部约束。见[本轮报告](reports/t3_r5_completion_20260920/REPORT.md)。下一步收集服务器分数，best不变。
