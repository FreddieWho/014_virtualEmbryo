# Virtual Embryo Challenge · 现有工具集成施工包

版本：2026-08-30  
依据：`Virtual_Embryo_Challenge_现有工具与方案总结报告_20260829.docx`、Batch 1 服务器复盘、既有 Batch 2 外部信息施工包  
默认入口：`01_AGENT_CONTROLLER_PROMPT.md` + `config/active_task.yaml`

## 1. 本包解决什么

本包不再讨论“可以尝试哪些模型”，而是把报告中的结论压缩成可编码、可验收、可停止的任务：

1. **P0-LOCK**：锁定 scorer、submission contract、board、canonical parent、SHA256 和工具环境；修复或明确阻塞 T1 full-panel scorer。
2. **T3-S1-PRIOR**：用 CollecTRI/CellOracle/scTenifoldKnk/OmniPath 建立 `gene × stage × lineage × state` 的 signed prior committee，只输出可审计先验与 gate，不急着生成细胞。
3. **T1-PRE-HARMONIZE**：统一 E8.5/E9.5 state vocabulary，验证 projection 稳定性；可复用已有 Batch 2 产物。
4. **T1-S2-MOSCOT-DECODER**：以锁定 parent 为锚，用 moscot/WOT + UOT/state mass + 两种 residual decoder 形成两条可提交 lane。
5. **T2-S3-SHAPE-FIELD**：冻结已经获服务器支持的 board-specific G1 scale 和表达行，只比较 Spateo 与 pycpd 对 G2/G3 的改造。
6. **T3-S1B-GENERATE**：只有 T3 prior gate 通过后，才把先验转成 WT-anchored sparse residual 候选。
7. **T2-J1-PROXY**：只有建立与 NFS 同方向的 source-only proxy 后，才允许重新启用 FGW/soft assignment。
8. **HX-DYNAMICS-KILLTEST**：MIOFlow 2.0 或 scDiffEq 的单假设高风险测试，默认冻结。

## 2. 当前证据快照

P0 必须到仓库中重新核验，不能把下面内容当作已锁定事实：

- T1 当前选择预计为 `candidate/T1_val/v0004_strict_pseudobulk_shift`；
- T2 预计是：两个插值 board 使用 B1-A1 的 board-specific scale winner，heart extrapolation 保留原 parent；
- T3 当前锚预计为 `wt_identity`；
- Batch 1 已否决：重复 WT-only Spearman signed residual、通用 greedy expression-coordinate permutation、机械复用插值 scale 到 heart extrapolation；
- 报告记录的内部任务分数与当前官方 floor 文案可能不在同一 scorer snapshot，必须先解释版本映射。

## 3. 推荐执行顺序

```text
P0-LOCK
  ├── T3-S1-PRIOR ──[gate pass]──> T3-S1B-GENERATE
  ├── T1-PRE-HARMONIZE ──> T1-S2-MOSCOT-DECODER
  └── T2-S3-SHAPE-FIELD

T2-J1-PROXY 仅在 S3 后独立进行；
HX-DYNAMICS-KILLTEST 仅在结构化主线完成后授权。
```

P0 后，`T3-S1-PRIOR` 与 `T1-PRE-HARMONIZE` 可以由不同 agent 并行做**只读分析和工具适配**；正式候选生成仍按 atom 独立完成，不允许把多条路线揉成一次不可诊断的运行。

## 4. 交给 agent 的最短方式

1. 将本目录复制到项目仓库。
2. 给 agent：`01_AGENT_CONTROLLER_PROMPT.md` 与 `config/active_task.yaml`。
3. 默认只运行 `P0-LOCK`。
4. 验收 `artifacts/tool_integration/P0-LOCK/RESULT.md`。
5. 将 `active_task` 改为下一任务，并同步替换 `prompt_file`。

不得让 agent 在一次执行中自动连跑全部任务。这里不是保守，而是为了保留因果归因：哪个工具改善了哪个评分原子。

## 5. 固定结束面

每个任务必须写入：

```text
artifacts/tool_integration/<TASK_ID>/
├── inputs/                         # 输入引用、hash、版本，不复制大文件
├── intermediates/                  # coupling/prior/field 等标准中间件
├── submissions/<board>/<lane>/prediction.h5ad   # 仅生成型任务需要
├── metrics/local_score.json        # 有 scorer 时
├── metrics/protected_checks.json
├── config_resolved.yaml
├── TOOL_VERSIONS.json
├── MANIFEST.json
├── COMPLETION_REPORT.md
├── RESULT.md
└── run.log
```

只允许以下结论：

- `READY_FOR_MANUAL_SUBMISSION`
- `HOLD_AS_COMPONENT`
- `REJECT`
- `BLOCKED_VALIDATION`
- `BLOCKED_COMPLIANCE`
- `BLOCKED_TOOLCHAIN`

任何候选均不得自动上传服务器。

## 6. 与已有 Batch 2 包的关系

本包是**增量工具适配包**，不是 Batch 2 的替代品。若仓库中已有 `docs/batch2_external/` 或 `artifacts/atomic_batch2/`：

- 复用已经审计和哈希锁定的外部数据；
- 复用 `state_vocabulary.tsv`、`state_crosswalk.tsv`、GATA4 evidence、prior vote 等有效中间产物；
- 不重复下载、不重复净化、不覆盖旧 artifact；
- 通过 `06_MERGE_WITH_EXISTING_BATCH2.md` 完成任务映射。
