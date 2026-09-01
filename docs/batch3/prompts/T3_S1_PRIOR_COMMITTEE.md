# T3-S1-PRIOR · 条件感知 signed prior committee

## 唯一目标

为以下条件建立可审计的 `state × gene` signed/ranked prior 和 confidence：

- validation：`Mesp1-Cre; Gata4 F/F; Gata6 F/+ @ E8.75`；
- hidden/test-ready：`Mesp1-Cre; β-catenin F/F @ E8.75`。

本 task **不生成 H5AD**、不优化幅度、不调用服务器。它只回答：哪些基因在什么谱系/状态中更可能上调或下调，以及证据有多强。

## Parent 与输入

- P0 锁定的 T3 `wt_identity` 及匹配 WT；
- 官方 WT 状态/细胞类型/500-gene panel；
- 已审计的 WT full-transcriptome context（若 Batch 2 已有则复用）；
- 已审计 GATA4 occupancy/directness 证据（若已有）；
- CollecTRI、OmniPath 等带 provenance 的知识边；
- CellOracle、scTenifoldKnk 工具只运行在允许的 WT context 上；
- Mab21l2 KO 只用于 adapter/sign-convention 与 response-shape 的后续接口，不能决定 Gata4/β-catenin 方向。

## 标准 vote schema

所有工具必须转换为：

```text
target_gene, condition_id, stage, state, response_gene,
sign, rank_score, confidence, evidence_family, directness_score,
lineage_gate, provenance, conflict_flag
```

`sign` 定义为 **KO - matched WT**：`+1` 表示 KO 后上调，`-1` 表示 KO 后下调。TF-target edge 的 sign 不能直接照抄；删除 TF 后需要显式翻转并经 toy network 检查。

## 共用施工

### A. Lineage/state gate

1. 复用或建立 harmonized state crosswalk；
2. 为每个 WT cell/state 计算 `p_mesp1_lineage ∈ [0,1]`；
3. 不硬编码未经审计的 celltype 白名单；
4. 输出每 state 的 lineage probability、target expression、TF/pathway activity 与证据；
5. gate 只决定响应范围，不决定 sign。

### B. Gata4/Gata6 evidence

- CollecTRI：signed TF-target candidate；
- CellOracle：state-specific virtual suppression vote；
- scTenifoldKnk：独立 WT-only virtual KO vote；
- occupancy/ChIP：只增加 directness，不单独决定上/下调；
- Gata6 F/+ 作为独立 dosage channel 保存，`dosage_fraction=0.5` 仅表示基因型剂量上限，不声称表达效应恰为 0.5。

### C. β-catenin evidence

- OmniPath/directed signaling graph 为主；
- WT state pathway activity 用于 gate；
- scTenifoldKnk/网络传播作为独立 vote；
- TF regulon 只能作为末端读取，不能替代 β-catenin signaling path；
- target gene naming 和复合物成员必须有显式映射。

### D. 独立性

证据 family 至少区分：

1. WT inferred GRN；
2. curated TF-target；
3. directed signaling/pathway；
4. occupancy/directness；
5. WT state activity/lineage gate。

同一数据库的不同导出不能伪装成多票。

## 两条预声明 lane

### L1_STRICT_AGREEMENT

- 每个非零 response 至少两个独立 sign model 同号；
- Gata4 还需 directness 或审计 signed edge；
- β-catenin 还需有向 signaling path；
- conflict = 0；
- 非零 panel 比例上限 10%；
- unresolved provenance 不进入。

### L2_CONDITION_AWARE

- 保留 state-specific rank aggregation；
- Gata4 与 Gata6 分通道输出，后续 candidate builder 再按基因型组合；
- β-catenin 允许中等置信 path propagation；
- conflict gene 仍为 0，不通过多数投票强行定 sign；
- 非零 panel 比例上限 25%；
- uncertainty 明确进入 shrinkage 建议。

## Source-only 检查

### 1. Toy sign convention

构建已知激活/抑制 toy network，验证 virtual KO 输出的符号转换。失败则整个 task `REJECT`/`BLOCKED_TOOLCHAIN`。

### 2. Known-KO adapter check

在不使用 Mab21l2 KO 训练 sign 的前提下，以 WT-only pipeline 为 Mab21l2 生成 prior，并与已观测 KO 做一次 DES/DCS-like 检查。该检查只验证 adapter 是否系统性反号或失真：

- 不用结果调 Gata4 top-k；
- 不用结果调 target-specific amplitude；
- 若工具对非 TF target 不适用，明确标记 `NOT_APPLICABLE`，不能伪造通过。

### 3. Stability

对 state sampling 或 evidence family leave-one-out 做一次稳定性分析；不做多 seed 网格。

## 输出

```text
artifacts/tool_integration/T3-S1-PRIOR/
├── intermediates/source_votes.tsv
├── intermediates/evidence.tsv
├── intermediates/state_gate.tsv
├── intermediates/prior_L1.json
├── intermediates/prior_L2.json
├── metrics/sign_convention_test.json
├── metrics/known_ko_adapter_check.json
├── metrics/stability.json
├── metrics/gate_report.json
├── METHOD_DISCLOSURE.md
├── DATA_SOURCES_USED.tsv
├── TOOL_VERSIONS.json
├── config_resolved.yaml
├── MANIFEST.json
├── COMPLETION_REPORT.md
├── RESULT.md
└── run.log
```

## 通过与停止

- `PRIOR_GATE_PASS`：L1 或 L2 满足 `04_DECISION_RULES.md`，允许进入 T3-S1B；
- `HOLD_AS_COMPONENT`：只有部分 target/state 可靠；
- `REJECT`：符号/独立性/stability 不成立，继续保留 wt_identity。

写完 prior 与 gate 后停止；不得“既然都算完了就顺便生成候选”。
