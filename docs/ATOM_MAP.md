# 原子任务地图（2026-10-09）

竞赛目标是门户榜，不是论文。科学门可以开着，但 `blocks_submission: false`。本地代理分不能当成服务器分。

数字日期：现役与回分止于 2026-10-09。本页不新造分数。门户确认合计最后一次读数仍是 **171.4**（2026-10-08T11:58Z，Human rank 61）。按现役相加的 **171.45** 是推导值，不能写成门户 Total。

## 现在选谁

平局规则：与现役差在 ±0.1 内不换人。`AUDIT.md` 印的是数值最高，且只统计 `score_status=scored` 的行——见下方已知缺口。

| 榜 | 现役 | 分数 | 数值最高但不换人 | 已关闭、别再调 |
|---|---|---:|---|---|
| T1 `val` | v0092 `ot_gen_v51` | **58.89** | v0093 `v51_anchor_pergroup` 58.22、v0091 `v51_anchor_auto` 57.99（已被 v0092 取代） | 混合族饱和在 53.3–54.0；late-anchor x1/x2（53.14/53.43）；扩散 D5/D5b/D5c；外部预训练；逐值手术、图平滑、矩约束、组成加力 |
| T2 胚胎插值 | v0021 `e3_scrna_copula` | **63.0047** | — | FGW 的 ε /“把同一目标解得更好”；E3 supportmix（61.39）；state Bures 配对（62.33）；geo coupling（62.65）；spateo 未上传保留 |
| T2 心脏插值 | v0023 `h_aniso50` | 62.48 | — | 低幅度空间探针 61.52，未反转；分位数搬运 v0024 60.61 已淘汰 |
| T2 心脏外推 | v0030 `x_r3_medlib09` | 51.12 | v0032 51.14（±0.1 带内不换人） | 配方族平台期 ~51.1；crosswalk；剂量轴最优 0.9；坐标缩到 0.9；QTE/Route C 本地综合分；外部终点秩 v0036 50.47 |
| T3 `gata4` | v0088 `condhurdle` | **53.69** | — | 半步倍率；统一残差；两架构；六项优先（CellOracle/活动/功能/Scouter/GEARS）；六新路线源侧变换（v0078 同分）；arank r2（49.34）；发射器成分轴（见下） |

推导：T2 任务均分 (63.0047+62.48+51.12)/3 = 58.87。三任务现役和 58.89+58.87+53.69 = 171.45。

`AUDIT.md` 的「Server bests」目前印 T1 57.99 / T2 胚胎 62.89，**低于上表现役**。原因：`scripts/generate_audit.py:42` 只统计 `score_status == "scored"`，而 v0092、v0093、v0021 及 54 行历史行用的是 `score_status == "registered"`。两者都带服务器分。这是既有 schema 不一致，不是分数缺失；**本表的分数一律以 `reports/SERVER_SCORE_REGISTRY.md` 为准**。是否统一该字段待 coordinator 裁决。

## 下一手（没有新授权就不要开工）

- **门户 Total 必须按现役重读。** 171.4 是 2026-10-08T11:58Z 的读数，早于 T1 v0092 与 T2 胚胎 v0021 两次易主。重读前不要把 171.45 写成官方合计。
- 门户榜单页显示的 T1 58.0 / T2 59.7 / T3 53.7 与本表现役和（58.89 / 58.87 / 53.69）**对不上**。T3 能对上（53.7≈53.69），T1、T2 对不上。重读时一并核对门户的 per-task 口径。
- 主办方边界邮件已发，等答复。答复前同基因扰动数据保持隔离。
- T2 胚胎 scRNA copula 是目前唯一拿到**服务器高精度晋级**的路线（+0.1117，经官方公开 API 解析，超出 ±0.1 带）。T1 late-anchor/OT、T2 心插几何各自成波，但只有 T2 这波用服务器分做了高精度仲裁。
- T3 发射器成分轴已扫完并判定饱和：最好变体 +0.0034 本地分（噪声级），`de_skill` 在所有变体中变化恰为 0。**T3 本地源侧指标不再是有效目标**，下一手要么直接用服务器分仲裁（需授权），要么改响应结构开新路线。
- T3 提交额度待确认：registry 记 2026-10-08 v0088 用尽当日 T3 用量 8/8 并声明无剩余授权；**2026-10-09 T3 无提交记录**，当日额度是否已重置未观测。OPEN。
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
