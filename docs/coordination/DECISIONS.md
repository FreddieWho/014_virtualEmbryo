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

### D-20260903-T2-S3-001 — T2-S3 服务器评分与 heart_interp 晋级
- date: 2026-09-03
- scope: T2-S3-SHAPE-FIELD-20260903-v1
- decision: "heart_interp v0007 t2_s3_l1_pycpd 服务器 56.7（+0.4 vs B1-A1 L1 56.3）晋级 board best 与当前 selection；embryo v0006 59.7（-0.4）不晋级；4 条本地 REJECT 候选（L2 全部 + heart_extrap L1）不上传、不可变保留。"
- evidence: "用户回填 leaderboard 行（2026-09-03 12:12/12:14）；reports/SERVER_SCORE_REGISTRY.md T2-S3 节；submissions/INDEX.tsv v0006/v0007 行。"
- boundary: "服务器未返回新 T2/Total，55.7/149.5 保持；derived 值不引用为服务器值；leaderboard 分数不作因果机制证据。"
- review_trigger: "服务器页面刷新后 Total/T2 与 derived 55.77/149.6 不一致时复核聚合规则。"

### D-20260903-NAME-001 — 上传命名规则固化
- date: 2026-09-03
- scope: 全部手动上传包
- decision: "上传 zip 成员名固定 `<task>_<board>__<lane>__vNNNN.h5ad`（≤50 字符，board 短码 t1 val / t2 emb_int|hrt_int|hrt_ext / t3 gata4），zip 名 `<atom短码>__<task>__upload__<YYYYMMDD>.zip`，包内附 MANIFEST.tsv（filename/bytes/sha256）。规则写入 AGENTS.md 与 submissions/README.md。"
- evidence: "deliveries/t2s3__t2__upload__20260903.zip、deliveries/t2j1__t2__upload__20260903.zip。"
- review_trigger: "官方 portal 变更文件名约束时。"

### D-20260904-T2-J1-001 — J1-FGW heart_interp v0009 晋级、embryo v0008 HOLD
- date: 2026-09-04（回填；服务器行 2026-09-03 19:51）
- scope: T2-J1-FGW-ASSIGNMENT-20260903-v1
- decision: "heart_interp v0009 j1_fgw_assignment 服务器 57.3（+0.6 vs v0007 56.7）晋级 board best 与当前 selection；embryo v0008 本地同靶 NFS 镜像无改善且探针为负，HOLD_AS_COMPONENT 不上传；当前 selection = embryo 60.1（B1-A1 L1）+ heart_interp 57.3（T2-J1 v0009）+ heart_extrap 50.5（baseline）。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md T2-J1 节；artifacts/tool_integration/T2-J1-FGW-ASSIGNMENT-20260903-v1/（manifest 40 文件自校验 PASS）；本地混合证据（nmmd 0.0967→0.0747 改善 vs morans 0.7365→0.6743 变差）由服务器正向仲裁。"
- boundary: "derived T2≈55.97/Total≈149.8 待服务器页面确认；FGW 改善不构成机制因果证据。"
- review_trigger: "服务器页面 Total 与 derived 不一致；或 embryo 补齐同靶 parent scorer 参照后重评 v0008。"

### D-20260904-HX-001 — HX-DYNAMICS-KILLTEST REJECT，增长/死亡动力学方向关闭
- date: 2026-09-04
- scope: HX-DYNAMICS-KILLTEST-20260904-v1（MIOFlow × T1 state-mass 单假设）
- decision: "预声明 kill metric（留 E9.5 per-state mass L1，须同时严格优于 strict-shift parent 与 moscot 双臂）未达成：mioflow 0.7475 vs moscot 0.6645 vs parent 1.1894 → REJECT。结论：moscot 的 state-mass 预测已显著优于 strict-shift，T1-S2 失败不在 mass 环节；增长/死亡+随机动力学方向对 T1 关闭。不生成候选、不上传。"
- evidence: "artifacts/tool_integration/HX-DYNAMICS-KILLTEST-20260904-v1/metrics/holdout_mass_l1.json（双臂复用冻结 artifact，SHA 记录）；mioflow==0.1.14 一次性 hash-lock 部署（Yale 非商业许可已披露）；12 新测试+174 全量回归 PASS。"
- boundary: "E9.5 为训练期 stage，holdout 只验证假设机制；kill test 不产生 leaderboard 证据；mioflow venv 保留可复用但不得作为统一 backbone。"
- review_trigger: "出现独立证据表明 T1 残差确实由 state-mass 漂移主导时，方可重开本方向。"

### D-20260904-T3-001 — B2-T3-A1 双 lane 并列晋级 T3 board best
- date: 2026-09-04（回填；服务器行 2026-09-03 23:40 / 23:41）
- scope: T3:gata4 / B2-T3-A1 v0006 L1_STRICT_WT_DIRECT、v0007 L2_GATA4_GATA6_CONDITION_AWARE
- decision: "两条候选服务器均 45.5（+0.2 vs wt_identity 45.3），并列新 board best，晋级当前 selection；v0002–v0005 五条历史候选保持不可变淘汰记录。服务器无法区分两 lane，不声称 lane 偏好。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md B2-T3-A1 节；INDEX.tsv v0006/v0007 行（d3cc8adb… / 012ac745…）；deliveries/b2t3a1__t3__upload__20260904.zip。"
- boundary: "derived T3=45.5/Total≈149.7 待服务器页面确认；leaderboard 增益不解除 T3-S1 科学 gate（仍 CLOSED_AS_RESEARCH_COMPONENT，UNSATISFIABLE_UNDER_FIREWALL），不作机制/因果证据；blocks_submission: false。"
- review_trigger: "服务器页面 Total 与 derived 149.7 不一致；或科学重开条件（收口报告 §6）被新证据满足时重估 gate。"

