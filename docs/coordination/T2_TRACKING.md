# T2 任务追踪：spatial-temporal

- 2026-10-03｜本地实验1：空间尺度校准｜从冻结QTE×组成基线起步，表达和细胞组成保持，围绕中心将坐标尺度乘0.9；固定三种子完整评分，检验本地尺度失配。属于开发集代理优化，不作发育生长或服务器获益解释。

- 2026-10-03｜T2 heart 外推前台 autoresearch 启动｜用户确认本地综合分目标≥6.0；独立仓库 `artifacts/autoresearch/t2-extrap-20261003-v1`，冻结三种子中位数及8通道评分/护栏，从QTE×组成历史本地最好方案起步。只作本地开发优化，未新增提交，服务器现役不变；旧代理的跨路线预测失效限制保留。

更新时间：2026-09-29

T2 有多个 board；不同 board 的分数不能直接当作同一个指标比较。服务器分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。

## 当前状态（2026-09-29）

- 选择没变：胚胎插值 v0010 **62.29**，心脏插值 v0013 **62.04**，心脏外推合计里仍用 **50.53**。三个榜平均是 58.29。
- 2026-09-28 交的低幅度位置变化 v0014、v0015 都是 **61.52**，低于心脏插值现役 0.52，不晋级。
- 心脏外推单独最高仍是 v0011 **50.64**，但确认过的合计没有用它。差 0.11，要重读门户，不能在这里宣布晋级。
- 没有未跑的已规划路线。不要再交“在赢家上再加位置变化”。决策 `D-20260928-T2LOWAMP-002`。

## 历史状态（2026-09-03，不是当前选择）

- 当时记录的合计是 149.5，T2 任务分是 55.7。后来已被表达桥加组成取代。下面保留原文。
- 当时最佳 board：embryo interpolation **60.1**、heart interpolation **56.7**、heart extrapolation **50.5**。

## 历史 Top 3（2026-09-03，不是当前选择）

下面这张表停在合计 149.5。当前选择看本文件开头。不同 T2 board 不做未经说明的跨 board 横比。

| 位次 | 路线 | 通俗说明 | 服务器证据 | 状态 |
|---|---|---|---|---|
| 1 | 当前 per-board selection | B1-A1 L1 保留 embryo interp，T2-S3 L1 保留 heart interp（56.7），heart extrap 回到 baseline | server T2 **55.7**；server Total **149.5** | 以服务器当前榜单为准；heart_interp 晋级后的新 aggregate 待服务器确认 |
| 2 | B1-A1 `L1_FORMAL_LOG_RMS` | 只做 source-only 的统一 G1 空间尺度校准 | raw board scores **60.1/56.3/50.2** | embryo/interp 胜出；heart extrap 低于 baseline 50.5 |
| 3 | B1-A1 `L2_ALL_STAGE_LOG_RMS_OLS` | 用全部训练阶段的 log-RMS OLS 校准统一尺度 | raw board scores **59.9/55.3/49.8** | 已评分；各 board scored backup |

raw server scores、submission ID 和证据只在 `reports/SERVER_SCORE_REGISTRY.md` 维护。上面 55.7 和 149.5 是 2026-09-03 的记录，不是现在的选择。

B1-A1 双 lane 最终集已完成服务器评分；L1 在三个 B1-A1 lane 中均优于 L2，但 heart extrapolation 的 baseline 50.5 高于两条新 lane，因此当前按 board 回退 baseline。

## 变更记录

