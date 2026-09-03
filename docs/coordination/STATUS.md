# 当前并行状态

本文件是实时摘要。详细候选索引、服务器分数和科学/技术知识分别见权威文件，不在此重复维护完整历史。
人类快速入口是根目录 [`STATUS.md`](../../STATUS.md)；任务路线变更分别见 [`T1_TRACKING.md`](T1_TRACKING.md)、[`T2_TRACKING.md`](T2_TRACKING.md)、[`T3_TRACKING.md`](T3_TRACKING.md)。

<!-- ve-status:start -->
```yaml
schema: ve.parallel-status.v1
updated_at: "2026-09-04"
updated_by: coordinator

policy:
  competition_primary: true
  science_supporting_only: true
  science_gate_for_submission: false
  scored_artifacts_immutable: true
  update_mode: event_driven

workspace:
  integration_branch: master
  worktrees: pending_initial_commit

starter_pack:
  status: CLOSED_FOR_COMPETITION_BASELINE
  research_extension: OPEN_FOR_RESEARCH_EXTENSION
  closure_report: reports/STARTER_PACK_CLOSURE.md
batch1:
  status: CLOSED_FOR_REVIEW
  formal_atoms: 4
  final_artifacts: 16
  server_scored_artifacts: 16
  active_atom: null
  phase_report: reports/PHASE_REPORT_BATCH1_20260829.md
  release_changelog: reports/RELEASE_CHANGELOG_20260829.md
  next_action: "等待新的明确授权；不自动启动 B1-C1 或新的 atom"
batch3:
  status: COMPLETE
  routes_executed: 8
  active_atom: null
  phase_report: reports/PHASE_REPORT_BATCH3_20260904.md
  release_changelog: reports/RELEASE_CHANGELOG_BATCH3_20260904.md
  next_action: "等待 batch4 授权（LEADS L-002 首选）或封板；已关闭路线不追加微调"
data:
  challenge_manifest: data/MANIFEST.tsv
  auxiliary_links: 7
  auxiliary_model_input: false

leaderboard:
  total: 149.5
  T1: 48.5
  T2: 55.7
  T3: 45.3
  aggregate_basis: "149.5 is the current server-returned Total; displayed T1/T2/T3 and board values are rounded independently"
  evidence: reports/SERVER_SCORE_REGISTRY.md

tasks:
  T1:
    status: active
    dependencies: []
    owner: coordinator
    branch: master
    worktree: current
    current_best: "candidate/T1_val/v0004_strict_pseudobulk_shift"
    current_best_score: 48.5
    next_action: "HX-DYNAMICS-KILLTEST 已 REJECT（mioflow 0.7475 未优于 moscot 0.6645），增长/死亡动力学方向关闭；T1 无新授权前不追加 atom"
    blocker: null
    owned_paths:
      - "submissions/candidates/T1_*"
      - "scripts/t1_temporal_model.py"
      - "tests/test_t1_temporal_model.py"
      - "scripts/t1_mass_residual.py"
      - "tests/test_t1_mass_residual.py"
      - "outputs/t1_model/"
      - "artifacts/atomic_batch1/B1-A3/"

  T2:
    status: active
    dependencies: []
    owner: coordinator
    branch: master
    worktree: current
    current_best: "per-board selection: B1-A1 L1 embryo 60.1 + T2-J1 v0009 heart_interp 57.3 + baseline heart_extrap 50.5"
    current_best_score: 55.7
    current_best_score_basis: "current server-returned T2 task score; derived T2≈55.97 after heart_interp 57.3 promotion pending server confirmation"
    next_action: "T2-J1 heart_interp v0009 服务器 57.3（+0.6）晋级；batch3 剩余 HX-DYNAMICS-KILLTEST（单工具/单 board/单 kill metric，实例化后执行）"
    blocker: null
    owned_paths:
      - "submissions/candidates/T2_*"
      - "scripts/t2_*"
      - "outputs/t2_*"

  T3:
    status: hold_as_component
    dependencies: []
    owner: coordinator
    branch: master
    worktree: current
    current_best: "baseline-001/T3_gata4/v0001"
    current_best_score: 45.3
    active_atom: "T3-S1C-GATE-SATISFIABILITY-20260902-v1"
    next_action: "已完成 activity gate 与 firewall 的可满足性审计；当前判定为 UNSATISFIABLE_UNDER_FIREWALL。保持 S1C/S1D 为审计组件，不重跑 S1B、不搜索近 E8.75 target perturbation；只有正式 claim/contract 授权后才可执行限定为 WT-context/modelled response 的 S1C-C exact E8.75 atom"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    owned_paths:
      - "submissions/candidates/T3_*"
      - "scripts/t3_shift_transfer.py"
      - "scripts/t3_signed_response.py"
      - "tests/test_t3_shift_transfer.py"
      - "tests/test_t3_signed_response.py"
      - "artifacts/atomic_batch1/B1-A2/"
      - "outputs/t3_shift_transfer/"

blockers:
  - id: SCIENCE-PROMOTION-001
    scope: science
    blocks_submission: false
    status: open
    reason: "已有 E9.5 组织限定 direct-perturbation context，但仍缺少足以支持 E8.75 state-specific scientific promotion 的独立 signed-family 证据"
    unblock_condition: "获得并验证 E8.0-E9.5 目标状态匹配的独立 signed-family 证据，或明确降低科学声明范围"
    owner: coordinator
  - id: T3-TOOLCHAIN-001
    scope: toolchain_and_external_data
    blocks_submission: false
    status: resolved
    reason: "CellOracle/scTenifoldKnk 方法及 CollecTRI/OmniPath 外部知识快照的本地部署曾缺少固定依赖/审计证据"
    resolution: "用户授权后，固定依赖与必要依赖已 hash-lock；genomepy/CellOracle import、CellOracle mm10 base-GRN 本地 loader、scTenifoldNet 1.4 与 scTenifoldKnk 1.1 source-version match、synthetic smoke、OmniPath/CollecTRI 内容级快照审计均通过；network_used=true；完整 CellOracle runtime 仍单独记录"
    unblock_condition: "若上游版本或快照更新，重新执行相同来源、许可证、schema、mapping、内容和 SHA256 审计"
    owner: coordinator
  - id: T3-S1-PRIOR-GATE-001
    scope: prior_gate_and_scientific_interpretation
    blocks_submission: false
    status: open
    reason: "prior/gate 为 HOLD_AS_COMPONENT；任一模型 family leave-one-out 都移除全部严格双 family consensus，且当前 prior adapter 尚未消费 panel-scoped CollecTRI/OmniPath 生成 beta-catenin sign"
    unblock_condition: "获得独立可重复的 family/stability 证据，并在单独授权的 S1B 路线中完成 panel-scoped snapshot 集成、验证和不确定性记录"
    owner: coordinator
  - id: T3-S1A-RUNTIME-001
    scope: toolchain_and_external_data
    blocks_submission: false
    status: resolved
    reason: "T3-S1A v5 在 exact E8.75 输入和 state join 通过后，CellOracle Gata6/Ctnnb1 的 full matrix simulate_shift 超过 bounded runtime window"
    resolution: "v6 保持 exact 输入、GRN、simulate_shift 参数和 scTenifold 参数不变；CellOracle target 改为独立 fork worker、原子 checkpoint、60 分钟/target 窗口。Gata4 real API PASS；Gata6/Ctnnb1 明确返回 base-GRN regulator 不适用；三条 scTenifold route 输出完成。"
    unblock_condition: "不适用；运行层阻塞已收口，剩余问题转入 T3-S1A-GATE-001"
    owner: coordinator
  - id: T3-S1A-GATE-001
    scope: scientific_validation_and_route_gate
    blocks_submission: false
    status: open
    status: open
    reason: "v7 exact input/state join PASS；S1B v3 已完成 full snapshot identity、external contextual integration、conflict audit 和 family-native LOFO；S1C target-compatible adapter/smoke 已通过方法边界；S1D v3 的三个 E9.5 context 仍非 E8.75 state-matched activity。进一步的 gate 可满足性审计判定旧 target-specific activity 要求与现行 firewall 不具备足够交集，biological activity 仍 NOT_VALIDATED，signed-family stability NOT_IDENTIFIABLE，四条 route 均 HOLD"
    unblock_condition: "获得 organizer/contract-owner 对合法 state-matched evidence 的书面许可，或正式建立新版本 claim/route gate；新版本必须保留 firewall、method、无泄漏和明确的 WT-context 语义，不得用 proxy、降采样或未等价替代解除旧 gate"
    owner: coordinator

leases: []
handoffs:
  - task: T2
    atom: B1-A1
    status: complete
    final_artifacts: 6
    candidate_ids: "见 submissions/INDEX.tsv 与 docs/coordination/DECISIONS.md 的 D-20260827-001"
    parents: "embryo/extrap: baseline-001；heart interpolation: submission-002/v0002"
    artifacts: "六个路径与 SHA256 以 submissions/INDEX.tsv 为准"
    checks: "6/6 contract pass；X、obs/var order、空间 shape、15-NN 全通过；target_used=false；服务器分数 6/6 已登记"
    risks: "heart extrapolation 两条 lane 均低于 parent；不作因果声明"
    recommended_decision: "L1 按 board 保留；L2 作为同批已评分第二候选和审计备份保留"
    blocker: null
    action: "B1-A1 完成；后续转入经授权的新 atom"
  - task: T3
    atom: B1-A2
    status: diagnostic_hold
    final_artifacts: 2
    candidate_ids: "B1-A2-L1-T3_gata4, B1-A2-L2-T3_gata4；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T3_gata4/v0001"
    artifacts: "artifacts/atomic_batch1/B1-A2/final/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract/invariant pass；7,449×500；target_used=false；上传文件 SHA256 与索引一致；Mab21l2 self-check 与公开 proxy 已完成；服务器 2/2 已登记"
    risks: "两条 WT-only signed-response 路线均低于 baseline；L1=44.7，L2=44.0；self-check 与公开代理显示响应方向和分布损伤"
    recommended_decision: "保留两份不可变候选供失败诊断；不进入 B1-A3，不新增候选"
    blocker: null
    action: "B1-A2 失败原因已归档；保持 T3 diagnostic_hold，不新增候选"
  - task: T2
    atom: B1-A4
    status: complete
    final_artifacts: 6
    candidate_ids: "B1-A4 双 lane × 三 board；详见 submissions/INDEX.tsv"
    parents: "B1-A1 immediate parents；heart extrapolation 使用 baseline-001"
    artifacts: "artifacts/atomic_batch1/B1-A4/final/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "6/6 manifest/schema/invariant pass；X/layers/raw/obs replay、坐标、15-NN、SHA256 均通过；local public proxy 6/6 complete；服务器 6/6 scored；target_used=false"
    risks: "服务器结果为 embryo 59.3/59.2、heart interpolation 56.3/56.3、heart extrapolation 50.0/49.9；仅 heart interpolation 持平当前 best，其余低于当前 best"
    recommended_decision: "六份 scored artifact 保持不可变；不提升 B1-A4，不追加 C1 重复缩放或新的 T2 atom"
    blocker: null
    action: "B1-A4 评分已回填 reports/SERVER_SCORE_REGISTRY.md；维持当前 per-board selection，等待新的授权"
  - task: T1
    atom: B1-A3
    status: complete
    final_artifacts: 2
    candidate_ids: "B1-A3-L1_SHARED_UNRESOLVED-T1_val, B1-A3-L2_E95_EXPRESSION_PROBE-T1_val；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T1_val/v0001"
    artifacts: "artifacts/atomic_batch1/B1-A3/final/；候选哈希以 submissions/INDEX.tsv 为准"
    checks: "2/2 contract/protected checks pass；5,118×32,285；source-only partition coverage 100%；target_used=false；row replay exact"
    risks: "E8.5/E9.5 label vocabulary is not harmonised；L2 expression projection is a source-only hypothesis；locked full-panel local scorer timed out on L1；L2 attempt produced no result and was interrupted；no substitute scorer"
    recommended_decision: "L2=47.7 高于 L1=47.5，为 B1-A3 lane winner；两者均低于历史 v0004=48.5，保留两份 artifact 不可变"
    blocker: "local_scorer_incomplete; blocks_submission: false"
    action: "B1-A3 完成；新授权 atom 前不追加 T1 调参"
  - task: T3
    atom: B2-T3-A1
    status: HOLD_AS_COMPONENT
    final_artifacts: 2
    candidate_ids: "B2-T3-A1-L1_STRICT_WT_DIRECT-20260830, B2-T3-A1-L2_GATA4_GATA6_CONDITION_AWARE-20260830；详见 submissions/INDEX.tsv"
    parents: "baseline-001/T3_gata4/v0001"
    artifacts: "artifacts/atomic_batch2/B2-T3-A1/；canonical candidate 与 SHA256 以 submissions/INDEX.tsv 为准"
    checks: "2/2 7,449×500 contract/protected PASS；Gata4/Gata6 lineage gate；target_used=false；每 lane 一次 local scorer；manual-upload package 已生成"
    risks: "E-MTAB-11763 为 metadata-only fallback；CellOracle/scTenifoldKnk 为本地可审计近似实现而非上游包执行；local 分数是 Mab21l2 source-only 诊断，不是 Gata4 leaderboard 分数"
    recommended_decision: "两条均保持 score_pending，不自动上传；作为独立 component 候选等待人工选择"
    blocker: null
    action: "停止在 B2-T3-A1；不启动下一个 atom，等待人工上传决定或新授权"
  - task: T3
    atom: T3-S1-PRIOR
    status: HOLD_AS_COMPONENT
    final_artifacts: 4
    candidate_ids: "none；本任务仅 prior/gate bundle，不生成候选"
    parents: "P0-LOCK；复用 immutable artifacts/atomic_batch2/B2-T3-A1"
    current_artifacts: "T3-S1-PRIOR MANIFEST SHA256 7ed19bda38b6362da1bb1051c865ca362cc33b53aa52bb831e32313c1447bc35；gate_report SHA256 69c1ffbd25039cb467865f2d7670c58dce58a7fe3efa48cba1e00195761f25e1；contract-preflight SHA256 67c38f32c4576b31a5b516495e046a7f0017d989217fe182ef9694bcec79c2a5；T3-S1B knowledge preflight SHA256 a41db892e852d9da794277eb8093c0bbfba7b52cc04d45bd4f93751dcda21632；stability preflight SHA256 3f96627ffa866c0ad17d51537f08c0ed7a36db8f06c4664f08b3fff6685213c8"
    current_checks: "5 个 current parent contract/registry SHA256、protected-field 和 round-trip PASS；实际 contract/interface tests 22 passed；deployment 与双源 snapshot audit PASS；directed integration preflight COMPONENT_PASS 但 candidate admission HOLD；scientific validation NOT_RUN；prior gate HOLD"
    historical_artifacts: "artifacts/tool_integration/T3-S1-PRIOR/；MANIFEST.json SHA256 30100e641107fc283dc0cb3275a9ec9205b989dae751f070cd87a2c9cb0a11b8；deployment_report.json SHA256 63d43571b85b5f711bedb460611ed671fd217b06f109ea45af8c79a52889ffa8；gate_report.json SHA256 4145bb01f7dfda28d0f80c8ad97ca50dc78c6a5ffe62b63fbecbe9b0bbaf32d5"
    historical_checks: "deployment PASS；genomepy/CellOracle import PASS；scTenifoldNet 1.4 与 scTenifoldKnk 1.1 source-version match；synthetic smoke PASS；CollecTRI 4,910 与 OmniPath 2,553 directed edges 内容级审计 PASS；接口测试 11 passed；输入锁定哈希全部匹配"
    risks: "gate HOLD_AS_COMPONENT；PASS_WITH_SENSITIVITY，移除任一 model family 后严格双 family consensus 全部消失；外部 edge 与现有模型族存在方向 discordance，且尚无 state-specific activity 验证；无 beta-catenin 生物学结论"
    recommended_decision: "contract 与外部 directed-evidence preflight 已闭合为可复用组件；仍不生成 H5AD/候选，不上传；若继续，单独激活 S1B state join、冲突处理和独立稳定性验证"
    blocker: "T3-S1-PRIOR-GATE-001; blocks_submission: false"
    action: "T3-S1-PRIOR 完成当前边界；最终 provenance-snapshot 版 contract-preflight、directed-evidence preflight 和 stability reinforcement 已写入；等待独立 stability 证据与 S1B 路线授权"
  - task: T3
    atom: T3-S1A-STATE-JOIN-20260901-v6
    status: BLOCKED
    final_artifacts: 5
    candidate_ids: "none；本 atom 仅执行 exact input/method/gate，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260831-v5；T3-S1-PRIOR immutable inputs"
    current_artifacts: "tool_execution.json SHA256 3dec70dc5bb9f1a4ffab747962768846ce650dc730c5ca1c5cc50e3b18c4d988；gate_report.v2.repaired.json SHA256 92560f5d2b5caf49b8a0160d2828fb7dcb4a591a859702c16d0a0ad03087481b；artifact_manifest.stable.json SHA256 ff0d8f323f2da369b26c5c9553ea9d230eb9804b88a7fe82cf06e4daeee16e30；route_artifact_repair.json SHA256 046c17369a51c043bb7fedb8ada8952a912501138710fa4cde9794ae75b6e03e；Gata4_votes.tsv SHA256 7d08cb82326b91c6ff5ceb2121026a3d8097f8174d36e8078a608a5eea6de724"
    current_checks: "exact input/state join PASS；Gata4 CellOracle real API PASS；Gata6/Ctnnb1 当前 base GRN 明确不适用；三条 scTenifold 输出完成；45 个接口/状态测试 PASS；py_compile PASS；修复后 hash-bound route audit PASS；全局 outcome/status BLOCKED，四路为 2 HOLD + 2 BLOCKED"
    risks: "state activity 为 NOT_VALIDATED；selected-gene/evidence-family stability 不可识别；v6 历史报告保留 Gata6/Ctnnb1 的实际 BLOCKED_TOOLCHAIN 标签；不能据此生成候选或宣称 leaderboard 改进"
    recommended_decision: "接受 v6 作为运行阻塞修复和审计组件；保持 candidate_generation/server_submission 关闭，后续单独解决 target-compatible GRN/applicability 与 state-specific activity/stability"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；等待下一项明确授权"
  - task: T3
    atom: T3-S1A-STATE-JOIN-20260901-v7
    status: HOLD_AS_COMPONENT
    final_artifacts: 8
    candidate_ids: "none；本 atom 仅完成 exact state-response/coverage 与 route gate 复核，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v6；T3-S1-PRIOR immutable inputs"
    current_artifacts: "tool_execution.json SHA256 368da3d484da99ef6227a7a8078b8fcc3c2c792377ea670fe985c678641eb15b；gate_report.v2.repaired.json SHA256 dfe522011bc3c198d30fc9f483f3b6e8842922c4f1f596713c7762c80095c8e5；artifact_manifest.stable.json SHA256 22d785ea59a85d13529db8896772ccdee5f79b95c4cd557bfabfff0897109db8；route_artifact_repair.json SHA256 6c2302c371cd3bf38cc96239a8847cb7bc22849fcb8e219fd79f1c8b2c129e3a；state_response_support.json SHA256 1bc9dfdb74ac386dbcd9de84919855199fb4c5ec384725cf3976f78ef964964c；Gata4_votes.tsv SHA256 8f0e3ba674b6bad13912905c66f3e37569e6edc8d624b0851fd2e121ff242578；Gata4_state_response.tsv SHA256 36588d3912264256469acbd868af8631af9595286d8d56460a92ea60884f56a2；Gata4_state_coverage.tsv SHA256 fd0c5a040753c3d7e4d4ea54ba0e5e7884dd3fdd202bfe5a00b2d74211ebd997；deployment manifest SHA256 8ee0fd511f8b03d4ea4e09bd9d1348beb7da49bec266640dd5fdacbcbc30a949"
    current_checks: "exact input/state join PASS；CellOracle PASS（Gata4=PASS，Gata6/Ctnnb1=NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT）；三条 scTenifold 输出均 PASS_UNSIGNED_RANK_ONLY；state-response support 为 NOT_IDENTIFIABLE（23 个 required mapped states 中 12 个通过、11 个 HOLD），claim=MODELLED_STATE_RESPONSE_ONLY，biological_activity=NOT_VALIDATED；GATA selected-gene stability PASS、BETA 因无适用 CellOracle target 保持不可识别；48 项接口/状态测试 PASS；py_compile PASS；223-file stable manifest 无 transient；hash-bound route audit PASS；全局 HOLD_AS_COMPONENT，四路均 HOLD"
    risks: "仍缺 biological activity 验证；Gata4 state response 只支持 modelled response，且存在映射碰撞与 11/23 mapped state 的 within-state sign stability 缺口；scTenifold 仅 unsigned rank evidence；Gata6/Ctnnb1 当前 base GRN 不适用；不能据此生成候选或宣称 leaderboard 改进"
    recommended_decision: "接受 v7 作为 applicability、state-response coverage 和 route-gate 审计组件；保持 candidate_generation/server_submission 关闭，后续仅在 target-compatible GRN 或独立 activity/stability 证据明确后复核"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；下一步处理可审计的 biological activity/stability 证据边界"
  - task: T3
    atom: T3-S1B-STATE-JOIN-20260901-v2
    status: HOLD_AS_COMPONENT
    final_artifacts: 27
    candidate_ids: "none；本 atom 仅完成 external contextual integration、conflict audit、LOFO 与四路 claim vector，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7"
    current_artifacts: "artifact_manifest.stable.json SHA256 239e5c474986cb54e70d5b1451330a20350be38fadaf7641c1e2177b2aea34ea；gate_report.v2.json SHA256 1d10e15b2be52eddd9693cbf84791e0ba66614359468c5708b844b96254f89f0；state_join_audit.json SHA256 0c5dc8bc03419e678b842ffa5dc82c2050626d795c77d0ff7e884d7d5f58e366；stability_s1b.json SHA256 19c32d6b65778a8696d1699055791f15e4ceab6e47679e8d88f8481f3de23c64；source_votes.tsv SHA256 fb26e8424a270f48a3fc7cbd6650e395edaedaea007a4cd3ebe499a4680c4a7e"
    current_checks: "parent 223-file stable manifest 与 CollecTRI/OmniPath full snapshot identity PASS；external raw 128、state-joined 5808、source 137148；external 全部 GLOBAL_CONTEXTUAL/SUPPORTING_KNOWLEDGE 且 activity_eligible=false；4/4 route HOLD、selected signed records=0；53 项回归测试 PASS；stable manifest 自校验 PASS"
    risks: "S1B 不是 biological activity validation；external evidence 不计为 independent signed family；9 个 external-state mapping collision 保留在 audit；Gata6/Ctnnb1 不会因 contextual evidence 恢复为 CellOracle-applicable；S1B v1 的封装失败 receipt 保留但不可复用"
    recommended_decision: "接受 v2 为可复用的 contextual/provenance 审计组件；保持 candidate_generation/server_submission 关闭，不写入 submissions/INDEX.tsv 或服务器 registry"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；下一步只处理独立 biological activity/stability 证据或另行授权 target-compatible GRN atom"
  - task: T3
    atom: T3-S1B-STATE-JOIN-20260901-v3
    status: HOLD_AS_COMPONENT
    final_artifacts: 27
    candidate_ids: "none；本 atom 仅完成 external contextual integration、conflict audit、LOFO 与 provenance lock，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7"
    current_artifacts: "artifact_manifest.stable.json SHA256 396b15d976e10700709c7628539dd2e9cac21b66612d9b72faa772921413744e；gate_report.v2.json SHA256 a4be63a1653353b238ce5cb29436cea834e438d9b2a3a3e85cb467d121d00e21；implementation SHA256 cd480790fa6cbf7e6618ec28675983143466788847e79e73040d63df7dfe9d8c；input_lock.json SHA256 7920f7f960cb298d5deabb6e30b298f16480b89b2054eae976514be51f519859"
    current_checks: "parent 223-file stable manifest 与 CollecTRI/OmniPath full snapshot identity PASS；external raw 128、state-joined 5808、source 137148；external 全部 GLOBAL_CONTEXTUAL/SUPPORTING_KNOWLEDGE 且 activity_eligible=false；4/4 route HOLD、selected signed records=0；53 项回归测试 PASS；独立 tester 5 S1B + 34 interface tests PASS；script/artifact/input lock SHA 一致；stable manifest 自校验 PASS"
    risks: "biological_activity_status=NOT_VALIDATED；signed-family stability=NOT_IDENTIFIABLE；external evidence 不计为 independent signed family；9 个 external-state mapping collision 保留在 audit；Git commit 锚点仍不可用"
    recommended_decision: "接受 v3 为当前可复用审计组件；保持 candidate_generation/server_submission 关闭，不写入 submissions/INDEX.tsv 或服务器 registry"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "不生成 H5AD/候选、不运行 scorer、不上传；下一步只处理独立 biological activity/stability 证据或另行授权 target-compatible GRN atom"
  - task: T3
    atom: T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1
    status: PASS_COMPONENT_HOLD
    final_artifacts: 11
    candidate_ids: "none；本 atom 仅构建 target-compatible TFdict adapter，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3"
    current_artifacts: "artifact_manifest.stable.json SHA256 6700b919cba382475cbd6a1c3bee0dd8af5271685285c18011c4e3bab8e8706c；augmented_tfdict.json SHA256 29ecc5bf4c4ff24ee5adf8c7ca6dfe14fb6026eb49678c9c3f8cdc9953785050"
    current_checks: "Gata4/Gata6/Ctnnb1 source membership 3/3 PASS；Gata6 18 个一跳 CollecTRI relation、Ctnnb1 1 个严格一跳 OmniPath relation；clean rerun payload 哈希一致；method_source_compatibility=PASS"
    risks: "仅证明接口/source membership；biological_activity=NOT_VALIDATED、state_specificity=NOT_EVALUATED、signed_family_stability=NOT_IDENTIFIABLE；不把外部 sign 注入 TFdict"
    recommended_decision: "接受为可复用方法组件；不直接进入 S1A/S1B biological gate，不生成候选、不上传"
    action: "等待 matched activity/stability 证据后另行授权 exact E8.75 full rerun"
  - task: T3
    atom: T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v2
    status: PASS_COMPONENT_HOLD
    final_artifacts: 7
    candidate_ids: "none；本 atom 仅执行 synthetic structural smoke，不生成候选"
    parents: "T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1"
    current_artifacts: "artifact_manifest.stable.json SHA256 806bf41acadfb9b5dc0d0b2329b36e1848b390231c573edcf8ec5e8e8ac0c817；target_results.json"
    current_checks: "真实 CellOracle 0.22.0 TFdict import/fit/simulate；Gata6/Ctnnb1 2/2 PASS；各 24×20、delta_x finite；runtime cache/config 写入 atom 内"
    risks: "synthetic fixture 无生物样本、sign、rank 或 state response；S1C-B/v1 Gata4 fixture 边界失败 receipt 保留且不可复用"
    recommended_decision: "接受 v2 为 source adapter smoke 组件；不作 activity 或模型效果证据"
    action: "不生成 H5AD/候选、不运行 scorer、不上传"
  - task: T3
    atom: T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1
    status: HOLD_INSUFFICIENT_MATCHED_ACTIVITY_EVIDENCE
    final_artifacts: 8
    candidate_ids: "none；本 atom 仅审计外部 perturbation context，不生成候选"
    parents: "T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3"
    current_artifacts: "artifact_manifest.stable.json SHA256 9017b2db83c09a776c8c1620f8ca00c6740f3c1d288ed857d9635c1b30f42fdf；processed_effects.json；evidence_inventory.tsv"
    current_checks: "GSE156307 Gata4 E14.5 HS log2FC=-1.1839、5/5 方向一致；GSE255237 Gata6 E11.5 OFT log2FC=-0.3362、4/4 方向一致；metadata PASS；E8.75 matched activity NOT_IDENTIFIABLE；independent signed family=0"
    risks: "两个 processed 文件均为 off-target stage/tissue；GSE255237 存在系列设计与文件列数冲突；raw 未下载；不能迁移为 E8.75 sign/activity 或 server improvement"
    recommended_decision: "接受为 context-only 证据，保持全局 HOLD_AS_COMPONENT；不写入 challenge input、submissions/INDEX.tsv 或 server registry"
    action: "继续寻找 E8.0-E9.5 matched tissue/state 且至少两个 biological replicates 的 target-specific perturbation"
  - task: T3
    atom: T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3
    status: PASS_COMPONENT_HOLD
    final_artifacts: 7
    candidate_ids: "none；本 atom 仅执行 synthetic structural smoke，不生成候选"
    parents: "T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1"
    current_artifacts: "artifact_manifest.stable.json SHA256 7770e075838309af5d339506b02e7975459aa651deb8d10f4079f25fec9c822d；target_results.json"
    current_checks: "真实 CellOracle 0.22.0 TFdict import/fit/simulate；Gata6/Ctnnb1 2/2 PASS；各 24×20、delta_x finite；进程退出后 stable manifest 7/7 文件 bytes/SHA PASS；runtime cache/mpl/numba 与 SQLite sidecar 明确排除"
    risks: "synthetic fixture 无生物样本、sign、rank 或 state response；v1/v2 失败或不可复用 receipt 保留且不可作为当前版本"
    recommended_decision: "接受 v3 为 source adapter smoke 组件；不作 activity 或模型效果证据"
    action: "不生成 H5AD/候选、不运行 scorer、不上传"
  - task: T3
    atom: T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3
    status: HOLD_EXACT_STAGE_CONTEXTUAL_ACTIVITY_NOT_STATE_MATCHED
    final_artifacts: 14
    candidate_ids: "none；本 atom 仅审计 exact-stage 外部 perturbation context，不生成候选"
    parents: "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v2；T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3"
    current_artifacts: "artifact_manifest.stable.json SHA256 6c2806aa381f099e3db88f38a35278d4500e1aeb1f8de7fe3cfa20e2db487e0c；gate_report.json SHA256 3da93e810aadf90769eb8e2eac1fd1fd35b41d9a3737aa01350bb1187e9c2579；contract SHA256 3cafa6d040caec2110a304cb260ef0c4a574aed51292748aff2aa017e3fd8267"
    current_checks: "GSE5298/GSE9652/GSE78125 matrix gzip、45101x8/45101x11/35556x24 shape、GSM group identity、GPL1261/GPL6246 probe/Entrez mapping PASS；Gata4 two early families、Ctnnb1 one AHF family、Gata6 zero；4 targeted tests PASS；核心输出 deterministic rerun PASS"
    risks: "E9.5 AVC/pooled heart/AHF tissue context 不能外推为 E8.75 state-specific activity；Gata4/Ctnnb1 target probe expression 不作为 functional gate；无 state-specific signed gene set 或 independent signed-family stability；无 raw CEL；不能宣称候选或 leaderboard 改善"
    recommended_decision: "接受 v3 为 exact-stage contextual evidence 组件；v2 初步原子保留但不复用；不写入 challenge input、submissions/INDEX.tsv 或 server registry"
    blocker: "T3-S1A-GATE-001; blocks_submission: false"
    action: "继续寻找真正 E8.0-E9.5、目标状态匹配且可复现的 signed-family 证据；在此之前不启动 E8.75 全量推断"
  - task: T3
    atom: T3-S1-CLOSURE-20260902-v1
    status: CLOSED_AS_RESEARCH_COMPONENT
    final_artifacts: 1
    candidate_ids: "none；纯文档收口，无新计算"
    parents: "T3-S1A-STATE-JOIN-20260901-v7；T3-S1B-STATE-JOIN-20260901-v3；T3-S1C-A/v1；T3-S1C-B/v3；T3-S1D/v3"
    current_artifacts: "artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md"
    current_checks: "五组件证据链 SHA 抄录完毕；三条未满足硬条件（signed family<2、E8.75 activity NOT_IDENTIFIABLE、stability 未闭合）与最小解锁条件已写死；与同日 T3-S1C-GATE-SATISFIABILITY 的 UNSATISFIABLE_UNDER_FIREWALL 结论一致"
    risks: "无；不改变任何已登记分数与历史 artifact；T3 best 仍为 45.3"
    recommended_decision: "接受收口；重开条件见 CLOSURE_REPORT 第 6 节；执行资源切换 T1-PRE-HARMONIZE"
    blocker: null
    action: "不生成 H5AD/候选、不运行 scorer、不上传；blocks_submission: false"
  - task: T1
    atom: T1-PRE-HARMONIZE-20260902-v1
    status: STATE_GATE_PASS_AND_FULL_PANEL_SCORER_PASS
    final_artifacts: 15
    candidate_ids: "none；本 atom 只建立词表/crosswalk/验证链，不生成正式候选"
    parents: "P0-LOCK；parent candidate/T1_val/v0004_strict_pseudobulk_shift（只读，SHA 与 P0-LOCK 一致）"
    current_artifacts: "artifacts/tool_integration/T1-PRE-HARMONIZE-20260902-v1/；stable manifest SHA256 e2f2889081d8bfffffe3111eb8cd024882c98d3304519618a964518b74698413；实现脚本 scripts/t1_pre_harmonize.py SHA256 5c2fed4c3d5c941819170dcf21d08dd540d38abb07c52347ff530318120add75"
    current_checks: "28 个 union fine_state（11 SHARED_EXACT/7 SOURCE_ONLY/10 TARGET_ONLY）；crosswalk 前向 13/18 解析、5 UNRESOLVED，反向 3/10、7 UNRESOLVED，无强配；stability 预声明一次（非 exact 边 bootstrap 0.40-0.50 已如实记录）；source-only pseudo-holdout projection 经锁定 full-panel scorer 实测 exit 0、323s、meta 三项校验全过；15 项新测试+103 全量回归 PASS；未触 E10.5/E12.5"
    risks: "pseudo-holdout 分数（de_score 0.6226）只验证表示与验证链，不是 leaderboard preview；wrapper 首版 RSS 采样只覆盖 supervisor 进程（已修为进程树合计，后续运行生效）"
    recommended_decision: "接受为 T1-S2-MOSCOT-DECODER 的前置组件；T1-S2 需单独授权"
    blocker: null
    action: "不生成正式候选、不上传；等待 T1-S2 授权"
  - task: T1
    atom: T1-S2-MOSCOT-DECODER-20260902-v1
    status: SCORED_REJECTED
    final_artifacts: 44
    candidate_ids: "T1-S2 v0007 (L1_EMPIRICAL_RESIDUAL, server 44.9)、v0008 (L2_MODULE_SCDESIGN3, server 44.8)；submissions/INDEX.tsv 已回填 scored/registered"
    parents: "T1-PRE-HARMONIZE-20260902-v1；candidate/T1_val/v0004_strict_pseudobulk_shift"
    current_artifacts: "artifacts/tool_integration/T1-S2-MOSCOT-DECODER-20260902-v1/；stable manifest SHA256 前缀 461fb3378ce4f9dc；实现 scripts/t1_s2_moscot_decoder.py；v0007 SHA256 4297f3fd344d4592eaf2176caa7f28b03148993aa1bbbcc52c6156f0b121d866；v0008 SHA256 d664db404418fe8558dbe9a966352921c2498e74343318e0f8c9c08ff9774280"
    current_checks: "moscot 0.5.2 coupling converged（234 非零 transition，主通量 lineage 内）；mass 21 state 归一化+clip/收缩；alpha=1.0127 一次解析冻结；双 lane 5118×32285 contract PASS、protected checks 全 PASS；formal scorer pseudo-target E9.5 双 lane exit 0；17 测试 PASS、manifest 自校验 PASS；服务器 v0007=44.9、v0008=44.8（2026-09-03 回填 reports/SERVER_SCORE_REGISTRY.md）"
    risks: "pseudo-holdout parent 臂占优已获服务器印证：结构化 moscot 外推在 E10.5 未胜 strict shift（-3.6/-3.7），且低于 copy_last baseline 47.0；本地 pseudo-target 分数不构成 leaderboard 证据"
    recommended_decision: "REJECT 为 leaderboard 改进，T1-S2 路线关闭；两份候选保留不可变做失败诊断；T1 best 仍为 v0004=48.5，不追加 T1 调参"
    blocker: null
    action: "链关闭；执行资源转向 T2-S3-SHAPE-FIELD"
  - task: T2
    atom: T2-S3-SHAPE-FIELD-20260903-v1
    status: SCORED_PARTIAL_PROMOTION
    final_artifacts: 157
    candidate_ids: "embryo v0006(L1, server 59.7 rejected)/v0007(L2)、heart_interp v0007(L1, server 56.7 PROMOTED)/v0008(L2)、heart_extrap v0006/v0007（本地 REJECT 不上传）；INDEX.tsv 已回填"
    parents: "embryo/heart_interp: B1-A1-L1；heart_extrap: baseline-001-v0001"
    current_artifacts: "artifacts/tool_integration/T2-S3-SHAPE-FIELD-20260903-v1/；stable manifest SHA256 4ffef666e95f9046811346e1d940fde322de9dca53f06f7c4055a8a1051f8a76；实现 scripts/t2_s3_shape_field.py"
    current_checks: "6/6 候选 contract PASS、表达/obs/var/gene order hash 不变、RMS 回锁在 P0 容差内；holdout L1: H1/H2 全胜、H3/H4 全负；L2: 4/4 全负、heart_extrap kNN CATASTROPHIC；服务器（2026-09-03）：embryo 59.7（-0.4 rejected）、heart_interp 56.7（+0.4 new board best）；14 测试 PASS、manifest 自校验 PASS"
    risks: "embryo H1 全胜但服务器 -0.4，印证窄间隔 holdout 获益不保证 board 获益；derived T2≈55.8/Total≈149.6 待服务器页面确认，不得引用为服务器值"
    recommended_decision: "heart_interp 56.7 晋级当前 selection；embryo 保留 B1-A1 L1=60.1；4 条 REJECT 候选不可变保留不上传"
    blocker: null
    action: "已完成评分回填；下一方向 T2-J1 FGW assignment candidate"
  - task: T2
    atom: T2-J1-PROXY-20260903-v1
    status: J1_PROXY_PASS
    final_artifacts: 46
    candidate_ids: "none；条件 gate atom，不生成候选"
    parents: "B1-A4 结果引用；T2-S3-SHAPE-FIELD-20260903-v1（执行序）"
    current_artifacts: "artifacts/tool_integration/T2-J1-PROXY-20260903-v1/；stable manifest SHA256 b5e2abe2718f4708363df4189088071e29f6ad6d52007f22ffcb68565511b751；实现 scripts/t2_j1_proxy.py"
    current_checks: "FGW objective spec 先冻结（SHA256 4cf86109…）；2 独立 holdout 同向改善（NFS-like 0.012/0.015 vs random 0.137/0.172，64 随机无一更优）；label-only/scrambled-reference null 均差于 random；行序不变性 abs diff=0；14 测试 PASS、148 全量回归 PASS"
    risks: "heart holdout 逐位置 pearson 为负（参考跨 1.25 天、标签交集仅 5），heart 参考构建需审视；source-only 第 4 层证据，不构成 leaderboard 宣称"
    recommended_decision: "J1_PROXY_PASS；可另行授权 FGW assignment candidate（先审视 heart 参考）"
    blocker: null
    action: "不生成候选、不上传；等待授权"
  - task: T2
    atom: T2-J1-FGW-ASSIGNMENT-20260903-v1
    status: SCORED_PARTIAL_PROMOTION
    final_artifacts: 40
    candidate_ids: "T2:embryo:val_interp v0008 j1_fgw_assignment（HOLD_AS_COMPONENT）、T2:heart:val_interp v0009 j1_fgw_assignment（READY 弱置信）；详见 submissions/INDEX.tsv"
    parents: "embryo v0002 g1_formal_log_rms（60.1）；heart_interp v0007 t2_s3_l1_pycpd（56.7）；objective 继承 T2-J1-PROXY-20260903-v1 冻结 spec 4cf86109"
    artifacts: "artifacts/tool_integration/T2-J1-FGW-ASSIGNMENT-20260903-v1/；候选 SHA256 以 submissions/INDEX.tsv 为准（embryo 81442478…、heart 4f2e7552…）"
    checks: "heart 参考审视按预声明标准 PROCEED（跨度 0.50、标签交集 33、探针弱正 +0.0138）；全量 FGW 无子采样；column_argmax_margin_greedy_v1 双射 PASS（conflicts 72.2%/73.3%）；objective 同靶 embryo −12.2%、heart −26.6%；contract 2/2 PASS、protected 2/2 PASS（坐标/obs/var/kNN 图/表达 multiset 精确一致）；重跑字节一致；40 文件 manifest 自校验 PASS；14 新测试 + 162 全量回归 PASS"
    risks: "heart morans_I_agreement 同靶 0.7365→0.6743 变差（已声明）；embryo NFS 镜像 no_improvement 0.0312→0.0344 且 bracket 探针为负；训练期 pseudo-target 循环论证；本地证据非 leaderboard 证据"
    recommended_decision: "heart_interp v0009 READY_FOR_MANUAL_SUBMISSION（弱置信，是否消耗提交由用户决定，不自动上传）；embryo v0008 HOLD_AS_COMPONENT 不可变保留"
    blocker: null
    action: "服务器仲裁（2026-09-04 回填，行 2026-09-03 19:51）：heart_interp v0009=57.3（+0.6 vs v0007 56.7）晋级 board best 与当前 selection；embryo v0008 未上传保持 HOLD；derived T2≈55.97/Total≈149.8 待服务器页面确认；batch3 剩余 HX-DYNAMICS-KILLTEST"
  - task: T1
    atom: HX-DYNAMICS-KILLTEST-20260904-v1
    status: REJECT
    final_artifacts: 18
    candidate_ids: "none；kill test 只出 report，不生成候选"
    parents: "candidate/T1_val/v0004_strict_pseudobulk_shift（只读）；双臂复用 T1-PRE-HARMONIZE-20260902-v1 与 T1-S2-MOSCOT-DECODER-20260902-v1 冻结 artifact"
    artifacts: "artifacts/tool_integration/HX-DYNAMICS-KILLTEST-20260904-v1/；stable manifest 18 文件自校验 PASS；实现 scripts/hx_dynamics_killtest.py + scripts/hx_mioflow_worker.py"
    checks: "一次性固定部署 mioflow==0.1.14（wheel/sdist SHA256 核验、Yale 非商业许可披露、56 包依赖快照）；kill metric 定义先于运行写死（config 04:15 早于训练产物 05:06）；MIOFlow 一次训练 wall 2747s<7200s cap、库默认超参无搜索；三臂 L1：parent 1.1894 / moscot 0.6645 / mioflow 0.7475；12 新测试 + 174 全量回归 PASS"
    risks: "E9.5 是训练期 stage，holdout 只验证假设机制、非 leaderboard preview；mioflow 上游 growth_rate 导入损坏以 sys.modules 别名绕过（源码未改，已记录 deviation）"
    recommended_decision: "REJECT（预声明阈值未达成：未严格优于 moscot 臂）；moscot mass 质量不是 T1-S2 失败点，增长/死亡动力学方向关闭；不生成候选、不上传"
    blocker: null
    action: "kill test 收口；batch3 全部任务执行完毕；T1 无新授权前不追加 atom"
```
<!-- ve-status:end -->

