# Bioinformatics data index summary

更新时间：2026-09-01

本索引覆盖当前工作区中的 9 个 challenge H5AD、5 个官方 board gene panels、官方 board `index.json`、官方 T1 released-stage composition JSON，以及随官方 `veckit` scorer 落盘的 6 个 tutorial sample H5AD。另登记了从 `/home/huyudi/006/data` 和实际存在的 `/home/huyudi/013_spatial/data` 接入的 7 个只读辅助目录链接。完整逐条记录见 [INDEX.tsv](INDEX.tsv)，辅助链接的来源、用途和许可边界见 [data/external/INDEX.tsv](../../data/external/INDEX.tsv)。

challenge/scorer 的文件行使用当前落盘文件 SHA-256；辅助目录是符号链接，不伪造内容哈希，标记为 `not_applicable_symlink`。

Batch 2 B2-T3-A1 的外部数据审计已登记：E-MTAB-6967 sanitized WT MatrixMarket（108,857 cells，保留 0 forbidden records）、GSE52123 两个 WT GATA4 ChIP replicate 与 matched input、NCBIM37 技术坐标映射、GO/Reactome 模块资源，以及两个固定 commit 的方法源码 provenance。E-MTAB-11763 当前只有 2,820 行 metadata，processed snapshot 不可用，未使用 raw FASTQ，明确标为 metadata-only fallback。B2-T3-A1 的目标数据未进入生成；完整 permit 和文件哈希见 `infra/external_data/AUDIT_COMPLETE.json`。

T3-S1-PRIOR 新增两类外部知识快照：CollecTRI Zenodo record 8192729 v2.0 的原始 `CollecTRI_regulons.csv`（CC BY 4.0，MD5 与官方记录一致），以及通过 OmniPath 官方 interactions API 获取的 mouse taxon 10090、T3 500-gene panel-scoped CollecTRI/OmniPath TSV。前者保留为 human raw reference；后两者各自带 `snapshot_manifest.json`，记录查询参数、panel 哈希、gene-symbol mapping、directed-edge 数、bytes 和 SHA-256。它们是已审计的外部知识组件，不等于完整数据库，也尚未单独形成 β-catenin 生物学结论。

## Challenge data

E6.75、E7.25、E8.0、E8.25_late、E8.75、E9.5、E8.5_RNA、E9.5_RNA 和 E9.5_mab21l2_ko 均已通过 AnnData 可读性、panel/schema、表达值 finite/non-negative 检查；空间数据的 `spatial_3D` 均为 `n_obs × 3` 且 finite。E8.0 的原始 500 genes 与官方 498-gene T2 embryo board 的交集完整，额外基因为 Casp4、Pnliprp1。

这些 challenge 文件是用户补充或保留在工作区的 release 文件，本索引不把它们宣称为官方 byte-identical。用户已再次人工确认 E8.25_late 官方下载为 225 MB；本地为 225,091,568 bytes，且通过结构校验。官网公开 handoff 页面仍显示 288 MB，作为页面版本差异保留记录，但不再阻塞当前资源闭环。其他已落盘 challenge 文件通过结构校验，但没有公开 release checksum/manifest。

官方 panel 文件均已从官网端点下载并与工作区原有文件逐字节比较，5/5 为 IDENTICAL。官方 `index.json` 通过 board/panel/cell-limit/required-`obsm` JSON 检查；`t1_composition.json` 只描述 E8.5/E9.5 released stages，不含 held-out target。

## Official scorer samples

6 个 sample 文件来自 `aristoteleo/veckit` commit `46d41e63f42a9aab815db20b742feeccd249cb17`，仅用于官方 scorer/tutorial smoke，不属于 challenge hidden target，也不应混入训练数据。此前 T1/T2/T3 scorer sample smoke 均返回 JSON metrics；两个本地 notebook 均通过 JSON 完整性检查，baseline notebook 的核心纯 Python 函数也已在临时 H5AD 上通过 smoke。

## Provenance boundary

本索引记录文件身份和当前结构校验，不替代官网登录下载、官方 release manifest 或 leaderboard validation。任何 scored submission 前仍需通过 board-aware validator，并保留 E8.25 provenance 记录。

新增的 7 个辅助链接均为 `model_input=false`，不进入 challenge 训练、调参或榜单提交；它们只保留用于空间/标签/扰动数据的技术 smoke。006/013_spatial 中未检测到可直接替代 Virtual Embryo challenge 数据的 E8.25/E8.75、KO 或官方 gene-panel 资源。`outputs/t2_controls/` 仍仅为基于已索引 pseudo-target 的 audit-only 派生文件。

## T3-S1A external-data and method deployment (2026-08-31)

已登记 Extended Mouse Atlas 官方 supplemental archive：26,307,535,907 bytes，官方 MD5 `442645308463a64c3bb947c25921199e`，并保留 archive tree、publication 和 checksum cache。归档中的 `embryo_complete.h5ad` 为 `430339×27669`，使用 `.raw.X`；metadata-first 防火墙保留精确 `E8.75` 的 68,910 行，使用 `celltype_extended_atlas` 作为 state。sanitized 输入已写入 `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5/`，完整文件身份和哈希见 [INDEX.tsv](INDEX.tsv)。

Atlas 注释中有 5 个 panel symbol 不直接出现在 `mgi_symbol` 列，但均通过官方 annotation 页面精确回连到现有 Ensembl gene identity：`Bex3→Ngfrap1→ENSMUSG00000046432`、`Ccn5→Wisp2→ENSMUSG00000027656`、`Cemip2→Tmem2→ENSMUSG00000024754`、`Cnmd→Lect1→ENSMUSG00000022025`、`Selenop→Sepp1→ENSMUSG00000064373`。映射 manifest 绑定 panel/metadata SHA，不减少 500-gene panel。