| 日期 | 版本/分叉 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-08-21 | `baseline-001/T2/*/v0001` | 无 | 先跑官方 `copy_last` 与 `pseudobulk_shift`，把三个 T2 board 的底线建立起来。 | T2 `53.4`；保留 |
| 2026-08-22 | `v0001_expression_midpoint_unscaled` | baseline heart interpolation | 尝试把 E8.25→E8.75 的表达中点直接用于 heart interpolation。 | 未上传；仅作历史比较 |
| 2026-08-22 | `submission-002/.../v0002_expression_midpoint_norm` | baseline heart interpolation | 在表达中点后恢复 library size normalization，仍不改几何。 | heart interp `53.6`，`+0.6`；当前 best |
| 2026-08-22 | 追踪文档建立 | `v0002` | 把已评分路线、board 分数和下一条 geometry 分叉集中记录。 | 不改变模型 |
| 2026-08-27 | `B1-A1-L1-T2_embryo_val_interp` | baseline-001/T2_embryo_val_interp/v0001 | 严格 `log(RMS)` 插值后统一缩放；表达与 15-NN 不变。 | local proxy `scale_log_ratio=0.5776`；服务器 `score_pending` |
| 2026-08-27 | `B1-A1-L1-T2_heart_val_interp` | submission-002/T2_heart_val_interp/v0002 | 严格 `log(RMS)` 插值后统一缩放；表达与 15-NN 不变。 | local proxy `0.5207`；服务器 `score_pending` |
| 2026-08-27 | `B1-A1-L1-T2_heart_val_extrap` | baseline-001/T2_heart_val_extrap/v0001 | 末段 `log(RMS)` 斜率外推后统一缩放；表达与 15-NN 不变。 | local proxy `1.204`；服务器 `score_pending` |
| 2026-08-27 | `B1-A1-L2-T2_embryo_val_interp` | baseline-001/T2_embryo_val_interp/v0001 | 全阶段 `log(RMS)` OLS 趋势后统一缩放；表达与 15-NN 不变。 | local proxy `0.6509`；服务器 `score_pending` |
| 2026-08-27 | `B1-A1-L2-T2_heart_val_interp` | submission-002/T2_heart_val_interp/v0002 | 全阶段 `log(RMS)` OLS 趋势后统一缩放；表达与 15-NN 不变。 | local proxy `0.5823`；服务器 `score_pending` |
| 2026-08-27 | `B1-A1-L2-T2_heart_val_extrap` | baseline-001/T2_heart_val_extrap/v0001 | 全阶段 `log(RMS)` OLS 趋势后统一缩放；表达与 15-NN 不变。 | local proxy `0.5059`；服务器 `score_pending` |
| 2026-08-29 | `B1-A4 J1` 双 lane × 三 board | B1-A1 immediate parents（heart extrapolation 为 baseline） | 固定种子下做 source-only hard expression-coordinate permutation；L1 为 latent KNN10，L2 为 same-celltype state-hash10，表达行、坐标和 15-NN 结构分别保持不变。 | 六个 contract-valid 候选；local NFS `0.15017/0.19003/0.10775` 与 `0.15104/0.19050/0.11151`（按 embryo/heart-interp/heart-extrap）；服务器已评分，未晋级 |
| 2026-08-29 | `B1-A4__T2__manual_upload__20260829.zip` | B1-A4 六个最终候选 | 按统一字段顺序重命名 ZIP 内副本：batch、task、board、lane、version；canonical artifact 保持不变。 | ZIP 含 6 个可上传 `.h5ad`、`UPLOAD_MANIFEST.tsv` 和说明；成员 SHA256 已逐一复核 |
| 2026-08-29 | `B1-A4` 服务器评分 | B1-A4 六个最终候选 | 按包内文件名映射回填用户返回的六条 board 分数；不使用 portal Model 字段推断候选。 | embryo `59.3/59.2`、heart-interp `56.3/56.3`、heart-extrap `50.0/49.9`；无 board 提升，全部 artifact 保持 scored immutable |
| 2026-09-03 | `T2-S3-SHAPE-FIELD-20260903-v1` | 各 board 锁定 parent（embryo/heart_interp 为 B1-A1-L1，heart_extrap 为 baseline-001） | 只改 3D 几何占据形状与内部距离（G2/G3 原子），G1 scale/表达/行序/J1 全部冻结；L1 pycpd 2.0.0 non-rigid CPD，L2 Spateo 1.1.1 vector field；interp 双向时间加权场、extrap endpoint 场+ρ0.25 强收缩；场应用后重新中心化和 RMS 回锁。 | 6 候选 contract 全过、表达 hash 不变、RMS 回锁在 P0 容差内；holdout：L1 在 H1（embryo 留 E7.25）/H2（heart 留 E8.25）三 proxy 全胜，H3（heart 宽间隔留 E8.75）/H4（外推留 E9.5）全负；L2 四个 holdout 全负且 heart_extrap kNN CATASTROPHIC（该候选 contract FAIL 为设计行为）；coordinator 裁定：embryo L1 与 heart_interp L1 `READY_FOR_MANUAL_SUBMISSION`（附 H3 反例与 pseudo-target 偏袒声明），heart_extrap L1 与全部 L2 `REJECT`；6 条已登记 INDEX.tsv `score_pending`，未上传；14 测试 PASS、157 文件 manifest 自校验 PASS，SHA256 `4ffef666e95f9046811346e1d940fde322de9dca53f06f7c4055a8a1051f8a76` |

## T2-S3 服务器评分与决定（2026-09-03 回填）

| 日期 | 版本/分叉 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-09-03 | `T2-S3` 服务器评分 | embryo v0006 / heart_interp v0007 | 用户上传两条 READY 候选并返回 board 分数（Model 短名与本地版本精确对应）。 | embryo `59.7`（-0.4 vs 60.1）rejected；heart_interp `56.7`（**+0.4** vs 56.3）**晋级为该 board 新 best**；当前 selection 变为 B1-A1 L1 embryo + T2-S3 L1 heart_interp + baseline heart_extrap；服务器未返回新 T2/Total，derived T2≈55.8/Total≈149.6 待确认；embryo 在 H1 全胜却服务器下降，印证 H3 警示（窄间隔 holdout 获益不保证 board 获益）；4 条本地 REJECT 候选保持 score_pending 不上传 |

## T2-S3 gate 裁定（2026-09-03，coordinator）

依据 `docs/batch3/04_DECISION_RULES.md` §6：

