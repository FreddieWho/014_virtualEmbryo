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

## D-20260920-T3R56PREP-001

- decision: 完成GSE261783第二次隔离过滤和R6用途门；原signed路线不得消费shape-only许可。新增shape后继设计与基础函数，未称为完整实现。
- evidence: reports/t3_r56_readiness_20260920/REPORT.md；PREPARATION_RECEIPT.json；R6_CONDITION_REVIEW.tsv；4项针对性测试通过。
- boundary: 4998细胞/23扰动仍QUARANTINE，3扰动保守排除不等于其他扰动通过；R5完整批准链0；书面确认NOT_PRESENT，草稿NOT_SENT；标准化、图、训练、候选均NOT_RUN。未提交/未评分，blocks_submission: false。

## D-20260920-T3R5SOURCE-001

- decision: R5采用最小SIGNOR CC-BY4通用非目标信号拓扑，逐边审核4关系、5节点人鼠一对一映射，聚合为Pdgfb/Pdgfrb/S100a10；仅官方WT拟合系数。生成父v0009的v0032/v0033，未提交/未评分。
- evidence: reports/t3_r5_completion_20260920/SOURCE_MANIFEST.json、FILTER_RECEIPT.json、EDGE_CONTEXT_REVIEW.tsv、EXECUTION.json；artifacts/t3_next/T3-R5-SIGNOR-MINIMAL-20260920-v1/RESULT.json；submissions/INDEX.tsv。
- boundary: 跨背景拼接为探索性先验，不是已验证的胚胎因果链；信号改变量小，服务器提升未知。原始全网络未批准，未使用外部响应值/符号/权重。R6保持隔离，不通过本许可放行。blocks_submission: false。
- rule attribution correction: 官网§10无所有外部Perturb-seq统一书面预审批或shape-only条款；两者来自本地2026-08-29保守解释。R5该范围为允许的通用pathway知识，不含受保护目标特异边或外部表达训练。不能把内部审查称为主办方批准。

## D-20260920-T3NEXTSCORE-001

- decision: 登记用户提供的R1/R2四候选总分及20子分。R1两候选分别与父版本同分，不晋级；R2两候选低于父版本，淘汰当前候选。selection v0009/v0010保持。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t3-next-r1r2-score-return-20260920；submissions/INDEX.tsv四个SHA实核一致；submission ID/time未提供，不伪造。
- boundary: 观察到自适应优于随机不等于优于基线或统计显著；无新模型训练。R5 v0032/v0033仍未提交/未评分。blocks_submission: false。
- rule_review: reports/T3_INTERNAL_RULE_REVIEW_20260920.md建议取消shape-only合规硬限制、统一书面确认和以通路关联替代phenocopy判定；本次只评审，现行规则/代码/数据许可未修改。

## D-20260921-T3POLICY-LAUNCH-001

- authorization: 用户要求按评审修改内部规则并准备开启R5/R6。
- decision: 生效政策 `docs/coordination/T3_EXTERNAL_DATA_POLICY_20260921.md` 替代旧shape-only及统一书面确认硬限制；保留按来源/条件审查、真实疑问隔离、许可和哈希。R6代码改用hash绑定ALLOWED review及condition allowlist；旧快照和permit不追改。
- execution: GSE261783 OP2选定26条件重新审查通过；Chd4/Smarca4/Yy1经实际成人实验背景复核恢复。5454×500标准化矩阵、27×80 WT特征和27×27图已准备，使用原净化WT全部68910细胞。R5既有两候选身份复核通过。
- evidence: reports/t3_r56_launch_20260921/REPORT.md、SOURCE_REVIEW.json、READINESS.json、GRAPH_PROVENANCE.json、VALIDATION.json；19项针对性测试通过。
- boundary: R6仅READY_FOR_R6_TRAINING，预测器训练/gene holdout/目标推断均NOT_RUN；无新候选。R5 v0032/v0033未提交/未评分。许可不跨task自动传播；成人→胚胎泛化未知，blocks_submission: false。

## D-20260921-T3R6RUN-001

- authorization: 用户“路线六开始”。
- execution: 原设计完成100步留出训练、26来源基因最终训练和Gata4推断；图模型通过整基因留出门槛，两个输出均失败负值门槛。
- decision: 本次run收口FAILED_DISASTER，0候选，不自动放宽1%门槛或修改设计。R6非负输出修复进入TODO；selection保持。
- evidence: reports/t3_r6_execution_20260921/REPORT.md、DIAGNOSTICS.json；artifacts/t3_next/T3-R6-OP2-20260921-v1/RESULT.json及两个权重。
- boundary: 未提交/未评分；源域留出通过不证明成人→胚胎泛化，完整Gata4真值评分NOT_RUN。blocks_submission: false。

## D-20260921-T3R5SCORE-001

- authorization: 用户要求登记R5两个候选的服务器回分。
- decision: v0032/v0033均与父版本同总分，不晋级；on/off全部回报指标相同。R5本轮SHIPPED，无已观测增益，selection保持v0009/v0010。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t3-next-r5-score-return-20260921；两个本地artifact SHA与INDEX一致；submission ID/time未提供。
- boundary: 显示精度相同不证明通信机制无效；未新建候选、训练或提交。科学状态不变，blocks_submission: false。

## D-20260921-T3REVIEW-001

- authorization: 用户要求复核本轮1–6及历史T3技术路线并整合汇报。
- decision: 仅形成优化建议，优先R6非负输出与强基线、R3机制输出、R4残差映射；R5/R1作为组件，R2整细胞替换与旧全表达平滑不原样重跑。既有verdict和selection不变。
- evidence: reports/t3_route_review_20260921/REPORT.md、CHECKS.json、check.py；R1/R5真实文件差分及R6训练集平均响应、最终权重推断诊断。
- boundary: 无新GCN训练、候选、提交或分数；补充对照非预注册，成人→胚胎泛化未知。旧替代实现不等同于原论文方法失败；blocks_submission: false。

## D-20260921-T3REPAIR-001

- authorization: 用户在全路线复核后要求“好的你来开始修”。
- decision: 完成第一优先级R6/R3/R4修复和完整数据执行，交付六候选；仅结构/格式通过，不晋级。R1叠加R6为NO_OP；R5扩链尚未执行。
- execution: R6样本内NTC/非负倍率及强对照，R3四空间块/比例机制，R4五基因组×四块残差映射及真正应用斜率的panel/中介推断；23测试通过。
- correction: R4 v1评估/推断校准不一致，未提交v0038/v0039撤回保留；v2完整重跑生成v0040/v0041。原失败记录及旧评分不改。
- evidence: reports/t3_repairs_20260921/REPORT.md、VALIDATION.json、R4_WITHDRAWAL.json；候选身份SHA见submissions/INDEX.tsv；上传包deliveries/r634fix__t3__upload__20260921.zip及receipt。
- boundary: R6图未胜过平均响应/平均倍率/置乱图，跨样本不稳定；R3/R4的WT评价不是KO验证。新候选未提交/未评分，selection v0009/v0010保持；blocks_submission: false。

## D-20260921-T1NEXT-001

- authorization: 用户要求按T3方案形式准备T1六路线方案。
- decision: 发布T1-NEXT-R1–R6，分离边际、残差、稳定动力学、模块运输、依赖结构与早期时间数据；建议实施顺序R2→R1→R5→R3→R4→R6。全部PROPOSED / NOT_RUN，未启动旧D2调参或D5b重跑。
- evidence: reports/T1_NEXT_ROUTES_20260921.md；SERVER_SCORE_REGISTRY、INDEX、D系列receipt；官方RNA metadata实读仅celltype且无layers；文献原站链接见方案。
- status_correction: D5b最终RESULT为FAIL且无v0026，更新旧摘要；v0004仍为selection，v0019按原TIE规则不晋级。官方E7.75未发布，外部T1许可不继承T3。
- boundary: 无新模型/候选/评分/下载；两点细胞留出不是独立时间外推，未证明E10.5或E12.5泛化；blocks_submission: false。

  - boundary: 零候选、零评分、零上传；T2 自此无未跑的已规划路线；heart_extrap 50.64-vs-50.53 的聚合差异仍未闭合；blocks_submission: false。

## D-20260927-T2LEADS-001

- authorization: 用户于 2026-09-27 授权执行 T2 两条未完成线索（L-001 同靶 parent 参照、L-002 ε 两值敏感性），并要求其按敏感性分析而非网格搜索定性。
- decision: L-001 关闭——对 T2 embryo parent v0002 跑锁定 scorer（同 pseudo-target E7.25／同 reference E6.75／同 seed 20260830），两个独立耦合指标同向变差（neighborhood_mmd 0.03124→0.03445；morans_I_agreement 0.9722→0.9555），排除“度量偏祥 parent”解释，embryo v0008 的 HOLD_AS_COMPONENT 升级为确证拒绝。L-002 关闭为已放弃——ε=0.002 使 plan 分散度大幅下降（有效来源数降到 18–20%）但效应未在两 holdout 同时变强（H1 反向 +0.000124），预声明升级判据未达成，不再扫 ε。
- evidence: reports/T2_LEADS_CLOSURE_20260927.md；artifacts/tool_integration/T2-L001-EMBRYO-PARENT-REF-20260927-v1/；artifacts/tool_integration/T2-L002-FGW-EPS-SENSITIVITY-20260927-v1/（含复现对照，相对偏差 ≤7.5e-6，容差 1e-4）；scripts/t2_l2_eps_sensitivity.py；scorer 与 parent SHA 均与 P0-LOCK／input_lock 逐位一致。
- method_note: 附带两条方法学结论——J1 的 NFS 镜像在 parent 臂上与官方 scorer 逐位吻合（代理当时无偏差）；冻结 FGW objective 的取值与官方度量镜像在 ε 方向上不对齐（objective 两 holdout 都更低而 NFS 只 H2 降），“objective 降 12.2% ⇒ 方向有效”缺一环。
- boundary: 零候选、零评分、零上传，未消耗提交配额；INDEX 未改；J1-PROXY／J1-FGW-ASSIGNMENT／B4-T2-R1 只读未改；复现对照只到浮点精度未主张位级一致；H1 上 Q2 反向幅度小（相对 +1.1%），不声明“ε=0.002 在 embryo 上有害”；L-001 不能区分“置换无效”与“参考太弱”，二者对 v0008 处置结论相同；L-002 不回答是否存在更优第三值。
- next_action: embryo 若再做行-点配对，前置条件是先修 M 参考构建（bracket 探针为负），已记入 LEADS L-006；heart_extrap 50.64-vs-50.53 聚合差异需重读门户页面。

## D-20260926-T1V23SCORE-001

- authorization: 用户转录 v0023 服务器分数（total 50.82＋四子项），按既定回填链登记。
- decision: v0023 PROMOTED 为新 T1 selection（+2.35，超 TIE 带）；Total 记 156.06；R1 SHIPPED，R2 FAIL（诊断关闭），R6 PARKED（待数据源裁决）；R5/R3/R4 后续对 v0023 基线。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t1-next-r1-score-return-20260926；INDEX v0023 行 scored；SUBMETRIC＋4 行；用户转录原文（ID/时间戳未提供）。
- boundary: 分数未从舍入子项重构；单次仲裁成功不证明 proxy 可靠排序；本次无新拟合/候选；blocks_submission: false。

## D-20260927-T3FIVE-001 — 三条新路线与两条优化交付

用户授权的五路线已全部实现并执行真实数据拟合/评价/目标推断，最终 v0042/v0044/v0046/v0047/v0048 contract PASS，11定向测试与五模型逐值重放PASS；未提交/未评分，selection v0009/v0010 不变。v0043/v0045 撤回保留，分别修正非负decoder与下游稳定性尺度后完整重训。收缩GCN仅小幅优于平均倍率、仍有跨样本失败；WT概率模型仅证明描述性预测优势，不能推导KO有效性。五lane PENDING_SERVER，旧六修复候选仍待回分。报告 reports/t3_five_20260927/REPORT.md；包 deliveries/five27__t3__upload__20260927.zip；blocks_submission: false。

## D-20260927-T2M0FREEZE-001

- authorization: 用户授权 T2 三个 board 各 2 新路线 + 1 条既有路线优化迭代共 9 条 lane，并裁定 5% 为量化阈值。
- decision: 冻结 9 lane 的执行口径。(1) 父版本：embryo v0010(62.29)、heart_interp v0013(62.04)、heart_extrap 迭代父 v0011(50.64)，extrap selection 仍为 baseline v0001(50.53) 不改动，v0011 与 156.06 聚合的 0.11 差异保持 OPEN。(2) 5% 三分类：主指标 neighborhood_mmd（lower-better），degradation%>5% 或任一结构性失败→严重劣势、关闭淘汰且不占名额、触发替补；≤5% 且无签名→轻微劣势、照常交付可提交；边界一律从宽按轻微处理。(3) 每 lane 须同时报告 degradation% 与重复测量相对离散度 disp%（同输入同伪目标 3 个 scorer seed 的极差/均值），未报 disp% 者不得声明落在噪声内。(4) 设计文档 mtime 必须早于 run 目录 mtime，M5 逐条核查。(5) 替补上限每 board 1 条，用尽仍无候选则停止询问用户。(6) 不得重提已耗尽轴：FGW ε 离散化、heart_extrap 空间平滑族、extrap 位移幅度族、embryo 行-点配对（须先修 M 参考构建）。
- evidence: reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md；父版本 SHA 磁盘复算与 submissions/INDEX.tsv 逐位一致；git status --porcelain submissions/ 输出 0 行（无已评分或候选产物被改动）；board 契约取自 artifacts/tool_integration/P0-LOCK/locks/BOARD_REGISTRY.yaml（veckit-0.1.1@46d41e6）。
- counter_evidence_must_cite: extrap 迭代父 v0011（G1-T2-R2-SHRINK）当年本地门判 NOT promoted（neighborhood_mmd 0.20506、de_score 0.2466 钉死）而服务器给 50.64、+0.11、board 最高。若机械套用 5% 会误杀这条已晋级最高分路线，故 5% 只能作筛选器不能作证伪器；同一板另有反向例（空间平滑族本地全胜、服务器全负）。
- boundary: 官方 target 为隐藏集，本地 scorer 无真值为 NOT_RUN_NO_MATCHED_TRUTH 而非跑不通；本地一律用观测期 stage 作 pseudo-target（证据第 4 层）并强制披露；5% 为单板单指标口径，主指标选择理由已在冻结文件写明；outputs/t2_pseudo_holdouts/ 当前未构建，extrap lane 如需 proxy 须先构建且不计 lane 预算；blocks_submission: false。

## D-20260927-T2UNATTENDED-001

- authorization: 用户 2026-09-27 睡前指示三件事——(1) 先跑 M1 两个预执行闸门；(2) **某条路线失败不消耗预算，须继续测试新路线**；(3) **所有形成硬阻隔的决策都尽量避免或推后**（用户将离开，不在线）。
- decision: 进入无人值守窗口，coordinator 的决策权限边界如下。(a) **可自行决定并记名**：pseudo-target 选择、每 lane 2 臂的构成、几何/正则化等实现细节、闸门后对路线做的重定向、6 条新路线的取舍、替补路线的挑选。全部写入 DECISIONS 并在收口报告披露，供用户醒来后追认或否决。(b) **仍然必须停下，不因"避免阻隔"而越过**：改动任何已评分或不可变 artifact；需要目标阶段真值才能拟合（泄漏）；放宽或重定义既有 contract；伪造或推测服务器分数；覆盖用户已明确关闭的路线。(c) 「失败不消耗预算」的操作化：严重劣势淘汰的 lane 不占该 board 的 3 个名额，替补上限仍为每 board 1 条（M0 已定），替补用尽则转入"新路线轮"而非停机——新路线同样须走 researcher 检索 + 设计冻结 + 审稿，且每轮消耗一次用户未明示的算力，故每 board 累计超过 5 条 lane 时必须停下等用户醒来。
- evidence: 用户的原始指示（本次会话）；M0 冻结文件 §8 预算记账与阻塞规则；reports/T2_NINE_ROUTES_20260927_M1_CANDIDATES.md §4 三条检索者自报存疑项。
- boundary: 本决策只放宽"停机等待"这一项，不放宽任何科学或完整性约束；用户醒来后所有 (a) 类决定均标记为"待追认"，用户可否决并要求重做；blocks_submission: false。

## D-20260927-T2GATES-001

- authorization: 用户 2026-09-27 睡前授权「先跑 M1 两个预执行闸门」；并按 D-20260927-T2UNATTENDED-001 授权 coordinator 在无人值守窗口内自决模糊项并记名待追认。
- decision: (1) **官方指标分层判决**——`T2/metrics_v2.py` 明示 `morans_I_agreement` 为 CONSTRAINT 非分数；`variogram_score(pred_X,true_X)` 为 PRIMARY-expression 且**坐标无关**；`d2_shape/occupancy_dice/sliced_wasserstein/scale_log_ratio` 为**纯坐标**指标，而现役几何逐位冻结，故这四个子分对只改表达的候选**恒定不变**。registry 中 heart `variogram` 32.2 为唯一离群项（其余 53–62）。(2) **闸门 A 判 CONFIRMED**：行置换统计不可分辨（均值偏移 −0.81%，落在同输入 6-seed 极差 4.19% 内），仅预测侧基因置乱恶化 **4.35×**，两侧同置乱 0.997×（对称不变）⇒ 度量的是基因间联合结构。原判据逻辑有错（位级阈值 1e-9 + 误用两侧同置乱臂），已在报告中纠正并公开。(3) **闸门 B 判前提未救回**：唯一为正的 V1 仅单方向 +0.0055，researcher 推荐的 V2/V3 全负且不优于基线；我原设的"任一变体任一方向>0"规则过松已纠正。另记：我的 V0 与 J1 历史值不等，因分层子样 seed 依赖 `side` 键。(4) **探针 C**：现役表达桥在两个插值板上**主动破坏**基因间协方差——embryo v0010 0.0907 vs 基线 0.0364（2.49× 更差）、heart v0013 0.0802 vs 基线 0.0557（1.44× 更差）；extrap v0011 0.0027 略优于基线 0.0032。(5) **噪声标定**：`neighborhood_mmd` 零噪声、de/de_direction/morans 零噪声、`variogram` 4.18%、`d2_shape` 4.50%、`energy_distance` 6.96%、`mmd_u` 9.00%。(6) **路线重定向**：E-N2/H-N1/X-N1 三条空间变异函数路线降级为备选（不占槽位）；E-N1/H-N2/X-N2 保留为新路线；三条迭代路线全部保留；每 board 腾出 1 个槽位给新增 GJC 族（基因间协方差保持/修复，A=保持、B=结构外推修复）。
- evidence: reports/T2_M1_GATES_REPORT_20260927.md；artifacts/gate/T2_M1_GATES_20260927-v1/{gates.json,probe_c_variogram_tradeoff.json}；scripts/gate/t2_m1_gates_20260927.py；scripts/gate/t2_m1_probe_c_variogram.py；third_party/veckit/T2/metrics_v2.py 模块 docstring；reports/SERVER_SCORE_REGISTRY.md 的 heart_interp 子分登记。
- self_corrections_disclosed: 闸门脚本 parents[1]→[2] 路径错；`mmd_u`→`mmd_unbiased` 函数名错；**闸门 A 判据逻辑错**（位级阈值 + 误用两侧同置乱臂），差点把已证实的假设标成不确定。
- lesson_recorded: researcher 三份简报独立收敛到"空间变异函数"，而官方 `variogram` 是基因间协方差——**名字撞了、被预测量完全不同**；researcher 无代码读权限故非其失误，但后续不得再以"官方 variogram ⇒ 空间"为推理前提。
- new_family_provenance: **GJC 族是本报告的推断，非 researcher 检索产物，无文献锚点**；按 M1 流程须补检索或由 coordinator 明确标注为"无先例的自研方向"，用户可整族撤销。
- boundary: 全部为 pseudo-target（E7.25/E8.75/E9.5 观测期）上的**同目标相对**比较，不预测服务器分数；heart 的 E8.75 为 bracket stage，部分循环论证；`variogram` 判据阈值须 ≥10%（噪声 4.18%），`mmd_u` 须 >9%，**均不得套用 5%**；veckit 快照与服务器是否同版本无法验证，6 子分权重只能从回填值反推；blocks_submission: false。

