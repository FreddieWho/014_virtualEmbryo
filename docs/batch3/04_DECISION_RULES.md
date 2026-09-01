# 决策规则与最低证据标准

## 1. 证据层级

1. 服务器登记与 immutable submission hash；
2. 当前可运行 scorer/contract；
3. 完整 candidate 的 local score；
4. source-only pseudo-holdout；
5. 训练期 proxy、可视化和工具内部 loss。

下层证据不能被包装成上层结论。尤其不能把 proxy 改善称为服务器提升。

## 2. 通用结论

### `READY_FOR_MANUAL_SUBMISSION`

必须同时满足：

- contract 与 invariant 全部通过；
- parent/scorer/board/hash 已锁定；
- 预声明主指标或 gate 改善；
- 受保护原子没有超过 P0 推导出的容忍范围；
- lane 未经过服务器反向调参；
- 产物完整且可人工上传。

### `HOLD_AS_COMPONENT`

适用于：

- 总体未胜 parent，但一个原子有独特、可重复改善；
- 与 current best 错误互补；
- 组件可在不重新训练的情况下与强 parent 组合；
- 没有违反 protected checks。

### `REJECT`

任一条件满足即拒绝：

- 预定原子没有改善；
- protected invariant 被破坏；
- 只是换 backbone/增加容量，没有改变识别假设；
- source-only proxy 与服务器已知方向冲突且没有新证据解释；
- 需要服务器分数才能确定符号、top-k、幅度或 lane 定义。

### `BLOCKED_*`

用于验证链、合规或工具链的硬阻塞。阻塞不是失败，也不是许可临时换方法。必须写清：

- 阻塞对象；
- 已完成动作；
- 最小解除条件；
- 不解除时损失什么。

## 3. P0 Gate

通过条件：

- scorer/contract 的文件、命令、版本和 SHA256 已记录；
- current parent 可定位、可校验、可复现读取；
- board registry 与 server registry 一致；
- T1 full-panel scorer 至少能对 parent 完成一次；
- 版本冲突有明确映射或被标为 hard blocker；
- Batch 2 可复用产物完成 hash 核验。

## 4. T3 prior gate

### 必须通过

- sign convention test 通过，明确 `KO - WT`；
- strict lane 中每个非零响应至少有两个独立 evidence family；
- directness 只提升置信度，不单独决定 sign；
- conflict gene 在 strict lane 为 0；
- Mesp1 lineage/state gate 可审计；
- nonzero panel fraction 不超过预声明 cap；
- 对已观测训练 KO 的 WT-only adapter 检查中，DES/DCS proxy 不得同时低于 identity；该检查只验证 adapter/sign，不用于调 Gata4 参数。

### 结果解释

- prior gate 通过：允许执行 `T3-S1B-GENERATE`；
- 只有 weighted lane 通过：`HOLD_AS_COMPONENT`，不得直接宣称 target prior 已成立；
- 两条均不通过：保留 `wt_identity`，停止幅度建模。

## 5. T1 Gate

### PRE-HARMONIZE

- crosswalk 对官方 E8.5/E9.5 重映射稳定；
- 低置信 state 明确进入 `UNRESOLVED`，不能强配；
- pseudo-holdout 复用同一 vocabulary；
- full-panel scorer 可运行。

### MOSCOT-DECODER

- coupling 与 state mass 有明确输入/输出和 mass conservation/unbalanced 说明；
- 小 state 有预声明 shrinkage；
- empirical lane 保持 residual 共变；
- module-scDesign3 不运行全基因 copula；
- 至少一个 lane 的预定原子改善；
- 未负责的 P1 不被宣称解决。

## 6. T2 shape gate

必须满足：

- parent 的表达矩阵与表达行顺序不变；
- board-specific G1 RMS 恢复到 P0 容忍范围内；
- 不使用绝对坐标 MSE 作为主要选择标准；
- source-only pseudo-holdout 中，G2/G3 proxy 至少在两个独立 holdout 同方向优于 parent或低成本基线；
- kNN overlap/拓扑破坏不超过由训练期真实相邻阶段形变估计出的合理区间；
- heart extrapolation 不复用插值系数，必须有独立 regime 与强收缩。

## 7. T2 J1 proxy gate

只有以下条件全部满足才允许生成正式 assignment candidate：

- 在至少两个 source-only leave-one-stage-out 中优于 random permutation；
- 改善方向一致，不出现一个 board 大幅正、另一个大幅负的无解释情况；
- objective 与 official NFS-like 实现使用相同近邻定义或已记录差异；
- 不以形态分改善冒充 NFS 改善；
- Batch 1 greedy pairing 的失败假设没有被原样重复。

## 8. 服务器使用

- 服务器只用于人工上传后的候选选择；
- 不用显示分数反推隐藏 ground truth；
- 不据服务器结果改 prior 符号、top-k、幅度、shrinkage 或 lane 定义；
- tie 记录为 tie，不称为改进；
- 负结果和原始候选不可变保留。