- L1 pycpd 满足"至少两个独立 holdout 同方向优于低成本基线"（H1 embryo、H2 heart 均三 proxy 全胜）；H3 为同 board 宽间隔反例，已如实记录为已知限制（插值获益随间隔变宽消失），不构成"无解释的方向不一致"。
- `READY_FOR_MANUAL_SUBMISSION`：embryo `v0006_t2_s3_l1_pycpd`、heart_interp `v0007_t2_s3_l1_pycpd`。是否上传由用户决定；不自动上传。
- `REJECT`：heart_extrap L1（唯一外推 holdout H4 全负）；全部 L2 Spateo（4/4 holdout 全负 + heart_extrap kNN 拓扑灾难，规则限定只能 HOLD/REJECT 且无 proxy 改善支持 HOLD）。
- 本地 scorer 分数均为 pseudo-target（embryo/extrap 两 board 的 pseudo-target 恰为 parent 几何底 stage，结构性偏袒 parent），不是 leaderboard 证据。
- 服务器分数未回填前不得宣称 T2 提升；当前 per-board selection 与 T2=55.7、Total=149.5 不变。

## T2-J1-PROXY gate 裁定（2026-09-03，coordinator 确认）

| 日期 | 版本 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-09-03 | `T2-J1-PROXY-20260903-v1` | `T2-S3-SHAPE-FIELD-20260903-v1`（执行序）、B1-A4（定性对照引用） | 固定 POT entropic-FGW 软配对 objective（表达 PCA30 + 内部距离 cost，alpha=0.5、eps=0.005，spec 先冻结），在 embryo 留 E7.25、heart 留 E8.75 两个 leave-one-stage-out holdout 上对照 identity/random/B1-A4 类 greedy。 | 7/7 criteria PASS，gate `J1_PROXY_PASS`：NFS-like 从 random 中位 0.137/0.172 降到 0.012/0.015（64 次随机无一更优）；label-only 与 scrambled-reference 对照均差于 random，改善依赖真实表达-位置信息；B1-A4 已发布 local NFS 落在 random 包络内，与其服务器失败一致。**caution**：heart holdout 逐位置 pearson 为负（参考跨 1.25 天、标签交集仅 5），授权正式 assignment candidate 前须审视 heart 参考构建。source-only 第 4 层证据，不构成 leaderboard 宣称；46 文件 manifest 自校验 PASS，SHA256 `b5e2abe2718f4708363df4189088071e29f6ad6d52007f22ffcb68565511b751`；148 全量回归 PASS |

## B1-A1 服务器结果与决定

- 六个服务器 ID 与 raw score 已登记在 `reports/SERVER_SCORE_REGISTRY.md`；成绩按用户回填记录。
- L1 相对 L2 在 embryo interpolation、heart interpolation、heart extrapolation 分别领先 0.2、1.0、0.4 分；这是 B1-A1 lane 内比较，不覆盖更高的 baseline heart-extrapolation 分数。
- L1 相对各自 parent 在 embryo interpolation 与 heart interpolation 上提升，在 heart extrapolation 上下降 0.3 分；因此当前 T2 选择必须按 board 混合保留，不是三 lane 全部采用 L1。
- 选择：当前 T2 board 使用 L1 的 embryo/interp 与 baseline 的 heart extrap；L2 作为同批第二候选和审计备份保留；不追加 B1-A1 第三 lane 或事后调参。

## B1-A4 服务器结果与决定

- 六个 B1-A4 候选均已 scored；embryo interpolation 两条低于 B1-A1 L1 的 60.1，heart interpolation 两条与当前 56.3 持平，heart extrapolation 两条低于 baseline 50.5。
- A4 全 L1 的 board 值只能推导为 T2 `55.2`，全 L2 为 `55.1`；服务器未返回新的 Total，当前服务器 T2 `55.7`、Total `149.5` 保持不变。
- 决定：B1-A4 不晋级；六份 artifact 作为不可变 scored 记录保留；不启动 B1-C1 重复缩放或新的 T2 atom。

## T2-J1-FGW-ASSIGNMENT gate 裁定（2026-09-03，coordinator 确认）

| 日期 | 版本 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-09-03 | `T2-J1-FGW-ASSIGNMENT-20260903-v1` | embryo v0002（g1_formal_log_rms）、heart_interp v0007（t2_s3_l1_pycpd）；objective 继承 `T2-J1-PROXY-20260903-v1` 冻结 spec | 固定表达行集合+固定坐标点云，用冻结 FGW objective（α=0.5/ε=0.005/PGD，全量无子采样）求解 soft plan，按预声明 `column_argmax_margin_greedy_v1` 转离散双射，只置换 X 行、obs/坐标不动。 | heart 参考审视按预声明标准 PROCEED（跨度 0.50、标签交集 33、探针弱正 +0.0138、支撑充足）。objective 同靶：embryo −12.2%、heart −26.6%（均优于恒等配对）。contract 2/2 PASS、protected 2/2 PASS（坐标/obs/var/kNN 图/表达 multiset 与 parent 精确一致）、重跑字节一致。40 文件 manifest 自校验 PASS；新增测试 14 passed、全量回归 162 passed。 |

裁定（依据 §6/§7，同靶相对证据优先）：

