# 原子任务地图（2026-10-05）

竞赛目标是门户榜，不是论文。科学门可以开着，但 `blocks_submission: false`。本地代理分不能当成服务器分。

数字日期：现役与回分止于 2026-10-07。本页不新造分数。门户确认合计仍是 **156.06**（2026-09-26 转录）。按现役相加的 **160.68** 只是推导值，不能写成门户 Total。

## 现在选谁

平局规则：与现役差在 ±0.1 内不换人。`AUDIT.md` 印的是数值最高，不是现役。

| 榜 | 现役 | 分数 | 数值最高但不换人 | 已关闭、别再调 |
|---|---|---:|---|---|
| T1 `val` | v0051 `mix36x38a` | 53.92 | v0054 53.98 | 混合族饱和在 53.3–54.0；扩散 D5/D5b/D5c；外部预训练；逐值手术、图平滑、矩约束、组成加力 |
| T2 胚胎插值 | v0014 `e_o1_shrinkmerge` | 62.89 | — | FGW 的 ε / “把同一目标解得更好”；spateo 未上传保留 |
| T2 心脏插值 | v0023 `h_aniso50` | 62.48 | — | 低幅度空间探针 61.52，未反转；分位数搬运 v0024 60.61 已淘汰 |
| T2 心脏外推 | v0030 `x_r3_medlib09` | 51.12 | v0032 51.14 | 配方族平台期 ~51.1；crosswalk；剂量轴最优 0.9；坐标缩到 0.9；QTE/Route C 本地综合分 |
| T3 `gata4` | v0048 `n2hurdle` | 47.93 | v0058 47.95 | 半步倍率；统一残差；两架构；六项优先（CellOracle/活动/功能/Scouter/GEARS）；六新路线源侧变换（v0078 同分） |

推导：T2 任务均分 (62.89+62.48+51.12)/3 = 58.83。三任务现役和 53.92+58.83+47.93 = 160.68。

## 下一手（没有新授权就不要开工）

- 门户 Total 还没按现役重读。重读前不要把 160.68 写成官方合计。
- 主办方边界邮件已发，等答复。答复前同基因扰动数据保持隔离。
- T1 混合、T2 外推配方、T3 强度扫描都进了平台或负结果。下一波要新机制，不是再扫权重、剂量、倍率。
- T2 留阶段 10% 目标（归一中位数 ≤0.90）未达成，reserve 仍是 `NOT_RUN`。服务器晋级不抵销这个本地目标。
- 待服务器分：INDEX 里还有 6 行 `score_pending`（早期未上传对照，不是当前队列）。当前三任务待分是 0。

## 文件放哪

| 要找的东西 | 唯一位置 | 不要当成正本 |
|---|---|---|
| 候选是谁、SHA、分数状态 | `submissions/INDEX.tsv` | 上传短名、门户 Model 列、旧 zip |
| 服务器分和子项 | `reports/SERVER_SCORE_REGISTRY.md` + `reports/SERVER_SUBMETRIC_REGISTRY.tsv` | 本地 proxy、`AUDIT.md` 的数值最高 |
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
