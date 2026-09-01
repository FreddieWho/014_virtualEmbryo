# B2-T3-A2 · 通用 Perturb-seq 响应形状预训练（条件 atom）

## 激活条件

只有同时满足以下条件才可运行：

1. B2-T3-A1 至少一个 lane 形成 submit-ready candidate；
2. A1 的 source-only direction kill test 不为负；
3. generic Perturb-seq 使用获得组织者书面许可，或项目已有等价书面确认；
4. 所有 source 与 perturbation blacklist 审计通过。

否则标记 `BLOCKED_COMPLIANCE`，不得下载大数据。

## 唯一目标

学习 perturbation 的 **稀疏度、标准化幅度、cell-level heterogeneity 与 covariance preservation**，用于校准 A1 已确定的 sign/rank。不得改变 Gata4/Gata6 的方向与 gene set 核心排序。

## 数据选择

从 Replogle 2022 / scPerturb 选择最多 3 个数据集：

- genetic CRISPR/CRISPRi；
- transcriptomic single-cell readout；
- 非 embryonic mouse；
- matched control 明确；
- license 明确；
- 总下载优先控制在 20 GB 内；
- 所有 blacklist perturbations 删除。

优先下载 normalized pseudobulk 与必要的小型 single-cell subset，不下载 159 GB 全量文件。

## 禁止学习

- target-specific direction；
- GATA4/GATA6/CTNNB1/MESP1 或 phenocopy 响应；
- embryonic stage trajectory；
- target cell-type identity。

## 学习对象

对每个安全 perturbation 估计：

- 响应 gene fraction；
- `|delta| / robust_SD_control` 分布；
- high-confidence direct vs indirect target 的幅度衰减；
- cell-level residual inflation/deflation；
- covariance-preserving residual resampling参数。

只训练小型统计 calibration model，不训练大型 foundation model。

## 两个 lane

### L1_ROBUST_STANDARDIZED_SCALE

- 使用安全 perturbations 的 median standardized magnitude；
- A1 sign/gene set 固定；
- WT residual replay；
- global strong shrinkage。

### L2_CONFIDENCE_CALIBRATED_SCALE

- 幅度是 A1 confidence、WT expression、network directness 的单调函数；
- 函数在 generic perturb data 上拟合一次；
- 预测范围裁剪到 L1 经验分布的 5%–95%；
- 不允许 response direction 作为训练标签进入 target-specific mapping。

## 输出

1–2 个 T3 Gata4 submit-ready candidate，parent 为 A1 winner。坐标保持 WT。

## 停止

每 lane 一次完整生成和 local score。不得根据 Gata4 server score回调 amplitude model。
