# T1 任务追踪：single-cell temporal

更新时间：2026-09-21

分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。本文件只做简短解释和路线选择。

## 当前状态（2026-09-21）

- selection保持v0004 strict pseudobulk shift；v0019最高观测值按原TIE规则未晋级。精确分数以SERVER_SCORE_REGISTRY为准。
- D1/D3/D4/D6及D5b已完成并未晋级；D2稳定版未过门，原调参分支保留为待决定，未自动启动。D5b最终RESULT明确失败、未生成v0026，订正本页旧尾部“训练完成、本地建门中”的滞后摘要。
- 新六路线方案已准备：`reports/T1_NEXT_ROUTES_20260921.md`。建议R2残差decoder→R1分布形状→R5依赖结构→R3稳定动力学→R4模块运输→R6早期时间数据；全部PROPOSED / NOT_RUN。
- 官方E7.75未发布；官方RNA仅有celltype元数据，不能宣称独立胚胎留出。无新候选，无训练，无上传。

## 历史 Top 3 路线（2026-09-02，非当前重新排名）

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

2026-09-05（batch4 Wave 1）：`B4-T1-R1-CONSERVATIVE-FAMILY` 完成，四 lane 待上传评分——v0011（L1 damp0.5，damp=1.0 字节复现 v0004）、v0012（L2 popmix，shift 与 v0004 重叠行逐值一致）、v0013/v0014（L3/L4 mass graft 0.25/0.50，obs-identity 记 FAIL_BY_DESIGN_ACCEPTED）；contract 服务器维度全过，行追溯 ledger 全断言通过，4× 本地 scorer 仅排序/防灾难。产物 `artifacts/batch4/B4-T1-R1-CONSERVATIVE-FAMILY-20260904-v1/`，交付包 `deliveries/b4t1r1{a,b,c,d}__t1__upload__20260904.zip`（推荐顺序 L1→L2→L4→L3）。结论待服务器仲裁。

2026-09-05（batch4 Wave 1）：`B4-T1-R1-CONSERVATIVE-FAMILY` 四 lane 服务器仲裁——v0011=**47.58**（-0.89）、v0012=**47.77**（-0.70）、v0013=**47.85**（-0.62，族内最优）、v0014=**46.90**（-1.57，低于 floor）；v0004=48.47 留任，保守族晋级路线关闭。26 个子项中 T1 占 16，已入库。详见 registry §B4-T1-R1 与 DECISIONS D-20260905-WAVE1-001。

2026-09-17（G0 15 轮目标）：`G1-T1-R1..R5` 七 lane 服务器仲裁——v0015=**48.51**（+0.04）/v0019=**48.54**（+0.07）落入 TIE 带，v0018/v0020=**48.48**（+0.01）TIE，v0016=**48.14**/v0017=**47.46**/v0021=**48.34** REJECT；selection 保持 v0004（48.47）。收缩 sweep 跨度仅 0.20，C 为弱旋钮，关闭。T1 本地 proxy 方向存活（三任务唯一正对照）。详见 registry §G1-T1 与 DECISIONS D-20260917-G0T1-001。

2026-09-17（T1-P0-1 开工门槛）：reset brief §9–§12 重读完毕——D5/D6/D3/OPT-A 对 §12(2) 非自主分支生成，D7＋OPT-A(c) 对 §12(1) 开放集多锚点；缺口：“外部时序预训练”无直接对应 lane、全转录组 decoder 待代码评估单列，记入 P0-2 仲裁；§10 四禁令（禁 target 反推、禁 proxy-win 即晋级、禁 validation 当 test、禁动 scored artifact）D 系均遵守；§11 floor 门延续（新 lane 只比 best，不重释 floor）。contract 核对：T1 background=[E7.75]（task_contracts.yaml 第 23 行），D7 合法。P0-2/P0-3 执行中。