- **heart_interp v0009 `j1_fgw_assignment`：`READY_FOR_MANUAL_SUBMISSION`（弱置信）**。同靶 NFS 镜像 0.0967→0.0747 改善（与 J1-PROXY 预声明 gate 指标同向），objective −26.6%；随附声明：morans_I_agreement 同靶 0.7365→0.6743 变差、A3 探针仅勉强为正、conflict 率 73.3%、训练期 pseudo-target 循环论证，本地证据非 leaderboard 证据。是否消耗提交由用户决定，不自动上传。
- **embryo_interp v0008 `j1_fgw_assignment`：`HOLD_AS_COMPONENT`**。机械项全过、objective −12.2%，但唯一同靶 parent 相对证据（NFS 镜像）no_improvement（0.0312→0.0344），且 embryo bracket 同型探针为负；本地证据不支持消耗提交。作为不可变组件保留，若未来推进需先补同靶 parent scorer 参照与探针问题。

**服务器仲裁（2026-09-04 回填，行时间 2026-09-03 19:51）**：heart_interp v0009 = **57.3（+0.6 vs v0007 56.7）**，晋级 board best，进入当前 selection；本地混合证据（nmmd 改善 vs morans 变差）由服务器正向仲裁。embryo v0008 未上传，保持 HOLD。derived T2≈55.97/Total≈149.8 待服务器页面确认，不得引用为服务器值。详见 `reports/SERVER_SCORE_REGISTRY.md`。

## 下一步

J1 assignment 已获服务器仲裁：heart_interp v0009=57.3（+0.6）晋级 board best；embryo_interp v0008 保持 HOLD 不上传。batch3 剩余未做任务为 HX-DYNAMICS-KILLTEST（单工具/单 board/单 kill metric，需实例化授权）。若需要科学晋级，仍需独立 stage/replicate 证据；leaderboard 分数不构成因果机制证据。

2026-09-04（batch4 Wave 1）：`B4-T2-R1-FGW-ASSIGNMENT-REPAIR` 完成，双 lane 待上传评分——v0010（L1 eps0.005+全局匹配：mass capture 0.718→0.796，NFS 0.0747→0.0733 improvement，Moran 0.6743→0.6823）、v0011（L2 eps0.002+全局匹配：mass 0.873，NFS 0.0732 improvement，Moran 0.6833）；contract/protected 全 PASS，确定性字节一致。产物 `artifacts/batch4/B4-T2-R1-FGW-ASSIGNMENT-REPAIR-20260904-v1/`，交付包 `deliveries/b4t2r1__t2__upload__20260904.zip`（先传）与 `deliveries/b4t2r1b__t2__upload__20260904.zip`（后传）。结论待服务器仲裁。

2026-09-04（夜）：B4-T2-R1 双 lane 服务器仲裁——v0010=**57.3**（+0.05）、v0011=**57.31**（+0.06），相对 greedy v0009=57.25 均落入 ±0.1 噪声带 → **TIE，不晋级**；v0009 留任 selection；按预声明停止规则**关闭 FGW 离散化微调**，不再扫 epsilon。16 个子项已入库。详见 registry §B4-T2-R1 与 DECISIONS D-20260904-B4T2R1-001。

2026-09-11（batch4 Wave 2）：`B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE` 完成，四 lane 待上传评分——embryo v0009/v0010（L1 mean bridge / L2 mean+mass，11/18 双端共享，7 缺 R keep-parent）、heart v0012/v0013（L1/L2，33/33 全共享；clip 60% 已披露，无 collapse）；geometry 全冻结。L1 双 lane contract PASS，L2 双 lane 行组成四项 FAIL_BY_DESIGN_ACCEPTED；四 lane 重跑字节一致。产物 `artifacts/batch4/B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE-20260911-v1/`，交付包 `deliveries/b4t2r2{a,b,c,d}__t2__upload__20260911.zip`（推荐 embryo L1→embryo L2→heart L2→heart L1）。结论待服务器仲裁。

2026-09-14（batch4 Wave 2）：`B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE` 四 lane 服务器仲裁——embryo v0009=**61.79**（+1.64）晋级、v0010=**62.29**（+2.14）新 best；heart v0013=**62.04**（+4.79）新 best、v0012=56.27（-0.98）淘汰；两 board 均 L2>L1，组成重采样是增量来源；heart 60% clip 未兑现为损伤。derived T2=58.29/Total≈153.71 待确认。详见 registry §B4-T2-R2 与 DECISIONS D-20260914-WAVE2-001。

2026-09-14（batch4 Wave 2）：`B4-T2-R3-HEART-EXTRAP-EXPRESSION-CAL` 完成，三 lane 待上传评分——v0008（L1 damp0.5，clip 0%）、v0009（L2 time1.333，clip 21.6% 已披露）、v0010（L3 popmix，clip 2.4%）；仅 5/22 states 有位移；backtest 偏好小 damp（仅记录）；contract 全 PASS，字节一致。单包 `deliveries/b4t2r3__t2__upload__20260914.zip`（一批一包新规首用）。产物 `artifacts/batch4/B4-T2-R3-HEART-EXTRAP-EXPRESSION-CAL-20260914-v1/`。结论待服务器仲裁。

2026-09-16（G0 15 轮目标）：`G1-T2-R2..R5` 六 lane 服务器仲裁——v0011（收缩）=**50.64**（+0.11）**新 board best**、v0012=**50.26**/v0013=**50.32**/v0014=**50.26**/v0015=**50.28**/v0016=**50.25**（空间族五 lane 全低于 baseline 50.53）；selection 更新为 v0011。本地/服务器方向反转：本地判收缩钉死、空间胜，服务器反之——proxy 教训已记。详见 registry §G1-T2 与 DECISIONS D-20260916-G0T2-001。