### D-20260904-B4P0-001 — Batch 4 启动与 P0 完成（human team）
- scope: B4-P0-STATE-FLOOR-PARITY（run `B4-P0-STATE-FLOOR-PARITY-2026-09-04T110859.403071+0000`）
- decision: "用户授权 batch4 并声明 human team（官方 Agent Team evidence 规则仅作内部纪律）；P0 完成：v0006/7 状态同步核对一致（45.5/45.5），INDEX.tsv 回填 6 行 B1-A1 缺分（60.1/59.9/56.3/55.3/50.2/49.8），生成 T1/T3 exact-floor 候选各一（均匀无放回抽样、保持原始行序、零表达变换）。"
- evidence: "artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/（RUN_LOCK.yaml、RESULT.md、floor_constructor_diff.tsv、protected_checks/floor_checks.json 全 PASS、重跑字节级一致）。"
- boundary: "floor parity 未在本地解决；官方 floor 行子集规则不公开；本地 scorer 只作 smoke。"
- review_trigger: "服务器分数回填（已发生，见 D-20260904-B4P0-002）或官方公开 floor 构造细节。"

### D-20260904-B4P0-002 — exact-floor 探针评分：T1 47.0 / T3 46.8，floor parity 正式 UNRESOLVED
- scope: T1:val v0009、T3:gata4 v0008（B4-P0 L0_EXACT_FLOOR）
- decision: "T1 exact floor=47.0，与分层版 baseline-001 完全相同 → celltype 分层抽样被排除为 -3.0 差距的原因，剩余主要假设为 pred n_obs（5,118 vs scorer 参考工作副本 1,706）或其他 bundle 级差异；T3 exact floor=46.8（+1.5 vs wt_identity 45.3，+1.3 vs v0006/7 45.5）→ 晋级 T3 新 board best，同时确认旧 signed-prior 下游 residual 相对 no-change 有害。T1/T3 均打开 FLOOR_PARITY_UNRESOLVED；Wave 1 低风险候选可继续，但 parity 未解决前复杂候选不作最终 parent；T3 后续对比基准改为 46.8。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §B4-P0；INDEX.tsv v0009(T1)/v0008(T3) 行；deliveries/b4p0__t1__upload__20260904.zip、b4p0__t3__upload__20260904.zip。"
- boundary: "derived T3=46.8/Total≈151.0 待服务器页面确认，不得引用为服务器值；+1.3 为构造/bundle 效应，非机制证据，T3-S1 科学 gate 不变；blocks_submission: false。"
- review_trigger: "服务器页面 Total 与 derived 151.0 不一致；或官方公布 floor bundle 构造；或 Wave 1 完成后 closeout 复核。"

### D-20260904-B4P0-003 — T1 n=1,706 floor 探针 46.8，n_obs 假设被排除
- scope: T1:val v0010 `b4p0_l0floor_n1706`（B4-P0 补充探针 run `…164205…`）
- decision: "v0010（n=1,706）服务器 46.8，比 n=5,118 的 v0009（47.0）低 0.2——细胞数假设被排除为 floor 差距（≈-3 vs 官方 50）的原因；FLOOR_PARITY_UNRESOLVED 维持，剩余解释为本地不可见的 bundle 级差异；T1 selection 不变（v0004=48.5）；Wave 1 可按 provisional-score 身份继续。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §B4-P0 supplemental；INDEX.tsv v0010 行（6994a38e…）；deliveries/b4p0p2__t1__upload__20260904.zip；artifacts/batch4/B4-P0-T1-FLOOR-PROBE2-20260904-v1/（检查全 PASS，重跑字节一致）。"
- boundary: "46.8/47.0 均为 board 分数；derived Total≈151.0 待服务器页面确认；blocks_submission: false。"
- review_trigger: "官方公布 floor bundle 构造；或 Wave 1 完成后 closeout 复核。"

### D-20260904-TOTAL-001 — 服务器确认 Total 151.2，子项分数入库并立规
- scope: 全任务当前 best（T1 v0004 48.47 / T2 embryo v0002 60.15 / heart_interp v0009 57.25 / heart_extrap baseline 50.53 / T3 v0008 46.79）
- decision: "服务器页面确认 Total=151.2（derived 151.24，差 0.04 为服务端舍入，以服务器为准）；五 board 精确分与全部 33 个 per-metric skill 回填 `reports/SERVER_SUBMETRIC_REGISTRY.tsv` 并在 registry 立快照节；即日起每次上传/评分必须登记子项分数（见 submissions/README.md 新增规则）。"
- evidence: "用户 2026-09-04 服务器页面读数；reports/SERVER_SCORE_REGISTRY.md §Current-best snapshot — Total 151.2；reports/SERVER_SUBMETRIC_REGISTRY.tsv（33 行）。"
- boundary: "子项分数只做误差归因与路线诊断，不单独构成机制证据；T2 任务值 55.98 为 board 均值推导，非服务器直接返回值；blocks_submission: false。"
- review_trigger: "下一次 board 分数变化时刷新快照与 TSV；若服务器口径变化则修订本规则。"

### D-20260904-B4T2R1-001 — T2-R1 双 lane 57.3/57.31，均与 v0009 打平，关闭 FGW 离散化微调
- scope: T2:heart:val_interp v0010/v0011（B4-T2-R1 run `…193416…`）
- decision: "L1=57.3（+0.05）、L2=57.31（+0.06）相对 greedy v0009=57.25 均落在 ±0.1 噪声带内 → TIE，不晋级；按预声明停止规则关闭 FGW 离散化微调，不再扫 epsilon；incumbent v0009 留任当前 selection（tie 归现任）；两 lane 之间不声称偏好（差 0.01）。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §B4-T2-R1；INDEX.tsv v0010/v0011 行；metrics/greedy_vs_global.tsv；deliveries/b4t2r1__t2__upload__20260904.zip、b4t2r1b__t2__upload__20260904.zip。"
- boundary: "本地 NFS/Moran/objective 全优但 board 打平——proxy 乐观偏差再添一例，不得用本地诊断宣称离散化胜利；16 个子项已按规则入库；blocks_submission: false。"
- review_trigger: "Wave 1 其余路线（T1-R1/T3-R1）完成后 closeout 复核；或官方口径变化。"

