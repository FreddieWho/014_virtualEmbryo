# T1/T2/T3 并行推进与交付系统

当前T3准入解释以 `docs/coordination/T3_EXTERNAL_DATA_POLICY_20260921.md` 为准：取消shape-only及统一书面确认要求，保留按来源/条件审查与真实边界疑问处理；仅替代旧快照中相应T3额外解释，其他任务约束不变。
跨任务数据资源入口：[`data_infra.md`](../../data_infra.md)（按来源查找；各 task 的使用许可独立）。

这是本项目的人类和 agent 共同入口。根目录 `STATUS.md` 是快速总览；三个任务追踪文档记录路线变更；本目录的 `STATUS.md` 保留机器可读的并行状态。

## 先看什么

```text
根目录 STATUS.md
→ docs/coordination/T1_TRACKING.md / T2_TRACKING.md / T3_TRACKING.md
→ docs/coordination/STATUS.md
→ docs/starter_pack/config/task_contracts.yaml
→ submissions/INDEX.tsv
→ 相关脚本、实验 registry 和报告
```

## 项目规则

- T1、T2、T3 是独立提交路线，默认 `dependencies: []`。
- T2/T3 可以共享 WT 数据、500-gene panel、空间 contract 和代码，但共享资源不等于任务依赖。
- leaderboard 是第一目标；科学结论用于指导和解释，不是提交前置门槛。
- 科学状态可以是 `BLOCKED_FOR_PROMOTION`，但必须明确 `blocks_submission: false`。
- 每个候选都必须有唯一版本、父版本、路径、SHA256 和 contract 结果。
- 已评分文件不可覆盖；服务器分数未登记前，不得宣称改进。
- 文档按事件更新，不写无决策价值的日常流水账。

## 权威来源

| 内容 | 权威来源 |
|---|---|
| 官方任务、数据和契约 | `docs/starter_pack/`、官方 starter kit |
| 当前任务、agent、lease、阻塞 | `docs/coordination/STATUS.md` |
| 候选路径、哈希、格式状态 | `submissions/INDEX.tsv` |
| 服务器分数、差值、submission ID、证据 | `reports/SERVER_SCORE_REGISTRY.md` |
| 保留/淘汰/暂停决策 | `docs/coordination/DECISIONS.md` |
| 跨任务科学结论和可复用方案 | `docs/coordination/KNOWLEDGE.md` |
| 实验级目录 | `docs/starter_pack/experiments/registry.csv` |

官方内容采用 cache-first：先读取 `reports/OFFICIAL_SYNC.md`、starter_pack 官方快照、已下载 notebook 和 `infra/bioinf-data-index/`。只有缓存缺失、疑似过期、用户明确要求或官方状态有变化风险时才重新访问官网；刷新后记录日期、来源和变化。

阶段报告如 `FIRST_CYCLE_REPORT.md` 和 `SUBMISSION_READINESS.md` 保留为历史/阶段说明，不作为实时状态源。

## 并行工作方式

推荐每个 agent 使用独立 worktree 和分支：

```text
master
├── agent/t1/<agent-id>
├── agent/t2/<agent-id>
└── agent/t3/<agent-id>
```

路径所有权默认如下：

| 路径 | 所有者 |
|---|---|
| `submissions/candidates/T1_*`、T1 专属代码 | T1 agent |
| `submissions/candidates/T2_*`、T2 专属代码 | T2 agent |
| `submissions/candidates/T3_*`、T3 专属代码 | T3 agent |
| 共享代码、validator、公共配置 | 先登记 lease 的 agent |
| `docs/coordination/*.md` | coordinator；agent 通过 handoff 提交更新 |
| `submissions/INDEX.tsv` | coordinator |
| `reports/SERVER_SCORE_REGISTRY.md` | coordinator |
| `submissions/scored/` | 只读 |

任何两个 agent 不得同时修改同一路径。共享代码需要先在 `STATUS.md` 登记 lease；如果当前仓库尚未有可用 commit，worktree 状态写 `pending`，不得伪造已初始化状态。

## 标准交付链

```text
claim
→ generate candidate
→ local contract validation
→ agent handoff
→ coordinator integration
→ update INDEX.tsv
→ user uploads
→ user returns score / submission ID（不额外要求原始证据）
→ update SERVER_SCORE_REGISTRY.md
→ calculate delta
→ retain / reject / hold
→ update STATUS.md and DECISIONS.md
```

## Agent handoff 模板

```text
task:
candidate_id:
parent_candidate:
method:
artifact_path:
sha256:
changed_paths:
contract_result:
tests_or_checks:
local_proxy_result:
known_risks:
proposed_decision:
new_shared_knowledge:
blocker:
```

agent 不直接伪造服务器分数，也不把本地 pseudo-score 写成官方分数。

## 手动上传包命名

每个 atom/task 生成一个上传包，命名为：

```text
{batch}__{task}__manual_upload__{YYYYMMDD}.zip
```

包内每个 `.h5ad` 使用以下字段顺序，便于人工识别批次、任务、board、路线和版本：

```text
{batch}__{task}__{board}__{lane}__{version}.h5ad
```

包内同时放置 `UPLOAD_MANIFEST.tsv`，映射重命名文件到 canonical candidate ID、路径和 SHA256。重命名只发生在 ZIP 内，不能改名、覆盖或替换 canonical artifact；portal 的 `Model` 列不作为候选身份依据。