2026-09-17（T1-P0-2 检索-评估＋仲裁）：OPT-A scIMF ✅（论文 PLOS Comp Biol 2026 pcbi.1013916＋代码 QiJiang-QJ/scIMF；scTimeBench forecast 最优）；OPT-B CellMNN 论文 ✅（ICLR 2026＋coherence 最优与 scNODE 并列）但代码 URL 未定位（OpenReview CAPTCHA；czi-ai/cell-mnn 判为同名假友，禁直接复用；D2 按论文实现）；D3 TorchCFM ✅（atong01/conditional-flow-matching）；D5 SquidDiff ✅（siyuh/Squidiff，Nature Methods 2025）；D6 PRESCIENT 接受为已知包；D4 锚点 ✅（mass_plan_heart.tsv＋ledgers＋L1/L2 h5ad 本地齐）；D7 ❌ 数据 blocked（E7.75.h5ad 本地无，官方 911MB 登录下载，OFFICIAL_SYNC 已定性 optional）。引文订正：scTimeBench 为 bioRxiv 预印本（非 Bioinformatics 期刊）＋9 方法（非 10），实质结论（forecast scIMF 最优、lineage 全员最难、pseudotime 救 lineage）成立且支持保守姿态。仲裁出场序：D4 → D2 → D3 → D1 → D6/D5 → D7（解 block 后）。R1 实测 wall 768s：D2/D3/D4 原型先走 CPU，GPU 只租 D1/D5 级。详见 DECISIONS D-20260917-T1P02-001。

2026-09-17（T1-P1 D4 起跑）：`G1-T1-D4-BRIDGE-20260917-v1` 执行中（脚本 `scripts/g0/t1_d4_bridge.py`）——门 G（E8.5→E9.5 回报：G1 份额锚定 vs G0 纯位移，不过则停、不建候选）；过门后双 lane：L1 v0022 fine-state 位移＋收缩份额 k=0.25 重采样（B4-L3 剂量先例固定值）vs L2 v0023 纯位移（组成消融）。后台任务运行中，门结果回包后仲裁。

2026-09-17（T1-P1 D4 门 FAIL 关闭）：G0 纯位移回报 de **0.566**/dir **0.6127** vs G1 份额锚定 de **0.4151**/dir **0.5869**——G1 双低于 G0（−0.151/−0.026），组成锚定无回报信号，按预声明停建候选，D4 关闭。组成雷区第四确认（v0002/B4-graft/今回报消融）。门臂 contract FAIL 仅 cell_limits（16,787 行诊断件超 5,118 板限），实质项全 PASS，分数比较有效。详见 run 内 RESULT.md 与 DECISIONS D-20260917-T1D4-001。P2 进 D2。

2026-09-17（T1-P2 D2 写码完成）：`scripts/g0/t1_d2_cellmnn.py` 落盘（编译通过）——单 MLP＋lineage 条件（用户裁决前者）、富集门从宽（用户裁决）；PCA 取 centered 版＋均值回加（1 行偏差备案）；torch CPU 16 线程；冒烟（dz=10）后台运行中，过则全量 dz=50（90 分钟 cap）。设计稿 §6 已记两条裁决； repo 不 clone。

2026-09-17（T1-P2 D2 冒烟通过＋null 门生效）：dz=10 全链路通（contract PASS）；富集初值 **10.38**（PCA 结构空赢实锤）vs 训练后 **22.84**（学习增量 ×2.2），null 门按设计扣掉空赢；机制声称双条件（>1 且 >初值）冒烟即满足。全量 dz=50 已起跑（90 分钟 cap），回包报三数。

2026-09-17（T1-P2 D2 首跑 VOID）：proxy 看似过（de 0.9434/dir 0.9519）但 step-41 NaN，
候选出自仅见 ~8k 细胞的早停模型——设计的 lane 没跑出来，按门 intent 判 VOID，不注册
v0022、不上传。伴随分布坍缩签名（variance 0.21/energy 6.48/library 0.84），富集数一并作废。
疑凶：L_inv=1/(det+eps) 在 50 维奇异。修复：warmup ramp（50..200 步）＋既有 guards，单次重跑；
再 NaN 则降 dz=20 或关 D2。详见 run 内 RESULT_VOID_01.md 与 DECISIONS D-20260917-T1D2-001。