### D-20260905-WAVE1-001 — Wave 1 剩余评分：T3 双 lane 46.95 新 best（打平），T1 四 lane 均未晋级
- scope: T3:gata4 v0009/v0010（B4-T3-R1 run `…010331…`）；T1:val v0011-v0014（B4-T1-R1 run `…195835…`）
- decision: "T3 L1/L2 双双 46.95（+0.15 vs floor 46.8），并列新 board best：旧下游 residual 为主要伤害源获第二实证；L2==L1，不声称 lineage 偏好。T1 四 lane 47.58/47.77/47.85/46.90 均低于 best 48.47（排序 L3>L2>L1>L4），v0004 留任；保守族作为晋级路线关闭。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §B4-T3-R1 / §B4-T1-R1；INDEX.tsv 六行；26 个子项已入库；deliveries 六包。"
- boundary: "derived Total≈151.40 待服务器页面确认，不得引用为服务器值；T3 增益为构造效应，非机制证据，科学 gate 不变；blocks_submission: false。"
- review_trigger: "服务器页面 Total 与 derived 151.40 不一致；或 Wave 2 授权后 closeout 复核。"

### D-20260911-B4T1R2-001 — T1-R2 数据就绪门控：BLOCKED_DATA_NOT_READY，立即停止
- scope: B4-T1-R1-LATE-PROGRAM-BRIDGE（Wave 2 条件任务，进入条件 8 项核查）
- decision: "门控未通过，任务停止，不建 run、不开网络窗口：(1) P0 完成 ✓；(2) 无已登记 allowlist（全仓 grep 仅见 prompt 对 allowlist 的引用性文字，无登记条目）✗；(3) 无可直接使用的已净化 processed expression——T3-S1A 的 atlas 净化输入仅 exact E8.75，不含可连 E9.5 前体的 late program；7 个辅助外链均为人类肝/癌/perturbseq，与小鼠胚胎 late program 无关 ✗；(4) 全量 atlas 含 E10.5+ 阶段，启用即触禁区；(5) 无 mutant 需求 ✓ 但无意义；(6)(7) 满足但无可用对象。按 prompt 判 BLOCKED_DATA_NOT_READY。"
- evidence: "infra/bioinf-data-index/INDEX.tsv（75 行，无 allowlist 条目）；data/external/INDEX.tsv（7 外链，人类非胚胎）；T3-S1A state_input_counts.mtx（exact E8.75 only）。"
- boundary: "这是 prompt 预设的数据停止位，不是科学失败；不得花数天修数据；blocks_submission: false。"
- review_trigger: "未来出现已登记 allowlist + 合规 late-program processed 对象时可重开新 run；本结论不关闭 T1 其他路线。"

### D-20260914-WAVE2-001 — Wave 2 评分：T2-R2 三晋级（含 heart +4.79），T3-R2 双败触发架构重置
- scope: T2 embryo v0009/v0010 + heart v0012/v0013（B4-T2-R2 run `…201037…`）；T3 v0011/v0012（B4-T3-R2 run `…201916…`）
- decision: "embryo L1=61.79（+1.64）晋级、L2=62.29（+2.14）新 best；heart L2=62.04（+4.79）新 best、L1=56.27（-0.98）淘汰；两 board 均为 L2> L1，组成重采样是 mean bridge 之上的增量。T3 双 lane 46.45/46.47 均低于 floor 46.8 → T3 标 ARCHITECTURE_RESET_REQUIRED，Batch 4 内不再追加 T3 手工路线。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §B4-T2-R2 / §B4-T3-R2；INDEX.tsv 六行；42 个子项已入库。"
- boundary: "derived T2=58.29/Total≈153.71 待服务器页面确认，不得引用为服务器值；T3 结论不解除科学 gate；blocks_submission: false。"
- review_trigger: "服务器页面 Total 与 derived 153.71 不一致；或 closeout 复核。"

### D-20260915-B4CLOSE-001 — Batch 4 closeout：Total 153.7 确认，ARCHITECTURE_RESET_REQUIRED
- scope: batch4 全批（P0 + R1×3 + R2×3，T1-R2 BLOCKED_DATA_NOT_READY，T2-R3 closed_unscored）
- decision: "服务器确认 Total=153.7（derived 153.71，差 0.01 为服务端舍入）；S0 达成、S1 未达成、S2 达成（T2 +2.31）、S3 未达成；触发器多项成立（floor 未解、总差距缩小 6.1%、T1<52、T3≤50 且离 68 差 21.05）→ ARCHITECTURE_RESET_REQUIRED；T2 插值 parent（v0010/v0013）保留为增量资产；T2-R3 三 lane 按用户明确决定关闭不评分（artifact 不变，可未来复用）。"
- evidence: "reports/BATCH4_PHASE_REPORT_20260915.md、BATCH4_SCORE_GAP.md、BATCH4_ERROR_SIGNATURES.md、BATCH4_COMPONENT_LEDGER.tsv、BATCH4_PROXY_VS_SERVER.md、ARCHITECTURE_RESET_BRIEF.md、ARCHITECTURE_INPUT_READINESS.tsv；registry Total 153.7 确认节；INDEX T2-R3 三行 closed_unscored 标注。"
- boundary: "closeout 不训练、不生成 H5AD、不改 scored artifact；新架构另行立项，本批不再追加 run；blocks_submission: false。"
- review_trigger: "新架构立项时重读 ARCHITECTURE_RESET_BRIEF.md §9–§12。"

### D-20260916-G0T3-001 — 15 轮目标 T3 五 lane 评分：无晋级（两持平三负），传播-剂量族关闭
- scope: T3 v0013–v0017（G1-T3-R1–R5 run `artifacts/g0/G1-T3-R*-20260916-v1/`）
- decision: "服务器 v0013=46.88（-0.07）、v0014=46.95（持平）、v0015=46.95（持平）、v0016=46.88（-0.07）、v0017=46.84（-0.11），selection 保持 v0009/v0010（46.95）；de_score 五 lane 全钉 39.2（最弱子项不动）；T3 传播-剂量手工族关闭为晋级路线。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §G1-T3；INDEX.tsv 五行 scored；25 个子项已入库；与开工前本地盲性诊断一致（proxy de 0.1739 五连同）。"
- boundary: "scored artifact 不变；T3 上传总挑仍以已证 best 为锚；blocks_submission: false。"
- review_trigger: "新机制出现时重开 T3 建模；当前族内不再追加 lane。"

