# T3 任务追踪：gene perturbation

更新时间：2026-09-29

分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。本文件明确区分已评分路线和待验证路线。

## 当前状态（2026-09-29）

- selection 是 v0048，服务器 47.93。
- 修复 v0037、v0040、v0041 已回分，分别是 46.98、47.08、47.09，都不晋级。修复队列关闭。
- v0049–v0053 未提交、未评分。优先仲裁 v0049。科学结论仍不确定，`blocks_submission: false`。
- 决策 `D-20260928-T3REPAIR2-001`。给人读的教训见根目录 `REVIEW.md`。

## 历史状态（2026-09-21）

- 当时六个修复候选还没回分。后来都已评分，不作为当前待办。
- 新上传包 `deliveries/r634fix__t3__upload__20260921.zip`；父版本均v0009。R1叠加R6为NO_OP；R5扩链未执行。证据 `reports/t3_repairs_20260921/REPORT.md`。

## 历史状态（2026-09-04）

- 当前最高服务器分数：**45.5**（v0006 / v0007 并列，2026-09-04 回填；derived Total≈149.7 待服务器页面确认）
- 当前最佳：`B2-T3-A1` `v0006_b2_t3_a1_l1` 与 `v0007_b2_t3_a1_l2`，并列 board best；原 baseline `wt_identity` 45.3 为历史 best
- 当前状态：`closed_as_research_component`（2026-09-02 收口，见 `artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md`）；S1A v7、S1B v3、S1C-A/v1、S1C-B/v3、S1D/v3 均为可审计组件，所有历史 artifact 与失败 receipt 不可变，候选生成仍关闭
- 任务阻塞：`T3-S1A-GATE-001`；缺口为公开证据边界（E8.75 state-matched signed family 不存在且近窗口数据属 target leakage），非工程问题；最小解锁条件见收口报告第 3 节，`blocks_submission: false`。**leaderboard +0.2 不解除科学 gate**：服务器分数不作机制/因果证据

## 历史 Top 3 路线（2026-09-04）

旧的两条 shift-transfer 候选已评分且低于 best；B1-A2 两条最终候选已评分且均低于 best，进入失败诊断 hold。

| 位次 | 路线 | 通俗说明 | 服务器分数 | 状态 |
|---|---|---|---:|---|
| 1 | `B2-T3-A1 L1_STRICT_WT_DIRECT` (v0006) | Gata4 自身+49 个 ChIP 直接下游基因的 WT-only 严格 residual | **45.5** | 已评分，并列当前 best |
| 1 | `B2-T3-A1 L2_GATA4_GATA6_CONDITION_AWARE` (v0007) | 加 Gata6 half-dose 条件的 73 下游基因 residual | **45.5** | 已评分，并列当前 best |
| 3 | `wt_identity` | 直接把 matched WT 当作 Gata4 KO 预测，先建立扰动 floor | **45.3** | 已评分，历史 best（被并列超越 0.2） |

历史对照：`shift_transfer_norm` v0002 为 45.2（低于 best 0.1），`shift_transfer_shrunk` v0003 为 43.8（低于 best 1.5），均已淘汰；B1-A2 `L1_CELL_LEVEL_SPEARMAN` v0004 为 44.7（−0.6）与 `L2_STATE_PSEUDOBULK_SPEARMAN` v0005 为 44.0（−1.3），均低于当时的 45.3，淘汰并保留失败诊断。

## 变更记录

| 日期 | 版本/分叉 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-08-21 | `baseline-001/T3_gata4/v0001` | 无 | 先用 `wt_identity` 建立 Gata4 KO 的合法提交底线。 | 服务器 `45.3`；保留 |
| 2026-08-22 | 追踪文档建立 | `v0001` | 把官方 `shift_transfer` 和状态分层响应作为两个后续分叉方向。 | 不改变模型；等待实现 |
| 2026-08-23 | `candidate-003/T3_gata4/v0002` | `v0001` | 全量 global shift-transfer，damp=1，并恢复 10k log1p library size。 | contract pass；未评分，保留为对照 |
| 2026-08-23 | `candidate-003/T3_gata4/v0003` | `v0001` | count-depth matching、top-50/50、damp=0.5、屏蔽 Mab21l2并将 Gata4 置零。 | contract pass；未评分，保留为保守对照 |
| 2026-08-24 | `submission-004/T3_gata4/v0002` | `v0001` | 按既定顺序回填服务器分数 `45.2`。 | 低于 `v0001` 0.1；淘汰 |
| 2026-08-24 | `submission-004/T3_gata4/v0003` | `v0001` | 按既定顺序回填服务器分数 `43.8`。 | 低于 `v0001` 1.5；淘汰 |
| 2026-08-28 | `B1-A2` 激活 | `v0001` | 冻结 L1/L2 两条 WT-only signed Spearman lane，均须人工评分。 | 进入生成 |
| 2026-08-28 | `v0004` / `v0005` | `v0001` | 生成 7,449×500 的 Gata4 signed sparse residual 两候选；硬性 contract/invariant 均通过，self-check 仅作诊断。 | `score_pending`；两条均交付人工上传 |
| 2026-08-28 | `v0004` / `v0005` 评分回填 | `v0001` | 用户返回 T3 服务器分数 44.7 / 44.0；两条均低于 45.3 baseline。 | 淘汰为 leaderboard 改进；保留不可变文件做失败诊断，暂停 B1-A3 |
| 2026-08-30 | `B2-T3-A1` / `v0006` / `v0007` | `v0001` | 按 signed prior committee 只用 sanitized WT 外部表达、GATA4 ChIP directness 和两票本地 WT-only 模型，生成 L1 严格 direct 与 L2 Gata6 half-dose 两 lane。 | 2/2 contract/protected PASS；local source-only diagnostic 已完成；服务器未提交，均 `score_pending`，结论 `HOLD_AS_COMPONENT` |
| 2026-09-04 | `B2-T3-A1` / `v0006` / `v0007` 评分回填 | `v0001` | 用户回填服务器分数：**L1=45.5、L2=45.5，均 +0.2 vs baseline 45.3，并列新 board best**。 | 首次有候选超过 `wt_identity` 45.3（此前 v0002–v0005 五次均失败）；两 lane 服务器无法区分，并列晋级当前 selection，不声称 lane 偏好；derived T3=45.5/Total=149.7 待服务器页面确认；科学 gate 不变（仍 `CLOSED_AS_RESEARCH_COMPONENT`，`blocks_submission: false`）；artifact 不可变 |
| 2026-08-31 | `T3-S1-PRIOR` | `P0-LOCK` | 按 Batch 3 契约开始 prior committee 实现；先锁定已审计本地数据/源归档并核验隔离部署，再实现多 condition schema、lineage gate 和 L1/L2 prior。 | 任务已激活；本阶段不生成 H5AD、不上传；外部快照缺失将显式 `BLOCKED_EXTERNAL_DATA` |
| 2026-08-31 | `T3-S1-PRIOR` bundle | `P0-LOCK` | 完成 B2 evidence adapter、multi-condition/dosage prior schema、L1/L2 cap/conflict/lineage gate 和 source-only checks。 | 31,458 records；L1/L2 非零 2,050/5,125；gate `HOLD_AS_COMPONENT`；β-catenin 10,500 条均 `BLOCKED_EXTERNAL_DATA`；不生成候选 |
| 2026-08-31 | `T3-S1-PRIOR` deployment hardening | `T3-S1-PRIOR` | 将 velocyto 改为显式锁定本地 wheel；补齐 source/archive SHA256、known-KO JSON、dosage/conflict/lineage fail-closed 与双源知识快照审计。 | velocyto import PASS；CellOracle 仍因 `genomepy` 缺失阻塞，scTenifoldKnk 仍因 `scTenifoldNet 1.3 < 1.4` 阻塞；两份 prior schema/manifest PASS；仍不进入 S1B |
| 2026-08-31 | `T3-S1-PRIOR` external deployment repair | `T3-S1-PRIOR` | 用户授权下载固定 `genomepy`/`scTenifoldNet` 及必要依赖，并将 CollecTRI/OmniPath 快照做内容级本地审计。 | deployment `PASS`；两源快照 `AUDITED_PASS`；prior 重跑仍为 `HOLD_AS_COMPONENT`，原因收敛为 stability sensitivity；不生成候选 |
| 2026-08-31 | pre-formal-analysis contract closure | `P0-LOCK` / `T3-S1-PRIOR` | 实现单一 H5AD contract 读写入口，加入 panel/order、cell ID、表达、空间、required fields、round-trip 和原子发布检查。 | 5 个 current parent 全部 contract `PASS`；接口测试 `18 passed`；新版 adapter 以独立 contract-preflight hash 锁定；不覆盖历史 P0 scaffold 快照 |
| 2026-08-31 | `T3-S1B` knowledge integration preflight | `T3-S1-PRIOR` | 实际读取已审计的 CollecTRI/OmniPath，生成 Gata4/Gata6 edge evidence 和 Ctnnb1 directed-path evidence；不做 state join 或 prior promotion。 | CollecTRI 21/18 条 TF-edge、OmniPath 1 条 Ctnnb1→Pitx2 路径；integration `PASS`，scientific validation `NOT_RUN` |
| 2026-08-31 | stability reinforcement preflight | `T3-S1-PRIOR` | 比较外部 signed edge 与两个本地 model family 的方向重叠，显式评估是否能解锁 leave-one-family-out。 | discordance 与 state-specific activity 缺口仍在；稳定性保持 `HOLD`，不把外部快照硬接为第三票 |
| 2026-08-31 | pre-formal-analysis hardening closeout | `P0-LOCK` / `T3-S1-PRIOR` | 根据复核补强 parent SHA/protected-field/no-clobber contract；外部快照增加 source/dataset/taxon/license fail-closed 校验，并将 directness 与未校准 confidence 分开；输出迁移到独立 v2 目录。 | 5/5 parent contract、registry SHA256、protected-field、round-trip PASS；实际接口测试 `22 passed`；knowledge `COMPONENT_PASS` 但 candidate admission `HOLD`；prior gate 仍 `HOLD_AS_COMPONENT`，不生成候选 |
| 2026-08-31 | pre-formal-analysis provenance refresh | `T3-S1-PRIOR` | 为 upstream gate 增加不可变 snapshot，重新串联 knowledge preflight、prior gate 和 stability preflight，避免后续可变 bundle 覆盖来源证据。 | v3 knowledge/stability manifest 与 source hash 自洽；prior 仍 `HOLD_AS_COMPONENT`，不生成候选、不上传 |
| 2026-08-31 | `T3-S1A-STATE-JOIN` 激活 | `T3-S1-PRIOR` | 按已落盘方案引入精确 E8.75 Extended Mouse Atlas、full mouse OmniPath/CollecTRI、真实 CellOracle/scTenifoldNet/scTenifoldKnk 和四条 route-specific gate；候选生成、评分、服务器提交保持关闭。 | 执行中；旧 prior 不覆盖；若输入或方法不可审计，route 显式 `BLOCKED`/`NOT_RUN`，不降级为 proxy |

