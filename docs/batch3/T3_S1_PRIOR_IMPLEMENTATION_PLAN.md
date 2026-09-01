# T3-S1-PRIOR 实施方案

日期：2026-08-31  
状态：COMPLETED_WITH_HOLD（本地方法/外部知识部署已通过；prior/gate 保持审慎 HOLD）
授权：2026-08-31 用户明确允许下载 `genomepy`、`scTenifoldNet` 等解除本地部署阻塞所需依赖。
权威任务：`docs/batch3/prompts/T3_S1_PRIOR_COMMITTEE.md`  
父任务：`P0-LOCK`  
输出根目录：`artifacts/tool_integration/T3-S1-PRIOR/`

## 目标与边界

只构建并审计 state × gene 的 signed prior committee，覆盖 `Gata4/Gata6`
验证条件和 beta-catenin 隐藏/待测条件。符号固定为
`sign = KO - matched WT`。本阶段不生成 H5AD、不优化扰动幅度、不运行
server scorer、不上传，也不把本地分数写成 leaderboard 结果。

## 已知阻塞与处理策略

1. 用户授权后，cache-only 部署已完成：CellOracle 0.22.0、`velocyto`、
   `genomepy` 0.16.4 以及 scTenifoldKnk 1.1 所需 `scTenifoldNet` 1.4
   均已按来源、版本、许可证、bytes、SHA256 锁定并通过本地 import/smoke。
2. B2-T3-A1 的 CellOracle/scTenifoldKnk 结果是可审计的本地近似/组件，不能
   伪称为上游包重跑；复用时保留原 hash、来源和 validation-only 边界。
3. 本阶段先 cache-first；在用户授权后已下载固定版本的软件依赖并将其
   来源、许可证、bytes、SHA256 写入锁文件。若本地没有 CollecTRI/OmniPath
   快照或其可核验替代来源，beta-catenin 的相应证据链仍标为
   `BLOCKED_EXTERNAL_DATA`，不得用未审计 TF-only 图静默替代。当前两份
   panel-scoped 快照已分别通过内容级审计；本轮 prior adapter 仍不消费它们，
   因此 beta 通路留到单独的 S1B 集成/验证。
4. CollecTRI/OmniPath 只有在各自快照分别通过来源、许可证、schema、mapping、
   directed-edge 内容和 bytes/SHA256 审计后才可解阻塞；文件名存在不算通过。
5. `contract_io.py` 已在独立的 pre-formal-analysis 包中实现并验证；当前写入与
   验证都要求 locked parent 的路径和 SHA256，并保护 cell/var/layers/raw/空间字段，
   同时采用 no-clobber 发布；它不改变本阶段 prior stop boundary，也不自动生成候选。

## Phase 0：任务激活与 ownership

- 激活 `T3-S1-PRIOR`，初始化其 artifact 目录，并保存本方案快照。
- 在 coordination status 登记本任务对 T3 专属实现文件的 lease；不修改已评分
  B2/P0 artifact。
- 记录父版本、配置 hash、允许网络/下载状态和本阶段预算。

## Phase 1：外部数据与方法的本地部署（授权下载后回到 cache-only）

- 输入数据只使用已审计的 B2 sanitized counts/meta/genes，并在部署报告中记录
  当前 SHA256；不读取 quarantine/raw 数据。
- 创建仓库内隔离环境 `.venvs/ve-t3-prior`，使用现有本地 Python/R 运行时和
  `--no-index`/本地路径安装；禁止隐式联网解析依赖。用户已授权的下载只用于
  明确锁定的 `genomepy`、`scTenifoldNet` 及其必要依赖；先复制到任务 deployment
  cache，再记录来源 URL、许可证、bytes、SHA256，安装时仍从本地 cache 复现。
- 从已锁定的 CellOracle 源归档做 `--no-deps` 本地安装/导入探测；从已锁定的
  scTenifoldKnk R 源归档做本地库安装或核对现有 `1.0.2`，并运行最小 synthetic
  smoke。所有失败必须写为 `NOT_DEPLOYED` 或 `NOT_TESTABLE`。
- 核对 decoupler 版本和实际 import 路径；它只能作为已存在的本地依赖，不能
  触发下载。
- 搜索并核验 CollecTRI/OmniPath 本地快照、版本、许可证/来源和 hash。缺失时
  记录 `BLOCKED_EXTERNAL_DATA`；只有取得可审计的固定快照后才进入补数。
- 生成 `deployment/deployment_report.json`、根目录 `TOOL_VERSIONS.json` 和日志，区分
  source archive、可导入 package、可执行 smoke、科学可用四种状态。最终
  `deployment_report.json` 为 `PASS`，且 `network_used=false`、
  `external_downloads_used=false`（下载在授权阶段预先完成）。

## Phase 2：接口、schema 与测试先行

- 将 prior schema 改为支持多 condition：顶层记录 `condition_ids`，每条 record
  必须带自己的 `condition_id`；保留 `KO_MINUS_MATCHED_WT` 符号定义。
- 为 `SignedPriorRecord` 补齐标准 provenance/conflict/source-family 信息，并
  保持 bounds、冲突时 sign=0、lineage gate 的 fail-closed 校验。