## D-20260927-T2LEADS-003

- authorization: 用户 2026-09-27 指示「修 status/roadmap，然后完成 T2 的未完成路线」，并对 L-002 复现门问题明确选择「立新 atom 重跑一次」。
- decision: (1) L-002 首次执行（atom v1）预声明的**绝对 1e-9** 复现容差**未通过**，且其 `reproduction_control_passed: false` **原样保留、产物不删不改**——根因是参照 TSV 只存 8 位小数（自对齐精度 ±5e-9），绝对 1e-9 在构造上不可达。(2) 立 **atom B**（`T2-L002B-FGW-EPS-SENSITIVITY-20260927-v1`），把容差改为**相对 1e-4 并在跑前声明**（PRE_RUN_DECLARED.py 与执行版 SHA 相同 `dd33f13e…`），对照**通过**（相对偏差 2.4e-08 ~ 7.5e-06）。(3) **atom B 不是第二次独立观测**：ε/冻结输入/离散规则/随机包络与 v1 逐位相同且求解确定，实测四臂 NFS 差值 0.000e+00；1e-4 系看过 v1 偏差后标定，**引用必须成对**。(4) **机制更正**：新诊断测得两 ε 臂离散化后**只有 46.05% / 45.80% 的位置选中同一行**（54% 不同），故"两 ε 落到相同行"被否证；正确机制是**冻结目标面在 ε 方向上接近退化**——两个解很不一样但 objective 分不出高下（hard 相对差 2.4e-03 / 4.6e-03），这是 `B4-T2-R1` 全量 heart 双 TIE（57.3 / 57.31）的成因。(5) L-002 关闭结论不变（已放弃、不再扫 ε），但**理由升级**：「把同一目标解得更好」这条轴在 T2 判为死路，复活该方向需要让目标有判别力或换参考构建，均属新路线。
- evidence: reports/T2_LEADS_CLOSURE_20260927.md（atom B 补正节）；artifacts/tool_integration/T2-L002B-FGW-EPS-SENSITIVITY-20260927-v1/{RESULT.md,metrics/sensitivity_results.json,provenance/}；atom v1 provenance/PROVENANCE.json 与 t2_l2_eps_sensitivity.EXECUTED.cpython-311.pyc（SHA `429814c6…`，即实际执行 1e-9 版本的字节级见证）。
- boundary: 零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、未消耗提交配额；全部为 pseudo-target（E7.25 / E8.75 观测期）上的 source-only 相对比较，不预测服务器分数；不构成对 T2 任一 board 的机制性主张；blocks_submission: false。
- process_note: 本 atom 跑在共享工作树中，同时段另一持租约会话（T3 五路线 → T1-NEXT R3/R4 → T2 M1 闸门）在同一目录写入，且在 v1 执行后改写过本 atom 的产出脚本。已通过 `.pyc` 留证实际执行版本、以 atom B 重建事前声明链解决；未触碰任何已评分 artifact、INDEX 行、registry 条目或其他 lane 结果。**教训：共享工作树下的 gate 容差不得由后到会话"顺手修正"，须以新 atom 事前声明。**

## D-20260927-T2M0APPX-001

- authorization: 用户 2026-09-27 指令范围为 T2；本条为 `reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md` §7 关闭依据的证据更新。
- decision: 按 M0 §0「不得回改而不追加新决策」的规则，**新增附录 A（§11）而不修改 §7 原文**。§7 两行的判定与后果**均不变**，仅更新关闭依据：① FGW ε 轴的真实理由是**冻结目标面在 ε 方向接近退化**（两 ε 落点差 54%、hard objective 仅差 2.4e-03/4.6e-03），而非「ε 不敏感」；后果扩展为**任何「把同一目标解得更好」的方向都不应被期待带来 board 增益**。② embryo 配对轴补一条前置约束：只换 M 参考数据可能不够，新参考需**同时改变被优化的目标**。已核对：本轮 9 条 lane 均不使用 FGW 目标、不做行-点配对，**与该约束一致，无需修改任何 lane**。
- evidence: reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md §11；artifacts/tool_integration/T2-L002B-FGW-EPS-SENSITIVITY-20260927-v1/RESULT.md；reports/T2_LEADS_CLOSURE_20260927.md（atom B 补正节）；LEADS.md L-002 与 L-006 各自的 2026-09-27 补正。
- boundary: 纯文档口径更新；未训练、未改已评分/候选产物、未改 selection、未上传；`blocks_submission: false`。

## D-20260927-T2PROBED-001

- authorization: 用户 2026-09-27「全都开始执行」。在执行前发现闸门 A/B 与引用核验已推翻 9 条候选中 4 条的被预测量，故未盲目建候选，改先跑**无争议且为所有修复路线共同前置**的探针 D。
- decision: 探针 D（只读）定位 B4-T2-R2 表达桥的基因间协方差损失来源，**结论三条**：(1) **归因修正**——罪魁是 **mean bridge 本身**，不是 mass/组成重采样；embryo 父→L1 已跳 2.440×，L2 相对 L1 仅 +2.24%，heart 上 L2 反而 −2.77%，两者均在闸门标定的 4.2% 噪声带内**不可分辨**。探针 C「组成重采样破坏协方差」的矛头指向错误，照原建议改 mass 臂会改错对象。(2) **探针 C 的行动建议被部分推翻**——「该子分可免费拿回且不影响其他子分」不成立：破坏最重的 embryo L2（2.495×）与 heart L2（1.209×）**恰是服务器 board best**（62.29/62.04），而破坏较轻的 heart L1（1.243×）反被淘汰（56.27）。服务器未因该子分变差而惩罚这两条路线，故「拿回协方差」是高风险假设而非已确认的高性价比入口。(3) **新增一个 proxy–server 反向族**——两个插值板上 `mmd_u` 均判 L1 更好而服务器均给 L2 更高分；连同 G1-T2-R3/R4 空间族与 G1-T2-R2 收缩，构成第三个本地门失效族。
- evidence: artifacts/gate/T2_PROBE_D_GENE_COV-20260927-v1/{RESULT.md,probe_d_gene_cov.json}；scripts/gate/t2_probe_d_gene_cov.py；上游 D-20260927-T2GATES-001（闸门 A/B、探针 C、噪声标定）。arm 路径逐条取自 submissions/INDEX.tsv 并在跑前核对。
- open_issue_for_coordinator: 探针 D 结论 (3) 对 M0 §3.2「分布侧会签」有直接影响——若会签单独使用 `mmd_u`，在 B4-T2-R2 族会给出与服务器相反的信号。**建议**追加新决策：该族上会签须与 `neighborhood_mmd` 同向才生效。**本次未回改 M0**（按其 §0 冻结规则须追加而非修改）。
- boundary: 只读探针；零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传；全部为 pseudo-target 上的同目标同 seed 相对比较，**不预测服务器分数**；未重新查询服务器、未产生新分数；`blocks_submission: false`。

## D-20260927-T3SCORE-001

- authorization: 用户转录 8 个 T3 分数（FIVE 五件＋修复三件：v0042/v0044/v0046/v0047/v0048/v0034/v0035/v0036），按既定回填链登记。
- decision: v0048 47.93（+0.98）PROMOTED 为新 T3 selection；Total 记 157.04；FIVE 五 lane＋REPAIR-R6 转 SHIPPED，REPAIR-R3 部分回填（v0037 待分）；v0046/v0034/v0044 记 scored backup。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t3-five-repair-score-return-20260927；INDEX 八行 scored；SUBMETRIC＋40 行；用户转录原文（ID/时间戳未提供）。
- boundary: 分数未从舍入子项重构；severity 全 50.0 无判别信号；本次无新拟合/候选；v0037/v0040/v0041 不在此轮；blocks_submission: false。

## D-20260927-T2VALIDATE-001

- authorization: 用户 2026-09-27「我们测试一次我们的本地判据是否是成立的和服务器端可浮现的」＋「4条只留两条分数最高的，其他的开始执行」。裁决结果：保留 `E-N2`(embryo 62.29) + `H-I1`(heart_interp 62.04) 作为判据验证实验。
- decision: 全历史 31 条已评分 T2 候选（embryo 8 / heart_interp 12 / extrap 11）的本地指标与服务器 board 分排名相关已实测。**结论：本地判据逐板方向不同，不是「不完美」。** `neighborhood_mmd`（M0 §3.1 主指标）在 heart_interp（Spearman −0.559）与 extrap（−0.627）**有预测力**，但在 **embryo 强反向（+0.833）**——按 M0 5% 规则判 DEGRADE 的 v0010（本地 +16.4%）**恰是服务器第一名 62.29**，而本地唯一判 IMPROVE 的 v0004 排第 6。另发现 **embryo 板存在「本地全零信号、服务器 +3.4 分」的输入对**：v0001 与 v0002 表达矩阵字节相同、obs 顺序与组成相同，仅 3D 坐标整体 ×1.305 膨胀，服务器 56.70→60.10，而 `neighborhood_mmd`/`d2_shape`/`mmd_u`/`variogram` 全部零变化（`d2_distance` 尺度不变）。**服务器几何子分对绝对尺度敏感，本地几何镜像看不见。** 另：`d2_shape` 在两个插值板均反向（embryo +0.357、heart_interp +0.629），heart_interp 板最佳的 v0013 其 `d2_shape` 是 12 条中最差的。
- evidence: artifacts/gate/T2_VALIDATE_V1_LOCAL_VS_SERVER-20260927-v1/{RESULT.md,validation_v1.json}；scripts/gate/t2_validate_v1_local_vs_server.py；与 D-20260927-T2PROBED-001（探针 D）的关系已澄清：`mmd_u` 跨族有预测力但**族内成对比较反向**，二者不矛盾。
- self_correction: 本脚本原设计的「方向一致率」统计量**无效**（一个板上只有一条能等于板最佳，必然低报；实测 25%/8.3%/27%）——**已作废，不作结论**。报告只采用 Spearman、M0 混淆矩阵、逐条对照三类证据。
- open_issue_for_coordinator: 本次证据要求 M0 追加决策（**未回改 M0**）：§3.1 主指标须逐板校准（embryo 5% 规则停用或反转）；§3.2 会签在 embryo 零信号、族内反向；§4 结构性失败签名须重审是否把形状恶化当失败（`d2_shape` 两板均反向）。
- boundary: 只读；零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、**未查询服务器**；全部本地指标在 pseudo-target（观测期 stage）上重算，**不预测未来服务器分**；样本量小（8/12/11），Spearman 置信区间宽；不构成对 T2 任一 board 的机制性主张；`blocks_submission: false`。

## D-20260927-T1FIVE-001 — T1三新两优化完成交付

五路线全量执行并生成v0024–v0028，contract、九项定向测试、完整保存模型独立逐值重放及包SHA/CRC通过。三新为类型内整行密度重加权、参数化分布映射、新类型变化迁移；两优化为R1显式零质量外推、R2非负倍率残差。旧R1 p_pred 未进入实际输出，基线已逐值复现，旧artifact/评分不改。n3borrow在同一report split五主项均胜，但类型留出相对平均倍率优势弱；o1/o2不形成整体预测改善。五lane=PENDING_SERVER，未上传/未获服务器评分，v0023继续selection；完整E10.5真值评分NOT_RUN_NO_TRUTH，blocks_submission: false。报告 reports/t1_five_20260927/REPORT.md；包 deliveries/t1five__t1__upload__20260927.zip。

## D-20260927-T2M0APPXB-001

- authorization: 用户 2026-09-27 批准（「yes and move on」），授权按 V1 证据追加 M0 决策并继续推进。
- decision: 在 M0 追加**附录 B（§12）**，**不回改 §3/§4 原文**。(1) **逐板主指标裁决**：heart_interp（Spearman −0.559）与 extrap（−0.627）**维持** `neighborhood_mmd` + 5% 阈值；**embryo 停用 5% 三分类**，本地 `neighborhood_mmd` 降为**只记录不否决**，该板改**服务器仲裁优先**。**不反转**该规则——V1 只证明其反向，未证明反向的它有预测力（n=8，CI 宽），停用是证据能支持的唯一动作。(2) **分布侧会签覆盖 §3.2**：`mmd_u` 在 extrap/heart_interp 跨族可用但**族内成对反向**，**embryo 上零信号不得单独否决**；其 9.0% 种子噪声本就不支持 5%。(3) **`d2_shape` 不得单独作结构性失败签名**（两插值板均反向，heart_interp 板最佳 v0013 的 d2 是 12 条中最差），§4 其余签名不受影响。
- evidence: reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md §12；artifacts/gate/T2_VALIDATE_V1_LOCAL_VS_SERVER-20260927-v1/{RESULT.md,validation_v1.json}（D-20260927-T2VALIDATE-001）；探针 D（D-20260927-T2PROBED-001）族内成对反向证据。
- consequence_for_lanes: **落在 `T2:embryo:val_interp` 的任何 lane 不得以本地 5% 规则作否决依据**；本地门结果只作记录，最终由服务器仲裁。此条直接约束 `E-N1 SBL`（设计已冻结于 reports/T2_E_N1_SBL_DESIGN_FREEZE_20260927.md）与保留作验证实验的 `E-N2`。
- boundary: 追加式裁决，未回改 M0 任何原有条款；零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、未查询服务器；全部本地指标在 pseudo-target 上重算，不预测未来服务器分；样本量小（8/12/11）；`blocks_submission: false`。

## D-20260927-T2M1VERDICT-001

- authorization: 用户 2026-09-27「4条只留两条分数最高的，我们测试一次我们的本地判据是否是成立的和服务器端可浮现的，其他的开始执行」＋授权推荐项「yes and move on」。
- decision: 9 条候选按闸门/引用核验/验证结果逐条裁决（明细见 `reports/T2_NINE_ROUTES_20260927_M1_CANDIDATES.md` §7.1，**追加不回改 §1/§2**）：**执行** `E-N1 SBL`（前提未被证伪，Perler 锚点已倒故标「自拟构造、无直接先例」）、`E-I1 TCI`、`H-N2 A2C`；**条件执行** `X-N2 occupancy`（须先把「占据度」重定义为可从表达直接观测的量，MacKenzie 的 mark-recapture 前提不满足）；**待澄清** `X-I1`（须确认其回测的「变差函数距离」是自有回测量而非误用官方 `variogram`）；**保留为验证实验但本轮不执行** `E-N2`、`H-I1`；**否决** `H-N1`、`X-N1`。
- 保留不执行的**理由**（诚实记录，非省事）：该两条的原始目的——「测本地判据是否与服务器端可浮现一致」——**已由 `D-20260927-T2VALIDATE-001` 在全历史 31 条已评分候选上完成**。两条的被预测量均已被闸门 A 证伪，继续执行不产生新信息，按「不为已知失败方向烧预算」的既有纪律不执行。若用户仍要求执行，作为登记在案的额外 lane 处理，**不得记为晋级路**。
- evidence: reports/T2_NINE_ROUTES_20260927_M1_CANDIDATES.md §7；artifacts/gate/T2_VALIDATE_V1_LOCAL_VS_SERVER-20260927-v1/RESULT.md；reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md §12；reports/T2_M1_CITATION_VERIFICATION_20260927.md。
- boundary: 纯裁决与文档追加；未训练、未建候选、未改任何已评分或候选文件、未上传、未查询服务器；`blocks_submission: false`。

## D-20260927-T2EN1-002

- authorization: 用户 2026-09-27 批准「yes and move on」，授权按推荐推进并执行 `E-N1 SBL`。
- decision: **`E-N1 SBL` 执行失败，路线立即关闭**（预声明否定判据触发）。两臂 `neighborhood_mmd` 为 0.395969（L1 gated，127/498 基因）与 0.324687（L2 ungated），对 do-nothing 基线 0.031240 **差 10.4–12.7 倍**；`mmd_u` 差 30 倍以上；预测表达均值比基线高 53–54%。按冻结设计 §5「L1 与 L2 均不优于 do-nothing 即立即关闭，不扩参数、不改 K、不调 ridge」——**不补救**。
- 失败机制（核心诊断）：**两条通道之间没有任何幅度控制**。回归在按基因 z-score 化表达上做，β̂ 捕捉的是该基因**标准差**量级的跨细胞变化，与**均值**无关；场项因而带有标准差量级的动态范围，加到每基因均值上把总质量抬高 53%+，分布整体被推高，`neighborhood_mmd` 与 `mmd_u` 同时崩塌。**不是过平滑、不是图案复制，是纯粹的幅度失配。** 逐基因稳定性门几乎不起作用（仅 127/498 通过，中位 cos 0.168），且开门更少反而更差。
- self_corrections: ① 冻结设计的「softplus」实现为 `log1p(expm1(x))`，该式**恒等于 x**（代数恒等），我**第一次的失败诊断（归因于非负场项抬高質量）是错的**，已订正并归档于 `attempt1_buggy/`。② 冻结设计写「取 τ=0.5」，但目标 stage E7.5 在 τ(E6.75)=0/τ(E7.25)=1/3/τ(E8.0)=1 轴上位于 **τ=0.6**（0.5 对应 E7.625）——**设计文本的算术不一致**，按合同固定的 target stage 与 spec 固定的轴订正为 0.6。**两项订正均非结果导向调参**；τ 订正使结果更差（0.348/0.275→0.396/0.325），不改变裁决。
- evidence: artifacts/tool_integration/T2-E-N1-SBL-20260927-v1/{RESULT.md,sbl_run.json,attempt1_buggy/}；scripts/t2_e_n1_sbl.py；设计冻结 reports/T2_E_N1_SBL_DESIGN_FREEZE_20260927.md；D-20260927-T2EN1-001。
- revival_condition: 复活须作为**新 lane** 重新预声明一个**跑前的幅度控制**（例如场项按单位方差标准化后再按预声明比例缩放）。**不得在本路线内继续调门、调 K 或调 ridge**——那是在看到结果之后放宽。
- boundary: 零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、未查询服务器；本地读数在 pseudo-target E7.25（观测期 stage）上计算，**不预测服务器分**；`d2_shape`/`occupancy_dice` 因不改几何而只是回显父版本，不构成独立信息；本报告不构成对 embryo 板任何机制的主张；`blocks_submission: false`。

## D-20260927-T2EXTRAPAGG-001