| 2026-08-31 | T3-S1A 输入/部署补强与实际运行 | `T3-S1A-STATE-JOIN` | 5 个 Atlas 注释别名通过固定 Ensembl identity 闭合到 500-gene panel；缓存 CellOracle mm10 base-GRN；修正二维 state 索引、R 4.5.1 版本锁和共享 GRN fit。 | 输入审计、state join、full OmniPath/CollecTRI audit PASS；v5 CellOracle Gata4 real API PASS，Gata6/Ctnnb1 full propagation 超过 bounded window，scTenifold/route gate 未在该 atom 启动；结果 `BLOCKED_RUNTIME`，不生成候选 |
| 2026-09-01 | `T3-S1A-STATE-JOIN-20260901-v6` | `T3-S1A-STATE-JOIN-20260831-v5` | 保持 exact 输入、GRN 和方法参数不变，将 CellOracle 每个 target 放入独立 fork worker，增加原子 checkpoint、RSS/runtime 记录，并完成 scTenifold 与四路 gate 汇总。 | exact input/state join PASS；Gata4 CellOracle real API PASS；Gata6/Ctnnb1 在当前 base GRN 中明确不适用；三条 scTenifold 输出完成；全局 gate `BLOCKED`，原因含 `STATE_ACTIVITY_NOT_VALIDATED`，不生成候选、不上传 |
| 2026-09-01 | `T3-S1A-STATE-JOIN-20260901-v7` | `T3-S1A-STATE-JOIN-20260901-v6` | 修正 state-specific CellOracle 输出到 recorded parent-state 的显式映射，排除 unmatched external states；增加 full-matrix state-response、state/sample coverage 和 biological-activity 分层审计，并将当前 GRN 的 N/A target 排除出 selected-gene stability。 | exact input/state join PASS；Gata4 CellOracle PASS；Gata6/Ctnnb1 显式 `NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT`；scTenifold 三路 `PASS_UNSIGNED_RANK_ONLY`；state-response support `NOT_IDENTIFIABLE`（12/23 通过、11/23 HOLD），全局 `HOLD_AS_COMPONENT`、四路均 `HOLD`；不生成候选、不上传 |
| 2026-09-01 | `T3-S1B-STATE-JOIN-20260901-v1` | `T3-S1A-STATE-JOIN-20260901-v7` | 首次执行 external state-context adapter；在输入行身份比较正确前置下，发现 unresolved OmniPath path 的 hop-rank 表示与 v7 不一致，fail-closed 并保留失败 receipt。 | `BLOCKED_INPUT_IDENTITY`；未生成候选、不评分、不上传；作为不可复用的封装失败记录保留 |
| 2026-09-01 | `T3-S1B-STATE-JOIN-20260901-v2` | `T3-S1A-STATE-JOIN-20260901-v7` | 修正 unresolved path 保留 hop-based rank，并将 external edge/path 严格隔离为 `GLOBAL_CONTEXTUAL`；LOFO 从 family-native biological rows 重算，冲突只对派生 sign 归零。 | 4/4 route gate `HOLD`；5808 条 external contextual rows、137148 条总 source rows；manifest SHA256 `239e5c474986cb54e70d5b1451330a20350be38fadaf7641c1e2177b2aea34ea`；53 项回归测试 PASS；不生成 H5AD/候选、不运行 scorer、不上传 |
| 2026-09-01 | `T3-S1B-STATE-JOIN-20260901-v3` | `T3-S1A-STATE-JOIN-20260901-v7` | 将实现脚本 SHA256 和无 initial Git commit 状态写入 input lock、stable manifest 与 gate，补齐 artifact-to-code provenance。 | 4/4 route gate `HOLD`；5808 条 external contextual rows、137148 条总 source rows；实现脚本 SHA256 `cd480790fa6cbf7e6618ec28675983143466788847e79e73040d63df7dfe9d8c`；manifest SHA256 `396b15d976e10700709c7628539dd2e9cac21b66612d9b72faa772921413744e`；53 项回归测试与独立 tester PASS；不生成 H5AD/候选、不运行 scorer、不上传 |
| 2026-09-02 | `T3-S1-CLOSURE-20260902-v1` | `T3-S1A/v7`、`S1B/v3`、`S1C-A/v1`、`S1C-B/v3`、`S1D/v3` | 纯文档收口，无新计算：汇总五组件证据链 SHA，写死三条未满足硬条件（signed family<2、E8.75 activity 不可得、stability 未闭合）与最小解锁条件；采纳外部建议，执行主线切换 T1。 | 链状态 `CLOSED_AS_RESEARCH_COMPONENT`；与同日 `T3-S1C-GATE-SATISFIABILITY` 的 `UNSATISFIABLE_UNDER_FIREWALL` 结论一致；best 仍为 45.3，`blocks_submission: false`；历史 artifact 全部不可变 |
## 下一步

下一步（2026-09-04 更新）：`B2-T3-A1` v0006/v0007 服务器双双 **45.5**（+0.2 vs baseline 45.3），并列新 board best 已晋级——这是 T3 首次有候选超过 `wt_identity`。科学 gate 不变：T3-S1 链仍 `CLOSED_AS_RESEARCH_COMPONENT`（`UNSATISFIABLE_UNDER_FIREWALL`），leaderboard 增益不解除 gate、不作机制证据；重开条件见收口报告第 6 节（官方新数据、organizer 书面放宽、或研究分支产出可审计独立 signed family）。derived T3=45.5/Total=149.7 待服务器页面确认。后续 T3 工作仍需新 atom 授权。

Batch 1 收尾报告：`reports/PHASE_REPORT_BATCH1_20260829.md`；Batch 3 收尾报告：`reports/PHASE_REPORT_BATCH3_20260904.md`。

## 2026-09-01 新增组件与证据

| 日期 | atom | 父版本 | 变更摘要 | 结果与边界 |
|---|---|---|---|---|
| 2026-09-01 | `T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1` | `T3-S1A-STATE-JOIN-20260901-v7`、`T3-S1B-STATE-JOIN-20260901-v3` | 按 CellOracle 原生 `TFdict` 逻辑构建不改 parquet 的 target-compatible adapter；加入 18 个 Gata6 一跳 CollecTRI panel relation 和 1 个严格一跳 `Ctnnb1→Pitx2` OmniPath relation，多跳全部排除。 | method/source compatibility `PASS`；stable manifest `6700b919cba382475cbd6a1c3bee0dd8af5271685285c18011c4e3bab8e8706c`；biological activity `NOT_VALIDATED`，`HOLD_AS_COMPONENT`；无候选、无 scorer、无服务器提交，`blocks_submission: false`。 |
| 2026-09-01 | `T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v1` | `T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1` | 初始 synthetic fixture 将 Gata4 也列为待验证 target，但 fixture 没有对应 native outgoing response；按 fail-closed 保留失败 receipt，不覆盖。 | Gata6/Ctnnb1 smoke 通过、Gata4 边界失败；不作为可复用版本，不生成候选，不上传，`blocks_submission: false`。 |
| 2026-09-01 | `T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v2` | `T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1` | 将 smoke 边界收窄为新 adapter 的 Gata6/Ctnnb1，并在项目 venv 中运行真实 CellOracle 0.22.0 的 `TFdict` import、fit 和 `simulate_shift`。 | 2/2 target `PASS`，输入/输出 `[24,20]` 且 finite；stable manifest `806bf41acadfb9b5dc0d0b2329b36e1848b390231c573edcf8ec5e8e8ac0c817`；仅 synthetic structural smoke，`NOT_VALIDATED`，无候选/上传，`blocks_submission: false`。 |
| 2026-09-01 | `T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1` | `T3-S1A-STATE-JOIN-20260901-v7`、`T3-S1B-STATE-JOIN-20260901-v3` | 获取并审计 GSE156307/GSE255237 两份 processed GEO 表达数据，同时登记 3 个 metadata-only 候选；保留样本设计冲突和阶段/组织不匹配。 | Gata4 E14.5 HS cKO/WT log2FC `-1.1839`（5/5 方向一致），Gata6 E11.5 OFT MUT/WT log2FC `-0.3362`（4/4 方向一致）；均为 off-target context，E8.75 matched activity `NOT_IDENTIFIABLE`，independent signed families `0`；stable manifest `9017b2db83c09a776c8c1620f8ca00c6740f3c1d288ed857d9635c1b30f42fdf`；不解锁候选/提交，`blocks_submission: false`。 |
| 2026-09-01 | `T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3` | `T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1` | v2 的 post-run self-check 发现 genomepy SQLite `cache.db-shm` 临时文件被误列入 stable manifest；新版本排除 runtime cache/mpl/numba 前缀和 SQLite sidecar，再次运行相同 2-target smoke。 | Gata6/Ctnnb1 真实 CellOracle 0.22.0 fit/simulate 2/2 PASS；stable manifest 自校验 7/7 PASS，SHA256 `7770e075838309af5d339506b02e7975459aa651deb8d10f4079f25fec9c822d`；v2 原子产物保持不可变但不再作为复用版本；仍为 synthetic structural smoke、`NOT_VALIDATED`，无候选/上传，`blocks_submission: false`。 |
| 2026-09-01 | `T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3` | `T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v2`、`T3-S1A-STATE-JOIN-20260901-v7`、`T3-S1B-STATE-JOIN-20260901-v3` | 在保留 v2 初步原子的前提下补齐冻结 contract、逐 GSM sample QC、GPL probe/Entrez mapping QC、gene/study effects 和 deterministic run manifest；三份官方 E9.5 series matrix 与两个官方 platform annotation 均 hash-locked，GPL1261 多探针改用样本内 median。 | GSE5298/GSE9652 为 Gata4 两个早期心脏组织 family，GSE78125 为 Ctnnb1 一个 AHF family；矩阵完整性/映射 `PASS`，target expression 仅 descriptive；E8.75 state-matched activity `NOT_IDENTIFIABLE`，independent signed family `0`，stable manifest `6c2806aa381f099e3db88f38a35278d4500e1aeb1f8de7fe3cfa20e2db487e0c`；无候选/上传，`blocks_submission: false`。 |
| 2026-09-02 | `T3-S1C-GATE-SATISFIABILITY-20260902-v1` | `T3-S1C-A/v1`、`T3-S1C-B/v3`、`T3-S1D/v3` | 对现行 activity gate、T3 firewall、S1B candidate contract 做证据集合审计，区分 WT-context coherence 与 target-specific activity；不读取新矩阵、不运行模型。 | 当前 gate 判定 `UNSATISFIABLE_UNDER_FIREWALL`；保持 `HOLD_AS_COMPONENT`、`candidate_generation=false`、`server_submission=false`、`blocks_submission=false`。只有正式 contract/claim 变更后才可另建 S1C-C exact E8.75 WT inference；旧 artifact 不变。 |

