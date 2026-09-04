# B4-CLOSEOUT-ARCHITECTURE-HANDOFF

## 唯一目标

在 Batch 4 服务器分数完整回填后，结束增量修复并决定：

```text
BATCH4_COMPLETE_INCREMENTAL_PARENT
或
ARCHITECTURE_RESET_REQUIRED
```

本 task 不训练、不生成 H5AD、不改 scored artifact。

## 前置

必须有：

- 所有实际上传候选的服务器分数；
- submission ID 或明确 pending；
- candidate SHA；
- run evidence；
- local diagnostics；
- 当前官网/榜单快照。

缺分数：

```text
BLOCKED_SCORE_BACKFILL
```

## 工作

### 1. 对齐 registry

逐 candidate：

```text
run_id
candidate_id
parent
board
sha256
server_score
delta
local_rank
decision
```

### 2. 更新 current best

服务器 aggregate 优先，derived estimate 次之且显式标记。

### 3. 计算 gap

相对用户第十名参考 62/62/68：

- absolute gap；
- gap reduction；
- Batch 4 gain；
- per-board gain。

### 4. 错误签名

至少分：

- floor constructor；
- amplitude；
- state mass；
- expression direction；
- covariance/residual；
- geometry；
- assignment；
- stage conditioning；
- genotype conditioning；
- proxy/server disagreement。

### 5. 组件账本

每个组件：

```text
server_positive
local_positive_only
neutral
server_negative
not_tested
```

### 6. 生成报告

```text
reports/BATCH4_PHASE_REPORT_<DATE>.md
reports/BATCH4_SCORE_GAP.md
reports/BATCH4_ERROR_SIGNATURES.md
reports/BATCH4_COMPONENT_LEDGER.tsv
reports/BATCH4_PROXY_VS_SERVER.md
reports/ARCHITECTURE_RESET_BRIEF.md
reports/ARCHITECTURE_INPUT_READINESS.tsv
```

### 7. 架构决策

按 `02_SCOPE_AND_SUCCESS_CRITERIA.md`。

若进入 reset，brief 只定义能力、数据、接口、kill tests 和预算，不直接挑一个模型名。

## 禁止

- 为了让 Batch 4 看起来成功而重定义 baseline；
- 把弱正写成获奖潜力；
- 把 validation success 当 test success；
- 删除阴性 candidate；
- 在 closeout 顺手生成组合候选；
- 不完整分数下强行作最终路线决策。
