# T3 任务追踪：gene perturbation

更新时间：2026-09-21

分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。本文件明确区分已评分路线和待验证路线。

## 当前状态（2026-09-21）

- selection保持v0009/v0010。R1 v0026/v0027均与各自父版本总分相同；R2 v0030/v0031均低于父版本。详见权威分数登记。
- R5 v0032/v0033未提交/未评分；R6新规则已生效、26条件重新审查通过，三件套READY_FOR_R6_TRAINING，预测器训练NOT_RUN。

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