2026-09-04（batch4）：`B4-P0-STATE-FLOOR-PARITY` 完成并评分。T3 exact-floor 候选 v0008（`b4p0_l0_exact_floor`，均匀抽样 seed 20260904、原始行序、坐标 float32、零变换）服务器 **46.8**（+1.5 vs wt_identity 45.3，+1.3 vs v0006/7 45.5）→ **新 board best，晋级当前 selection**；同时实证旧 signed-prior 下游 residual 相对 no-change 有害。仍低于官方 floor 定义 50 → `FLOOR_PARITY_UNRESOLVED` 开启。derived T3=46.8/Total≈151.0 待服务器页面确认。T3 后续对比基准改为 46.8；科学 gate 不变。产物 `artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/`。下一步：Wave 1 `B4-T3-R1-GENOTYPE-ONLY-ABLATION` 待授权。

2026-09-05（batch4 Wave 1）：`B4-T3-R1-GENOTYPE-ONLY-ABLATION` 完成，两 lane 待上传评分——v0009（L1 全细胞 Gata4=0，col sum 6495.1→0.0）、v0010（L2 p≥0.5 hard lineage，4916 细胞，col sum→192.5）；其余 499 genes 逐值 parent，Gata6 未动，坐标/行序/n_obs 逐位一致，contract 全 PASS。L3 因本地权威源无 Gata6 F/+ 确认而标记 `BLOCKED_CONDITION_NOT_CONFIRMED`（未替换）。产物 `artifacts/batch4/B4-T3-R1-GENOTYPE-ONLY-ABLATION-20260905-v1/`，交付包 `deliveries/b4t3r1a__t3__upload__20260905.zip`（先）与 `deliveries/b4t3r1b__t3__upload__20260905.zip`（后）。结论待服务器仲裁（三分支解释见 RESULT）。

2026-09-05（batch4 Wave 1）：`B4-T3-R1-GENOTYPE-ONLY-ABLATION` 双 lane 服务器仲裁——v0009/v0010 双双 **46.95**（+0.15 vs floor 46.8），**并列新 board best**；旧下游 residual 为主要伤害源获第二实证，L2==L1 不声称 lineage 偏好；科学 gate 不变。derived Total≈151.40 待确认。详见 registry §B4-T3-R1 与 DECISIONS D-20260905-WAVE1-001。

2026-09-11（batch4 Wave 2）：`B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR` 完成，双 lane 待上传评分——v0011/v0012（delay α=0.25/0.50，仅 5/33 三阶段共享 states 有方向 + raw-roundtrip genotype transform）；contract 全 PASS，坐标/行序/n_obs 逐位一致，重跑字节一致，clip 0.06%。产物 `artifacts/batch4/B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR-20260911-v1/`，交付包 `deliveries/b4t3r2a__t3__upload__20260911.zip`（先）与 `deliveries/b4t3r2b__t3__upload__20260911.zip`（后）。若双 lane ≤ floor 则 T3 标 ARCHITECTURE_RESET_REQUIRED。

2026-09-14（batch4 Wave 2）：`B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR` 双 lane 服务器仲裁——v0011=**46.45**、v0012=**46.47**，均低于 floor 46.8 → T3 标 **ARCHITECTURE_RESET_REQUIRED**，Batch 4 内不再追加手工路线；de_score 仍是最弱子项（38.1/38.5），delay 假设不动 DE 幅度。selection 保持 v0009/v0010（46.95）。详见 registry §B4-T3-R2 与 DECISIONS D-20260914-WAVE2-001。

2026-09-16（G0 15 轮目标）：`G1-T3-R1..R5` 五 lane 服务器仲裁——v0013=**46.88**（-0.07）、v0014=**46.95**（持平）、v0015=**46.95**（持平）、v0016=**46.88**（-0.07）、v0017=**46.84**（-0.11）；selection 保持 v0009/v0010（46.95）；de_score 五 lane 全钉 **39.2**，与开工前本地盲性诊断（proxy de 0.1739 五连同）一致；传播-剂量族关闭为晋级路线。详见 registry §G1-T3 与 DECISIONS D-20260916-G0T3-001。

2026-09-17（G1-T3 30 轮计划 D2 首轮）：`G1-T3-R6-CIPHER` 完成——v0018（L_A，CellOracle 级联 u＋心脏全量/其余半量＋t-收缩 C=2；Step-0 恒等复现 v0009 通过；contract PASS；119 基因位移，Kitl/Cdk1 居首）。本地 de 0.1739/dir 0.2443/slope −0.5371，无回归但盲（proxy 盲性第 6 例）→ 机制 bet 待上传。单包 `deliveries/g1t3r6__t3__upload__20260917.zip`。更正：T3 行中心脏谱系实占 20.75%（1546/7449），调研备忘中的 52% 作废。详见 run 内 RESULT.md。

2026-09-17（G1-T3 30 轮计划 D8/D5/D4/D3/D6/D1/D7 全收）：R7-SPLIT v0019（`4b6c5b45…`，fallback=0，R6 消融对照）、R8-KNK v0020（`d8b50dd9…`，498 基因全覆盖）、R9-HOP2 v0021（`1bde8b96…`，motif-hop1＋共表达-hop2，首跑维度 bug 已修）、R10-GRAPH v0022（`5423dc56…`，PPR Top-150，唯一 dir 为正）、R11-SIGNMAX v0023（`22340b14…`，一致性平方，mmd_u 最低）、R12-DEBIAS v0024（`b1a3c01d…`，去偏后 dir≡baseline）、R13-SPATIAL v0025（`4f64ce1e…`，k15 平滑，lib-ratio 0.69 系 Jensen 效应已披露）；7/7 contract PASS、无回归、本地全盲（第 6–12 例）。8 候选（＋R6 v0018）统包 `deliveries/g1t3__t3__upload__20260917.zip`（8 成员 SHA 全验，替代单包 g1t3r6）。D4 首跑失败 receipt 保留。服务器仲裁待用户统一提交后回填。

2026-09-17（G1-T3 30 轮计划 R9–R13 仲裁）：v0021=**46.88**（-0.07）/v0022=**46.93**（-0.02）/v0024=**46.90**（-0.05）落 TIE 带不晋级，v0023=**46.95**（持平，exact TIE）留任不断，v0025=**43.30**（-3.65，mmd -9.4/variogram -26）灾难性淘汰；selection 保持 v0009/v0010（46.95）。de_score 首次松动（R10/R11=39.6，+0.4 vs 十连钉 39.2），但 variogram 回吐，天花板呈 de↔variogram 互换（同 T1 形）。空间平滑族在 T3 关闭（本地 proxy 再反一例）。R6–R8（v0018–v0020）同包仍待分。详见 registry §G1-T3-R9..R13 与 DECISIONS D-20260917-G0T3R9R13-001。

2026-09-20（D-20260920-G0T3R6R8-001）：T3 R6–R8 分数回填完成：v0018=46.94（TIE）、v0019=46.95（exact TIE）、v0020=46.64（REJECT）；selection 保持 v0009/v0010=46.95。R6–R13 八候选均已评分，余分队列清零，后续轮次待决定。三个 de_score 均为 39.2；R8 direction 增益伴随 variogram 下降，不能据此声称机制改进。15 子项入库；科学 gate 不变。

