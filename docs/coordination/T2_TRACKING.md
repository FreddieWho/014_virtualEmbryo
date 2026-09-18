# T2 任务追踪：spatial-temporal

更新时间：2026-09-03

T2 有多个 board；不同 board 的分数不能直接当作同一个指标比较。服务器分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。

## 当前状态

- 当前最高 aggregate：**149.5（服务器当前返回值）**
- 当前最佳分叉：按 board 选择 B1-A1 L1（embryo interpolation）+ T2-S3 L1 pycpd（heart interpolation）+ baseline（heart extrapolation）
- 当前 T2 task 分数：**55.7（服务器当前返回值）**；heart_interp 晋级 56.7 后推导 T2≈55.8、Total≈149.6（derived，待服务器页面确认）
- 当前最佳 board：embryo interpolation **60.1**、heart interpolation **56.7**、heart extrapolation **50.5**；raw score/ID 以 `reports/SERVER_SCORE_REGISTRY.md` 为准
- 下一步：T2-S3 两条 READY 候选已评分（embryo 59.7 未提升、heart_interp 56.7 +0.4 晋级）；T2-J1-PROXY gate `J1_PROXY_PASS`（2026-09-03），FGW soft-assignment objective 值得重启 J1 路线，授权 assignment candidate 前需审视 heart 参考构建质量

## Top 3 路线

排序依据是“当前 aggregate 保留优先级 + 已有 board 分数”；不同 T2 board 不做未经说明的跨 board 横比。

| 位次 | 路线 | 通俗说明 | 服务器证据 | 状态 |
|---|---|---|---|---|
| 1 | 当前 per-board selection | B1-A1 L1 保留 embryo interp，T2-S3 L1 保留 heart interp（56.7），heart extrap 回到 baseline | server T2 **55.7**；server Total **149.5** | 以服务器当前榜单为准；heart_interp 晋级后的新 aggregate 待服务器确认 |
| 2 | B1-A1 `L1_FORMAL_LOG_RMS` | 只做 source-only 的统一 G1 空间尺度校准 | raw board scores **60.1/56.3/50.2** | embryo/interp 胜出；heart extrap 低于 baseline 50.5 |
| 3 | B1-A1 `L2_ALL_STAGE_LOG_RMS_OLS` | 用全部训练阶段的 log-RMS OLS 校准统一尺度 | raw board scores **59.9/55.3/49.8** | 已评分；各 board scored backup |

raw server scores、submission ID 和证据只在 `reports/SERVER_SCORE_REGISTRY.md` 维护；当前 T2=55.7、Total=149.5 是服务器返回值，不用显示的一位小数自行反推。

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
