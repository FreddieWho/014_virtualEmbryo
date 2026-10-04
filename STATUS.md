最新 T1 事件（2026-10-03 INDEX 补登记）：AR-MIX/AR-MIX2 八 lane（v0049–v0056）早先已回分，今日补 canonical 落盘＋INDEX 登记；v0051=53.92 现役（v0054 53.98 TIE 备份，v0049 53.72 高备份），T1 待分仍为零。

最新 T3 回分（2026-10-03）：v0072已登记、REJECT，较现役低0.42；分布小幅改善未抵消DE损失，当前半步试验关闭，现役v0048不变。[复盘](reports/t3_halfstep_20261003/SCORE_REVIEW.md)。

最新 T3 事件（2026-10-03）：v0071回分已登记，不晋级；现役v0048保持。新v0072仅将新增响应强度减半，contract PASS，未提交/未评分；来源诊断不是本地晋级。[下载与复盘](reports/t3_halfstep_20261003/REPORT.md)。

最新 T3 交付（2026-10-03）：v0071 sparse_scale，以现役v0048为母本；来源完整矩阵筛选有界表达强度转换，保留母本零值结构、contract PASS。未提交/未评分，现役不变。[下载与检查](reports/t3_sparse_response_20261003/REPORT.md)。

最新 T3 回分（2026-10-03）：v0070 已登记、REJECT，较现役低2.13；现役v0048不变，当前配置关闭。来源均值MSE优化未转化为目标H5AD收益；统一残差使非零比例10.46%→62.20%。[复盘](reports/t3_autoresearch_score_review_20261003/REPORT.md)。

最新 T2 回分（2026-10-03）：v0030＝51.12（+0.59 vs 基线）晋级新外推 board best（该榜 2026-09-16 后首次易主），v0031＝49.91 REJECT、crosswalk 轴关闭；16 子项已入库。外推现役切到 v0030，T2 待分清零。dev 目标未达成（0.92868 vs 0.90），reserve 仍 NOT_RUN。[复盘](reports/t2_holdout10_score_review_20261003/REPORT.md)。

最新 T3 本地优化（2026-10-02）：48次实验完成确认目标，固定来源域开发MSE降低20.31%；锁定后原test降低6.12%（区间跨零）。保留预测模块，服务器现役不变，无新候选、未提交/未评分。[报告](reports/t3_autoresearch_20261002/REPORT.md)。

最新 T1 事件（2026-09-30）：十一条回分已登记；v0038/v0043同为53.55（较旧best+0.12），v0038现役、v0043同分备份；T1待分清零，均值平移四臂不晋级。[复盘](reports/t1_score_review_20260930/REPORT.md)。

最新 T3 事件（2026-10-01架构回分）：v0066/v0068及10子项已登记，两件REJECT、当前配置关闭、待分清零；A方向最高显示值未抵消DE/共表达损失，B组成未获收益，现役v0048不变。[回分复盘](reports/t3_arch_two_score_review_20261001/REPORT.md)。

# Virtual Embryo 项目状态

更新时间：2026-10-05（只更新导航；选集仍是上面 2026-10-03 的事件，不是新分数）。

上面的日期条目是事件日志，不是现在的选集。现在的选手和文件地图看 [docs/ATOM_MAP.md](docs/ATOM_MAP.md)。

## 第一部分：给人读的进展

**已完成什么。** 三个任务的当前选手都已经回分：T1 是 53.92，心脏往后推是 51.12，T3 是 47.93。混合、外推配方和响应强度扫描都进了平台或已经证明没用。结构入口在 [docs/ATOM_MAP.md](docs/ATOM_MAP.md)。

**正在做什么。** 没有新的提交在跑。下一步要么是新机制，要么等主办方回信和门户合计重读。不要按旧的 batch 提示再开一轮。

**卡在哪里。** 网页上一次确认的三个任务合计仍是 **156.06**。按现在各榜现役相加是 160.64，但这不是网页已经返回的合计，不能当成官方总分。心脏往后推的那一项，新现役是 51.12（v0030，今日刚回分），门户合计待重读确认。另外，我们自己交的“什么都不做”复制件并不是 50 分，所以不能把“超过 50”直接说成已经稳定超过官方的什么都不做。

**准备怎么解决。** 重读一次门户合计。主办方回信之前，同基因的扰动数据继续隔离。没有新机制授权时，不再交混合权重、外推剂量或响应倍率的小变体。

```

2026/9/29
ROADMAP  [##############-] 14/15 节点（N8 仍未正式裁决）
本周投入  科学问题 ████████░░ 80%   基础设施 ██░░░░░░░░ 20%

偏离程度  中
偏离位置  原定“先选方向或封板”的节点一直没有正式裁决，后面的工作是直接做上去的。
         160.07 只是现役相加，不是网页确认的合计。
建议      门户合计仍待确认；用户已单独授权 T3 六项新路线，不以合计对账阻止该执行。
```

## 第二部分：给 agent 的接手信息

