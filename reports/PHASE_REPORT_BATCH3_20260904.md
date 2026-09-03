# Batch 3 综合评审报告

报告日期：2026-09-04  
报告状态：`COMPLETE`（全部计划任务执行完毕，无 active atom）  
评审对象：Virtual Embryo Challenge Batch 3（`docs/batch3/`，执行窗口 2026-08-30 至 2026-09-04；artifact 根 `artifacts/tool_integration/`）

## 0. 阅读说明与结论边界

本报告不使用外部文献、网页或其他正式引用，也不把项目内部报告包装成外部依据。文中的文件路径、candidate ID、指标名称只是项目内部证据定位锚点；候选完整路径与 SHA256 以 `submissions/INDEX.tsv` 为准，服务器分数与原始回填记录以 `reports/SERVER_SCORE_REGISTRY.md` 为准，逐 atom 的决策日志以 `docs/coordination/DECISIONS.md` 为准。

本报告的目标是让读者仅凭本文判断：

1. Batch 3 是否按其方案约束执行；
2. 每条路线的结果属于服务器反馈、本地诊断还是纯组件建设；
3. 被关闭的路线失败在哪里、被保留的路线潜力在哪里；
4. 后续（batch4 或封板）应该做什么。

结论保持克制：Batch 3 证明了 POT-FGW 软配对与 pycpd 位移场两条工具路线在 T2 窄间隔插值 regime 有服务器验证的改善；证明了 moscot 结构化外推与 MIOFlow 增长/死亡动力学在 T1 上不胜出 strict-shift；证明了 T3 的科学验证 gate 在当前数据 firewall 下结构性不可达。它没有证明任何生物学机制、因果关系或跨任务泛化规律。

## 1. 执行摘要

### 1.1 总体结果

Batch 3 的方案目标是：**测试已有工具能否比较好地完成比赛目标，或具备优化潜力**。计划的 8 条路线全部执行完毕：

| 路线 | 工具 | 计划终点 | 实际完成 | 结果概括 | 当前处理 |
|---|---|---|---:|---|---|
| T3-S1-PRIOR + S1A/S1B/S1C/S1D 链 | CellOracle 0.22.0 / scTenifoldKnk 1.1 / CollecTRI / OmniPath | T3 prior→候选 | 13 个 atom 版本，0 候选 | 工具部署与审计全 PASS；E8.75 state-matched 证据不可得，gate 判定 `UNSATISFIABLE_UNDER_FIREWALL` | `CLOSED_AS_RESEARCH_COMPONENT`（2026-09-02），重开条件写死 |
| T1-PRE-HARMONIZE | 自建词表/crosswalk | T1 状态词表前置组件 | 1 atom，0 候选 | 28 union fine_state + 严格 crosswalk；锁定 full-panel scorer 实测跑通 | gate PASS，组件被 T1-S2 与 HX 复用 |
| T1-S2-MOSCOT-DECODER | moscot 0.5.2 | 双 lane T1 候选 | 2 候选 | 服务器 44.9 / 44.8，均低于 best 48.5 与 baseline 47.0 | **REJECT，路线关闭**；候选不可变保留 |
| T2-S3-SHAPE-FIELD | pycpd 2.0.0 / spateo | 双 lane × 3 board | 6 候选 | heart_interp 56.7（**+0.4**）晋级；embryo 59.7（−0.4）；外推 regime 无证据 | L1 heart_interp 晋级后又被 J1 超越；L2 全部 REJECT |
| T2-J1-PROXY | POT 0.9.7 entropic-FGW | 条件 gate（不生成候选） | 1 atom | 两个独立 holdout 上 NFS-like 0.012/0.015 vs random 0.137/0.172，7/7 criteria | `J1_PROXY_PASS`，授权正式 assignment |
| T2-J1-FGW-ASSIGNMENT | POT（冻结 spec） | embryo + heart_interp 候选 | 2 候选 | heart_interp 57.3（**+0.6**）晋级 board best；embryo 本地证据不足 | heart 晋级当前 selection；embryo HOLD_AS_COMPONENT |
| HX-DYNAMICS-KILLTEST | MIOFlow 0.1.14 | 单假设 kill-test report | 1 atom，0 候选 | 预声明 kill metric 未达成：mioflow 0.7475 vs moscot 0.6645 vs parent 1.1894 | **REJECT，方向关闭** |

