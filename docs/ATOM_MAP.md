# 原子任务地图（2026-10-09）

竞赛目标是门户榜，不是论文。科学门可以开着，但 `blocks_submission: false`。本地代理分不能当成服务器分。

数字日期：现役与回分止于 2026-10-09。门户确认合计 **172.9**（用户 2026-10-09 确认；per-task T1 58.9 / T2 60.3 / T3 53.7；registry 记 Human 71/187 @ 09:23:59Z）。按现役相加 **172.857**，与门户合计在显示精度内一致。

## 现在选谁

平局规则：与现役差在 ±0.1 内不换人。`AUDIT.md` 印的是数值最高，且只统计 `score_status=scored` 的行——见下方已知缺口。

| 榜 | 现役 | 分数 | 数值最高但不换人 | 已关闭、别再调 |
|---|---|---:|---|---|
| T1 `val` | v0092 `ot_gen_v51` | **58.89** | v0093 `v51_anchor_pergroup` 58.22、v0091 `v51_anchor_auto` 57.99（已被 v0092 取代） | 混合族饱和在 53.3–54.0；late-anchor x1/x2（53.14/53.43）；扩散 D5/D5b/D5c；外部预训练；逐值手术、图平滑、矩约束、组成加力 |
| T2 胚胎插值 | v0021 `e3_scrna_copula` | **63.0047** | v0023 `source_library` 63.0185（Δ+0.0138，带内不换人） | FGW 的 ε /“把同一目标解得更好”；E3 supportmix（61.39）；state Bures 配对（62.33）；geo coupling（62.65）；spateo 未上传保留 |
| T2 心脏插值 | v0025 `h_heart_copula` | **66.7064** | — | 低幅度空间探针 61.52；分位数搬运 v0024 60.61；各向异性 v0023 62.48（被 v0025 超越 +4.23） |
| T2 心脏外推 | v0030 `x_r3_medlib09` | 51.12 | v0032 51.14（±0.1 带内不换人） | 配方族平台期 ~51.1；crosswalk；剂量轴最优 0.9；坐标缩到 0.9；QTE/Route C 本地综合分；外部终点秩 v0036 50.47；零保位移 v0037 48.86 |
| T3 `gata4` | v0088 `condhurdle` | **53.69** | v0089 `resplam15unmask` 未评分（本地 +0.1985） | 半步倍率；统一残差；两架构；六项优先（CellOracle/活动/功能/Scouter/GEARS）；六新路线源侧变换（v0078 同分）；arank r2（49.34）；发射器成分轴（饱和）；联合秩传输新架构（−12.07 负结果） |

T2 任务均分 (63.0047+66.7064+51.12)/3 = **60.2770**。三任务现役和 58.89+60.2770+53.69 = **172.857** ≈ 门户 172.9。

**per-task 已对账（2026-10-09 关闭）。** 此前记录的"T1/T2 与现役和对不上"已解决：T1 门户 58.9 = v0092 58.89，T3 门户 53.7 = v0088 53.69，T2 门户 60.3 = 选集均值 60.2770。门户 T2 用的是各榜**数值最高**（embryo v0023 63.0185 + 心插 v0025 66.7064 + 外推 51.1388）/3 = 60.2879，与选集的差 0.011 完全来自 ±0.1 带内的两处保留（胚胎、外推），显示精度下同为 60.3。

`AUDIT.md` 的「Server bests」只统计 `score_status=scored`，而 66+ 行用 `registered`（含 v0092/v0093/v0021/v0025），故其数值最高低于现役。这是既有 schema 不一致，不是分数缺失；**分数一律以 `reports/SERVER_SCORE_REGISTRY.md` 为准**。是否统一该字段待 coordinator 裁决。

## 下一手（没有新授权就不要开工）

