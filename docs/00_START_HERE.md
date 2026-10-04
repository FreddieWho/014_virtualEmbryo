# 先读这里（不要扫整个仓库）

这是竞赛项目。新 agent 用下面 6 个文件就能接手，不必从 `docs/batch*/prompts` 或 `reports/` 全文开始。

1. [`ATOM_MAP.md`](ATOM_MAP.md) — 现在各榜现役、已关闭的路、文件放哪。
2. [`../reports/README.md`](../reports/README.md) — 报告怎么读；任务结论在 `reports/SYNTHESIS_T1.md` / `T2` / `T3`。
3. [`../STATUS.md`](../STATUS.md) — 给人看的近况。数字以索引为准，不以本文件旧段落为准。
4. [`../submissions/INDEX.tsv`](../submissions/INDEX.tsv) — 候选身份、路径、SHA256、服务器分。唯一文件账。
5. [`../reports/SERVER_SCORE_REGISTRY.md`](../reports/SERVER_SCORE_REGISTRY.md) — 服务器分数唯一账。只翻相关锚点，不要通读。
6. [`coordination/T1_TRACKING.md`](coordination/T1_TRACKING.md) / [`T2_TRACKING.md`](coordination/T2_TRACKING.md) / [`T3_TRACKING.md`](coordination/T3_TRACKING.md) — 路线变更流水。先看文末。

审计链仍是：[`../AUDIT.md`](../AUDIT.md)（`python scripts/generate_audit.py` 生成，手改无效）→ [`../reports/LANE_VERDICTS.tsv`](../reports/LANE_VERDICTS.tsv) → INDEX → [`../TODO.md`](../TODO.md)。`AUDIT.md` 的数字最高分不是现役：±0.1 平局带内现任留下。

## 不要跟着走的目录

- `batch1/`、`batch2/`、`batch4/` 的 prompts 和 controller 文是当时的执行包，已经走完。`batch4/` 见 [`batch4/SUPERSEDED.md`](batch4/SUPERSEDED.md)。
- `batch3/prompts` 同样是历史。**不要移动** `batch3/interfaces/` 和 `batch3/config/`：前者被 20+ 脚本 import，后者是依赖锁。
- `_starter_pack/` 是官方快照，只读。`starter_pack` 是指向它的兼容链接（旧文档写过不带下划线的路径）。
- `coordination/STATUS.md` 是并行状态机摘要，不是入门读物。先看 ATOM_MAP。

官方规则缓存：`_starter_pack/03_OFFICIAL_SNAPSHOT_20260814.md` 和 `../reports/OFFICIAL_SYNC.md`。缓存缺失或用户要求时才重新抓官网。