### D-20260916-G0T2-001 — 15 轮目标 T2-extrap 六 lane 评分：一晋级（v0011 收缩 +0.11），空间族关闭
- scope: T2 heart_extrap v0011–v0016（G1-T2-R2–R5 run `artifacts/g0/G1-T2-R*-20260916-v1/`；R1 为门控轮无新候选）
- decision: "服务器 v0011=50.64（+0.11）→ 新 board best（取代 baseline v0001 50.53）；v0012=50.26、v0013=50.32、v0014=50.26、v0015=50.28、v0016=50.25 均低于 baseline。空间平滑族关闭为晋级路线；selection 更新为 v0011。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §G1-T2；INDEX.tsv 六行 scored；48 个子项已入库。关键反转：本地门判收缩钉死-微负、空间胜出，服务器正好反过来——本地 extrap proxy 在这两族上方向反了，已记 proxy 教训。"
- boundary: "scored artifact 不变；heart_extrap 新最弱项变为 T3；blocks_submission: false。"
- review_trigger: "新机制出现时重开 extrap 建模；空间平滑族内不再追加 lane。"

### D-20260917-G0T1-001 — 15 轮目标 T1 七 lane 评分：无晋级（v0004 留任），收缩族 C1 最优但落入 TIE 带
- scope: T1 v0015–v0021（G1-T1-R1–R5 run `artifacts/g0/G1-T1-R*-20260916-v1/`）
- decision: "服务器 v0015=48.51（+0.04）/v0019=48.54（+0.07）落入 ±0.1 TIE 带 → v0004（48.47）留任；v0018/v0020=48.48（+0.01）TIE；v0016=48.14/v0017=47.46/v0021=48.34 REJECT。收缩族内 C1>C2=C4 排序成立但全程仅 0.20 跨度，C 为弱旋钮，关闭收缩扫参。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §G1-T1；INDEX.tsv 七行 scored；28 个子项已入库。T1 本地 proxy 方向存活（PROMOTED 全 ≥48.34，rejected 全低于），三任务中唯一正对照。"
- boundary: "scored artifact 不变；selection 不变；blocks_submission: false。"
- review_trigger: "新机制（非收缩族）出现时重开 T1 建模。"

### D-20260917-G0T3R9R13-001 — 30 轮计划 R9–R13 五 lane 评分：一持平（v0023 46.95）+ 一灾难（v0025 43.30），selection 不变，空间族关闭
- scope: T3 v0021–v0025（G1-T3-R9-HOP2 / R10-GRAPH / R11-SIGNMAX / R12-DEBIAS / R13-SPATIAL；统包 `g1t3__t3__upload__20260917.zip` 内 5 成员；R6–R8 同包仍待评分）
- decision: "服务器 v0021=46.88（-0.07）、v0022=46.93（-0.02）、v0023=46.95（持平 exact TIE）、v0024=46.90（-0.05），四 lane 均落 ±0.1 TIE 带 → selection 保持 v0009/v0010（46.95），不做 late-tie 共晋级（先例 G1-T3-R2/R3）；v0025=43.30（-3.65）灾难性淘汰。空间平滑族在 T3 关闭为晋级路线。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md §G1-T3-R9..R13；INDEX.tsv 五行 scored；25 个子项已入库。de 首动（R10/R11 de=39.6，+0.4 vs 十连钉 39.2）但 variogram 回吐（49.0/49.6 vs 51.0）；R13 mmd 42.1/variogram 25.0，复刻 T2-extrap 空间族本地胜→服务器败。"
- boundary: "scored artifact 不变；Total 153.7 不变（T3 best 未动）；R6–R8 回分前不做新 claim；blocks_submission: false。"
- review_trigger: "R6–R8 分数返回；或新机制（非空间/传播-剂量族）出现时重开 T3 建模。"

### D-20260917-T1P02-001 — T1 P0-2 仲裁：D4 先行，D2/D3 随后，D1/D5/D6 押后，D7 数据 blocked
- scope: G1_T1_30ROUND_RESEARCH D1–D7（OPT-A=scIMF 联合 VAE+SDE；OPT-B=CellMNN 局部线性 ODE；D3=OT-CFM；D4=T2 桥移植；D5=条件扩散组合；D6=势景观 SDE；D7=E7.75 对齐）
- decision: "出场序 D4 → D2 → D3 → D1 → D6/D5 → D7。D4 数据齐＋CPU 便宜＋proxy 门可用，最先；D2 论文与 benchmark 双强、单阶段比 SDE 便宜，代码未定位则按 ICLR 论文实现；D3 TorchCFM 现成，需单细胞适配＋panel-then-fullgene；D1 代码现成但最重（SDE＋Sinkhorn），等 D2/D3 方向信号；D5/D6 GPU 重，届时按原型成本二选一；D7 等 E7.75 下载解 block。R1 wall 768s 证明小 lane CPU 可跑，原型一律先 CPU，GPU 只为 D1/D5 级租赁。"
- evidence: "T1_TRACKING P0-2 行；scIMF PLOS pcbi.1013916＋QiJiang-QJ/scIMF；CellMNN ICLR 2026 proceedings（代码未定位，czi-ai 同名假友禁复用）；TorchCFM atong01；Squidiff siyuh＋Nat Methods 2025；mass_plan_heart.tsv 本地齐；E7.75 缺（OFFICIAL_SYNC/INVENTORY 已定性）。引文订正：scTimeBench=bioRxiv 预印本＋9 方法，实质结论成立。"
- boundary: "外部时序预训练（reset §9）在 D 系无直接 lane，记为后续调研缺口，不阻塞出场；全转录组 decoder 在 D2/D3 实现时单列核查（PCA-first 可疑）；§10 四禁令延续；blocks_submission: false。"
- review_trigger: "D4 本地门结果；D2 代码定位成功；E7.75 下载完成；任一 lane 服务器仲裁。"

