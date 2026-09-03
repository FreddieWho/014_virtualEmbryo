# 决策与交付事件日志

本文件追加式维护。历史事件不覆盖、不删除；详细 artifact 清单以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准，详细服务器分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准。

## 事件类型

```text
candidate_created
contract_validated
submitted
server_scored
decision_made
blocker_opened
blocker_closed
reuse_promoted
```

## 记录要求

每个候选至少记录：任务/board、candidate ID、父版本、方法、artifact 路径、SHA256、contract、服务器 ID、分数状态、决策和风险；用户未提供的服务器字段写 `pending`，不猜测。不额外要求截图、链接或 JSON 原始证据。

## 已登记决策

### D-COORD-001 — 建立三任务并行控制面

- date: 2026-08-22
- event: decision_made
- scope: T1,T2,T3
- decision: retain_four_document_coordination_system
- documents:
  - `docs/coordination/README.md`
  - `docs/coordination/STATUS.md`
  - `docs/coordination/DECISIONS.md`
  - `docs/coordination/KNOWLEDGE.md`
- rationale: "使用少量控制文档，复用现有候选索引和服务器分数 registry，避免重复状态源"
- constraints: "leaderboard 优先；科学阻塞不得阻断提交；共享代码需要 lease"

### D-T2-002 — 保留 T2 heart interpolation v0002

- date: 2026-08-22
- event: decision_made
- task: T2
- board: heart_interpolation
- candidate: `submission-002/T2_heart_val_interp/v0002`
- artifact: `submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad`
- server_score: 53.6
- decision: retain_as_current_best
- evidence: `reports/SERVER_SCORE_REGISTRY.md`
- next_candidate: `T2 heart interpolation v0003 geometry_scale_midpoint`
- notes: "相对 baseline-001 的该 board 分数提升 +0.6；成绩已登记，submission ID 未用于本次比较"

### D-T1-003 — 淘汰 T1 v0002，保留 copy_last 基线

- date: 2026-08-24
- event: decision_made
- task: T1
- board: val
- candidate_id: `submission-003/T1_val/v0002`
- parent_candidate: `baseline-001/T1_val/v0001`
- method: shrunk_pseudobulk_shift（celltype_weight=0.5, unmapped_delta=global, composition_extrap=linear, damp=1.0, seed=20260822）
- artifact: `submissions/scored/submission-003/T1_val/submission.h5ad`
- sha256: `bef1d4654ee1723b7e27716b676dda97f229a5560f2295e144d78bd1334acb3d`
- contract: pass
- server_submission_id: pending
- score: 45.9
- delta_vs_parent: -1.1
- evidence: `reports/SERVER_SCORE_REGISTRY.md`（用户回填）
- decision: reject
- blocker: null

- notes: "v0002 低于 copy_last 底线 1.1 分；baseline-001/T1_val/v0001（47.0）保留为 T1 当前 best。线索指向组成外推过激进（30% 分布项），下一步用 `--composition-extrap none` 或严格官方复刻分叉 v0003"

### D-T3-004 — 淘汰 T3 shift-transfer norm，关闭本轮

- date: 2026-08-24
- event: decision_made
- task: T3
- board: gata4
- candidate_id: `submission-004/T3_gata4/v0002`
- parent_candidate: `baseline-001/T3_gata4/v0001`
- method: shift_transfer_norm
- artifact: `submissions/candidates/T3_gata4/v0002_shift_transfer_norm/submission.h5ad`
- sha256: `adfc109ef565e4813aed1f4dd60d0bdc62ef96ad4f1ac96dcfcf9dbf92a2ef5c`
- contract: pass
- server_submission_id: pending
- score: 45.2
- delta_vs_parent: -0.1
- evidence: `reports/SERVER_SCORE_REGISTRY.md`（用户回填）
- decision: reject
- blocker: null
- notes: "按候选列出顺序登记；低于 baseline-001/T3_gata4/v0001（45.3），不构成 leaderboard 提升。"

### D-T3-005 — 淘汰 T3 shift-transfer shrunk，关闭本轮

- date: 2026-08-24
- event: decision_made
- task: T3
- board: gata4
- candidate_id: `submission-004/T3_gata4/v0003`
- parent_candidate: `baseline-001/T3_gata4/v0001`
- method: shift_transfer_shrunk
- artifact: `submissions/candidates/T3_gata4/v0003_shift_transfer_shrunk/submission.h5ad`
- sha256: `7f0ecf27f6b453122842dc77c25d860b36f6166428f43a28f62651f52f05d50f`
- contract: pass
- server_submission_id: pending
- score: 43.8
- delta_vs_parent: -1.5
- evidence: `reports/SERVER_SCORE_REGISTRY.md`（用户回填）
- decision: reject
- blocker: null
- notes: "按候选列出顺序登记；低于 baseline-001/T3_gata4/v0001（45.3），不构成 leaderboard 提升。本轮 T3 关闭，v0001 保留。"

## D-20260827-001 — B1-A1 双 lane 六候选冻结
- event: candidate_created | contract_validated
- date: 2026-08-27
- task: T2
- lane_policy: "`L1_FORMAL_LOG_RMS` + `L2_ALL_STAGE_LOG_RMS_OLS`; 每条 lane 覆盖三个 board，各生成一次"
- exploration_attempt_budget: 4
- score_handoff: manual_user_upload
- candidates:

| candidate_id | board | parent_candidate | method | artifact | sha256 | contract | server_submission_id | server_score | evidence | decision |
|---|---|---|---|---|---|---|---|---|---|---|
| `B1-A1-L1-T2_embryo_val_interp` | T2 embryo interpolation | `baseline-001/T2_embryo_val_interp/v0001` | `g1_formal_log_rms` | `artifacts/atomic_batch1/B1-A1/final/L1_FORMAL_LOG_RMS/T2_embryo_val_interp/prediction.h5ad` | `392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4` | pass | pending | pending | pending | pending |
| `B1-A1-L2-T2_embryo_val_interp` | T2 embryo interpolation | `baseline-001/T2_embryo_val_interp/v0001` | `g1_all_stage_log_rms_ols` | `artifacts/atomic_batch1/B1-A1/final/L2_ALL_STAGE_LOG_RMS_OLS/T2_embryo_val_interp/prediction.h5ad` | `f06540293b9bb479e7090926825ec722420d266257455a85ca8f470ee565f668` | pass | pending | pending | pending | pending |
| `B1-A1-L1-T2_heart_val_interp` | T2 heart interpolation | `submission-002/T2_heart_val_interp/v0002` | `g1_formal_log_rms` | `artifacts/atomic_batch1/B1-A1/final/L1_FORMAL_LOG_RMS/T2_heart_val_interp/prediction.h5ad` | `f8a4da854bf9e01e25503b59fddb70bae242c0382b38cc0f3984bf80cd751424` | pass | pending | pending | pending | pending |
| `B1-A1-L2-T2_heart_val_interp` | T2 heart interpolation | `submission-002/T2_heart_val_interp/v0002` | `g1_all_stage_log_rms_ols` | `artifacts/atomic_batch1/B1-A1/final/L2_ALL_STAGE_LOG_RMS_OLS/T2_heart_val_interp/prediction.h5ad` | `6239e6fa24fefb6a3f6ee76564a58f5e08a4463c24fc46747d9e59ee561d9538` | pass | pending | pending | pending | pending |
| `B1-A1-L1-T2_heart_val_extrap` | T2 heart extrapolation | `baseline-001/T2_heart_val_extrap/v0001` | `g1_formal_log_rms` | `artifacts/atomic_batch1/B1-A1/final/L1_FORMAL_LOG_RMS/T2_heart_val_extrap/prediction.h5ad` | `8c76db9cdd5453422d4c392108fd459c4ca44b9c391dd9af4605017988164834` | pass | pending | pending | pending | pending |
| `B1-A1-L2-T2_heart_val_extrap` | T2 heart extrapolation | `baseline-001/T2_heart_val_extrap/v0001` | `g1_all_stage_log_rms_ols` | `artifacts/atomic_batch1/B1-A1/final/L2_ALL_STAGE_LOG_RMS_OLS/T2_heart_val_extrap/prediction.h5ad` | `a85b8207e50002068a3bdfd4d9dd6677fffd4f1177262e83a1fb0f271fb86a26` | pass | pending | pending | pending | pending |

- local_evidence: "`artifacts/atomic_batch1/B1-A1/final/*/*/metrics/local_or_official.json`；仅 fixed public pseudo-holdout，不是服务器或 hidden score"
- notes: "冻结时六个候选均待服务器评分；已评分 artifact 不覆盖、不重命名。"
- blocker: null

## 后续事件模板

```markdown
## D-YYYYMMDD-NNN — <简短标题>

- event: candidate_created | contract_validated | submitted | server_scored | decision_made
- date: YYYY-MM-DD
- task: T1 | T2 | T3
- board: <board>
- candidate_id: <unique-id>
- parent_candidate: <id-or-null>
- method: <method>
- artifact: <path>
- sha256: <hash-or-pending>
- contract: pass | fail | pending
- server_submission_id: <id-or-pending>
- score: <value-or-pending>
- delta_vs_parent: <value-or-pending>
- evidence: <path-or-pending>
- decision: retain | reject | hold | pending
- blocker: <id-or-null>
- notes: <short reason>
```

## D-20260827-002 — B1-A1 服务器评分与逐 board 决策
- event: server_scored | decision_made
- date: 2026-08-27
- task: T2
- board_set: T2:embryo:val_interp; T2:heart:val_interp; T2:heart:val_extrap
- evidence: `reports/SERVER_SCORE_REGISTRY.md`；依据为用户回填的服务器成绩

| candidate_id | server_submission_id | server_score | delta_vs_parent | decision |
|---|---|---:|---:|---|
| `B1-A1-L1-T2_embryo_val_interp` | `t2_emb_int_b1_a1_l1` | 60.1 | +3.4 vs 56.7 | retain; board winner |
| `B1-A1-L2-T2_embryo_val_interp` | `t2_emb_int_b1_a1_l2` | 59.9 | +3.2 vs 56.7 | retain as scored second candidate |
| `B1-A1-L1-T2_heart_val_interp` | `t2_hrt_int_b1_a1_l1` | 56.3 | +2.7 vs 53.6 | retain; board winner |
| `B1-A1-L2-T2_heart_val_interp` | `t2_hrt_int_b1_a1_l2` | 55.3 | +1.7 vs 53.6 | retain as scored second candidate |
| `B1-A1-L1-T2_heart_val_extrap` | `t2_hrt_ext_b1_ba_l1` | 50.2 | -0.3 vs 50.5 | retain; board winner but below parent |
| `B1-A1-L2-T2_heart_val_extrap` | `t2_hrt_ext_b1_ba_l2` | 49.8 | -0.7 vs 50.5 | retain as scored second candidate; below parent |

- comparison: L1 beats L2 on all three boards by 0.2, 1.0 and 0.4 points.
- derived aggregate: selecting L1 on all boards gives T2 55.5 and aggregate 147.8; selecting L2 gives T2 55.0 and aggregate 147.3. These are protocol-derived, not server-returned Total values.
- final_decision: use L1 per board; keep all six immutable artifacts and L2 as the required scored second candidate/audit backup; no B1-A1 third lane or post-score tuning.
- blocker: null

