# T3-S1A-STATE-JOIN · state-joined external evidence and route gate repair

## 唯一目标

在不生成 H5AD、不调用 scorer、不上传服务器的前提下，修复 T3-S1 prior 的两个阻塞：

1. 将官方 Extended Mouse Atlas 的精确 E8.75 WT raw counts 经过 metadata-first 防火墙审计，形成可复用的 state/activity 输入；
2. 将真实 CellOracle、scTenifoldNet/scTenifoldKnk 和 full mouse CollecTRI/OmniPath 接入 state-joined evidence，生成 route-specific prior/gate。

## 固定边界

- stage 只接受官方 `E8.75`；边界/转换不明确的记录为 `AMBIGUOUS_BLOCKED`。
- 只保留 WT、非 perturbation、非 target/phenocopy 条件；Gata4、Gata6、Ctnnb1、Mesp1 及 WNT blacklist 不得作为扰动输入。
- 若官方 cell metadata 没有逐细胞 genotype/condition 列，只能使用已缓存论文方法段的明确 WT source attestation，并在审计中保持 `PASS_SOURCE_ATTESTED` 与逐细胞条件 PASS 的区别；不得凭空填入 WT。
- Extended Mouse Atlas 外层归档官方 MD5：`442645308463a64c3bb947c25921199e`；先保存 file list、size、license、publication 和 planned keep/remove，再解包。
- CellOracle 必须记录真实上游包版本和实际 API 执行；不能把回归近似称为 CellOracle。
- 运行时修复采用共享 GRN 拟合一次、每个 target 独立 `fork` worker、原子 target 输出和 checkpoint；保持 exact-stage 全细胞/全选定基因输入、`n_propagation=3`、扰动值、GRN 和随机种子不变。单 target 观察窗口为 60 分钟；超时仍必须写 `BLOCKED_RUNTIME`，不得截断后标记成功。
- CellOracle 的 exact external state 输出必须通过已记录的 parent→matched-external state mapping 消费；未匹配 external state 不得静默当作 parent state。新增的 state-response/coverage 只可声明 `MODELLED_STATE_RESPONSE_ONLY`，不能改写为 biological activity；当前 GRN 不具备 Gata6/Ctnnb1 TF source 时只标记 CellOracle×target route `NOT_APPLICABLE`，不能推断 target 生物学无效。
- scTenifoldNet/scTenifoldKnk 只提供 WT-only network/rank evidence；其 unsigned distance/rank 不能包装成 signed causal direction。
- ChIP/occupancy 只提供 directness；Reactome/GO 只提供 membership/provenance。
- 不下载或使用 GSE7430/MSigDB target-perturbation signature，不引入 target perturbation data。

## 路线

```text
GATA4_GATA6_VALIDATION_E875::L1_STRICT_AGREEMENT
GATA4_GATA6_VALIDATION_E875::L2_CONDITION_AWARE
BETA_CATENIN_HIDDEN_E875::L1_STRICT_AGREEMENT
BETA_CATENIN_HIDDEN_E875::L2_CONDITION_AWARE
```

- L1：至少两个独立 sign family 同号，conflict=0；Gata4 需 directness；β-catenin 需有向 signaling path；非零上限 10%。
- L2：保留 state-specific rank aggregation；冲突 gene sign=0；Gata6 dosage channel 单独保存 `dosage_fraction=0.5`；非零上限 25%。L2 也必须通过 state mapping、样本量、selected-gene stability 和 evidence-family stability；不能因路线较宽而绕过未验证 activity。
- state/activity 必须进入 committee：`state_join_status` 与 `activity_gate_pass` 共同决定记录是否可保留非零 sign。当前 WT expression 与 source attestation 不构成已验证的 perturbation/state activity，故应记录 `NOT_VALIDATED_*` 并保持 route `HOLD`，不得写 `candidate_generation: true`。
- route 通过不等于全局通过。四条 route 全部通过才写 `PRIOR_GATE_PASS`；部分通过写 `PARTIAL_ROUTE_PASS`；全不通过写 `HOLD_AS_COMPONENT`；输入/工具不可审计写 `BLOCKED`。

## 输出

写入新目录 `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v1/`，至少包括：

- `intermediates/state_gate.tsv`
- `intermediates/state_activity.tsv`
- `intermediates/source_votes.tsv`
- `intermediates/prior_<route_slug>.json`
- `intermediates/evidence_<route_slug>.tsv`
- `metrics/gate_report.v2.json`
- `metrics/data_audit.json`
- `metrics/tool_execution.json`
- `metrics/stability.json`
- `metrics/state_response_support.json`
- `DATA_SOURCES_USED.tsv`, `TOOL_VERSIONS.json`, `METHOD_DISCLOSURE.md`
- `MANIFEST.json`, `COMPLETION_REPORT.md`, `RESULT.md`, `run.log`

每个 route 必须同时记录 status、blockers、evidence paths 及其 hash、source artifacts 及其 hash、route prior/artifact manifest 绑定、state/stability gate、方法实际执行状态和 `blocks_submission: false`。route gate 必须精确包含四条契约路线，并校验 prior schema、manifest、输入文件身份和方法输出哈希。若任何核心方法无法在锁定环境运行，保留 route 为 `NOT_RUN`/`BLOCKED`，不得用 proxy 结果替代。

## 停止条件

完成数据/工具审计、route-specific prior/gate 和稳定性复核后立即停止。不得自动进入 S1B、生成候选、评分或提交服务器。
