# B2-T1-A2 · 允许早期数据上的时间转移 operator 预训练

## 前置

必须已有 B2-T1-A1 的：

- `state_vocabulary.tsv`
- `state_crosswalk.tsv`
- sanitized E-MTAB-6967 / E-MTAB-11763
- 可运行的 full-panel local scorer

## 唯一目标

用 E6.5–E9.5 的 6 小时时间序列学习 **lineage/state-specific expression transport**，替代只看官方两个阶段的全局线性 shift。A2 不重新定义新状态；新状态支持由 A1 提供。

## 方法骨架

采用结构化低自由度方案：

```text
allowed early atlas
→ state/program latent
→ adjacent-stage unbalanced OT coupling
→ one-step lineage operator
→ compose 4 steps from E9.5 to E10.5
→ official residual decoder
→ shrink to current parent
```

优先复用 `moscot` / `POT`；不要新写完整 ODE/SDE/flow 框架。

## 训练数据

- E-MTAB-6967 WT E6.5–E8.5；
- E-MTAB-11763 WT E8.5–E9.5；
- 官方 E7.75/E8.5/E9.5 作为 domain calibration；
- GSE193346 E9.5 与 E14.5+ 只允许在 L2 作 terminal program direction；
- external absolute proportions不进入 operator loss。

## Operator

1. 使用 A1 的 gene programs 与 state vocabulary；
2. 每相邻 6h stage 在同 lineage 内求 unbalanced OT；
3. cost = program distance + state mismatch penalty；
4. growth/decay 只影响 state probability，不被解释成绝对胚胎细胞数；
5. 从 coupling 估计每个 lineage 的 one-step program delta 与 branch probability；
6. 对样本稀少 state 向 lineage mean 收缩；
7. apply 时保留官方 E9.5 cell residual。

## 两个 lane

### L1_EARLY_UOT_OPERATOR

- 只用 <=E9.5 数据；
- 将最近若干 6h operator 按 source-only reliability 加权；
- 从 E9.5 连续 compose 4 次到 E10.5；
- 不添加 A1 late-only state；
- state mass 以 A1 L1 support 为基础。

### L2_LATE_CONSTRAINED_OPERATOR

- 相同 early operator；
- 加一个 **方向约束**：结果不得背离 A1 允许的 E14.5+ late program direction；
- terminal anchor 只作用于 program direction，不复制 late cell/比例；
- E10.5 约束权重按 0.2 时间比例固定；
- state support 使用 A1 L2 的 admission 集合。

## Parent shrinkage

每 lane 与当前 T1 best 做：

```text
prediction = parent + alpha * operator_delta
```

`alpha` 仅通过官方 E8.5→E9.5 pseudo-holdout 的 pseudobulk least-squares 一次解析求解，并裁剪到 `[0,1]`。不得网格搜索。

## Decoder

- 在 program latent 中移动均值；
- 从官方 E9.5 同 state residual bank 重放完整 residual vector；
- full-panel 不交集 genes 保持 parent；
- 协方差保护检查必须通过；
- cell count 保持 parent。

## 输出

```text
artifacts/atomic_batch2/B2-T1-A2/submissions/T1_val/L1_EARLY_UOT_OPERATOR/prediction.h5ad
artifacts/atomic_batch2/B2-T1-A2/submissions/T1_val/L2_LATE_CONSTRAINED_OPERATOR/prediction.h5ad
```

附加 coupling/operator summary、解析 alpha、local score 与 disclosure。

## 停止

两 lane 各完成一次候选和评分后停止。不调 OT 正则，不换 latent 维度，不增加 deep dynamics lane。