## D-20260828-003 — B1-A2 T3 signed-response 双候选交付

- event: candidate_created | contract_validated
- date: 2026-08-28
- task: T3
- board: gata4
- parent_candidate: `baseline-001/T3_gata4/v0001`
- lane_policy: "固定 L1/L2 两条 lane；两条通过 contract/invariant 的候选都必须人工上传并评分"
- submission_mode: manual_user_upload

| candidate_id | lane | method | artifact | sha256 | contract | server_submission_id | score | decision |
|---|---|---|---|---|---|---|---|---|
| `B1-A2-L1-T3_gata4` | `L1_CELL_LEVEL_SPEARMAN` | `signed_response_cell_spearman` | `submissions/candidates/T3_gata4/v0004_b1_a2_cell_spearman/submission.h5ad` | `c6a09de79c8f29fb6096fabd36e2270e828a4c7d86da3966075babea3a0c5c8f` | pass | pending | pending | submit; score_pending |
| `B1-A2-L2-T3_gata4` | `L2_STATE_PSEUDOBULK_SPEARMAN` | `signed_response_state_pseudobulk_spearman` | `submissions/candidates/T3_gata4/v0005_b1_a2_state_pb_spearman/submission.h5ad` | `a702805d24786308a90dfbe7c4db0a37fad626be2fef45e16a1cf76a9899b84d` | pass | pending | pending | submit; score_pending |

- local_self_check: L1 `DES=-0.0143, DCS=-0.112, PSS=-3.4367`; L2 `DES=-0.0286, DCS=-0.058, PSS=-3.4411`; these are diagnostic pseudo-target metrics, not server scores.
- risks: WT-only weak prior; self-check direction is weak; no causal or universal claim.
- evidence: no extra screenshot, link, or JSON raw-evidence requirement; server fields remain pending until user returns scores.
- blocker: null

## D-20260828-004 — B1-A2 服务器失败与诊断 hold

- event: server_scored | decision_made
- date: 2026-08-28
- task: T3
- board: gata4
- parent_candidate: `baseline-001/T3_gata4/v0001`
- evidence: `reports/SERVER_SCORE_REGISTRY.md`；分数依据为用户回填的服务器成绩，不新增原始证据要求

| candidate_id | lane | server_submission_id | server_score | delta_vs_parent | decision |
|---|---|---|---:|---:|---|
| `B1-A2-L1-T3_gata4` | `L1_CELL_LEVEL_SPEARMAN` | `t3_v0004` | 44.7 | -0.6 vs 45.3 | reject; retain for diagnosis |
| `B1-A2-L2-T3_gata4` | `L2_STATE_PSEUDOBULK_SPEARMAN` | `t3_v0005` | 44.0 | -1.3 vs 45.3 | reject; retain for diagnosis |

- artifacts: v0004 SHA256 `c6a09de79c8f29fb6096fabd36e2270e828a4c7d86da3966075babea3a0c5c8f`; v0005 SHA256 `a702805d24786308a90dfbe7c4db0a37fad626be2fef45e16a1cf76a9899b84d`
- contract: both pass; actual uploaded files match the indexed SHA256 and remain immutable
- local_diagnosis: target-matched Mab21l2 self-check had DES/DCS below the WT floor for both lanes; actual-file public proxy also had DES/DCS, MMD and variogram below baseline directionally. L2 used larger residuals and had more clipping than L1.
- failure_assessment: the WT-only Spearman sign prior and borrowed Mab21l2 absolute-effect budget do not provide a reliable Gata4 perturbation response; the two lanes are an algorithm-level failure, not a packaging failure.
- final_decision: keep baseline-001/T3_gata4/v0001 as current best; hold B1-A2 for diagnosis; do not enter B1-A3 or generate a replacement candidate in this turn.
- blocker: diagnostic_hold; blocks_submission: false

## B1-A3 activation — 2026-08-28

- user_authorization: proceed with a source-only cross-stage partition freeze and two formally scored T1 lanes
- parent: keep immutable `baseline-001/T1_val/v0001` (server score 47.0); do not parent on unscored or mean-shifted v0003/v0004
- partition_lanes: `L1_SHARED_UNRESOLVED` and `L2_E95_EXPRESSION_PROBE`
- constraints: no target read, no external data, no re-clustering, no manual biological label crosswalk, no automatic upload
- residual_rule: balanced complete-row replay from the immutable parent, preserving full expression vectors and total n=5118
- scoring: one final local scorer run and one manual server score per lane; server results remain `score_pending` until user provides scores

## T1 leaderboard reconciliation — 2026-08-28
- source: user-provided leaderboard table; the portal Model column is explicitly treated as unreliable.
- mapping: the two unlabeled T1 rows at 12:30 and 12:43 are mapped by chronological candidate/upload order to local v0003 and v0004; this restores scores 46.2 and 48.5.
- decision: v0004=48.5 is the current T1 best; B1-A3 v0006=47.7 is only the B1-A3 lane winner, and v0005=47.5 is its scored backup.
- aggregate: retain the derived current total 48.5 + 55.5 + 45.3 = 149.3; the server returned board scores, not a direct Total.
- correction: the earlier status that called B1-A3 v0006 the global T1 best was wrong and has been synchronized.

