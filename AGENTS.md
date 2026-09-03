# Project-level agent constraints

本文件只补充本项目的协作与更新规则；全局安全、工具和文件编辑约束继续适用。

## Required entrypoint

开始任何 T1/T2/T3 工作前，先阅读：

1. `docs/coordination/README.md`
2. `docs/coordination/STATUS.md`
3. 对应任务契约和现有权威索引

## Concise update rules

- 只在有决策价值的事件发生时更新文档：候选生成、contract 检查、提交、服务器评分、保留/淘汰、阻塞、共享结论或技术方案晋级。禁止为了显示活跃而频繁更新。
- `docs/coordination/STATUS.md` 是当前状态摘要，由 coordinator 串行更新；不要让多个 agent 同时编辑它。
- `docs/coordination/DECISIONS.md` 只追加，不覆盖或删除历史决策。
- `docs/coordination/KNOWLEDGE.md` 中的科学结论必须带成熟度、证据和限制；假设不得写成事实，T2/T3 的比赛分数不得单独写成因果机制证据。
- 候选文件、SHA256 和 contract 只登记在 `submissions/INDEX.tsv`；服务器分数、submission ID 和原始证据只登记在 `reports/SERVER_SCORE_REGISTRY.md`。不要维护第二份完整分数表。
- agent 只修改自己拥有的任务路径；共享代码先登记 lease。已评分 artifact 不得覆盖、重命名或静默替换。
- 每次 handoff 必须说明任务、candidate ID、父版本、artifact、SHA256、检查结果、风险、建议决策和 blocker。
- 服务器分数未回填前只能标记为 `score_pending`，不得宣称模型进步；下一次提交前必须提醒用户提供分数和证据。
- 科学阻塞必须标明 `blocks_submission: false`，不得阻断合规的 leaderboard 候选生成或提交。
- 新增外部生信数据时，交付前必须更新 `infra/bioinf-data-index/` 的索引与汇总。
- 官方内容采用 cache-first：先读取 `reports/OFFICIAL_SYNC.md`、`docs/starter_pack/03_OFFICIAL_SNAPSHOT_20260814.md`、已下载 notebook 和 `infra/bioinf-data-index/`；只有缓存缺失、疑似过期、用户明确要求或官方状态有变化风险时才重新抓取官网。重新抓取后必须记录日期、来源和变化。
- 核心计算不得静默跳过、替代或降级；无法执行时必须记录原因、状态和对结论的影响。
- 长任务只使用事件驱动或低频状态检查；无新信息时停止轮询。
- 每次候选新建、参数修改或路线分叉，必须在对应 `docs/coordination/T{1,2,3}_TRACKING.md` 追加一行通俗变更摘要；只有当前 best、Top 3、任务状态或下一步变化时才更新根目录 `STATUS.md`。
- `STATUS.md` 只做人的快速入口；候选哈希以 `submissions/INDEX.tsv` 为准，服务器分数以 `reports/SERVER_SCORE_REGISTRY.md` 为准。未评分路线必须写 `未评分/未提交`，不得排成已验证高分。

## Ownership defaults

- T1/T2/T3 专属代码、输出和候选由对应 agent 负责。
- `docs/coordination/`、`submissions/INDEX.tsv` 和 `reports/SERVER_SCORE_REGISTRY.md` 由 coordinator 负责。
- `docs/starter_pack/` 默认只读；其中的官方契约优先于旧叙述。

## Manual-upload naming rule (fixed 2026-09-03, mandatory)

交付 zip 成员名（= portal Model 名）必须为 `<task>_<board>__<lane>__v<NNNN>.h5ad`，全小写、总长 ≤50 字符；zip 包名为 `<atom短码>__<task>__upload__<YYYYMMDD>.zip`，≤50 字符。board 短码与细则见 `submissions/README.md`。身份核验以 SHA256 与 `submissions/INDEX.tsv` 为准，短名不承载语义完整性；历史长名 artifact 不回溯改名。