### D-20260917-T1D7-001 — 撤回 E7.75 下载要求：T1 用途合规但即时需求不成立，D7 转 PARKED
- scope: T1-D7（E7.75 background＋时间扭曲对齐）；用户质疑下载必要性
- decision: "撤回下载要求。合规核查：E7.75 的 absolute-holdout 身份属于 T2-embryo（hidden test E7.75，外部数据禁区 [E7.5, E7.75]，conservative policy 未 clearance 前外部实测数据不启用）；T1 侧 E7.75 是 contract 明示 background（task_contracts.yaml 第 23 行）＋protected_windows T1 explicitly_allowed（含 stage≤E9.5）＋OFFICIAL_SYNC 限定'只能按官网用途作为 T1 background'＋pseudo_holdouts T1_sanity_holdout 列 optional_background——T1-background 用途合规，但防火墙是禁入 T2-embryo（INVENTORY 原话：不能把它当作 T2 embryo 的 E7.75 target 使用）。不下载的理由：D7 排仲裁末位、价值只是'多一个锚点'（且 pseudo_holdouts 已注 whole-embryo 非 matched-heart，收益本就打折），911MB 登录下载＋provenance 成本现在不值得。D7 转暂缓 PARKED。"
- evidence: "OFFICIAL_SYNC.md §2/§7；protected_windows.yaml（T1/T2_embryo 条款）；pseudo_holdouts.yaml T1_sanity_holdout；OFFICIAL_DOWNLOAD_INVENTORY.md §3。"
- boundary: "将来若触发（D4→D5 均败），下载前重议防火墙：文件落盘即登记、T2-embryo 工作区隔离、provenance 进 infra/bioinf-data-index/；blocks_submission: false。"
- review_trigger: "D4→D5 均败且需新数据轴；或 organizer 对 E7.75 出新口径。"

### D-20260917-T1D7-002 — E7.75 缓存订正：not released，D7 由 PARKED 转 CLOSED
- scope: E7.75 缓存记录（SYNC §2/§7、INVENTORY §3）＋T1-D7
- decision: "2026-09-17 实抓 https://virtualembryo.ai/challenge/data：E7.75 行为'unused / not released — held out as the Task-2 embryo test stage'，'no measured data from that stage is distributed for any task'。此前'released/911MB/登录下载'缓存作废（官方页优先于静态快照），三处文件已订正并记录来源日期。T1-D7 前提（能拿到 E7.75）不存在，由 PARKED 转 CLOSED，D-20260917-T1D7-001 的下载触发条件作废；禁从第三方镜像补齐（withheld 清单＋protected window）。出场序删除 D7，止于 D6/D5。"
- evidence: "官网 Data 页 2026-09-17 实抓原文；SYNC/INVENTORY 订正 diff。"
- boundary: "若官网未来发布 E7.75，重开需新决议＋合规重议；blocks_submission: false。"
- review_trigger: "官网 Data 页 E7.75 状态变化。"

### D-20260917-T1P23-001 — D2 调参挂起（用户特批）＋D3 开工
- scope: T1-P2 执行分支切换（D2→D3）
- decision: "用户裁决：D2 不关闭，dz=20 加 patience/调参挂起入 TODO 暂缓（触发条件 D3/D1 双败或另行指示）；执行分支切为 T1-P2 D3 OT-CFM。明确记录：D2 调参踩收缩/sweep 类调参红线，本次为例外特批，不构成先例；复活时仍须过同一本地门（de>0.8868 且 dir>0.8895），门槛不降。"
- evidence: "dz20 run RESULT.json（410 步稳定，de 0.8113/dir 0.8652 挂门）；用户原话'D2调参进入TODO，开始D3'。"
- boundary: "D2 调参冻结当前脚本与种子，复活即开新 run 目录；blocks_submission: false。"
- review_trigger: "D3/D1 双败；或用户另行指示。"

### D-20260917-T1D3-001 — D3 全基因门 FAIL 关闭：panel 成功未传导，P2 进 D1（待 GPU 批）
- scope: G1-T1-D3-FLOW（panel PASS → full 1200 步；v0022 未建）
- decision: "门 FAIL 即关闭：全基因场回报 energy 0.4855 差于基线 0.4340（cosine 0.8125 优于 0.7796 但门要双指标），不建 v0022，不上传；D3 关闭；P2 进 D1 OPT-A。D1 为 GPU 级（SDE＋Sinkhorn），启动前需 P0-3 租赁批准。"
- evidence: "run 内 RESULT.json/RESULT.md（足额 1200 步，wall ~26min）；panel 门 PASS 记录（energy 4.6×/cos 0.985）同 run 可查，同 scaler 下比较有效。"
- boundary: "panel→full 的传导失败记为 D3 机制结论（高维 OT 耦合噪声主导），不是实现 bug——实现链（vendor loss＋积分＋门）全程 PASS；blocks_submission: false。"
- review_trigger: "D1 本地门结果；V100 上机启动。"

### D-20260917-T1GPU-001 — V100 沿用获批＋OPT-A(c) 修订（去 E7.75 锚点）
- scope: T1-P2 D1（OPT-A scIMF 式联合 VAE＋Transformer-MV-SDE）上机准备
- decision: "用户批 V100 沿用链路，待登录方式。OPT-A(c) 修订：原三点 DOT（E7.75 作锚点正则）回退为两点 DOT E8.5→E9.5（论文原装）＋预报 E9.5→E10.5——E7.75 CLOSED（D-20260917-T1D7-002），锚点前提不存在。验证门不变：E8.5→E9.5 回报 held-out 先行，standing 双门（de>0.8868 且 dir>0.8895）过才碰 E10.5。scIMF repo（QiJiang-QJ）LICENSE 未明示（main/LICENSE 404），沿 D2 先例按论文规格自实现，repo 仅作对照、不 clone。候选构建与 contract/scorer 链放本地，GPU 只回传 checkpoint（~MB 级），训练数据外不出境。"
- evidence: "用户原话'沿用v100，现在做好准备，等待登陆方式即启动工作'；G1_T1_30ROUND_RESEARCH.md §3 OPT-A；LICENSE 404 实抓。"
- boundary: "GPU 机只跑训练（locked run：network/external/server_submission 均为 false，除 pip 依赖安装）；候选/上传仲裁仍走本地链；blocks_submission: false。"
- review_trigger: "登录方式到达即上机；D1 本地门结果。"

