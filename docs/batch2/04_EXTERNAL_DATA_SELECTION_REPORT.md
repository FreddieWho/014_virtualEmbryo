# 外部数据选择报告

## 1. 选择原则

外部数据只有在提供官方训练集缺失的信息时才进入 Batch 2：

- T1：时间更密、状态更全、或处于允许的晚期阶段；
- T3：目标基因 directness、signed GRN、谱系 context 或通用 response shape；
- T2：可迁移的形态信息，且必须通过更严格的 stage/board 审计。

“细胞更多”本身不是准入理由。

## 2. T1 核心数据

### E-MTAB-6967 · Pijuan-Sala mouse gastrulation atlas

- 内容：116,312 个细胞，E6.5–E8.5，9 个连续时间点。
- 价值：提供 6 小时级早期状态转移和谱系分支。
- 使用：仅 WT atlas；删除 Tal1−/− chimera、注入 ESC 与其他非 WT 组件。
- 状态：`ALLOW_FILTERED`。

### E-MTAB-11763 · Extended Mouse Atlas

- 内容：扩展到 E9.5，E6.5–E9.5 共 13 个时间点、约 430k 细胞；新增 E8.75–E9.5。
- 价值：与官方 E9.5 形成 domain bridge，并提供 E8.5–E9.5 的稠密转移。
- 使用：仅明确 WT；保存 embryo proper/yolk sac 元数据，不混用绝对组成。
- 状态：`ALLOW_FILTERED`。

### GSE193346 · Developing mouse heart

- 内容：两个小鼠品系、E9.5–P9、18 个阶段，并含 Wt1/Tbx18 mutants。
- 价值：允许的 E14.5+ 心脏状态与基因程序可作为晚期锚；E9.5 用于跨域校准。
- 使用：仅 WT；只保留 E9.5 与 E14.5+；删除 E10.5–E13.5 和全部 mutants。
- 注意：只转移程序方向与状态支持，不转移外部绝对比例。
- 状态：`ALLOW_FILTERED`，仅 T1。

### 不纳入默认路线：Qiu prenatal atlas / GSE228590 等

这些大图谱覆盖保护阶段，processed embeddings、labels 或 trajectory 可能已混入受保护细胞。除非能从 raw per-stage 数据重新处理并证明保护样本在训练前完全删除，否则默认 `REJECT`。

## 3. T3 核心数据与知识

### GSE52123 · WT GATA4 occupancy

- 内容：E12.5 mouse heart 的 GATA4 ChIP/bioChIP 数据及其他阶段/条件。
- 价值：给出目标基因可能直接结合哪些区域；只提供 directness，不自动提供激活/抑制符号。
- 使用：仅 E12.5 WT heart GATA4 ChIP replicate 与 matched input；删除 adult/stress 条件。
- 状态：`ALLOW_FILTERED`，仅 T3。

### CellOracle

- 价值：在目标 WT context 中构建 GRN，并模拟 TF perturbation 的传播方向。
- 使用：只在 sanitized WT 数据上现场训练；不使用作者预训练模型。
- 状态：`ALLOW`，代码许可需记录。

### scTenifoldKnk

- 价值：从 WT scGRN 出发，将目标基因 outdegree 置零，产生独立的 virtual KO 排序。
- 使用：只在 sanitized WT 数据上运行；作为独立证据，不单独决定 submission。
- 状态：`ALLOW`。

### CollecTRI

- 内容：大规模 signed TF-target regulons。
- 价值：提供目标 TF 的激活/抑制先验。
- 风险：聚合资源不一定提供足够 stage/genotype provenance。
- 使用：仅保留可审计、非目标 perturbation 来源的 edge；strict lane 不允许 unresolved edge 决定符号。
- 状态：`ALLOW_FILTERED`；更宽松使用需组织者确认。

### OmniPath / Reactome / Gene Ontology

- OmniPath：有向/有符号 signaling topology，尤其为后续 β-catenin 提供路径约束；继承上游资源许可证，必须按 academic license 过滤。
- Reactome：CC0 的 curated pathway data；用于 pathway membership 与传播边界。
- GO：CC BY 4.0；用于 lineage/state/function gate，不提供因果符号。

### Replogle 2022 Perturb-seq / scPerturb

- 价值：学习一般 perturbation 的稀疏度、标准化幅度和异质性。
- 不允许承担：Gata4/β-catenin 的方向。
- 必须删除：GATA4、GATA6、CTNNB1、MESP1、核心 canonical WNT 组件、核心 cardiac-lineage TF，以及任何可能 phenocopy 的 perturbation。
- 状态：`CONDITIONAL`，只在 T3-A1 方向路线通过后启用。

### 明确拒绝：GATA4 mutant cardiogenesis 数据

任何 GATA4 mutation/KO/knockdown 或明显相同心脏发育表型数据，尤其接近 E8.75 条件者，视为同基因或 phenocopy 风险，默认不用。

## 4. 外部空间数据

MOSTA 覆盖 E9.5–E16.5，但同时包含 E10.5、E12.5、E13.5 等保护或近保护阶段。即使过滤后：

- 对 T1 没有空间评分；
- 对 T3 当前没有形态排名；
- 对 T2 的可用阶段和 Data 页措辞仍需书面确认；
- 2D sagittal Stereo-seq 与比赛 3D MERFISH heart/embryo 存在显著 modality/geometry mismatch。

因此 `B2-T2-X1` 默认禁用。书面确认后也只允许使用明确获准的 stage，并只优化 G2/G3，不重新做未经验证的 NFS pairing。

## 5. 数据与 atom 的对应

| Source | T3-A1 | T1-A1 | T1-A2 | T3-A2 | T2-X1 |
|---|---:|---:|---:|---:|---:|
| E-MTAB-6967 | lineage context | state dictionary | temporal operator | — | 禁止默认复用 |
| E-MTAB-11763 | lineage context | E9.5 bridge | temporal operator | — | 禁止默认复用 |
| GSE193346 | — | late programs | terminal prior | — | 禁止默认复用 |
| GSE52123 | directness | 禁止 | 禁止 | parent prior | 禁止 |
| CellOracle/scTenifold | signed vote | — | — | parent prior | — |
| CollecTRI/OmniPath | conditional vote | — | — | parent prior | — |
| Reactome/GO | gate/module | state modules | state modules | blacklist/module | — |
| Replogle/scPerturb | — | — | — | response shape | — |
| MOSTA | — | — | — | — | conditional |