- 先读 `docs/00_START_HERE.md`、`docs/ATOM_MAP.md`、`reports/SYNTHESIS_T1.md` / `T2` / `T3`。不要从 `docs/batch*` 提示开工。
- 当前选择：T1 v0051=53.92（v0054 53.98 TIE 备份，v0049 53.72 高备份）；T2 62.89 / 62.36 / 外推 v0030=51.12；T3 v0048=47.93。
- 核心文件：`submissions/INDEX.tsv`、`reports/SERVER_SCORE_REGISTRY.md`、`docs/ATOM_MAP.md`。
- 最近决策：`D-20261005-STRUCT-001`（只改导航，不改选集）；科学决策仍看各任务追踪。
- 下一步：三任务待分为 0。没有新机制授权就不生成候选。T3 重开仍须新增响应依据。
- 未闭合：门户合计仍是 156.06；160.64 只是推导值（53.92+58.79+47.93）。门户 Total 重读后确认。

---

## 比赛细节（以下为本项目原有 STATUS 内容）

完整分数不在本文件重复维护：候选文件与哈希看 [`submissions/INDEX.tsv`](submissions/INDEX.tsv)，服务器分数看 [`reports/SERVER_SCORE_REGISTRY.md`](reports/SERVER_SCORE_REGISTRY.md)，任务细节看 [`docs/coordination/`](docs/coordination/) 下的三个追踪文档。

## 总体状态

- 比赛优先；starter_pack 已关闭为 `CLOSED_FOR_COMPETITION_BASELINE`。
- 门户确认过的合计仍是 **156.06**（2026-09-26 转录）。按现在各榜现役相加的推导值是 **160.64**（53.92+58.79+47.93）。160.64 不是门户已返回的合计。
- 任务分数：T1 **53.92**（v0051，2026-10-02），T2 **58.79**（62.89 / 62.36 / 外推 v0030 51.12），T3 **47.93**（v0048）。
- **未闭合的账**：门户确认过的合计仍是 156.06；推导合计 160.64（53.92+58.79+47.93）待门户页面确认。在此之前不引用推导值为服务器值。
- T3待分已关闭：本轮六件全部回分、无晋级；T1/T2队列以各自权威账本为准。
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

1. `v0051_mix36x38a`：**53.92**，现役（2026-10-02）；混合族 8 条 scored 全入库。
2. `v0054_mix3638even`：**53.98**，TIE 数值最高备份（±0.1 带内，不晋级）。
3. `v0049_mix35x38a`：**53.72**，高备份（超旧 best 0.17，落后现役 0.20，不并列晋级）。

同批精确同分按用户供给列表顺序登记，非上传先后证据。历史见[T1_TRACKING.md](docs/coordination/T1_TRACKING.md)，复盘见[报告](reports/t1_score_review_20260930/REPORT.md)。

### T2 — spatial-temporal

1. 当前 per-board selection：`v0014` embryo **62.89** + `v0019` heart_interp **62.36** + `v0030` heart_extrap **51.12**（2026-10-03 新 best；上一任 baseline 50.53）。
2. 前任 `v0011 L1_SHRINK` heart_extrap **50.64** 已被 v0030（51.12）取代；更早的未晋级最高 50.74（v0022，未并列）一并退为参照。
3. T2-J1 v0009 heart_interp **57.25** 已被 v0013 取代。

T2 三条 board 的现役机制不同：embryo/heart_interp 是"均值+组成桥"（几何沿用 pycpd 插值结果），heart_extrap 是中位数位移＋library 守恒（v0030，5 共享态）。

Batch3 `T2-J1-FGW-ASSIGNMENT-20260903-v1`：heart_interp v0009 服务器 **57.3（+0.6 vs v0007 56.7）** 晋级 board best（2026-09-04 回填）；embryo_interp v0008 未上传，保持 `HOLD_AS_COMPONENT` 不可变。

详情：[T2_TRACKING.md](docs/coordination/T2_TRACKING.md)

### T3 — gene perturbation

1. v0048 n2hurdle：**47.93**，已评分，当前best。
2. v0046 o2shrink：**47.65**，已评分备选。
3. v0034 r6meanfix：**47.53**，已评分备选。

v0049–v0059 十一条已全部回分：最高 v0058 47.95（平局），v0056/v0059 精确打平 47.93，都不晋级。以下为历史研究记录。

Batch2 `B2-T3-A1` 的 v0006/v0007 后来已评分 45.5，并被后续版本超过。这里不再把它们写成待评分。

Batch3 `T3-S1-PRIOR` 已形成 prior/gate bundle：31,458 条 state×gene 记录，L1/L2 非零分别为 2,050/5,125；用户授权后的本地方法部署与 CollecTRI/OmniPath panel-scoped 内容审计均为 `PASS`。正式分析前的 5 个 current parent contract/registry SHA256、protected-field/round-trip 复核和实际 22 项接口测试均已闭合；directed-evidence 组件为 `COMPONENT_PASS`，但 candidate admission 仍 `HOLD`，这些预检不等于 state-specific activity validation。β-catenin 相关 prior 仍显式为 `sign=0/EXTERNAL_KNOWLEDGE_AUDITED_NOT_INTEGRATED`，S1 prior 未消费 state-joined evidence。prior/gate 仍为 `HOLD_AS_COMPONENT`，原因是 stability sensitivity；不进入 H5AD 或候选生成。