## 2026-09-27 两条线索闭环（L-001 / L-002）

- L-001（embryo v0008 同靶 parent 参照）**关闭**：对 parent v0002（SHA `392c470e…`）跑锁定 scorer（`score_h5ad.py` SHA `52034554…`，与 P0-LOCK 一致），同 pseudo-target E7.25／同 reference E6.75／同 seed 20260830，只改 `--input`/`--out`。结果：`neighborhood_mmd` 0.03124→0.03445、`morans_I_agreement` 0.9722→0.9555，**两个独立耦合指标同向变差**；`energy_distance` 改善 −0.01544 属混合信号；其余 14 项置换/几何不变、逐位一致。同靶同 seed 排除了“度量偏祥 parent”解释。附带：parent 臂官方 scorer 0.03124 与 J1 镜像 nfs_parent 0.031240 **逐位吻合**，代理当时无偏差。→ v0008 保持 `HOLD_AS_COMPONENT`（确证拒绝），不上传、不删、不改名。证据 `artifacts/tool_integration/T2-L001-EMBRYO-PARENT-REF-20260927-v1/RESULT.md`。
- L-002（FGW ε 两值敏感性，**非网格搜索**）**关闭为已放弃**：proxy 尺度、ε∈{0.005 冻结, 0.002}、其余逐位复用冻结 J1-PROXY（代价矩阵按 SHA、prepared、alpha/迭代/容差/损失/求解器/离散规则、64 次随机包络）。复现对照通过（相对偏差 ≤7.5e-6，容差 1e-4，未主张位级一致）。结果：分散度大幅下降（有效来源数 64.15→11.46、59.84→12.20；冲突率 0.610→0.395、0.620→0.409；mass capture 0.771→0.854、0.773→0.850）——**Q1 成立**；但 NFS-like 只在 H2 变好（0.015221→0.010517），H1 反而略差（0.011681→0.011805）——**Q2/Q3 未在两 holdout 同时成立**，预声明升级判据未达成，脚本 fail closed。与全尺度 B4-T2-R1（heart ε=0.002 服务器 57.31 vs 57.3 TIE）一致。附带：objective 在两 holdout 都更低而 NFS 只 H2 降，**冻结 objective 与官方度量在 ε 方向不对齐**。证据 `artifacts/tool_integration/T2-L002-FGW-EPS-SENSITIVITY-20260927-v1/RESULT.md`。
- 两者均为**预算外诊断**：零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、未消耗提交配额。J1-PROXY / J1-FGW-ASSIGNMENT / B4-T2-R1 只读未改。决策 `D-20260927-T2LEADS-001`；收口报告 `reports/T2_LEADS_CLOSURE_20260927.md`。
- **T2 现状**：三个 board selection 为 embryo v0010（62.29）／heart_interp v0013（62.04）／heart_extrap baseline v0001（50.53），derived T2 58.29；**本项目内已无未跑的已规划 T2 路线**。唯一未闭合的账是 heart_extrap v0011 已评分 50.64 但未反映在 Total 156.06 的组合里（差 0.11），需重读门户页面。

- 2026-09-27（atom B 补正，`D-20260927-T2LEADS-003`）：L-002 首次执行的复现门（绝对 1e-9）未通过且**原样保留**——根因是参照 TSV 仅 8 位小数，绝对 1e-9 构造上不可达；按用户指示立 atom B 改为**跑前声明**的相对 1e-4 并通过（相对偏差 2.4e-08~7.5e-06）。atom B 与首次执行数字逐位相同（差值 0.000e+00），**非独立复现**，引用须成对。新增落点诊断：两 ε 臂仅 46.05%/45.80% 位置重合，**推翻「落到相同行」的原解读**；正确机制为**冻结目标面在 ε 方向近退化**（两解不同但 objective 差 2.4e-03/4.6e-03），即 `B4-T2-R1` heart 双 TIE 的成因。结论：L-002 仍关闭为已放弃，但「把同一目标解得更好」这条轴在 T2 判为死路。零候选零上传，`submissions/INDEX.tsv` 未改。证据 `artifacts/tool_integration/T2-L002B-FGW-EPS-SENSITIVITY-20260927-v1/`。

- 2026-09-27（`E-N1 SBL` 执行与关闭，`D-20260927-T2EN1-002`）：设计冻结后完整执行，22.1s CPU，**预声明否定判据触发、路线立即关闭**。L1 gated（127/498 基因过 cos≥0.5 门）`nmmd` 0.395969、L2 ungated 0.324687，对 do-nothing 0.031240 **差 10.4–12.7 倍**；预测表达均值比基线高 53–54%。根因是**两条通道间无幅度控制**（回归在 z-score 化表达上做，场项带标准差量级动态范围，加到均值上抬高总质量）——非过平滑、非图案复制。稳定性门几乎无效（开门更少反而更差）。两项自我订正如实记录：设计所写「softplus」实为 `log1p(expm1(x))` 恒等式，**我的首次诊断因此错误**；设计 τ=0.5 与目标 stage E7.5 算术不一致，正确为 0.6。两项均非结果导向调参。**不补救**（不扩参数/不改 K/不调 ridge）；复活须作新 lane 预声明跑前幅度控制。零候选零上传，`submissions/INDEX.tsv` 未改。

