# B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR

## 定位

这是对旧 T3 路线“忽略目标阶段正常发育方向”的修复，不是新神经架构。

旧方法主要从 WT 相关性、GRN 或训练 KO 猜 Gata4 响应，却没有把 E8.75 的正常发育时间方向作为条件。这里测试一个低容量假设：

> 条件 KO 的部分表达效应表现为 Mesp1/cardiac lineage 的成熟延迟。

这只是可证伪 baseline，不是机制结论。

## 输入

只使用官方可见 WT：

```text
E8.25 heart
E8.75 heart
E9.5 heart
```

以及：

- P0 exact WT identity；
- frozen Mesp1 lineage probability；
- T3 500-gene panel。

不使用任何 Gata4 KO 真值、近邻外部 held-out数据或服务器分数。

## temporal direction

对可稳定匹配的 state 计算 per-day pseudobulk delta：

\[
d^{(1)}_s = \frac{\mu_{E8.75,s}-\mu_{E8.25,s}}{0.5}
\]

\[
d^{(2)}_s = \frac{\mu_{E9.5,s}-\mu_{E8.75,s}}{0.75}
\]

稳健方向：

- 两段同号：取幅度较小者或中位数；
- 两段异号：置零；
- 低表达/低样本 state-gene：置零；
- 不共享 state：使用强收缩 global direction 或零，规则预先固定；
- Gata4/Gata6 从 temporal program 中排除，最后由 genotype transform 单独处理。

developmental delay residual：

\[
\Delta^{delay}_{s,g}=-\alpha d_{s,g}
\]

只作用于 lineage probability \(p\)：

\[
X'=X_{WT}+p\Delta^{delay}
\]

然后应用与 T3-R1 L3 相同的 genotype transform。

## 两条 lane

### L1_DELAY025

\[
\alpha=0.25
\]

### L2_DELAY050

\[
\alpha=0.50
\]

这里 alpha 的单位是 day-equivalent，不是服务器校准值。

## caps

- 每 gene/state delta ≤ 0.25 × E8.75 state robust SD；
- 非负 clip；
- clipping 行/基因完整记录；
- 非 lineage cell保持 WT；
- coordinates exact；
- 不改 composition；
- 不加 noise；
- 不使用旧 signed prior。

## 诊断

在正常 WT ladder上做 source-only sanity：

- direction 是否能把较晚 stage 拉回较早 stage；
- shared-state coverage；
- temporal sign consistency；
- library / variance；
- pseudobulk change；
- modified gene fraction；
- lineage selectivity。

这不是 Gata4 score preview。

## 输出

```text
candidates/T3_gata4/L1_DELAY025/submission.h5ad
candidates/T3_gata4/L2_DELAY050/submission.h5ad
intermediates/temporal_direction.tsv
intermediates/state_mapping.tsv
metrics/temporal_consistency.tsv
```

## 决策

- 若两个 lane 都不胜 exact floor：`ARCHITECTURE_RESET_REQUIRED` for T3；
- 不追加反方向、第三 alpha 或旧 prior 组合；
- validation 成功也不自动宣称 β-catenin 泛化。
