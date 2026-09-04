# B4-T2-R1-FGW-ASSIGNMENT-REPAIR

## 唯一目标

修复 Batch 3 heart interpolation FGW 的 soft-to-hard 离散化损失。

已知问题：

- FGW heart candidate 服务器 +0.6；
- 当前 `column_argmax_margin_greedy_v1` 中约 72–73% position 的首选 row 已被抢占；
- 大量 coupling 信息在 greedy 顺延时被丢失。

本 task 不更换 FGW 架构，不改 geometry，不改 expression row set。

## Parent

使用 FGW 前的 frozen heart parent：

- current scale + pycpd geometry；
- 与 v0009 生成时相同的 expression row set；
- 相同 bracket/reference construction；
- 相同 PCA / alpha / loss / cost normalization。

必须锁定 parent 和旧 v0009 mapping。

## 共用求解

沿用现有 POT entropic FGW：

```text
alpha = 0.5
square_loss
uniform marginals
same PCA and reference construction
same seed
```

只允许两个 epsilon。

## 全局双射

替换 greedy：

1. 对每个 position 取 coupling top-64 rows；
2. 构建 sparse bipartite graph；
3. edge cost：

\[
c_{ij}=-\log(T_{ij}+10^{-12})
\]

4. 使用 `scipy.sparse.csgraph.min_weight_full_bipartite_matching` 或等价确定性全局求解；
5. 若 top-64 图不存在 full matching，只允许一次扩展到 top-128；
6. 仍失败则 `BLOCKED_SOLVER`，不得临时换规则；
7. 验证一对一、全覆盖、确定性；
8. 输出旧 greedy 与新 global matching 的：
   - retained coupling mass；
   - total assignment cost；
   - top-1 retention；
   - top-k rank；
   - NFS mirror；
   - local Moran diagnostic。

## 两条 lane

### L1_EPS005_GLOBALMATCH

- epsilon=0.005；
- 复用旧 soft objective；
- 只改变 hard assignment。

这条隔离“离散化修复”。

### L2_EPS002_GLOBALMATCH

- epsilon=0.002；
- 同一 global matching；
- 其余完全相同。

这条测试“计划集中度”。

不得增加第三 epsilon。

## Protected checks

必须 exact：

- expression row multiset；
- coordinate array；
- coordinate order；
- geometry；
- n_obs；
- gene order；
- library-size distribution；
- expression values；
- parent `obs` / `var` contract；
- 只允许 X row permutation；
- no external target data。

## 本地诊断

- old v0009 mapping 作为 frozen control；
- same-target NFS mirror；
- two source-only holdouts；
- plan concentration；
- matching cost。

本地指标只排序。若 new mapping contract-valid，即便 Moran 小幅下降也保留服务器候选。

## 输出

```text
candidates/T2_heart_val_interp/L1_EPS005_GLOBALMATCH/submission.h5ad
candidates/T2_heart_val_interp/L2_EPS002_GLOBALMATCH/submission.h5ad
intermediates/assignment_L1.tsv
intermediates/assignment_L2.tsv
metrics/greedy_vs_global.tsv
```

## 停止

生成两个候选、evidence 和 RESULT 后停止。不跑 embryo，不扫 alpha，不改 reference。
