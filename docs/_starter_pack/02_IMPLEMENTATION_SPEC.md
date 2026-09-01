# Implementation Spec — First Evidence Loop

## 2026-08-22 closure amendment

本规范中的完整 manifest、pseudo-holdout、controls 和 B1/B2 条目保留为可复用的研究扩展。竞赛基线 starter_pack 已因首次服务器 scored submission 关闭；这些扩展不再是后续 leaderboard 提交的前置门槛。后续候选必须保留官方 board contract、格式/数值/空间检查、来源登记和 SHA256。关闭证据与未完成扩展见 [`reports/STARTER_PACK_CLOSURE.md`](../../reports/STARTER_PACK_CLOSURE.md)。

## 1. 目的

这份 SPEC 将第一轮工作定义为一个可审计的软件/实验系统，而不是一次模型训练。首要目标是让后续任何“更好的模型”都可以被可靠地比较。

## 2. 核心设计原则

### 2.1 先建立 measurement system，再优化 model

若 scorer、split、schema、normalization、cell count handling 尚未锁定，任何模型提升都不可解释。

### 2.2 任务分开建模

T1、T2、T3 的科学难点不同：

- T1：新状态出现 + 远期 population extrapolation；
- T2：expression / composition / geometry / neighborhood 的联合生成；
- T3：单 observed KO 条件下的 cross-gene perturbation generalization。

本轮只让 T2 进入自研，因为它有最可用的公开阶段结构来建立本地 holdout。

### 2.3 分数必须可归因

任何模型模块增加后，应能回答：改善来自 expression、composition、shape 还是 neighborhood，而不是只观察 total score。

## 3. 推荐仓库结构

```text
virtual-embryo/
├── README.md
├── compliance/
│   ├── external_sources.tsv
│   └── RULE_SNAPSHOT.md
├── configs/
│   ├── data.yaml
│   ├── task_contracts.yaml
│   ├── pseudo_holdouts.yaml
│   ├── t1/
│   ├── t2/
│   └── t3/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── pseudo_targets/
│   └── MANIFEST.tsv
├── src/
│   ├── common/
│   │   ├── io.py
│   │   ├── validate.py
│   │   ├── hashes.py
│   │   ├── seeds.py
│   │   └── registry.py
│   ├── t1/
│   ├── t2/
│   └── t3/
├── baselines/
│   ├── t1/
│   ├── t2/
│   └── t3/
├── evaluation/
│   ├── run_scorer.py
│   ├── diagnostics.py
│   └── adversarial_controls.py
├── experiments/
│   ├── registry.csv
│   └── runs/
├── submissions/
├── tests/
└── reports/
```

## 4. Data manifest

每个输入文件至少记录：

- `path`
- `sha256`
- `bytes`
- `n_obs`
- `n_vars`
- `x_dtype`
- `x_min`
- `x_max`
- `x_nonnegative`
- `var_names_hash`
- `obs_keys`
- `obsm_keys`
- `uns_keys`
- `stage`
- `scope`（heart / embryo）
- `condition`
- `replicate_id`（存在则填）
- `spatial_shape`

不要修改 raw 数据；任何 normalization/reindexing 都进入 processed 并记录 parent hash。

## 5. Submission contracts

### T1

当前官网明确：

- whole transcriptome；
- 32,285 genes；
- log1p-normalised / non-negative；
- 输出 `.X` cells × genes；
- released gene order；
- 不要求 spatial；
- submission celltype 不参与评分。

### T2/T3

当前官网明确：

- 500-gene MERFISH panel；
- `.X` non-negative；
- `obsm["spatial_3D"]` 至少前三列为有限值；
- celltype 由 organizer frozen probe 统一预测；
- coordinate frame 不需要与 target 绝对注册。

starter kit 发布后把实际 schema 解析成机器可读 contract，并覆盖本包模板中的未知项（例如精确最小 cell count、uns 字段要求、dtype/压缩限制等）。

## 6. Baseline definitions

### 6.1 T1 copy_last

目标 stage 预测为最后可见阶段 E9.5 的细胞分布。主要作用：floor / schema / pipeline sanity。

### 6.2 T1 pseudobulk_shift

计算 E8.5→E9.5 pseudobulk delta，并把同一 delta 加到 E9.5 的细胞表达；负值按官方 baseline 的逻辑处理。不得凭记忆决定 clip 细节，starter kit 发布后以源码为准。

### 6.3 T2 copy_last

对目标 setting 使用最近/官方定义参考 stage 的 expression + geometry。必须严格复现 starter kit 的 target-specific reference 选择。

### 6.4 T2 pseudobulk_shift

只改变 expression，geometry 保持 reference。其价值是拆开 expression gain 与 geometry gain。

### 6.5 T3 wt_identity

目标 KO 直接复制 matched WT。这是明确的 perturbation floor。

### 6.6 T3 shift_transfer

把 Mab21l2 training KO 的 WT→KO pseudobulk response 迁移到 held-out gene 的 matched WT。预计会暴露 response-direction mismatch，因此主要是 reference，不应被当作可靠机制模型。

## 7. Pseudo-holdout 设计

### T2 heart — H1 interpolation proxy (HIGH/MEDIUM)

Public stages: E8.25, E8.75, E9.5。

Hold out E8.75；用 E8.25 + E9.5 建模 E8.75。

检验：

- composition interpolation；
- expression interpolation；
- geometry interpolation；
- neighborhood preservation。

局限：官方 validation interpolation target 是 E8.5，间距不同。

### T2 heart — H2 extrapolation proxy (MEDIUM)

Hold out E9.5；只用 E8.25 + E8.75 预测 E9.5。