- authorization: 用户 2026-09-27「三项都开始工作」；本条为第一项（heart_extrap 50.64/50.53）的定案。
- decision: **`T2:heart:val_extrap` 的 0.11 聚合差异定为 `RESOLVED_BY_LOCAL_EVIDENCE`**，此前标 OPEN。结论：**服务器 Total 不是「每板历史最高分之和」，而是按一个已登记的 per-board 选集聚合；extrap 在该选集内的条目是 baseline v0001（50.53），v0011 虽已提交并评分（`score_status: scored`）但不是选集条目。** 0.11 不是被吃掉，也不是提交失败。
- decisive_evidence: 服务器**第二个** Total **157.04**（2026-09-27，T1/T2 分量未变）**仍为 T2=58.29 ⇒ extrap=50.53**，且发生在 v0011 被评分（09-16）**十一天之后**。据此排除三种解释：**非舍入**（58.29 与 58.32 差 0.03 ≫ 0.01 舍入量级）；**非「最新提交」**（extrap 最后提交的是 v0016=50.25，若按最新聚合 T2 应为 58.19、Total 156.96，与 156.06/157.04 均不符）；**非「自动取每板最高」**（v0011 的 50.64 已评分，若自动取最高 T2 应为 58.32）。
- corrections: ① `registry` §G1-T2 / `D-20260916-G0T2-001` 的「selection updates to v0011」**与服务器行为不符**，按只追加原则不追溯改写，以本条订正。② **`INDEX.tsv` 无需修改**：`v0011` 的 `status=candidate` + `score_status=scored` 是自洽的（有真实分数但不在选集内），与 v0012–v0016 处理一致；此前把「INDEX 说未晋级 vs registry 说已晋级」当作矛盾是**误读**——矛盾在 registry 正文，不在 INDEX。
- open_for_user: (a) 若要让 +0.11 进入 Total，需把 extrap 的登记条目从 baseline 换成 v0011——**用户侧决定**（改选集需门户操作），本 agent 不代做。(b) +0.11 落在 ±0.1 TIE 带**边界**上；`D-20260916-G0T2-001` 记为「晋级」与 B4-T2-R1（+0.01 判 TIE 不晋级）口径一致，但与 TIE 规则字面冲突，**需用户裁决**。(c) **【2026-09-27 自查更正】初稿称「v0011 子项未回填、违反 `submissions/README.md` 第 6 条」不成立，已撤回**：`SERVER_SUBMETRIC_REGISTRY.tsV` 中该板 v0011 **有完整 8 行**（官方 anchors 亦为 8），与同批 v0012–v0016 一致，**无需补齐**。全量自查：已评分候选 **60 条齐全 / 32 条完全缺失**，32 条**全部**为 2026-09-04 规则固化**之前**的候选，固化后无一缺失——属历史登记缺口而非本次违规；是否回补由用户定，不影响当前 selection。
- evidence: reports/T2_HEART_EXTRAP_AGGREGATE_20260927.md；`reports/SERVER_SCORE_REGISTRY.md` §153.7 快照、§T1 NEXT R1 score return（156.06）、§T3 157.04 回填、§G1-T2；`submissions/INDEX.tsv` extrap 全部 15 行；`docs/coordination/STATUS.md` leaderboard basis。
- boundary: **完全基于既有本地登记，未查询服务器、未打开门户、未产生任何新分数**；不改 INDEX、不改已评分 artifact；`blocks_submission: false`。

## D-20260927-T2DESIGN-001

- authorization: 用户 2026-09-27「三项都开始工作」；本条为第三项（`E-I1 TCI` 与 `H-N2 A2C` 设计冻结），依据 M0 §5「设计先于训练」。
- decision: 两份设计冻结文档已在任何 run 之前落盘：`reports/T2_E_I1_TCI_DESIGN_FREEZE_20260927.md`（embryo，迭代 v0010）与 `reports/T2_H_N2_A2C_DESIGN_FREEZE_20260927.md`（heart_interp，迭代 v0013）。两者各自写死了机制、双臂（含隔离对照臂）、pseudo-target/seed、判定规则、预声明失败签名、否定判据、成本与训练前检查清单。
- contract_check_caught_a_leak: **`H-N2` 的训练前 bracket 核对抓出一处会导致 target 泄漏的设计错误。** 检索简报写「在 E8.5 与 E8.75 之间取中点」，但 `BOARD_REGISTRY.yaml`（`target_label: E8.5`）、`t2_s3_shape_field.py`（`target_stage=8.5 / left=8.25 / right=8.75`）、`t2_j1_pairing.py`（`target_stage=8.5 / source_stages=(8.25, 8.75)`）**三处一致**：bracket 是 **[E8.25, E8.75]**。原设计会拿**目标 stage 自己**当源阶段。已修正为 E8.25_late / E8.75，`λ = (8.5−8.25)/(8.75−8.25) = 0.5` 仍为等权平均，并新增**泄漏断言**（任何源阶段不得等于 target_stage）为训练前检查第 4 项。**这正是 M0 §5「设计先于训练」要拦下的东西。**
- board_wise_judgement: `E-I1` 落在 embryo——按 `D-20260927-T2M0APPXB-001` 该板 5% 规则**已停用**，故本地读数**只作记录、不作否决**，由服务器仲裁；并明确其**已知上限**：embryo 存在本地完全看不见的 3.4 分坐标尺度杠杆（`D-20260927-T2VALIDATE-001`），本路线不改坐标故原则上无法捕获该杠杆。`H-N2` 落在 heart_interp——该板 5% 规则**维持**，故采用三档判定，且 `d2_shape` **不得单独否决**（该板与服务器反向 +0.629）。
- design_lesson: 两条路线各自封堵了 `E-N1 SBL` 的已知失败根因（`D-20260927-T2EN1-002`：全局水平与场项间无幅度控制）——`E-I1` 靠「层内标准差归一 + 水平/对比度解耦」，`H-N2` 靠「`f_g` 在层内按标准差归一」。但这**不构成对成功���预期**，只表示移除了一个已知的失败原因。
- open_for_user: **`PLAN.md` 科学问题节写「heart 插值（E9.0）」，与上述三处权威来源的 E8.5 冲突。** 属事实性不一致，按规则未自行修改 PLAN，建议用户授权修订。
- evidence: reports/T2_E_I1_TCI_DESIGN_FREEZE_20260927.md；reports/T2_H_N2_A2C_DESIGN_FREEZE_20260927.md；artifacts/tool_integration/P0-LOCK/locks/BOARD_REGISTRY.yaml；scripts/t2_s3_shape_field.py；scripts/t2_j1_pairing.py。
- boundary: **两份设计冻结均未跑训练、未建候选、未改任何已评分或候选文件、未上传**；锚点（Myronenko & Song、Aviñó-Esteban）尚未 `web_read` 核验，设计内已列为训练前必做项并规定核验不通过时按「未核验引用」标注后仍可执行；`blocks_submission: false`。

## D-20260928-T1FIVESCORE-001

- authorization: 用户转录 T1 五路线分数（v0024–v0028 总分及四子项），按既定回填链登记，并要求把结果写进既有综述，不另开新文件。
- decision: v0024 51.92（+1.10 vs v0023）PROMOTED 为新 T1 selection；Total 记 158.14。v0027/v0025 记 scored backup；v0026/v0028 REJECT 相对父版本。综述 `reviews/2026-09-27_submitted-route-synthesis/REPORT.md` 原文件更新。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t1-five-score-return-20260928；INDEX 五行 scored；SUBMETRIC＋20 行；用户转录原文（ID/时间戳未提供）。
- boundary: 分数未从舍入子项重构；单次回填不证明密度比的生物学机制；本次无新拟合/候选；blocks_submission: false。

## D-20260927-T2CITE-002

- authorization: 用户 2026-09-27「完成这些工作，另外检查一下 plan 或其他顶层文件……然后修复」。本条为两项锚点的原文级核验。
- method: 不依赖检索命中。使用 **arXiv 摘要页原文**（Myronenko & Song）与 **Europe PMC REST API `resultType=core` 官方元数据**（Aviñó-Esteban 等，含题名/DOI/期刊卷期/摘要全文）。PubMed 直连因 cookie 限制失败，已换 Europe PMC。
- decision_EI1: **Myronenko & Song, *Point-Set Registration: Coherent Point Drift*（arXiv:0905.2635 / IEEE TPAMI）核心锚点成立**——原文确为概率软对应（GMM 拟合、最大化似然、E 步给隶属概率、EM 且 M 步闭式解），且明确支持非刚性（正则化位移场 + 变分法）。**但子主张「正反一致性自诊断」不成立**：摘要只把 noise/outliers 列为挑战，未提出该诊断。该子主张已从文献属性移除，改为本项目自定工程选择；`E-I1` 设计冻结 §0 已相应标注。**不阻塞执行。**
- decision_HN2: **Aviñó-Esteban, Cardona-Blaya & Sharpe, *Spatio-temporal reconstruction of gene expression patterns in developing mice*, *Development* 152(4):dev204313（PMID 39982400, DOI 10.1242/dev.204313）——核心思想成立、锚点降级。** 摘要确证其方法为「整合跨发育阶段的静态表达图案、生成连续 2D 时空重建」，故「跨阶段插值空间表达图案」确有先例。**但该文是 limb（肢芽）/ 2D / 全胚 ISH 静态图案（含 *Sox9*、*Hand2*），而 `H-N2` 做的是 heart / 3D / 单细胞空间组（MERFISH）/ 细胞级 ——组织、维度、模态三项均不匹配。** 故降级为「概念相邻的先例」，**不得**在 RESULT 中声称其支撑本路线的 3D 心脏构造。**不阻塞执行**，但本路线价值来自自拟设计而非该文献。
- cumulative: M1 九条路线的承重引用现已核验 5 条——**3 条撑不住**（Perler 2021、MacKenzie 2003、Aviñó-Esteban 2025 的承重性）、**1 条部分不成立**（CPD 的「正反一致性」子主张）、**1 条核心成立**（CPD 本体）。`X-N2` 的 MacKenzie 前置条件待其「占据度重定义」落实后重核。
- evidence: reports/T2_M1_CITATION_VERIFICATION_20260927_BATCH2.md；arXiv:0905.2635 摘要页；Europe PMC `resultType=core` 记录（PMID 39982400 / 10.1242/dev.204313）；已回填 reports/T2_E_I1_TCI_DESIGN_FREEZE_20260927.md 与 reports/T2_H_N2_A2C_DESIGN_FREEZE_20260927.md 的 §0 与训练前检查项。
- boundary: 仅读取公开文献与官方元数据；**未训练、未建候选、未改已评分文件、未上传**；核验只判断「引用能否支撑机制描述」，不评估两条路线的科学价值；`blocks_submission: false`。

## D-20260928-T3R2-001 — T3高分组合及三新两优化交付

用户指定009 KIR kill-test prompt已读并保存SHA；沿用精确基线、组件分离、强对照和不救失败门原则，不执行009 caller任务。H=v0048与G=v0046均从模型逐值复现；组合G(H)实建v0049，另外四路线生成v0050–v0053，全部7449×500且contract/独立重放/13测试通过。正交、logistic与基因收缩局部未显示稳定优势；来源出现率组件增益不稳定。五lane PENDING_SERVER，科学INCONCLUSIVE_NEEDS_INDEPENDENT_TRUTH，不推断目标信息上限，不晋级。best保持v0048=47.93；旧v0037/v0040/v0041待回分。报告 reports/t3_round2_20260928/REPORT.md；交付 deliveries/t3r2__t3__upload__20260928.zip；blocks_submission: false。

## D-20260927-T2ROUTES-EXEC-001

- authorization: 用户 2026-09-27「现在继续推进，直到完整产出可推进路线的最终产物并给我上传包」。
- decision: `E-I1 TCI` 与 `H-N2 A2C` 均已完整执行，**两条均失败，裁决 `RECOMMEND_NO_SUBMISSION`，本轮不产生上传包**。两条的几何、行序、obs 名、组成重采样**逐字节复现**现役版本（坐标 SHA 与 v0013 / v0010 逐位相同，byte-identity 断言通过），恶化全部来自表达项：`H-N2` 相对现役 v0013 劣化 **+77.8% ~ +96.9%**，`E-I1` 相对现役 v0010 劣化 **+2378.5% ~ +2567.9%**，且 `neighborhood_mmd` / `mmd_u` / `energy_distance` / `variogram` **四项同向变差**。
- 关键证据: ① **桥移植精确**——`H-N2` 的 `bridge_only` 读出 0.040877，与验证 V1 独立记录的 v0013 差 **1.5e-07**，故失败来自机制而非移植 bug。② 几何项在两臂完全相同（几何未改），证明 byte-identity 有效并把恶化定位到表达项。③ `E-I1` 板虽已停用 5% 规则（本地只记录），但 +2568% 远超 `neighborhood_mmd` 的 0.00% 种子噪声，"只记录"不构成可提交理由。
- 三次尝试的合并发现（本轮最重要的产出）: `E-N1 SBL`(+1085~1164%)、`H-N2 A2C`(+78~97%)、`E-I1 TCI`(+2379~2568%) 收敛到**同一失败模式**——给已被服务器正向验证的低空间方差均值场叠加任何"学出来的空间对比度"都会摧毁分布，劣化幅度与对比度相对全局水平的幅度同向。**`E-N1 SBL` 的事前修正（逐基因 sd → 层内 sd）并未解决问题**：把对比度定标到 sd=1 本身就把幅度固定在远大于每基因均值（log 空间约 0.25）的水平。**归一化的原则对，sd=1 这个定标是病灶。** 与正例一致：`B4-T2-R2` 的 +4.79 与 `G1-T1` 收缩族都作用在**边际分布**上，不是空间结构。
- consequence_for_M0_nine_routes: M1 九条里**最后两条前提未证伪的路线也做完了，结论为负**。加上闸门 A 证伪的 4 条，**T2 九路线的共同前提「换一个被预测的空间量能提分」已被三重独立证据否定**。已登记 LEADS **L-008**（对比度幅度必须由数据决定）作为**前置问题**；在解决它之前不应再开任何"均值场 + 加性空间项"的 lane。**未执行**，作为线索登记。
- evidence: reports/T2_ROUTES_EXEC_CLOSURE_20260927.md；artifacts/tool_integration/T2-H-N2-A2C-20260927-v1/{a2c_run.json,candidates/}；artifacts/tool_integration/T2-E-I1-TCI-20260927-v1/{tci_run.json,candidates/}；scripts/t2_h_n2_a2c.py；scripts/t2_e_i1_tci.py；上游 D-20260927-T2EN1-002。
- self_corrections: 实现缺陷 4 处已如实记录并修复（样条节点数、CPD 权重轴/平移项/置信度转置、变量解包）。**其中泄漏断言本身写错**：曾把「E7.25 是本地 pseudo-target」误判为泄漏，而 board 目标是 **E7.5**；已改为正确断言并加循环性披露（E7.25 同时是桥源与评价目标，J1 起即如此、部分循环、已声明）。三条路线的 `GAIN`/`ALPHA`/`N_LAYERS`/CPD 迭代数/`SEED` **全部在首次执行前冻结，无任何参数按结果调整**。
- no_submission_rationale: 四个分布侧指标同时劣化、无任何可取长补短口径；heart_interp 是本地指标确有预测力的板（Spearman −0.559）而劣化 +78%；embryo 劣化 +2568% 远超噪声带。提交将消耗配额换取**可预见的回归**。两个候选作为**不可变诊断物**保留在 `artifacts/`，**不进 `submissions/`、不进 INDEX、不打包**。若用户愿承担风险试探服务器需明示授权。
- boundary: 零上传、零服务器查询、`submissions/INDEX.tsv` 未改、已评分 artifact 0 改动；本地读数在 pseudo-target（E7.25 / E8.75 观测期 stage）上计算，heart E8.75 与 embryo E7.25 均**部分循环**——相对比较有效、绝对水平不可解释；本决策不对 T2 任一 board 作机制性主张；`blocks_submission: false`。

## D-20260927-T2L008-001

- authorization: 用户 2026-09-27「好的继续」，采纳推荐顺序（L-008 前置探针 → 边际分布方向）。
- decision: **L-008 前置探针已执行，结论为「均值场 + 加性空间对比度」机制族在 T2 两个插值板关闭。** 幅度是本探针**唯一被扫的变量**（`a ∈ {0, 0.02, 0.05, 0.10, 0.25, 0.50, 1.00}`，对比项按 sd=1 标准化，故 `a` 的单位是「每基因全局均值的倍数」），其余全部冻结（pseudo-target、seed、行序、组成重采样、几何）。基座为各板现役 L2 桥（`bridge_only`），本轮再次核对 `obs_names` 与 `coords` 与现役 artifact **逐位一致**（两板 PASS）。对比项**刻意用几何派生**（目标几何的解剖轴向坐标）而非学习场，以隔离「幅度」与「内容是否正确」。
- key_result: 损伤随幅度**单调递增**，两板**可接受带均只到 `a ≤ 0.05`**，首个出带幅度均为 `a = 0.10`；`mmd_u` 与 `neighborhood_mmd` 逐步同向（非单指标伪影）。**关键交叉校验：真值侧经验半方差中位的平方根为 1.20060（embryo）/ 1.54624（heart_interp），比可接受幅度上限大 24.0× / 30.9×。** 即**即使空间对比度方向完全正确，按真值应有的幅度加上去也必然毁掉分布**——这不是定标方式问题，而是机制与官方邻域度量不兼容。
- cross_validation: 本曲线在 `a = 1.0` 处给出 heart_interp 劣化 **+79.9%**，与 `H-N2 A2C`（`ALPHA = 1.0`）实测 **+77.8% ~ +96.9%** 几乎重合。**两次独立测量数值重合，把「A2C 失败是幅度驱动而非内容驱动」从推断升级为定量确认**——A2C 学到的解剖对比度，其分布损伤与一个纯几何、完全不含表达信息的对比项同量级。三次失败的排序（`E-N1 SBL` +1085~1164% > `E-I1 TCI` +2379~2568% > `H-N2 A2C` +78~97%）与各自注入的有效幅度排序一致。
- lead_disposition: LEADS **L-008 状态改为「已放弃」**，原诉求（幅度须由数据决定）被更强结论取代（幅度取真值量级亦不可用）。**保留一条可复用方法学**：任何「向已校准的低方差均值场加空间项」的路线，动手前先跑这条幅度阶梯（约 1.5 CPU·min/板，比完整建模便宜两个数量级）。
- consequence_for_T2_search: 三次路线失败 + 本探针把 T2 搜索空间收窄到**唯一一条**：**作用在边际分布上的机制**（细胞类型取值分布 / 组成），而非空间结构。这与唯一的服务器正向验证证据一致——`B4-T2-R2` 的 heart_interp **+4.79** 来自组成重采样、`G1-T2-R2` 的 heart_extrap **+0.11** 来自收缩；**两条被服务器确认有效的 T2 路线没有一条是靠空间结构赢的**。
- evidence: reports/T2_L008_AMPLITUDE_DAMAGE_20260927.md；artifacts/gate/T2_L008_AMPLITUDE_DAMAGE-20260927-v1/l008_amplitude_damage.json；scripts/gate/t2_l008_amplitude_damage.py；上游 D-20260927-T2ROUTES-EXEC-001。
- limitations: 全部读数在 pseudo-target（E7.25 / E8.75 观测期 stage）上计算，**部分循环**，绝对水平不可解释，只有「同一基座下不同幅度的相对变化」有效；对比项为几何派生，故本曲线不是「任何可能空间场」的上界（但第 4 节的交叉验证表明主项是幅度）；阶梯为 7 点粗网格，0.05–0.10 边界未细查（**不影响结论**，因结论依赖「真值幅度超上限 24–31×」的量级关系而非边界位置）；**本探针不授权任何新 lane**。
- boundary: 只读探针；零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、未查询服务器；不构成对 T2 任一 board 的机制性主张；`blocks_submission: false`。

### D-20260928-T1R2-001 — T1 第二轮三新两优化完成

用户授权三条新路线、两条优化，要求高分合并计入新路线预算。实际完成n1stack(v0029：v0024+v0027组合)、n2composition(v0030)、n3states(v0031)、o1caldensity(v0032)、o2shrinkmass(v0033)。完整官方32285列scorer五次、16定向测试、五模型独立重放及拟合参数审查、contract和ZIP SHA/CRC全部PASS。v0030本地DE持平、其他四主项改善；v0029有取舍；另外三条未胜各自原模型。未提交/未评分；best v0024=51.92不变。优先v0030，次选v0029；不把cell holdout当未来/独立胚胎验证。证据 reports/t1_round2_20260928/REPORT.md；deliveries/t1r2__t1__upload__20260928.zip；blocks_submission:false。

## D-20260927-T2MARGINAL-001