2026-09-20（新路线提案，未执行）：结合 R6–R13 评分提出六方向：表达排序重建、WT 流形内异质响应、稀疏条件机制、全转录组中介映射、细胞间信号、多扰动监督训练。详见 `reports/T3_NEXT_ROUTES_20260920.md`；均为 PROPOSED/NOT_RUN，未建候选。建议先做前两项；v7 WT 输入在盘但旧索引部分指向已清理 v5，多扰动数据尚未就绪。selection、科学 gate 与 active_atom 不变。

2026-09-20（六路线执行开工）：用户授权实现六方案；设计锁定于 configs/t3_next/design.json，独占 scripts/t3_next、tests/t3_next、configs/t3_next 与 artifacts/t3_next。先实现共用校验与路线算法，再逐路线执行全 panel；缺数据/许可的正式计算记录 BLOCKED，不以 smoke 替代。

2026-09-20（v0026 r1graph）：新建六路线候选，parent=v0022；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-NEXT-SIX-20260920-v4/r1/RESULT.json。

2026-09-20（v0027 r1sign）：新建六路线候选，parent=v0023；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-NEXT-SIX-20260920-v4/r1/RESULT.json。

2026-09-20（v0028 r2adapt）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-NEXT-SIX-20260920-v4/r2/RESULT.json。

2026-09-20（v0029 r2random）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-NEXT-SIX-20260920-v4/r2/RESULT.json。

2026-09-20（路线二对照修复）：回查发现 v0029 随机臂包含 self donor，实际改变 1,383 细胞而非标称 1,840；v0028/v0029 成对撤回、未上传，artifact 保留，INDEX 标 invalidated_unsubmitted。新增禁止 self/相同表达 donor 和实际改变计数断言，另 run 重跑；不将旧对照用于结论。

2026-09-20（v0030 r2adapt）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-NEXT-SIX-20260920-v5/r2/RESULT.json。

2026-09-20（v0031 r2random）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-NEXT-SIX-20260920-v5/r2/RESULT.json。

| 2026-09-20 | T3-NEXT-SIX 收口 | R1 v0026/v0027、R2 v0030/v0031 已打包，未提交/未评分；R3 全量线性/样条裁剪超限，R4 映射劣于类型均值，无候选；R5/R6 缺输入，正式计算 NOT_RUN；12 项测试通过 | reports/T3_NEXT_EXECUTION_20260920.md；D-20260920-T3NEXT-001 |

| 2026-09-20 | R5/R6 首轮数据收集 | GSE261783 两样本完成隔离过滤，5454×32287，26 候选扰动，500/500 panel；R5 来源表/37 引用卡片落盘但完整链未准入；全部未训练、model_input=false；R3/R4 修复加入 TODO | reports/t3_data_intake_20260920/REPORT.md；D-20260920-T3DATA-001 |

- 2026-09-20｜R5/R6开工准备｜原R6补用途门；提出显式shape-only后继设计并实现基础目标转换（未完成训练集成）。过滤Chd4/Smarca4/Yy1后4998细胞/23扰动，仍隔离；R5批准链0。未生成候选、未提交/未评分；见 `reports/t3_r56_readiness_20260920/REPORT.md`。

2026-09-20（v0032 r5off）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-R5-SIGNOR-MINIMAL-20260920-v1/RESULT.json。

2026-09-20（v0033 r5on）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-R5-SIGNOR-MINIMAL-20260920-v1/RESULT.json。

- 2026-09-20｜R5最小SIGNOR链补齐并执行｜4条源边组成Pdgfb/Pdgfrb/S100a10先验，系数仅官方WT拟合。父v0009→v0032(r5off)、v0033(r5on)，contract/checks PASS；未提交/未评分。artifact/SHA见submissions/INDEX.tsv；信号幅度小，未证明增益。报告 `reports/t3_r5_completion_20260920/REPORT.md`。

- 2026-09-20｜R1/R2服务器回分｜v0026/v0027父版本同分，不晋级；v0030/v0031低于父版本，当前候选淘汰。四个SHA核验通过，R5两候选仍未提交/未评分。证据 `reports/SERVER_SCORE_REGISTRY.md#t3-next-r1r2-score-return-20260920`；决策 D-20260920-T3NEXTSCORE-001。

- 2026-09-21｜R5/R6开工准备｜规则修改生效；R5保留v0032/v0033待评分，不重复生成；R6按新标准重审26条件并恢复3项先前保守排除，5454×500矩阵、27×80 WT特征、27×27图就绪。完整WT图谱68910细胞用于表示，无扰动响应构图。训练/目标推断NOT_RUN；19测试通过。见 `reports/t3_r56_launch_20260921/REPORT.md`。

- 2026-09-21：R6按冻结设计首次训练及目标推断完成；负值门槛失败，0候选，未改参数。证据 `reports/t3_r6_execution_20260921/REPORT.md`。

- 2026-09-21：R5 v0032/v0033回分登记，总分及五子分在显示精度下完全相同，两者均与父版本同总分；保留原selection，不晋级。证据 `reports/SERVER_SCORE_REGISTRY.md#t3-next-r5-score-return-20260921`；D-20260921-T3R5SCORE-001。

- 2026-09-21：本轮六路线与历史路线复核完成；R6缩幅不能消除零条目负值，图模型相对平均响应优势约1.36%；R5实际只改变一列。优化建议见 `reports/t3_route_review_20260921/REPORT.md`，无新候选，历史结果不改写。

- 2026-09-21：启动新修复分支R6→R3→R4；冻结repair_20260921.json，采用非负输出、样本内NTC/强对照、四空间块与五遮蔽基因折；无超参搜索，旧失败保留，服务器未提交。

2026-09-21（v0034 r6meanfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R6-20260921-v1/RESULT.json。

2026-09-21（v0035 r6graphfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R6-20260921-v1/RESULT.json。

- 2026-09-21：R6修复v1生成v0034/v0035，负值消除但未优于平均倍率/置乱图；R3/R4正式运行前将比例输出统一到expm1后的强度空间，保持原观察零值且限制强度倍率，不在log表达上直接相乘。新设计与代码快照以各run为准，R6历史快照不改。

2026-09-21（v0036 r3linfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R3-20260921-v1/RESULT.json。

2026-09-21（v0037 r3splfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R3-20260921-v1/RESULT.json。

2026-09-21（v0038 r4panelfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R4-20260921-v1/RESULT.json。

2026-09-21（v0039 r4medfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R4-20260921-v1/RESULT.json。

- 2026-09-21：R4修复v1的映射评估通过，但最终推断漏用校准斜率；v0038/v0039未提交撤回，文件保留。补齐验证/推断一致性并在v2重跑完整映射与反事实，不修改旧run。

2026-09-21（v0040 r4panelfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R4-20260921-v2/RESULT.json。

2026-09-21（v0041 r4medfix）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-REPAIR-R4-20260921-v2/RESULT.json。

- 2026-09-21：修复首批最终交付6候选，R4 v2已应用校准斜率；R1结构组件对R6为NO_OP，不重复打包。23测试及最终身份/包校验通过，未提交/未评分。见 `reports/t3_repairs_20260921/REPORT.md`；D-20260921-T3REPAIR-001。

- 2026-09-27｜n1quant｜新路线：按类型和深度分层的阳性分位数响应迁移，不替换整细胞；执行前设计冻结于 configs/t3_next/five_20260927.json，报告 reports/T3_FIVE_DESIGN_20260927.md；未提交/未评分。

- 2026-09-27｜n2hurdle｜新路线：出现概率/阳性强度分开建模，允许零条目响应；执行前设计冻结于 configs/t3_next/five_20260927.json，报告 reports/T3_FIVE_DESIGN_20260927.md；未提交/未评分。

- 2026-09-27｜n3latent｜新路线：来源响应低秩核回归，无图传播；执行前设计冻结于 configs/t3_next/five_20260927.json，报告 reports/T3_FIVE_DESIGN_20260927.md；未提交/未评分。

- 2026-09-27｜o1stable｜优化既有R3：四空间块响应稳定性收缩；执行前设计冻结于 configs/t3_next/five_20260927.json，报告 reports/T3_FIVE_DESIGN_20260927.md；未提交/未评分。

- 2026-09-27｜o2shrink｜优化既有R6：训练扰动内嵌套估计向均值收缩；执行前设计冻结于 configs/t3_next/five_20260927.json，报告 reports/T3_FIVE_DESIGN_20260927.md；未提交/未评分。

2026-09-27（v0042 n1quant）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v1/n1quant/RESULT.json。

2026-09-27（v0043 n2hurdle）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v1/n2hurdle/RESULT.json。

2026-09-27（v0044 n3latent）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v1/n3latent/RESULT.json。

2026-09-27（v0045 o1stable）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v1/o1stable/RESULT.json。

2026-09-27（v0046 o2shrink）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v1/o2shrink/RESULT.json。

- 2026-09-27｜o1stable首跑撤回｜v0045未提交，保留文件；Gata4自身置零幅度混入下游稳定性先验，v2排除该列并完整重训四块及最终模型；其余四路线不受影响。

2026-09-27（v0047 o1stable）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v2/o1stable/RESULT.json。

- 2026-09-27｜n2hurdle首跑撤回｜v0043未提交保留；原零值的负向加法请求需投影，改为正向有界log增量/负向有界原强度衰减，无负值裁剪；配置新快照与v2完整重训。

2026-09-27（v0048 n2hurdle）：新建六路线候选，parent=v0009；contract PASS，结构灾难检查 PASS，未提交/未评分，不晋级。证据 artifacts/t3_next/T3-FIVE-20260927-v2/n2hurdle/RESULT.json。

- 2026-09-27｜五路线收口｜3新+2优化全量执行，最终 n1quant=v0042、n2hurdle=v0048、n3latent=v0044、o1stable=v0047、o2shrink=v0046；五contract/重放PASS，11测试；v0043/v0045撤回，未提交/未评分，不晋级。reports/t3_five_20260927/REPORT.md；D-20260927-T3FIVE-001。注：本轮候选自动登记沿用旧writer的“六路线”文案，实际属于本次五路线方案。