T3-S1A v7 已完成 exact E8.75 input/state join、显式 target applicability、Gata4 CellOracle real API、三条 scTenifold 输出、full-matrix state-response/coverage 审计和 hash-bound route audit；随后 S1B v3 已完成 full CollecTRI/OmniPath identity、external contextual integration、冲突归零审计、family-native LOFO 与实现脚本 SHA 绑定。经用户授权继续后，S1C-A/v1 已用原生 CellOracle `TFdict` 构建 Gata6/Ctnnb1 target-compatible adapter，S1C-B/v3 在真实 CellOracle 0.22.0 上完成 2/2 synthetic fit/simulate smoke 并通过进程退出后的 stable manifest 自校验；S1D/v3 又获得 GSE5298/GSE9652 两个 Gata4 与 GSE78125 一个 Ctnnb1 的 E9.5 exact-stage、组织限定 processed perturbation context，并完成 sample/mapping/effect provenance。

**2026-09-02 收口**：T3-S1 链已正式收口为 `CLOSED_AS_RESEARCH_COMPONENT`（[`artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md`](artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md)）。同日独立的 gate 可满足性审计（`T3-S1C-GATE-SATISFIABILITY-20260902-v1`）判定 `UNSATISFIABLE_UNDER_FIREWALL`，两条结论一致：signed family<2、E8.75 state-matched activity 公开不可得、stability 未闭合，且 E8.5–E9.0 窗口目标扰动数据属 target leakage，gate 在当前 firewall 下结构性不可达。候选生成、scorer、上传保持关闭，`blocks_submission: false`；重开条件见收口报告。执行资源已切换至 batch3 `T1-PRE-HARMONIZE`。

详情：[T3_TRACKING.md](docs/coordination/T3_TRACKING.md)

## 下一步总览

| 任务 | 下一步 | 提交前硬要求 |
|---|---|---|
| T1 | v0051=53.92现役，v0054 TIE 备份（53.98）；混合族饱和 ~53.7 | 八 lane 全部scored，T1待分清零；混合族内调参无服务器意义 |
| T2 | 胚胎 62.89、心插 62.36 双晋级。外推 v0030=51.12 现役 | 门户 Total 待重读（推导 160.64 待确认）；同族调参已入平台期 |
| T3 | best v0048=47.93，v0058 平局备份不变 | 两架构已评分REJECT、待分0；科学增量未确立，blocks_submission: false |

## 更新规则

每次新版本、参数修改或路线分叉，都要在对应任务追踪文档的“变更记录”追加一行，用一句通俗话说明：

> 把什么改成什么；为什么改；结果是什么；保留还是淘汰。

根目录本文件只在当前 best、Top 3、任务状态或下一步发生变化时更新。服务器分数返回后，先更新 `reports/SERVER_SCORE_REGISTRY.md`，再同步本文件和对应任务文档。

- 2026-09-20 T3 R5/R6：已补第二次隔离过滤与用途门；尚未获准训练。下一步为剩余扰动/信号链审查、书面用途确认及shape版完整集成，见 [准备报告](reports/t3_r56_readiness_20260920/REPORT.md)。既有best与待评分队列不变。

- 2026-09-20 T3更新：R5已补齐最小信号链并生成v0032/v0033，合约PASS，未提交/未评分；[交付包](deliveries/r5sig__t3__upload__20260920.zip)。R6仍待审查，书面确认/shape-only为项目内部约束。见[本轮报告](reports/t3_r5_completion_20260920/REPORT.md)。下一步收集服务器分数，best不变。

- 2026-09-29：按已回填分数同步当前选择。T1 best 改为 v0029=52.5；T3 修复三条改为已评分不晋级；T2 低幅度两条改为已评分不晋级。158.72 只记为推导值。旧的“最新事件”横幅不再放在文首，避免和当前选择矛盾。

- 2026-09-29：三批回分。T1 best 改为 v0035=53.43；T2 改为胚胎 62.89 / 心插 62.36；T3 第二轮关闭。推导合计记 159.95（待门户确认）。待分只剩 T3 六条。

最新 T2 回分（2026-10-03 第二轮）：v0032＝51.14（+0.02，TIE 带内不晋级）、v0033＝50.89（REJECT，半剂量削弱 de）、v0034＝51.02（TIE 不晋级）；现役 v0030=51.12 不变，T2 待分清零。服务器确认 de 剂量最优 0.9（与 dev 一致）；recipe 家族进入 ~51.1 平台期，下一波需行集合/几何级新机制或封存。[复盘](reports/t2_holdout10_score_review_20261003/REPORT.md)。
