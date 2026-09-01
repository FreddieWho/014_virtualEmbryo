# T2 任务追踪：spatial-temporal

更新时间：2026-08-29

T2 有多个 board；不同 board 的分数不能直接当作同一个指标比较。服务器分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。

## 当前状态

- 当前最高 aggregate：**149.5（服务器当前返回值）**
- 当前最佳分叉：按 board 选择 B1-A1 L1（embryo interpolation、heart interpolation）+ baseline（heart extrapolation）
- 当前 T2 task 分数：**55.7（服务器当前返回值）**
- 当前最佳 board：embryo interpolation **60.1**、heart interpolation **56.3**、heart extrapolation **50.5**；raw score/ID 以 `reports/SERVER_SCORE_REGISTRY.md` 为准
- 下一步：B1-A4 六个候选已完成服务器评分但未提升当前 per-board selection；不启动 B1-C1 重复缩放或新的 T2 atom

## Top 3 路线

排序依据是“当前 aggregate 保留优先级 + 已有 board 分数”；不同 T2 board 不做未经说明的跨 board 横比。

| 位次 | 路线 | 通俗说明 | 服务器证据 | 状态 |
|---|---|---|---|---|
| 1 | 当前 per-board selection | B1-A1 L1 保留 embryo/interp，heart extrap 回到 baseline | server T2 **55.7**；server Total **149.5** | 以服务器当前榜单为准；不是手工 composite |
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

## B1-A1 服务器结果与决定

- 六个服务器 ID 与 raw score 已登记在 `reports/SERVER_SCORE_REGISTRY.md`；成绩按用户回填记录。
- L1 相对 L2 在 embryo interpolation、heart interpolation、heart extrapolation 分别领先 0.2、1.0、0.4 分；这是 B1-A1 lane 内比较，不覆盖更高的 baseline heart-extrapolation 分数。
- L1 相对各自 parent 在 embryo interpolation 与 heart interpolation 上提升，在 heart extrapolation 上下降 0.3 分；因此当前 T2 选择必须按 board 混合保留，不是三 lane 全部采用 L1。
- 选择：当前 T2 board 使用 L1 的 embryo/interp 与 baseline 的 heart extrap；L2 作为同批第二候选和审计备份保留；不追加 B1-A1 第三 lane 或事后调参。

## B1-A4 服务器结果与决定

- 六个 B1-A4 候选均已 scored；embryo interpolation 两条低于 B1-A1 L1 的 60.1，heart interpolation 两条与当前 56.3 持平，heart extrapolation 两条低于 baseline 50.5。
- A4 全 L1 的 board 值只能推导为 T2 `55.2`，全 L2 为 `55.1`；服务器未返回新的 Total，当前服务器 T2 `55.7`、Total `149.5` 保持不变。
- 决定：B1-A4 不晋级；六份 artifact 作为不可变 scored 记录保留；不启动 B1-C1 重复缩放或新的 T2 atom。

## 下一步

B1-A4 已完成六个 contract-valid 候选及服务器评分；结果未改善当前选择，下一步等待新的明确授权。若需要科学晋级，仍需独立 stage/replicate 证据；本次 leaderboard 分数不构成因果机制证据。
