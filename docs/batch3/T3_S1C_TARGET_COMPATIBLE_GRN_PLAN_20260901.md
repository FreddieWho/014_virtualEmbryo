# T3-S1C target-compatible GRN atom 方案

版本：2026-09-01  
主线：`T3-S1C-REGULATOR-SOURCE-COMPATIBILITY-20260901`  
父版本：`T3-S1A-STATE-JOIN-20260901-v7`  
关联组件：`T3-S1B-STATE-JOIN-20260901-v3`
状态：`COMPLETED_WITH_HOLD`；S1C-A/v1 与 S1C-B/v3 已完成，未进入 exact E8.75 full rerun

## 目标

建立一个可独立审计的 mm10、500-gene-panel-compatible regulator prior，使 CellOracle 的 `TFdict` source adapter 能明确处理 `Gata4`、`Gata6`、`Ctnnb1`。当前 S1A v7 的 promoter base-GRN 对后两者缺少 source column；本线只修复方法学适用性，不把 Ctnnb1 pathway 伪装成 native promoter GRN。

## 固定边界

- 不修改或覆盖 S1A v7、S1B v3、既有 CellOracle 快照和已评分候选。
- 不把 GRN 中存在的边、motif 或 pathway 解释为 target activity、state specificity、KO response 或 independent biological family。
- 不向既有 parquet 追加 synthetic gene/peak 行；通过 CellOracle 原生 `TFdict` 接口添加明确标注的 source adapter。
- 不改变 500-gene panel、E8.75 exact input、seed、dosage、route 定义或 scorer 配置。
- 在 GRN 身份、schema、taxon、license、source-column presence、panel closure 和 deterministic rerun 全部通过前，不运行 full target inference；不生成 H5AD、不评分、不提交。
- 若需新增外部资源，先记录 source/version/URL 或 commit、许可、下载日期、bytes、rows、SHA256、schema 和 target applicability，并在交付前更新 `infra/bioinf-data-index/`。

## 执行阶段与验收门

1. **Inventory**：核对当前 CellOracle 的 `TFdict` 逻辑，并盘点已有 CollecTRI/OmniPath/CellOracle 资源；不把同一来源的转换副本计作独立证据。
2. **Stage A / regulator prior build**：严格按 CellOracle 原生逻辑把锁定 parquet 转为 base `TFdict`；仅追加 Gata6 的 18 个 CollecTRI 一跳 panel response relation，以及 Ctnnb1 的严格一跳 OmniPath `Ctnnb1→Pitx2` relation。多跳路径全部排除并记录理由。
3. **Capability audit**：逐 target 报告 source membership、response row、panel overlap、方向/权重可用性、缺失和冲突；新增 relation 统一 `activity_eligible=false`、`signed_family_eligible=false`。
4. **Stage B / source-adapter smoke**：只用固定 seed 的 synthetic fixture，分别用新的 Oracle 对象验证 `TFdict` 导入、fit 和 simulate 的结构完整性；不输出 votes、sign、rank 或 state response。
5. **Exact rerun decision**：只有前四门均通过，才另行授权 exact E8.75 target-level rerun；默认 `candidate_generation=false`、`server_submission=false`。

## 预期输出

Stage A atom：`T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1`；Stage B 可复用版本：`T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3`。v1 的 fixture 边界失败 receipt 与 v2 的 post-run volatile-manifest receipt 均保留不可复用。两者分别包含 input lock、edge/TFdict、source audit、能力表、测试/运行 receipt、deterministic hash、completion report 和 gate report。实际结果区分为 `METHOD_SOURCE_COMPATIBLE`、`LOADER_FIT_SIMULATION_SMOKE_PASS`、`BIOLOGICAL_ACTIVITY_NOT_VALIDATED` 与 `HOLD_AS_COMPONENT`；exact E8.75 full rerun 未启动。

## 失败解释

无法找到真实 target-compatible 输入时保持 `BLOCKED_TARGET_COMPATIBILITY`；找到输入但没有独立 activity/stability 时保持 `HOLD_AS_COMPONENT`。两种情况都不构造 synthetic biological sign，不以 proxy、降 panel 或替代 scorer 解除阻塞。