- 2026-09-28｜低幅度空间项回分｜心脏插值 v0014、v0015 都是 61.52，比现役 v0013 的 62.04 低 0.52，不晋级。几何三项和现役相同，亏在表达，主要是协变下降。小幅劣化没有在服务器上反过来。选择不变。`D-20260928-T2LOWAMP-002`。

- 2026-09-29｜T2-ROUND2 三新两优化 × 三 board｜15 候选建成（embryo v0011–v0015、heart v0016–v0020、extrap v0017–v0021）：新路线=分位数桥（T1 机制移植）、三阶段趋势/曲率（E6.75、E8.25、E9.5 首次入相应 board）、组成粒度（子状态 / cm 联合状态 / 组成趋势外推）、谱系映射 delta（17 个零位移类型）；优化=v0010/v0013×t 收缩、v0010×G1 尺度回锁、v0013+文库重标定、趋势×收缩、v0011×组成趋势。contract 10 PASS + 5 FAIL_BY_DESIGN_ACCEPTED（R2 同四类）、工程门 15/15、字节重放 15/15、v0011 组件逐值复现、质量计划逐名复现。heart 无 5% nmmd 旗帜（h_n1 本地 nmmd −45%、de +0.36 最强）；x_o2 唯一过历史 R1 局部双门。15 件未提交/未评分，交付 `deliveries/t2r2__t2__upload__20260929.zip`，报告 `reports/t2_round2_20260929/REPORT.md`，决策 `D-20260929-T2ROUND2-001`。选择不变。

- 2026-09-29｜T2-ROUND2 回分（14 条）｜胚胎 v0014 62.89（+0.60）晋级新 board best；心脏插值 v0019 62.36（+0.32，先返回）晋级，v0016 62.35（−0.01）平局备份；v0020 心脏插值 57.74 属表达侧塌。外推 v0019 50.38、v0021 50.52（baseline 平局）都不进合计。另记一次外推文件误投胚胎榜拒收（细胞数对不上，只记 registry）。x_n1_lineage 本次没回分。推导合计 159.95（待门户确认）。`D-20260929-T2R2SCORE-001`。

- 2026-09-30｜T2-ROUND2 收尾：x_n1_lineage v0017 回分 48.17（-2.36 vs baseline 50.53），REJECT。17个零位移类型的谱系映射delta在外推榜不动，variogram 33.3最弱。外推选择不变，第二轮15/15全部回分，队列关闭。`D-20260930-T2XN1SCORE-001`。

- 2026-09-30｜B4-T2-R3迟到回分（三条）｜v0008 48.40（-2.13）REJECT；v0009 50.51（-0.02 vs baseline，平局带内）TIE但不及board-best 50.64，不晋级；v0010 48.87（-1.66）REJECT。v0009的de 50.4是外推尝试中最强的差异表达读数，但总分不动，仅描述。外推选择不变，B4的closed_unscored状态就此结清。`D-20260930-T2R3SCORE-001`。

- 2026-10-01｜goal mupdz021-pfttwg启动：三board×两轮（R1新路线+R2旧优化），设计冻结reports/T2_GOAL_DESIGN_20261001.md + configs/t2_goal/design_20261001.json；R1=embryo v0016趋势份额×现役表达/interp v0021同机制/extrap v0022 E8.25late锚定基线；R2=三board收缩C=1单冻结变体（v0017/v0022/v0023）；6 lane构建中，未提交/未评分。

- 2026-10-01｜goal mupdz021-pfttwg R1三条建成｜embryo v0016趋势份额×现役表达（pass_with_deviation预声明）、interp v0021同机制（pass_with_deviation）、extrap v0022 E8.25late锚定基线（pass）；6/6重放字节一致；轻微问题（embryo var门分母 artifact、h_r2 clip 0.58）如实记录，无严重落后、不重开。未提交/未评分。
- 2026-10-01｜goal mupdz021-pfttwg R2三条建成｜embryo v0017 / interp v0022收缩C=1（行计划与现役逐名一致，pass）、extrap v0023基线收缩C=1（pass）。6候选INDEX登记score_pending，合打一包deliveries/t2goal__t2__upload__20261001.zip（6成员+四件套，receipt READY_NOT_SUBMITTED）。未评分，best不变。

- 2026-10-01｜goal mupdz021-pfttwg回分（6条，队列清零）｜胚胎 v0016 61.65（-1.24）/ v0017 62.55（-0.34）均不敌现役62.89；心脏插值 v0021 62.22（-0.14）/ v0022 62.21（-0.15）均不敌现役62.36；外推 v0023 50.03（-0.50）REJECT，v0022 50.74（+0.21 vs基线/+0.10 vs原最高50.64）恰落平局带上沿，按不并列规则记TIE最高数备份、不晋级。选择不变，推导合计160.07不变（非门户值），门户确认合计仍156.06。外推OPEN项更新为50.74-vs-50.53，待重读门户。`D-20261001-T2GOALSCORE-001`。