### D-20260917-T1D1-001 — D1 回报门 FAIL 关闭：联合 VAE+SDE 塌向均值
- scope: G1-T1-D1-SCIMF（V100 足额训练＋本地回报门）
- decision: "门 FAIL 即关闭：回报 de 0.3585/dir 0.6243 双远低于门（-0.53/-0.27），不建 E10.5 候选，不上传；D1 关闭。非 marginal，加步同配方难救；修复属重加权/重架构＝新 lane，不在本次重跑之列。P2 剩 D5/D6（皆 GPU 级，需新设计＋续租决策）。"
- evidence: "run 内 RESULT_train.json（870 步无 NaN）＋BUILD.json（回报 contract 实质 PASS，行身份 FAIL_BY_DESIGN 沿 D4 先例）＋RESULT.md；坍缩签名 variance 0.086。"
- boundary: "GPU 机闲置保留，续租/释放由用户定；blocks_submission: false。"
- review_trigger: "D5/D6 启动决策；或 D1 重设计授权。"

### D-20260917-T1GPU-002 — D5/D6 全开＋费用纪律：完工即关机
- scope: T1-P2 D5（条件扩散）＋D6（势景观SDE）；V100 计费
- decision: "用户指令：D5/D6 全开，快开；任务完成之后及时关闭实例（烧钱）。执行：D5 先行（脚本→冒烟→GPU 训练），D6 排队（D5 训练期间写码，GPU 空出即上）；任一 lane 回报门 FAIL 即关，不续跑烧钱；全部完工（或双败）后即关机——先远程 poweroff，再请用户控制台确认释放（面板侧停止才停费的按面板为准）。 early-stop/patience/cap 一律从紧， wall 上限单 lane 4h。"
- evidence: "用户原话'开，快开，任务完成之后要及时关闭实例，你烧了我的钱！'"
- boundary: "关机前必须回传全部 checkpoint＋RESULT＋日志；blocks_submission: false。"
- review_trigger: "D5 回报门结果；D6 上机；双败或完工即关机。"

### D-20260917-T1D5-001 — D5 回报门 FAIL 关闭：扩散回报分布崩（8×），门腿空转设计债
- scope: G1-T1-D5-DIFF（V100 足额训练＋本地回报门）
- decision: "门 FAIL 即关闭：场回报 energy 2.203 差于基线 0.265（8×），compJSD 双边 0.1555 全同；不建 v0024，不上传；D5 关闭。非 marginal，不加训。P2 进 D6。"
- evidence: "run 内 RESULT_train.json（680 步无 NaN）＋BUILD.json＋RESULT.md。设计债：逐持留细胞类型生成迫使成分一致，JSD 腿空转——门实质单指标（energy）；如实记录，不追溯修门（移动门柱，§10）。"
- boundary: "D5 扩散路线关闭；v0024 空号保留不再用；blocks_submission: false。"
- review_trigger: "D6 回报门结果。"

### D-20260917-T1UPLOAD-001 — 本地门降格为上传筛选器：单门显著优＋余门无显著劣→一次上传仲裁
- scope: 全任务上传政策（由此前 D3 全基因门 FAIL 争议触发）
- decision: "用户裁决：本地计分不完全可靠，standing 门不再一票否决上传。今后：某 lane 在任一本地门上显著优化、其余门无显著劣化，即建候选走一次服务器上传仲裁（8/task/day 内）。D3 v0022 首适用（cosine 0.8125>0.7796 显著优，energy 差记入风险由服务器仲裁）。本条为例外政策，与 §10 禁 proxy-win 直写'晋级结论'不冲突——上传仲裁≠晋级宣称，回分前仍只能记 score_pending。"
- evidence: "用户原话（2026-09-17）：本地计分不一定准确，全基因门给结果上传试一下。"
- boundary: "上传仍须 contract PASS＋字节一致＋INDEX 登记；blocks_submission: false。"
- review_trigger: "上传仲裁连续两次证伪本地门（双向误判统计）。"

### D-20260917-T1D3-002 — v0022 服务器仲裁 REJECT（45.3）：上传仲裁政策首战即证伪，proxy 教训修正
- scope: G1-T1-D3 v0022（单包上传仲裁，D-20260917-T1UPLOAD-001 首适用）
- decision: "服务器 45.3（-3.17 vs best 48.47，低于 floor 47.0），REJECT；selection 保持 v0004；D3 维持关闭。上传仲裁政策本身按设计工作（仲裁回 REJECT，未宣称晋级）。"
- evidence: "registry §G1-T1-D3；INDEX v0022 行 scored；4 子项已入库。加权验算 45.31→45.3 ✓；分项增量 de -0.1/dir 0.0/mmd -3.6/vario -10.4。"
- boundary: "proxy 教训修正入库：T1 首个本地假阳性——本地 de 0.9623 传成服务器持平，崩盘点在 variogram（-10.4）；但本地 energy 旗预警正确。细化 doctrine：de/dir 须分布侧本地指标连署。G0 正对照结论收敛适用范围，不推翻。blocks_submission: false。"
- review_trigger: "再一次本地/服务器双向误判即重审门权重。"

