# B4-T3-R1-GENOTYPE-ONLY-ABLATION

## 唯一目标

在旧 signed-prior v0006/7 已失败后，去掉全部推测下游 residual，单独检验三个确定或近确定条件：

1. Gata4 被敲除；
2. 作用受 Mesp1 lineage 限制；
3. Gata6 为 F/+ dosage condition。

这不是复活旧 prior，而是确认旧候选是否因为错误下游方向压过了已知 genotype signal。

## 条件身份预检

在生成 L3 前，必须从当前官方 starter metadata / task contract / locked project snapshot 中确认 validation 条件确实包含 `Gata6 F/+`。当前公开任务页只以 “Gata4 KO” 简称该 board，不能仅凭旧报告假定复合基因型。

- 若本地权威 metadata 明确确认：执行 L3；
- 若缺失、模糊或与当前官方材料冲突：L3 标记 `BLOCKED_CONDITION_NOT_CONFIRMED`，只生成 L1/L2；
- 不得为凑足三条 lane 临时替换成别的 dosage。

## Parent

P0 生成的 exact `wt_identity` candidate。  
若 floor parity 尚未确认，也使用其 H5AD，但在 RESULT 中标为 provisional。

复用已有 frozen `p_mesp1_lineage`，不得重新训练 prior。

## 坐标

所有 lane：

- coordinates bitwise exact；
- cell order exact；
- n_obs exact；
- 不优化 T3 geometry；
- 只修改声明 gene。

## 三条 lane

### L1_GATA4_ZERO_ALL

- 所有细胞 `Gata4=0`；
- 其他 499 genes bitwise parent；
- 这是 target-fact upper-isolation，不声称 Cre 全胚胎作用正确。

### L2_GATA4_ZERO_HARD_LINEAGE

- `p_mesp1_lineage >= 0.5`：Gata4=0；
- 其他细胞完全 parent；
- 不修改 Gata6；
- 不修改下游 gene。

### L3_GATA4_ZERO_SOFT_GATA6

在 raw-like scale 操作后回 log1p：

\[
Gata4' = Gata4 \times (1-p)
\]

\[
Gata6' = Gata6 \times (1-0.5p)
\]

其中 \(p=p_{\text{mesp1 lineage}}\)。

要求：

- 证明 transform domain 正确；
- 不直接把 log value 乘 0.5；
- 其他 498 genes bitwise parent；
- 输出每 state / p-bin 的修改量。

## 不允许

- 使用 v0006/7 下游 top-k；
- 使用 CellOracle / scTenifold sign；
- 使用 Mab21l2 direction；
- 加噪；
- 改 composition；
- 重新采样细胞；
- 调 lineage threshold；
- 增加第四 lane。

## 本地诊断

本地 target-free诊断只验证：

- target gene 实际被改变；
- 非 target gene exact；
- library shift 极小；
- variance 不 collapse；
- lineage范围；
- no negative/NaN；
- coordinates exact。

由于没有 Gata4 truth，不能用 local score判断方向正确。

## 输出

```text
candidates/T3_gata4/L1_GATA4_ZERO_ALL/submission.h5ad
candidates/T3_gata4/L2_GATA4_ZERO_HARD_LINEAGE/submission.h5ad
candidates/T3_gata4/L3_GATA4_ZERO_SOFT_GATA6/submission.h5ad
```

## 服务器解释

- 若任一 lane > exact floor：旧下游 residual 很可能是主要伤害源；
- 若 L2/L3 > L1：lineage / dosage 编码有价值；
- 若全部 ≤ floor：known genotype facts alone 不够，T3 必须转大型 gene-conditioned architecture。

服务器回来前不得提前下结论。
