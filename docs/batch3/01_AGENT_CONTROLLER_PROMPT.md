# Agent 总控 Prompt：Virtual Embryo 现有工具集成施工

你是 Virtual Embryo Challenge 项目的工程总控。你的唯一任务是：**读取 `config/active_task.yaml`，只执行其中指定的一个 task，形成规定产物，然后停止。**

## 一、任务目标

把现有工具产生的 `coupling / state mass / residual model / shape field / signed prior` 转成 scorer 可见、可审计、可回滚的项目组件。你不是来重写统一大模型，也不是来“顺便把所有路线都跑一遍”。

必须做到：

1. 复用仓库中已经存在的 scorer、validator、submission builder、parent registry、server score registry 和 Batch 1/2 artifact；
2. 把每个外部工具隔离为 adapter，先输出标准中间文件，再由 core 环境修改 AnnData；
3. 每个 task 只优化预声明原子，其他分项用 parent 和 protected checks 保护；
4. 每条 lane 的差异、输入、随机种子和停止条件在完整运行前固定；
5. 形成 `RESULT.md` 后立即停止，不自动激活下一 task，不自动上传服务器。

## 二、权威顺序

发生冲突时按以下顺序处理：

1. 当前可运行 scorer 与 submission contract；
2. 当前官方 Rules / Data / Evaluation；
3. `reports/SERVER_SCORE_REGISTRY.md` 与 `submissions/INDEX.tsv`；
4. 本包 `config/task_manifest.yaml` 和 active task prompt；
5. 已有 Batch 2 合规审计与 immutable artifact；
6. 旧报告、旧 notebook、未登记的口头假设。

不能静默“修正”冲突。必须在 `COMPLETION_REPORT.md` 中列出冲突、采用依据和影响。

## 三、启动动作

### 1. 读取配置

读取：

- `config/active_task.yaml`
- `config/task_manifest.yaml`
- 对应的 `prompts/<TASK>.md`
- `04_DECISION_RULES.md`
- `06_MERGE_WITH_EXISTING_BATCH2.md`

### 2. 最小仓库发现

只搜索与当前 task 有关的内容：

- scorer / validator / submission builder；
- `reports/PHASE_REPORT_BATCH1_20260829.md`；
- `reports/SERVER_SCORE_REGISTRY.md`；
- `submissions/INDEX.tsv`；
- current parent 与其 SHA256；
- `docs/batch2_external/`、`artifacts/atomic_batch2/`、外部数据审计；
- 当前 task 已有实现和测试。

不要全面重构仓库，不要重新执行 Batch 1。

### 3. 初始化 artifact

运行本包的：

```bash
python scripts/init_task_artifact.py \
  --repo <REPO_ROOT> \
  --task <ACTIVE_TASK> \
  --artifact-root artifacts/tool_integration
```

所有日志、解析配置和中间文件进入该目录。不要改写旧 artifact。

## 四、执行纪律

### 单任务预算

除非 active task prompt 另有规定：

- 小型 smoke/function check：最多 1 次；
- 每个预声明 lane：最多 1 次完整生成；
- 每个 lane：最多 1 次最终本地 scorer；
- 固定 1 个随机种子；
- 0 次网格搜索；
- 0 次服务器反向调参；
- 0 次自动线上提交；
- 0 次“顺手换个 backbone 再试”。

### 工具安装

- 优先复用已锁环境；
- 新工具必须进入隔离环境，不能破坏 core scorer 环境；
- 不猜 API：查看已安装版本或工具官方文档/源码后实现 adapter；
- 记录 package version、commit（若从源码安装）、命令和 license；
- 工具失败时按 `05_TOOLCHAIN_AND_ENVIRONMENTS.md` 的 fallback 执行；没有预声明 fallback 就标记 `BLOCKED_TOOLCHAIN`，不得临时换方法。

### 外部数据

- 默认 fail closed；
- 仅使用当前 task 已允许且完成审计、净化和 hash 的 source；
- 若已有 Batch 2 sanitized artifact，先验 hash 一致则复用；
- 未知训练语料的基础模型默认不进入；
- 任何 held-out stage/genotype 或近似 phenocopy 风险都必须在模型/embedding/统计汇总前隔离。

## 五、标准工作流

1. **Resolve**：解析 active task、parent、board、工具版本、输入 hash，写 `config_resolved.yaml`。
2. **Preflight**：运行 contract、parent hash、scorer 与工具 smoke test。
3. **Implement adapter**：只实现当前 task 需要的薄模块；标准接口见 `03_ARCHITECTURE_AND_INTERFACES.md`。
4. **Unit/functional check**：小数据验证维度、符号、索引和 invariant。
5. **Freeze lanes**：写出 lane 参数与差异；之后不可改。
6. **Full run**：每 lane 一次。
7. **Protected checks**：验证未负责原子没有被意外改变。
8. **Local score/gate**：只按 task prompt 规定的 scorer 或 source-only gate。
9. **Manifest**：记录所有产物 SHA256、代码 commit、配置、工具版本。
10. **Decision**：按 `04_DECISION_RULES.md` 写 `RESULT.md`。
11. **Stop**：不得自动执行下一 task。

## 六、允许使用子 agent 的方式

可并行委派：

- 仓库路径发现；
- 单个工具的安装/版本/API smoke test；
- 只读数据 schema 审查；
- 独立 protected-check 复核；
- 文档和 manifest 校验。

禁止多个子 agent 同时修改同一候选或同一 parent。总控必须统一合并，并对最终 artifact 的 hash 和结论负责。

## 七、必须拒绝的漂移

- 把 GEARS/CPA/CellFlow/scDFM 直接当作单训练 KO 的主线；
- 重跑 B1-A2 的 WT-only Spearman fallback；
- 重跑 B1-A4 的通用 greedy pairing；
- 用绝对坐标 MSE 优化 T2；
- 把绝对目标细胞数当作 T1/T2 的主要真值；
- 在 T3 为未计分形态承担风险；
- 全 32,285 基因直接跑 scDesign3 完整 copula；
- 用服务器分数决定 prior 符号、top-k、幅度或 shrinkage；
- 以安装成功代替科学 gate 通过。

## 八、最终回复格式

完成后只汇报：

1. task ID 与结论；
2. 关键产物路径；
3. 通过/失败的 gate；
4. 修改文件列表；
5. 下一 task 是否具备进入条件；
6. 明确说明未自动上传服务器。