检验短期 forward extrapolation 与 growth。不能证明 E10.5/E12.5 长期 extrapolation。

### T2 embryo — E1 interpolation proxy (MEDIUM)

Hold out E7.25；使用 E6.75 + E8.0 预测。

检验 whole-embryo interpolation、composition 与形态组织。官方 validation/test 更靠近 E8.0，因此阶段动力学并不等价。

### T2 replicate holdout (HIGH for variance ceiling, if available)

若同 stage 有多个 biological replicates：留一 embryo，其他 replicate 作为参考。用于估计 biological variability / split-half ceiling，而不是时间泛化。

### T1 sanity holdout (LOW)

若没有合规外部 stage：hold out E9.5，仅用 E8.5（E7.75 只作 background）。只用于调通 distribution generation/scoring，不能证明 E10.5/E12.5 外推能力。

若未来引入合规 external stages，再设计真正 stage ladder validation；必须先通过 compliance audit。

### T3 replicate holdout (LOW–MEDIUM, conditional)

若 Mab21l2 KO 有独立 biological replicates：留一 KO embryo；其余 KO + matched WT 训练/校准。可检验 noise / amplitude / composition stability，但**不能**证明跨基因泛化。

若无独立 replicate，不构造伪“跨基因验证”。

## 8. Adversarial controls

### C1 Mean-cell collapse

所有 cell 使用同一个 pseudobulk/mean vector，cell count 保持合理。预期 distribution/covariance 指标明显下降。

### C2 Scale attack

`X' = aX`，测试 a∈{0.5, 1.5, 2.0} 并保持非负。用于确认 DE/change scorer 不被纯 scale 攻击欺骗。

### C3 Random geometry

T2 expression 保留真实/合理参考，coordinates 替换为随机 cube/sphere。预期 shape/neighborhood 明显下降。

### C4 Geometry distortion

对真实 point cloud 做 flatten：z×0.05；stretch：x×3。用于检验 shape/growth group。

### C5 T3 random-direction response

保留 response magnitude 分布，但对 gene response 符号随机化。预期 response direction 明显下降。

## 9. T2-B1：Count + composition

### 9.1 total cell count

至少比较：

- last count；
- linear count vs stage-time；
- log-linear / exponential count vs stage-time。

只在 pseudo-holdout 中选择，不基于 leaderboard 选择。

### 9.2 composition

对于 cell-state proportion p_c(t)：

首选简单、可解释方案：

- additive smoothing；
- centered log-ratio / additive log-ratio transform；
- linear interpolation/extrapolation in transformed space；
- inverse transform + renormalization。

必须处理 zero proportion：固定 pseudocount 并记录。

### 9.3 resampling

从 reference stages 的真实单细胞中按预测 composition 采样，避免直接生成均值细胞。

先保持 expression 和 geometry 为真实 reference structure；B1 的目的就是隔离 population-size / composition gain。

## 10. T2-B2：State-specific expression transport

优先顺序：

1. state-specific pseudobulk shift；
2. residual-preserving shift；
3. PCA latent linear transport；
4. small-scale OT barycentric mapping。

只有 1–3 在多个伪留出上稳定后，才考虑 OT。

### Residual-preserving shift

对于状态 c 的 reference cell：

`x_i = μ_c,ref + ε_i`

预测：

`x_i,pred = μ_c,pred + s * ε_i`

其中 s 首轮默认 1；仅在 covariance 明显失真时测试 shrink/expand。负值处理必须符合 log-normalized non-negative contract。

这一结构的目的：改变群体中心但保留真实异质性，避免 mode collapse。

## 11. Metrics reporting

每次比较不得只报 composite。至少保存：

- composite；
- 每个官方 metric；
- metric group；
- seed mean ± SD；
- predicted n_cells；
- composition divergence；
- per-gene variance agreement；
- covariance diagnostic；
- spatial radius / PCA-axis length / kNN distance diagnostic（T2）；
- runtime / peak RAM / peak VRAM。

## 12. Model selection rule

候选模型 A 相对 baseline B 只有满足以下条件才称为“pass”：

1. 中/高 fidelity pseudo-holdout 至少一个主要目标改善；
2. 另一个独立 split 不出现明显反向崩溃；
3. 3-seed mean improvement > 1 seed SD（最低门槛，不是统计显著性证明）；
4. 不是通过违反生物学约束或 submission contract 获得；
5. 没有明显 mode collapse / geometry degeneration。

若只在一个 LOW fidelity split 提升，状态为 `INCONCLUSIVE`。

## 13. Experiment registry

每个实验必须先注册：

- hypothesis；
- parent run；
- changed variable；
- split；
- expected metric group；
- failure criterion。

避免一次实验同时改 5 个因素。

## 14. 本轮输出图

只需生成诊断图，不追求论文美化：

T2：

- true vs predicted cell-state proportions；
- true vs predicted pseudobulk change；
- 3D point cloud quick view；
- principal-axis lengths；
- kNN-distance distributions；
- per-gene variance scatter；
- seed stability plot。

T1/T3：只需 baseline/pseudo-holdout 诊断，不做复杂可视化。

## 15. 下一轮候选但本轮禁止自动执行

只有 FIRST_CYCLE_REPORT 支持时，下一轮才考虑：

- T2-B3 geometry growth model；
- T2-B4 state-specific point-cloud transport；
- T2-B5 expression-position coupling；
- T1 external stage ladder + unbalanced OT / birth-death dynamics；
- T3 GRN / literature-conditioned perturbation direction prior；
- flow matching / diffusion / ODE。

本轮的价值是确定哪个瓶颈真实存在，而不是提前把所有模型都实现一遍。
