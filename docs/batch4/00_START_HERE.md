# Virtual Embryo Challenge · Batch 4 修错补漏与追赶施工包

版本：2026-09-04  
定位：**remediation / catch-up sprint，不是最终主架构，不是获奖路线宣言**  
建议安装位置：`docs/batch4/`  
默认入口：`01_CODEX_CONTROLLER_PROMPT.md` + `config/active_task.yaml`

## 一句话结论

Batch 4 只做四件事：

1. 修复 Batch 1–3 暴露的基线、记录、实现和实验制度错误；
2. 补齐已经规划但没有端到端完成的低容量路线；
3. 放大已有服务器正信号，而不是重新部署一批名字更响的工具；
4. 为下一轮可能发生的大型架构调整留下干净接口、失败证据和可复用组件。

它不假装当前路线有获奖潜力。用户给出的当前第十名参考为：

| Task | 第十名参考 | 项目当前公开记录 | 公开差距 |
|---|---:|---:|---:|
| T1 | 62 | 48.5 | 13.5 |
| T2 | 62 | 约 56.0（按当前 per-board best 推算） | 约 6.0 |
| T3 | 68 | 45.3 floor best；v0006/7 已由用户更新为失败 | 22.7 |

第十名数值属于用户提供的当前榜单快照；执行时不得把本文当成实时榜单源。

## 为什么需要单独的 Batch 4

前三批产生了真实信息，但执行制度出现了偏差：

- `copy_last` / `wt_identity` 没有证明与官方 floor 构造同构，项目提交低于 floor=50；
- 本地 proxy 被赋予了过强的路线关闭权，但它与服务器结果多次不一致；
- T3 花了大量资源在出版级证据 gate，真实工具链却没有形成候选；
- Batch 2 的若干计划路线没有真正施工到 H5AD；
- “零网格、单 lane、单 seed”被误当作合规要求，压制了正常的有限校准；
- 工具成功、组件成功、科学证据成功和 leaderboard 成功被混在一起；
- 失败经常被扩大解释，例如“某个 decoder 失败”被写成“整个动力学方向失败”。

Batch 4 改为：

```text
仓库与分数状态对齐
→ 官方 floor 构造同构
→ 低容量、可归因的候选族
→ 人工服务器评分
→ 精确关闭当前实现
→ 输出大型架构调整所需的 handoff
```

## 本包包含什么

### 强制前置

- `B4-P0-STATE-FLOOR-PARITY`
  - 回填并核对 T3 v0006/7 的实际服务器分数；
  - 清理旧 `score_pending` / `HOLD_AS_COMPONENT` 状态；
  - 逐项比较项目 floor builder 与官方 runnable floor；
  - 形成严格 T1 `copy_last` 和 T3 `wt_identity` 候选。

### T1 修复

- `B4-T1-R1-CONSERVATIVE-FAMILY`
  - 对 strict pseudobulk shift 做有限幅度校准；
  - 测试 population mixture，而不是逐基因平均；
  - 只移植 Batch 3 中有本地正证据的 moscot state-mass，不复用失败 decoder。
- `B4-T1-R2-LATE-PROGRAM-BRIDGE`
  - 仅补完 Batch 2 已规划、但没有真正执行的 late-program bridge；
  - 条件任务，数据不就绪则快速停止，不新建大型数据工程。

### T2 修复

- `B4-T2-R1-FGW-ASSIGNMENT-REPAIR`
  - 修复 72–73% 软耦合冲突被 greedy 顺延破坏的问题；
  - 只做全局离散化与两个预声明 entropy。
- `B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE`
  - 补齐长期被几何路线挤压的表达与状态组成插值；
  - geometry / scale / assignment 冻结。
- `B4-T2-R3-HEART-EXTRAP-EXPRESSION-CAL`
  - 冻结失败的外推几何；
  - 只校准表达 shift 的时间尺度与保守混合。

### T3 修复

- `B4-T3-R1-GENOTYPE-ONLY-ABLATION`
  - 旧 signed-prior 路线整体关闭；
  - 只分离 Gata4 缺失、Mesp1 lineage gate、Gata6 F/+ 三个确定条件。