2026-09-17（T1-P2 D2 warmup 重跑仍 NaN）：死亡推迟 41→88 步，未治愈；proxy de 0.7547/
dir 0.7581 双低于门（与 dz=10 冒烟 de 完全同值 0.7547，欠训模型输出坍缩到同一结构，存疑不追）；
富集训练后 2.08 < 初值 6.23（训练越练越差），机制双条件挂零。按预案降 dz=20（新目录
G1-T1-D2R2-DZ20，审计分离），脚本加 --dz 开关。若再败则关 D2 进 D3（届时请示）。

2026-09-17（T1-P2 D2 调参挂起＋D3 开工，用户裁决 D-20260917-T1P23-001）：D2 不关闭——dz=20 加 patience/调参挂起入 TODO 暂缓（触发条件 D3/D1 双败或另行指示；注意这踩调参红线，已获用户特批）；执行分支切 D3 OT-CFM。

2026-09-17（T1-P2 D3 起跑）：`G1-T1-D3-FLOW-20260917-v1` panel 原型执行中（脚本 `scripts/g0/t1_d3_flow.py`；vendor torchcfm 7c65385 MIT＋POT 0.9.7；top-500 HVG＋E8.5 冻结 scaler；MLP 场 3×256；门 G-return：场积分回报 vs 同空间 per-type-shift 双指标 energy＋cosine，不过则停、不进全基因）。冒烟后台运行中。

2026-09-17（T1-P2 D3 冒烟链路通、门挂）：100 基因小网全链路通；场回报 energy 0.5655 < 基线 0.6123（分布胜）但 cosine 0.4289 < 0.5197（方向负），门按双指标判 FAIL——冒烟规模不作 verdict。panel 全量（500 基因、3×256、2000 步）已起跑，回包再仲裁。

2026-09-17（T1-P2 D3 scaler bug 作废首轮）：E8.5 冻结 scaler 把 9 个 E8.5 零方差维放大 1e8 倍，基线 energy 失真到 ~1.9e4（独立重算复现 1.6e4，同量级，证非偶发）；场 cosine≈0 亦不可信。改合并训练集 z-score＋下限 1e-3（DESIGN 已备案），panel 全量重跑。冒烟数同废止（同 scaler）。

2026-09-17（T1-P2 D2 dz20 稳定但挂门）：410 步无 NaN（降维治愈发散）；proxy de 0.8113/dir 0.8652 双低于门，不晋级；富集训练后 6.23 > 初值 4.15（双条件满足，但 proxy 挂则无上传）；分布侧仍差（energy 6.6/library 0.83）。注：训练后富集数与 warmup 初值小数点后 15 位全同（同为 3/500 命中同基线率，粗粒度巧合，存档不追）。按预案下一步为关 D2 进 D3，已请示用户待裁决。

2026-09-17（T1-P2 D3 panel 门 PASS）：scaler 修复后尺度健康——场回报 energy **0.0562**（基线 0.2595，4.6×）＋cosine **0.9852**（基线 0.5912），双指标严格超，按预声明进 Phase-2 全基因（v0022）。

2026-09-17（T1-P2 D3 全基因起跑）：`--full` 模式已加（32285 维、MLP 512 宽、batch 256 exact-OT、1200 步＋3h cap；t=1→2 场外推预报 bank 行；过 standing 门才 PROMOTED）；v0022 候选构建＋scorer＋INDEX 登记全在门内。后台运行中，回包仲裁。

2026-09-17（T1-P2 D3 v0022 上传构建中，用户 override D-20260917-T1UPLOAD-001）：本地门降格为上传筛选器——D3 cosine 显著优＋余门无显著劣，建 v0022 走一次上传仲裁；门 FAIL 记录保留，实现链 verdict 不变。构建脚本 `scripts/g0/t1_d3_build.py`（复用训练场，不重训），contract＋scorer＋INDEX＋单包全在门内。

2026-09-17（T1-P2 D3 全基因门 FAIL 关闭）：1200 步足额跑完（~26 分钟，无 cap 无 NaN）——场回报 energy **0.4855** 差于基线 0.4340，cosine **0.8125** 优于 0.7796；门要双指标，按预声明停建 v0022，D3 关闭。panel 成功未传到 32285 维（仲裁时点名的风险兑现：高维噪声主导 OT 耦合）。事后改单指标 cosine 放行属于移动门柱，拒绝（§10）。详见 run 内 RESULT.md 与 DECISIONS D-20260917-T1D3-001。P2 进 D1（GPU 级，需 P0-3 租赁批）。

