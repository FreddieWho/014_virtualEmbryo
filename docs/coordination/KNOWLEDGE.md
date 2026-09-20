# 共享科学知识与技术复用登记

本文件不记录普通进度，只记录可以跨任务复用的科学边界、假设、结论和技术方案。代码仍放在 `scripts/`，本文件只登记路径、契约、证据和限制。

## 成熟度

```text
hypothesis       尚未验证的假设
candidate        有局部证据，不能当作稳定结论
validated        已通过相应的本地/官方验证
rejected         已被证据否定或明确停用
boundary         适用范围或不可推断边界
```

只有 `validated` 条目可以作为默认复用方案；`hypothesis` 和 `candidate` 必须在使用时保留风险说明。

## 科学框架

### K-0001 — 三任务共享“发育状态变化”这一上层问题

- scope: T1,T2,T3
- type: scientific_boundary
- maturity: hypothesis
- claim: "T1 研究正常时间表达变化，T2 研究正常时空状态变化，T3 研究 KO 对正常状态的偏离；三者共享科学框架，但不是同一个因果结论。"
- evidence:
  - `docs/starter_pack/config/task_contracts.yaml`
  - official task definitions
- reusable_in: T1,T2,T3
- limitations:
  - "单个任务的 leaderboard 分数不能单独证明跨任务机制"
  - "T2 预测提升不能直接推出 T3 KO 因果结论"

### K-0002 — WT 发育状态可作为 T2/T3 的共享先验

- scope: T2,T3
- type: technical_reuse
- maturity: candidate
- claim: "T2/T3 可以共享 WT 表达、细胞状态和空间 contract；T3 仍必须独立预测 KO 响应并独立评分。"
- evidence:
  - `data/E8.75.h5ad`
  - `docs/starter_pack/config/task_contracts.yaml`
  - official T2/T3 task definitions
- reusable_in:
  - T2
  - T3
- implementation:
  - `third_party/veckit/score_h5ad.py`
  - `docs/starter_pack/config/task_contracts.yaml`
- limitations:
  - "共享 WT 数据不是任务结果依赖"
  - "T3 坐标虽需提交，公开 T3 评分重点仍是扰动响应和细胞状态"

## 已验证或可复用技术

### A-0001 — 官方 scorer 与任务 contract 入口

- scope: T1,T2,T3
- type: reusable_code
- maturity: validated
- implementation:
  - `third_party/veckit/score_h5ad.py`
  - `docs/starter_pack/config/task_contracts.yaml`
- input_contract: "AnnData；任务对应的 gene order、X、以及 T2/T3 的 spatial_3D 要求"
- output_contract: "本地 contract/scoring 结果；不包含隐藏验证答案"
- consumers:
  - T1
  - T2
  - T3
- tests: `tests/`
- limitations:
  - "本地 pseudo-score 不等于服务器 score"
  - "隐藏 target 不得进入模型或验证流程"

### A-0002 — T2 expression midpoint normalization

- scope: T2
- type: reusable_code
- maturity: validated
- implementation: `scripts/t2_expression_model.py`
- consumers:
  - T2 heart interpolation
- evidence:
  - `submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad`
  - `reports/SERVER_SCORE_REGISTRY.md`
- limitations:
  - "当前只在 T2 heart interpolation board 获得服务器验证"
  - "不得未经独立 contract 和评分验证直接宣称适用于 T1/T3"

### A-0003 — 版本化 submission artifact 管理

- scope: T1,T2,T3
- type: reusable_code
- maturity: validated
- implementation:
  - `submissions/README.md`
  - `submissions/INDEX.tsv`
- consumers:
  - T1
  - T2
  - T3
- contract: "每个 candidate 使用独立目录和 submission.h5ad；评分后保留不可变快照"
- limitations:
  - "服务器 submission ID 和分数仍需人工回填"