- authorization: 用户 2026-09-27「继续」，采纳 T2 唯一剩余方向（边际分布）的响应面读数。
- decision: **边际分布响应面探针完成（只读）。两条独立的一维阶梯——`COMP_INTENSITY`（每型计数从现役插值回父版本原始计数）与 `SHRINK_INTENSITY`（向每型均值收缩）——均显示现役处于局部最优。** 从现役单调向外移动时，服务器已确认有效过的子分全部单调变差：heart_interp `de_score` 0.54350→0.36960（−32%）、`de_direction` 0.76970→0.63910（−17%）、`neighborhood_mmd` 0.04088→0.06319（+55%）、`mmd_u` 0.02240→0.03476（+55%）；embryo 的 SHRINK 臂同样单调恶化（`neighborhood_mmd` +91%、`mmd_u` +522%）。**唯一随旋钮单调变好的子分是 `occupancy_dice`(+8%) 与 `d2_shape`(−28%)，而这两个恰是验证 V1 已证实与服务器反向的子分。**
- key_mechanistic_fact: **收缩对 DE 类指标完全不敏感**——`s` 从 0 到 1，heart 的 `de_score` 恒为 0.54350、`de_direction` 恒为 0.76970。因收缩只改型内相对幅度、每型均值不变，而 DE 只读「相对 reference 的变化量」。**推论：想在不动 DE 的前提下改分布，必须改每型均值（组成/位移），不能只改型内幅度。**
- 附带发现: `de_score` 在 embryo 的 pseudo-target 上恒为 `UNDEF`（官方 `metrics_v2` 在非有限时返回 `None`）——**该板 `de_score` 在本地不可用作筛选判据**。几何子分在 SHRINK 臂完全冻结（行序未动，与预声明一致），在 COMP 臂会变（组成重采样必然改变点云所含的行，**属固有混淆而非 byte-identity 失败**；`c=0` 已断言逐位复现现役）。
- verdict: **`B4-T2-R2` 的 +4.79 是从 L1 mean bridge 回到现役这一点，不是从现役再往前走——该方向已走完一次。** T2 的空间结构方向已由 `D-20260927-T2L008-001` 关闭，边际方向按 composition-intensity 与 shrinkage 两种实例化也已耗尽。**两条杠杆都到头。** 若要继续，须引入**第三类机制**：同时改变每型均值与组成、且作用方向与 `occupancy_dice` 相反。**本探针不授权任何新 lane**，已把该入口登记为 LEADS **L-009**。
- evidence: reports/T2_MARGINAL_RESPONSE_20260927.md；artifacts/gate/T2_MARGINAL_RESPONSE-20260927-v1/marginal_response.json；scripts/gate/t2_marginal_response.py；上游 D-20260927-T2L008-001、D-20260927-T2VALIDATE-001。
- self_corrections: **首版探针的 COMP 构造有缺陷**（用父行索引现役表达矩阵，导致 `c=0` 都无法复现现役）——已改为在现役自身各型行内重采样，并加入 `c=0` 必须逐位复现现役的硬断言。另修正：坐标比对的 float32/float64 精度假阳性、`de_score` 的 `None` 未容错、官方索引键的冒号/下划线不匹配、probe 反复重训导致耗时。**均不改变结论**——修正后 `c=0` 与基座完全一致，响应面形状与首版同向。
- limitation: 读数在 pseudo-target 上计算，**部分循环**，绝对水平不可解释，只有同一子分随旋钮的相对变化有效；COMP 臂混淆组成与点云，SHRINK 臂是干净单因子阶梯；阶梯为 5 点粗网格（结论依赖响应面形状而非边界位置）。
- boundary: 只读探针；零候选、零 h5ad、零 submission、`submissions/INDEX.tsv` 未改、零上传、未查询服务器；不构成对 T2 任一 board 的机制性主张；`blocks_submission: false`。

## D-20260928-T3REPAIR2-001 — T3修复剩余三 lane 回分（v0037/v0040/v0041，均不晋级）

- authorization: 用户转录三条 T3 修复候选分数（v0037 46.98、v0040 47.08、v0041 47.09 及各五子项），按既定回填链登记。
- decision: 三条均记 scored，不晋级；selection 保持 v0048（47.93）。v0037（+0.03 vs 父 v0009）为 TIE，五子项与同胞 v0036 在回报精度下完全相同；v0040（+0.13）/v0041（+0.14）超父版本但距现 best -0.85/-0.84，记 scored backup。修复队列在分数上关闭：v0034/v0035/v0036/v0037/v0040/v0041 全已评分，v0038/v0039 保持 invalidated_unsubmitted（已撤回）。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t3-repair-r3r4-score-return-20260928；INDEX 三行 scored（SHA 实核通过）；SUBMETRIC＋15 行；用户转录原文（ID/时间戳未提供）。
- boundary: 总分未从舍入子项重构；未提供新 Total，按既有 158.14 推导值不变；单次回分不证明 R3/R4 机制有效；本次无新拟合/候选；blocks_submission: false.

## D-20260928-T1R2SCORE-001 — T1第二轮五 lane 回分（v0029 晋级新 best）

- authorization: 用户转录 T1 第二轮五条候选分数（v0029 52.5、v0030 52.49、v0031 50.51、v0032 51.97、v0033 51.10 及各四子项），按既定回填链登记。
- decision: v0029 52.5（+0.58 vs v0024）PROMOTED 为新 T1 selection；Total 记 158.72。v0030 52.49 距新 best -0.01，按不并列晋级规则记 scored backup；v0032（-0.53 vs 新 best）、v0031、v0033 REJECT。ROUND2 队列分数关闭。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t1-round2-score-return-20260928；INDEX 五行 scored（SHA 实核通过）；SUBMETRIC＋20 行；用户转录原文（ID/时间戳未提供）。
- boundary: 总分未从舍入子项重构；按既有分量推导 158.72 待门户页面确认，不得引用为服务器值；双雄差 0.01 且子项画像镜像（v0030 方向强、v0029 分布强），不作机制推断；本地曾更看好 v0030，排序在头部反转，约束 T1 proxy 的适用范围；本次无新拟合/候选；blocks_submission: false.

## D-20260928-T2LOWAMP-001

- authorization: 用户 2026-09-28「我就需要你给我一组可靠的可提交结果」；并于同日指出「小幅劣化的结果可以尝试提交一下，毕竟可能存在反转」。
- decision: **产出可提交包 `deliveries/t2hn2lo__t2__upload__20260928.zip`（2 个候选，heart_interp）。** 采用**低幅度** `ALPHA = 0.05` 的 `H-N2` 变体，而不是本会话先前的 `ALPHA = 1.0` 版本——**因为用户的判断在证据上是成立的**：本地门与服务器确有反转先例（`G1-T2-R2` 收缩本地 NOT promoted 而服务器 +0.11 成为板最佳；验证 V1 实测 `neighborhood_mmd` 在 embryo 与服务器强反向 +0.833、`d2_shape` 在两插值板反向），因此「本地小幅劣化」**不排除**服务器持平甚至转好。但**幅度**决定了该判断是否可迁移：`ALPHA = 1.0` 的两个候选本地劣化 **+77.8% ~ +96.9%**，超出 5% 带 16 倍以上，不属「小幅」；而 L-008 幅度探针（在**任何路线结果之前**冻结的独立测量）给出 `a = 0.05` 时损伤仅 **+3.2% ~ +3.7%**。故 `ALPHA = 0.05` 是**由预声明的独立测量决定的幅度**，不是从本路线自身结果倒推的。
- result: 两个候选在锁定 pseudo-target 上相对现役 v0013：`L1(共享系数)` nmmd 0.041319（**+1.08%**）、mmd_u 0.02217（**优于现役 0.02228**）；`L2(分别拟合)` nmmd 0.041284（**+0.99%**）、mmd_u 0.02221（**优于现役**）。**两者均落在 ±5% 带内**，且分布侧指标不劣于现役。几何/行序/obs 名/组成重采样与 v0013 **byte-identity 通过**（坐标 SHA 逐位相同），contract 全部 PASS（panel 逐位一致、无负值、有限、5872×500）。
- honest_limitation: **这是探针候选，不是提分候选。** 其唯一目的是用一次提交配额检验「服务器是否对小幅本地劣化也反向」——即用户指出的反转可能。L-008 已证明 `a = 0.05` 的空间结构量只贡献真值应有量的 3–4%，故**其增益空间本就很小**；如实记录：预期为「持平或略降」，转好概率低但非零。不得宣称其有望超过 v0013。
- package: zip `t2hn2lo__t2__upload__20260928.zip`（12,551,186 bytes，SHA256 `d0b915ee…`）；成员 `t2_hrt_int__l1__v0014.h5ad` / `t2_hrt_int__l2__v0015.h5ad`（各 26 字符，符合 ≤50 规则）；包内附 `MANIFEST.tsv` / `UPLOAD_MANIFEST.tsv` / `RUN_ID_MAP.tsv` / `EVIDENCE_MANIFEST_POINTERS.tsv`（一批次一包，符合 2026-09-11 规则）。包内 SHA 已复核一致，且与 `submissions/candidates/` 中的文件逐位相同。
- registration: `submissions/INDEX.tsv` 新增 v0014 / v0015 两行（`status=candidate`、`score_status=score_pending`、`local_contract=pass`），SHA 已登记。
- evidence: artifacts/tool_integration/T2-H-N2-LOWAMP-20260927-v1/a2c_run.json；deliveries/t2hn2lo__t2__upload__20260928.zip；submissions/INDEX.tsv v0014/v0015；上游 D-20260927-T2L008-001（幅度来源）、D-20260927-T2ROUTES-EXEC-001、reports/T2_L008_AMPLITUDE_DAMAGE_20260927.md。
- boundary: **未上传、未查询服务器、无服务器分数。** 提交与否由用户决定；上传后须按 `submissions/README.md` 第 6 条回填 total + 8 个子项。`blocks_submission: false`。

## D-20260928-T2LOWAMP-002

- authorization: 用户 2026-09-28 转录两个 portal board 总分与各 8 个子项。
- decision: **两条低幅度候选均已评分 61.52，低于现役 v0013 的 62.04（−0.52，远在 ±0.1 TIE 带外）→ 均不晋级，selection 不变，Total 不因本轮改变。** `T2:heart:val_interp` 继续用 v0013。
- submetric_decomposition: `d2_shape` 65.4、`occupancy_dice` 47.8、`scale_log_ratio` 97.9 **三项与现役逐位相同**——这是 **byte-identity 的正面对照**，确证提交件与 v0013 只差表达矩阵。全部损失都在表达侧：`variogram` **28.4→25.4（−3.0，最大单项）**、`neighborhood_mmd` 65.8→**64.5 / 64.7（−1.3 / −1.1）**；`de_score` +0.6/0.0、`de_direction` +0.2、`mmd_u` +0.1 的微幅改善不足以抵消。
- findings: ① **反转假设在本地被实证否定**：本地 +0.99~1.08% 劣化 → 服务器 −0.52，方向一致、约 1:1。用户「小幅劣化可能反转」的判断**有先例依据**（`G1-T2-R2` 收缩本地 NOT promoted 而服务器 +0.11 成板最佳），本次探针以一次提交配额给出该板该族的**否定答案**：此族的小幅本地劣化**不会**在服务器反转。② **跨阶段系数共享约束经验上为 null**：L1（共享）与 L2（分别拟合）**总分完全并列 61.52，8 项中 6 项逐位相同**，仅 `de_score`(61.2 vs 60.6) 与 `neighborhood_mmd`(64.5 vs 64.7) 有差。H-N2 路线为隔离该约束而设的第二个臂，**其存在理由已被证伪**。③ **与 α 无关的符号一致性**：`α=1.0` 两条路线本地劣化 +78~97%（`H-N2 A2C`），`α=0.05` 本地 +1.0% 而服务器 −0.52——**两种幅度下符号一致为负**，说明失败不是幅度调参问题。
- consequence: `H-N2 A2C` 的核心假设（解剖位置函数替代/叠加均值项能提分）**由服务器证伪**，不再只是本地证伪。T2 的**空间结构方向至此在本地与服务器两侧都被否定**（空间路线三次失败 + L-008 幅度探针关闭机制族 + 本次服务器确认）。`E-I1 TCI`（embryo）仍为本地证伪，**其服务器侧未验证**；按 embryo 板 `neighborhood_mmd` 与服务器强反向（+0.833）的事实，**不建议**为 TCI 消耗配额。
- evidence: reports/SERVER_SCORE_REGISTRY.md `## T2 H-N2 LOWAMP score return — 2026-09-28`；reports/SERVER_SUBMETRIC_REGISTRY.tsv 新增 16 行；submissions/INDEX.tsv v0014/v0015 → `scored` 61.52；artifacts/tool_integration/T2-H-N2-LOWAMP-20260927-v1/；deliveries/t2hn2lo__t2__upload__20260928.zip（SHA `d0b915ee…`，未改动）。
- boundary: 用户转录，未查询服务器；未提供 submission ID 与时间戳。分数按供给精度登记，不从舍入子项重构。已评分 artifact 0 改动，交接包 SHA 未变。`blocks_submission: false`。

## D-20260929-T3R2SCORE-001 — T3第二轮五 lane 回分（v0049 TIE，其余不晋级）

- authorization: 用户供给分数表（2026-09-28 07:30–07:33 五条 T3 总分及各五子项），按既定回填链登记。
- decision: v0049 47.86（−0.07 vs v0048）在 ±0.1 平局带内，记 scored TIE backup，不并列晋级；v0053/v0052/v0050/v0051 依次 −0.27/−0.31/−0.53/−1.86 → REJECT。selection 保持 v0048（47.93）。高分叠加（v0048+v0046）没有超过 v0048 自己。severity_slope 五条仍是 50.0，无区分信号。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t3-round2-score-return-20260929；INDEX 五行 scored（SHA 实核通过：v0049 `19094705…`、v0050 `4a0ca825…`、v0051 `bc88b624…`、v0052 `652d3b0a…`、v0053 `ed4e82fe…`）；SUBMETRIC＋25 行；verdicts T3-ROUND2 五行 SHIPPED。
- boundary: 总分未从舍入子项重构；单次回分不证明叠加机制有效；本次无新拟合/候选；blocks_submission: false.

## D-20260929-T1THREESCORE-001 — T1三路线回分（v0035 晋级新 best）

- authorization: 用户供给分数表（2026-09-28 18:57–19:08 三条 T1 总分及各四子项），按既定回填链登记。
- decision: v0035 53.43（+0.93 vs v0029）PROMOTED 为新 T1 selection；v0036 53.36 距新 best −0.07，按不并列晋级规则记 scored backup；v0034 53.24（−0.19 vs 新 best）REJECT，但仍高于旧线，记 scored。三条相对 v0029 四个子项同涨，最大的是方向（+1.0 到 +1.7），属描述不属机制。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t1-three-score-return-20260929；INDEX 三行 scored（SHA 实核通过：v0034 `dbe266bd…`、v0035 `d5cce857…`、v0036 `89891ef9…`）；SUBMETRIC＋12 行；verdicts T1-THREE 三行 SHIPPED。
- boundary: 总分未从舍入子项重构；三条 exploration-only（报告场景分、无 E10.5 真值），不作机制推断；本次无新拟合/候选；blocks_submission: false.

## D-20260929-T2R2SCORE-001 — T2第二轮回分（胚胎+心脏插值双晋级，外推不动）

- authorization: 用户供给分数表（2026-09-28 19:05–19:08 心脏插值五条+外推一条；2026-09-29 04:36–04:39 胚胎五条；07:33–07:35 外推三条；各八子项；另附一条胚胎榜误投拒收备注），按既定回填链登记。
- decision: 胚胎 v0014 62.89（+0.60）PROMOTED 新 board best；心脏插值 v0019 62.36（先返回，+0.32）PROMOTED 新 board best，v0016 62.35（−0.01）按不并列规则记 backup；其余插值/胚胎 lane 不晋级（v0020 心脏插值 57.74 属表达侧塌：mmd_u 36.8、variogram 38.6，几何未动）。外推四条无一进入合计：v0019 50.38（−0.15 vs baseline）、v0021 50.52（baseline 平局、−0.12 vs board-best 50.64）、v0020/v0018 更差。外推选择与 50.64-vs-50.53 OPEN 项不变。
- rejected_attempt: 外推文件 v0020（25179 细胞）误投胚胎榜被拒（该榜只收 583–5000 细胞），只记 registry，不改 INDEX；该文件外推榜分数 48.59 有效。
- derived_total: 159.95（53.43 + 58.59 + 47.93；T2 = (62.89+62.36+50.53)/3 = 58.59）。推导值，待门户页面确认，不得引用为服务器值。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t2-round2-score-return-20260929；INDEX 14 行 scored（SHA 全部实核通过）；SUBMETRIC＋112 行；verdicts T2-ROUND2 14 行 SHIPPED（x_n1_lineage 未在本次回分，仍 PENDING）。
- boundary: 用户供给，未查询服务器；未提供 submission ID。分数按供给精度登记，不从舍入子项重构；子项解读只作描述；本次无新拟合/候选；blocks_submission: false.

## D-20260929-T3SCORE-002 — T3最后六 lane 回分（v0058 平局，其余不晋级）

- authorization: 用户供给分数表（三路线 v0054–v0056 与五选三 v0057–v0059 的总分及各五子项；单条时间未提供），按既定回填链登记。
- decision: v0058 47.95（+0.02 vs v0048）在 ±0.1 平局带内，记 scored TIE backup，不并列晋级；v0056/v0059 均为 47.93，与现役精确打平，不晋级（五子项与 v0048 在供给精度下相同：42.6/50.0/50.0/51.8/49.3）；v0054/v0057/v0055 依次 −0.18/−0.56/−0.68 → REJECT。selection 保持 v0048（47.93）。T3 分数队列关闭：无 score_pending T3 候选。
- evidence: reports/SERVER_SCORE_REGISTRY.md#t3-pending-score-return-20260929；INDEX 六行 scored（SHA 实核通过：v0054 `dd4ff51f…`、v0055 `11076fed…`、v0056 `586fad56…`、v0057 `06a7dc29…`、v0058 `b671f35b…`、v0059 `914054b8…`）；SUBMETRIC＋30 行；verdicts 六行 SHIPPED；AUDIT 重生成（106 lanes，10 pending）。
- boundary: 总分未从舍入子项重构；v0058 与 v0048 机制不同但读数相同，只作描述不作机制推断；本次无新拟合/候选；blocks_submission: false.

### D-20260929-T3THREE-001 — T3 三个响应候选完成

用户要求三路线并交付三个可提交h5ad。实际执行r1agree=v0054（高分H/G同向门控叠加）、r2damp=v0055（概率分量减弱）、r3diffuse=v0056（类型/活跃细胞内响应扩散）；完整7449×500推断、四块WT重新拟合及条件诊断完成，12测试、三模型独立重放、contract、旧候选去重、direct export和ZIP校验PASS。局部r1胜H但不胜无门叠加，r2弱于H，r3仅极小变化；不据此宣称KO准确率提高。best v0048=47.93保持，三项未提交/未评分。交付deliveries/t3three_20260929/与deliveries/t3three__t3__upload__20260929.zip；证据reports/t3_three_20260929/REPORT.md。匹配KO官方scorer NOT_RUN，blocks_submission:false。

### D-20260929-T1THREE-001 — T1 三路线提交包完成

用户授权设计/实现三路线并交付含三个可提交h5ad的包。r1compose=v0034、r2joint=v0035、r3mix=v0036均实际执行，完整5118×32285、三次32285列官方本地scorer、13测试、独立模型重放/整行身份/contract与ZIP SHA/CRC通过。v0035相对v0029本地DE持平其余四主项改善，并在同类型人数下胜r1；与v0030仍有DE/MMD取舍。r1/r3有DE代价，r3五主项弱于v0030，不追调参数。三个未提交/未评分，best仍v0029=52.50。证据reports/t1_three_20260929/REPORT.md；deliveries/t1three__t1__upload__20260929.zip。隐藏未来真值未运行，基础模型按设计复用冻结组件；blocks_submission:false。

### D-20260929-T2ROUND2-001 — T2 三新两优化 × 三 board 完成

