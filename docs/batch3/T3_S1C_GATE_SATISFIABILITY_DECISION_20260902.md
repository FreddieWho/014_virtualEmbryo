# T3-S1C activity gate 可满足性与 claim 定界

版本：2026-09-02  
类型：decision/preflight atom（文档与契约审计，不运行模型）  
主线：`T3-S1C-GATE-SATISFIABILITY-20260902-v1`  
父版本：`T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1`、`T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3`、`T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3`  
状态：`COMPLETED_WITH_HOLD`；当前 activity gate 在现行 firewall 下判定为 `UNSATISFIABLE_UNDER_FIREWALL`

## 1. 本 atom 的范围

本 atom 只回答一个问题：当前 T3 route gate 所需的 biological activity/stability 证据，是否能在正式允许的数据范围内获得。它不读取新矩阵、不运行 CellOracle/scTenifold、不改变 route 状态、不生成 H5AD、不评分、不提交服务器。

审计输入为：

- [T3 执行顺序与 gate](/home/huyudi/014_virtualEmbryo/docs/batch3/02_EXECUTION_ORDER_AND_GATES.md)；
- [T3-S1C target-compatible GRN 方案](/home/huyudi/014_virtualEmbryo/docs/batch3/T3_S1C_TARGET_COMPATIBLE_GRN_PLAN_20260901.md)；
- [T3-S1B 候选生成前置契约](/home/huyudi/014_virtualEmbryo/docs/batch3/prompts/T3_S1B_PRIOR_TO_CANDIDATE.md)；
- [外部数据 firewall](/home/huyudi/014_virtualEmbryo/docs/batch2/compliance/DATA_FIREWALL_SPEC.md) 与 [T3 protected windows](/home/huyudi/014_virtualEmbryo/docs/batch2/compliance/protected_windows.yaml)；
- S1A v7、S1B v3、S1C-A/v1、S1C-B/v3、S1D/v3 的稳定 receipt、gate 和协调状态。

## 2. 所需证据与允许证据对照

| 证据对象 | 旧 gate 需要什么 | firewall 下的状态 | 现有结果 | 结论 |
|---|---|---|---|---|
| E8.75 target-specific perturbation | 可重复、state-matched、signed biological response | held-out 等价扰动/同基因可比阶段扰动禁止 | 无 | 不可满足 |
| E8.75 WT | 同一状态的参考背景 | 默认允许 | S1A exact WT 已锁定 | 只能支持 WT-context coherence，不能识别 KO effect |
| 远窗口 target perturbation | 可迁移到 E8.75 的 target activity | 需逐 source/permit 审计，且本身不是 E8.75 state match | 未计入 S1D family | 不能桥接为 E8.75 activity |
| 远窗口非目标扰动 | target-specific signed response | 可作为方法迁移检查时才有意义 | 无 target-specific 结论 | 不能支持目标 activity |
| CollecTRI/OmniPath | state-specific in-vivo activity | 允许作为 contextual knowledge | S1B integration PASS | `GLOBAL_CONTEXTUAL`，不是 biological family |
| S1D E9.5 Gata4/Ctnnb1 | E8.75 independent signed family | 现为 quarantine context，且阶段/组织不匹配 | Gata4 2 family、Ctnnb1 1 family，E8.75 eligible 为 0 | 只能保留历史描述性 context |

## 3. 决策

### 3.1 当前严格主线

保持旧 gate 不变：

- `T3-S1A-GATE-001` 继续 `HOLD`；
- `biological_activity=NOT_VALIDATED`；
- `signed_family_stability=NOT_IDENTIFIABLE`；
- `candidate_generation=false`；
- `server_submission=false`；
- `blocks_submission=false`。

不得通过重复 S1B、扩大网络知识、WT/远窗口代理、unsigned rank 或 S1C smoke 清除该 gate。

### 3.2 只有正式授权后才可采用的 scope-change 分支

若确实需要继续推进候选生成，必须建立新的 contract 版本，而不是修改 S1B v3：

1. 保留 firewall compliance 和 method/source compatibility 为硬门；
2. 新增、预先冻结并单独命名 `WT-context regulatory coherence`；
3. 将 target-specific E8.75 perturbational activity 明确标为 `NOT_TESTABLE_UNDER_FIREWALL`，不得改名为已验证 activity；
4. 在新 contract 的所有门通过前，仍保持 `candidate_generation=false`；
5. 旧 S1A–S1D artifact、gate 和历史结论不可追溯修改。

这属于实质性的 claim/gate 变更，需要用户或 contract owner 明确授权。本 atom 不自动采用该分支。

## 4. 后续 exact rerun 的条件

当前不启动 exact E8.75 S1C rerun。只有在上节 scope-change 分支获正式授权，或 contract owner 明确确认 exact rerun 仅作非因果方法诊断后，才可另建：

`T3-S1C-C-EXACT-E875-WT-INFERENCE-20260902-v1`

固定输入与边界：

- exact E8.75 WT、冻结 state labels、S1A v7 input/state manifest、S1C-A/v1 adapter、S1C-B/v3 runtime；
- 不读取 S1D quarantine 矩阵，不把任何外部 target perturbation 用于拟合、调参、阈值选择或模型选择；
- 固定 seed、排序和 target 查询，一次预定运行，无网格搜索；
- 只报告 target mapping、WT-context coherence、modelled state response、coverage、稳定性和运行 receipt；
- 失败或部分输出不得标为 PASS；不得生成候选、运行 scorer 或上传服务器。

即使该 atom 通过，也只能清除新定义的 coherence/method gate，不能清除旧 target-specific activity gate。

## 5. firewall 与 S1D 的复用说明

官方快照确认 T3 的 held-out 条件为 Gata4 KO 与 β-catenin KO @ E8.75，并提示同基因其他 allele、相近 stage 或明显 phenocopy 也可能属于 held-out。现行 firewall 同时明确：WT 默认允许，target perturbation 默认排除，quarantine 只能用于 metadata inspection 与立即过滤。

因此：

- 外部建议中“所有同组织 WT 都不可用”不是正式规则原文，不写入新 contract；
- S1D v3 的 E9.5 矩阵不追溯删除，但在用途未重新取得明确 permit 前，不得作为模型或统计验证输入继续复用；
- 本 atom 没有新增外部数据，`infra/bioinf-data-index/` 不需更新。

## 6. 停止边界与风险

本 atom 完成于可满足性结论和两条正式分支已经明确之处。继续搜索近 E8.75 target KO/KD/mutation、把远窗口结果桥接到 E8.75、或把 WT coherence 改写成 biological activity，均属于 semantic laundering 或 firewall 偏航。

当前硬阻隔不是“尚未找到足够数据”，而是旧 gate 所需证据集合与现行 fail-closed firewall 的允许集合没有足够交集。若不修改 claim/gate，保持 `HOLD` 是完整且有效的结果。
