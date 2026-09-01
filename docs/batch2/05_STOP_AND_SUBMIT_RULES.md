# Batch 2 停止、晋级与提交规则

## 1. 原子必须以提交候选结束

除一次性 P0 外，每个 atom 至少产生一个满足官方 contract 的 `.h5ad`。路线低于 parent 也要保留 candidate 与负结果，然后结束。

## 2. 固定预算

每个 atom：

- 功能检查：1 次；
- 完整生成：每 lane 1 次；
- 最终 local scorer：每 lane 1 次；
- seed：1 个；
- 网格搜索：0；
- 自动服务器提交：0；
- 临时第三 lane：0。

异常崩溃可用相同配置重启，不计新试验。

## 3. Parent 比较

候选必须与当前 canonical parent 比较：

- T1：current best，不是 Batch 1 旧 baseline；
- T3：`wt_identity`，以及若存在更强的 B2-T3-A1 parent；
- T2：按 board 当前 best。

不得通过复制旧 artifact 到新路径制造“候选”。

## 4. 原子保护

### T1

- 不允许外部绝对细胞比例直接替代官方分布；
- 只改允许的 state mass、program delta、transition 与 residual；
- full-panel 非交集基因由 parent 保持；
- 避免均值细胞、独立逐基因噪声和 covariance collapse。

### T3

- coordinates 保持 WT；
- 非 Mesp1 lineage 和低置信 gene 保持 WT；
- conflicting sign 设为零，不投票强行决定；
- target-specific directness 与 sign 分开；
- A1 不为 PSS 过度扩大幅度；
- A2 不允许重新定义方向。

### T2

- 外部空间路线未获书面许可前不得运行；
- 保留 Batch 1 已验证的 board-specific scale winner；
- 不再运行通用 greedy expression-coordinate permutation。

## 5. 本地决策

### READY_FOR_MANUAL_SUBMISSION

- contract/invariant PASS；
- data audit PASS；
- 主目标在 source-only pseudo-holdout 上优于 parent 或提供此前没有的信息能力；
- protected metrics 未出现明显崩溃；
- 方法披露完整。

### HOLD_AS_COMPONENT

- 主原子有局部改善，但总分或保护指标不足；
- 可作为 C1/ensemble 的独立组件；
- 不自动上传。

### REJECT

- 主目标没有改善；
- 或 source-only kill test 明确方向错误；
- 或候选破坏 parent 的非目标维度；
- 或 data/domain mismatch 使结果无解释价值。

### BLOCKED_COMPLIANCE

- source 处于 `CONDITIONAL` 且没有书面许可；
- stage/genotype 无法可靠过滤；
- license 或预训练语料不透明。

## 6. 服务器分数

- 人工上传后，只有高于当前 board best 才晋级；tie 仅记录。
- 不根据一个 score 反调 external stage、gene sign 或 phenocopy blacklist。
- 不通过差分 submission 推断 hidden target 属性。
- 服务器返回值、submission ID、candidate hash 全部登记且不可变。

## 7. 必需文件

每个 atom 必须写：

- `DATA_SOURCES_USED.tsv`：真实使用的 source、版本、hash、过滤；
- `METHOD_DISCLOSURE.md`：足以提交给组织者的方法摘要；
- `metrics/protected_checks.json`：非目标原子保护；
- `RESULT.md`：支持与不支持的结论；
- `MANIFEST.json`：全部 artifact hash。