## Current leaderboard aggregate correction — 2026-08-28
- source: user-provided current leaderboard tuple: Total=149.5, T1=48.5, T2=55.7, T3=45.3.
- correction: the prior local derivation 149.3/55.5 incorrectly used B1-A1 heart extrapolation L1=50.2 instead of the higher baseline=50.5.
- selection: T2 currently uses B1-A1 L1 for embryo interpolation=60.1 and heart interpolation=56.3, plus baseline heart extrapolation=50.5.
- rounding: displayed component scores average to 55.633..., so the local record must not override the server-returned T2=55.7; unrounded server values or exact aggregation precision are unavailable.

## B1-A4 J1 activation and completion — 2026-08-29
- route: execute two final lanes, `L1_LATENT_KNN10` and `L2_STATE_HASH10`, across the three T2 boards; six artifacts are the terminal candidate set for this atom.
- parent rule: use the immediate B1-A1 parent for embryo/heart interpolation and the immutable baseline for heart extrapolation; do not reapply B1-C1 scale correction.
- implementation: source-only hard expression-coordinate permutation with fixed seed; expression rows are permuted bijectively while `obs`, coordinates and scorer-equivalent 15-NN structure remain unchanged.
- result: all six artifacts passed contract/invariant checks and fixed public proxy scoring; server status remains `score_pending`, so no leaderboard improvement is claimed.

## B1-A4 server scoring decision — 2026-08-29
- supplied scores: embryo interpolation `59.3/59.2`, heart interpolation `56.3/56.3`, heart extrapolation `50.0/49.9` for L1/L2 respectively.
- comparison: embryo is below B1-A1 L1 `60.1`; heart interpolation ties `56.3`; heart extrapolation is below baseline `50.5`.
- decision: B1-A4 is not promoted. The current T2 selection and server-returned aggregate remain T2 `55.7` and Total `149.5`; all six A4 artifacts remain immutable scored records.
- mapping: scores were matched by the explicit batch/task/board/lane/version filenames in the upload package; no submission ID was supplied and none was fabricated.

## D-20260829-005 — Batch 1 收尾冻结与外部评审交付
- event: blocker_closed | decision_made
- date: 2026-08-29
- scope: B1-A1, B1-A2, B1-A3, B1-A4, conditional B1-C1
- decision: close_batch1_for_review
- result: "四个正式 atom 均完成；最终候选 6/2/2/6，共 16 个，服务器评分登记 16/16。A1 仅在两个 T2 interpolation board 形成当前可保留改进；A2、A3、A4 不改变当前选择。"
- current_selection: "T1=48.5；T2=55.7；T3=45.3；Total=149.5，具体 per-board selection 以现有状态和服务器 registry 为准。"
- conditional_atom: "B1-C1 不执行；A4 的 immediate parent 已携带 A1 scale 或 identity scale，重复组合记为不需要生成。"
- audit: "INDEX 中 16 个 B1 canonical 文件 SHA256 全部重算匹配；4 份 final-set manifest 可解析；已评分 artifact 未覆盖或重命名。"
- documents:
  - `reports/PHASE_REPORT_BATCH1_20260829.md`
  - `reports/RELEASE_CHANGELOG_20260829.md`
- next_action: "无 active atom；任何新 atom、下一批或服务器提交需要新的明确授权。"
- limitations: "A3 full-panel local scorer 不完整；仓库尚无 initial Git commit；科学 promotion 仍不满足独立 stage/replicate 证据要求。"

## D-20260830-001 — B2-T3-A1 生成完成但保留为组件

- event: candidate_created | contract_validated | decision_made
- date: 2026-08-30
- scope: B2-T3-A1
- task: T3
- board: gata4
- parent: `submissions/scored/baseline-001/T3_gata4/submission.h5ad`
- candidates:
  - `v0006_b2_t3_a1_l1` — `submissions/candidates/T3_gata4/v0006_b2_t3_a1_l1/submission.h5ad`, SHA256 `d3cc8adb6f46070f7dbfecbdff9c10e9df9184a417376fb0d4a4813b2517c175`
  - `v0007_b2_t3_a1_l2` — `submissions/candidates/T3_gata4/v0007_b2_t3_a1_l2/submission.h5ad`, SHA256 `012ac745c995f5f5ef0209c44250cf8aa1bb35ae1fe2355550e7ab16297cf900`
- contract: "两条 lane 均 contract PASS、protected checks PASS；P0 task_permit=true，forbidden_records_remaining=0。"
- score_status: score_pending
- server_id: pending
- decision: HOLD_AS_COMPONENT
- rationale: "E-MTAB-11763 仅可作 metadata-only fallback；CellOracle/scTenifoldKnk 为可审计本地近似而非上游完整执行；本轮未上传服务器。Mab21l2 kill test 仅为 source-only 跨扰动诊断，不构成 Gata4 因果证据。"
- next_action: "停止于本 atom；如需 leaderboard 证据，由用户明确选择后手动上传并回填原始分数。"

## D-20260831-002 — T3-S1-PRIOR 外部部署阻塞解除但 gate 保持 HOLD

- event: external_download_authorized | local_deployment_validated | gate_recomputed
- date: 2026-08-31
- scope: T3-S1-PRIOR
- task: T3
- parent: `P0-LOCK`
- authorization: "用户明确授权下载 `genomepy`、`scTenifoldNet` 等解除本地部署阻塞所需的固定依赖；授权仅用于本地 hash-locked cache，未授权服务器提交。"
- evidence:
  - `artifacts/tool_integration/T3-S1-PRIOR/deployment/deployment_report.json`
  - `artifacts/tool_integration/T3-S1-PRIOR/TOOL_VERSIONS.json`
  - `infra/external_data/sanitized/T3/B2-T3-A1/COLLECTRI/snapshot_manifest.json`
  - `infra/external_data/sanitized/T3/B2-T3-A1/OMNIPATH/snapshot_manifest.json`