用户授权 T2 三个子任务各 5 候选（3 新路线+2 优化/合并）。15 候选实际执行：embryo v0011–v0015（分位数桥/三阶段趋势/子状态粒度/×收缩/×尺度回锁）、heart v0016–v0020（分位数桥/E9.5 曲率桥/cm 联合粒度/×收缩/+文库重标定）、extrap v0017–v0021（谱系映射 delta/三阶段趋势/组成趋势外推/趋势×收缩/v0011×组成趋势）。15 项测试、10 严格 contract PASS + 5 FAIL_BY_DESIGN_ACCEPTED（R2 同四类）、工程门 15/15、独立重放 15/15 字节一致、v0011 收缩组件逐值复现、v0010/v0013 质量计划逐名复现、ZIP 成员 SHA/CRC PASS。heart 全部无 5% nmmd 旗帜；x_o2 唯一过历史 R1 局部双门（该门方向不可靠已声明）；embryo 按 M0 附录 B 只记录。15 件未提交/未评分，三 board best 不变（62.29/62.04/50.53）。证据 reports/t2_round2_20260929/REPORT.md；deliveries/t2r2__t2__upload__20260929.zip。隐藏真值与服务器评分 NOT_RUN；blocks_submission:false。

### D-20260929-T3FIVESELECT-001 — T3 五路线完整运行、固定选三

用户授权实现五条T3路线并交付三件。活动量门控来源组合、基因同号来源组合、四次bootstrap hurdle、非线性hurdle、局部残差校正均完整7449×500实际执行。训练块0/1、开发2按族选1+2、名单锁定后审计3；选中v0057/r2gene、v0058/r4spline、v0059/r3bag，另两条PARKED保留研究输出，无工程失败、不调参挽救。6测试及独立进程14项验收、五条contract/重放/去重与ZIP SHA/CRC通过。bootstrap开发略差H、审计略好；仅3/2个WT组，不构成KO或服务器改进。三个未提交/未评分，best v0048=47.93保持，匹配KO scorer NOT_RUN，科学NOT_IDENTIFIABLE；blocks_submission:false。证据 reports/t3_five_select_20260929/REPORT.md；deliveries/t3five3__t3__upload__20260929.zip。

### D-20260930-T1SEVEN-001 — T1 七路线完整执行

用户授权3新＋2失败优化＋2成功优化。七条完整report/future拟合推断，七次32285列官方本地scorer，8测试和14矩阵独立重放/模型参数与训练边界检查通过；4父矩阵精确复现，ZIP SHA/CRC通过。候选v0037、v0038、v0039、v0040、v0042、v0041、v0043均未提交/未评分；best v0035=53.43保持。失败优化追溯v0031/v0033，成功优化基于v0035/v0036；局部取舍与负结果见reports/t1_seven_20260930/REPORT.md，不追调参数救援。未来真值NOT_RUN、科学EXPLORATORY_LOCAL，blocks_submission:false。包deliveries/t1seven__t1__upload__20260930.zip。

## D-20260930-T1SCORE-001 — T1十一条回分，v0038晋级、v0043精确同分备份

- authorization/evidence：用户本轮提供11个文件总分与44子项；reports/SERVER_SCORE_REGISTRY.md#t1-seven-pbmean-score-return-20260930。11个本地SHA与INDEX一致；submission ID、时间、门户Total未提供，不补造。
- decision：v0038/v0043均53.55，较v0035+0.12，超过±0.1带；同批按供给列表顺序登记v0038为selection，v0043备份，不推断上传时间、不并列晋级。Top3为v0038、v0043、v0035。其他九条不晋级，T1待分清零。
- review：新路线并非全失败，协方差路线胜出；双模型混合亦胜出，二者本地局部五项不能完整预示服务器结果。两条失败优化未胜旧best。平均数平移四臂均大幅损失，尤其variogram；局部均值向量的高分不是截断后提交矩阵的完整评估，不能证明泛化。终止本批平均数平移家族的提分推荐，不追加alpha扫描。
- limits：子项归因为描述，不识别因果机制；+0.12是登记规则上的晋级，不是重复测量统计显著性。推导合计160.07，不是门户新Total；现役选集仅本地登记，未操作portal。blocks_submission:false。报告reports/t1_score_review_20260930/REPORT.md。

## D-20260930-T2XN1SCORE-001 — T2第二轮收尾，x_n1_lineage回分REJECT
- authorization/evidence：用户本轮提供外推v0017总分48.17与八子项；reports/SERVER_SCORE_REGISTRY.md#t2-xn1-score-return-20260930。本地SHA 7ffd3053…与INDEX一致；submission ID、时间、门户Total未提供，不补造。
- decision：v0017较baseline 50.53低2.36、较board-best 50.64低2.47，REJECT；外推选择不变（合计仍用baseline 50.53）。第二轮15/15回分完毕，队列关闭。
- review：17个零位移类型的谱系映射delta在外推榜无增益；variogram 33.3为八项最弱，与外推榜“空间自相关是余量”模式一致，不作机制解读。
- limits：单次回报，无重复测量显著性；推导合计160.07仍是本地派生，不是门户新Total；现役选集仅本地登记，未操作portal。blocks_submission:false。

## D-20260930-T2R3SCORE-001 — B4-T2-R3三条迟到回分，v0009平局、余下REJECT
- authorization/evidence：用户本轮提供外推v0008/v0009/v0010总分与24子项；reports/SERVER_SCORE_REGISTRY.md#t2-r3-score-return-20260930。本地SHA（a58896c9…/f692fd8f…/4475b233…）与INDEX一致；包deliveries/b4t2r3__t2__upload__20260914.zip当年已打好、无receipt；submission ID、时间、门户Total未提供，不补造。
- decision：v0009 50.51较baseline 50.53低0.02，落在±0.1带内判TIE，但低于board-best 50.64，不晋级；v0008 48.40、v0010 48.87均REJECT。外推选择不变（合计仍用baseline 50.53）。B4的closed_unscored结清，无未来待分。
- review：时间归一1.333倍Delta外推追平无变化基线但超不过收缩lane；其de 50.4为外推尝试最强，但总分不动，仅描述。阻尼与半嫁接两条在de与variogram双输。
- limits：单次回报，无重复测量显著性；推导合计160.07仍是本地派生，不是门户新Total；现役选集仅本地登记，未操作portal。blocks_submission:false。

## D-20260930-T3SIX-001：报告完整计划登记，六项优先路线开始执行

- 授权：用户明确要求先将 reports/t3_research_audit_20260930/REPORT.md 完整实现计划计入 leads，再执行六项优先路线。L-010 已登记八方向及六个执行项，其余三方向为后续 leads。
- 六项：原生状态化 CellOracle、显式状态质量、独立 TF 活动、功能 embedding 线性/双线性、作者 Scouter、作者 GEARS。核心拟合和完整推断均须实跑，不能用旧结果、smoke、子集或自制小 GCN 替代。
- 责任：coordinator 串行更新账本；新实现独占 scripts/t3_priority_six/、configs/t3_priority_six/、tests/test_t3_priority_six.py、artifacts/t3_priority_six_20260930/、reports/t3_priority_six_20260930/；旧评分产物只读。
- 来源：优先复用已批准 GSE261783 OP2 resting 26 扰动及 WT atlas；功能表示/原工具及扩展基因输入须逐项记录来源与许可，新增数据更新索引。整扰动留出不把随机细胞配对当独立重复。
- 状态：EXECUTION_STARTED，六项未评分/未提交；现役 v0048 保持。目标匹配 Gata4 KO 真值缺失，来源域结果不能称目标验证。旧 S1 科学 gate 保留，blocks_submission:false；本轮不自动上传 portal。

## D-20261001-T3SIX-002：六项核心执行交付；状态质量零效应保留

- 六项核心拟合与完整目标推断实际完成：CellOracle 全68910细胞×2000模型基因，状态质量与活动全目标，功能线性/双线性、作者Scouter与GEARS在完整5454来源细胞上的整扰动留出和26条件最终拟合。所有目标为7449×500。原报告完整八方向已在L-010，后三方向仍未运行。
- 来源结果：功能线性/双线性略胜平均扰动；Scouter GO128和GEARS小鼠GO没有超过平均扰动。未删困难扰动或重选test。Scouter为作者自定义GO表示变体，不冒称GenePT1536论文复现；GEARS为完整panel的作者原模型，不冒称全转录组。
- 质量路线：硬状态跨越0/68910，预测质量等于WT，NULL_STATE_MASS_RESPONSE；不登记质量单独及组合两件。修正初版随机采样制造假变化为整数配额/无变化精确保留原行，早期未登记输出隔离保留。
- 交付：v0060–v0065，父v0009，六件contract PASS，包deliveries/t3six__t3__upload__20260930.zip；5项针对性测试PASS，hash/CRC核验PASS。候选哈希以submissions/INDEX.tsv为准。未提交/未评分，score_pending，现役v0048不变；没有操作portal。
- 证据：reports/t3_priority_six_20260930/REPORT.md；artifacts/t3_priority_six_20260930/DELIVERY.json。新GO派生输入已更新infra/bioinf-data-index/。完整Gata4目标scorer NOT_RUN_NO_MATCHED_GATA4_TRUTH；成人→胚胎迁移、活动失活尺度及科学因果机制仍未验证，blocks_submission:false。

D-20261001-T3SIX-002 包装补充：最终交付包为 deliveries/t3six__t3__upload__20261001.zip；六成员 artifact/INDEX 不变。证据清单分别指向 CALIBRATED 与 core RESULT，并补 exact native 输入锁；首次未交付包装移入 artifacts/t3_priority_six_20260930/packaging_attempts/，保留审计，不作为交付。

## D-20261001-T2GOAL-001 — goal三board×两轮建成合打一包，均提交计轮
- authorization/evidence：goal mupdz021-pfttwg；设计reports/T2_GOAL_DESIGN_20261001.md + configs/t2_goal/design_20261001.json；报告reports/t2_goal_20261001/REPORT.md。6候选SHA与INDEX一致；包deliveries/t2goal__t2__upload__20261001.zip（receipt READY_NOT_SUBMITTED）。
- decision：R1三条（v0016/v0021/v0022）与R2三条（v0017/v0022/v0023）全部contract通过（2条为预声明pass_with_deviation）、6/6重放一致；轻微问题如实记录，无严重落后、无重开，计6轮。合打一包交付，待用户上传回分。
- review：趋势份额×现役表达为新组合；C=1收缩为T1证据移植的单冻结变体；lateref为单参照替换。本地不作晋级宣称。
- limits：分数未回填前只能标记score_pending，不得宣称进步；推导合计不得引用为门户值。blocks_submission:false。

## D-20261001-T3SIXSCORE-001：T3 六件全部回分，REJECT；实现审计定位转换风险

- 来源：用户逐件提供六总分及30显示子项；上传包/manifest/INDEX/实际H5AD SHA身份核对PASS。submission ID和实际提交时间未提供；不发明门户Total，不独立声称已查询portal。权威分数见reports/SERVER_SCORE_REGISTRY.md#t3-priority-six-score-return-20261001。
- 裁决：v0060–v0065全低于现役v0048（47.93）超过0.1，全部REJECT；现役与平局备份不变，T3 score_pending清零。v0060与旧v0018的-0.03属于平局，没有恢复虚拟敲除增益。状态质量NULL无候选、无回分。
- 实现审计：共同decoder保状态count均值，却改变评分读取的log均值；活动路线64/316个非微小响应方向被转换翻转，其他路线也出现位移放大。来源Stmn2 220对照全零，线性预测微增量经0.001分母成为约29.83倍效应。局部诊断证明转换不透明，不证明单一掉分原因。
- 范围：Scouter是GO128变体，GEARS是500输出panel的作者小鼠图实现；本次负结果只针对具体数据/表示/reference/decoder，不普遍证伪神经网络或原论文。来源留出小增量没有验证跨平台完整输出。
- 后续：当前六件关闭；L-010保留后三方向及有明确信息增量的新分支，先使完整转换后的验证对象与评分空间一致。此任务未重训、未改已评分artifact、未生成新候选、未再上传。科学因果识别不足，blocks_submission:false。复盘reports/t3_score_review_20261001/REPORT.md。

## D-20261001-T2GOALSCORE-001 — T2-GOAL六件回分：五REJECT + 外推一TIE最高数备份，选择不变
- 来源：用户本轮提供11组总分及子项；其中5组（x_n1 v0017 48.17、x_o2 v0021 50.52、T1 v0044 48.75 / v0045 47.92 / v0046 49.10）与已登记值逐位一致，不重复登记。本决策仅登记6件T2-GOAL新分；submission ID/提交时间/门户Total未提供，不发明，不独立声称已查portal。权威分数见reports/SERVER_SCORE_REGISTRY.md#t2-goal-score-return-20261001，子项见reports/SERVER_SUBMETRIC_REGISTRY.tsv。
- 裁决：胚胎e_r1 61.65（-1.24）/e_r2 62.55（-0.34）REJECT，现役v0014 62.89不变；心脏插值h_r1 62.22（-0.14）/h_r2 62.21（-0.15）REJECT，现役v0019 62.36不变；外推x_r2 50.03（-0.50 vs基线）REJECT，x_r1 50.74（+0.21 vs基线/+0.10 vs原最高v0011 50.64）恰落±0.1平局带上沿，按不并列规则记TIE最高数备份、不晋级，v0011留任、合计仍用50.53。T2-GOAL待分清零（6/6）。
- 范围：趋势份额×现役表达组合与C=1收缩单变体均未在服务器上超过shrinkmerge现役；x_r1的de 53.7为外推迄今最强差异表达读数但总分仍受平局规则约束，仅描述。推导合计160.07不变（非门户值），门户确认合计仍156.06；外推OPEN项更新为50.74-vs-50.53，待重读门户。本任务未重训、未改已评分artifact、未生成新候选。blocks_submission:false。

### D-20261001-T1D2R3-001 — D2 调参 R3 单轮启动（用户授权，09-17 特批延续）
- scope: T1-P2 D2 CellMNN patience 调参（dz=20 冻结，种子 20260916 冻结，LR/WD/batch/loss/门全冻结）
- decision: "单轮 R3：`--max-checks 120`（默认 40 即冻结行为不变），新 run 目录 `artifacts/g0/G1-T1-D2R3-PATIENCE-20261001-v1`，候选号 v0048（v0022 已被 D3 占用）。门不变（de>0.8868 且 dir>0.8895），过则按 standing 流程建候选/登记/打包，不自动上传；不过则 D2 关闭。不做 sweep、不调第二参（延续 D-20260917-T1P23-001 的调参红线例外，不构成先例）。"
- evidence: "用户原话'D2调参启动'（2026-10-01）；触发条件 D3/D1 双败已满足（D-20260917-T1D3-001、D-20260917-T1D1 均 FAIL 关闭）；R2 基线 de 0.8113/dir 0.8652（410 步 patience 耗尽停，非 cap 停，故加 patience 是对因单轮）。"
- boundary: "脚本改动仅 --max-checks 透传＋候选目录号＋diag 记录（默认行为逐位不变）；复活即开新 run 目录已执行；blocks_submission: false。"
- review_trigger: "R3 门结果；无论过与不过，分数/关闭都要回填 registry/INDEX/TRACKING。"

### D-20261001-T1D2R3-002 — D2-R3 挂门，D2 关闭（预声明执行）
- scope: T1-P2 D2 CellMNN R3 patience 单轮仲裁
- decision: "R3 1210 步足额跑完仍挂门（de 0.8113/dir 0.8652，双低于 0.8868/0.8895），按 R3 启动决议关闭 D2，不再扫 patience 或其他超参。patience 轴在 D2 上判为死路：最优检查点位置不受 patience 影响。"
- evidence: "run `artifacts/g0/G1-T1-D2R3-PATIENCE-20261001-v1/RESULT.json`：train_steps 1210、best_val_mmd 0.013763200491666794 与 R2 逐位相同、local 八项与 R2 逐位相同、contract PASS、wall 457s。"
- boundary: "v0048 候选目录永不进 INDEX/submissions/上传包，仅作 run 内不可变诊断物；T1-P2 至此无剩余路线；blocks_submission: false。"
- review_trigger: "无（关闭）；复活需全新 lane 立项＋新决议。"

## D-20261001-T3ARCH-001 — T3 两次额度的架构研究建议（非运行启动）

- 来源：用户要求结合全部尝试与独立检索，判断两次剩余额度的新架构方向。
- 建议：A为WT锚定、基因功能条件化的联合分布残差OT flow；B为谱系条件化的发育分支与相对群体份额联合模型。禁止把旧hurdle/occupancy、硬状态softmax替换、仅换embedding或decoder调参记成这两条架构。完整设计见reports/t3_two_architectures_20261001/REPORT.md，检索IDs/降级见同目录JSON，登记L-012。
- 边界：DESIGN_ONLY、两条NOT_RUN，未训练/未生成候选/未提交/未评分，不占用候选号、不消耗或核验portal额度；不自动重开关闭分支。既有现役与分数不变。来源26扰动向胚胎的迁移不足、B的Gata4干预入口与份额识别缺口显式保留；blocks_submission: false。
- 后续：实施时冻结输入、结构和训练预算，完成核心算法与完整目标矩阵后再登记候选；共同log-space链路修复不算独立架构，不从服务器分数反演目标比例。

## D-20261001-T3ARCH-002 — 用户授权两项架构顺序执行
- 用户原话：“你来逐次完成两项你提出的工作”。顺序A条件残差flow→B软发育命运/相对份额；每项完整核心计算、来源/WT验证、完整目标推断、contract、候选登记，最终一个批次包，无自动portal操作。
- 冻结配置：artifacts/t3_arch_two_20261001/CONFIG.json；owned新增scripts/t3_arch_two/、对应artifacts/reports，仅复用旧工具/数据、不修改共享旧模型或已评分artifact。A使用实际TorchCFM采样器和逐条件/样本全量exact OT；B为全细胞聚合UOT监督的非线性转移/质量双头，非原生DeepRUOT复现。科学不确定blocks_submission:false；核心不能执行则记录，不冒称完成。

## D-20261001-T3ARCH-003 — B未上传初版撤回并修复WT发射抽样
- 证据：冻结状态配额仅需替换223/7449行；v0067有放回整簇重抽仅保留6063个不同原始WT细胞，额外抽样噪声不属于模型预测。未上传/未评分，旧文件/hash保留，INDEX标invalidated_unsubmitted。
- 修复：不改神经模型/WT拟合/干预/状态份额，只在同一配额下最大保留原有WT细胞；新b_fate_mass_emit2另登记。两次手工上传预算仍只用于A与修正版B，不提交v0067。blocks_submission:false。

## D-20261001-T3ARCH-004 — 两架构执行完成，交付两件探索候选
- 顺序A→B已完成；最终v0066/a_flow、v0068/b_fate均完整7449×500、contract PASS、READY_NOT_SUBMITTED/score_pending；统一包deliveries/arch2__t3__upload__20261001.zip。v0067未上传初版撤回并保留旧文件，不能提交。
- 验收：4项数值测试、A完整目标模型重放、B完整供体/配额追溯、空时间identity、输入锁、INDEX/canonical/package CRC与SHA一致全部通过。证据artifacts/t3_arch_two_20261001/ACCEPTANCE.json与DELIVERY.json，候选哈希只以INDEX及包manifest为准。
- 科学边界：A来源侧ΔMSE/MMD未胜平均/功能线性；B的WT中间时点覆盖69.65%，未整体胜简单份额插值；Gata4活动代理仅约解释10.5%WT RNA变异，KO功能/因果效应未验证。B完整输入110239个WT，使用声明的64状态聚合UOT，非全细胞pairwise OT或原生DeepRUOT。来源及结构完整，不因科学不足阻止合规探索，blocks_submission:false。
- 后续：用户可手工上传这两件并返回总分及五项子分；无自动portal操作、无新服务器分数或晋级，现役不变。完整报告reports/t3_arch_two_execution_20261001/REPORT.md。