- 2026-09-27｜FIVE+修复回分｜v0048 47.93 (+0.98) PROMOTED 新 T3 best；v0046 47.65 (+0.70)/v0034 47.53 (+0.58)/v0044 47.47 (+0.52) 超旧线居次；v0035 47.03/v0036 46.98/v0047 46.97 TIE；v0042 46.95 exact tie。Total 156.06→157.04。v0037/v0040/v0041 仍 score_pending。D-20260927-T3SCORE-001。

- 2026-09-28 T3-ROUND2 n1stack：新1：高分v0048与v0046顺序叠加，单组件/平均融合/反向次序消融；配置与kill-test对照已冻结，完整执行；未提交/未评分。设计 reports/T3_ROUND2_DESIGN_20260928.md。

- 2026-09-28 T3-ROUND2 n2orth：新2：类型空间混杂交叉拟合后学习正交残差响应；配置与kill-test对照已冻结，完整执行；未提交/未评分。设计 reports/T3_ROUND2_DESIGN_20260928.md。

- 2026-09-28 T3-ROUND2 n3occup：新3：合规来源检测率与阳性强度的联合迁移；配置与kill-test对照已冻结，完整执行；未提交/未评分。设计 reports/T3_ROUND2_DESIGN_20260928.md。

- 2026-09-28 T3-ROUND2 o1logit：优化v0048：Bernoulli logistic替换裁剪线性概率；配置与kill-test对照已冻结，完整执行；未提交/未评分。设计 reports/T3_ROUND2_DESIGN_20260928.md。

- 2026-09-28 T3-ROUND2 o2geneshrink：优化v0046：训练内部OOF估计输出基因收缩权重；配置与kill-test对照已冻结，完整执行；未提交/未评分。设计 reports/T3_ROUND2_DESIGN_20260928.md。

- 2026-09-28 T3-ROUND2 n1stack 新候选 v0049，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_round2/T3-ROUND2-20260928-v1/n1stack/RESULT.json。

- 2026-09-28 T3-ROUND2 n2orth 新候选 v0050，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_round2/T3-ROUND2-20260928-v1/n2orth/RESULT.json。

- 2026-09-28 T3-ROUND2 n3occup 新候选 v0051，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_round2/T3-ROUND2-20260928-v1/n3occup/RESULT.json。

- 2026-09-28 T3-ROUND2 o1logit 新候选 v0052，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_round2/T3-ROUND2-20260928-v1/o1logit/RESULT.json。

- 2026-09-28 T3-ROUND2 o2geneshrink 新候选 v0053，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_round2/T3-ROUND2-20260928-v1/o2geneshrink/RESULT.json。

- 2026-09-28 ROUND2收口：三新n1stack=v0049（高分v0048+v0046叠加）、n2orth=v0050、n3occup=v0051；两优化o1logit=v0052、o2geneshrink=v0053。全部全量执行/contract/独立模型重放PASS，13测试。KIR经验落实为精确组件复现、六臂组合诊断、强均值/置乱对照及固定模型出现率/强度消融；局部多数弱或负，不调参救门。未提交/未评分，best v0048保持；reports/t3_round2_20260928/REPORT.md；D-20260928-T3R2-001。

- 2026-09-28｜修复剩余三 lane 回分｜v0037 46.98（+0.03 vs 父 46.95 TIE，与同胞 v0036 五子项完全相同）、v0040 47.08（+0.13）、v0041 47.09（+0.14），三条距现 best 47.93 均 -0.8 以上，不晋级；selection v0048 不变。修复队列分数关闭（v0034/v0035/v0036/v0037/v0040/v0041 全已评分，v0038/v0039 已撤回）。D-20260928-T3REPAIR2-001。

- 2026-09-29 T3-THREE r1agree：高分响应方向一致门控叠加；参数执行前冻结，计划完整7449×500推断和四块WT诊断；未提交/未评分。reports/T3_THREE_DESIGN_20260929.md。

- 2026-09-29 T3-THREE r2damp：hurdle概率分量减弱/阳性强度保留；参数执行前冻结，计划完整7449×500推断和四块WT诊断；未提交/未评分。reports/T3_THREE_DESIGN_20260929.md。

- 2026-09-29 T3-THREE r3diffuse：同类型活跃细胞内预测响应图扩散；参数执行前冻结，计划完整7449×500推断和四块WT诊断；未提交/未评分。reports/T3_THREE_DESIGN_20260929.md。

- 2026-09-29 T3-THREE r1agree 新候选 v0054，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_three/T3-THREE-20260929-v1/r1agree/RESULT.json。

- 2026-09-29 T3-THREE r2damp 新候选 v0055，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_three/T3-THREE-20260929-v1/r2damp/RESULT.json。

- 2026-09-29 T3-THREE r3diffuse 新候选 v0056，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_three/T3-THREE-20260929-v1/r3diffuse/RESULT.json。

- 2026-09-29 T3-THREE收口：r1agree=v0054、r2damp=v0055、r3diffuse=v0056；三个完整7449×500 h5ad，四块WT拟合/条件诊断、12测试、独立重放/contract/包校验通过。三个未提交/未评分，best v0048=47.93保持；旧v0049–v0053仍待分。reports/t3_three_20260929/REPORT.md；D-20260929-T3THREE-001。

- 2026-09-29 T3-FIVE-SELECT r1active 新路线冻结：配置 configs/t3_five_select/design_20260929.json；训练块0/1、开发块2、锁定后审计块3，完整推断7449×500，仅三条入包。未提交/未评分。

- 2026-09-29 T3-FIVE-SELECT r2gene 新路线冻结：配置 configs/t3_five_select/design_20260929.json；训练块0/1、开发块2、锁定后审计块3，完整推断7449×500，仅三条入包。未提交/未评分。

- 2026-09-29 T3-FIVE-SELECT r3bag 新路线冻结：配置 configs/t3_five_select/design_20260929.json；训练块0/1、开发块2、锁定后审计块3，完整推断7449×500，仅三条入包。未提交/未评分。

- 2026-09-29 T3-FIVE-SELECT r4spline 新路线冻结：配置 configs/t3_five_select/design_20260929.json；训练块0/1、开发块2、锁定后审计块3，完整推断7449×500，仅三条入包。未提交/未评分。

- 2026-09-29 T3-FIVE-SELECT r5local 新路线冻结：配置 configs/t3_five_select/design_20260929.json；训练块0/1、开发块2、锁定后审计块3，完整推断7449×500，仅三条入包。未提交/未评分。

- 2026-09-29 T3-FIVE-SELECT r2gene 新候选 v0057，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r2gene/registered/RESULT.json。

- 2026-09-29 T3-FIVE-SELECT r4spline 新候选 v0058，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r4spline/registered/RESULT.json。

- 2026-09-29 T3-FIVE-SELECT r3bag 新候选 v0059，parent=v0048，完整7449×500，contract PASS，未提交/未评分。证据 artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r3bag/registered/RESULT.json。

- 2026-09-29 T3-FIVE-SELECT r1active 收口：完整推断/contract/独立进程重放PASS；同族开发排名未选，PARKED研究输出。证据 reports/t3_five_select_20260929/REPORT.md；D-20260929-T3FIVESELECT-001。

- 2026-09-29 T3-FIVE-SELECT r2gene 收口：完整推断/contract/独立进程重放PASS；v0057入三件包，未提交/未评分。证据 reports/t3_five_select_20260929/REPORT.md；D-20260929-T3FIVESELECT-001。

- 2026-09-29 T3-FIVE-SELECT r3bag 收口：完整推断/contract/独立进程重放PASS；v0059入三件包，未提交/未评分。证据 reports/t3_five_select_20260929/REPORT.md；D-20260929-T3FIVESELECT-001。

- 2026-09-29 T3-FIVE-SELECT r4spline 收口：完整推断/contract/独立进程重放PASS；v0058入三件包，未提交/未评分。证据 reports/t3_five_select_20260929/REPORT.md；D-20260929-T3FIVESELECT-001。

- 2026-09-29 T3-FIVE-SELECT r5local 收口：完整推断/contract/独立进程重放PASS；同族开发排名未选，PARKED研究输出。证据 reports/t3_five_select_20260929/REPORT.md；D-20260929-T3FIVESELECT-001。

- 2026-09-29｜T3-ROUND2 五 lane 回分｜v0049 47.86（−0.07 vs v0048，平局）不晋级，只作备份；v0053/v0052/v0050/v0051 依次更低，不晋级。selection v0048=47.93 不变。高分叠加没有超过 v0048 自己。D-20260929-T3R2SCORE-001。

- 2026-09-29｜T3最后六 lane 回分｜v0058 47.95（+0.02）平局备份；v0056/v0059 精确打平 47.93；v0054/v0057/v0055 不晋级。selection v0048 不变。T3 分数队列关闭，无待分候选。D-20260929-T3SCORE-002。
- 2026-09-30｜路线研究与虚拟敲除再审计｜只读核对53个已评分产物、15个代表表达矩阵及真实工具转换链；发现旧IQR幅度压零、状态响应平均抵消、RNA零检测无响应与缺少显式状态质量预测。在线检索后提出8个技术方向，建议优先状态化CellOracle、状态质量、活动因子、功能线性/Scouter及原版GEARS六项比较；均PROPOSED/NOT_RUN，无新候选、无上传、无新评分，selection v0048保持。报告 `reports/t3_research_audit_20260930/REPORT.md`；科学限制 `blocks_submission: false`。