- result: "deployment `PASS`; genomepy/CellOracle import、scTenifoldNet 1.4 与 scTenifoldKnk 1.1 source-version match、synthetic smoke 均通过；CollecTRI 4,910 与 OmniPath 2,553 条 panel-scoped directed edges 均通过内容级审计。"
- gate: "prior/gate 重算为 `HOLD_AS_COMPONENT`；稳定性为 `PASS_WITH_SENSITIVITY`，删除任一模型 family 后严格双 family consensus 全部消失。"
- scientific_boundary: "已审计的 panel-scoped 快照尚未被当前 prior-only adapter 消费；beta-catenin 记录保持 sign=0，不做生物学结论。"
- submission_boundary: "blocks_submission: false；未生成 H5AD/候选，未调用 scorer，未上传服务器，未产生 submission ID 或新分数。"
- next_action: "保持 prior bundle 为审计组件；如继续，单独授权并验证 S1B 快照集成及独立稳定性证据。"

## D-20260831-003 — 正式候选前闭合与外部证据分层

- scope: "P0 contract / T3-S1-PRIOR / T3-S1B preflight"
- decision: "完成新版单一 H5AD contract 入口、5 个 current parent 的完整 contract round-trip 复核，以及 CollecTRI/OmniPath directed-evidence 本地消费预检；保留原 P0 contract scaffold hash 作为历史快照，使用独立 contract-preflight adapter hash 作为后续有效实现。"
- evidence:
  - `artifacts/tool_integration/CONTRACT-PREFLIGHT-20260831/contract_preflight.json`
  - `artifacts/tool_integration/T3-S1B-PREFLIGHT/summary.json`
  - `artifacts/tool_integration/STABILITY-PREFLIGHT-20260831/stability_preflight.json`
  - `docs/batch3/interfaces/tests/`（18 passed）
- scientific_boundary: "snapshot_audit=PASS、directed integration preflight=PASS 不等于 state-specific activity validation 或 prior gate pass；当前 S1 prior 不消费 state-joined external evidence。"
- stability_decision: "CollecTRI edge 与现有 model-family signs 存在 target/family-specific discordance，且 leave-one-family-out 仍为结构性 HOLD；不得硬接成第三票或生成候选。"
- submission_boundary: "blocks_submission: false；不生成 H5AD/候选、不调用 scorer、不上传；T3 current best 仍为 baseline-001/T3_gata4/v0001=45.3。"
- next_action: "仅在单独激活 S1B 后执行固定 state-join adapter、冲突处理、独立稳定性复核；route gate 未通过前不物化正式 L1/L2 候选。"

## D-20260831-004 — pre-formal-analysis 补强复核结果
- event: engineering_hardening_completed | gate_recomputed
- date: 2026-08-31
- scope: `P0-LOCK` / `T3-S1-PRIOR` / `T3-S1B-KNOWLEDGE-PREFLIGHT`
- decision: "parent-bound contract、输入 provenance 和外部证据分层已补强；使用独立 v2 preflight 目录保留旧证据，不覆盖历史输出。"
- evidence:
  - `artifacts/tool_integration/CONTRACT-PREFLIGHT-20260831-v2/contract_preflight.json`
  - `artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v2/summary.json`
  - `artifacts/tool_integration/STABILITY-PREFLIGHT-20260831-v2/stability_preflight.json`
  - `docs/batch3/interfaces/tests/`（22 passed）
- result: "5/5 current parent 的 registry SHA256、protected fields、round-trip 通过；外部快照 source/dataset/taxon/license fail-closed 通过；directness 与未校准 confidence 分离。"
- scientific_boundary: "组件证据通过不等于 state-specific activity validation；candidate admission 保持 HOLD，T3 prior gate 保持 HOLD_AS_COMPONENT。"
- submission_boundary: "blocks_submission: false；本轮未生成 H5AD/候选、未运行 scorer、未上传服务器。"

## D-20260831-005 — pre-formal-analysis provenance snapshot 收口
- event: evidence_chain_refreshed | status_reconfirmed
- date: 2026-08-31
- scope: `T3-S1-PRIOR` / `T3-S1B-KNOWLEDGE-PREFLIGHT`
- decision: "将 upstream gate 复制为 preflight 内不可变 snapshot 后，重新生成 v3 knowledge/stability evidence；旧 v2 输出保留为历史记录，不覆盖。"
- evidence:
  - `artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3/summary.json`（SHA256 `a41db892e852d9da794277eb8093c0bbfba7b52cc04d45bd4f93751dcda21632`）
  - `artifacts/tool_integration/STABILITY-PREFLIGHT-20260831-v3/stability_preflight.json`（SHA256 `3f96627ffa866c0ad17d51537f08c0ed7a36db8f06c4664f08b3fff6685213c8`）
  - `artifacts/tool_integration/T3-S1-PRIOR/metrics/gate_report.json`（SHA256 `69c1ffbd25039cb467865f2d7670c58dce58a7fe3efa48cba1e00195761f25e1`）
- result: "manifest source/file hashes 自洽；knowledge 为 `COMPONENT_PASS` 但 candidate admission `HOLD`，stability 为 `HOLD`，prior gate 为 `HOLD_AS_COMPONENT`。"
- submission_boundary: "blocks_submission: false；仍未生成 H5AD/候选、未运行 scorer、未上传服务器。"

