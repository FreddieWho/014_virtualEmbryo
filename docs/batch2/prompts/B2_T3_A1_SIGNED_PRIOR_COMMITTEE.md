# B2-T3-A1 · 可审计的 Gata4/Gata6 有符号先验委员会

## 唯一目标

在 `wt_identity` 上增加 **高置信、Mesp1-lineage 特异、Gata4/Gata6 条件一致** 的稀疏响应，主要优化 T3 的 DES/DCS，并保护 MMD/CSS 与 WT 背景。

本 atom 不追求精确 PSS，不训练空间模型，不复用 Batch 1 的 WT Spearman fallback，也不借用 Mab21l2 的绝对效应预算。

## Parent

从 registry 解析当前 `T3:gata4` 的 canonical `wt_identity`。表达与坐标只读复制后再做稀疏修改。

## 允许输入

- 官方 WT E8.75 3D MERFISH；
- sanitized E-MTAB-6967 / E-MTAB-11763 WT developmental scRNA；
- sanitized GSE52123 E12.5 WT GATA4 ChIP；
- Reactome、GO；
- 现场训练的 CellOracle 与 scTenifoldKnk；
- CollecTRI/OmniPath 仅按 P0 审计结果作为可追溯 secondary vote。

## 关键生物条件

目标不是纯 Gata4 全胚胎 KO，而是：

```text
Mesp1-Cre; Gata4 F/F; Gata6 F/+ @ E8.75
```

因此必须同时处理：

- Mesp1 lineage gate；
- Gata4 双等位缺失；
- Gata6 单等位剂量下降；
- 非 lineage 细胞保持 WT。

## 共用施工

### 1. Lineage/state gate

1. 用官方 celltype、外部 WT atlas label 与 mesoderm/cardiac gene programs 建立 harmonized state crosswalk。
2. 为每个官方 WT 细胞计算 `p_mesp1_lineage ∈ [0,1]`。
3. 只允许 `p >= 0.5` 的细胞发生响应，实际 residual 乘以 `p`。
4. 不硬编码一个未经审计的 celltype 列表；在结果中输出每个 state 的 lineage probability 与证据。

### 2. Target directness

1. 将 GSE52123 GATA4 peaks 映射到 mouse genes：promoter ±5 kb 为高置信 direct；更远 peak 只在有公开 enhancer-gene link 时使用。
2. ChIP 只增加 directness/confidence，不能决定激活还是抑制。
3. 对 500-gene panel 输出 `directness_score` 与 peak evidence。

### 3. 两个独立 WT-only sign model

- **CellOracle vote**：在 sanitized full-transcriptome WT context 中构建 state-specific GRN，再模拟 Gata4/Gata6 suppression；
- **scTenifoldKnk vote**：从同一 WT context 独立构建 scGRN，分别对 Gata4/Gata6 做 virtual KO。

两个模型分别输出每个 `state × gene` 的 sign、rank 与 confidence。不得把模型输出先平均再声称“两票一致”。

### 4. Knowledge vote

- Reactome/GO：只定义 cardiac/mesoderm/pathway module 和不合理响应过滤；
- CollecTRI：仅使用 P0 判定可审计的 edge；
- OmniPath：仅用于有向 signaling path 与后续 β-catenin-compatible 接口；
- unresolved provenance edge 在 strict lane 中为 0 票。

### 5. Consensus

对每个 `state × gene`：

- CellOracle 与 scTenifold 同号是最低条件；
- direct ChIP 或可审计 signed knowledge 至少满足一项；
- 冲突或只有一票：residual = 0；
- confidence 由独立证据族数量和 rank 决定，不由服务器分数决定。

KO response sign 的方向是“删掉 TF 后的基因变化”，不是 TF-target edge 本身的符号；实现中显式检查符号翻转。

## 两个预声明 lane

### L1_STRICT_WT_DIRECT

- 只含 Gata4；
- 必须满足两个 WT-only sign model 同号；
- 必须有 direct ChIP 或可审计 target edge；
- 仅 top confidence genes，最大非零 panel 比例 10%；
- 不使用 unresolved CollecTRI/OmniPath edge。

### L2_GATA4_GATA6_CONDITION_AWARE

- 包含 L1 Gata4 response；
- 加入 Gata6 virtual heterozygous component，幅度乘 0.5；
- GATA6 必须同样通过两个 WT-only sign vote；
- Gata4 与 Gata6 对同一 gene 冲突时相互抵消或置零，不强投票；
- 最大非零 panel 比例 15%。

若 optional knowledge source 未通过合规，L2 仍可只用 WT-only Gata6 vote；不得因此停止 L1。

## 幅度

A1 只给保守幅度：

```text
|delta(state,gene)| = confidence × directness_weight × 0.15 × robust_SD_WT(state,gene)
```

- indirect but allowed evidence：系数减半；
- Gata6 F/+：再乘 0.5；
- 每 gene delta 不超过该 state WT 1%–99% 区间宽度的 10%；
- 不从 Mab21l2 复制绝对 delta；
- 不用网格搜索。

### KO gene 本身

- lineage 内 Gata4 设为 0；lineage 外保持 WT；
- lineage 内 Gata6 相对 WT 向 50% 剂量收缩；
- 若 panel/normalisation 使“50% expression”需在原始尺度处理，先反变换再 log1p；不得直接把 log 值乘 0.5。

## 群体保护

- 细胞、坐标、cell order 与 WT parent 保持；
- 仅修改被选中的 gene/cell；
- 非响应 gene bitwise 保持 parent；
- 非负截断后记录 clipping 数量；
- 不添加独立逐基因噪声。

## 一次 source-only kill test

使用已公开 Mab21l2 KO 作为一次性 sanity check：

1. 不用 KO 数据训练 prior；
2. 用同一 WT-only sign pipeline预测 Mab21l2；
3. 预测完成后仅比较 DCS/DES 与 identity；
4. 不调 top-k、符号或 source；
5. 若 DCS <= 0，则 final Gata4 candidate 只保留满足“三证据族一致”的 ultra-strict subset，并在 RESULT 中标记高风险。

## 输出

至少 L1，一个合规 L2 时再输出 L2：

```text
artifacts/atomic_batch2/B2-T3-A1/submissions/T3_gata4/<lane>/prediction.h5ad
```

同时输出：

- `prior_votes.tsv`：state × gene × evidence family；
- `response_program.tsv`：最终 sign、confidence、amplitude；
- `lineage_gate.tsv`；
- local scorer 与 protected checks；
- 完整 source disclosure。

## 停止

候选通过 contract 并完成一次 local score 后停止。不得因为分数一般而增加第三种 GRN、扩大 top-k 或调幅度。