- 2026-10-02｜Route C 探索轮打包上传待仲裁（5 件）｜自动研究轮把外推板当算法试验场扫了 10 种做法：胜出机制是「逐基因逐状态的分位数边缘外推」（时间按 4/3 归一）×「组成重采样」，本地冻结 8 通道综合分 3.913，是此前本地最强 lane（x_o2 1.709）的两倍多；同族另外三条（3.464 / 2.608 / 3.606）一并打包。其中 v0027 是诊断探针（library 12 倍，本地护栏不过，不建议占名额），v0028 是同一设计换种子（测服务器侧抽签方差）。五件 contract 均 pass 或既有质量豁免，已登记 INDEX score_pending，未上传。另：本轮纠正了一个旧错误——variogram 本地指标是「越低越好」，Route B 当时方向写反，其 keep 已撤回（详见 `.auto/ROUTE_C_SUMMARY.md`）。`D-20261002-ARROUTEC-001`。

- 2026-10-02｜Route C 五件回分，全部不敌现役｜外推榜：v0025 50.17（最好的一件）、v0024 50.09、v0028 50.08、v0026 50.03，四条都低于基线 50.53；探针 v0027 39.60（崩在 d2 23.6 / mmd_u 37.3 / nmmd 37.6，与本地护栏预警一致）。选择不变（外推 aggregate 仍 50.53，50.74-vs-50.53 OPEN 未动）。三点硬结论：① 本地冻结综合分对新机制「失灵」——17 条合并看相关只剩 0.122（旧 12 条上是 0.539），冠军本地 +3.913 换来 -0.44，说明它不能再用作提交依据；② 唯一确证可迁移的通道是 variogram：本轮把该技能打到 49.5–50.1，是全榜最好（旧 lane 47.4–48.5），与本地（已纠正方向）的排序一致；③ 服务器侧「换种子」几乎无方差——v0024 vs v0028 同设计不同行只差 0.01，而本地综合差 0.31，即本地种子波动是代理噪声不是真方差。`D-20261002-ARROUTCESCORE-001`。

- 2026-10-03｜本地实验1保留、前台目标完成｜坐标中心缩放0.9使固定三种子综合分中位数3.912955→7.523743，3/3护栏通过；全部增益来自尺度项，其他七项不变。v0029（父v0024）已生成且contract PASS，未提交/未评分，HOLD_LOCAL_ONLY；服务器选择不变。D-20261003-T2LOCAL-001；reports/t2_autoresearch_20261003/REPORT.md。

- 2026-10-03｜v0029服务器回分、配置关闭｜总分和8项已入库，v0029 REJECT；仅尺度技能分下降，其余7项与父v0024相同，本地7.524不能解释为服务器收益。当前scale0.9配置关闭，现役不变；先重建留阶段外推评估（NOT_RUN）。D-20261003-T2SCALE-SCORE-001；reports/t2_scale_score_review_20261003/REPORT.md。

- 2026-10-03｜继续优化前重建留阶段评价｜仅用E8.25/E8.75预测E9.5，完整500基因×2基础对照×3评分种子完成；归一误差复制末阶段1.0优于均值位移1.1683，后续以强基线起步并固定几何。新目标10%/5%待确认，新循环未初始化；reports/t2_holdout_setup_20261003/REPORT.md。未新增候选/提交。

- 2026-10-03｜留阶段外推 10% 目标确认＋评估冻结｜用户选 10%（归一中位数 ≤0.90，5% 备选放弃）；独立仓库 `artifacts/t2_holdout_10pct_20261003-v1/`（DESIGN/EVAL_FREEZE/eval_normalized.py/RUN_LOG），evaluator 自检 SETUP_REPRODUCED（复制臂 1.0，位移臂中位数 1.16833）；初轮冻结坐标+行集合只优化表达，reserve NOT_RUN；未新增候选/提交，现役不变。reports/t2_holdout_setup_20261003/REPORT.md。

- 2026-10-03｜留阶段 10% 第一轮收敛封存｜15 次运行（run01–15）：damp 0.25–1.5（最优 0.9）、均值/中位数（中位数胜）、library 守恒（关键）、方差匹配（拒）、类型自适应（平）、剂量括号（闭合 0.9）、供体匹配（拒）、t 掩膜（拒）；组分按标签不可识别（标签域几乎不重叠＋scope 差）。最佳 run10＝0.92868，差目标 0.029；reserve 仍 NOT_RUN，未新增候选/提交，现役不变。仓库 `artifacts/t2_holdout_10pct_20261003-v1/`（RUN_LOG 15 行）。

- 2026-10-03｜留阶段 run10 配方榜单交付｜x_r3_medlib09 v0030（中位数delta×0.9＋library守恒，5共享态/8123行，orphan 保持母本），contract strict PASS、replay 字节一致，SHA `71f587ed…`，INDEX 登记 score_pending，交付包 `deliveries/t2h10__t2__upload__20261003.zip`（receipt READY_NOT_SUBMITTED）；dev 估计 0.9287 系 100% 行基础，榜单部分迁移预期，弱-中置信，未上传/未评分，现役不变。