### A-0004 — B1-A1 双 lane source-only uniform G1 scale
- scope: T2
- type: candidate_method
- maturity: candidate
- implementation: `scripts/t2_g1_scale.py`
- claim: "在不改变表达、细胞顺序和 15-NN 空间拓扑的前提下，用训练阶段空间 RMS 的 log-scale 估计目标阶段的统一坐标尺度；L1 为正式相邻阶段插值/末段斜率外推，L2 为全部训练阶段等权 OLS。"
- evidence:
  - `artifacts/atomic_batch1/B1-A1/FINAL_SET_MANIFEST.json`
  - 六个 per-candidate `manifest.json` 的 contract/invariant checks
  - 六个 `metrics/local_or_official.json`（fixed public pseudo-holdout）
- limitations:
  - "public pseudo-holdout 仅是生成前的本地诊断，不能替代服务器成绩。"
  - "heart 阶段 RMS 非单调，L1 extrapolation 对末段斜率敏感；L2 是平滑替代，不能据此宣称真实发育机制。"
  - "目前只有候选成熟度，不能晋级为 validated，也不能替换已有 53.6 T2 best。"

### A-0005 — B1-A1 server-scored lane comparison
- scope: T2
- type: server_scored_candidate
- maturity: candidate_with_server_evidence
- evidence: `reports/SERVER_SCORE_REGISTRY.md` 的 B1-A1 条目；用户回填六个 board 分数与 submission ID
- claim: "L1_FORMAL_LOG_RMS 在 B1-A1 的 embryo interpolation、heart interpolation、heart extrapolation 三个 board 均高于 L2；相对 parent，前两个 board 提升，heart extrapolation 下降。"
- decision: "按 board 保留 L1；L2 作为已评分第二候选和审计备份；不把两条 extrapolation 结果解释为机制证据。"
- limitations:
  - "T2 55.5 与 aggregate 147.8 是由 L1 三个 board 分数按现有协议推导，服务器未直接返回 Total。"
  - "单轮六个结果不能晋级为普适或因果科学结论。"

## 晋级规则

- agent 可以提出新的 `K-*` 或 `A-*` 条目，但必须写明证据和限制。
- coordinator 才能把条目从 `hypothesis/candidate` 晋级为 `validated`。
- 只有跨任务重复出现且有独立证据的结果，才能写成跨任务科学结论。
- 任何科学解释都不得改变比赛交付路线或成为合规提交的额外门槛。

## Batch 1 收尾观察

### B1-K-0001 — G1 uniform scale 的 board-specific 竞争信号
- scope: T2
- type: server_scored_candidate
- maturity: candidate
- evidence: `reports/SERVER_SCORE_REGISTRY.md` 的 B1-A1 记录；A1 L1 在两个 interpolation board 高于各自 parent，heart extrapolation 低于 parent。
- reusable_in: "仅可作为后续 T2 board-specific 候选的起点，不可当作通用发育尺度规律。"
- limitations: "单次 server scoring；heart RMS 外推敏感；没有跨组织、跨阶段或独立 replicate 证据。"

### B1-K-0002 — WT-only Spearman signed response 不足以支撑本轮 T3 KO
- scope: T3
- type: rejected_candidate_method
- maturity: rejected
- evidence: `artifacts/atomic_batch1/B1-A2/` 的 protected checks 与 Mab21l2 self-check；两条 lane 均 contract-valid 但低于 `wt_identity` server baseline。
- reusable_in: "作为失败边界：没有 Gata4-specific response prior 时，不应直接重复该 fallback。"
- limitations: "方向先验、借用的幅度预算和状态 gate 未做 factorial isolation；不能据此推出 Gata4 生物学方向。"

### B1-K-0003 — 状态质量 residual 路线存在弱服务器信号但当前不可晋级
- scope: T1
- type: server_scored_candidate
- maturity: candidate
- evidence: `reports/SERVER_SCORE_REGISTRY.md` 的 B1-A3 记录；两条 lane 高于最初 baseline 但低于已有 T1 best，且 full-panel local scorer 未完成。
- reusable_in: "若重新施工，应先解决跨阶段 state assignment 与 scorer 可重复性，再决定是否保留 mass residual 方向。"
- limitations: "没有完成本地 full-panel scorer；E8.5/E9.5 label vocabulary 未 harmonise；不能分离 partition、mass forecast 和 residual bank 的贡献。"