### D-20260917-T1D4-001 — D4 门 FAIL 关闭：组成锚定无回报信号，P2 进 D2
- scope: G1-T1-D4-BRIDGE-20260917-v1（脚本 scripts/g0/t1_d4_bridge.py；门 G E8.5→E9.5 回报）
- decision: "门 FAIL 即关闭：G1（位移＋E9.5 份额锚定）de 0.4151/dir 0.5869 双低于 G0（纯位移）0.566/0.6127，不建 L1/L2 候选，D4 关闭；P2 仲裁序进 D2（OPT-B，按 ICLR 论文实现）。"
- evidence: "run 内 RESULT.json/RESULT.md；门臂 contract FAIL 仅 cell_limits（诊断件 16,787 行超板限），基因序/finite/非负/obs 唯一全 PASS，scorer 分布比较有效。"
- boundary: "组成雷区第四确认（v0002 −1.1、B4 graft ≤47.85、今回报 −0.15）；D4 的 k=0.25 收缩份额、`__dup`+ledger 重采样件随门同葬，不进入候选；blocks_submission: false。"
- review_trigger: "D2 本地门结果；或新的组成机制证据出现。"

### D-20260917-T1D2-000 — 订正：CellMNN 代码已定位（论文自引 czi-ai），仍按论文自实现
- scope: D-20260917-T1P02-001 中的“OPT-B 代码未定位 / czi-ai 同名假友禁复用”
- decision: "订正：ICLR 论文全文（摘要页＋§Reproducibility）自引 github.com/czi-ai/cell-mnn，假友结论作废。但 D2 仍按论文规格自实现、不 clone（免 license 审计＋免网络窗口）；repo 仅作实现对照。设计稿见 artifacts/g0/G1-T1-D2-CELLMNN-20260917-v1/DESIGN.md，待用户过目后写码。"
- evidence: "arXiv:2510.02903v2 PDF（27pp）§2.1/Table 3/App F；repo URL 论文内两处。"
- boundary: "订正只改代码可得性判断，不改出场序与门；blocks_submission: false。"
- review_trigger: "D2 写码启动。"

### D-20260917-T1D2-001 — D2 首跑 VOID（step-41 发散）：门按 intent 不判晋级，warmup 后单次重跑
- scope: G1-T1-D2-CELLMNN 首跑（dz=50，论文原损失＋λ-clamp/grad-clip guards）
- decision: "首跑 VOID：proxy de 0.9434/dir 0.9519 字面过门，但 step-41 NaN（仅 ~8k 细胞更新），候选非 designed-lane 产物，不注册 v0022、不上传；伴随分布坍缩（variance 0.21/energy 6.48），富集 18.69 同作废。单次重跑：L_inv warmup ramp（50..200 步）；再 NaN 则降 dz=20 或关 D2。字面过门但训练失败的 lane 按 intent 不得晋级——此即 §10 禁 proxy-win 直写晋级在本案的适用。"
- evidence: "run 内 RESULT_VOID_01.md＋RESULT.json（nan_loss_at_step=41）；DESIGN §7 补丁。"
- boundary: "void 只杀本次 run，不杀 D2 机制；重跑仍走双门；blocks_submission: false。"
- review_trigger: "warmup 重跑结果。"

### D-20260917-T1D6-001 — D6 回报门 FAIL 关闭：de 恰等门线不算过＋GPU 已关机
- scope: G1-T1-D6-POT（V100 足额训练＋本地回报门）
- decision: "门 FAIL 即关闭：回报 de 0.8868 恰等于门线 0.8868（须严格大于，不算过），dir 0.7921 差 0.097；不建 v0025，不上传；D6 关闭。平局适用服务器 TIE 带、不适用本地门（§10，无移动门柱）。费用纪律执行：GPU 实例 OS halt（双线验不可达），控制台释放待用户确认。"
- evidence: "run 内 RESULT_train.json（825 步无 NaN）＋BUILD.json（回报 contract 实质 PASS）＋RESULT.md；坍缩签名 variance 0.26（D1 0.086/D2-void/D6 0.26 三连）。"
- boundary: "P2 GPU lane 清零；D2 调参触发条件已满足（D3/D1 双败），启动待用户定夺；blocks_submission: false。"
- review_trigger: "D2 调参启动；或新架构立项。"

### D-20260917-T1AUDIT-001 — 独立复核：D5 测试无效（模型缺阶段条件＋门 JSD 腿不可满足），其余 verdict 确认
- scope: 本轮 T1-P2 全部 lane（D1/D5/D6 GPU＋D2/D3/D4 CPU＋v0022 上传）：脚本重读＋JSON 数字复核＋SHA 重验
- decision: "D1/D6/D4/D2/v0022 verdict 全部确认无误；D5 的 FAIL  verdict（不建 v0024）维持，但理由订正：测试无效而非机制证伪。D2 run-local 重名目录已改名去雷（v0022X_…_UNREGISTERED），未注册产物零影响。"
- evidence: "(1) D5 主 bug：t1_d5_diff.py 里阶段时间条件 tc 建而不用（L262 建、L265 den(x,tcur,ty) 未传；训练侧 L218 同样丢弃 tt0；Denoiser 输入唯一标量是扩散步不是阶段）→ generate(tcond=1.0) 与 (2.0) 输出全同，模型学的是阶段混合 p(x|type)，回报 energy 8× 差主要由此解释。DESIGN 的 t=2 外推风险披露针对的是不存在的机制。(2) D5 门 bug：JSD 腿按持留类型逐个生成、成分被迫一致 → 要求严格更优的腿恒为平局 → 门恒不可通过；能量腿再好也救不回来。两 bug 叠加：扩散假设未经检验。(3) 确认项：D1 真 held-out（h_mask 排除训练）、D5/D6 为样本内回报（保守方向，不翻转 FAIL）；D6 de 0.8868 为 scorer 实算（FULLSCORER 独立文件一致），dir 差 0.097 verdict 鲁棒；D2 dz20 数值/未晋级、D4 双低、v0022 SHA 与 INDEX 一致、v0004 未动、三 checkpoint SHA 全对、submissions 无 v0023/24/25 孤儿。"
- boundary: "D5b（补阶段条件＋释放成分别腿）属新 lane，需立项＋约 15 分钟 GPU，不属重跑；开不开用户定。D2 调参问题仍悬。blocks_submission: false。"
- review_trigger: "D5b 立项；或 D2 调参启动；或 T1 封存。"