## D-20260831-T3-S1A-004
- scope: `T3-S1A-STATE-JOIN`
- decision: "接受 Extended Mouse Atlas exact E8.75 source-attested input、5 个官方 Ensembl alias closure、full mouse OmniPath/CollecTRI 和 CellOracle mm10 base-GRN 的本地部署；不接受未完成的 CellOracle target 作为 route gate 通过。"
- evidence:
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5/metrics/runtime_blocked.json`
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5/celloracle/Gata4_votes.tsv`（real API partial output）
  - `infra/bioinf-data-index/INDEX.tsv`（external data and SHA256 index）
- result: "输入审计和 state join PASS；Gata4 real API PASS；Gata6/Ctnnb1 full propagation 超过 bounded runtime window，scTenifold 和 route gate 未在 v5 完成；T3-S1A 保持 `BLOCKED_RUNTIME`。"
- submission_boundary: "blocks_submission: false；不生成 H5AD/候选、不运行 scorer、不上传服务器。"

## D-20260901-T3-S1A-005
- scope: `T3-S1A-STATE-JOIN`
- decision: "接受 v6 的运行层修复和实际执行证据，但不把 partial/non-applicable target 或未验证 state activity 解释为 route gate 通过；候选生成和服务器提交继续关闭。"
- evidence:
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/metrics/tool_execution.json`
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/metrics/gate_report.v2.repaired.json`
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/metrics/artifact_manifest.stable.json`
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v6/celloracle/Gata4_votes.tsv`
- result: "exact input/state join PASS；Gata4 CellOracle real API PASS；Gata6/Ctnnb1 因当前 base GRN 缺少可扰动 TF source 而不适用；三条 scTenifold 输出完成；全局 route gate 为 `BLOCKED`，主要剩余缺口为 `STATE_ACTIVITY_NOT_VALIDATED` 和 target applicability。"
- submission_boundary: "blocks_submission: false；本轮未生成 H5AD/候选、未运行 scorer、未上传服务器；45.3 baseline 仍是当前已评分 best。"
- limitations: "v6 的 Gata6/Ctnnb1 status 保留实际运行返回的 `BLOCKED_TOOLCHAIN` 历史标签；后续新运行将通过 base-GRN capability preflight 明确标记 `NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT`。"