2026-09-17（T1-P2 D3 v0022 已交付上传，首适用 D-20260917-T1UPLOAD-001）：构建数 de **0.9623**（+0.076，T1 本地历史最强）/dir **0.8889**（差门 0.0006，非显著劣）；分布侧健康（var 0.976/lib 1.012/composition_JSD 0.0，无坍缩）——这正是 doctrine 说的情形。INDEX 已登记（score_pending）；单包 `deliveries/g1t1d3__t1__upload__20260917.zip`（成员 t1_val__d3otcfm__v0022.h5ad＋双 MANIFEST，406MB）已交用户上传。

2026-09-17（T1-P2 D1 回报门 FAIL 关闭）：V100 足额训完（30 epochs/870 步/~17min，无 NaN）但回报 de **0.3585**/dir **0.6243**双远低于门；坍缩签名（variance 0.086/library 0.77/energy 13.4）——联合 VAE+SDE 塌向均值，非 marginal，加步难救，按预声明停建 E10.5，D1 关闭。GPU 机已闲置待命（续租/释放等你一句话）。

2026-09-17（T1-P2 D1 V100 全量开训）：GPU 冒烟 smoke_ok（依赖闭包逐层追补 4 文件＋PYTHONPATH 双保险）；全量训练已 nohup detached（6h kill 内置），回传 checkpoint 即本地建候选过门。

2026-09-17（T1-P2 D1 首训 OOM Killed＋流式 PCA 修复重开）：vstack float64 峰值 ~15GB 撑爆 15GB 机（dmesg OOM 实锤，anon-rss 15.4GB）；改 IncrementalPCA 2048 行流式（峰值 ~5.5GB，固定顺序确定性；DESIGN 已备案）；GPU 冒烟复过；全量 detached 重开。

2026-09-17（T1-P2 D1 训练完成回传，本地建候选中）：V100 实跑 30 epochs/870 步/~17 分钟，无 NaN；checkpoint（98MB，sha 双验一致）＋pca.npz 已回传；本地 --build-only 建回报候选→locked scorer 门→过门建 E10.5，后台运行中。

2026-09-17（T1-P2 D1 V100 上机中）：双线 SSH 均通（同机 ubuntu22）；V100-SXM2-32GB（超预期 16GB）＋driver 550；密钥登录已生效、密码文件已销毁；裸机（无 pip/torch）→后台装 cu121 全家桶；数据 1.2GB 已上传，SHA 双验通过（E8.5/E9.5/panel 全对）。待环境回包即冒烟开训。

2026-09-17（T1-P2 D1 冒烟通过，待 V100 登录）：tiny 子集全链路通（PCA→VAE→谱系掩码注意力→EM→可微 Sinkhorn→checkpoint 存取，smoke_ok）；附带修好 DOT 梯度断流（前版 W2 被包成常数）。STAGING 上机清单＋RUN_LOCK＋lineage_map（100% 覆盖）齐备。

2026-09-17（T1-P2 D1 上机准备中，V100 已批待登录 D-20260917-T1GPU-001）：OPT-A(c) 修订（去 E7.75 锚点，回两点 DOT）；设计稿＋训练脚本＋CPU 冒烟＋STAGING 上机清单本地备齐；GPU 只回传 checkpoint，候选构建与门放本地。

2026-09-17（T1-P2 D3 v0022 服务器仲裁 REJECT）：**45.3**（-3.17，连 floor 47.0 都没过）。分项：de 43.7≈持平、dir 55.9 持平，mmd -3.6、variogram **-10.4**——输的全在分布/协变侧。proxy 教训修正：T1 首个假阳性（本地 de 0.9623 最强却传成持平），但本地 energy 旗（0.486 差于基线）预警正确；细化 doctrine：de/dir 需分布侧本地指标（energy/variogram）连署，单看 de 会被 variogram 崩盘背刺。详见 registry §G1-T1-D3 与 DECISIONS D-20260917-T1D3-002。

2026-09-17（轻微劣势落选者横扫，用户要求）：INDEX 待分行＋各 run 目录未注册候选逐项核——结论：无新增可打包。