- 2026-09-30｜T3-PRIORITY-SIX-20260930｜父：v0009 WT 载体，现役 v0048；来源报告 t3_research_audit_20260930/REPORT.md｜L-010 已登记完整计划；用户授权开始原生 CellOracle、状态质量、独立活动、功能线性、Scouter、GEARS 六项，均执行中/未评分/未提交；证据 reports/t3_priority_six_20260930/；D-20260930-T3SIX-001。

- 2026-09-30｜T3-PRIORITY-SIX decoder｜新增报告要求的来源侧检测率校准：按固定整扰动拆分拟合，检测率与阳性值分别处理，各状态预测 count 均值保留；保留原始 count-ratio 输出为对照，六项共同使用同一 decoder。无目标 KO 参与；尚未评分。配置/证据 artifacts/t3_priority_six_20260930/DETECTION_CALIBRATION.json。

- 2026-09-30｜T3-PRIORITY-SIX r2｜完整 native+状态质量推断的预测比例完全等于 WT（状态跨越 0/68910），判 NULL_STATE_MASS_RESPONSE，不登记质量单独/组合两件；修正无效应时随机采样制造假变化的问题，改整数配额采样且零变化精确保持原行。早期未登记随机研究输出隔离保留，不上传。科学 blocks_submission:false，其他六个独立表达候选继续。

- 2026-09-30｜T3-PRIORITY-SIX｜v0060 r1_celloracle｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；submissions/candidates/T3_gata4/v0060_six_r1_celloracle/submission.h5ad；D-20260930-T3SIX-001。

- 2026-09-30｜T3-PRIORITY-SIX｜v0061 r3_activity｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；submissions/candidates/T3_gata4/v0061_six_r3_activity/submission.h5ad；D-20260930-T3SIX-001。

- 2026-09-30｜T3-PRIORITY-SIX｜v0062 r4_functional｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；submissions/candidates/T3_gata4/v0062_six_r4_functional/submission.h5ad；D-20260930-T3SIX-001。

- 2026-09-30｜T3-PRIORITY-SIX｜v0063 r4_bilinear｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；submissions/candidates/T3_gata4/v0063_six_r4_bilinear/submission.h5ad；D-20260930-T3SIX-001。

- 2026-09-30｜T3-PRIORITY-SIX｜v0064 r5_scouter｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；submissions/candidates/T3_gata4/v0064_six_r5_scouter/submission.h5ad；D-20260930-T3SIX-001。

- 2026-09-30｜T3-PRIORITY-SIX｜v0065 r6_gears｜父 v0009（质量路线另绑定可追溯重采样载体）｜完整目标 7449×500，contract PASS；未提交/未评分；submissions/candidates/T3_gata4/v0065_six_r6_gears/submission.h5ad；D-20260930-T3SIX-001。

- 2026-10-01｜T3-PRIORITY-SIX交付｜六项核心计算及完整7449×500目标完成；v0060–v0065统一包，5测试/六件contract/包hash+CRC通过；未提交/未评分；状态质量NULL不登记，源侧功能基线小增量、Scouter/GEARS未胜平均扰动；父v0009，现役v0048不变；reports/t3_priority_six_20260930/REPORT.md；D-20261001-T3SIX-002。

- 2026-10-01｜组成通道诊断（T3-COMP-DIAG-20261001-v1）｜纯数据诊断，无候选/评分/外部数据。真实 KO 组成重加权的方向偏相关 +0.325（通道真实）；但"目标高表达簇被削"朴素规则在 Mab21l2 上不成立（Spearman +0.208/Pearson −0.078）；Gata4 在 E8.75 集中于心脏谱系（IFT-CM 88% 检出）。证据 artifacts/t3_comp_diag/T3-COMP-DIAG-20261001-v1/REPORT.md。现役 v0048=47.93 不变。

- 2026-10-01｜T3六项回分收口｜v0060–v0065及30子项已登记，全部REJECT；现役v0048不变，T3待分0；新CellOracle与旧adapter平局，强改动主要损伤分布；共同decoder在log评分空间改变响应，低来源基线的ratio放大已量化；reports/t3_score_review_20261001/REPORT.md；D-20261001-T3SIXSCORE-001。

- 2026-10-01｜T3架构建议A｜从逐基因平均响应转向WT锚定、功能条件化的联合分布残差OT flow；文献启发的设计，NOT_RUN、未生成候选/未提交/未评分，父版本不适用；reports/t3_two_architectures_20261001/REPORT.md；L-012；D-20261001-T3ARCH-001。
- 2026-10-01｜T3架构建议B｜多时间点软命运转移与相对群体份额联合建模，区别于旧硬状态迁移及逐基因occupancy；Gata4干预入口待落实；NOT_RUN、未生成候选/未提交/未评分，父版本不适用；同报告；L-012；D-20261001-T3ARCH-001。

- 2026-10-01｜T3-ARCH-TWO启动｜用户授权逐次完成：A条件残差flow先行，B软命运/相对份额后行；两项各一个候选，不自动上传；CellFlow/WOT启发的自定义实现，非原论文复现；来源/预算/结构冻结在artifacts/t3_arch_two_20261001/CONFIG.json；D-20261001-T3ARCH-002。

- 2026-10-01｜B发射抽样修复｜v0067未上传初版撤回，模型只需替换223行，整簇有放回抽样却丢掉1386个原有WT细胞；修复为同一预测配额下最大保留原有行，不重训、不改预测份额；旧artifact保留，新候选另登记；D-20261001-T3ARCH-003。

- 2026-10-01｜两架构交付｜A→B完整执行与验收通过，最终v0066/a_flow、v0068/b_fate统一包arch2__t3__upload__20261001.zip；两件完整7449×500、未提交/未评分。A来源未胜强基线，B部分覆盖WT时间留出未整体胜线性插值；Gata4干预是假设。现役不变；reports/t3_arch_two_execution_20261001/REPORT.md；D-20261001-T3ARCH-004。

- 2026-10-01｜两架构回分收口｜v0066/v0068总分与10子项登记，均REJECT，配置关闭，待分0；现役v0048不变。A方向显示值有亮点但DE/共表达损失主导，B当前组成预测无收益；v0067仍未提交撤回；reports/t3_arch_two_score_review_20261001/REPORT.md；D-20261001-T3ARCHSCORE-001。

- 2026-10-01｜Scaling 程序启动（用户授权逐个完成）｜T3 侧两条按序排在 D5c 之后：方向四全转录组中介（v7 输入在盘，先修索引引用；CPU 约 8h）→方向六多扰动监督（metadata-first 数据任务先行，BLOCKED_DATA_NOT_READY 则停）。`D-20261001-SCALE-001`。

- 2026-10-01｜T3-ARCH-TWO｜v0066 a_residual_flow｜父v0009，完整7449×500，contract PASS；未提交/未评分；新架构完整实跑、科学限制见执行报告；submissions/candidates/T3_gata4/v0066_arch_a_residual_flow/submission.h5ad；D-20261001-T3ARCH-002。

- 2026-10-01｜方向四输入核验＋设计冻结完成｜v7 三文件实核（27669×68910，2.8 亿非零）与提案一致；bioinf 索引无 v5 引用，无需修复；parent v0009。冻结见 `artifacts/t3_direction4/T3-DIR4-20261001-v1/DESIGN.md`（配对比较/预留验证/四条停止条件跑前写死）。下一步：实现映射脚本。

- 2026-10-01｜T3-ARCH-TWO｜v0067 b_fate_mass｜父v0009，完整7449×500，contract PASS；未提交/未评分；新架构完整实跑、科学限制见执行报告；submissions/candidates/T3_gata4/v0067_arch_b_fate_mass/submission.h5ad；D-20261001-T3ARCH-002。

- 2026-10-01｜T3-ARCH-TWO｜v0068 b_fate_mass_emit2｜父v0009，完整7449×500，contract PASS；未提交/未评分；新架构完整实跑、科学限制见执行报告；submissions/candidates/T3_gata4/v0068_arch_b_fate_mass_emit2/submission.h5ad；D-20261001-T3ARCH-002。

- 2026-10-02｜方向四脚本建成＋冒烟过＋全量开跑｜新文件 `scripts/t3_direction4/dir4_map_response.py`（相关kNN映射50验证基因硬隔离/配对AB臂/log1p加性响应/Gata4列锁定；门G1留出MAE<G2同粗谱系≥80%/G3中介可识别/增量非零，任一不过即STOP）。CPU冒烟机制过（小样本G1/G2不过，仅作全量参考，不改门）。全量后台开跑（8h cap），回包仲裁。候选号预留v0069（T3最大v0068）。

- 2026-10-02｜方向四双挂关闭｜全量（68910 RNA，wall 22 秒）G1 留出 MAE 0.552 vs 基线 0.518（33 类仅 7 类胜，最差 NCC/Forebrain/Hindgut；16 样本组 9 组胜）；G2 同谱系权重 0.612 vs 门 0.80（426 Unknown 细胞已排除）。按冻结 STOP：跨模态 kNN 映射精度过不了"同类型均值"这一关——RNA 邻居平均在 MERFISH 尺度上不如本类型均值，中介传播无从谈起。未建 v0069，未进 INDEX。`D-20261002-T3DIR4-001`。

- 2026-10-02｜方向六数据任务元数据屏蔽通过｜GSE261783 26 扰动基因逐一比对黑名单 31 项（GATA/WNT/cardiac/SMAD），显式命中 0/26，组合无；数量足够 gene-held-out。功能性 phenocopy 人工复核仍 open（Smarca4/Rest/Yy1 列复核提示，不扩黑名单）；许可仍 QUARANTINE（model_input=false），放行待合规决议。训练继续 BLOCKED_DATA_NOT_READY。证据 `reports/t3_dir6_datascreen_20261002/REPORT.md`。

