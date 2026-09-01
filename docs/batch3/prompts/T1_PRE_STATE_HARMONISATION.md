# T1-PRE-HARMONIZE · 状态词表、projection 与验证链

## 唯一目标

在运行 moscot/WOT 前，建立 E8.5/E9.5 可复用 state vocabulary 与稳定 crosswalk，并确认 T1 full-panel scorer 可用。本 task 不生成正式未来阶段候选。

## 复用优先

若已有 Batch 2 `B2-T1-A1`：

- 校验 `state_vocabulary.tsv`、`state_crosswalk.tsv`、program matrix 和 manifest hash；
- 检查其 scorer/contract snapshot；
- 可直接转换到本包 schema；
- 不重复聚类和不重下数据。

## 施工

### 1. 表示

优先顺序：

1. 项目已有、冻结且稳定的 state label；
2. 已有 frozen latent + centroid；
3. 必要时才构建 48–64 个非负 gene programs，基于 state/sample pseudobulk，不训练统一大深模型。

### 2. Vocabulary

统一：

```text
lineage -> state_family -> fine_state
```

- 官方 E9.5 为目标 domain；
- 允许外部 E9.5 只用于 domain offset，不直接复制比例；
- marker/program cosine + mutual nearest centroid 建 crosswalk；
- 低置信 state 进入 `UNRESOLVED`；
- 禁止为提高匹配率强行一对一配完。

### 3. Stability

至少检查：

- label/centroid bootstrap 或 sample leave-one-out 稳定性；
- E8.5→E9.5 projection 的 mutual consistency；
- 小状态对阈值的敏感性；
- state residual 是否仍可从 parent cells 提取。

只做一次预声明检查，不做阈值网格。

### 4. Pseudo-holdout

使用相同 vocabulary 做一次 E8.5→E9.5 的 source-only projection，使用 full-panel scorer/相同 contract 评估。该结果只用于确认表示和验证链，不据此发明新的未来状态。

## 输出

```text
intermediates/state_vocabulary.tsv
intermediates/state_crosswalk.tsv
intermediates/state_centroids.npz
intermediates/program_definition.tsv
metrics/state_stability.json
metrics/projection_pseudoholdout.json
metrics/full_panel_scorer_check.json
```

## Gate

- `STATE_GATE_PASS_AND_FULL_PANEL_SCORER_PASS`：允许 T1-S2；
- `BLOCKED_VALIDATION`：scorer 仍不可运行；
- `REJECT`：state mapping 不稳定且没有可复用的 frozen representation。

写完结果后停止。