- 门户合计与 per-task 均已按现役确认（172.9 / 58.9 / 60.3 / 53.7），无待重读项。下一次现役变动后须重新确认。
- 主办方边界邮件已发，等答复。答复前同基因扰动数据保持隔离。
- T2 心插 v0025 copula（66.7064，官方 API 精度）是目前**最大单榜跃升**（+4.23 vs v0023）；其与 T2 胚胎 v0021 同属 scRNA copula 族，值得作为优先方向继续。embryo 侧 v0023 已在带内，继续同族微调的边际收益应按 v0023 与 v0021 的 0.0138 差距估计。
- T3 发射器成分轴已扫完并判定饱和：最好变体 +0.0034 本地分（噪声级），`de_skill` 在所有变体中变化恰为 0 —— **发射器只重分配已激活细胞，不能改变 DE 集合**。
- T3 **响应结构**才是 DE 的所在：收缩 lam nk/(nk+50)→nk/(nk+15) 并去掉 `global_valid` 掩码，本地 +0.1985（赢 4/7，冻结门 PASS），已建候选 **v0089** 并打包 `deliveries/t3lam15__t3__upload__20261009.zip`（`score_pending`、未提交）。增益不均匀（Ehmt2 +1.0 对 Dnmt1 −0.855）。
- T3 联合秩传输新架构本地 −12.07 且对照组不变，是干净负结果。状态粒度（S≠8）与分位数分辨率（nq≠21）两族作为响应替换 fail closed，需**整体重训模型**才能测，未执行。
- T3 提交额度待确认：registry 记 2026-10-08 v0088 用尽当日 T3 用量 8/8 并声明无剩余授权；**2026-10-09 T3 无提交记录**，当日额度是否已重置未观测。**上传 v0089 需你明确重新授权。**
- T2 留阶段 10% 目标（归一中位数 ≤0.90）未达成，reserve 仍是 `NOT_RUN`。服务器晋级不抵销这个本地目标。
- 待服务器分：INDEX 里 6 行 `score_pending` 全是早期未上传对照（v0001/v0007/v0008 系列），不是当前队列。当前三任务待分是 0。

## 文件放哪

| 要找的东西 | 唯一位置 | 不要当成正本 |
|---|---|---|
| 候选是谁、SHA、分数状态 | `submissions/INDEX.tsv` | 上传短名、门户 Model 列、旧 zip |
| 服务器分和子项 | `reports/SERVER_SCORE_REGISTRY.md` + `reports/SERVER_SUBMETRIC_REGISTRY.tsv` | 本地 proxy、`AUDIT.md` 的数值最高（只统计 `score_status=scored`） |
| 候选 h5ad | `submissions/candidates/<board>/vNNNN_<method>/submission.h5ad` | `artifacts/` 里的运行副本；`deliveries/` 里的打包 |
| 脚本锁定的早期父本 | `submissions/scored/baseline-001/`（按 SHA 读取，不能搬） | 不要并进 candidates |
| 已评分上传包 | 2026-10-05 已删。记录在 `reports/DELETION_MANIFEST.tsv`，说明在 `deliveries/README.md` | 历史文档里的 zip 链接会失效，身份仍看 INDEX |
| 未评分/作废包 | `deliveries/` 里只剩 VOID 包、留阶段 inspect 包、receipt | 不是候选身份 |
| 路线为什么关 | `reports/SYNTHESIS_T1.md` 等，再点进对应复盘 | `docs/batch*/prompts`、G1“到 70+”调研 |
| 官方契约 | `docs/_starter_pack/`、`reports/OFFICIAL_SYNC.md` | 不要当实时榜 |
| 早期冒烟 JSON | `outputs/`（63KB，可忽略） | 不要并进 reports |

## 和旧批次的关系

Batch 1–4 的设计包是当时的施工图，结论已经进 INDEX 和 registry。活着的只有：

- `docs/batch3/interfaces/`：contract IO，脚本在 import。
- `docs/batch3/config/`：依赖锁。
- `docs/_starter_pack/`：官方快照。
- `docs/coordination/`：决策、追踪、知识。只追加，不重写历史。

更细的关闭原因和证据指针在三份综合里，不在本页重复分数表。
