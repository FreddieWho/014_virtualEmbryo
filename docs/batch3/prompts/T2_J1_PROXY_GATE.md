# T2-J1-PROXY · NFS-correlated source-only objective gate

## 状态

条件任务。它不生成正式 candidate，只判断是否存在值得重新启用 FGW/soft assignment 的 objective。

## 唯一目标

在观察阶段的 leave-one-stage-out 设置中，验证一个 expression-neighborhood objective 是否：

- 与 official NFS-like 邻域定义结构一致；
- 稳定优于 random permutation；
- 在至少两个独立 holdout 中同方向改善；
- 不只是重新发现形态或 cell-type label。

## 禁止

- 重复 Batch 1 greedy local swap；
- 直接在隐藏目标 board 上调 objective；
- 使用服务器分数反推目标邻域；
- 生成正式 submission；
- 把几何改善当 NFS 改善。

## 候选 objective

只允许在 full run 前固定一个：

- moscot/POT FGW：表达 state/program cost + graph/internal-distance cost；
- 或 novoSpaRc/SpaOTsc 设计模式的 soft assignment。

必须先定义目标空间支撑：来自 source pseudo-holdout 的真实点云；本 task 不声称隐藏未来支撑已知。

## Baselines

至少比较：

- identity/current pairing；
- random permutation；
- Batch 1 类结构保持 greedy（可读取旧结果，不必重跑）；
- 新 objective。

## 输出

```text
intermediates/objective_spec.yaml
metrics/holdout_results.tsv
metrics/random_baseline.tsv
metrics/proxy_gate_report.json
RESULT.md
```

## Gate

- `J1_PROXY_PASS`：允许另行授权 assignment candidate；
- `REJECT`：不稳定或只在单一 holdout 改善；
- `BLOCKED_VALIDATION`：无法实现同结构 NFS-like scorer。

写完 gate 后停止。