### D-20260917-T1D5B-001 — D5b 新 lane 立项：审计修复＋CPU 先行，零 GPU 花费
- scope: G1-T1-D5B-DIFF（D5 的审计修复子 lane）
- decision: "立项 D5b：Fix A 阶段条件实接线（含冒烟敏感性断言——D5 缺的正是这个测试）、Fix B 全 schedule 采样、Fix C 可满足分布门（overall＋per-type energy，JSD 腿删除、成分输入化）＋坍缩 veto；其余配方冻结以隔离修复效应；同种子保基线可比（build 内断言基线复现 0.265）。用户令 CPU 先行：本地全量训练＋建门，不开机不花钱。交付 v0026。"
- evidence: "DESIGN.md（6 节）＋t1_d5b_diff.py（d+2 输入、lane 标记防 D5 ckpt 误装）。"
- boundary: "D5b 是新 lane 不是重跑；v0026 空号启用；blocks_submission: false。"
- review_trigger: "D5b 回报门结果。"

### D-20260917-T1D5B-002 — D5b 回报门 FAIL 关闭：接线修好后暴露严重欠拟合，27× 落败
- scope: G1-T1-D5B-DIFF（CPU 全量训练＋本地回报门，零 GPU 花费）
- decision: "门 FAIL 即关闭：场 overall energy 7.23 差基线 0.265（27×），per-type 12.12 差 0.63（19×）；不建 v0026，不上传；D5b 关闭。基线复现断言通过（同设置可比成立）。诊断：20 epochs 的 score 又糙又错，正确全 schedule 采样把误差放大到底（library 4.3×/方差 2.2× 发散状）；D5 的截断采样是误打误撞的正则。公平检验扩散需 ~10× 训练量＝新假设 D5c，不属重跑，开不开用户定。"
- evidence: "run 内 RESULT_train.json（680 步无 NaN）＋BUILD.json（基线 0.26469780398582543 精确复现）＋RESULT.md；重读代码未发现新 bug（接线顺序/采样器/数据通路一致）。"
- boundary: "扩散线两连败但死因不同（D5 测试无效，D5b 欠拟合发散）；‘扩散证伪’仍不成立，‘扩散可 promotion’同样无证据。D2 调参仍悬。blocks_submission: false。"
- review_trigger: "D5c 立项；或 D2 调参启动；或 T1 封存。"

### D-20260920-G0T3R6R8-001 — T3 R6–R8 评分回填，统包评分闭环

- scope: G1-T3-R6/R7/R8；仅登记和评分决策。
- decision: "T3 R6–R8 分数回填完成：v0018=46.94（TIE）、v0019=46.95（exact TIE）、v0020=46.64（REJECT）；selection 保持 v0009/v0010=46.95。R6–R13 八候选均已评分，余分队列清零，后续轮次待决定。R8 淘汰为晋级候选；R6/R7 不替换 incumbent。"
- evidence: "用户本轮提供的三个 board 分数和 15 子项，原值见 reports/SERVER_SCORE_REGISTRY.md 的 G1-T3-R6..R8 节及 reports/SERVER_SUBMETRIC_REGISTRY.tsv；成员映射和本地 SHA256 核对通过。submission ID、上传时间和新 Total 未提供，不补造。"
- boundary: "不把评分闭环写成 30 轮全部执行，不新增训练或上传；科学 gate 不变，blocks_submission: false。"
- review_trigger: "用户决定下一轮路线。"


### D-20260920-T3NEXT-001 — 六路线实现与可行计算收口

- decision: "R1/R2 四候选 v0026/v0027/v0030/v0031 待人工上传回分，selection 不变；R3 FAILED_DISASTER（裁剪 6.19%/2.68% > 1%），R4 FAILED_MAPPING_GATE；R5 BLOCKED_PROVENANCE、R6 BLOCKED_DATA_NOT_READY，正式计算 NOT_RUN。"
- evidence: "reports/T3_NEXT_EXECUTION_20260920.md 与 .json；configs/t3_next/design.json；候选身份以 submissions/INDEX.tsv 为准；12 项定向测试通过，交付包四候选哈希/CRC 通过。"
- boundary: "v0028/v0029 自 donor 对照缺陷导致 invalidated_unsubmitted，原文件不可变且排除上传；修复重跑生成 v0030/v0031。不用错靶 local scorer，不放宽门槛，不宣称新 best 或科学识别；blocks_submission: false。"
- review_trigger: "四候选服务器分数与原始证据，或 R5/R6 所缺的合规输入到位。"


### D-20260920-T3DATA-001 — R3/R4 待修复，R5/R6 首轮数据收集

- decision: "按用户要求将 R3 非负输出/传播修复、R4 跨平台映射修复写入 TODO，未执行；线上优先选 GSE261783 OP2 静息两个样本，metadata-first 后下载并隔离过滤为 5454×32287，26 个候选扰动，另有 220 对照细胞计入总细胞数，panel 500/500。R5 关系资源与 37 张 panel 引用卡片已收集。"
- evidence: "reports/t3_data_intake_20260920/REPORT.md；SOURCE_SHORTLIST.tsv；COLLECTION_MANIFEST.json；FIBRO_FILTER_RECEIPT.json；FILTER_VALIDATION.json；R5_RESOURCE_AUDIT.json。生信索引同步。"
- boundary: "所有新文件 QUARANTINE_NOT_APPROVED，model_input=false；固定 blacklist 零命中不等于完整 phenocopy 审查通过。generic Perturb-seq 响应形状用途/许可未闭合，R5 许可和下游 target 链未闭合；正式训练/归一化/embedding/候选生成均 NOT_RUN。既有候选待评分和 selection 不变。blocks_submission: false。"
- next_action: "完成明确剩余的数据准入与用途审查；R3/R4 保留待办。不替组织者发消息、不自动把已收集文件晋级为模型输入。"
