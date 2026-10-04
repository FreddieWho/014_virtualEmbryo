# reports 怎么读

本目录不搬动。几乎每个文件都被 `STATUS`、决策、追踪或脚本按路径引用。搬走会制造断链，比现在的平铺更难懂。导航靠本文件和 [`INDEX.md`](INDEX.md)。

## 新 agent 只读这些

1. [`SYNTHESIS_T1.md`](SYNTHESIS_T1.md)、[`SYNTHESIS_T2.md`](SYNTHESIS_T2.md)、[`SYNTHESIS_T3.md`](SYNTHESIS_T3.md) — 各任务服务器上什么有效、什么已关。
2. [`../docs/ATOM_MAP.md`](../docs/ATOM_MAP.md) — 现役版本和文件地图。
3. 分数只查 [`SERVER_SCORE_REGISTRY.md`](SERVER_SCORE_REGISTRY.md) 里对应锚点，和 [`SERVER_SUBMETRIC_REGISTRY.tsv`](SERVER_SUBMETRIC_REGISTRY.tsv)。不要在综合里找第二份分数表。
4. 关 lane 的机器表是 [`LANE_VERDICTS.tsv`](LANE_VERDICTS.tsv)。

## 不要误读

- `G1_T1_30ROUND_RESEARCH.md`、`G1_T3_30ROUND_RESEARCH.md` 是 2026-09-16 的调研，标题里的“到 70+”没有实现，不是现行计划。
- `ARCHITECTURE_RESET_BRIEF.md` 和 `BATCH4_*` 的分数停在 2026-09-15。
- `PHASE_REPORT_*`、`RELEASE_CHANGELOG_*`、`FIRST_CYCLE_REPORT.md` 是阶段档案。
- 设计冻结（`*_DESIGN_*`、`*_FREEZE*`）是执行前的合同，结果以回分复盘和 registry 为准。
- 本地综合分、report proxy、留阶段 dev 都不能单独决定提交。T2 Route C 和 T2 scale 0.9 已经在服务器上证伪过这种用法。

历史文档里的 `deliveries/*.zip` 链接，在 2026-10-05 删除已评分包之后会失效。身份看 `submissions/INDEX.tsv`，删除记录看 [`DELETION_MANIFEST.tsv`](DELETION_MANIFEST.tsv)。
