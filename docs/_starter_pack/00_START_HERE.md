# Virtual Embryo Challenge 2026 — Agent 启动包

版本：2026-08-14
用途：让 coding/research agent 在已有数据与环境基础上直接开始第一轮工作。

## 2026-08-22 关闭修订

starter_pack 的主要目的已经完成：搭建可生成、检查、登记并提交榜单候选的基本环境。由于项目已经完成首次合法 scored submission，本包现在标记为 `CLOSED_FOR_COMPETITION_BASELINE`。

关闭条件是官方同步、challenge 数据/面板清单、board-aware submission contract、baseline 候选、本地 scorer smoke、来源登记和首个服务器评分；不是完整科研证据链。原文中的 pseudo-holdout 稳定性、完整 controls、3-seed B1/B2 和 scientific promotion 要求转为 `OPEN_FOR_RESEARCH_EXTENSION`，详见 [`reports/STARTER_PACK_CLOSURE.md`](../../reports/STARTER_PACK_CLOSURE.md)。

后续提交不需要等待科研 Gate；每个候选仍必须通过官方 board contract、格式/数值/空间字段检查并登记 SHA256。

## 一句话目标

维护一个可信、可追溯、合规的 **data → baseline → scorer → artifact → leaderboard** 闭环；pseudo-holdout 和 B1/B2 作为后续候选筛选与研究扩展。

## 本轮不做什么

本启动包不是最终参赛方案，也不是“大模型选型文档”。首轮明确禁止：

- 直接上 diffusion / flow matching / Neural ODE 等高复杂度模型；
- 同时大规模攻坚 T1/T2/T3；
- 用 leaderboard 反复试超参数；
- 未审计就引入外部胚胎数据、预训练模型或包含受保护阶段/基因型的数据；
- 把单次随机种子高分当作有效结论；
- 在官方 starter kit 发布后继续依赖本文件中可能过时的猜测，而不锁定官方实现。

## 默认赛道

默认按 **Human Team** 工作流组织：agent 可以写代码、跑实验、生成诊断；人类可以阅读结果并据此调整方向。

如果实际准备参加 Agent Team，必须重构执行方式：人类不能读取中间结果后继续干预，并且必须保留符合官方要求的 trajectory / prompts / harness 证据。本包当前并不按 Agent Team 的自治约束设计。

## 项目级优先级覆盖

本项目以 Human Team 的 leaderboard 竞争结果为第一目标。首次合法 scored
submission 返回服务器分数时，first-cycle 即视为完成；本包中的 pseudo-holdout、
多 seed、科学 Gate 和报告用于提高候选质量与解释风险，不是后续 leaderboard
submission 的前置门槛。

科学路线和 biological claim 是辅助路线。缺少独立 stage/replicate 时，可以保留
科学状态为 `BLOCKED_FOR_PROMOTION`，但不得因此暂停合规的高分候选生成、提交和
服务器反馈循环。每次提交只保留必要的格式、合规、可追溯性检查；形式化重复检查
不得挤占有效的 leaderboard 尝试。

## 首轮执行顺序

1. 读取 `01_MASTER_AGENT_PROMPT.md` 并将其作为总控提示词。
2. 读取 `02_IMPLEMENTATION_SPEC.md`，严格执行 Gate 顺序。
3. 读取 `03_OFFICIAL_SNAPSHOT_20260814.md`；运行开始时重新检查官网和 starter-kit 状态。
4. 使用 `config/task_contracts.yaml` 建立 submission/data contract。
5. 使用 `config/pseudo_holdouts.yaml` 建立本地伪留出。
6. 维护 `compliance/external_sources.tsv`，任何外部资源先登记后使用。
7. 维护 `experiments/registry.csv`，任何可比较实验必须注册。

## 原始研究扩展标准（关闭后仍可执行，不再是竞赛关闭条件）

必须同时满足：

- challenge 数据输入可以稳定读取并记录 hash；
- T1/T2/T3 submission validator 可运行；
- 官方或等价 floor baseline 可复现；
- 本地 pseudo-holdout scorer 闭环可运行；
- 至少一组对抗性错误预测能被评分/诊断系统正确识别为坏结果；
- 随机种子、配置、git commit、环境和输出均可追溯；
- 若上述全部通过，完成 T2-B1 和 T2-B2 的第一轮实验及消融；
- 输出一份 `FIRST_CYCLE_REPORT.md`，明确：通过项、失败项、可信结论、不可推断事项、下一轮候选动作。

## 强制停止条件

满足以下任一情况时，不得继续堆模型复杂度：

- 官方基线无法复现；
- scorer 与官方行为不一致且原因未定位；
- 数据 schema / gene order / normalization 不确定；
- pseudo-holdout 上的改善小于随机种子波动；
- T2-B1/B2 的改善只来自单一指标而损害其他主要指标；
- 发现外部数据合规疑点；
- starter kit 刚发布且当前实现尚未与其逐项 diff。

出现硬阻塞时生成 `BLOCKER_REPORT.md`，写明：问题、已尝试方案、证据、最小需要的人类决策；不要用泛化描述代替日志。