2026-09-17（T1-P2 D5 起跑，费用纪律 D-20260917-T1GPU-002）：SquidDiff 式条件扩散＋v0004 按权重拼；D5 先行（写码→冒烟→GPU 训），D6 排队；完工/双败即关机，单 lane wall 4h 上限。

2026-09-17（T1-P2 D5 冒烟通过＋GPU 全量开训）：本地冒烟 smoke_ok（纯自实现 DDPM 无外部依赖）；脚本已上传 GPU 机；全量训练中（20 epochs，4h cap 内置；输出本地任务日志＋远端 log 双保险）。

2026-09-17（T1-P2 D6 冒烟通过＋GPU 全量开训）：本地冒烟 smoke_ok（double-backward autograd drift 通）；脚本已上传；全量训练中（25 epochs，4h cap；阻塞式 SSH＋远端 log 双保险）。

2026-09-17（T1-P2 D6 训练完成回传，本地建门中）：V100 实跑 25 epochs/825 步/~18 分钟，无 NaN；checkpoint（97MB，sha 双验一致）已回传；本地 --build-only 建回报门→过门建 v0025，后台运行中。

2026-09-17（T1-P2 D6 回报门 FAIL 关闭＋GPU 已关机）：de **0.8868** 恰等门线（须严格超，不算过）、dir 0.7921 差 0.097； accomp 坍缩签名（variance 0.26）——能量/MMD 系训练第三次塌方差。平局不算过（TIE 带是服务器规则，本地门无此例，§10）。GPU 实例已 OS halt（双线验不可达），控制台释放待用户确认。P2 GPU lane 清零；D2 调参触发条件已满足（D3/D1 双败），待用户定夺。

2026-09-17（独立复核 D-20260917-T1AUDIT-001）：D1/D6/D4/D2/v0022 verdict 全确认；D5 测试无效（阶段条件死代码＋JSD 腿恒不可过）——CLOSE 维持但不得引为证伪，D5b 属新 lane 待立项；D2 重名目录已改名去雷；SHA/台账全对。

2026-09-17（T1-P2 D5 训练完成回传，本地建门中）：V100 实跑 20 epochs/680 步/~14 分钟，无 NaN；checkpoint（109MB，sha 双验一致）已回传；本地 --build-only 建回报门→过门建 v0024，后台运行中。

2026-09-17（T1-P2 D5 回报门 FAIL 关闭）：场回报 energy **2.203** 差基线 0.265 **8 倍**；compJSD 0.1555==0.1555（按持留细胞类型逐个生成，成分被迫一致，门腿空转——设计债如实记，不追溯修门）。非 marginal，按预声明停建 v0024，D5 关闭。P2 进 D6（码即写，GPU 闲置中）。。D2-dz20（de/dir 双低、无显著优项，不合上传仲裁条）、warmup 件（同上；初版 NaN 件已被 warmup 重跑覆盖，现文件即 warmup 件）、D4 门臂（诊断件非候选）、T2-S3 四件（holdout 全负/kNN 灾难，有因淘汰）、T2-J1 v0008（缺参照 component hold，非门误杀）、G0 各 lane（已全部分数回填）。唯一上传就绪未传是 T2-R3 三 lane 包（`b4t2r3__t2__upload__20260914.zip`，contract PASS×3，7 文件齐）——但系用户 09-15 明示关闭，且无本地显著优记录（backtest 明示不作服务器预测）、board best 已移至 v0011=50.64；重开需用户明示，不擅自打包。

2026-09-17（T1-P2 D5b 立项开工，D-20260917-T1D5B-001）：审计修复三件套＋坍缩 veto＋v0026；用户令 CPU 先行，GPU 保持关机；冒烟过（stage_sensitivity 0.745，条件活的）。

2026-09-17（T1-P2 D5b 训练完成，本地建门中）：CPU 实跑 20 epochs/680 步/~12 分钟，无 NaN，checkpoint SHA 自洽，PCA 与 D5 同值；本地 --build-only 建回报门→过门建 v0026，后台运行中。

## 2026-09-21 新六路线提案（未执行）

