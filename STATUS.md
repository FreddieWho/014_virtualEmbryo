# Virtual Embryo 项目状态

更新时间：2026-09-03

这是给人看的总入口。完整分数不在这里重复维护：候选文件看 [`submissions/INDEX.tsv`](submissions/INDEX.tsv)，服务器分数看 [`reports/SERVER_SCORE_REGISTRY.md`](reports/SERVER_SCORE_REGISTRY.md)，任务细节看下面三个追踪文档。

## 总体状态

- 比赛优先；starter_pack 已关闭为 `CLOSED_FOR_COMPETITION_BASELINE`。
- 当前 aggregate best：**149.5（服务器当前返回值）**。
- 当前任务分数：T1 **48.5**，T2 **55.7（服务器当前返回值）**，T3 **45.3**。
- 科学 promotion 仍开放，但 `blocks_submission: false`。
- 仓库已于 2026-09-02 完成首次推送：`github.com/FreddieWho/014_virtualEmbryo` main 分支（commit `cde3c9c`，251 个代码/文档/配置文件；`data/`、`artifacts/`、`outputs/` 等大文件按 `.gitignore` 排除）。

## Batch 1 收尾

- 状态：`CLOSED_FOR_REVIEW`；4 个正式 atom 已完成，共 16 个最终候选并全部获得服务器分数登记。
- B1-A1 为局部有效路线；B1-A2、B1-A3、B1-A4 均不替换当前 best；B1-C1 按条件不需要执行。
- 综合评审报告：[`reports/PHASE_REPORT_BATCH1_20260829.md`](reports/PHASE_REPORT_BATCH1_20260829.md)
- 收尾变更日志：[`reports/RELEASE_CHANGELOG_20260829.md`](reports/RELEASE_CHANGELOG_20260829.md)
- 新 atom 或新提交前需要明确授权。

## 各任务评分最高的 Top 3 路线

### T1 — single-cell temporal

1. `v0004_strict_pseudobulk_shift`：**48.5**，已评分，当前 best。
2. B1-A3 `L2_E95_EXPRESSION_PROBE`：**47.7**，已评分，B1-A3 lane winner。
3. B1-A3 `L1_SHARED_UNRESOLVED`：**47.5**，已评分，scored backup。

详情：[T1_TRACKING.md](docs/coordination/T1_TRACKING.md)

### T2 — spatial-temporal

1. 当前 per-board selection：B1-A1 L1 保留 embryo/interp，baseline 保留 heart extrap；服务器 T2 **55.7**、Total **149.5**。
2. B1-A1 `L1_FORMAL_LOG_RMS`：raw scores 60.1/56.3/50.2；heart extrap 低于 baseline 50.5。
3. B1-A1 `L2_ALL_STAGE_LOG_RMS_OLS`：raw scores 59.9/55.3/49.8，已评分 backup。

详情：[T2_TRACKING.md](docs/coordination/T2_TRACKING.md)

### T3 — gene perturbation

1. `wt_identity`：**45.3**，已评分，当前 best。
2. B1-A2 `L1_CELL_LEVEL_SPEARMAN`：v0004，**44.7（-0.6）**，低于 baseline，淘汰并保留诊断。
3. B1-A2 `L2_STATE_PSEUDOBULK_SPEARMAN`：v0005，**44.0（-1.3）**，低于 baseline，淘汰并保留诊断。

历史对照：`shift_transfer_norm` v0002 为 45.2（-0.1），`shift_transfer_shrunk` v0003 为 43.8（-1.5），均已淘汰。

Batch2 `B2-T3-A1` 已生成两条未评分候选：L1 `v0006`（49 个下游基因 + Gata4）和 L2 `v0007`（73 个下游基因 + Gata4/Gata6 half-dose）。二者 contract/protected 均 PASS；本地 Mab21l2 source-only 诊断不等于 Gata4 或服务器分数，状态保持 `score_pending`、结论 `HOLD_AS_COMPONENT`，不自动上传。

