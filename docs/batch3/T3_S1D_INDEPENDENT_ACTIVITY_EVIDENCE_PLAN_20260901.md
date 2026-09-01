# T3-S1D 独立 biological activity/stability 证据线方案

版本：2026-09-01  
atom：`T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3`（v1/v2 历史原子保留）  
父版本：`T3-S1A-STATE-JOIN-20260901-v7`  
关联组件：`T3-S1B-STATE-JOIN-20260901-v3`
状态：`COMPLETED_WITH_HOLD`；已获得三个 E9.5 exact-stage、组织限定的 processed perturbation context，E8.75 matched activity 仍 `NOT_IDENTIFIABLE`

## 目标

按缓存优先寻找能够支持 Gata4/Gata6/Ctnnb1 activity 或 stability 的独立生物学证据，重点核对真实扰动、胚胎阶段、样本/生物学重复、响应读出和可审计原始来源。该 atom 不把公共网络知识、WT-only 表达、技术拆分或同一数据的再分析当作独立验证。

## 独立性与最低证据条件

- 必须能定位 accession/DOI/原始记录、样本 ID 或 replicate、物种/基因型/扰动、阶段和 assay/readout。
- 能支持 signed biological claim 的证据需有与目标相关的实际 perturbation/contrast；只有 binding、motif、pathway membership 或 target expression 的记录只能标为 contextual/supporting。
- 同一研究的技术重复不自动等于独立 family；同一原始数据的不同模型/数据库转换不计为独立 family。
- 保留 exact gene identity、condition、stage、sample coverage、raw/processed availability、license 和 SHA256；不因缺失而填补或推断 sign。

## 执行阶段与停止边界

1. **Cache inventory**：先查 `infra/bioinf-data-index/`、已有 quarantine/sanitized snapshots、官方同步记录和 batch2/batch3 manifests。
2. **Targeted retrieval**：缓存不足时只检索最小的 primary source metadata/processed object；大规模 raw download 需单独记录许可、容量和用途，不先下载整库。
3. **Evidence audit**：建立逐 accession 的 inclusion/exclusion 表，区分 `DIRECT_PERTURBATION`、`RESPONSE_REPLICATE`、`CONTEXTUAL_ONLY`、`METADATA_ONLY`、`NOT_IDENTIFIABLE`。
4. **Integration decision**：只有至少两个相互独立且有 signed biological support 的 family，并通过 stage/condition/replicate、冲突和 leave-one-family-out 审计，才可提交“候选前 gate 再评估”；否则保持 `HOLD`。

## 禁止事项

- 不用 Extended Mouse Atlas WT、E-MTAB-6967 WT、GSE52123 GATA4 ChIP 或 CollecTRI/OmniPath 快照冒充目标 KO activity。
- 不把 S1C 的 target compatibility、接口 smoke 或网络方向当作 S1D 的独立 activity 证据。
- 不生成候选、不写 H5AD、不运行 scorer、不提交服务器；若新增外部数据，交付前更新 `infra/bioinf-data-index/INDEX.tsv` 与 `SUMMARY.md`。

## 预期输出

输出 evidence inventory、source/accession manifest、样本与重复审计、独立性判定、证据等级、缺口、检索日志/缓存 hash 和 completion report。缺少 exact perturbation 或 replicate 时，结论必须明确为 `NOT_IDENTIFIABLE`，并标注 `blocks_submission: false`。
本次执行结果：GSE156307 与 GSE255237 的 processed 文件已下载至 quarantine 并完成 hash、样本列、靶基因和描述性方向审计；GSE67463、GSE50859、GSE70134 仅完成 metadata inventory。新增文件已登记到 `infra/bioinf-data-index/INDEX.tsv` 与 `SUMMARY.md`。由于阶段/组织不匹配，未将两份表达方向计入 E8.75 independent signed family，未生成候选、未运行 scorer、未提交服务器。

## v3 exact-stage evidence closure（2026-09-01）

在不覆盖 v1/v2 的前提下，v3 使用冻结 contract `docs/batch3/T3_S1D_EXACT_ACTIVITY_EVIDENCE_CONTRACT_20260901_v3.json`，审计 GSE5298、GSE9652、GSE78125 的官方 series matrix 和 GPL1261/GPL6246 官方平台注释。输出目录为 `artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3/`，包含逐 GSM `sample_qc.tsv`、`mapping_qc.tsv`、`gene_effects.tsv`、`study_evidence.tsv`、运行清单和 stable manifest；stable manifest SHA256 为 `6c2806aa381f099e3db88f38a35278d4500e1aeb1f8de7fe3cfa20e2db487e0c`。

Gata4 有两个独立早期心脏组织 family，Ctnnb1 有一个早期 AHF family，Gata6 仍无 exact processed perturbation family。GPL1261 的 Gata4 多探针按样本内 median 聚合；target expression 不作为功能 gate。矩阵完整性和 probe/Entrez mapping 为 `PASS`，但三项均是组织/状态限定的 E9.5 context，不能转写成 E8.75 signed activity；v3 gate 为 `HOLD_EXACT_STAGE_CONTEXTUAL_ACTIVITY_NOT_STATE_MATCHED`，independent signed family 为 `0`，`blocks_submission: false`。下一步仍是获得或授权收窄一个真正 state-matched、可复现的 signed-family 验证；在此之前不生成候选、不运行 scorer、不提交服务器。
