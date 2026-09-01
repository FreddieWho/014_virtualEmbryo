# AGENTS.md · Tool Integration Pack

## 工作方式

- 先读 `01_AGENT_CONTROLLER_PROMPT.md` 与 active task prompt。
- 只施工一个 task；完成后停止。
- 优先复用现有模块；新增代码应为薄 adapter，而不是平行重写工作台。
- 重要函数必须有类型提示、输入校验、确定性 seed 和清晰错误信息。
- 不在 notebook 中留下唯一实现；生产逻辑进入脚本/模块，notebook 只作诊断。

## 数据与 artifact

- 大数据不复制到本包目录；使用 path + SHA256 引用。
- 所有写入均落在 `artifacts/tool_integration/<TASK_ID>/` 或当前任务批准的代码目录。
- 旧 candidate 与旧 manifest 不可变。
- 中间件必须可脱离 Python session 重读。

## 测试

至少包含：

- schema/维度测试；
- gene/obs 索引一致性；
- sign convention toy test；
- parent hash 与不可变性；
- task-specific protected invariant；
- 一个小型端到端 smoke test。

## 日志

记录：

- 命令；
- 随机种子；
- 输入/输出路径与 hash；
- 工具版本；
- lane 差异；
- fallback 是否触发；
- 异常与恢复动作。

## 禁止

- 自动服务器提交；
- 网格搜索；
- 根据服务器分数改方法；
- 破坏 core scorer 环境；
- 临时下载未审计外部数据；
- 把 proxy 结果写成排行榜结论。
