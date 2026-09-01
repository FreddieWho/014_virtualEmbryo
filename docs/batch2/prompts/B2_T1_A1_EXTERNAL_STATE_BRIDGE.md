# B2-T1-A1 · 外部状态支持桥与允许晚期程序

## 唯一目标

补足 T1 官方 E8.5/E9.5 无法识别的状态词表与晚期程序，同时保留当前 T1 best 的全转录组背景、残差和基因共变。主要优化 P1–P4，并为后续 temporal operator 建立统一 state vocabulary。

## Parent

当前 canonical `v0004_strict_pseudobulk_shift`。所有 candidate 从该 parent 生成，而不是从 Batch 1 A3 旧 parent 生成。

## 允许输入

- 官方 E7.75（unused）、E8.5、E9.5；
- sanitized E-MTAB-6967 WT E6.5–E8.5；
- sanitized E-MTAB-11763 WT E8.5–E9.5；
- sanitized GSE193346 WT：仅 E9.5 与 E14.5+；
- GO/Reactome state/program annotations。

禁止：任何 E10.5–E13.5 external cell、任何 mutant/chimera、任何在保护细胞上预训练的表示。

## 共用施工

### 1. State vocabulary

1. 在基因交集上构建 48–64 个非负 gene programs；使用 state/sample pseudobulk，而不是把全部百万细胞塞进统一深模型。
2. 将所有外部 label 映射为：`lineage → state family → fine state`。
3. 使用 marker/program cosine + mutual nearest state centroid 建 crosswalk。
4. 官方 E9.5 是目标 domain；外部 E9.5 只用于学习每个 state 的 domain offset。
5. 保存 mapping confidence；低置信 state 进入 `UNRESOLVED`，不创建新状态。

### 2. Composition

外部数据的 dissection 与组织范围不同，禁止直接采用绝对比例。状态质量只由：

- 官方 E8.5→E9.5 的变化；
- external lineage 是否持续/分支；
- 小群体 shrinkage；
- 固定 mass cap

共同决定。

### 3. Decoder

- 以官方 E9.5 parent cells 为基础；
- state/program delta 加到完整 cell row；
- residual vector 保持，不逐 gene 采独立噪声；
- external 不相交 genes 由 parent 保持；
- 最终仍是 32,285 genes、官方顺序。

## 两个 lane

### L1_HARMONIZED_SUPPORT

目的：仅验证外部 early atlas 能否修复状态词表和质量，不创建 late-only state。

1. 使用统一 vocabulary 对官方 E8.5/E9.5 重映射；
2. 用外部 E6.5–E9.5 只判断 lineage persistence/branch support；
3. 重新分配 parent cells 的 state mass；
4. 总细胞数保持 parent；
5. state 内表达保持 parent distribution，只有必要的 state-specific parent delta。

### L2_LATE_PROGRAM_BIRTH

目的：利用规则明确允许的 E14.5+ 数据提供晚期 program direction，但只做保守一步外推。

1. 从 GSE193346 WT E14.5/E16.5（可加后续 stage）提取 cardiac state/program；
2. 一个 late program 只有在两个 strain，或至少两个允许 late stage 中重复出现，才可 admission；
3. 将 late state 映射到 external E9.5 parent lineage；
4. `late_delta = late_centroid - external_E9.5_parent_centroid`；
5. 转到官方 domain 后，E10.5 只施加时间比例 `1 day / 5 days = 0.2`；
6. 单 gene delta 再截断到官方 E8.5→E9.5 state-specific delta 的 95% 范围；
7. late/open-set program 总质量 <=10%，每个 program <=3%；
8. 未通过 lineage/admission 的 late state 不生成。

这里的“新状态”是 parent cell 加入有限新 program 后的 prototype，不是直接复制 E14.5 细胞。

## 一次 pseudo-holdout

预测官方 E9.5：

- 输入官方 E8.5；
- 外部数据只允许 `<=E8.5`；
- 运行同一 state vocabulary/decoder；
- 用官方本地 full-panel scorer 一次比较 parent 与两个 lane 的对应伪预测；
- 不据此做网格，只允许解析计算一个 global shrinkage coefficient。

若 full-panel scorer 仍不可运行，必须先修到可以完成一次评分；禁止用简化 proxy 替代后继续宣称通过。

## 输出

两个可提交 T1 E10.5 candidate：

```text
artifacts/atomic_batch2/B2-T1-A1/submissions/T1_val/L1_HARMONIZED_SUPPORT/prediction.h5ad
artifacts/atomic_batch2/B2-T1-A1/submissions/T1_val/L2_LATE_PROGRAM_BIRTH/prediction.h5ad
```

附加：

- `state_vocabulary.tsv`
- `state_crosswalk.tsv`
- `late_program_admission.tsv`
- `mass_plan.tsv`
- source disclosure 与 protected checks。

## 停止

两个 candidate 完整生成并各完成一次 local score 后停止。不加第三个 late-mass cap，不换 encoder，不自动组合 A2。