### B1-K-0004 — 固定 expression-coordinate pairing 方案未获 server 晋级
- scope: T2
- type: rejected_candidate_method
- maturity: rejected
- evidence: `artifacts/atomic_batch1/B1-A4/` 的 permutation/geometry protected checks 与 B1-A4 server scoring；六个候选结构检查通过，但没有 board improvement。
- reusable_in: "后续若重做，必须先验证 local objective 与 NFS 的公开可重复关联，不能只重复当前 greedy swap。"
- limitations: "没有重复 seed 或独立 NFS proxy；不能推出 expression-coordinate pairing 一般无效。"

### B3-K-0001 — T3 正式候选前置 contract 与 directed-knowledge 分层
- scope: T3 / Batch 3 pre-formal-analysis
- type: reusable_gate_and_limitation
- maturity: verified_engineering_with_scientific_hold
- evidence: `artifacts/tool_integration/CONTRACT-PREFLIGHT-20260831-v2/contract_preflight.json`、`artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3/summary.json`、`artifacts/tool_integration/STABILITY-PREFLIGHT-20260831-v3/stability_preflight.json`；5 个 P0 current parent contract/registry SHA256、protected-field 和 round-trip 复核通过，接口测试 22 passed。
- conclusion: "新版单一 H5AD contract 可用于后续候选写入；CollecTRI/OmniPath 快照已被本地 directed-evidence consumer 实际读取并通过来源元数据与内容审计；外部 edge confidence 仍未校准。"
- scientific_boundary: "integration preflight 只证明 edge/path 消费和 KO-WT 符号转换，不证明 state-specific activity、prior promotion 或 beta-catenin 生物学机制；当前 S1 prior 未消费 state-joined external evidence。"
- decision: "保持 T3-S1-PRIOR gate 为 HOLD_AS_COMPONENT；两个 local model family 的 leave-one-family-out 仍结构性失败，外部 edge 与既有模型族存在方向 discordance，不硬接为第三票。"
- limitations: "CollecTRI/OmniPath 为 T3 500-gene panel-scoped snapshot；未运行 S1B state join、科学验证、H5AD、local candidate score 或服务器提交。blocks_submission: false。"

- scope: T3-S1A / Extended Mouse Atlas state-join deployment
- type: external_input_and_runtime_status
- maturity: verified_input_and_partial_runtime_block
- evidence: `infra/bioinf-data-index/INDEX.tsv`、`infra/bioinf-data-index/SUMMARY.md`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5/metrics/data_audit.json`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5/metrics/runtime_blocked.json`；官方 archive MD5、exact E8.75 metadata-first raw-count input、5 个 Ensembl alias closure、full OmniPath/CollecTRI snapshot 和 CellOracle base-GRN 均有本地哈希记录。
- conclusion: "Extended Mouse Atlas 可作为 exact E8.75 WT source-attested state-join input，500-gene panel 已通过精确 gene identity 闭合；CellOracle 0.22.0 的本地资源部署可实际完成 Gata4 target。"
- scientific_boundary: "source-level WT attestation 不是逐细胞 genotype；state/activity 仍未验证为 target perturbation activity；Gata6/Ctnnb1 full propagation 未完成，不能据此晋级任何 route 或生成候选。"
- decision: "保持 T3-S1A 为 BLOCKED_RUNTIME；不生成 H5AD/candidate，不运行 scorer，不提交服务器。后续必须用新 atom 完成剩余 target 和 scTenifold，再重新生成 route-specific gate。blocks_submission: false。"
- limitations: "v5 在 CellOracle Gata6/Ctnnb1 simulate_shift 超过 bounded observation window 后中止；scTenifold 与 gate_report.v2.json 未在该 atom 运行，当前不存在可提交结果。"