新增全 mouse taxon 10090 OmniPath（31,384 rows）和 CollecTRI（39,849 rows）TSV snapshot，均通过 schema、license、mapping、bytes/SHA256 审计；新增 CellOracle 0.22.0 的 mm10 promoter base-GRN（29,308×1,096，SHA256 `32de319419199f53bbdbf7c8545394a70052c7d14918d59b54c96593000dea40`），已通过本地 loader smoke。`genomepy` 0.16.4、scTenifoldNet 1.4、scTenifoldKnk 1.1、R 4.5.1 和 Matrix 1.7.3 的部署锁已落盘。

T3-S1A v5 实际运行状态为 `BLOCKED_RUNTIME`：输入审计和 state join 通过，CellOracle Gata4 real API 已产出 votes/state-sampling；Gata6/Ctnnb1 的 exact-stage full matrix propagation 在 bounded observation window 内未完成，scTenifold 与 route gate 未在该 atom 启动。无候选、H5AD、scorer、服务器提交或 leaderboard 结论；`blocks_submission: false`。历史 v1-v4 partial artifacts 均保留且不可覆盖。

## T3-S1D independent perturbation evidence (2026-09-01)

在用户授权下新增两个官方 GEO processed 文件，均放入 quarantine，不下载 raw 数据，也不作为 challenge 输入：GSE156307 的 Gata4 E14.5 胚胎胃部条件敲除表达矩阵（22,906×15，SHA256 `aefee8cfe37d436faf70795240d957d0acb3a04a9aa89e22e9b33dbc134ab46b`），以及 GSE255237 的 Gata6 E11.5 outflow tract NormCounts（14,732×9，SHA256 `91e295db3e51c200a8dbba2480322ccfae87ac0b708803c82516d470b2c97023`）。

处理后描述性审计显示：GSE156307 的 Gata4 cKO 相对 HS control 的 log2FC 为 `-1.1839`（5 个 cKO 样本方向一致）；GSE255237 的 Gata6 MUT 相对 WT 的 log2FC 为 `-0.3362`（4 个 MUT 样本方向一致）。两者均为 E8.75 之外的组织/阶段，保留为 context-only，不能解除 E8.75 candidate gate。GSE255237 官方系列设计描述为每个基因型 3 个 pools，但处理文件实际出现 4 个 MUT 与 3 个 WT 列，计数冲突已保留在证据记录中。

GSE67463、GSE50859、GSE70134 目前仅登记官方 metadata，未下载 processed/raw 文件；它们同样不计入 E8.75 independent signed family。完整文件身份与状态见 [INDEX.tsv](INDEX.tsv)，效应和 gate 见 `artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1/`。

在用户授权下继续补齐 E8.0-E9.5 目标扰动证据：新增 GSE5298（45101×8，Gata4，E9.5 AVC）、GSE9652（45101×11，Gata4，E9.5 pooled heart）和 GSE78125（35556×24，Ctnnb1，E9.5 AHF mesoderm）官方 series matrix，以及 GPL1261/GPL6246 官方 annotation。所有文件 gzip/矩阵结构、GSM 列身份、平台探针映射和 SHA256 均通过；Gata4 对应 GPL1261 的 2 个探针（Entrez 14463），Ctnnb1 对应 GPL6246 的 1 个探针（Entrez 12387）。

S1D v3 的描述性效应为：GSE5298 Gata4 `+0.02084`（linear-expression log2 ratio，target probe down fraction 0.50；排除 target 后 panel 373 down/108 up），GSE9652 Gata4 `+0.25275`（0.40；206 down/275 up），GSE78125 Ctnnb1 `-0.02584`（RMA Δlog2，0.50；272 down/219 up）；多探针按样本内 median 聚合。两份 Gata4 与一份 Ctnnb1 是早期、组织限定的 direct-perturbation context，但不等同于 E8.75 state-matched activity；target expression 仅作 descriptive readout，未计入 signed family。当前 gate 仍为 `HOLD_EXACT_STAGE_CONTEXTUAL_ACTIVITY_NOT_STATE_MATCHED`，independent signed family `0`，无候选、无 scorer、无服务器提交，`blocks_submission: false`。v3 artifact stable manifest SHA256 为 `6c2806aa381f099e3db88f38a35278d4500e1aeb1f8de7fe3cfa20e2db487e0c`；v2 初步原子保留但不作为当前复用版本。

## 2026-09-20 存储注记（结构整理 P2，用户定保留）
- `infra/external_data/quarantine/`（~51G）与 `sanitized/`（~7G）保留：外部原始数据，已索引（本 INDEX 含 quarantine 路径引用 21 处），删除前必须先 re-index；用户未授权删除。
- 同期清理（见 `reports/DELETION_MANIFEST.tsv`）：tool_integration S1A 旧版 v1–v6、outputs/t2_*、g0 重复副本/训练件、v0002 孤儿副本；scored 产物、INDEX、git 历史均未触碰。

## 2026-09-20 T3 新路线输入引用修正
三个 exact E8.75 WT 当前输入索引由已清理 v5 改指实际存在的 `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data/`；三文件 SHA256 已按 v7 MANIFEST 实际重算通过。原始 MatrixMarket 是 genes×cells（27,669×68,910），建模时转置；不是新增外部数据，也不解除 S1 科学 gate。执行证据见 `artifacts/t3_next/` 的 r4/ATLAS_PERMIT.json。