- 2026-10-03｜crosswalk 榜单交付｜x_r4_xwalk09 v0031（12 映射态/16889 行，10 orphan 保持母本，映射阈值冻结 train-only），contract strict PASS、replay 字节一致，SHA `86fec27f…`，INDEX 登记 score_pending，交付包 `deliveries/t2h10x4__t2__upload__20261003.zip`（receipt READY_NOT_SUBMITTED）；run16 dev 门判 INVALID（行身份泄漏），按 G1 先例直送服务器仲裁，弱置信，未上传/未评分，现役不变。

- 2026-10-03｜HOLDOUT10 双 lane 服务器仲裁｜v0030＝**51.12**（+0.59 vs 基线 50.53，+0.48 vs 原 best 50.64）**晋级新外推 board best**（该榜 2026-09-16 后首次易主）；v0031＝49.91（−0.62）REJECT，mmd 44.3 塌，crosswalk 轴关闭不调阈。16 子项已入库，推导 T2＝58.79（待门户确认）。dev 目标未达成（0.92868 vs 0.90），reserve 仍 NOT_RUN。`D-20261003-T2H10SCORE-001`；reports/t2_holdout10_score_review_20261003/REPORT.md。

- 2026-10-03｜run18 配方榜单交付 v0032｜x_r5_tshrink09（软收缩 w=|t|/(\|t\|+2) 中位数delta×0.9＋library守恒，5共享态/8123行，orphan 保持母本），contract strict PASS、replay 字节一致，SHA `079cc775…`，INDEX 登记 score_pending，交付包 `deliveries/t2h10x5__t2__upload__20261003.zip`（成员 `t2_hrt_ext__x_r5tshk09__v0032.h5ad`，receipt READY_NOT_SUBMITTED）；dev 估计 0.91944（本地最佳，−0.009 vs run10 配方 v0030 服务器 51.12），弱-中置信，未上传/未评分，现役 v0030 不变。

- 2026-10-03｜异路线双 lane 榜单交付（一批一包）｜v0033 x_r6_medlib05（run04 半剂量 0.5＋library守恒，dev 0.93755，DE 方向票最纯）＋v0034 x_r7_typeadapt（run09 逐类型 cos 自适应剂量，dev 0.93470，机制与 v0030/v0032 不同族），2/2 contract strict PASS、replay 字节一致，SHA `32b3fd6e…`/`bcc90053…`，INDEX 登记 score_pending，合包 `deliveries/t2h10x67__t2__upload__20261003.zip`（receipt READY_NOT_SUBMITTED）；现役 v0030=51.12 不变，未上传/未评分。

- 2026-10-03｜HOLDOUT10 三 lane 服务器仲裁｜v0032＝51.14（+0.02，±0.1 带内）**TIE 不晋级**（记数值最高平局备份）；v0033＝50.89（−0.23）REJECT，半剂量削弱服务器 de（50.8 vs 52.0），dev"方向票最纯"读数未兑现；v0034＝51.02（−0.10 带边缘）TIE 不晋级，逐类型自适应剂量无信号关闭。服务器 de 剂量响应单调（0.5→50.8/0.73→51.6/0.9→52.0），dev 剂量括号双端复现；同族三 lane dev↔服务器排序 Spearman 1.0。24 子项入库，现役 v0030=51.12 不变，T2 待分清零。`D-20261003-T2H10X567SCORE-001`；reports/t2_holdout10_score_review_20261003/REPORT.md。

- 2026-10-07｜几何新机制第一刀，只诊断不交卷｜把心脏插值现役坐标的三个主轴相对长度拉到 E8.25 与 E8.75 的正中间，再把整体大小锁回去；表达没动。源侧代理两个括号都更近，判 CONTINUE；胚胎两阶段形状几乎没变，按写死的门关闭。不是服务器分，不建候选。`D-20261007-T2GEOM-002`；artifacts/t2_geom_aniso_20261007-v1/RESULT.md。

- 2026-10-07｜四件几何包，未交卷｜用户再给 3 个新预算。心脏插值交了主轴中点和分位数搬运，胚胎交了同一分位数搬运，心脏外推交了训练曲线外推的形状和大小（倍数 0.890，靠近旧尺度旋钮，已写明）。四件契约通过，现役不动。`D-20261007-T2GEOM4-001`；deliveries/t2geom__t2__upload__20261007.zip。

- 2026-10-07｜四件回分，心脏插值换人｜主轴中点 v0023 得到 62.48，比旧现役高 0.12，超出平局带，换上。形状分升了，占位分降了，所以不是占位修好了。分位数搬运两件和把心脏外推缩小到 0.89 的那件都输了，这两条关掉。`D-20261007-T2GEOM4SCORE-001`。

### 2026-10-09 T2 三板算子迁移收口
Heart interp v0025在exact H1父上迁移心脏重拟合copula，服务器晋级；embryo v0023在exact E3父上恢复均值桥输入XB自身library，数值略升但落±0.1带，保v21；extra v0037在exact X2父上迁移zero-preserve drift，不晋级。三份单线程重放、独立审查、精确panel通过；开发折限制和probe未收敛均披露。今日7/8，仅新授权3/3已耗尽；不再提交。构建worker未推送；用户随后授权专属publisher同步GitHub。详见reports/SERVER_SCORE_REGISTRY.md#t2-operator-transfers-2026-10-09及reports/t2_operator_transfers_20261009/REPORT.md。