### B3-K-0002 — T3-S1A v6 runtime repair and gate boundary
- scope: T3-S1A / CellOracle and route gate
- type: runtime_repair_with_scientific_hold
- maturity: verified_runtime_with_scientific_block
- evidence: `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/metrics/tool_execution.json`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/metrics/gate_report.v2.repaired.json`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/metrics/artifact_manifest.stable.json`；exact input/state join、Gata4 CellOracle、三条 scTenifold 输出和 hash-bound route audit 均有本地记录。
- conclusion: "target-level process isolation、atomic checkpoint 和低频 RSS/runtime 记录解决了 v5 的运行窗口阻塞；Gata4 real API 在 v6 完成。当前 base GRN 没有 Gata6/Ctnnb1 可扰动 TF source，因此两者不能被当前 CellOracle route 当作已验证 perturbation。"
- scientific_boundary: "state activity 仍为 NOT_VALIDATED，route gate 为 BLOCKED；这不是候选生成资格，也不支持机制或 leaderboard 改进结论。"
- decision: "保持 T3-S1A gate blocked，blocks_submission: false；不生成 H5AD/candidate，不运行 scorer，不提交服务器。后续必须解决 target-compatible GRN/applicability 与 state-specific activity/stability 缺口，不得用 proxy、降采样或未等价替代。"
- limitations: "v6 历史 gate 中 Gata6/Ctnnb1 保留实际运行返回的 BLOCKED_TOOLCHAIN 标签；代码已加入 capability preflight，后续新运行会显式区分 NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT。"

### B3-K-0003 — T3-S1A v7 的 state-response 与 target applicability 边界
- scope: T3-S1A / state join / CellOracle / route gate
- type: verified_engineering_with_scientific_hold
- maturity: verified_component_with_scientific_hold
- evidence: `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/tool_execution.json`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/state_response_support.json`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/gate_report.v2.repaired.json`、`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/artifact_manifest.stable.json`；exact input/state join、Gata4 CellOracle、三条 scTenifold 输出、coverage 文件和 hash-bound route audit 均有本地记录。
- conclusion: "state-specific CellOracle 输出必须经记录的 external-state→recorded-parent-state 映射后才可参与 route evidence；unmatched external states 排除，mapping collision 不当作独立样本。当前 base GRN 中 Gata6/Ctnnb1 缺少可扰动 TF source，因此它们的 CellOracle 状态为 NOT_APPLICABLE，而不是 biological invalid。"
- scientific_boundary: "Gata4 full-matrix state response/coverage 只支持 `MODELLED_STATE_RESPONSE_ONLY`；23 个 required mapped states 中 12 个通过、11 个未通过 within-state consistency，整体 support 为 `NOT_IDENTIFIABLE`。`biological_activity_status=NOT_VALIDATED`，不能由 model response、WT expression 或 proxy 活性替代。"
- decision: "保持 T3-S1A 为 `HOLD_AS_COMPONENT`，四条 route 均 HOLD，`blocks_submission: false`；不生成 H5AD/candidate，不运行 scorer，不提交服务器。"
- reusable_in: "可复用为后续 route-specific activity/stability 复核的 provenance 和 coverage 审计组件；不能直接作为候选生成器或因果机制证据。"
- limitations: "scTenifold 结果仅为 unsigned rank evidence；state mapping 有 collision；当前 GRN 对 Gata6/Ctnnb1 不可用；尚无 biological activity 和独立 stability 证据。"

### B3-K-0004 — External directed knowledge must remain contextual in S1B
- type: boundary
- maturity: validated
- evidence: `artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v2/metrics/gate_report.v2.json`、`artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v2/metrics/state_join_audit.json`、`artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v2/metrics/stability_s1b.json`、`artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v2/metrics/artifact_manifest.stable.json`
- conclusion: "在当前 S1A v7 输入中，CollecTRI/OmniPath 可以被重新审计并投影到 parent state 作为 `GLOBAL_CONTEXTUAL` supporting knowledge；它们不能改变 `activity_gate_pass`、CellOracle applicability、signed biological sign 或独立 family 数。S1B 的四条 route 均保持 HOLD。"
- engineering_rule: "LOFO 必须从 family-native biological rows 删除 family 后重算 conflict/claim；external edge/path 与 unsigned rank 不得作为 signed biological family。冲突时仅将派生 canonical contribution 归零并标记 `CONFLICT`，不得把冲突解释为 inactive。"
- reusable_in: "后续 route-specific activity/stability 复核的 contextual evidence adapter、state collision audit、raw-versus-derived conflict audit。"
- limitations: "state mapping 有 9 个 external labels 对应多个 parent states；该 collision 已保留在 audit，不是独立样本。当前 biological activity 仍未验证，不能进入正式候选生成。"
- decision: "保持 `HOLD_AS_COMPONENT`，`blocks_submission: false`；无候选、无 scorer、无服务器结论。"

