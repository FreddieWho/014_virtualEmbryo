> 2026-10-09 11:37 UTC user direction: PAUSE all T2 experiments and submissions; focus now moves to T1. Today8/8 is complete. Tomorrow proposals require renewed authorization; no automatic run, submission or GitHub push. Handoff: reports/t2_final_slot_20261009/TOMORROW_HANDOFF.md.

> 2026-10-09 final-slot update: v0026 API66.7846 is numeric high, +0.0782 inside±0.1 vs incumbentv25 66.7064, so v25 stays selected. Portal T2 best mean60.3139666667, Human71/187. Today8/8 used; stop. See SERVER_SCORE_REGISTRY final-slot entry. Code and reports are included in the subsequent repository synchronization.

最新 T1 两发收口（2026-10-09）：v0094 joint_carrier 晋级为现役；v0095 joint_external_e95 未晋级。两件共享重建父本，历史差值存在重建混杂；MMD改善、variogram仍弱。预算2/2用尽。DISCLOSURE_CORRECTION_PENDING，已记录E16.5历史诊断来源遗漏，未补正已提交metadata。详细分数与精度见 [registry](reports/SERVER_SCORE_REGISTRY.md#t1-joint-structure-2026-10-09)。

最新 T3 回分（2026-10-09）：v0089 `resplam15unmask`（响应结构路线）服务器 **53.74**，较现役 v0088 53.69 为 **+0.05，落在 ±0.1 平局带内，不换人**，v0088 保持现役。子项 de 41.7→**42.1**（+0.4）、severity 75.2→76.2（+1.0），但 direction 51.2→50.5、mmd 51.1→50.3、variogram 43.1→42.7。**本地源侧复合分预测的 de 上涨方向成立，但净效应被其余三项回落吸收，本地分高估约四倍**——本地复合分只能当候选筛选器，不能当服务器总分预测。这是本地增益未能按预测转化的第三例。[registry](reports/SERVER_SCORE_REGISTRY.md#t3-resplam15-v0089-score-return-20261009)。
最新 T3 候选 v0089（2026-10-09）：响应结构路线——收缩 lam nk/(nk+50)→nk/(nk+15) 且去掉 global_valid 掩码，发射器/atlas/几何全部冻结。本地源侧复合 **74.936110** vs v0088 74.737588（**+0.1985**，赢 4/7，冻结门 PASS），分项 de **+0.354**——这是首次真正移动 DE（发射器层做不到，发射器只重分配已激活细胞）。contract 全 PASS。交付包 `deliveries/t3lam15__t3__upload__20261009.zip`（成员名即 portal Model 名，SHA 对 INDEX 核验通过）。`score_pending`、**未提交**：T3 提交额度未解决，上传需重新授权。增益不均匀（Ehmt2 +1.0 对 Dnmt1 −0.855）。同批全新架构「联合秩传输」本地 −12.07 且对照组不变，为干净负结果。[台账](autoresearch/loop-261009-1845/)、[报告](reports/t3_rebuild_20261009/REPORT.md)。
最新门户确认（2026-10-09）：**Total 172.9**，per-task T1 58.9 / T2 60.3 / T3 53.7，Human rank 71/187。按现役相加 58.89+60.2770+53.69 = **172.857**，与门户合计在显示精度内一致。**此前记录的 per-task 对不上问题关闭**——根因是选集滞后，不是门户口径未知。
最新 T2 回分（2026-10-09 第二波）：operator-transfer 三件完成。**心插 v0025 h_heart_copula = 66.7064 晋级**（官方 API 精度；较字节精确 H1 65.0260 +1.6804，较旧现役 v0023 62.48 **+4.23，最大单榜跃升**）；胚胎 v0023 = 63.0185 带内不换人，现役仍 v0021；外推 v0037 零保位移 48.86 REJECT。心插现役已换 v0025。[registry](reports/SERVER_SCORE_REGISTRY.md#t2-operator-transfers-2026-10-09)。
最新 T3 本地重训（2026-10-09）：v0088 从公开代码完整重建，v0087/v0088 表达式哈希与三个推理产物**逐位复现**，GO embedding 亦逐字节相同；基线复合分与归档 summary 最大绝对差 0.0。`PUBLIC_REBUILD_FOLLOWUP.md` 的"完整拟合未验证"限制已可撤销。发射器成分轴 14 次迭代判定饱和（最好 +0.0034，DE 分零变化），不建议提交任何变体。[报告](reports/t3_rebuild_20261009/REPORT.md)。
最新 T2 回分（2026-10-09）：胚胎四实验 v0019–v0022 全部登记，**v0021 scRNA copula = 63.0047 晋级**（+0.1117 vs v0014 62.8930，经官方公开 API 取高精度，超出 ±0.1 带）；v0022 62.65、v0019 62.33、v0020 61.39 均淘汰。胚胎现役易主。[registry](reports/SERVER_SCORE_REGISTRY.md#t2-embryo-20261009)。
最新 T1 回分（2026-10-09）：late-anchor/OT 五 lane v0089–v0093 登记，**v0092 ot_gen_v51 = 58.89 晋级为新 board best**（+0.90 vs v0091 57.99）；v0093 58.22、v0091 57.99、v0090 53.43、v0089 53.14。[registry](reports/SERVER_SCORE_REGISTRY.md)。
最新 T3 回分（2026-10-08）：v0088 condhurdle = 53.69 晋级（+0.27 vs v0087）；v0084=49.55 曾因 q0.25 重建晋级，v0086 arank r2=49.34 REJECT。**2026-10-09 T3 无提交**。
（历史）门户观测（2026-10-08T11:58Z）：Total 171.4、rank 61、T1 58.0 / T2 59.7 / T3 53.7——当时的 per-task 对不上问题已在 2026-10-09 关闭，根因是选集滞后而非门户口径未知。
> 2026-10-09 operator-transfer update: three authorized submissions are complete. Heart interpolation v0025 is promoted (official API66.7064); embryo numeric-high v0023 is63.0185 but project incumbent stays v0021 under±0.1; extra v0037 is48.86 UI, not promoted. Official T2 best-per-board mean60.2879, Human71/187. Today7/8 used; remaining1 unauthorized. Full precision/source distinctions: reports/SERVER_SCORE_REGISTRY.md#t2-operator-transfers-2026-10-09.

最新 T1 回分（2026-10-07）：T1-SIX 六路线 v0057–v0062 全部登记，v0058＝53.85 带内 TIE 不晋级（−0.07 vs v0051 53.92；本地 de 冠军未转化），其余 5 件 REJECT；现役 v0051 不变，T1 待分清零。[registry](reports/SERVER_SCORE_REGISTRY.md#t1-six-score-return-20261007)。

最新 T2 回分（2026-10-07）：心脏插值 v0023＝62.48 晋级（+0.12，超出平局带）；v0024＝60.61、外推 v0035＝49.06、胚胎 v0018＝62.50 均淘汰。占位项变差，不能写成占位修好了。门户合计仍是 156.06。[复盘](reports/t2_geom4_20261007/SCORE_REVIEW.md)。

最新 T2 事件（2026-10-07）：几何新机制第一刀只诊断不交卷。心脏插值各向异性源侧 CONTINUE，胚胎线性族关闭；无候选，现役不变。[结果](artifacts/t2_geom_aniso_20261007-v1/RESULT.md)。

最新 T1 事件（2026-10-07）：六条新路线（3 优化/结合＋3 全新）全部实现并全量执行，v0057–v0062 score_pending、未提交/未评分；本地信号 ostabmix v0058 de +0.0185 改善（其余持平）、nbidir v0060 dir/Energy/Vario 改善取舍，其余全劣；best v0051=53.92 保持，服务器对照 pending 用户回填。[报告](reports/t1_six_20261007/REPORT.md)。

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

更新时间：2026-10-09（选集已按 08/09 全部回分刷新；门户 Total 172.9 已确认，per-task 已对账）。

上面的日期条目是事件日志，不是现在的选集。现在的选手和文件地图看 [docs/ATOM_MAP.md](docs/ATOM_MAP.md)。

## 第一部分：给人读的进展

**已完成什么。** 三个任务的当前选手都已回分，本轮三个榜全部易主过：T1 是 58.89（v0092 OT 生成式位移），T2 胚胎插值 63.00（v0021 scRNA copula）、心脏插值 **66.71**（v0025 copula，本轮最大单榜跃升 +4.23）、心脏往后推 51.12，T3 是 53.69（v0088 conditional hurdle）。T2 两件晋级都经官方公开 API 解析高精度后裁决。结构入口在 [docs/ATOM_MAP.md](docs/ATOM_MAP.md)。

**正在做什么。** 没有新的提交在跑。T3 发射器成分轴已扫完并判定饱和：最好变体本地 +0.0034（噪声级），且 `de_skill` 在全部 14 个变体中变化恰为 0——T3 本地源侧指标不再是有效目标。下一步要么直接用服务器分仲裁（需重新授权），要么改响应结构开新路线。

**卡在哪里。** 账目本身已经对齐：门户 **172.9**（per-task 58.9 / 60.3 / 53.7）与现役相加 172.857 在显示精度内一致，Human rank 71/187。剩下的不是分数缺口，而是两处方法问题：(1) `AUDIT.md` 的数值最高只统计 `score_status=scored` 的行，因此印出的数值低于现役——这是字段不一致（60+ 行用 `registered`），不是分数缺失，重跑生成器也修不好；(2) **T2 外推仍是短板**，51.12 已进平台期，本轮 v0037 零保位移 48.86 更低，而心插靠 copula 族一次跳了 4.23——三榜的机制成熟度很不均衡。

**准备怎么解决。** 重读门户合计与 per-task 口径。主办方回信之前，同基因的扰动数据继续隔离。没有新机制授权时，不再交混合权重、外推剂量、响应倍率或发射器超参的小变体。

```

2026/10/09
ROADMAP  [##############-] 14/15 节点（N8 仍未正式裁决）
本周投入  竞赛执行 ████████░░ 80%   基础设施 ██░░░░░░░░ 20%

偏离程度  中
偏离位置  原定“先选方向或封板”的节点一直没有正式裁决，后面的工作是直接做上去的。
         T3 曾改用本地源侧复合分做了一轮 14 次成分迭代，事后判定该指标失效——
         顺序上等于先跑本地仲裁、后发现仲裁器不可信。
         三榜机制成熟度不均衡：T2 心插靠 copula 族一次跳 4.23，T2 外推停在 51.12 平台期，
         T3 停在 53.69 且本地代理已失效。
建议      T3 若继续，只用服务器分仲裁（须用户重新授权提交额度）；T2 优先沿 copula 族，
         外推需新机制而非再调同一形变的比例。
```

## 第二部分：给 agent 的接手信息

- 先读 `docs/00_START_HERE.md`、`docs/ATOM_MAP.md`、`reports/SYNTHESIS_T1.md` / `T2` / `T3`。不要从 `docs/batch*` 提示开工。
- 当前选择：T1 v0092=58.89（v0093 58.22、v0091 57.99 备份）；T2 胚胎 v0021=63.0047 / 心脏插值 v0025=66.7064 / 外推 v0030=51.12；T3 v0088=53.69（v0087 53.42 回退）。
- 核心文件：`submissions/INDEX.tsv`、`reports/SERVER_SCORE_REGISTRY.md`、`docs/ATOM_MAP.md`。
- 最近决策：`D-20261009-NAV-001`（导航按 08/09 回分刷新，不改候选身份与分数）；`D-20261009-T3REBUILD-001`（T3 v0088 本地完整复现＋发射器成分轴饱和）；科学决策仍看各任务追踪。
- 下一步：门户 172.9 与 per-task 已对账，无待重读项（下次现役变动后重读）。T3 发射器成分轴已判定饱和，本地指标失效，下一手需服务器分仲裁（须重新授权）或改响应结构开新路线。T2 优先沿 copula 族（心插已验证 +4.23），外推需新机制。
- 未闭合：`AUDIT.md` 因 `score_status` 字段不一致低估数值最高，待 coordinator 裁决（不影响分数本身）；T3 当日提交额度未观测；T2 外推平台期与 T3 的 53.69 水位是两个已知短板。

---

## 比赛细节（以下为本项目原有 STATUS 内容）

完整分数不在本文件重复维护：候选文件与哈希看 [`submissions/INDEX.tsv`](submissions/INDEX.tsv)，服务器分数看 [`reports/SERVER_SCORE_REGISTRY.md`](reports/SERVER_SCORE_REGISTRY.md)，任务细节看 [`docs/coordination/`](docs/coordination/) 下的三个追踪文档。

## 总体状态

- 比赛优先；starter_pack 已关闭为 `CLOSED_FOR_COMPETITION_BASELINE`。
- 上次三任务门户观测合计 **172.9**（本轮T1之前，per-task 58.9 / 60.3 / 53.7）。本轮后按现役算术和 **172.9557**（58.9887+60.2770+53.69），不是新的三任务门户观测。
- 任务分数：T1 **58.9887**（v0094，2026-10-09），T2 **60.277**（63.0047 / 心脏插值 v0025 66.7064 / 外推 v0030 51.12），T3 **53.69**（v0088，2026-10-08）。
- **历史对账已闭合**：T1本轮前172.9 / 172.857一致；本轮后需另查三任务总榜才能更新门户Total。T2最终门户各榜数值最高均值为60.3139666667；v0026带内不换现役。
- **已知数据缺口**：`AUDIT.md` 的 Server bests 只统计 `score_status=scored`，而 60+ 行用 `registered`（含 v0092/v0093/v0021/v0025），故 AUDIT 印出的数值最高低于现役。待 coordinator 裁决是否统一字段。
- 待分队列为 0：INDEX 中 6 行 `score_pending` 全是早期未上传对照，不是当前队列。
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

1. `v0094_joint_carrier`：**58.9887**，现役；固定边缘的配对carrier联合秩恢复。
2. `v0092_ot_gen_v51`：**58.8865**（官方API补精度），前现役；非重建父本的已评分原件。
3. `v0095_joint_external_e95`：**58.64**（UI），已评分但未晋级；独立E9.5来源联合秩。

混合族（v0049–v0058，~53.7）与 late-anchor 直用轴（v0089 53.14 / v0090 53.43）均已过平台。历史见[T1_TRACKING.md](docs/coordination/T1_TRACKING.md)。

### T2 — spatial-temporal

1. 当前 per-board selection：`v0021` embryo **63.0047**（scRNA copula；数值最高 v0023 63.0185 在 ±0.1 带内不换人）+ `v0025` heart_interp **66.7064**（copula，2026-10-09 新 best；前任 v0023 62.48）+ `v0030` heart_extrap **51.12**。
2. 前任 `v0011 L1_SHRINK` heart_extrap **50.64** 已被 v0030（51.12）取代；更早的未晋级最高 50.74（v0022，未并列）一并退为参照。
3. heart_interp 数值最高备份是 v0032 类同带内条目；外推 v0032 = 51.14 在 ±0.1 带内不换人，v0036 = 50.47 REJECT。

T2 三条 board 的现役机制不同：embryo 与 heart_interp 都是 **scRNA copula 联合分布传输**（v0021 / v0025），heart_extrap 仍是中位数位移＋library 守恒（v0030，5 共享态）。两件晋级都经官方公开 API 取高精度后裁决，是本项目目前唯一做到服务器高精度仲裁的一路。成熟度不均衡：心插一次跳 +4.23，外推停在 51.12 平台期。

Batch3 `T2-J1-FGW-ASSIGNMENT-20260903-v1`：heart_interp v0009 服务器 **57.3（+0.6 vs v0007 56.7）** 晋级 board best（2026-09-04 回填）；embryo_interp v0008 未上传，保持 `HOLD_AS_COMPONENT` 不可变。

详情：[T2_TRACKING.md](docs/coordination/T2_TRACKING.md)

### T3 — gene perturbation

1. v0088 condhurdle：**53.69**，已评分，当前 best（2026-10-08）。
2. v0089 resplam15unmask：**53.74**，数值最高但 +0.05 在 ±0.1 带内，**不换人**（2026-10-09）。
3. v0087 embhurdle_v2：**53.42**，高备份（落后现役 0.27）。

本轮机制线：v0083–v0085 源侧路线（v0084 = 49.55）→ v0086 arank r2（49.34 REJECT）→ v0087 七 KO 通用胚胎状态响应 hurdle v2（53.42）→ v0088 把随机零激活 tie 换成 WT-only 状态条件化激活倾向（53.69）。改善集中在分布/发射行为，DE 停在 41.7。2026-10-09 本地重训已完整复现该模型，发射器成分轴判定饱和（`de_skill` 全变体零变化），详见 [报告](reports/t3_rebuild_20261009/REPORT.md)。

Batch2 `B2-T3-A1` 的 v0006/v0007 后来已评分 45.5，并被后续版本超过。这里不再把它们写成待评分。

Batch3 `T3-S1-PRIOR` 已形成 prior/gate bundle：31,458 条 state×gene 记录，L1/L2 非零分别为 2,050/5,125；用户授权后的本地方法部署与 CollecTRI/OmniPath panel-scoped 内容审计均为 `PASS`。正式分析前的 5 个 current parent contract/registry SHA256、protected-field/round-trip 复核和实际 22 项接口测试均已闭合；directed-evidence 组件为 `COMPONENT_PASS`，但 candidate admission 仍 `HOLD`，这些预检不等于 state-specific activity validation。β-catenin 相关 prior 仍显式为 `sign=0/EXTERNAL_KNOWLEDGE_AUDITED_NOT_INTEGRATED`，S1 prior 未消费 state-joined evidence。prior/gate 仍为 `HOLD_AS_COMPONENT`，原因是 stability sensitivity；不进入 H5AD 或候选生成。

T3-S1A v7 已完成 exact E8.75 input/state join、显式 target applicability、Gata4 CellOracle real API、三条 scTenifold 输出、full-matrix state-response/coverage 审计和 hash-bound route audit；随后 S1B v3 已完成 full CollecTRI/OmniPath identity、external contextual integration、冲突归零审计、family-native LOFO 与实现脚本 SHA 绑定。经用户授权继续后，S1C-A/v1 已用原生 CellOracle `TFdict` 构建 Gata6/Ctnnb1 target-compatible adapter，S1C-B/v3 在真实 CellOracle 0.22.0 上完成 2/2 synthetic fit/simulate smoke 并通过进程退出后的 stable manifest 自校验；S1D/v3 又获得 GSE5298/GSE9652 两个 Gata4 与 GSE78125 一个 Ctnnb1 的 E9.5 exact-stage、组织限定 processed perturbation context，并完成 sample/mapping/effect provenance。

**2026-09-02 收口**：T3-S1 链已正式收口为 `CLOSED_AS_RESEARCH_COMPONENT`（[`artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md`](artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md)）。同日独立的 gate 可满足性审计（`T3-S1C-GATE-SATISFIABILITY-20260902-v1`）判定 `UNSATISFIABLE_UNDER_FIREWALL`，两条结论一致：signed family<2、E8.75 state-matched activity 公开不可得、stability 未闭合，且 E8.5–E9.0 窗口目标扰动数据属 target leakage，gate 在当前 firewall 下结构性不可达。候选生成、scorer、上传保持关闭，`blocks_submission: false`；重开条件见收口报告。执行资源已切换至 batch3 `T1-PRE-HARMONIZE`。

详情：[T3_TRACKING.md](docs/coordination/T3_TRACKING.md)

## 下一步总览

| 任务 | 下一步 | 提交前硬要求 |
|---|---|---|
| T1 | v0094 现役；v0092 / v0095 为数值Top3，分数见权威registry | 两发结束，披露缺口已记录且未解决；重建混杂；优先边缘校准而非rank-blend微调 |
| T2 | 胚胎 v0021=63.0047、心插 v0025=66.7064、外推 v0030=51.12；心插 copula 族优先 | 门户 60.3 已对账；外推 existing-route 预算 2/2 用尽、平台期 ~51.1，需新机制；仲裁沿官方 API 高精度口径 |
| T3 | best v0088=53.69；v0089=53.74 带内不晋级；发射器轴饱和、响应结构路线已验证到服务器 | 后续 T3 用服务器分裁决，本地复合分仅作筛选；剩余提交额度待用户确认；blocks_submission: false |

## 更新规则

每次新版本、参数修改或路线分叉，都要在对应任务追踪文档的“变更记录”追加一行，用一句通俗话说明：

> 把什么改成什么；为什么改；结果是什么；保留还是淘汰。

根目录本文件只在当前 best、Top 3、任务状态或下一步发生变化时更新。服务器分数返回后，先更新 `reports/SERVER_SCORE_REGISTRY.md`，再同步本文件和对应任务文档。

- 2026-09-20 T3 R5/R6：已补第二次隔离过滤与用途门；尚未获准训练。下一步为剩余扰动/信号链审查、书面用途确认及shape版完整集成，见 [准备报告](reports/t3_r56_readiness_20260920/REPORT.md)。既有best与待评分队列不变。

- 2026-09-20 T3更新：R5已补齐最小信号链并生成v0032/v0033，合约PASS，未提交/未评分；[交付包](deliveries/r5sig__t3__upload__20260920.zip)。R6仍待审查，书面确认/shape-only为项目内部约束。见[本轮报告](reports/t3_r5_completion_20260920/REPORT.md)。下一步收集服务器分数，best不变。

- 2026-09-29：按已回填分数同步当前选择。T1 best 改为 v0029=52.5；T3 修复三条改为已评分不晋级；T2 低幅度两条改为已评分不晋级。158.72 只记为推导值。旧的“最新事件”横幅不再放在文首，避免和当前选择矛盾。

- 2026-09-29：三批回分。T1 best 改为 v0035=53.43；T2 改为胚胎 62.89 / 心插 62.36；T3 第二轮关闭。推导合计记 159.95（待门户确认）。待分只剩 T3 六条。

最新 T2 回分（2026-10-03 第二轮）：v0032＝51.14（+0.02，TIE 带内不晋级）、v0033＝50.89（REJECT，半剂量削弱 de）、v0034＝51.02（TIE 不晋级）；现役 v0030=51.12 不变，T2 待分清零。服务器确认 de 剂量最优 0.9（与 dev 一致）；recipe 家族进入 ~51.1 平台期，下一波需行集合/几何级新机制或封存。[复盘](reports/t2_holdout10_score_review_20261003/REPORT.md)。
