# B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE

## 唯一目标

补齐 T2 两个插值 board 长期缺失的表达与状态组成桥，同时冻结已经验证的 geometry。

T2 当前主要提分来自 scale / pycpd / FGW，但表达变化和群体分布约占一半评分。早期 `expression_midpoint_norm` 已有小幅正信号，却没有形成完整 board-specific bridge。

## Boards

### Embryo

```text
left = E7.25
target = E7.5
right = E8.0
lambda = 1/3
```

### Heart

```text
left = E8.25
target = E8.5
right = E8.75
lambda = 1/2
```

## Parent

- embryo：60.1 scale winner；
- heart：当前 57.3 parent 的 geometry/assignment；
- 执行时以 registry current parent 为准。

所有坐标和 geometry transform 冻结。

## 状态匹配

优先：

1. exact shared celltype；
2. frozen crosswalk；
3. global fallback。

不得：

- 新聚类；
- 用 hidden target；
- 用外部 held-out stage；
- 强行匹配低置信 state；
- 使用 submitted celltype 作为官方 scorer 标签的假设。

## L1_MEAN_BRIDGE

对每个 shared state：

\[
\mu_t=(1-\lambda)\mu_L+\lambda\mu_R
\]

构造：

- carrier population 来自当前 parent；
- 将 parent state mean 移到 interpolated mean；
- 保留 parent 的完整 residual vector；
- rowwise normalization 与 parent一致；
- unmatched states 使用全局 mean bridge 的强收缩或保持 parent，规则预先固定。

不改变 state mass。

## L2_MEAN_MASS_BRIDGE

在 L1 基础上：

\[
p_t=(1-\lambda)p_L+\lambda p_R
\]

- 对 shared states 插值份额；
- endpoint-only states 使用 50% shrink 到近端份额；
- largest-remainder deterministic allocation；
- 从 parent residual bank 重采样；
- n_obs 保持 parent；
- 不生成新 state。

## Geometry / assignment

- embryo current scale/coordinates exact；
- heart current coordinates exact；
- heart assignment mapping exact；
- 表达值变换后不重新跑 FGW；
- 若后续需要 composition，另起新 locked run，不在本 task 顺手组合。

## 诊断

至少：

- endpoint reconstruction；
- leave-one-observed-stage holdout；
- per-state mean error；
- composition error；
- DE direction；
- MMD/variogram；
- library/variance；
- NFS mirror（确认 expression 修改没有产生灾难）。

proxy 不作绝对 gate。

## 输出

每 board 两个：

```text
candidates/T2_embryo_val_interp/L1_MEAN_BRIDGE/submission.h5ad
candidates/T2_embryo_val_interp/L2_MEAN_MASS_BRIDGE/submission.h5ad
candidates/T2_heart_val_interp/L1_MEAN_BRIDGE/submission.h5ad
candidates/T2_heart_val_interp/L2_MEAN_MASS_BRIDGE/submission.h5ad
```

## Protected checks

- coordinates bitwise exact；
- n_obs exact；
- panel exact；
- finite/nonnegative；
- no new external data；
- row ledger；
- state mass only L2 changes；
- no geometry rescaling；
- no additional pairing optimization。

完成后停止。