- 实现 `lineage_state_gate.py`：按 condition/state 输出可审计 gate，匹配失败
  不产生 prior residual。
- 实现 `perturb_prior_committee.py`：只做标准化投票、独立 evidence-family
  汇总、冲突处理、rank/confidence 和 caps；不在模块内读取 H5AD 或运行 scorer。
- 先补 source-only 单元测试：符号方向、重复 family 不计独立证据、conflict、
  lineage fail-closed、多 condition/dosage schema 和确定性排序；schema 还必须
  拒绝 `conflict_flag=true` 且 `sign!=0`。

## Phase 3：T3 适配与两条 lane

- 新增 T3-S1 专属 runner/adapter，把 B2 证据转换为标准字段；CellOracle 和
  scTenifold 仅作独立 vote 的输入，Mab21l2 known-KO 只作 validation-only，
  不参与 target sign/top-k/amplitude。
- L1 `STRICT_AGREEMENT`：两类独立 sign model 同号、directness/审计 signed edge、
  lineage gate、conflict=0、非零 cap 10%。
- L2 `CONDITION_AWARE`：按 state 排名，Gata4/Gata6 分开，beta-catenin 允许
  medium-path propagation，conflict=0、cap 25%，显式输出不确定性。
- 不把 lane 作为 evidence family；不把 directness 当作 sign 证据。
- 当前锁定 B2 lineage gate 只提供连续 lineage/marker probability；target expression、
  TF activity、pathway activity 在输出中显式记为 `NOT_AVAILABLE_IN_LOCKED_B2_GATE`，
  不做隐式填补。

## Phase 4：门禁与证据包

按任务契约生成 `source_votes.tsv`、`evidence.tsv`、`state_gate.tsv`、
`prior_L1.json`、`prior_L2.json`、`metrics/sign_convention_test.json`、
`known_ko_adapter_check.json`、`stability.json`、`gate_report.json`，以及
`METHOD_DISCLOSURE.md`、`DATA_SOURCES_USED.tsv`、`TOOL_VERSIONS.json`、
`config_resolved.yaml`、`MANIFEST.json`、`COMPLETION_REPORT.md`、`RESULT.md`、
`run.log`。

门禁必须明确：符号 convention、两类独立证据、directness、lineage/state、
conflict、cap、known-KO adapter 的 DES/DCS 不同时低于 identity、stability
以及外部数据可用性。任一核心链路无法执行则输出 `HOLD_AS_COMPONENT` 或
`BLOCKED_EXTERNAL_DATA`，不伪造 `PRIOR_GATE_PASS`。

## 验收、停止与后续接口

- 通过：输出可被后续 T3-S1B 消费的 prior/gate bundle；这不等于生物学结论或
  leaderboard improvement。
- 未通过但组件可审计：`HOLD_AS_COMPONENT`，保留完整原因、hash 和可复现命令。
- 外部数据/方法缺失：`BLOCKED_EXTERNAL_DATA`，`blocks_submission: false`；
  等待新授权或本地 cache，不扩大任务范围。
- 只有在 prior gate 明确 `PRIOR_GATE_PASS` 后，才规划 T3-S1B 的 H5AD 生成和
  local scorer；本轮到 prior/gate 即停止。

## 本次执行结果

- 软件部署：`PASS`；`genomepy`/CellOracle import、scTenifoldNet 1.4 与
  scTenifoldKnk 1.1 source-version match、synthetic smoke 均通过。
- 外部知识：CollecTRI 4,910 条和 OmniPath 2,553 条 mouse panel-scoped
  directed edges 均通过 TSV/schema、panel mapping、bytes/SHA256 审计；不是
  完整数据库，也未单独形成 beta-catenin 生物学结论。
- prior/gate：`HOLD_AS_COMPONENT`；31,458 条记录，L1/L2 非零
  2,050/5,125。当前 gate blocker 是 `PASS_WITH_SENSITIVITY`：任一模型
  family leave-one-out 都移除全部严格双 family consensus。
- 正式分析前闭合：5 个 P0 current parent 均通过新版 H5AD contract
  round-trip、protected-field 和 registry SHA256 复核；实际接口测试为
  `22 passed`，测试日志、输入文件和 adapter hash 见
  `artifacts/tool_integration/CONTRACT-PREFLIGHT-20260831-v2/`。
- 外部知识集成预检：CollecTRI 实际消费 21 条 Gata4、18 条 Gata6
  panel-edge；OmniPath 实际消费 1 条 Ctnnb1→Pitx2 directed path，证据见
  `artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3/`。快照
  来源、dataset、mouse taxon 和 license 元数据已做 fail-closed 检查；边的
  directness 与未校准 confidence 分开记录。该结果是
  `status=COMPONENT_PASS`、`candidate_admission_status=HOLD`、
  `scientific_validation_status=NOT_RUN`，没有 state join、prior promotion 或 H5AD。
- 稳定性补强：外部 edge 与现有模型族的方向重叠存在明显 discordance，且
  尚无 state-specific activity 验证；报告明确保持 `HOLD`，不把外部快照
  硬接成第三票，证据见 `artifacts/tool_integration/STABILITY-PREFLIGHT-20260831-v3/`。
- 停止边界：不生成 H5AD/候选，不调用 scorer，不上传；`blocks_submission: false`。