## 人类快速阅读

| 任务 | 当前状态 | 当前最佳 | 下一动作 |
|---|---|---|---|
| T1 | active | v0004 strict pseudobulk shift，48.5 | HX-KILLTEST 已 REJECT（增长/死亡动力学方向关闭）；无新授权不追加 T1 atom |
| T2 | active | per-board selection（embryo 60.1 / heart_interp **57.3** / heart_extrap 50.5），服务器 T2 55.7 | J1-FGW heart_interp v0009 服务器 57.3（+0.6）晋级；余 HX-DYNAMICS-KILLTEST 实例化 |
| T3 | gate_blocked | baseline-001，45.3 | S1C-A/B 方法组件已通过、S1D v3 获得 E9.5 exact-stage 但组织限定 context；继续寻找 E8.0-E9.5 state-matched activity/stability，不生成候选 |

Batch 1 已关闭为 `CLOSED_FOR_REVIEW`。综合评审报告为 `reports/PHASE_REPORT_BATCH1_20260829.md`；新 atom 需要新的明确授权。

当前科学阻塞只影响 scientific promotion，不影响比赛候选、上传和服务器反馈循环。

## 状态更新要求

coordinator 只在候选、检查、上传、评分、决策、阻塞或共享知识发生变化时更新本文件。agent 通过 handoff 提交更新，不直接并行编辑本文件。
