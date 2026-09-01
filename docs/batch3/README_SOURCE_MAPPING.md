# 本包与依据报告的映射

## 主要来源

- `Virtual_Embryo_Challenge_现有工具与方案总结报告_20260829.docx`
- `PHASE_REPORT_BATCH1_20260829.md`
- 既有 Batch 2 外部数据驱动施工包及其 prompts/artifacts（若仓库存在）

## 映射

| 报告结论 | 本包实现 |
|---|---|
| 强锚 + 中间件 + scorer-aware adapter | `03_ARCHITECTURE_AND_INTERFACES.md` |
| 先锁 scorer/parent/state vocabulary | `P0-LOCK`、`T1-PRE-HARMONIZE` |
| T3 prior committee 优先 | `T3-S1-PRIOR` |
| T1 moscot/WOT + mass + residual decoder | `T1-S2-MOSCOT-DECODER` |
| T2 冻结 G1，只做 board-specific G2/G3 | `T2-S3-SHAPE-FIELD` |
| J1 无 proxy 不再做 | `T2-J1-PROXY` 条件任务 |
| MIOFlow/scDiffEq 只做高风险 kill test | `HX-DYNAMICS-KILLTEST` 冻结任务 |
| 十个薄模块 | `interfaces/virtual_embryo_tools/` |

## 明确未解决

本包不能让工具凭空识别：

- T1 隐藏晚期新状态的真实身份；
- T2 隐藏目标阶段的真实联合生态位；
- T3 未见基因在目标阶段/谱系/状态中的真实因果符号。

它的作用是把这些不可识别部分显式隔离，用合规先验和强收缩减少自由度，而不是把不确定性藏进一个大模型。