## D-20261001-T3ARCHSCORE-001 — 两项新架构回分，均REJECT、当前配置关闭
- 来源：用户提供v0066/a_flow 43.21、v0068/b_fate 46.37及全部10子项；身份按交付包/INDEX/canonical SHA256匹配。原始证据reports/t3_arch_two_score_review_20261001/USER_SCORE_REPORT.md；权威分数reports/SERVER_SCORE_REGISTRY.md#t3-architecture-two-score-return-20261001。未独立查询portal，submission ID、实际提交时间、新门户Total均未知。
- 裁决：相对现役47.93分别−4.72/−1.56，均REJECT。v0066方向53.5是已登记T3方向子项最高显示值，但DE recovery与分布损失主导；不是正确率/显著性。v0068比Gata4-zero载体46.95低0.58，当前组成预测没有收益。v0067仍未提交撤回，无分数。
- 状态：两件score_pending→scored，T3待分清零，两条当前架构配置关闭；现役v0048及平局备份v0058不变，推导合计/上次门户Total不变。已评分artifact与创建时执行/交付收据不改，不自动重训或新建候选。
- 范围：否定这两个实现的提分主张，不普遍否定flow/神经网络/组成通道。来源覆盖与跨域背景、弱TF功能代理和WT时序覆盖缺口均保留，因果机制NOT_IDENTIFIED，blocks_submission:false。后续重开须明确新增响应依据/合法来源/适用背景，不能仅因单项方向亮点就晋级。复盘reports/t3_arch_two_score_review_20261001/REPORT.md。

### D-20261001-SCALE-001 — Scaling 四条路线程序建立（用户授权逐个完成）
- scope: ①T1-D5c 长训 ②T3 方向四全转录组中介 ③T3 方向六多扰动监督 ④T1 外部时序预训练；一次只跑一条，按序推进
- decision: "用户指令逐个完成四条。每条跑前写死设计冻结（假设/门/预算/停止条件），触发停止条件即停并记录，不硬凑。每条的候选/上传/回填仍走 standing 链（INDEX/scorer/contract/registry），不自动上传。顺序不可并行：后一条须等前一条关闭（晋级或关闭）后再开工。"
- evidence: "用户原话（2026-10-01）；各条设计依据：D5c 见 D-20260917-T1D5B-002（10× 量属新假设）；方向四/六见 reports/T3_NEXT_ROUTES_20260920.md（PROPOSED/NOT_RUN）；外部预训练见 T1 P0-2 缺口记录。"
- boundary: "GPU 未获批前 D5c 只做设计冻结不训练；方向六/外部预训练的数据任务先行、训练后行；无合规数据则 BLOCKED 停，不下载可疑来源。blocks_submission: false。"
- review_trigger: "每条关闭或晋级；用户动作（GPU/邮件/上传）到位情况。"

### D-20261001-T1D5C-001 — D5c 挂门关闭，扩散线三振出局（预声明执行）
- scope: T1-D5C 200 epochs 公平检验（G-return 分布门仲裁）
- decision: "G 门挂即关闭：overall 3.88 vs 基线 0.265、pertype 4.99 vs 0.63；D5c 关闭，不建 v0049，不上传。扩散线三振（D5 测试无效、D5b 欠拟合 27×、D5c 足量 14.7× 仍败），不再立扩散新 lane。10× 相对 D5b 好转（27×→14.7×）记为方向性事实，不构成复活理由。"
- evidence: "`artifacts/g0/G1-T1-D5C-DIFF-20261001-v1/BUILD.json`（gate False，veto False，8 types，基线复现精确）；训练 `RESULT_train.json`（6800 步/200 epochs 足额，wall 986s，无 NaN）。"
- boundary: "未建候选，INDEX/submissions 零改动；T1-P2 扩散轴永久关闭；blocks_submission: false。"
- review_trigger: "无（关闭）。"

- id: D-20261002-ARROUTEC-001
  date: 2026-10-02
  task: T2
  kind: exploratory_batch_packaged
  decision: "Route C 自动研究轮收口并打包 5 个外推板候选待服务器仲裁（v0024-v0028）。冻结目标 = 门户对该板实际返回的 8 个 skill 通道等权综合（`.auto/composite_config.json`，方向逐条从 scorer 源码 docstring 核实）。本地最优 v0024 = 时间归一化(4/3) 分位数边缘外推 × compmix 重采样，综合 3.913（expr 6.812），三种子 {3.913, 4.0088, 3.6058} 全部超过此前本地最强 lane x_o2=1.709；v0025=3.464、v0028=3.606（同设计换种子）、v0026=2.608（确定性、无重采样、唯一 strict contract PASS）、v0027=0.855 但 expr 11.479（诊断探针，已知 library 12×、护栏不过，不建议占名额）。零上传；INDEX 登记 score_pending。"
  corrections: "① variogram 本地指标方向为「越低越好」（core_metrics.py:326），此前 Route B 头部写反，其 comp-only keep 撤回为劣化（artifact 仅作研究记录，不作候选）；② 已停用的失败轴：均值平移族（7 个设计把 de 钉死在 0.2466）、协方差对齐（+55% vario 劣化）、PC 空间分位（-0.60）、二次分位外推（方差 3.3×）、SVD 去噪（-1.38）、FDR 门控（2500/2500 饱和）。"
  evidence: "跑前冻结 `.auto/composite_config.json`；全记录 `.auto/log.jsonl`（31+ 条）；汇总 `.auto/ROUTE_C_SUMMARY.md`；代理校准 Spearman 0.538（n=12，仅用已有服务器分的 lane）；交付 `deliveries/arcqte__t2__upload__20261002.zip` sha256 f51e79a397c7f5d77b916decee35dc6c…；成员 t2_hrt_ext__qte_tc_s929__v0024.h5ad, t2_hrt_ext__qte_compmix__v0025.h5ad, t2_hrt_ext__qte_time__v0026.h5ad, t2_hrt_ext__sharetrend_qte__v0027.h5ad, t2_hrt_ext__qte_tc_s008__v0028.h5ad。"
  boundary: "本地分数不是 leaderboard 证据，代理只中等相关且该板历史上出现过反向/对抗行为；v0027 自带已知缺陷；服务器分数未回填前不得宣称进步，回分后须按 SERVER_SCORE_REGISTRY + SERVER_SUBMETRIC_REGISTRY 双登记并重读门户合计（外推 50.74-vs-50.53 OPEN 项仍在）。blocks_submission: false。"
  review_trigger: "用户返回任一成员的门户分数时。"

### D-20261002-T3DIR4-001 — T3 方向四双挂关闭（预声明执行）
- scope: T3-DIR4 全转录组中介映射全量仲裁
- decision: "G1/G2 同败即关闭：留出验证 0.552 vs 0.518、谱系集中 0.612 vs 0.80；不建候选，不配对比较（G3/增量无意义）。跨模态映射轴在 T3 判为死路：同样本相关 kNN 在 MERFISH 尺度上输给同类型均值，说明问题不在邻居数量（68910 已全量）而在跨模态本身。"
- evidence: "`artifacts/t3_direction4/T3-DIR4-20261001-v1/RESULT.json`（verdict STOP_no_candidate；per-celltype 7/33 胜、per-sample 9/16 胜）。"
- boundary: "未建候选，INDEX/submissions 零改动；方向五若借方向四补 panel 外信号的设想一并作废（§7 原文已有此条）；blocks_submission: false。"
- review_trigger: "无（关闭）。"

- id: D-20261002-ARROUTCESCORE-001
  date: 2026-10-02
  task: T2
  kind: score_return
  decision: "Route C 五件外推候选回分，全部 REJECT、零晋级：v0025 50.17、v0024 50.09、v0028 50.08、v0026 50.03（基线 50.53，board-best v0011 50.64，数值最高 x_r1 50.74），探针 v0027 39.60 灾难性失败。外推 selection 与 aggregate 保持 50.53，50.74-vs-50.53 OPEN 项不变。本地综合分不再作为提交依据。"
  findings:
    - "代理被证伪（对新产品族）：冻结 8 通道综合分在本轮 5 件上给出 +0.9…+3.9 的'改善'，服务器全部 ≤ 基线；全 17 条 Spearman 降至 0.122（旧 12 条 0.539）。今后本地分只能用于同族内排序，跨族提交必须带服务器锚点。"
    - "第一个确证可迁移通道 = variogram：本轮 49.5–50.1 为该榜历史最好（旧 lane 47.4–48.5），且与本地（方向已纠正为越低越好）排序一致。这是本轮唯一可继承的技术资产。"
    - "de_score 通道反转：本轮 45.8–46.8 vs 旧 lane 48.9–50.0，尽管本地 de 更高；优化本地 DE 读数会主动损耗服务器 DE。"
    - "服务器侧抽签方差可忽略：v0024/v0028 同设计不同行 → 50.09 vs 50.08（Δ0.01），而本地综合差 0.31（8.5%）。本地 3 种子中位规则对服务器而言属过度保守。"
    - "本地护栏是唯一预测正确的部件：v0027 的 library 11.98×/variance 1.74 预警与其服务器崩塌一致。"
  evidence: "reports/SERVER_SCORE_REGISTRY.md#route-c-extrap-score-return--2026-10-02；reports/SERVER_SUBMETRIC_REGISTRY.tsv（40 行 = 5 件 × 8 技能）；submissions/INDEX.tsv v0024-v0028 已回填 score+scored；reports/LANE_VERDICTS.tsv 五行；交付 deliveries/arcqte__t2__upload__20261002.zip（sha f51e79a3…）；本地过程 .auto/log.jsonl + .auto/ROUTE_C_SUMMARY.md（含 variogram 方向纠正与失败轴台账）"
  boundary: "用户报告的分数与八项技能，无 submission ID、无时间戳、无门户 Total；未做独立门户查询。artifact 冻结不可变。无 Total 变化，无晋级声明。blocks_submission: false"
  review_trigger: "需要新证据才能重启该轴：或（a）拿到该板 variogram 通道的服务器锚点族，或（b）用户重读门户（50.74-vs-50.53）。"

- id: D-20261002-T3AR-001
  date: 2026-10-02
  task: T3
  kind: local_research_target_complete
  decision: "用户确认的前台autoresearch本地目标完成：48次实测，13保留/35回滚；固定17原训练扰动LOPO、500输出基因，MSE 0.004258208→0.003393314，降低20.3112%。控制器达到20%后停止；保留具体复合物响应迁移与幅度收缩模块，不据此晋级服务器现役。"
  evidence: "reports/t3_autoresearch_20261002/REPORT.md；FINAL_CHECK.json；EXPERIMENTS.tsv；artifacts/autoresearch/t3-20261002-v1/autoresearch-results/events.jsonl；保留commit 1b9847b0472d9b893face74f564e80eff29500b4。"
  final_check: "模型锁定后一次检查：原val3扰动MSE降低17.4561%；原test6扰动降低6.1245%（4改善/2变差），配对扰动bootstrap区间跨零。历史test早前已被评估，不能称全新独立外部验证。检查后无调参。"
  boundary: "48次自适应开发选择；成人成纤维细胞来源、两sample独立动物未确认；Gata4仅1个具体复合物供体，未触发高可信GO供体分支。无目标真值、无H5AD候选、未提交/未评分，服务器现役不变。科学限制blocks_submission:false。"
  review_trigger: "新的Gata4响应依据或目标域迁移方案；后续不得把已检查test当作未使用的选择集。"

## D-20261003-T2LOCAL-001 — T2 heart外推本地尺度优化达到确认目标

- 用户确认codex-autoresearch前台目标≥6.0；独立仓库run `4c13e854a96e450b834647507385bfe5`，一次实验完成，控制器complete。
- 冻结三种子中位数3.912955→7.523743，三次完整panel评分与全部护栏通过；baseline同时完整复测。表达/行序/组成不变，仅围绕质心坐标乘0.9。
- 原始通道比较仅scale_log_ratio改变，且已达到冻结公式的+30%截断；其余七通道不变。E9.5子集proxy存在几何偏倚，历史跨机制排序已失效；不作表达或服务器提升宣称。
- 候选v0029，父v0024；contract相对直接父PASS，身份见submissions/INDEX.tsv。祖先组成偏离保留披露，未提交/未评分，score_pending。
- 决策：HOLD_LOCAL_ONLY；保留本地模型与结果，服务器选择不变。不继续已饱和尺度轴；后续路线先固定留阶段外推评估。
- 证据：reports/t2_autoresearch_20261003/REPORT.md；comparison.json；独立仓库autoresearch-results/events.jsonl。
- blocker: none；blocks_submission: false；独立外推验证NOT_RUN。

- id: D-20261003-T3ARDEL-001
  date: 2026-10-03
  task: T3
  kind: candidate_delivery
  decision: "补齐上一轮缺失的H5AD交付：v0070 ar_complex，父v0009，完整7449×500，contract PASS，登记score_pending，单件H5AD与完整ZIP已生成；未提交/未评分。"
  evidence: "reports/t3_autoresearch_delivery_20261003/REPORT.md；HANDOFF.json；ACCEPTANCE.json；候选路径、SHA256、contract以submissions/INDEX.tsv对应行为准。"
  execution: "锁定模型全部26条件重放通过；log残差直接加入WT母本、截负、Gata4置零；保留细胞/基因/空间及内部保护的layers/raw。v0069未登记草稿仅参考元数据保护检查失败，v0070修复，X逐值一致。"
  boundary: "来源开发20.31%不是H5AD目标评分；正残差激活原零条目，截负改变负响应幅度，目标迁移尚未验证。服务器现役不变。blocks_submission:false。"
  next_action: "用户上传v0070，回传总分、各子项和submission ID/截图后入库；不伪造上传或评分。"

### D-20261002-T3DIR6-001 — T3 方向六放行（用户授权）
- scope: 方向六多扰动监督训练数据门（GSE261783 OP2 resting 集，26 扰动基因）
- decision: "用户放行：GSE261783 26 扰动已过显式黑名单 31 项（0/26 命中，`reports/t3_dir6_datascreen_20261002/REPORT.md`），许可由 QUARANTINE_NOT_APPROVED 转 RELEASED_BY_OWNER_20261002，model_input=true（仅此集）。残留如实保留：Smarca4/Rest/Yy1 功能性 phenocopy 人工复核仍 open（列复核提示，不扩黑名单）；organizer clearance 缺席（边界邮件未发）；其余来源仍需逐源审查。"
- evidence: "用户原话（2026-10-02 方向6放行）；26/26 屏蔽报告；本地文件 58MB SHA 见 intake receipt。"
- boundary: "放行仅覆盖 GSE261783 OP2 resting 集；训练仍走方向六设计（线性基线 vs 神经模型 gene-held-out）；blocks_submission: false。"
- review_trigger: "organizer 答复若收紧 phenocopy 口径，重新冻结 source 集。"

## D-20261003-T2SCALE-SCORE-001 — T2 v0029回分：尺度代理方向错误，当前配置关闭

用户回填总分与8项子分已登记权威server registry，身份按INDEX和ZIP成员SHA核对通过；submission ID/时间未提供，记录为unknown，不伪造。v0029 REJECT；与父v0024的七个非尺度子项完全相同，仅尺度恶化。本地综合增益完全来自尺度代理，因此本轮是局部目标达成、服务器迁移失败。原冻结实验事件保持不变，不能改写为模型成功。当前scale0.9配置关闭；现役、最高分和合计选择不变。下一步应先建立真正留阶段外推评价（NOT_RUN），不自动开启放大坐标或调参。本次不训练、不新增候选。证据：reports/t2_scale_score_review_20261003/REPORT.md；reports/SERVER_SCORE_REGISTRY.md#t2-scale09-score-return--2026-10-03。blocks_submission:false。

- id: D-20261003-T3ARSCORE-001
  date: 2026-10-03
  task: T3
  kind: server_score_return
  decision: "v0070用户回分与五子项原样登记，REJECT；当前统一残差配置关闭，现役v0048不变。"
  evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-autoresearch-score-return-20261003；reports/t3_autoresearch_score_review_20261003/REPORT.md；OUTPUT_AUDIT.json。"
  finding: "身份与表达公式重放PASS；来源均值MSE目标未覆盖最终单细胞矩阵，统一残差激活大量零值并扭曲负效应；Gata4只有一个特异复合物供体，高置信分支未启用。"
  boundary: "一次回分不能唯一归因来源模型或转换；保留来源域结果但不作目标晋级证据。未自动开始新实验；blocks_submission:false。"
  next_action: "后续先建立最终矩阵留扰动评估及输出失配诊断，再判断是否重开；不覆盖已评分文件。"

- id: D-20261003-T3SPARSE-001
  date: 2026-10-03
  task: T3
  kind: candidate_delivery
  decision: "按用户进一步优化并交付指令，生成v0071 sparse_scale，父v0048；完整7449×500、contract PASS、score_pending，未提交/未评分；现役不变。"
  evidence: "reports/t3_sparse_response_20261003/REPORT.md；DESIGN.md；FULL_MATRIX_METRICS.tsv；SELECTION.json；OUTPUT_CHECK.json；HANDOFF.json。候选身份以submissions/INDEX.tsv为准。"
  finding: "三个预设强度在来源17扰动LOPO实际矩阵五分项比较，选1.0；历史test基因对结构误差与均值MSE较旧加法改善，方向略退步。新方法开发平均秩未胜旧加法。输出保留v0048零结构，无激活/截负。"
  boundary: "来源重复使用、迁移未验证；换母本与换转换为联合候选，不是单因素服务器消融。blocks_submission:false。"
  next_action: "用户上传新H5AD/ZIP，回填总分和五子项；无分数前不晋级。"

### D-20261002-T3DIR6SRC-001 — 方向六 source v1 冻结（researcher 补检索后）
- scope: 方向六训练 source 集 v1（gene-held-out 的留出单位即 perturbation gene）
- decision: "冻结 source=GSE261783 OP2 resting（26 扰动＋220 对照，panel 500/500，已放行）。GSE92872（Datlinger CROP-seq，20 非黑名单基因）屏蔽通过但暂缓集成：单细胞小鼠成分仅一组 Drop-seq 混样， bulk/Jurkat 为主，集成成本大于当前收益；26 扰动不够时再议。GSE157977（Jin 脑，35 扰动）基因表未取到（Table S1 在 supplement 内，主文无），黑名单屏蔽未完成，且 P7 脑 readout 上下文远，记 GENE_LIST_PENDING 不下载。Axin 系维持排除。"
- evidence: "本会话 eutils 元数据（GSE92872 100 样本题录、GSE157977 38 样本确认）、sc-pert 23 行全表、黑名单 31 项比对（GSE92872 20 基因 0 命中）。"
- boundary: "gene-held-out 以 26 扰动为留出池；跨 cell context 无支持则只报同域；E10.5 真值不用；blocks_submission: false。"
- review_trigger: "organizer 答复放宽口径，或新合规源出现。"

- id: D-20261003-T3HALF-001
  date: 2026-10-03
  task: T3
  kind: score_return_and_candidate_delivery
  decision: "v0071总分与五项原样入库，NOT_PROMOTED，现役v0048保持；用户授权后续优化，生成仅强度减半的v0072，contract PASS，未提交/未评分。"
  evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-sparse-scale-score-return-20261003；reports/t3_halfstep_20261003/REPORT.md；HANDOFF.json；候选身份以INDEX为准。"
  finding: "方向收益被DE和分布损失抵消，分差小且无重复评分；预设strength=0.5检验折中。历史test大多弱于strength1，不是本地晋级，不按本次诊断再次选参。"
  boundary: "只改变强度，母本、模型和倍率不变；目标收益未知，不将服务器端点线性插值当预测。blocks_submission:false。"
  next_action: "用户上传v0072后回填总分和五项，未回分不晋级。"

- id: D-20261003-T3HALFSCORE-001
  date: 2026-10-03
  task: T3
  kind: server_score_return
  decision: "v0072用户总分及五项原样登记，REJECT，现役v0048不变；关闭当前半步响应试验，不继续细分倍率。"
  evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-half-scale-score-return-20261003；reports/t3_halfstep_20261003/SCORE_REVIEW.md；SCORE_DECOMPOSITION.json。"
  finding: "半步对分布项的小幅改善未抵消DE/方向损失；目标分数不随已测强度单调变化，来源代理不能代替服务器验证。"
  boundary: "无重复评分，不主张显著差异或生物机制；blocks_submission:false。"
  next_action: "保留现役与已评分记录；后续需新响应依据或模型结构证据，不自动新建候选。"

