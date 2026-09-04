# Agent Team locked run 与证据规范

官方规则快照日期：2026-09-04。执行前仍需检查官网是否更新。

## 1. 核心边界

Agent Team 判断的是**配置锁之后的自主性**。

锁之前允许：

- 人修改 prompt；
- 人选择模型、harness、工具和预算；
- 人读取旧 run 结果；
- 人重新设计下一次 run；
- 人启动多个 run。

锁之后禁止：

- 人读取中间结果后改变当前 run；
- 人替 agent 选择当前 run 的中间 output；
- 人修改 H5AD；
- 人改变工具权限、prompt 或预算后继续声称同一个 run。

配置变化意味着新 run，不是原 run 的续跑。

## 2. 服务器选择

人可以从已经完成的 locked runs 中选择提交哪个。  
服务器返回值可以用于普通模型选择和下一 run 立项。  
不能用返回值计算 hidden truth 后再把该真值写进 candidate。

## 3. 每个 scored candidate 必须可追溯到 run

Batch 4 要求至少保存三类证据，实际提交至少上传官方要求的两个不同种类：

1. **prompts**
   - controller；
   - active task prompt；
   - task manifest；
   - 所有子 agent prompts；
   - prompt SHA256。
2. **trajectory**
   - agent 尝试、观察、决策和 tool calls；
   - 不能事后凭记忆重建；
   - 允许压缩，不允许静默截断。
3. **harness**
   - 运行 agent 的代码、配置或 commit；
   - model / tool permissions / budget；
   - environment lock。

## 4. 固定文件

每个 run：

```text
evidence/
├── PROMPTS/
│   ├── controller.md
│   ├── task.md
│   ├── active_task.yaml
│   └── subagents/
├── trajectory.jsonl.zst 或 trajectory.txt.gz
├── harness_snapshot.tar.zst 或 HARNESS_COMMIT.txt
├── TOOL_PERMISSIONS.json
├── ENVIRONMENT.json
├── PROMPT_SHA256.tsv
└── EVIDENCE_MANIFEST.json
```

## 5. `RUN_LOCK.yaml` 必填字段

- run_id；
- task_id；
- UTC start；
- git commit；
- git dirty digest；
- controller hash；
- task prompt hash；
- active task hash；
- task manifest hash；
- model/provider；
- effort/reasoning setting；
- harness commit/hash；
- tools与权限；
- network；
- server submission permission；
- external download permission；
- seed；
- lanes；
- walltime / compute budget；
- parent path/hash；
- allowed output paths；
- evidence capture command。

## 6. lane 选择

若一个 run 生成多个 lanes：

- lane 定义必须在 lock 前固定；
- agent 在 run 内可以使用本地诊断给出推荐顺序；
- 全部 contract-valid lane 保留；
- 人不能在 run 中途告诉 agent 哪个表现更好；
- run 结束后，人可选择上传任意完整 lane。

## 7. 崩溃和重启

配置不变、只是进程崩溃：

- 可重启；
- 记录 restart；
- 不改 run_id。

任何配置变化：

- 新 run_id；
- 新 lock；
- 旧 run 保留失败 receipt。

## 8. 预测文件所有权

- H5AD 必须由 agent / harness 写出；
- 人工重命名只能发生在上传 ZIP 内；
- canonical H5AD 不得人工编辑；
- ZIP 内副本 SHA 必须映射 canonical SHA；
- scored candidate 必须有对应 evidence manifest。

## 9. Batch 4 对旧 evidence 的处理

- 旧 scored artifacts 不补造 trajectory；
- Batch 4 不声称旧候选满足新 evidence；
- 从旧 parent 派生的新 candidate 必须有新的完整 run evidence；
- 旧代码可复用，但其 commit/hash必须进入当前 lock。

## 10. 官网参考

- Rules: `https://virtualembryo.ai/challenge/rules`
- Submission contract: `https://virtualembryo.ai/challenge/account/submissions`
- Reference rows: `https://virtualembryo.ai/challenge/baselines`

若官网规则变化，以新版本为准，并把差异写入 `OFFICIAL_RULE_DIFF.md`。