净收益：**T2 heart_interp 56.3 → 57.3（+1.0）**；服务器返回值保持 T1 48.5 / T2 55.7 / T3 45.3 / Total 149.5（服务器未随单 board 提交返回新聚合值）。按 per-board best 选择推算 derived T2≈55.97、derived Total≈149.8——**仅为协议推算值，待服务器页面确认，不得引用为服务器值**。

### 1.2 当前竞争选择

- T1：`candidate/T1_val/v0004_strict_pseudobulk_shift`，48.5（batch3 未撼动）；
- T2：B1-A1 L1 embryo 60.1 + T2-J1 v0009 `j1_fgw_assignment` heart_interp 57.3 + baseline heart_extrap 50.5；
- T3：`baseline-001/T3_gata4/v0001` `wt_identity`，45.3（batch3 未生成任何 T3 候选）。

### 1.3 最重要的判断

1. **成败分野在归纳假设，不在工具工程。** 六条路线涉及的五组外部工具全部部署成功、审计通过、按预期运行；阴性结果（moscot、MIOFlow、spateo lane、T3 链）没有一条可归因于工具失效。
2. **结构化先验在 T2 插值 regime 有效且已兑现。** pycpd 位移场（+0.4）与 FGW 配对（+0.6）相继在 heart_interp 上被服务器验证；两者的效域都限于窄间隔插值，外推 regime（H4 holdout）无任何本地证据。
3. **T1 的可行空间被双向收窄。** moscot 结构化外推被服务器双否；HX kill test 进一步证明失败不在 state-mass 环节（moscot mass 已显著优于 strict-shift，0.66 vs 1.19）。T1 剩余嫌疑集中于表达内容本身；重启需要全新假设而非调参。
4. **T3 是证据环境失败，不是工具失败。** CellOracle real API、scTenifoldKnk 版本匹配、双源快照审计全部 PASS；但 E8.75 state-matched 扰动证据公开不存在，近窗口数据属 target leakage。收口处置正确，重开条件已写死。
5. **FGW 是唯一"已验证且留有后手"的路线。** ε=0.005 导致 72–73% 分配冲突是已知的、可机制的改进杠杆（见 LEADS L-002）；embryo 侧的 HOLD 只差一次同靶 parent scorer 参照即可闭环（LEADS L-001）。

## 2. 原始方案与执行范围

方案文档：`docs/batch3/`（`00_START_HERE.md`、`02_EXECUTION_ORDER_AND_GATES.md`、`04_DECISION_RULES.md`、任务卡 `prompts/`）。核心约束：single_task 串行、seed 20260830、artifact 落 `artifacts/tool_integration/<TASK>-<YYYYMMDD>-vN/`、不自动上传服务器、不网格搜索、BLOCKED 须写清对象/已完成/最小解除条件、核心计算不得静默降级。

执行偏差：无方案级偏离。两处经记录的计划内演进——(a) J1-PROXY 的 objective_spec 在首个 holdout 后按修订流程修正 null 设计（"标签内行打乱"被实证为该 objective 的精确对称），修订记录写入 spec 与 config deviations；(b) HX 任务卡于 2026-09-04 由 coordinator 实例化（工具/board/kill metric/预算/阈值一次性写死，FROZEN→ACTIVE）。

## 3. 过程审计

