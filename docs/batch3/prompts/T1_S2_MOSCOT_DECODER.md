# T1-S2-MOSCOT-DECODER · Temporal coupling、state mass 与双 decoder

## 唯一目标

在锁定的 T1 parent 上，用现有工具替换“全局恒速 shift”的部分假设：

```text
future population
= locked parent cells
+ temporal coupling / state-mass forecast
+ state-specific mean program
+ residual/covariance replay
```

主要覆盖 E1/E2、P2–P4。本 task 不声称解决 P1 隐藏新状态身份。

## 前置

- P0 locks；
- T1 state vocabulary/crosswalk gate 通过；
- T1 full-panel scorer 可运行；
- current parent SHA256 锁定；
- 当前所有 T1 target board/stage 已由 board registry 定义。

## 工具职责

- moscot `TemporalProblem` 优先，WOT/POT 为预声明 fallback；
- coupling 在 state/program latent 上求，不对全部细胞×全部基因暴力计算；
- UOT/state mass 只预测概率质量；
- parent 提供完整 32,285-gene 背景与 residual；
- scDesign3 只作为 module-wise decoder，不作为时间模型。

## 共用施工

### 1. Coupling

- 在相邻允许阶段/官方 E8.5→E9.5 求 coupling；
- cost = program distance + lineage/state mismatch penalty；
- 记录 balanced/unbalanced 设定；
- 输出 sparse coupling 与 state transition；
- 小 state 向 lineage mean 收缩。

### 2. Mass forecast

- 从 transport/growth 估计目标 state probability；
- 不预测绝对胚胎细胞数；
- 目标总细胞数沿用 contract/parent 策略；
- 对插值/外推 board 使用独立 time regime；
- 远期不默认相同 slope 无限延伸。

### 3. Mean program

- state-specific pseudobulk delta；
- 与 coupling/mass 解耦保存；
- 对每 board 由锁定时间系数应用；
- 不创建 vocabulary 外的新 state。

### 4. Calibration

仅允许一次 source-only pseudo-holdout 推导解析 `alpha`：

```text
prediction = parent + alpha * structured_delta
```

`alpha` 随后冻结。禁止网格搜索和服务器反调。

## 两条 lane

### L1_EMPIRICAL_RESIDUAL

- state mean shift 后，从匹配 parent state 重放完整 residual row；
- residual source index 固定并保存；
- 优先保持真实多模态和全转录组共变；
- 不逐基因加独立噪声。

### L2_MODULE_SCDESIGN3

- 使用相同 coupling、mass 和 mean program；
- 按 state × gene module 拟合边缘/必要的局部 copula；
- module 定义在 full run 前冻结；
- 不运行全 32,285 gene copula；
- 不相交/低信息基因由 parent residual 保持；
- R 环境输出标准 simulator parameters，再由 core 采样。

若 scDesign3 构成硬工具链阻塞，L1 仍必须完整完成；L2 标记 `BLOCKED_TOOLCHAIN`，不得临时换成第三种生成器。

## Source-only 检查

一次 E8.5→E9.5 pseudo-holdout：

- coupling/mass/decoder 使用同一流程；
- 比较 parent、L1、L2 的 DES/DCS/MMD/CSS；
- 只用于固定解析 alpha 与检查反号/共变破坏；
- 不据此做多轮调参。

## 正式生成

对 board registry 中每个 T1 target：

- 每 lane 一次完整生成；
- 一次 contract；
- 一次 full-panel local scorer；
- 写出 state mass、mean delta、residual 贡献拆分。

## Protected checks

- gene order/normalisation；
- parent residual 的可追踪性；
- state mass 总和；
- 小 state cap/shrinkage；
- L1/L2 只在 decoder 上不同；
- P1 未被偷偷扩展；
- candidate cell count 满足 contract。

## 输出与停止

每 board 两条 candidate H5AD，加：

```text
intermediates/coupling.npz
intermediates/state_transition.tsv
intermediates/state_mass.tsv
intermediates/state_gene_delta.npz
intermediates/sampling_plan.tsv
metrics/component_ablation.json
```

完成后按 decision rules 结论并停止。
