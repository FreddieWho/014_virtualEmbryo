# T3-S1A 实现方案（2026-08-31）

## 目标

修复 `T3-S1-PRIOR-GATE-001` 的可执行部分：让 prior 真正消费 state-joined external evidence，补上 route-specific gate，且保持候选生成与服务器提交关闭。

## 执行顺序

1. 复核旧 P0/T3-S1 输入和不可变 artifact；登记新的独立 artifact 目录。
2. 先做 Extended Mouse Atlas metadata/file-list/license 审计；再下载并校验官方 25GB 归档；只从 raw counts 和 metadata 构造精确 E8.75 WT sanitized view。
   若 cell metadata 缺少逐细胞 condition，必须先验证缓存论文方法段的 `wild-type C57BL/6 matings` source attestation，并在结果中单独标识 source-attested WT。
3. 下载 full mouse OmniPath/CollecTRI 到新的 task-scoped sanitized 目录，记录 URL、日期、taxon、license、schema、内容摘要和 SHA256；不覆盖 B2 panel snapshot。
4. 使用已锁定的 `.venvs/ve-t3-prior` 执行真实 CellOracle API 和 scTenifoldNet/scTenifoldKnk API；若实际 API 不能在精确输入上完成，明确 `NOT_RUN`/`BLOCKED`。
5. 生成 state activity、source votes、四条 route 的 prior/evidence，并用 gate v2 汇总：全通过才 `PRIOR_GATE_PASS`，部分为 `PARTIAL_ROUTE_PASS`，否则 `HOLD_AS_COMPONENT` 或 `BLOCKED`。
6. 运行聚焦接口测试、数据审计和一次固定配置的 prior 计算；更新 `infra/bioinf-data-index/`、T3 tracking 和必要的协调状态。

## 不做

- 不生成/修改任何 H5AD；不运行 full-panel scorer；不提交服务器。
- 不使用 GSE7430、MSigDB target-perturbation signature 或任何 target/phenocopy perturbation data。
- 不把 CellOracle/scTenifold proxy、unsigned scTenifold distance 或 local diagnostic 当作 signed causal validation。
- 不覆盖 `artifacts/tool_integration/T3-S1-PRIOR/`、已评分 artifact 或既有 B2 snapshot。

## 验收

- 官方归档 checksum 与来源元数据可复核；E8.75 keep/remove、WT/blacklist 计数和 sanitized hash 完整。
- 四条 route 各自有明确 status/blocker/evidence；未通过 route 不得被全局 gate 隐式放行。
- route gate 精确覆盖四条路线，并把 prior、evidence、artifact manifest、官方输入成员和方法输出都绑定到可复核 SHA256；S1B 激活配置必须携带 route/gate/prior/evidence 绑定。
- state mapping、每个 state 的样本量、activity gate、selected-gene stability 和 evidence-family stability 必须实际参与 prior/gate；`NOT_VALIDATED` 或 `NOT_IDENTIFIABLE` 不得产生候选生成资格。
- prior record 的 confidence 可表达缺失/未校准，不以 `0.0` 冒充已测低置信度。
- 所有核心方法的实际执行状态、版本、输入输出 hash 和限制均写入结果。
- 交付仍明确 `blocks_submission: false`；结果只用于决定是否可以单独激活 S1B。

## 2026-08-31 执行记录

- 官方输入、500-gene alias closure、state join、OmniPath/CollecTRI 和 CellOracle base-GRN 本地部署已闭合；聚焦契约测试 `29 passed`。
- `v1` 在输入 cell key join 阶段阻塞，`v2` 在二维 state 索引阶段阻塞，`v3` 暴露并记录 CellOracle 默认只读路径和 R 版本校验问题；旧目录均保留且不可覆盖。
- 修复后 `v5` 使用共享 CellOracle cluster GRN fit：Gata4 real API 已完成；Gata6/Ctnnb1 的 exact-stage full matrix `simulate_shift` 在 bounded observation window 内未完成，故 `BLOCKED_RUNTIME`，不生成 route gate、不进入 S1B。
- 当前 partial handoff：`artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5/metrics/runtime_blocked.json`；下一次必须使用新版本化 atom。
- `2026-09-01` v6 execution closeout：使用新版本化 `T3-S1A-STATE-JOIN-20260901-v6`；exact E8.75 input/state join PASS；CellOracle Gata4 real API PASS（isolated worker）；Gata6/Ctnnb1 在当前 base GRN 中明确为 regulator 不适用；三条 scTenifold route 输出完成；route gate 汇总为 `BLOCKED`，state activity 为 `NOT_VALIDATED`，不生成候选、不上传。
- v6 runtime repair 保持 exact 输入、GRN、`n_propagation=3`、方法版本和参数不变；仅增加 target-level process isolation、atomic checkpoint、RSS/runtime 记录和 transient artifact 排除。v5 与 v6 均保留不可变。

## 2026-09-01 v7 执行与收口

- v7 在新版本化目录 `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/` 完成；稳定 manifest 共 223 个文件、无 transient 条目，manifest SHA256 为 `22d785ea59a85d13529db8896772ccdee5f79b95c4cd557bfabfff0897109db8`。
- 修正 state-specific CellOracle 输出的 state 语义：只通过已记录的 external-state→recorded-parent-state 映射投影；unmatched external states 不进入 method vote；mapping collision 保留在 audit，不当作独立样本。当前 GRN 中 Gata6/Ctnnb1 明确记为 `NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT`，不再混同为 biological invalid。
- Gata4 full-matrix state response/coverage 已落盘；23 个 required mapped states 中 12 个通过 within-state response consistency、11 个保持 HOLD。该组件的 claim 固定为 `MODELLED_STATE_RESPONSE_ONLY`，`biological_activity_status=NOT_VALIDATED`，故总体 state-response support 为 `NOT_IDENTIFIABLE`。
- v7 gate：`HOLD_AS_COMPONENT`，四条 route 均 `HOLD`，`blocks_submission: false`。48 项接口/状态测试、`py_compile`、stable-manifest 和 hash-bound route audit 均通过；不生成 H5AD/候选，不运行 scorer，不上传服务器。