### B3-K-0005 — 可复用 artifact 必须绑定实现脚本版本
- type: provenance_boundary
- maturity: validated
- evidence: `artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v3/inputs/input_lock.json`、`artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v3/metrics/artifact_manifest.stable.json`、`artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v3/metrics/gate_report.v2.json`
- conclusion: "在没有 initial Git commit 的工作区中，artifact 内部 hash 自洽仍不足以证明生成代码版本；S1B v3 将实现脚本 SHA256 `cd480790fa6cbf7e6618ec28675983143466788847e79e73040d63df7dfe9d8c` 同时写入 input lock、stable manifest、gate 和 completion，形成可复核的 artifact-to-code 绑定。"
- reusable_in: "后续所有 T3 prior/state/generate atom 的 provenance lock；若脚本发生修改，应新建版本化 atom，不覆盖旧 artifact。"
- limitations: "Git commit 仍不可用（branch unknown/no initial commit），因此不能声称 commit-level reproducibility；脚本 SHA 绑定只证明代码文件版本，不替代环境、输入和方法审计。"
- decision: "接受 S1B v3 为当前复用版本；保持 `HOLD_AS_COMPONENT`，不生成候选，不上传。"

### B3-K-0006 — target-compatible GRN 证明接口适用性，不证明生物活性
- type: method_compatibility_boundary
- maturity: validated_component
- evidence: `artifacts/tool_integration/T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1/metrics/gate_report.json`、`artifacts/tool_integration/T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v2/metrics/target_results.json`、`artifacts/tool_integration/T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v2/metrics/gate_report.json`
- conclusion: "原生 CellOracle TFdict adapter 可让 Gata6 与 Ctnnb1 进入真实 fit/simulate API；Gata6 使用 18 个一跳 CollecTRI panel relation，Ctnnb1 仅保留一跳 Ctnnb1→Pitx2。该结果只说明 source membership 和方法接口可运行，不说明 edge sign、target activity、state specificity、causal validity 或 independent family stability。"
- reusable_in: "后续获得 E8.0–E9.5 matched activity 后的单独 full rerun 前置组件；不得把 augmented TFdict 直接视作 challenge prior 或候选证据。"
- limitations: "Ctnnb1 为 custom non-TF direct-signaling source adapter；外部 relation 的 sign 只作审计元数据，未注入 TFdict；S1C-B fixture 是 24×20 synthetic structural smoke，无生物样本、rank、sign 或 state response。"
- decision: "接受 S1C-A/v1、S1C-B/v2 为可复用方法组件；全局 gate 继续 `HOLD_AS_COMPONENT`。"

### B3-K-0007 — 外部扰动表达方向支持 context，不足以迁移到 E8.75
- type: independent_activity_context
- maturity: preliminary_context
- evidence: `artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1/metrics/processed_effects.json`、`artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1/data/evidence_inventory.tsv`、`infra/bioinf-data-index/INDEX.tsv`
- conclusion: "GSE156307 的 Gata4 E14.5 胚胎胃部 cKO 与 GSE255237 的 Gata6 E11.5 OFT perturbation 均显示靶基因下降方向，但它们是不同阶段/组织/扰动剂量的 context-only observations；截至本 atom，E8.75 matched activity 不可识别，independent signed family count 为 0。"
- reusable_in: "用于后续证据检索的优先级和方向性 sanity check；不进入 S1A/S1B route gate、challenge 输入或候选生成。"
- limitations: "GSE255237 官方系列设计和 processed 列数存在重复数冲突；GSE156307 也不是 E8.75 胚胎组织。两份文件为 processed-only，raw 未下载；不能据此声明可迁移效应或服务器改善。"
- decision: "保持 `HOLD_INSUFFICIENT_MATCHED_ACTIVITY_EVIDENCE`；继续寻找 E8.0–E9.5 matched tissue/state、至少两个 biological replicates 的 target-specific perturbation。"