- 2026-09-21 T1-NEXT-R1：零率与阳性分位数的阶段外推，分布形状对照；PROPOSED / NOT_RUN。证据 `reports/T1_NEXT_ROUTES_20260921.md`。
- 2026-09-21 T1-NEXT-R2：同一动力学下保留/丢弃逐细胞全基因残差的decoder比较；PROPOSED / NOT_RUN。证据 `reports/T1_NEXT_ROUTES_20260921.md`。
- 2026-09-21 T1-NEXT-R3：有界对角/低秩仿射动力学，替换病态det目标；PROPOSED / NOT_RUN。证据 `reports/T1_NEXT_ROUTES_20260921.md`。
- 2026-09-21 T1-NEXT-R4：模块运输代价与正交残差保留，全基因最终验证；PROPOSED / NOT_RUN。证据 `reports/T1_NEXT_ROUTES_20260921.md`。
- 2026-09-21 T1-NEXT-R5：固定基因边际，独立检验阶段依赖演化；PROPOSED / NOT_RUN。证据 `reports/T1_NEXT_ROUTES_20260921.md`。
- 2026-09-21 T1-NEXT-R6：T1合规早期多阶段表示与来源滚动留出，数据审查未完成；PROPOSED / NOT_RUN。证据 `reports/T1_NEXT_ROUTES_20260921.md`。

## 2026-09-21 新六路线执行（R2/R6 先行）

- 2026-09-21 T1-NEXT-R2 启动：残差接口脚本 `scripts/g0/t1_next_r2_resid.py`（seed 20260921，PCA-50，fit 区=60% 分层 train，recipient=E8.5 outer 3,357，伪 target=E9.5 outer 3,411，temp 件不进拟合）；身份门 B(Δ=0)≡源行。本地件（gitignored）：`artifacts/g0/T1-NEXT-R2-RESID-20260921-v1/`。
- 2026-09-21 T1-NEXT-R2 关闭（诊断，无候选、无上传）：身份门 PASS（maxabs 2.38e-07）；PCA-50 解释 21.08%，瓶颈丢 29.65% 方差；7 个 E8.5 特有类型 1,123 细胞全臂零位移 fallback（公平对照、绝对值稀释）。同 recipient 下：strict de 0.593/dir 0.522/energy 0.216；A 重构 de 0.667/dir 0.635 但 energy **6.983**（32 倍）+var_ratio 0.198 坍缩+零率 0.879→0.316；B 残差 de 0.611/dir 0.530/energy 0.211（≈strict 持平）但 22.8% 条目被裁剪、零率 0.629。结论：decoder 失真确认是真失败模式（A 复刻 D3 服务器签名），但残差修复只回到 strict 水平——潜质心时间预测器相对基因空间 shift 无增益。归因收窄，R3/R4 须复用 B 式接口＋更强时间预测器；decoder 修复 alone 非晋级路。v0004 服务器分仅作语境引用。
- 2026-09-21 T1-NEXT-R6 数据源审查（只读元数据，零下载）：E-MTAB-6967 与 ExtendedMouseAtlas 实为同一研究谱系（Pijuan-Sala 2019 Original＋Marioni Extension），"至少两个来源"条不满足；atlas 含 14,493 个 E7.75 WT 细胞（T2 隐藏测试期，R6 训练须排除除非用户明批）；基因覆盖 83%/80% 可用；与官方 T1 barcode 去重待做。 verdict：BLOCKED_DATA_NOT_READY。本地件：`artifacts/g0/T1-NEXT-R6-SOURCE-REVIEW-20260921-v1/REVIEW.md`。

- 2026-09-21 T1-NEXT-R1 v0023 已建待传：B-rule 全量拟合，recipient=v0004 的 5,118 E9.5 行，fallback=父行，覆盖 33%；SHA `d462c166…`，contract PASS；INDEX 登记 score_pending；上传包 `deliveries/t1nxr1__t1__upload__20260921.zip`（SHA `1979815f…`，成员 `t1_val__r1qshape__v0023.h5ad`，4 manifests＋receipt READY_NOT_SUBMITTED）。单发仲裁依据：报告内 B 对 strict 七项全优零退化＋caveat，服务器仲裁。门户上传 NOT_RUN，待用户操作。