- `B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR`
  - 修复旧路线忽略目标阶段正常发育方向的问题；
  - 使用公开 WT 时间梯构造低容量 developmental-delay residual；
  - 不复活旧 GRN committee，不引入新神经架构。

### 收尾

- `B4-CLOSEOUT-ARCHITECTURE-HANDOFF`
  - 不再训练；
  - 汇总服务器结果、错误模式、可复用组件和下一代架构需求；
  - 生成 `ARCHITECTURE_RESET_BRIEF.md`。

## 建议阅读顺序

1. `01_CODEX_CONTROLLER_PROMPT.md`
2. `02_SCOPE_AND_SUCCESS_CRITERIA.md`
3. `03_FAILURE_AUDIT_AND_ROUTE_STATUS.md`
4. `04_EXECUTION_ORDER_AND_SERVER_BUDGET.md`
5. `05_AGENT_TEAM_RUN_AND_EVIDENCE_RULES.md`
6. `config/task_manifest.yaml`
7. 当前 active task 对应的 `prompts/*.md`

## 如何开始

将本目录复制到仓库：

```bash
cp -r Virtual_Embryo_Batch4_Remediation_Catchup_Pack_20260904 \
  <REPO>/docs/batch4
```

先运行只读预检：

```bash
python docs/batch4/scripts/preflight_repo_state.py \
  --repo <REPO> \
  --out <REPO>/artifacts/batch4/PREFLIGHT/repo_state.json
```

然后创建 Agent Team run lock：

```bash
python docs/batch4/scripts/create_run_lock.py \
  --repo <REPO> \
  --pack <REPO>/docs/batch4 \
  --out <REPO>/artifacts/batch4/RUN_LOCKS/B4-P0-STATE-FLOOR-PARITY \
  --provider <PROVIDER> \
  --model <MODEL> \
  --effort <EFFORT> \
  --harness <HARNESS_PATH_OR_COMMIT>
```

把以下两个文件交给总控 agent：

```text
docs/batch4/01_CODEX_CONTROLLER_PROMPT.md
docs/batch4/config/active_task.yaml
```

## 不可违反的边界

- 每次只运行一个 active task；每个 task 是一个独立 locked run。
- locked run 启动后，人不读取中间结果并干预。
- agent 可在该 run 内按冻结规则评估 lane，并自行给出推荐顺序。
- 用户可在多个已经结束的 locked runs 中选择上传哪个。
- 不自动上传服务器。
- 不用服务器分数计算隐藏 target 的属性。
- 允许 2–4 个事先声明、具有明确含义的 calibration lanes；禁止无边界网格。
- 每个评分任务必须形成可提交 H5AD，除非格式、合规或输入硬阻塞。
- 本地 proxy 只排序和防灾难，不再以“稍差一点”阻止服务器探针。
- 已评分 artifact 不覆盖。
- `third_party/veckit/` 只校验锁，不在 Batch 4 修改。
- T3 v0006/7 精确分数以本地最新 registry 为准，本包不猜测或复制尚未同步到公开仓库的数值。
- 新建代码放在 `scripts/batch4/`，不把补丁揉进旧脚本形成不可拆单体。

## 每个 task 的固定结束面

```text
artifacts/batch4/<TASK_ID>-<YYYYMMDD>-vN/
├── RUN_LOCK.yaml
├── config_resolved.yaml
├── candidates/
├── metrics/
├── protected_checks/
├── evidence/
│   ├── PROMPTS/
│   ├── trajectory.*
│   ├── harness_snapshot.*
│   └── EVIDENCE_MANIFEST.json
├── CANDIDATE_HANDOFF.md
├── RESULT.md
├── MANIFEST.json
└── run.log
```

## Batch 4 的最终含义

若 Batch 4 提分，它提供可继续优化的低方差 parent。  
若 Batch 4 仍远离 62/62/68，它不再追加“小补丁”，而是用本批生成的误差分解和接口资产启动大型架构重构。

这批的价值不是证明旧路线正确，而是把“旧路线到底错在哪里、哪些部件还能复用、下一代架构必须新增什么能力”变成可执行事实。