- **执行模式**：全部重活由委派 coder 子代理执行，coordinator 独立核验（manifest 自校验复跑、SHA 抽查、测试复跑、预声明时间戳核查）后裁定 gate。所有 atom 的裁定均为 coordinator 确认。
- **不可变性与自校验**：每个 atom 产出 stable manifest（文件×SHA256），本批全部自校验 PASS：T1-PRE 15 文件、T1-S2 44 文件、T2-S3 157 文件、J1-PROXY 46 文件、J1-FGW 40 文件、HX 18 文件，T3 链各版本（v6/v7、S1B v3 27 文件、S1C 系列、S1D v3 14 文件）此前均已核验。
- **测试基线演化**：103（T1-PRE）→ 148（J1-PROXY）→ 162（J1-FGW）→ **174 passed**（HX，2026-09-04 全量复跑确认）。命令：`PYTHONPATH=docs/batch3/interfaces /opt/anaconda3/bin/python -m pytest tests/ -q`。
- **外部部署审计**：本批新增两个隔离环境，均固定版本+SHA256+license 披露——`.venvs/ve-t1-ot`（moscot 0.5.2/POT 0.9.7/ott，T1-S2 起）与 `.venvs/ve-hx-mioflow`（mioflow 0.1.14，torch 2.2.2+cpu；**Yale 非商业许可**已披露）。HX 部署后网络窗口关闭，计算阶段 `allow_network: false`。
- **上传链路**：命名规则固化（成员名 `<task>_<board>__<lane>__vNNNN.h5ad` ≤50 字符，zip 附 MANIFEST.tsv，写入 AGENTS.md 与 submissions/README.md）；本批三个人工上传包（T1-S2 旧长名包、`t2s3__t2__upload__20260903.zip`、`t2j1__t2__upload__20260903.zip`）全部完成服务器评分回填，登记链路完整。

## 4. 结果与证据解读（逐路线）

### 4.1 T3-S1 链：工具可用，证据环境锁死（收口）

链路：S1-PRIOR（31,458 条 state×gene 记录 bundle）→ S1A v5–v7（exact E8.75 state join；Gata4 CellOracle real API PASS；Gata6/Ctnnb1 因 base-GRN 缺可扰动 TF source 明确不适用）→ S1B v3（CollecTRI/OmniPath full snapshot identity、external contextual integration、LOFO）→ S1C-A/B（target-compatible TFdict adapter + 真实 CellOracle synthetic smoke 2/2 PASS）→ S1D v3（GSE5298/GSE9652/GSE78125 三份 E9.5 组织限定 processed perturbation context，审计通过但非 state-matched）→ S1C-GATE-SATISFIABILITY（2026-09-02）判定 `UNSATISFIABLE_UNDER_FIREWALL` → T3-S1-CLOSURE 收口（CLOSURE_REPORT SHA256 `0184ebf1…f0d44`）。

判读：三条未满足硬条件（independent signed family < 2、E8.75 activity NOT_IDENTIFIABLE、stability 未闭合）均为证据环境约束；firewall 禁止的 E8.5–E9.0 窗口正是唯一可能有公开数据的区间。重开条件见收口报告第 6 节。全程 `blocks_submission: false`，未影响比赛主线。

### 4.2 T1-PRE-HARMONIZE：组件成功

28 个 union fine_state（11 SHARED_EXACT / 7 SOURCE_ONLY / 10 TARGET_ONLY），crosswalk 前向 13/18 解析、5 UNRESOLVED 无强配；锁定 full-panel scorer 实测 exit 0、323s。两条非 exact 边 bootstrap recovery 仅 0.40–0.50 已如实记录——后续 atom 应把非 exact 边当软证据（T1-S2/HX 均照此执行）。manifest SHA256 `e2f28890…98413`。

### 4.3 T1-S2-MOSCOT-DECODER：服务器双否，路线关闭