- 2026-10-02｜T3 autoresearch 启动｜用户确认前台、固定来源域交叉验证MSE降低20%；仅复用已批准OP2，17训练扰动逐个留出、全部500基因，基线0.00425821，目标约0.00340657；原val/test不参与优化。隔离仓库 artifacts/autoresearch/t3-20261002-v1，run_id=2da224cca360437983d20f16b8492be8；未生成候选、未提交/未评分，来源域改善不等同Gata4提升。
- 2026-10-02｜T3 autoresearch 实验1–4｜依次检验响应减半、增强GO拟合、按基因不确定性收缩和温和收缩；每次控制器独立测量并保留/回滚。前三项MSE分别变差0.45%、19.43%、1.25%；完整参数/实测保留于隔离仓库autoresearch-results，未生成提交候选。
- 2026-10-02｜T3 autoresearch 实验5–6｜温和收缩实际保留1.292%改善；功能邻居凸组合将改善提高到3.485%，继续检验非线性GO树集成。全部为固定17扰动开发交叉验证；参数与每轮保留/回滚见autoresearch-results。
- 2026-10-02｜T3 autoresearch 实验7–9｜PLS响应低维化及样本匹配校正未超过功能邻居3.485%改善；新分叉直接使用已批准GO全部术语的信息量相似度，未新增外部数据/未接触目标真值。每轮独立实测与回滚保留在控制器历史。
- 2026-10-02｜T3 autoresearch 实验10–12｜训练扰动内监督相似度学习变差并回滚；仅在GO高度相似时迁移的门控路线使MSE降低7.762%，已保留；继续检验更严格的相似性门。仍属反复选择后的开发指标，非独立验证/服务器收益。
- 2026-10-02｜T3 autoresearch 实验13–14｜可信邻居不缩幅将开发MSE改善提高到9.904%；读取实核的完整68910细胞E8.75 WT，提取27个扰动基因的状态表达/检测率作为新增特征，检验WT背景特征能否帮助未知扰动预测。无新增外部数据，来源/输入哈希见artifacts/t3_autoresearch_features_20261002/PROVENANCE.json；固定评估不变。
- 2026-10-02｜T3 autoresearch 实验15–17｜保守整合WT特征、训练折内部选择核函数均未超过9.904%并回滚；新路线用完整GO术语做稀疏多输出回归，所有特征筛选只在训练折，尝试恢复压缩表示丢失的功能信息。
- 2026-10-02｜T3 autoresearch 实验18–19｜完整GO浅层规则树仍未改善，回滚；下一分叉只用细胞组分/蛋白复合物GO注释做功能邻居，区分同一分子机器与泛功能相似。当前保留改善9.904%，目标20%尚未达成。
- 2026-10-02｜T3 autoresearch 实验20–21｜细胞组分GO路线实际保留10.850%改善；WT摘要预测响应幅度未胜而回滚；继续检验复合物邻居的集中程度。仍未达到20%，未生成/提交目标候选。
- 2026-10-02｜T3 autoresearch 实验22–24｜把供体响应方向与幅度分开后，开发MSE改善提高到11.362%；分子功能GO视角反而显著变差并回滚；继续比较平均/中位供体幅度以匹配MSE目标。无独立验证或服务器晋级声明。
- 2026-10-02｜T3 autoresearch 实验25–26｜平均供体幅度实际保留11.931%改善；低秩响应去噪未胜而回滚；新分叉在细胞组分核上拟合条件残差，比较学习效应与直接复制邻居方向。
- 2026-10-02｜T3 autoresearch 实验27–29｜更集中邻居、取消额外幅度收缩、按最近邻差距门控均未胜，已逐次回滚；保留11.931%改善。每轮参数与逐扰动MSE均保留于控制器日志，原val/test仍未用于选择。
- 2026-10-02｜T3 autoresearch 实验30–31｜幅度标准化后重新检验尖锐邻居仍未胜；完整68910细胞WT计算状态内相关，另取22471中胚层/心脏/间充质细胞生成新基因表示，无缺失panel基因；只以对照表达加权，未用KO响应造特征。来源哈希与观测性限制见CORRELATION_PROVENANCE.json。
- 2026-10-02｜T3 autoresearch 实验32–33｜状态内相关不能直接替代功能表示；把相关到响应的映射放在训练折学习后，改善小幅提高至11.946%。继续检验强正则的逐输出基因映射，固定开发指标与留出边界不变。
- 2026-10-02｜T3 autoresearch 实验34–35｜非线性高斯过程未超过保留结果并回滚；改为用7个可解释的GO/WT相似性视角学习供体可靠性，全部监督来自训练扰动对。最佳仍为11.946%开发改善，目标未完成。
- 2026-10-02｜T3 autoresearch 实验36–37｜浅层多视角可靠性模型未胜而回滚；新分叉学习正权重的GO/WT协方差组合及独立噪声，条件预测未知扰动。此前一次历史读取错误未产生实验/未改保留状态，已修复并经控制器status核对。
- 2026-10-02｜T3 autoresearch 实验38–39｜从已批准同一GSE261783原始哈希文件，仅按已批准身份提取220对照全基因表达；同源WT线性响应校正未胜，继续检验同源对照共表达邻居。无新增KO标签，原val/test不用；细胞/审查绑定见SOURCE_CONTROL_PROVENANCE.json。
- 2026-10-02｜T3 autoresearch 实验40–41｜GO信息量改用完整35640小鼠基因背景后改善12.084%；新分叉去掉重复祖先及泛核定位，只用最具体的蛋白复合物成员关系，避免把大类相近当作同一复合物。
- 2026-10-02｜T3 autoresearch 实验41–42｜具体蛋白复合物成员关系取得明显开发收益：MSE相对基线降低18.578%；继续去除覆盖超过1%小鼠基因的宽泛复合物词条，检验泛定位干扰。目标20%尚未达到，原val/test保持不用作选择。
- 2026-10-02｜T3 autoresearch 实验42–44｜过滤宽泛复合物词条后开发改善19.877%，仍低于20%不四舍五入宣称达标；无共享复合物回退均值未胜并回滚，继续检验按sample均衡的供体方向估计。
- 2026-10-02｜T3 autoresearch 实验45–46｜硬剔除零复合物重叠供体未胜并回滚；在明确改善的具体复合物表示上重新校准供体幅度（0.75→0.85），避免沿用旧弱表示的幅度假设。控制器按真实数值判定20%门，不改评分。
- 2026-10-02｜T3 autoresearch 实验47–48｜沿实测幅度方向检验更强收缩；进一步区分“同功能”和“同幅度”：对可信供体也把幅度部分收缩到训练扰动平均值，保留其方向，检验跨基因效应强度差异。所有参数变更仍由控制器独立计分。

### 2026-10-02 本地autoresearch逐次变更审计（控制器已完成）

- 2026-10-02｜本地实验01｜响应幅度减半；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验02｜降低GO回归正则；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验03｜按输出基因不确定性收缩；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验04｜温和收缩至0.75；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验05｜GO功能邻居凸组合；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验06｜GO特征树集成；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验07｜两个PLS响应方向；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验08｜按sample匹配对照后均衡响应；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验09｜完整GO信息量相似度；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验10｜训练扰动对监督相似度；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验11｜高可信功能近邻门控；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验12｜将近邻门提高到0.9；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验13｜可信供体保留完整幅度；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验14｜加入WT状态表达/检测率特征；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验15｜WT状态残差保守整合；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验16｜训练折内部选择核和收缩；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验17｜完整GO稀疏多输出回归；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验18｜完整GO浅层规则树；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验19｜细胞组分/复合物特异核；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验20｜WT摘要只预测公共响应幅度；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验21｜尖锐复合物邻居权重；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验22｜供体方向标准化及中位幅度；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验23｜分子功能特异核；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验24｜以平均供体幅度匹配MSE目标；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验25｜三个响应主成分去噪；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验26｜在复合物核上拟合响应残差；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验27｜中等集中复合物邻居；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验28｜取消额外幅度收缩；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验29｜最近邻差距决定迁移置信度；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验30｜标准化方向后重测尖锐邻居；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验31｜中胚层WT状态内共表达表示；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验32｜共享WT相关性到响应的校准；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验33｜逐输出基因强正则校准；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验34｜非线性高斯过程响应模型；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验35｜七视角线性供体可靠性；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验36｜七视角浅层非线性可靠性；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验37｜正权重多核协方差与噪声学习；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验38｜同源220对照的线性响应校准；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验39｜同源对照共表达邻居；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验40｜完整小鼠背景GO信息量；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验41｜最具体的蛋白复合物成员关系；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验42｜排除覆盖超过1%基因的宽泛复合物标签；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验43｜无共享复合物时回退普通均值；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验44｜样本均衡的复合物供体方向；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验45｜硬排除零重叠供体；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验46｜供体幅度系数0.85；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验47｜供体幅度系数0.65；回滚；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。
- 2026-10-02｜本地实验48｜可信供体幅度向训练平均值部分收缩；保留；本地来源域，非服务器结果。参数/计分/提交见 `reports/t3_autoresearch_20261002/EXPERIMENTS.tsv` 对应实验号。

- 2026-10-02｜T3本地目标完成｜48次实测，13保留/35回滚，冻结17扰动开发MSE 0.004258208→0.003393314（降低20.3112%）；锁定后val降低17.4561%、历史test降低6.1245%（4/6改善、区间跨零），未再调参。保留模型commit1b9847b，未生成候选、未提交/未评分，服务器现役不变。报告 reports/t3_autoresearch_20261002/REPORT.md；D-20261002-T3AR-001。

- 2026-10-03｜T3 autoresearch交付草稿v0069｜表达/形状/基因顺序/空间坐标检查通过，但母本layers/raw保护检查失败；保留未登记草稿和失败报告，不交付。仅修复参考元数据保留，下一新版本重新检查；模型与X预测不变。

