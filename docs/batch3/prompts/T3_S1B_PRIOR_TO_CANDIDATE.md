# T3-S1B-GENERATE · 将通过 gate 的 prior 转为可提交候选

## 前置

必须有：

- P0 locks；
- 显式 `route_id` 和对应 `T3-S1A-STATE-JOIN/metrics/gate_report.v2.json`；
- 从 `config/active_task.yaml` 读取 route/gate/prior/evidence/manifest 的路径与 SHA256 绑定，并在入口重新计算哈希、调用 route-gate validator；任何绑定变化均 fail-closed；
- 对应 route 的 `status: PASS`、`candidate_generation: true`、`blocks_submission: false`；
- 全局 `outcome` 必须是 `PRIOR_GATE_PASS` 或 `PARTIAL_ROUTE_PASS`，不得从 `HOLD_AS_COMPONENT` 推断放行；
- 锁定的 target-stage WT anchor；
- 可运行 T3 local scorer/contract；
- 若使用 CINEMA-OT，必须明确其只提供训练 KO 的 response-shape，而非 target sign。

## 唯一目标

构造：

```text
X_KO = X_WT
     + p_mesp1_lineage
     × state_gate
     × confidence_shrinkage
     × signed_prior
     × severity
     + residual_replay
```

首先保护 DES/DCS 和 WT 背景，再看 PSS/MMD/CSS。坐标默认复制 WT。

## 两条 lane

### L1_STRICT_SPARSE

- 仅使用 prior L1；
- 非零基因/状态极稀疏；
- severity 使用一次解析规则：由训练 KO 标准化效应分布的中位/分位形状给出，不能复制绝对方向；
- 强 WT shrinkage；
- KO target 只在 Mesp1 gate 内抑制；
- 未响应行完整保留 WT residual。

### L2_CONDITION_AWARE_SHRUNK

- 使用 prior L2；
- Gata4 与 Gata6 分通道组合，Gata6 dosage 上限来自基因型，实际 residual 仍乘 confidence；
- state-specific severity；
- 比 L1 更宽，但总响应质量与非零比例在生成前固定；
- β-catenin test-ready 路线使用独立配置，不与 Gata4 lane 共用 sign source。

## Response-shape

允许从 Mab21l2 + CINEMA-OT/Pertpy 学：

- 响应细胞比例的分布形状；
- state heterogeneity；
- 标准化 effect magnitude 的稀疏度/尾部；
- residual/covariance replay 方式。

禁止学习/迁移：

- target response gene 方向；
- Gata4/β-catenin 绝对 severity；
- 目标基因的 top-k。

## Protected checks

- gene order/normalisation/obs schema；
- 非 Mesp1 gate 细胞与 WT 的差异接近 0；
- conflict prior 不产生 residual；
- coords 与 WT 完全一致或 contract-required 最小复制；
- 未响应基因的均值与 residual/covariance 不被无意重写；
- 两 lane 差异与配置一致。

## 评分

每 lane 一次 local score。选择顺序：

1. DES/DCS 不得同时低于 identity；
2. 方向成立后再比较 PSS；
3. MMD/CSS 作为群体保护；
4. 不用 local score 重新调 sign/top-k/severity。

## 输出与停止

每个当前 T3 board/condition 生成完整 H5AD，写齐固定结束面。完成两 lane 后停止，不自动提交。