moscot TemporalProblem 在 state/program latent 求 E8.5→E9.5 coupling（converged，234 非零 transition），state-mass forecast（clip/收缩，alpha=1.0127 一次解析冻结）+ state-specific mean delta；L1 empirical residual replay / L2 scDesign3 1.6.0 双 lane，5118×32285，contract/protected 全 PASS。本地 pseudo-holdout 已示警（parent 臂 de_score 0.6226 vs L1 0.4528 / L2 0.4340）；服务器仲裁 v0007=44.9、v0008=44.8，低于 best 48.5 与 baseline 47.0。失败假设：两天跨度外推中传输耦合携带的信息不敌 strict-shift 的保守性。manifest SHA256 `461fb337…d93e2`。

### 4.4 T2-S3-SHAPE-FIELD：窄间隔有效，效域清晰

从相邻实测 stage 对学平滑位移场（1500 celltype 分层 landmark、Gaussian 场 beta=1.0），解析时间系数施加到 parent 点云后 RMS 回锁。L1 pycpd（PCA canonical + 4-flip Chamfer + rigid polish + deformable CPD alpha=2.0）：H1/H2 holdout 三 proxy 全胜、H3 宽间隔全负、H4 外推全负；L2 spateo：4/4 全负 + heart_extrap kNN CATASTROPHIC（保护机制按设计触发）。服务器：embryo 59.7（−0.4，未晋级）、heart_interp 56.7（**+0.4**，当时晋级）。H1 全胜却 −0.4 实证了"窄间隔 holdout 获益不保证 board 获益"。manifest SHA256 `4ffef666…f8a76`（157 文件）。

### 4.5 T2-J1：batch3 最完整的证据链

PROXY 阶段：objective spec 先冻结（POT entropic FGW，alpha=0.5、eps=0.005、square_loss、PGD、均匀边际、表达 PCA30 + 内部距离 cost、max 归一；SHA256 `4cf86109…110e7`），两个独立 leave-one-stage-out holdout 上 NFS-like 0.012/0.015 vs random 中位 0.137/0.172（64 随机无一更优），label-only/scrambled-reference 对照均差于 random——改善依赖真实表达-位置信息。7/7 criteria，`J1_PROXY_PASS`。caution 记录：heart 参考跨 1.25 天、标签交集仅 5，holdout 逐位置 pearson 为负。

ASSIGNMENT 阶段：heart 参考按预声明标准审视 PROCEED（跨度 0.50、标签交集 33、探针弱正 +0.0138）；全量求解无子采样；`column_argmax_margin_greedy_v1` 离散化双射 PASS（conflicts 72.2%/73.3%）；objective 同靶 embryo −12.2%、heart −26.6%；坐标/obs/var/kNN 图/表达 multiset 与 parent 精确一致；重跑字节一致。embryo 因 NFS 镜像 no_improvement（0.0312→0.0344）+ 负探针裁定 HOLD 不上传；heart 本地混合证据（nmmd 0.0967→0.0747 改善 vs morans 0.7365→0.6743 变差）以 READY（弱置信）提交，服务器 **57.3（+0.6）正向仲裁晋级**。manifest SHA256 `be8f8943…284da`（40 文件）。

### 4.6 HX-DYNAMICS-KILLTEST：快速、便宜、不留争议的否定

唯一假设：增长/死亡+随机动力学改善 state-mass 外推。kill metric 先于运行写死（留 E9.5 per-state mass L1，须同时严格优于 strict-shift parent 与 moscot 双臂；config 时间戳 04:15 早于训练产物 05:06）。MIOFlow 一次训练（库默认超参、3000+3000 细胞、wall 2747s < 7200s cap）。三臂 L1：parent 1.1894 / moscot 0.6645 / **mioflow 0.7475** → REJECT。副产品：moscot 的 mass 环节不是 T1-S2 失败点；mioflow 在 8/14 state 更准但 Pericardium/pPHM/BEC/aSHF 四态反向失误吃掉全部收益（明细 `intermediates/mass_predictions.tsv`）。manifest SHA256 `b10082e2…4533b`（18 文件）。

