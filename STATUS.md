# Virtual Embryo 项目状态

更新时间：2026-09-04

## 第一部分：给人读的进展

**已完成什么。** 三个比赛任务都已建立合法提交并拿到服务器分数，当前总分 149.5。最近一轮把心脏插值从 56.3 提到 57.3（位移场 +0.4、表达重排 +0.6 两步），胚胎插值保持 60.1，扰动预测首次超过基线（45.5 vs 45.3，两条并列）；六条新路线里两条晋级、四条被证明无效并已关闭存档。

**正在做什么。** 第三批计划（batch3）的全部任务已执行完毕，此刻没有正在运行的计算。等你从比赛页面读回最新总分，确认我们推算的 149.8 是否成立。

**卡在哪里。** 时间外推任务（T1）停在 48.5：结构化传输和"增长/死亡动力学"两条路都被严格判掉了，剩下的提升空间需要全新想法而不是调参。扰动任务（T3）的预测分数已超过基线（45.5），但它的科学验证在当前数据规则下结构性做不到，已正式收口——分数提升不代表机制验证，两者我们分开记账。

**准备怎么解决。** 不盲目追加实验。T1 等待新假设或接受现状；T3 等待官方新数据或规则放宽；下一步是开辟第四批方向（候选见 TODO.md 与 LEADS.md）还是封板，由你决定。

```

2026/9/4
ROADMAP  [#######-] 7/8 节点（N8 待授权）
本周投入  科学问题 ███████░░░ 70%   基础设施 ███░░░░░░░ 30%

偏离程度  中
偏离位置  T3-S1 链（N3）连续 6 个 atom、约 3 个工作日，最终全部 HOLD/收口，
         未产生任何候选；产出的否定边界真实有价值，但探索深度超出
         "快速证伪"的初衷，且期间 blocks_submission=false 才未耽误主线。
建议      科学 promotion 类探索预设更硬的早期止损：连续 2 个 atom 无阳性
         证据即暂停上报，由人决定是否继续深挖。
```

## 第二部分：给 agent 的接手信息

- 活跃节点：无；batch3 完毕，N8（batch4 方向）待用户授权。
- 核心文件：`submissions/INDEX.tsv`（候选+哈希）、`reports/SERVER_SCORE_REGISTRY.md`（分数）、`docs/coordination/STATUS.md`（并行状态）。
- 复现：`PYTHONPATH=docs/batch3/interfaces /opt/anaconda3/bin/python -m pytest tests/ -q`（174 passed）。
- 最近 DECISIONS：`D-20260904-HX-001`（HX REJECT）；同批 `D-20260904-T2-J1-001`（57.3 晋级）。
- 下一步：等服务器 Total 读数确认 derived 149.8；等 push 与 batch4/封板授权。

---

## 比赛细节（以下为本项目原有 STATUS 内容）

完整分数不在本文件重复维护：候选文件与哈希看 [`submissions/INDEX.tsv`](submissions/INDEX.tsv)，服务器分数看 [`reports/SERVER_SCORE_REGISTRY.md`](reports/SERVER_SCORE_REGISTRY.md)，任务细节看 [`docs/coordination/`](docs/coordination/) 下的三个追踪文档。

## 总体状态

- 比赛优先；starter_pack 已关闭为 `CLOSED_FOR_COMPETITION_BASELINE`。
- 当前 aggregate best：**149.5（服务器当前返回值）**。
- 当前任务分数：T1 **48.5**，T2 **55.7（服务器当前返回值）**，T3 **45.3（服务器当前返回值；board best 已升至 45.5）**。
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

1. `v0004_strict_pseudobulk_shift`：**48.5**，已评分，当前 best。
2. B1-A3 `L2_E95_EXPRESSION_PROBE`：**47.7**，已评分，B1-A3 lane winner。
3. B1-A3 `L1_SHARED_UNRESOLVED`：**47.5**，已评分，scored backup。

详情：[T1_TRACKING.md](docs/coordination/T1_TRACKING.md)

### T2 — spatial-temporal

1. 当前 per-board selection：B1-A1 L1 embryo 60.1 + T2-J1 v0009 `j1_fgw_assignment` heart_interp **57.3** + baseline heart extrap 50.5；服务器 T2 **55.7**、Total **149.5**（derived T2≈55.97/Total≈149.8 待服务器确认）。
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
| T1 | `HX-DYNAMICS-KILLTEST-20260904-v1` 完成：MIOFlow（增长/死亡+随机动力学）在预声明 kill metric（留 E9.5 state-mass L1）上 0.7475，未同时优于 moscot 0.6645 与 parent 1.1894 → **REJECT**，方向关闭；当前 best 仍为 v0004=48.5，无新授权不追加 T1 atom | kill test 只出 report，不生成候选；分数已回填的候选见 `reports/SERVER_SCORE_REGISTRY.md` 与 INDEX.tsv |
| T2 | J1-FGW heart_interp v0009 服务器 **57.3（+0.6）晋级 board best**（2026-09-04 回填）；embryo v0008 保持 HOLD 不上传；**batch3 全部任务执行完毕**（`HX-DYNAMICS-KILLTEST` 已 REJECT，见 T1 行） | 服务器未返回新 T2/Total（保持 55.7/149.5）；derived T2≈55.97/Total≈149.8 待服务器确认 |
| T3 | B2-T3-A1 v0006/v0007 双双 **45.5（+0.2）** 并列晋级 board best（2026-09-04 回填，首次超过 wt_identity 45.3）；科学 gate 仍收口 `CLOSED_AS_RESEARCH_COMPONENT`，leaderboard 增益不解除 gate | derived T3=45.5/Total≈149.7 待服务器页面确认；重开条件见收口报告 §6 |

## 更新规则

每次新版本、参数修改或路线分叉，都要在对应任务追踪文档的“变更记录”追加一行，用一句通俗话说明：

> 把什么改成什么；为什么改；结果是什么；保留还是淘汰。

根目录本文件只在当前 best、Top 3、任务状态或下一步发生变化时更新。服务器分数返回后，先更新 `reports/SERVER_SCORE_REGISTRY.md`，再同步本文件和对应任务文档。