### B3-K-0008 — stable manifest 必须排除进程生命周期内的 runtime cache
- type: artifact_provenance_boundary
- maturity: validated_component
- evidence: `artifacts/tool_integration/T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v2/metrics/artifact_manifest.stable.json`、`artifacts/tool_integration/T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3/metrics/artifact_manifest.stable.json`、`tests/test_t3_s1c_source_adapter_smoke.py`
- conclusion: "S1C-B/v2 的 post-run 检查证明 SQLite `cache.db-shm` 可能在生成进程结束后消失；将 runtime cache、MPL/Numba cache 和 `-shm/-wal` sidecar 纳入 stable manifest 会破坏交付后的可复核性。v3 通过排除策略和进程退出后的 7/7 文件 hash/bytes 校验收口。"
- reusable_in: "所有包含 genomepy/CellOracle 本地 runtime 的后续 atom；stable manifest 只登记稳定输入、配置、结果和 receipt，不登记生命周期临时文件。"
- limitations: "v3 的 manifest provenance 已闭合，但其 fit/simulate 仍是 24×20 synthetic structural smoke，不是 biological activity、state specificity 或 candidate evidence。"
- decision: "接受 S1C-B/v3 为当前可复用 source-adapter smoke 组件；v1/v2 receipt 保留但不复用。"
### B3-K-0009 — exact-stage GEO perturbation 不等于 E8.75 state-matched activity
- type: scientific_evidence_boundary
- maturity: validated_component
- evidence: `artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3/metrics/gate_report.json`、`metrics/processed_effects.json`、`data/sample_qc.tsv`、`data/mapping_qc.tsv`；官方 GSE5298/GSE9652/GSE78125 series matrix 与 GPL1261/GPL6246 annotation 的 SHA256 记录见 `metrics/source_audit.json`
- conclusion: "三份 E9.5 官方 processed matrix 可审计出 Gata4 两个 direct cardiac-tissue perturbation family 和 Ctnnb1 一个 AHF family；Gata6 仍无 exact processed family。Gata4 target probe 的 two-probe median effect 在 GSE5298 为 `+0.02084`、GSE9652 为 `+0.25275`，Ctnnb1 在 GSE78125 为 RMA `-0.02584`；这些 target expression readouts 不作为功能 gate。"
- reusable_in: "可用于候选前的 external context inventory、样本/平台/探针映射审计和后续假设生成；不能作为 E8.75 candidate activity、leaderboard improvement 或机制证明。"
- limitations: "E9.5 与 E8.75 不同，组织为 AVC/pooled heart/AHF 而非挑战状态；pooled biological material、平台尺度、probe placement 和 lineage composition 限制跨状态转移；无 raw CEL、无 state-specific signed gene set、无独立 signed-family stability，因此 gate 为 HOLD，blocks_submission=false。"
- decision: "接受 S1D v3 为当前 exact-stage contextual evidence 组件；保持 candidate_generation=false、server_submission=false，继续寻找 state-matched signed-family 证据。"

## 2026-09-21 T3输出与验证限制复核

- 成熟度：当前冻结artifact的直接数值诊断。R6最终GCN负值全部落在父版本零条目；幅度1/0.1/0.01时负值比例不变，说明当前加法表示不能靠缩小正幅度解决。证据 `reports/t3_route_review_20260921/CHECKS.json`；不外推为所有模型的普遍失败。
- 成熟度：补充对照，非预注册独立验证。R6图模型相对训练基因平均扰动响应的留出MSE优势仅约1.36%；原始两对照通过事实保留，但基因特异学习证据较弱。证据同上；成人→胚胎泛化未验证。
- 成熟度：当前候选的直接差分。R5 on/off仅S100a10的1,319个表达条目不同；同分只限制本次最小链实现，不能推出通信机制无效。证据同上和权威分数注册表。
- 成熟度：待验证技术假设。非负表达依赖输出、样本内NTC、R4类型内残差映射可能改变工程/泛化结果，均未执行新训练或生成候选，不声称服务器增益。详细复核 `reports/t3_route_review_20260921/REPORT.md`；blocks_submission: false。