## 5. 证据层级（供评审采用）

1. **服务器分数**（最高）：heart_interp 56.7→57.3 两次晋级；T1-S2 44.9/44.8 否定。仅作 per-board 选择依据，不作机制证据。
2. **source-only 预声明 holdout + 随机/对照臂**：J1-PROXY 的 NFS-like 对照、T2-S3 的 H1–H4、HX 的三臂 kill metric。筛选有效，不保证 leaderboard。
3. **本地 scorer pseudo-target**：训练期 stage，存在结构性偏袒（T2-S3 已记录），仅作方向参考。
4. **组件级审计**（不产生分数证据）：contract/protected checks、manifest 自校验、部署审计、确定性重跑。

## 6. 下一阶段方案评估

按期望值排序（详见根目录 `LEADS.md`，仅收录有明显潜力者）：

- **L-002（batch4 首选）**：FGW ε 敏感性——ε=0.005 致 plan 分散、conflict 72–73%；更小 ε 可能集中 plan、增强 board 效应。授权时须把 2 值对照写明为敏感性分析而非网格搜索。
- **L-001（证据闭环）**：embryo v0008 补同靶 parent scorer 参照（约 200s）；定位是把 HOLD 闭环为确证，翻盘概率低。
- 已关闭不再投入：T1 moscot 外推、MIOFlow 增长/死亡、spateo lane、T3-S1（重开条件见收口报告 §6）。
- 无本地证据支撑、暂不立项：heart_extrap（外推 regime 只能靠服务器盲试，期望不足）。

## 7. 结论分级

- **服务器级证实**：FGW 配对与位移场在 heart 窄间隔插值各值 +0.4–0.6 分；moscot 双 decoder 在 T1 E10.5 外推不敌 strict-shift。
- **本地强证据（未上服务器）**：FGW objective 的改善依赖真实表达-位置信息；位移场效域限于窄间隔；moscot mass 预测优于 strict-shift（故 T1-S2 失败不在 mass）；MIOFlow 增长/死亡不能进一步改善 mass。
- **不可判定**：embryo 板 FGW 配对的 board 效应（证据不足，候选 HOLD）；任何外推 regime 路线（无本地验证手段）。
- **明确排除**：把 T3 gate 缺口归因于工具链；把 leaderboard 分数当作机制因果证据。

## 8. 收尾状态与交付面

Batch 3 全部计划任务执行完毕，无 active atom；任何新计算需新的明确授权。交付面：

- 本报告：`reports/PHASE_REPORT_BATCH3_20260904.md`；收尾变更日志：`reports/RELEASE_CHANGELOG_BATCH3_20260904.md`；
- 状态入口：`STATUS.md`（含 PLAN/ROADMAP/TODO/LEADS/DECISIONS 文档体系）、`docs/coordination/STATUS.md`；
- 服务器登记：`reports/SERVER_SCORE_REGISTRY.md`；候选登记：`submissions/INDEX.tsv`；
- 不可变 artifact：`artifacts/tool_integration/` 下 T3-S1 链各版本、T1-PRE-HARMONIZE-20260902-v1、T1-S2-MOSCOT-DECODER-20260902-v1、T2-S3-SHAPE-FIELD-20260903-v1、T2-J1-PROXY-20260903-v1、T2-J1-FGW-ASSIGNMENT-20260903-v1、HX-DYNAMICS-KILLTEST-20260904-v1；
- 人工上传包：`deliveries/`（T1-S2 包、`t2s3__t2__upload__20260903.zip`、`t2j1__t2__upload__20260903.zip`）。

最终建议：把 Batch 3 作为一次"工具假设边界已测绘"的竞争实验冻结——T2 插值方向两条路线兑现分数且 FGW 留有后手，T1 两个方向干净关闭，T3 被证据环境锁死。下一阶段应只做 LEADS 中有明确潜力的条目（L-002 优先），不为已关闭方向追加任何形式的微调。
