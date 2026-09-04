# B4-T1-R1-CONSERVATIVE-FAMILY

## 唯一目标

在不引入新 backbone 的情况下，拆解 T1 当前 best `strict pseudobulk shift`：

1. 校准 shift 强度；
2. 测试 population mixture；
3. 只移植 Batch 3 中有独立正信号的 state-mass forecast；
4. 不复用已被服务器否决的 moscot expression decoder。

## Parent

必须从 P0 的 `current_parent_lock.yaml` 解析：

- exact-floor candidate；
- T1 current best v0004 strict shift；
- frozen moscot state-mass artifact；
- T1-PRE harmonized state crosswalk。

若 hash 不一致：`BLOCKED_INPUT`。

## 不允许

- 重新拟合 moscot；
- 运行 MIOFlow；
- 重新聚类；
- 新下载外部数据；
- 创建新 state；
- 使用 raw state-specific moscot delta；
- 使用 scDesign3 decoder；
- 改 gene panel；
- 独立逐基因加噪；
- 根据服务器分数选择 amplitude。

## 共用 primitive

严格 per-celltype shift：

\[
\Delta_c = \mu_{E9.5,c} - \mu_{E8.5,c}
\]

- shared celltype：使用自身 delta；
- E9.5-only type：delta=0；
- clip at zero；
- 不做 composition extrapolation；
- residual 使用真实 E9.5 完整行向量；
- T1 不携带 coordinates。

## 四条预声明 lane

### L1_DAMP050

\[
X'=X_{E9.5}+0.5\Delta_c
\]

目的：判断 v0004 是否 overshoot。

### L2_POPMIX050

不是逐基因平均。构造 5,118-cell population：

```text
50% exact copy-last cells
50% strict-shift cells
```

要求：

- 两个 pool 都从同一 E9.5 source-row universe 构建；
- 稳定 hash/seed 选择；
- 保留完整行 residual；
- 不重复同一 source row，除非官方 contract 迫使且需披露；
- 输出 composition 与 parent 的差异。

目的：在 population level 平衡分布保护和变化方向。

### L3_MASSGRAFT025

表达使用 v0004 strict shift。状态份额：

\[
p'=0.75p_{E9.5}+0.25p_{\text{moscot}}
\]

- 只使用 frozen moscot mass；
- unresolved state 回退 E9.5 share；
- 重新归一化；
- 在 E9.5 carrier/residual bank 中按目标份额采样；
- 不使用 moscot expression delta。

### L4_MASSGRAFT050

同 L3，但：

\[
p'=0.50p_{E9.5}+0.50p_{\text{moscot}}
\]

目的：判断 mass 正信号是否足够强。

## Source-only 诊断

至少：

- leave-E9.5-out 或现有冻结 pseudo-holdout；
- full-panel scorer；
- de_score / direction；
- MMD / variogram；
- composition；
- variance / library size；
- state-mass error；
- clipping fraction。

本地结果只用于：

- 检查 lane 是否实际不同；
- 排除灾难；
- 给上传顺序。

只要 contract 通过且没有明显退化（例如 collapse、极端 library shift、>20% cell rows 异常 clipping），全部保留供服务器探针。

## Protected checks

- 32,285 gene order exact；
- n_obs 按 board；
- finite/nonnegative；
- no `obsm`；
- residual rows可追溯；
- no target data；
- lane only changes declared dimensions；
- determinism；
- candidate hash。

## 输出

四个 H5AD：

```text
candidates/T1_val/L1_DAMP050/submission.h5ad
candidates/T1_val/L2_POPMIX050/submission.h5ad
candidates/T1_val/L3_MASSGRAFT025/submission.h5ad
candidates/T1_val/L4_MASSGRAFT050/submission.h5ad
```

同时输出：

```text
intermediates/state_mass_plan.tsv
intermediates/source_row_ledger.tsv
metrics/lane_comparison.tsv
CANDIDATE_HANDOFF.md
RESULT.md
```

## 决策

run 内只给推荐上传顺序：

- 不因 local proxy 小幅下降删除 lane；
- catastrophic 才 `REJECT_IMPLEMENTATION`；
- 服务器回来前不能 `PROMOTE_PARENT`。

完成后停止。