### D-20261003-T3DIR6CLOSE-001 — 方向六阶段二挂门，升级关闭（预声明执行）
- scope: T3-DIR6 GEARS vs 双 bar（同折同中心化 macro MSE）
- decision: "mse_neural 0.05747 双低于 no-change 0.05545 与 ridge 0.05729，按冻结 STOP：不升级图模型，方向六关闭。26 扰动集上，线性与图模型皆不能胜过预测零响应——响应本身在该表示下不可学。GSE261783 放行集保留作他用，不删除。"
- evidence: "`artifacts/t3_dir6/T3-DIR6-20261002-v1/stage2/RESULT.json`（5 折明细；bar_check 1e-6 通过；cos 已修正）；阶段一 RESULT.json（ridge 5 折全败）。"
- boundary: "比较轮未建候选，INDEX/submissions 零改动；blocks_submission: false。"
- review_trigger: "无（关闭）；新 source 或新表示需新 lane 立项。"

- id: D-20261003-T2H10SCORE-001
  date: 2026-10-03
  task: T2
  kind: server_score_return
  decision: "v0030 51.12 PROMOTED 新外推 board best（+0.59 vs 基线；+0.48 vs 50.64），selection 由 baseline v0001 切到 v0030；v0031 49.91 REJECT（−0.62），crosswalk 轴关闭不调阈。"
  evidence: "reports/SERVER_SCORE_REGISTRY.md#t2-holdout10-xr3xr4-score-return-20261003；reports/SERVER_SUBMETRIC_REGISTRY.tsv（16 行）；INDEX 两行 scored；reports/t2_holdout10_score_review_20261003/REPORT.md。"
  finding: "library 守恒解开 DE 通道（de 52.0 全榜第二）；dev–server 方向一致但刻度差远（dev −7% vs 服务器 +1.2%），dev 达标≠服务器晋级；v0031 的 mmd 44.3 说明覆盖扩张方向错。"
  boundary: "推导 T2=58.79/合计 160.27 均为推导值，门户确认合计仍 156.06；无重复评分，不作机制因果声明；blocks_submission:false。"
  next_action: "更新 STATUS/TODO/T2_TRACKING 选择；门户 Total 重读后确认；外推下一步需新冻结。"

- id: D-20261003-T2H10X567SCORE-001
  date: 2026-10-03
  task: T2
  kind: server_score_return
  decision: "v0032 51.14 TIE 不晋级（+0.02 vs v0030 51.12，±0.1 带内；记数值最高平局备份）；v0033 50.89 REJECT（−0.23）；v0034 51.02 TIE 不晋级（−0.10 带边缘）；现役 v0030=51.12 不变，T2 待分清零。"
  evidence: "reports/SERVER_SCORE_REGISTRY.md#t2-holdout10-x567-score-return-20261003；submetric 24 行；INDEX 三行 scored；verdicts 三行；reports/t2_holdout10_score_review_20261003/REPORT.md。"
  finding: "服务器 de 随剂量单调（0.5→50.8 / 自适应0.73→51.6 / 0.9→52.0），dev 剂量括号（最优 0.9）在服务器复现，剂量轴以双端一致关闭；同族三 lane dev↔服务器排序完全复现（Spearman 1.0）——dev 失灵是 Route C 族特异现象，同族内 dev 是可靠排序器；v0033 的 dev '方向票最纯' 读数未兑现（服务器 de 50.8）。"
  boundary: "推导 T2=58.79/合计 160.27 不变（推导值，门户确认仍 156.06）；无重复评分不作显著性声明；blocks_submission:false。"
  next_action: "外推 recipe 家族在 ~51.1 进入平台期；下一波要么行集合/几何级新机制（需新冻结授权），要么封存。dev 留阶段 10% 目标仍未达成（0.91944 vs 0.90），reserve 仍 NOT_RUN。"

### D-20261003-T1EXTPRE-001 — T1 外部预训练 G-return 挂门，lane 关闭
- scope: T1-EXTPRE-20261003-v1 步骤 B（ExtendedMouseAtlas 8 档合规子集预训练 → 官方 E8.5→E9.5 回报门）
- decision: "G-return 双门挂即关闭：de 0.0189 / dir 0.1412，远低于 0.8868/0.8895；不建 v0052，不上传。外部时序均值位移算子迁到官方面板后摧毁分布，不构成对 v0051=53.92 的挑战。"
- evidence: "`artifacts/t1_extpretrain/T1-EXTPRE-20261003-v1/RESULT_B.json`（verdict STOP_gate1；n_G 25824；pca_explained 0.264；wall 562s）。"
- boundary: "未建候选，INDEX/submissions 零改动；atlas 新用途仅限本 lane 且已关闭；blocks_submission: false。"
- review_trigger: "无（关闭）；换表示或换迁移头需新 lane。"

### D-20261003-T1MIX2SCORE-001 — T1 AR-MIX2 五 lane 回分：v0054 53.98 落 ±0.1 TIE 带不晋级，v0051=53.92 留任
- scope: AR-T1-MIX2-20261003-v1（5 lane winner-pair 整行混合：50/50 v0035×v0038 双种子、50/50 v0036×v0038、三等分 v0035/36/38、30/70 v0035×v0038；contract parent 全 v0035；zip deliveries/art1mix2__t1__upload__20261003.zip sha e8b60cd8…）
- decision: "服务器 v0054=53.98（+0.06 vs v0051=53.92）落 ±0.1 TIE 带 → 不晋级、tie 归现任，v0051 留任 T1 selection，v0054 记 tied numeric-high backup（D-20260917-G0T1-001 口径）；v0052=53.67（−0.25）/v0056=53.76（−0.16）超双父版本（53.43/53.55）记 scored backup；v0053=53.36（−0.56，低于双父）REJECT、v0055=53.48（−0.44，超 v0035/v0036 父、低于 v0038 父）记 marginal scored backup。derived sum 不变 160.44（换 v0054 计为 160.50，仅推导；portal 确认 Total 仍 156.06）。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t1-ar-mix2-score-return-20261003；reports/SERVER_SUBMETRIC_REGISTRY.tsv +20 行；reports/LANE_VERDICTS.tsv +5 行；artifacts/autoresearch/t1-20261003-v1/FINAL_BUILD_v2.json；用户转录分数（submission ID/时间戳未提供）。"
- knowledge: "(1) 种子彩票第三次复现：同设计 v0052 vs v0053 Δ0.31（首报 Δ0.40）→ T1 混合类服务器行运气 ±0.3-0.4，大于 TIE 带；后续 lane 须发 2 种子或确定性构造，单次读数是彩票。(2) 受控配对比较（同权重同种子）：36×38 比 35×38 高 +0.31，36 系配对第三次领先（53.92→53.98）。(3) 35×38 权重轴死：f0.3/0.5/0.7 全在行运气内。(4) 三池混合是稀释不是叠加（53.48 低于两个组分 53.67/53.98），该轴关闭。(5) 混合族八 lane 饱和于 53.32–53.98（均值≈53.7），下一个真动作需要新机制族而非更多 winner-pair 算术。"
- boundary: "版本 v0052–v0056 为 PROPOSED，INDEX 行与 canonical 落位待 coordinator（2026-10-02 批 v0049–v0051 的 INDEX 行、子项行与 LANE_VERDICTS 行亦仍欠，一并请 coordinator 补）。v0052 编号曾被已关闭 T1-EXTPRE（D-20261003-T1EXTPRE-001）以「不建 v0052」形式引用、无产物，本批 v0052 为 mix3538even（sha 7a6be221…），无产物冲突，身份以 SHA256 为准。blocks_submission: false；target_used=false；未晋级不作模型进步声明。"
- review_trigger: "portal Total 刷新（仍记 156.06）；或用户决定按惯例不换 tied backup 之外的选集；混合族若再出一轮无超出 ±0.1 的结果则整族转为维持模式。"

### D-20261005-STRUCT-001 — 结构整理：删已评分上传包，不搬被引用的目录
- date: 2026-10-05
- scope: navigation only; no candidate, no score, no science claim
- decision: "已评分且 SHA 对上 INDEX、正本仍在 submissions/candidates 的 deliveries 包和散落 h5ad 删除（75 个文件，约 9.45 GB），记录在 reports/DELETION_MANIFEST.tsv。reports/、submissions/、docs/batch3 不搬动：路径被脚本和决策引用，搬走会增加断链。新入口是 docs/00_START_HERE.md、docs/ATOM_MAP.md、reports/README.md 和三份 SYNTHESIS。outputs/ 保留并写明它只是早期冒烟。submissions 不与 artifacts 或 deliveries 合并。"
- evidence: "deliveries/README.md；reports/DELETION_MANIFEST.tsv 2026-10-05 行；INDEX 回填 T3 v0026=46.93、v0027=46.95、v0030=46.6、v0031=46.12、v0032=46.95、v0033=46.95（数字已在 reports/SERVER_SCORE_REGISTRY.md，此前 server_score 单元格空白）。"
- boundary: "未改任何已评分 h5ad，未改选集。历史文档里的 zip 链接会失效，身份仍以 INDEX SHA 为准。VOID 包和 t2holdout inspect 包保留。blocks_submission: false。"
- review_trigger: "若有脚本在运行时必须读取已删 zip，而不是 receipt 或 canonical h5ad，再从 candidates 按短名规则重打，不要恢复成第二份身份库。"

### D-20261006-T3SIX-001 — T3: 六新路线一次性实现并源侧 LOPO 选择
- date: 2026-10-06
- scope: T3:gata4 candidate generation; no server submission
- decision: "按既有冻结源侧协议实现 6 条新路线的 operator 与选择：O1 结合 v0070 加性残差 × v0071 乘法；O2 以 v0048 Hurdle 概率门控 v0071 乘法发射；O3 按跨扰动离散度收缩 v0071 beta；N1 WT 共表达程序 NMF 消融；N2 WT marker 谱系门 × 源模型发射；N3 源侧双向开关/零膨胀发射。选中 sm0.25_sa0.5 / s0.5 / k2.0 / s0.25 / s2.0 / s0.5，交付 v0075–v0080，contract PASS，score_pending。abort重试产生的 v0073/v0074 O1 副本标记 invalidated_unsubmitted。"
- evidence: "reports/t3_six_routes_20261006/REPORT.md、DESIGN.md、各 route 的 SELECTION.json/EVALUATION_COMPLETE.json/FULL_MATRIX_METRICS.tsv；scripts/t3_six/{evaluate,deliver}.py；v0075–v0080 submissions/candidates/T3_gata4/。"
- boundary: "源侧 LOPO 不等于服务器分；候选未评分不晋级。O2 源选择用密度 proxy 门，交付用 Hurdle probability；N3 的 交付开关率取自最 GO 相似供体条件（Gata4 不在来源条件表），记录在 reports/t3_six_routes_20261006/n3_donor.json。blocks_submission:false。"
- review_trigger: "任一候选回分；若回分显示分布/DE 失衡，优先审视 O2 的源-胚胎门不等价与 N3 供体开关率的失配。"

### D-20261007-T3SIXSCORE-001 — T3 六新路线回分：无一晋级，v0078 同分现役留下
- date: 2026-10-07
- scope: T3:gata4 score registration; incumbent unchanged
- decision: "六新路线候选一次回分原样登记：v0075=46.73、v0076=47.31、v0077=47.43、v0078=47.93、v0079=47.40、v0080=46.82。对照现役 v0048=47.93：v0078（N1 NMF 程序消融）同分，按 ±0.1 平局带规则现役留下；其余 5 个 NOT_PROMOTED。六条源侧变换路线（加性×乘法、hurdle 概率门、可靠性收缩、NMF 消融、marker 门、开关发射）全部关闭，不再扫参数；INDEX score_pending 清零。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-six-score-return-20261007（用户原文五分项）；SERVER_SUBMETRIC_REGISTRY.tsv 2026-10-07 行（30 行）；INDEX.tsv v0075–v0080 已填 server_score=scored。"
- boundary: "v0078 同分不构成晋级或 NMF 机制优势证据；单次评分无重复性。O2 源-胚胎门不等价与 N3 供体开关率失配仍未被服务器数据单独检验。blocks_submission:false。"
- review_trigger: "若后续要重开 T3 机制线，需换信息：合规且覆盖更好的扰动监督、与胚胎状态对得上的背景，或来源侧最终矩阵确实获益的迁移；不得据此回分重扫 transform 参数。"

### D-20261007-T3SIX2-001 — T3 第二波六新路线：5 交付 + n3_pswap 源侧关闭
- date: 2026-10-07
- scope: T3:gata4 candidate generation; no server submission
- decision: "第二波 6 条路线：O1 现役⊕v0078 NMF 等权平均、O2 hurdle 概率门×NMF 消融、O3 门×收缩×乘法（参数沿用第一波冻结值，不重扫）；N1 分位数形状迁移（选中 q0.25）、N2 供体符号一致性门（选中 g0.5）、N3 程序置换/质量再分配（identity 秩最优、三强度单调更差，源侧关闭不交付）。交付 v0081–v0085，contract PASS，score_pending。"
- evidence: "reports/t3_six_routes_20261007/REPORT.md、DESIGN.md、各 route 的 SELECTION.json/EVALUATION_COMPLETE.json/FULL_MATRIX_METRICS.tsv、n3_pswap/SOURCE_CLOSED.json；scripts/t3_six2/{evaluate,deliver,package}.py；deliveries/t3six2__t3__upload__20261007.zip。"
- boundary: "源侧 LOPO 不等于服务器分；候选未评分不晋级。O1 源侧诊断的现役类似物是加性发射（hurdle 不可迁移），非等价声明。N1/N2 供体为 GO argmax（donor.json）。blocks_submission:false。"
- review_trigger: "任一候选回分；若回分仍低于 48.03 门槛，第二波全部关闭，不再扫 transform 参数。"

## D-20261007-T1SIX-001 — T1 六路线批次：设计、运行前修订与交付

- date: 2026-10-07
- scope: T1
- type: route_batch_delivery
- decision: "用户 /goal 授权 3 条既有路线优化/结合＋3 条全新路线；两项裁决：混合只作载体须带新组件（不重复 v0049–v0056 已试配比）、全新路线本轮检索优先（2026-09-21 T1-NEXT 草案核实为已执行并关闭，未采用）。运行前修订：POT ot.emd 精确 LP 替代发散且过慢的 numpy Sinkhorn（原冻结 ε=0.05 在原始平方距离尺度溢出）；ocovstab 可靠性距离改 per-scope 来源（report 10 类型中位 0.9491/final 11 类型中位 0.9498，NCC 仅在 final 侧）；ostabmix 无冻结比例的阶段特有类型保留原骨架 identity 行；环境修复（用户级 h5py 3.16.0+xarray 2026.9.0 修 numpy-2.4.6 ABI 链，anndata+scorer 导入验证）。交付 v0057–v0062（osoftcov/ostabmix/nconf/nbidir/ocovstab/nwasser），contract PASS，score_pending。"
- evidence: "reports/t1_six_20261007/REPORT.md、VALIDATION.json、METRICS.json；configs/t1_six/design_20261007.json（修订内嵌）；reports/T1_SIX_DESIGN_20261007.md；tests/t1_six/test_ops.py 13 测试；artifacts/t1_six/T1-SIX-20261007-v1/（CACHE_LOCK 37 项、MODEL_REPLAY PASS×6、BATCH_RESULT_v4_partial.json 审计线索）；deliveries/t1six__t1__upload__20261007.zip（sha 22e99637f39afc2e…，READY_NOT_SUBMITTED）。"
- boundary: "本地五项只作提交优先信号，不晋级现役；v0051=53.92 保持，服务器对照在用户回填前 pending。父版本 v0035 字节级复现（跨版本 SVD 漂移 3.4e-05 未翻转 donor）；环境修复后参照重评与旧环境数值一致。blocks_submission:false。"
- review_trigger: "任一候选回分；若 ostabmix 回分不低于现役带则考虑 per-type 自适应比例进入下一轮组合；软 donor 重选家族（ocovstab/osoftcov/nconf/nwasser）若服务器也无意外即关闭。"

## D-20261007-T2GEOM-001 — T2 几何新机制冻结：RMS 锁定的各向异性插值

- date: 2026-10-07
- scope: T2 heart interpolation，胚胎插值仅同代码复现读
- type: design_freeze
- decision: "用户选几何新机制。第一刀只改坐标形状：在现役自己的 PCA 轴上把各向异性谱拉到两个训练括号的日历中点，再把 RMS 锁回现役。不改表达、不做整体缩放、不做 FGW、不建候选。"
- evidence: "reports/T2_GEOM_ANISO_FREEZE_20261007.md；scripts/t2_geom_aniso_diag.py。心脏插值现役 v0019 occupancy 47.8 / d2 65.4 / scale 97.9；尺度×0.9、加性空间对比度、FGW 均已关闭。"
- boundary: "只覆盖椭球各向异性，不覆盖叶/管/空洞。对括号的 dice 不是服务器技能。CONTINUE 也不授权本回合建候选。不读 E7.5/E8.5/E10.5。心脏外推不在本刀。blocks_submission:false。"
- review_trigger: "诊断按冻结判 STOP，或另行冻结一个能动高阶支撑的几何机制。不得用本次数字改 t 或升级非线性形变。"

## D-20261007-T2GEOM-002 — 各向异性诊断：心脏源侧继续，胚胎线性族关闭

- date: 2026-10-07
- scope: T2 interpolation geometry
- type: diagnostic_verdict
- decision: "按冻结判 HEART_ONLY_CONTINUE。心脏插值线性各向异性未被源侧代理否定；胚胎谱差 0.030 < 0.05，INSUFFICIENT_ANISOTROPY，关闭该板的线性族。不建候选，不改现役。"
- evidence: "artifacts/t2_geom_aniso_20261007-v1/RESULT.md 与 result.json。心脏 dice 0.7541→0.7689、0.7403→0.7589，d2 0.03854→0.03825、0.07761→0.07839（晚括号略差，仍在 1.10 内）。v0019 与 v0013 坐标一致。胚胎括号谱差 0.0300。实现锁通过：RMS、恒等形变、×0.9 再锁回均未漏进形状。"
- boundary: "对训练括号的 dice 不是服务器 occupancy。幅度约 0.015，远小于官方 oracle 几何把 heart interp occupancy 从 0.7704 抬到 0.8223 的缺口。不得把 HEART_ONLY_CONTINUE 写成通用几何定律，不得用这次数字改 t 或升级非线性。blocks_submission:false。"
- review_trigger: "若要消耗提交名额，须另写候选冻结：只改 v0019 坐标、表达字节不变、不调 t。否则本族停在诊断。"

## D-20261007-T2GEOM4-001 — 三个新几何预算，四件可提交包

- date: 2026-10-07
- scope: T2
- type: candidate_delivery
- decision: "用户再给 3 个新路线预算，并要一份 4 件 h5ad 包。交付 v0023 主轴中点、v0024 心脏分位数搬运、v0035 外推生长、v0018 胚胎分位数搬运。四件 contract PASS，score_pending，未上传。现役不变。"
- evidence: "reports/T2_GEOM4_FREEZE_20261007.md；reports/t2_geom4_20261007/REPORT.md；deliveries/t2geom__t2__upload__20261007.zip sha f864af3719f479ffe183297402a9e1a5fedf6bc9a0387c12b4354be8aa49a478。候选 SHA 以 submissions/INDEX.tsv 为准。"
- boundary: "v0035 的尺度比是训练曲线外推的 0.890，落在预声明护栏内，但靠近已关闭的 ×0.9。不是服务器预测。未读验证期真值。blocks_submission:false。"
- review_trigger: "四件任一件回分。无分数前不晋级，不用本地综合分补判。"