## D-20260901-T3-S1A-006
- event: state_mapping_repaired | state_response_audited | gate_recomputed
- date: 2026-09-01
- scope: `T3-S1A-STATE-JOIN-20260901-v7`
- task: T3
- parent: `T3-S1A-STATE-JOIN-20260901-v6`
- decision: "接受 v7 的 explicit external-state→recorded-parent-state 映射、target applicability 分层和 full-matrix state-response/coverage 审计；不把 modelled response 当作 biological activity，也不把当前 base GRN 缺少 Gata6/Ctnnb1 source 当作生物学无效。"
- evidence:
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/tool_execution.json`（SHA256 `368da3d484da99ef6227a7a8078b8fcc3c2c792377ea670fe985c678641eb15b`）
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/gate_report.v2.repaired.json`（SHA256 `dfe522011bc3c198d30fc9f483f3b6e8842922c4f1f596713c7762c80095c8e5`）
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/state_response_support.json`（SHA256 `1bc9dfdb74ac386dbcd9de84919855199fb4c5ec384725cf3976f78ef964964c`）
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/artifact_manifest.stable.json`（SHA256 `22d785ea59a85d13529db8896772ccdee5f79b95c4cd557bfabfff0897109db8`）
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/celloracle/Gata4_state_response.tsv`（SHA256 `36588d3912264256469acbd868af8631af9595286d8d56460a92ea60884f56a2`）
  - `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/celloracle/Gata4_state_coverage.tsv`（SHA256 `fd0c5a040753c3d7e4d4ea54ba0e5e7884dd3fdd202bfe5a00b2d74211ebd997`）
- result: "exact input/state join PASS；CellOracle Gata4=PASS，Gata6/Ctnnb1=`NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT`；三条 scTenifold 输出均为 `PASS_UNSIGNED_RANK_ONLY`；Gata4 selected-gene stability PASS；state-response support 为 `NOT_IDENTIFIABLE`（23 个 required mapped states 中 12 个通过、11 个 HOLD），claim=`MODELLED_STATE_RESPONSE_ONLY`，biological activity=`NOT_VALIDATED`；hash-bound route audit PASS，四条 route 均 HOLD，全局为 `HOLD_AS_COMPONENT`。"
- submission_boundary: "blocks_submission: false；未生成 H5AD/候选，未运行 scorer，未上传服务器；T3 当前已评分 best 仍为 `baseline-001/T3_gata4/v0001=45.3`。"
- limitations: "state mapping 存在 collision，已保留在 audit 且未当作独立样本；scTenifold 没有 signed claim；Gata6/Ctnnb1 在当前 GRN 没有适用的 CellOracle source；state-response 不能替代 in-vivo activity。"
- next_action: "仅在获得可审计 biological activity 与独立 stability 证据，或经授权切换到 target-compatible GRN 后复核 route gate；不得用 proxy、降采样或未等价替代解锁候选生成。"

### D-20260901-T3-S1B-001 — S1B external context 与 stability gate 收口
- event: decision_made | blocker_opened
- date: 2026-09-01
- task: T3
- atom: `T3-S1B-STATE-JOIN-20260901-v2`
- parent_atom: `T3-S1A-STATE-JOIN-20260901-v7`
- candidate_id: none
- artifact: `artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v2/`
- artifact_manifest_sha256: `239e5c474986cb54e70d5b1451330a20350be38fadaf7641c1e2177b2aea34ea`
- gate_report_sha256: `1d10e15b2be52eddd9693cbf84791e0ba66614359468c5708b844b96254f89f0`
- checks: "full parent manifest 与双源 snapshot identity PASS；external raw 128 条、状态上下文投影 5808 条、总 source rows 137148；外部全部 `GLOBAL_CONTEXTUAL`/`SUPPORTING_KNOWLEDGE` 且不具 activity eligibility；4/4 route HOLD；53 项回归测试 PASS；stable manifest 27 files SHA256 自洽。"
- decision: "保留 S1B v2 作为可复用审计组件，不生成 H5AD/candidate，不运行 scorer，不上传服务器。"
- blocker: "T3-S1A-GATE-001；`biological_activity_status=NOT_VALIDATED`，signed biological family stability 为 `NOT_IDENTIFIABLE`，blocks_submission: false。"
- risks: "external edge/path 不能作为独立 biological family、不能补 activity/sign、不能恢复 Gata6/Ctnnb1 的当前 GRN applicability；contextual conflict 只在派生 sign 中归零，raw evidence 保留。"
- superseded_attempt: "S1B v1 首次运行因 unresolved path 的 hop-based rank 封装错误触发 `BLOCKED_INPUT_IDENTITY`；该失败 receipt 保留，v2 为同一输入的修正版，不覆盖 v1。"
- next_action: "仅在获得独立 biological activity 与 stability 证据，或另行授权 target-compatible GRN atom 后复核 route gate；不得用 proxy、降采样或未等价替代解锁候选生成。"

### D-20260901-T3-S1B-002 — 补齐 artifact-to-code provenance 后以 v3 收口
- event: reuse_promoted | decision_made
- date: 2026-09-01
- task: T3
- atom: `T3-S1B-STATE-JOIN-20260901-v3`
- parent_atom: `T3-S1A-STATE-JOIN-20260901-v7`
- candidate_id: none
- artifact: `artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v3/`
- implementation_sha256: `cd480790fa6cbf7e6618ec28675983143466788847e79e73040d63df7dfe9d8c`
- artifact_manifest_sha256: `396b15d976e10700709c7628539dd2e9cac21b66612d9b72faa772921413744e`
- gate_report_sha256: `a4be63a1653353b238ce5cb29436cea834e438d9b2a3a3e85cb467d121d00e21`
- decision: "接受 v3 作为当前 S1B 可复用审计组件；v2 仍不可变但未记录脚本 SHA，v3 在 input lock、stable manifest、gate 和 completion 中完成绑定。"
- checks: "53 项回归测试 PASS；独立 tester：5 S1B tests + 34 interface tests PASS；27 stable files bytes/SHA PASS；实现脚本 SHA、artifact SHA、gate SHA 和输入锁定 SHA 一致；4/4 route HOLD，selected signed records=0。"
- blocker: "T3-S1A-GATE-001; biological_activity_status=NOT_VALIDATED; signed-family stability=NOT_IDENTIFIABLE; blocks_submission: false"
- submission_boundary: "无 H5AD、无 candidate；未修改 submissions/INDEX.tsv；未修改 reports/SERVER_SCORE_REGISTRY.md；未运行 scorer、未上传服务器。"
- next_action: "仅在独立 biological activity/stability 或 target-compatible GRN 新 atom 经授权后复核 route gate；保持 external contextual 与 unsigned rank 不进入 biological gate。"

### D-20260901-T3-S1C-001 — target-compatible GRN 采用原生 TFdict 双阶段收口
- date: 2026-09-01
- scope: T3-S1C target-compatible GRN
- decision: "接受 S1C-A/v1 的 source-membership 组件和 S1C-B/v2 的真实 CellOracle API smoke；不修改 S1A/S1B、base parquet 或已评分 artifact。Gata6 仅纳入 18 个一跳 CollecTRI panel relation，Ctnnb1 仅纳入严格一跳 OmniPath Ctnnb1→Pitx2；多跳路径不折叠。"
- evidence: "S1C-A stable manifest SHA256 6700b919cba382475cbd6a1c3bee0dd8af5271685285c18011c4e3bab8e8706c；S1C-B/v2 stable manifest SHA256 806bf41acadfb9b5dc0d0b2329b36e1848b390231c573edcf8ec5e8e8ac0c817；clean rerun 的 TFdict 与 regulator_edges payload 哈希均与 S1C-A 原子产物一致。"
- boundary: "method_source_compatibility=PASS；biological_activity_status=NOT_VALIDATED；state_specificity_status=NOT_EVALUATED；signed_family_stability=NOT_IDENTIFIABLE；candidate_generation=false；server_submission=false；blocks_submission=false。"
- next_action: "只有在独立 matched activity/stability 证据到位后，另行授权 exact E8.75 full rerun；不得把 synthetic smoke 或 adapter source membership 当作生物学活动证据。"

### D-20260901-T3-S1C-002 — 保留 S1C-B/v1 fixture 边界失败并采用 v2
- date: 2026-09-01
- scope: T3-S1C-B source adapter smoke
- decision: "S1C-B/v1 因把无匹配 native outgoing response 的 Gata4 放入 synthetic smoke target 而 fail-closed；失败 receipt 保留不可复用。S1C-B/v2 将 smoke 边界限定为新 adapter 的 Gata6/Ctnnb1，并通过真实 CellOracle 0.22.0 fit/simulate。"
- evidence: "v2 target results 为 Gata6/Ctnnb1 2/2 PASS，均 24×20、delta_x finite；v1 与 v2 均未生成 H5AD/候选、未运行 scorer、未上传。"
- boundary: "这是测试边界修复，不是模型效果或候选改进；blocks_submission=false。"

### D-20260901-T3-S1D-001 — off-target GEO perturbation 只能作为 context
- date: 2026-09-01
- scope: T3-S1D independent activity evidence
- decision: "接受 GSE156307 和 GSE255237 的 processed expression 为可审计的外部扰动 context，但不将其转移为 E8.75 activity/sign/family evidence；GSE67463、GSE50859、GSE70134 仅保留 metadata-only。"
- evidence: "GSE156307 Gata4 E14.5 HS cKO/WT log2FC=-1.1839，5/5 cKO 方向一致；GSE255237 Gata6 E11.5 OFT MUT/WT log2FC=-0.3362，4/4 MUT 方向一致；S1D stable manifest SHA256 9017b2db83c09a776c8c1620f8ca00c6740f3c1d288ed857d9635c1b30f42fdf。"
- boundary: "两者均非 E8.75 matched tissue/stage；GSE255237 series design 与 processed sample columns 存在 3 pools/genotype vs 4 MUT/3 WT 冲突；independent_signed_family_count_for_E875=0，candidate_generation=false，server_submission=false，blocks_submission=false。"
- next_action: "继续检索 E8.0–E9.5、目标组织/状态匹配且至少两个生物学重复的 target-specific perturbation；在此之前保持 candidate gate。"

### D-20260901-T3-S1C-003 — 修复 stable manifest 的 volatile runtime 误收录
- date: 2026-09-01
- scope: T3-S1C-B source adapter smoke artifact provenance
- decision: "S1C-B/v2 的真实 smoke 结果保留为执行 receipt，但 post-run self-check 发现 genomepy SQLite `cache.db-shm` 在进程退出后消失，故不接受 v2 stable manifest 为可复用交付。新建 v3，stable manifest 排除 runtime cache、MPL/Numba cache 和 SQLite `-shm/-wal` sidecar，不覆盖 v2。"
- evidence: "S1C-B/v3 stable manifest SHA256 7770e075838309af5d339506b02e7975459aa651deb8d10f4079f25fec9c822d；manifest 自校验 7/7 PASS；Gata6/Ctnnb1 真实 CellOracle 0.22.0 fit/simulate 2/2 PASS；v2 manifest SHA256 806bf41acadfb9b5dc0d0b2329b36e1848b390231c573edcf8ec5e8e8ac0c817 保持不变。"
- boundary: "这是 artifact provenance 修复，不是生物学效果改进；synthetic smoke 仍不产生 activity/sign/rank/state response；candidate_generation=false；server_submission=false；blocks_submission=false。"
- next_action: "后续使用 `.venvs/ve-t3-prior/bin/python`，并在生成 stable manifest 后执行进程退出后的完整 hash/bytes 自校验。"
### D-20260901-T3-S1D-002 — 接受 exact-stage context 作为审计证据但不解除 E8.75 gate
- date: 2026-09-01
- scope: T3-S1D independent perturbation evidence
- decision: "保留 S1D v2 初步原子不覆盖；采用 v3 作为当前可复核版本，补齐冻结 contract、逐 GSM sample QC、官方 GPL probe/Entrez mapping、gene/study effect、run manifest 和稳定性复跑。三份 E9.5 矩阵均通过完整性与映射审计，但只作为 tissue-limited contextual evidence。"
- evidence: "`artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3/metrics/gate_report.json`；GSE5298/GSE9652 Gata4 两个 family，GSE78125 Ctnnb1 一个 family，Gata6 为 0；stable manifest SHA256 `6c2806aa381f099e3db88f38a35278d4500e1aeb1f8de7fe3cfa20e2db487e0c`；核心输出复跑一致，4 个 targeted tests PASS。"
- boundary: "target expression 仅作 descriptive readout；未将 E9.5 组织限定效应转写为 E8.75 state-specific signed activity，independent signed family 仍为 0；candidate_generation=false；server_submission=false；blocks_submission=false。"
- next_action: "继续寻找真正 E8.0-E9.5、目标状态匹配且可复现的 signed-family 证据；若无法获得，在单独授权下再评估是否收窄科学声明，不自动启动 E8.75 全量推断。"

### D-20260902-T3-S1C-001 — 先完成 activity gate 可满足性审计，不直接启动 exact rerun
- date: 2026-09-02
- scope: T3-S1C activity gate and claim boundary
- decision: "接受 `T3-S1C-GATE-SATISFIABILITY-20260902-v1` 作为当前决策 atom。按现行 firewall，旧 gate 所需的 E8.75/comparable-stage target-specific perturbational signed evidence 与允许证据集合不具备足够交集，判定为 `UNSATISFIABLE_UNDER_FIREWALL`。保持 S1B/S1C/S1D 历史结果不变，不重跑 S1B，不继续搜索近 E8.75 target perturbation，不立即启动 S1C exact rerun。"
- evidence: "`docs/batch3/T3_S1C_GATE_SATISFIABILITY_DECISION_20260902.md`；`docs/batch2/compliance/DATA_FIREWALL_SPEC.md`；`docs/batch2/compliance/protected_windows.yaml`；`docs/batch3/prompts/T3_S1B_PRIOR_TO_CANDIDATE.md`；当前 S1A v7、S1B v3、S1C-A/v1、S1C-B/v3、S1D/v3 receipts。"
- boundary: "E8.75 WT 只能支持 WT-context regulatory coherence；远窗口数据不能桥接为 E8.75 activity；CollecTRI/OmniPath、adapter、synthetic smoke 和 unsigned rank 不构成 independent signed family；quarantine 中的 S1D 矩阵在用途重新取得 permit 前不得继续复用。candidate_generation=false；server_submission=false；blocks_submission=false。"
- next_action: "若用户或 contract owner 正式授权 scope-change，先建立新 contract，再执行限定为 WT-context/modelled response 的 S1C-C exact E8.75 atom；否则维持 HOLD，不增加无效计算。"
