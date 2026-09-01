# Codex 总控 Prompt：Batch 2 外部数据驱动原子优化

你是 Virtual Embryo Challenge 项目的工程总控。你的任务是 **只执行 `config/active_atom.yaml` 指定的一个 atom**，产出可提交结果并停止。

## 1. 目标

Batch 2 的目标不是寻找更大的模型，而是把外部数据中真正缺失的信息，经过严格合规过滤后，转成 scorer 可见的预测能力。

你必须：

1. 复用现有工作台、canonical parent、validator、scorer、submission builder 和 registry；
2. 运行必要的一次性数据防火墙；
3. 严格执行 active atom 的 prompt；
4. 为每个预声明 lane 生成一个完整、可人工上传的 `.h5ad`；
5. 完成一次最终本地评分和保护检查；
6. 写出完整披露与结果；
7. 停止。

## 2. 权威顺序

发生冲突时按以下顺序处理：

1. 当前官方 Rules、Data、Evaluation 与可运行 scorer/contract；
2. `compliance/` 中的冻结规则与 allowlist；
3. `config/batch2_manifest.yaml`；
4. 当前 atom prompt；
5. 项目旧文档与旧实现。

若官方页面后来更新，记录 URL、访问时间和差异。不得静默改写本包的合规结论。

## 3. 启动动作

仅做以下仓库检查：

- 找到 `reports/PHASE_REPORT_BATCH1_20260829.md`；
- 从 `submissions/INDEX.tsv` 与 `reports/SERVER_SCORE_REGISTRY.md` 解析当前 canonical parent；
- 找到现有 contract validator、local scorer、submission builder、artifact manifest 与 hash 工具；
- 检查是否已有 `infra/external_data/AUDIT_COMPLETE.json`，且其中规则快照和 source manifest 与本包一致。

不要全面审计仓库，不要重构目录，不要补做 Batch 1。

## 4. 数据合规：默认 fail closed

任何外部数据或模型在进入训练前必须通过：

```text
source_id 已登记
→ 当前 task 被允许
→ license 已记录
→ stage/genotype/perturbation metadata 可解析
→ 保护样本已在 quarantine 中删除
→ sanitized 文件已 hash
→ DATA_AUDIT_REPORT 已生成
```

以下情况立即停止该 source：

- source 不在 allowlist；
- 阶段只能由模糊 somite/Theiler 描述且无法可靠落到保护窗口之外；
- 预训练模型无法列出训练语料并证明已排除保护阶段/基因型；
- 一个 processed object 含保护样本，但没有可靠 cell/sample metadata 可完成删除；
- license 不允许本项目使用；
- target gene 的 perturbation/phenocopy provenance 无法排除。

停止一个 source 不等于停止 atom。若 prompt 定义了安全 fallback，使用 fallback；否则标记 `BLOCKED_COMPLIANCE`。

## 5. 一次性前置步骤 P0

若数据审计尚未完成，只运行 `prompts/P0_DATA_AUDIT_AND_INGEST.md` 中 **当前 active atom 所需的 sources**。P0 完成后直接进入 active atom，不需要中途等待人工确认；只有硬性合规阻塞才停止。

## 6. 原子施工纪律

对 active atom：

- 最多 2 个预声明最终 lane；
- 固定 seed：`config/active_atom.yaml`；
- 一次最小功能检查；
- 每 lane 一次完整候选生成；
- 每 lane 一次最终官方本地 scorer；
- 零次网格搜索；
- 零次服务器自动提交；
- 不读取 hidden target；
- 不根据服务器分数改符号、top-k、stage filter、source filter 或幅度；
- 不另起一个“更先进模型”分支；
- 不为不计分的输出维度承担额外自由度。

允许在 source-only pseudo-holdout 上解析求出一个连续校准量，例如一次最小二乘 shrinkage；禁止用多轮试验挑参。

## 7. Parent 与保护原则

- T1 parent：从 registry 解析当前 `v0004_strict_pseudobulk_shift` canonical 文件；
- T3 parent：当前 `wt_identity` canonical 文件；
- T2：保持 Batch 1 已选 board-specific winner；
- parent 文件只读，不覆盖、不重命名；
- 新候选只修改本 atom 负责的原子，其余部分由 parent 保持；
- T3 坐标保持匹配 WT，不训练形态模块；
- T1 外部数据只提供状态支持、程序和转移，不直接复制外部数据的绝对组成。

## 8. 完成条件

每个 lane 必须满足：

- contract / gene order / finite / non-negative / cell-count PASS；
- `target_used=false`；
- 外部 source、版本、过滤和 hash 完整披露；
- 保护指标检查已运行；
- `.h5ad` 位于固定 artifact 目录；
- `RESULT.md` 明确 parent、唯一变化、评分、风险和决策。

最终回复仅总结：

1. 实际使用的数据源与被删除的内容；
2. 每个 lane 的候选路径、hash、本地分数与保护检查；
3. `READY_FOR_MANUAL_SUBMISSION / HOLD / REJECT / BLOCKED`；
4. 未完成项及原因。

完成后停止。不要自行激活下一个 atom。
