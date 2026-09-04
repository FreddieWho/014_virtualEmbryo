# B4-P0-STATE-FLOOR-PARITY

## 唯一目标

在任何新候选前完成两项修复：

1. 把用户已更新的 T3 v0006/7 分数与项目权威状态源对齐，正式关闭旧 signed-prior 路线；
2. 证明或修复 T1 `copy_last` 与 T3 `wt_identity` 的官方 floor 构造同构性。

本 task 不优化模型，不调参，不使用服务器反推 target。

## 输入

必须读取本地工作区而不是只读公开 GitHub：

```text
reports/SERVER_SCORE_REGISTRY.md
submissions/INDEX.tsv
STATUS.md
TODO.md
LEADS.md
docs/coordination/T1_TRACKING.md
docs/coordination/T2_TRACKING.md
docs/coordination/T3_TRACKING.md
docs/coordination/DECISIONS.md
scripts/prepare_t1_t3_submission.py
third_party/veckit/
官方 runnable baseline notebook/cache
官方 starter kit / reference implementation
```

## A. 分数与状态对齐

### A1. v0006/7

定位：

```text
submissions/candidates/T3_gata4/v0006_b2_t3_a1_l1/submission.h5ad
submissions/candidates/T3_gata4/v0007_b2_t3_a1_l2/submission.h5ad
```

从本地 registry 读取精确服务器分数和提交 ID。不得猜测。

检查：

- `SERVER_SCORE_REGISTRY.md` 有 score；
- `submissions/INDEX.tsv` 不再 `score_pending`；
- `T3_TRACKING.md` 不再称它们未评分；
- `STATUS.md` 不再把它们列为待验证；
- `TODO.md` 不再暂缓该路线；
- `route_status.yaml` 与用户结论一致：旧 signed-prior candidate family `CLOSE_ROUTE`。

agent 不直接并发编辑权威文件；输出：

```text
registry_reconciliation.md
registry_patch_suggestions.diff 或 coordinator_patch.md
```

若本地仍没有精确 score：

```text
status: BLOCKED_SCORE_SYNC
```

但仍可继续只读 floor audit；不得写虚构数值。

### A2. current best

逐 task 解析 current best，不能用本包静态数字覆盖本地更新。

输出：

```text
current_parent_lock.yaml
```

字段：

```text
task
board
candidate_id
path
sha256
server_score
score_source
```

## B. scorer lock

校验：

- vendored scorer 与当前项目锁；
- official cache/notebook source hash；
- scorer入口；
- gene panel；
- submission contract；
- T3 官方排名是否计 spatial shape，禁止根据本地诊断字段误优化未计分项。

Batch 4 不修改 `third_party/veckit/`。

输出：

```text
scorer_lock_audit.json
```

## C. floor constructor diff

逐项对比官方 runnable floor 与项目现有 builder：

| 维度 | 官方 | 项目现有 | 是否影响 score |
|---|---|---|---|
| source H5AD | | | |
| source cells | | | |
| n_obs | | | |
| row IDs | | | |
| row order | | | |
| sampling | | | |
| sampling seed | | | |
| stratification | | | |
| use of `obs.celltype` | | | |
| gene order | | | |
| coordinates | | | |
| float dtype | | | |
| normalization | | | |
| extra fields | | | |

重点审查 `scripts/prepare_t1_t3_submission.py` 的自定义 celltype-stratified sampling。官方 submission contract 忽略 submitted celltype；不得把“格式合法”当成“floor 同构”。

输出：

```text
floor_constructor_diff.tsv
FLOOR_PARITY_ANALYSIS.md
```

## D. 生成 exact floor candidates

### T1

严格执行官方 `copy_last`：

- 以官方代码选择的 last observed stage / rows 为准；
- 不额外做 pseudobulk shift；
- 不做 state resampling；
- 不做 composition extrapolation；
- 不携带 coordinates；
- panel 与顺序完全一致；
- n_obs 按官方 runnable implementation；
- 若官方使用固定 working subset，必须复现该 subset。

### T3

严格执行官方 `wt_identity`：

- 使用 matched WT E8.75；
- expression 与 coordinates 按官方 floor constructor；
- 不置零任何 gene；
- 不做 lineage gate；
- 不做 residual；
- 不按项目自定义 stratification 改行集合。

输出：

```text
candidates/T1_val/L0_EXACT_FLOOR/submission.h5ad
candidates/T3_gata4/L0_EXACT_FLOOR/submission.h5ad
```

## E. 检查

- format；
- gene order；
- finite/nonnegative；
- T1 no coordinates；
- T3 coordinates exact；
- repeated run byte/content deterministic；
- parent source row identity；
- n_obs；
- SHA256；
- file size。

本地 scorer 只做 smoke；不能证明服务器恰好 50。

## F. 上传交付

生成：

```text
deliveries/b4p0__t1__upload__<date>.zip
deliveries/b4p0__t3__upload__<date>.zip
```

每个 ZIP 包括 H5AD、manifest、run/evidence pointers。

不自动上传。

## 结果状态

- `COMPLETE`
- `BLOCKED_SCORE_SYNC`
- `BLOCKED_OFFICIAL_BASELINE`
- `BLOCKED_CONTRACT`

`RESULT.md` 必须明确：

- v0006/7 是否已真正同步；
- floor constructor 差异；
- 新 exact floor 与旧项目 floor 的细胞/表达/坐标差异；
- 不能在服务器分数回来前宣称 floor 已修复。