## D-20261007-T2GEOM4SCORE-001 — 几何四件回分：心脏插值换人，另外三条关闭

- date: 2026-10-07
- scope: T2
- type: server_score_return
- decision: "v0023＝62.48 晋级心脏插值现役（+0.12，超出 ±0.1）。v0024＝60.61、v0035＝49.06、v0018＝62.50 均 REJECT。分位数搬运和外推生长关闭。门户合计仍记 156.06。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t2-geom4-score-return-20261007；reports/t2_geom4_20261007/SCORE_REVIEW.md；32 行 submetrics。submission ID/时间未提供，不伪造。"
- boundary: "v0023 的表达和尺度与 v0019 逐位相同。增益全在 d2 65.4→69.5，占据 47.8→45.2 变差。晋级不表示占位孔被修好。v0035 的 0.890 倍被服务器读成尺度更差。blocks_submission:false。"
- review_trigger: "门户合计重读。不得用这次 0.12 去扫主轴比例。"

## D-20261007-T1SIXSCORE-001 — T1-SIX 六路线回分：v0058 带内 TIE 不晋级，其余五件 REJECT，现役 v0051 留任

- date: 2026-10-07
- scope: T1
- type: server_score_return
- decision: "v0057–v0062 全部登记。v0058＝53.85 落 ±0.1 平局带（−0.07 vs v0051 53.92），不换人；v0057＝49.28、v0059＝51.13、v0060＝52.07、v0061＝49.42、v0062＝51.02 均 REJECT。现役 v0051=53.92 不变，T1 待分清零。混合/结合与全新机制三件一次回分无一晋级，本波关闭。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t1-six-score-return-20261007；24 行 submetrics；reports/t1_six_20261007/REPORT.md。用户回填 portal 分数，submission ID/时间未提供，不伪造。候选 SHA 以 submissions/INDEX.tsv 为准。"
- boundary: "v0058 本地 de 冠军（0.6111，+0.0185）服务器 TIE——本地 de 信号再次未转化为服务器收益，与 T1 phase 预承诺 proxy 警告一致。v0058 的 dir 60.4（与 v0054 并列已知最高）/vario 51.2（已知最高）为板面强项，被 de −0.5/mmd −0.6 抵消；不得据此宣称 ostabmix 优于现役或重启混合族调参。blocks_submission:false。"
- review_trigger: "门户 Total 重读。不得用本波数字扫混合权重或方向权重。"

## D-20261009-NAV-001 — 导航按 2026-10-08/09 回分刷新；两处账目缺口显式记录，未擅自改写 INDEX

- date: 2026-10-09
- scope: coordination
- type: navigation_refresh
- decision: "按已登记的服务器分刷新 docs/ATOM_MAP.md、根 STATUS.md、docs/coordination/STATUS.md 与三份 TRACKING。现役改为 T1 v0092=58.89、T2 胚胎 v0021=63.0047 / 心插 v0023=62.48 / 外推 v0030=51.12（任务均分 58.87）、T3 v0088=53.69。三任务现役相加推导 171.45；门户观测仍为 171.4（2026-10-08T11:58Z，rank 61），早于 T1 与 T2 胚胎两次易主。T3 提交额度标 OPEN/UNVERIFIED。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md（#t1-late-anchor-20261009、#t2-embryo-20261009、#t3-condhurdle-v0088-score-return-20261008）；submissions/INDEX.tsv；scripts/generate_audit.py:42。"
- boundary: "两处缺口显式记录但不代为裁决：(1) 门户榜单 per-task 显示 T1 58.0 / T2 59.7 与现役和 58.89 / 58.87 不符，仅 T3 53.7 与 53.69 吻合，门户 per-task 聚合口径未确立，不得假设等于 board 均值；(2) AUDIT.md 数值最高因只统计 score_status=scored 而低于现役，66 行使用 registered（含 v0092/v0093/v0021，均有真实服务器分），属字段不一致而非分数缺失——未改写 INDEX，服务器分数一律以 SERVER_SCORE_REGISTRY.md 为准。T3 2026-10-09 无提交记录，不等于额度可用。"
- review_trigger: "门户 Total 重读并完成 per-task 对账；coordinator 裁决 score_status 字段是否统一；T3 提交前需用户重新授权。"

## D-20261008-T3BACKLOG-001 — T3 v0081–v0085 回分：v0084=49.55 晋级，同 ID 重建件不追认历史字节

- date: 2026-10-08
- scope: T3
- type: server_score_return
- decision: "v0081=47.92、v0082=47.94 落在旧现役 v0048 的平局带内，不晋级；v0083=47.51、v0085=47.45 REJECT；v0084 q0.25 重建修订=49.55 晋级（+1.62 vs v0048 47.93，超出 +0.03 阈值）。v0083–v0085 明确标注为同 ID 重建修订，不是原始字节恢复；重建件的表达式数组哈希精确，序列化 H5AD 字节不同，不追认历史原始件得分。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-backlog-score-return-20261008；reports/t3_backlog_20261008/RECONSTRUCTION_RECEIPT.json。门户未暴露 artifact 哈希，v0081/v0082 的历史 INDEX SHA 未获独立二进制核验。"
- boundary: "同 ID 重建不追认不可得的原始字节；重建数组哈希精确但容器字节不同，不得声称与原始件字节一致。blocks_submission:false。"
- review_trigger: "无。后续 v0087/v0088 已超越该水位。"

## D-20261008-T3ARANK-001 — T3 v0086 arank r2 = 49.34 REJECT，源侧改善未转化

- date: 2026-10-08
- scope: T3
- type: server_score_return
- decision: "v0086 arank 修订 2 = 49.34，低于现役 v0084 49.55（−0.21），不跨 ±0.1 平局带，不晋级，现役不变。仅提交修订 2；更早的预提交草稿与未使用的临时版本号未登记为候选，也不计入提交次数。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-arank-v0086-score-return-20261008。方法：域锚定响应秩搬运，池化对照源域范围校正，按胚胎正秩索引的等权样本匹配正分位数变化，父版本 v0084。"
- boundary: "源侧代理改善未转化为该配置的胚胎榜收益。此负结果不建立因果机制，也不否定所有域迁移方法。源侧证据是历史且自适应复用的，不是独立验证集。blocks_submission:false。"
- review_trigger: "无。配置级负结果已登记关闭。"

## D-20261008-T3EMBHURDLE-001 — T3 v0087 七 KO 通用胚胎状态响应 hurdle v2 = 53.42 晋级

- date: 2026-10-08
- scope: T3
- type: server_score_return
- decision: "v0087 embhurdle_v2 = 53.42，较 v0084 49.55 高 3.87，超出平局带，晋级。现役切到 v0087，v0084 保留为历史回退。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-embhurdle-v0087-score-return-20261008。方法：七 KO 通用胚胎状态响应 + 组成重采样 + 分离检测比例/正分位数 hurdle v2 发射。源条件为 GSE137337 的 E8.5 Dnmt1/Dnmt3a/Dnmt3b/Ehmt2(G9a)/Kdm2b/Kmt2a/Kmt2b，GSE122187 E8.5 WT 与本体信息，替换此前成体成纤维细胞响应源。"
- boundary: "相对 v0084 方向 48.4→51.2、severity 50.0→75.0 上升，但 DE 47.1→41.7、MMD 54.8→49.7、variogram 53.4→42.3 下降——这是带分布/DE 权衡的总分提升，不是各指标一致改善。这是通用发育扰动先验，不是 Gata4 特异因果机制的证据。WT-only 状态、性别匹配对照与等胚胎加权不能消除队列、化药、性别与发育背景混杂；发育过程是自适应的，不是独立确认。"
- review_trigger: "无。已被 v0088 超越。"

## D-20261008-T3CONDHURDLE-001 — T3 v0088 conditional hurdle = 53.69 晋级为现役

- date: 2026-10-08
- scope: T3
- type: server_score_return
- decision: "v0088 condhurdle = 53.69，较 v0087 高 0.27，超出 ±0.1 现役带，晋级为 T3 现役。v0087 保留为历史回退。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t3-condhurdle-v0088-score-return-20261008。方法边界：与 v0087 同一七 KO 通用胚胎状态响应 hurdle，把随机零激活 tie 换成 WT-only 状态条件化激活倾向。该臂由冻结四族源侧对比选出，本记录不含门户后调参。源仍为已准入的 GSE137337 胚胎 KO 条件与 GSE122187 WT 及本体信息，无新增源范围或隐藏目标结果。"
- boundary: "五项子项为门户显示的 SKILL 值，非原始指标；原始值未暴露也不推断。相对 v0087，DE/方向在显示精度上未变，severity +0.2、MMD +1.4、variogram +0.8——改善集中在分布/发射行为，不建立新的目标特异因果响应，也不意味着未变的舍入子项在数值上相同。该次提交消耗了用户单独授权的最后一次尝试预算，门户显示当日 T3 用量 8/8。blocks_submission:false。"
- review_trigger: "门户 2026-10-08T11:58Z 观测 Total 171.4、rank 61、T1 58.0/T2 59.7/T3 53.7。2026-10-09 T3 无提交，当日额度是否重置未观测，需用户确认。"

## D-20261009-T1LATEANCHOR-001 — T1 late-anchor/OT 五 lane 回分：v0092=58.89 晋级为新 board best

- date: 2026-10-09
- scope: T1
- type: server_score_return
- decision: "v0089 late_anchor_x1=53.14、v0090 late_anchor_x2_comphalf=53.43、v0093 v51_anchor_pergroup=58.22 均低于现役；v0091 v51_anchor_auto=57.99 先晋级后被取代；v0092 ot_gen_v51=58.89 晋级为 T1 现役（+0.90 vs v0091）。T1 现役由 v0051=53.92 改为 v0092=58.89，备份为 v0093 与 v0091。T1 待分清零。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t1-late-anchor-20261009；reports/t1_late_anchor_20261008/。证据类别为门户已读回分。"
- boundary: "v0089–v0093 为晚外部锚（GSE230531 E8.5/E14.5/E16.5 按样本文件）与 OT 生成式位移路线。混合族（~53.7）与 late-anchor 直用轴均已过平台。误用草稿号 v0063–v0067 已退役（与 T3:gata4 冲突），正式编号 v0089–v0093，SHA-256 未变。本条为导航刷新时依据 registry 事实补写的决策条目。"
- review_trigger: "门户 Total 与 per-task 口径需按现役重读。"

## D-20261009-T2EMBRYO-SUPPORT-001 — T2 胚胎 v0021 scRNA copula = 63.0047 晋级（服务器高精度）

- date: 2026-10-09
- scope: T2
- type: server_score_return
- decision: "v0019 e3_state_bures=62.33、v0020 e3_supportmix=61.39、v0022 copula_geocouple=62.65 全部 REJECT；v0021 e3_scrna_copula=63.0047 晋级，胚胎现役由 v0014=62.8930 改为 v0021。T2 任务均分由 58.83 改为 58.87=(63.0047+62.48+51.12)/3。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t2-embryo-20261009 与 #v0021-scrna-copula-return。官方公开 API 于 2026-10-09 07:51:48–51 UTC 解析出 v0021 总分 63.0047、前任 v0014 62.8930，Δ+0.1117，超出 0.1 晋级阈值。这是本项目目前唯一以服务器高精度做出平局带外裁决的晋级。"
- boundary: "E3 supportmix、state-Bures 配对、geo-coupling 三轴关闭。心插现役 v0023=62.48、外推 v0030=51.12 不变。外推 existing-route 预算 2/2 已用尽。blocks_submission:false。"
- review_trigger: "门户 per-task 显示 59.7 与 58.87 不符，口径待核对。"

## D-20261009-T2EMBRYO-CLOSE-003 — T2 胚胎 campaign 收口

- date: 2026-10-09
- scope: T2
- type: lane_close
- decision: "T2-EMBRYO-20261009 四实验 campaign 以 v0021 晋级、v0022 REJECT 收口；external slots 与既有路线预算分离记录，不因本次收口而扩大。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#v0022-geo-coupling-return-and-campaign-close；reports/t2_embryo_campaign_20261009/V0022_HANDOFF.json。"
- boundary: "本条为导航刷新时依据 registry 事实补写的决策条目，不改写任何已有分数或候选身份。"
- review_trigger: "无。"

## D-20261009-T3REBUILD-001 — T3 v0088 本地完整复现；发射器成分轴判定饱和，不建议提交变体

- date: 2026-10-09
- scope: T3
- type: local_reconstruction_and_route_gate
- decision: "从 research/t3_20261008 公开代码完整重建 v0088：GEO 源 12/12 哈希通过、8/8 注释 TSV 逐字节、GO embedding 重建逐字节、8 个归一化面板 frozen_merge_matches、模型拟合 REBUILT_EXPRESSION_EXACT，v0087/v0088 表达式哈希与三个推理产物全部逐位复现；基线复合分与归档 summary 最大绝对差 0.0。据此 PUBLIC_REBUILD_FOLLOWUP.md 的『完整拟合未验证』限制可撤销。发射器成分轴 14 次单轴迭代判定饱和：最好 propensity_penalty=0.2 仅 +0.0034 且不单调，de_skill 全变体变化恰为 0，三个轴精确 no-op，检测比例轴曲率极陡。不建议提交任何变体；服务器现役 v0088 不变。"
- evidence: "reports/t3_rebuild_20261009/REPORT.md；autoresearch/loop-261009-1450/loop/results.tsv 与 handoff.json；rebuilt_model/REBUILD_MANIFEST.json 状态 REBUILT_EXPRESSION_EXACT。"
- boundary: "本地源侧指标不是服务器预测：v0086 源侧改善而服务器 49.34 低于 v0084，T1 v0058、T2 v0035 同样本地好而服务器不涨。发射器只重分配已激活细胞给谁，不能改变 DE 集合，故 DE 端在发射器层面结构不可动；DE 短板若要动须改响应结构，那等于开新路线而非成分迭代。T3 提交额度 OPEN：registry 记 2026-10-08 用尽当日 8/8 并声明无剩余授权，2026-10-09 T3 无提交记录，当日额度是否重置未观测，不宣称可用。blocks_submission:false。"
- review_trigger: "下一手需服务器分仲裁（须用户重新授权）或改响应结构开新路线；GO 重建复现结论可据此更新 PUBLIC_REBUILD_FOLLOWUP.md 的限制条目。"

## D-20261009-PORTALTOTAL-001 — 门户合计 172.9 确认，per-task 对账关闭

- date: 2026-10-09
- scope: coordination
- type: leaderboard_reconciliation
- decision: "采纳用户确认的门户读数：Total **172.9**，per-task T1 58.9 / T2 60.3 / T3 53.7；registry 记 Human rank 71/187 @ 2026-10-09T09:23:59Z。现役相加 58.89 + 60.2770 + 53.69 = **172.857**，与门户合计在显示精度内一致，全部导航改用该基准。D-20261009-NAV-001 中标记为 UNRESOLVED 的 per-task 对账在此关闭。"
- evidence: "用户 2026-10-09 转录；reports/SERVER_SCORE_REGISTRY.md#t2-operator-transfers-2026-10-09（official best-per-board mean 60.2879）；submissions/INDEX.tsv。"
- boundary: "门户 T2 的 per-task 值用的是各榜**数值最高**（embryo v0023 63.0185 + heart_interp v0025 66.7064 + extrap 51.1388）/3 = 60.2879，而项目选集按 ±0.1 带内保留现任（embryo v0021、外推 v0030），选集均值 60.2770；两者 0.011 的差额完全来自这两处带内保留，显示精度下同为 60.3。据此不得把门户 per-task 直接当作现役和，也不得据此宣称项目选集更优。另：`AUDIT.md` 因 score_status 字段不一致低估数值最高的问题仍未裁决，不属本决策范围。"
- review_trigger: "任一现役变动后须重新确认门户 Total 与 per-task；协调 score_status 字段。"

## D-20261009-T2OPTRANSFER-001 — T2 算子迁移三件：心插 v0025 晋级并易主，胚胎 v0023 带内不换人，外推 v0037 REJECT

- date: 2026-10-09
- scope: T2
- type: server_score_return
- decision: "心插 v0025 h_heart_copula = 66.7064（官方 API 精度；UI 66.71）晋级，心插现役由 v0023 = 62.48 换为 v0025，跃升 +4.23，为本轮最大单榜变化。胚胎 v0023 = 63.0185 为数值最高但与现任 v0021 = 63.0047 仅差 0.0138，按 ±0.1 带内不换人规则保留 v0021。外推 v0037 零保位移 = 48.86（UI），低于现役 v0030 = 51.12，REJECT。现役 = 胚胎 v0021 / 心插 v0025 / 外推 v0030，T2 任务均分 60.277。"
- evidence: "reports/SERVER_SCORE_REGISTRY.md#t2-operator-transfers-2026-10-09（embryo v0023 submission 866a8e68fecd4c89baacbef1e73dcd35 09:16 UTC；heart_interp v0025 submission 84e1cb88cbdd4dd8861488783a1002b9 09:20 UTC；extra v0037 submission 01f2cb4b59794d63ac27dd0d84962cff 09:22 UTC）；reports/t2_operator_transfers_20261009/ 各 SCORE_RETURN 与 HANDOFF。"
- boundary: "心插 v0025 的 +1.6804 是相对字节精确 H1 父件 65.0260，不是相对旧现役 v0023 62.48；引用增益时必须写清比较基线。外推 v0037 是配置级负结果，不否定零结构保持这一思路在其他形变下的适用性。三件分数精度不同（心插与胚胎有官方 API 高精度，外推仅 UI 两位），跨板比较时不得混用精度。当日 T2 用量记为 7/8，剩余 1 次未授权。blocks_submission:false。"
- review_trigger: "T2 优先沿 scRNA copula 族继续（心插已验证 +4.23）；外推停在 51.12 平台期需新机制而非再调同一形变的比例；任何新提交前须取得用户授权。"

## D-20261009-T3RESPLAM-001 — T3 v0089 响应结构路线：本地 +0.1985，交付但未提交

- date: 2026-10-09
- scope: T3
- type: candidate_generation
- decision: "新建候选 T3:gata4 v0089 `resplam15unmask`，父 v0088。method/mode 沿用冻结源侧选择 mean_combined，seed 20260904、atlas、状态划分、发射器与几何全部冻结；**唯一结构改动是响应**——收缩 lam 由 nk/(nk+50) 改为 nk/(nk+15)，并去掉 global_valid 基因掩码。E8.75 WT 载体 7449×500，contract 全 PASS。交付包 deliveries/t3lam15__t3__upload__20261009.zip，成员名即 portal Model 名，SHA 对 INDEX 核验通过。score_pending，未提交/未评分。服务器现役 v0088=53.69 不变。"
- evidence: "autoresearch/loop-261009-1845（30 次迭代台账、handoff.json、8 个脚本、33 份路线结果）；reports/t3_rebuild_20261009/REPORT.md；submissions/candidates/T3_gata4/v0089_resplam15unmask/RECEIPT.json；本地复合 74.936110 vs 74.737588（+0.1985，赢 4/7，冻结门 PASS）。响应重实现保真度 PASS：delta/composition/support 相对原缓存 maxabs 0.0。"
- boundary: "本地源侧复合分**不是服务器预测**：v0086 源侧改善而服务器 49.34 低于 v0084，T1 v0058、T2 v0035 同类。本候选增益不均匀（Ehmt2 +1.0、Kmt2b +0.87、Kmt2a +0.59 对 Dnmt1 −0.855）。**T3 提交额度未解决**：registry 记 2026-10-08 用尽当日 8/8 并声明无剩余授权，2026-10-09 T3 无提交记录，当日计数器是否重置未观测；上传需用户明确重新授权。联合秩传输新架构为干净负结果（−12.07，对照组不变）。blocks_submission:false。"
- review_trigger: "用户授权 T3 提交额度后方可上传；服务器回分后按 ±0.1 带内保留规则裁决是否晋级 v0089。"