- 2026-10-03｜T3 autoresearch补齐H5AD｜v0070，父v0009；锁定模型完整26条件推断重放，log残差加到完整7449×500 WT载体、截负及Gata4置零，坐标保留，contract PASS。已登记、未提交/未评分；源域20.31%不作为此H5AD目标分。D-20261003-T3ARDEL-001。

- 2026-10-03｜v0070服务器回分｜总分与五子项原样入库；REJECT、现役v0048不变、当前配置关闭。哈希/公式重放通过；来源均值MSE与目标矩阵评分脱节，零值激活/截负未被用作有效性门槛。D-20261003-T3ARSCORE-001；reports/t3_autoresearch_score_review_20261003/REPORT.md。

- 2026-10-03｜T3稀疏响应转换分叉｜预设strength=0.25；锁定来源模型不变，倍率[0.5,2]内求解、保留零结构；原17扰动LOPO实际矩阵五分项选强度，历史test只作锁定后检查。设计 reports/t3_sparse_response_20261003/DESIGN.md；未生成候选。

- 2026-10-03｜T3稀疏响应转换分叉｜预设strength=0.5；锁定来源模型不变，倍率[0.5,2]内求解、保留零结构；原17扰动LOPO实际矩阵五分项选强度，历史test只作锁定后检查。设计 reports/t3_sparse_response_20261003/DESIGN.md；未生成候选。

- 2026-10-03｜T3稀疏响应转换分叉｜预设strength=1.0；锁定来源模型不变，倍率[0.5,2]内求解、保留零结构；原17扰动LOPO实际矩阵五分项选强度，历史test只作锁定后检查。设计 reports/t3_sparse_response_20261003/DESIGN.md；未生成候选。

- 2026-10-03｜T3新候选v0071｜父v0048，来源完整矩阵LOPO选择strength=1.0，有界强度倍率、母本零值结构严格保留；7449×500、contract PASS、未提交/未评分。reports/t3_sparse_response_20261003/REPORT.md；D-20261003-T3SPARSE-001。

- 2026-10-02｜方向六补检索＋source冻结＋lane冻结｜researcher 补挖：sc-pert 23 行全表过筛，GSE92872（20 非黑名单基因）屏蔽过但小鼠单细胞成分过少暂缓集成，GSE157977 基因表未取到记 PENDING，Axin 系排除；source v1 冻结为 GSE261783（D-20261002-T3DIR6SRC-001）。lane 冻结见 `artifacts/t3_dir6/T3-DIR6-20261002-v1/DESIGN.md`（ridge 基线先行→单个图模型；双超门；比较轮不建候选）。下一步：实现阶段一。

- 2026-10-03｜v0071回分与半步分叉｜总分与五项原样登记、NOT_PROMOTED；固定新分叉strength 1→0.5，其余保持v0071方案，以v0048为母本；不根据历史test再次选参。reports/t3_halfstep_20261003/DESIGN.md；D-20261003-T3HALF-001。

- 2026-10-03｜T3新候选v0072｜父v0048，固定半步strength=0.5，有界强度倍率、母本零值结构严格保留；7449×500、contract PASS、未提交/未评分。reports/t3_halfstep_20261003/REPORT.md；D-20261003-T3HALF-001。

- 2026-10-03｜方向六阶段一完成（ridge 基线）：5 折全跑完，ridge MSE 0.05729 vs no-change 0.05545——5 折全部 ridge 更差（cos 0.009–0.111，方向信号≈0）。结论：GO 功能相似性对这批扰动响应几乎无预测力；bar 已立（no-change 0.05545），神经模型须双超才继续。阶段二锁定 GEARS（vendored＋ve-t3-six 环境验证通过；TxPert 不选；custom mouse GO 图先例见 priority-six）。脚本 `scripts/t3_dir6/ridge_baseline.py`；RESULT.json＋PROVENANCE.json 已落 run 目录；无候选无 INDEX。

- 2026-10-03｜v0072回分｜总分与五项原样登记、REJECT；分布恢复未抵消DE退步，现役v0048不变，当前半步试验关闭。D-20261003-T3HALFSCORE-001；reports/t3_halfstep_20261003/SCORE_REVIEW.md。

- 2026-10-03｜方向六阶段二开跑｜脚本 `scripts/t3_dir6/gears_stage2.py`（冒烟过；修：bar 复算须与阶段一同口径 macro 平均、GEARS 要稀疏输入、fold 目录须自带 gene2go_all.pkl，均 disclosed 先例复刻）。5 折×20 epochs CPU 后台跑（10h cap），同折同中心化 metric，回包按双门仲裁。run 目录 `artifacts/t3_dir6/T3-DIR6-20261002-v1/stage2/`。

- 2026-10-03｜方向六阶段二挂门，升级关闭｜GEARS 5 折×20 epochs 全跑完：mse_neural 0.05747 vs no-change 0.05545 vs ridge 0.05729——双挂（且比 ridge 还差一档）；修正后 cosine：ridge 0.178、GEARS 0.097（-0.111~0.28），方向信号皆弱。按冻结 STOP：图结构未带来增量，方向六升级关闭（保留线性结果备查）。诚实记录一次 metric bug：两轮 cosine 原按 pooled cell-level 点积/范数算，对 constant-per-gene 预测不是合法 cosine（曾报 1.293>1）；已写 `scripts/t3_dir6/recompute_cos.py` 用 saved 模型重算 per-gene-mean cosine 并回填两 RESULT（MSE 原样， verdict 不变）。`D-20261003-T3DIR6CLOSE-001`。
- 2026-10-06｜T3 六新路线实现完成｜v0075(o1_dual_form sm0.25_sa0.5)、v0076(o2_gate_mult s0.5)、v0077(o3_shrunk_beta k2.0)、v0078(n1_nmf_ablation s0.25)、v0079(n2_marker_gate s2.0)、v0080(n3_switch_emit s0.5)；父v0048、contract PASS、score_pending、未提交/未评分；v0073/v0074 O1 重试副本已标 invalidated_unsubmitted；设计 reports/t3_six_routes_20261006/DESIGN.md。
- 2026-10-07｜T3 六新路线交付包｜deliveries/t3six__t3__upload__20261006.zip（6 成员，v0075–v0080，SHA 对 INDEX 核验通过）；READY_NOT_SUBMITTED；receipt 同目录；v0073/v0074 副本不打包。
- 2026-10-07｜T3 六新路线回分｜v0075=46.73、v0076=47.31、v0077=47.43、v0078=47.93、v0079=47.40、v0080=46.82；对照现役v0048=47.93：v0078 同分平局带内现役留下，其余5个 NOT_PROMOTED，六路线无一晋级；INDEX/registry 已回填 score_pending 清零；D-20261007-T3SIXSCORE-001；reports/SERVER_SCORE_REGISTRY.md#t3-six-score-return-20261007。
- 2026-10-07｜T3 第二波六新路线实现完成｜v0081(o1_hnmf 现役⊕v0078等权)、v0082(o2_pnmf hurdle门×NMF)、v0083(o3_psb 门×收缩×乘法)、v0084(n1_qtl q0.25 分位数形状迁移)、v0085(n2_dsign g0.5 供体符号门)；n3_pswap 源侧关闭（identity 秩最优，无正信号，不交付）；父v0048、contract PASS、score_pending、未提交/未评分；设计 reports/t3_six_routes_20261007/DESIGN.md；交付包 deliveries/t3six2__t3__upload__20261007.zip（5 成员，READY_NOT_SUBMITTED）。

## 2026-10-09 追加

- 2026-10-08｜T3 v0083–v0088 回分与晋级｜v0084 重建 q0.25=49.55 晋级、v0086 arank r2=49.34 REJECT、v0087 embhurdle_v2=53.42 晋级、**v0088 condhurdle=53.69 晋级为现役**（+0.27 vs v0087）。五项子项 de 41.7 / dir 51.2 / sev 75.2 / mmd 51.1 / vario 43.1。registry 已登记，T3 待分清零。
- 2026-10-09｜T3 本地重训完整复现｜从 research/t3_20261008 公开代码重建：GEO 12/12 源哈希通过、8/8 注释 TSV 逐字节、GO embedding 重建逐字节（a81ff9a5）、8 个归一化面板 frozen_merge_matches（含已知 690 个缺失 WT barcode）、模型拟合 REBUILT_EXPRESSION_EXACT，v0087/v0088 表达式哈希与 state_emitter.joblib / generic_response.npz / expected_donor_rows.npy 全部逐位复现。据此 PUBLIC_REBUILD_FOLLOWUP.md 的"完整拟合未验证"限制可撤销，公开 clone 不再需要私有 cache。基线复合分与归档 summary 最大绝对差 0.0。
- 2026-10-09｜T3 发射器成分轴判定饱和｜14 次单轴迭代（propensity_penalty / propensity_min_cells / composition_clip / detection_offset / zero_frac_scale），最好 propensity_penalty=0.2 仅 +0.0034（噪声级）且不单调（0.15/0.2/0.3 = +0.0016/+0.0034/+0.0003）；de_skill 在全部变体中变化恰为 0，说明发射器只重分配已激活细胞、不能改变 DE 集合；三个轴为精确 no-op；检测比例轴 ±10% 损失约 2.08、−50% 损失 1.71，冻结值在窄峰。**结论：不建议提交任何变体；T3 本地源侧指标不再是有效目标。** 服务器现役 v0088 不变。证据 reports/t3_rebuild_20261009/REPORT.md、autoresearch/loop-261009-1450/。
- 2026-10-09｜T3 提交额度 OPEN｜registry 记 2026-10-08 v0088 用尽当日 T3 用量 8/8 并声明无剩余授权；本日 T3 无提交记录，当日额度是否已重置未观测。标 OPEN，不宣称可用，需用户确认。blocks_submission:false。