Batch3 `T3-S1-PRIOR` 已形成 prior/gate bundle：31,458 条 state×gene 记录，L1/L2 非零分别为 2,050/5,125；用户授权后的本地方法部署与 CollecTRI/OmniPath panel-scoped 内容审计均为 `PASS`。正式分析前的 5 个 current parent contract/registry SHA256、protected-field/round-trip 复核和实际 22 项接口测试均已闭合；directed-evidence 组件为 `COMPONENT_PASS`，但 candidate admission 仍 `HOLD`，这些预检不等于 state-specific activity validation。β-catenin 相关 prior 仍显式为 `sign=0/EXTERNAL_KNOWLEDGE_AUDITED_NOT_INTEGRATED`，S1 prior 未消费 state-joined evidence。prior/gate 仍为 `HOLD_AS_COMPONENT`，原因是 stability sensitivity；不进入 H5AD 或候选生成。

T3-S1A v7 已完成 exact E8.75 input/state join、显式 target applicability、Gata4 CellOracle real API、三条 scTenifold 输出、full-matrix state-response/coverage 审计和 hash-bound route audit；随后 S1B v3 已完成 full CollecTRI/OmniPath identity、external contextual integration、冲突归零审计、family-native LOFO 与实现脚本 SHA 绑定。经用户授权继续后，S1C-A/v1 已用原生 CellOracle `TFdict` 构建 Gata6/Ctnnb1 target-compatible adapter，S1C-B/v3 在真实 CellOracle 0.22.0 上完成 2/2 synthetic fit/simulate smoke 并通过进程退出后的 stable manifest 自校验；S1D/v3 又获得 GSE5298/GSE9652 两个 Gata4 与 GSE78125 一个 Ctnnb1 的 E9.5 exact-stage、组织限定 processed perturbation context，并完成 sample/mapping/effect provenance。

**2026-09-02 收口**：T3-S1 链已正式收口为 `CLOSED_AS_RESEARCH_COMPONENT`（[`artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md`](artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md)）。同日独立的 gate 可满足性审计（`T3-S1C-GATE-SATISFIABILITY-20260902-v1`）判定 `UNSATISFIABLE_UNDER_FIREWALL`，两条结论一致：signed family<2、E8.75 state-matched activity 公开不可得、stability 未闭合，且 E8.5–E9.0 窗口目标扰动数据属 target leakage，gate 在当前 firewall 下结构性不可达。候选生成、scorer、上传保持关闭，`blocks_submission: false`；重开条件见收口报告。执行资源已切换至 batch3 `T1-PRE-HARMONIZE`。

详情：[T3_TRACKING.md](docs/coordination/T3_TRACKING.md)

## 下一步总览

| 任务 | 下一步 | 提交前硬要求 |
|---|---|---|
| T1 | `T1-S2-MOSCOT-DECODER-20260902-v1` 服务器仲裁完成：v0007=44.9、v0008=44.8，均低于 best 48.5 与 baseline 47.0，REJECT 为改进，路线关闭；当前 best 仍为 v0004=48.5，不追加 T1 调参 | 分数已回填 `reports/SERVER_SCORE_REGISTRY.md` 与 INDEX.tsv |
| T2 | T2-S3 服务器评分回填：heart_interp **56.7（+0.4）晋级 board best**，embryo 59.7（-0.4）未提升；当前 selection = B1-A1 L1 embryo + T2-S3 L1 heart_interp + baseline extrap；`T2-J1-PROXY` gate PASS，下一方向 FGW assignment candidate | 服务器未返回新 T2/Total（保持 55.7/149.5）；derived T2≈55.8/Total≈149.6 待服务器确认 |
| T3 | S1 链已收口 `CLOSED_AS_RESEARCH_COMPONENT`（2026-09-02）；当前 best 仍为 45.3，不生成新候选 | 重开需满足收口报告第 6 节条件（官方新数据/organizer 放宽/研究分支独立 signed family） |

## 更新规则

每次新版本、参数修改或路线分叉，都要在对应任务追踪文档的“变更记录”追加一行，用一句通俗话说明：

> 把什么改成什么；为什么改；结果是什么；保留还是淘汰。

根目录本文件只在当前 best、Top 3、任务状态或下一步发生变化时更新。服务器分数返回后，先更新 `reports/SERVER_SCORE_REGISTRY.md`，再同步本文件和对应任务文档。
