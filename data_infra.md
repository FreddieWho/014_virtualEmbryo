# data_infra — 跨任务数据资源索引

更新：2026-09-20。用于 T1/T2/T3 查找已收录的数据、共享基础资源和候选来源。

**资源可以共享查找和存储，使用许可必须按 task / board / 用途分别判断。** “已下载”“结构检查通过”“已在某个 task 使用”都不等于其他 task 可以训练。下表记录已有用途，不新增授权。

本文件是按数据源组织的人工入口；逐文件路径、SHA256 和状态仍以 [生信文件索引](infra/bioinf-data-index/INDEX.tsv) 为准，不另复制一份哈希账本。历史用途来自现有登记，本次没有重新验收历史数据。

## 1. 官方数据与基础文件

| 资源 | 本地入口 | 当前登记用途 | 共用边界 |
|---|---|---|---|
| E6.75 / E7.25 / E8.0 MERFISH | [data/](data/) 中对应阶段 H5AD | T2 embryo 训练 | 按官方任务契约使用；不自动改作其他 board 的外部数据 |
| E8.25_late / E8.75 / E9.5 MERFISH | [data/](data/) | T2 heart 训练；E8.75/E9.5 另作 T3 WT 参考 | 同一个文件可有不同任务角色，须分别保留角色记录 |
| E8.5_RNA / E9.5_RNA | [data/](data/) | T1 训练 | 不混同 MERFISH 文件或阶段标签 |
| E9.5 Mab21l2 KO | [E9.5_mab21l2_ko.h5ad](data/E9.5_mab21l2_ko.h5ad) | T3 官方训练扰动 | 不是 Gata4 KO 真值；不能作错靶验证 |
| 各 board gene panel / index | [gene_panel/](data/gene_panel/) | 各 task 的基因集合与顺序检查 | 必须选择对应 board，不能统一套用一个 panel |
| 官方 T1 composition | [t1_composition.json](data/reference/t1_composition.json) | T1 已发布阶段组成元数据 | 不代表隐藏阶段组成 |
| veckit tutorial 数据 | [third_party/veckit/data/](third_party/veckit/data/) | 官方示例与工程检查 | tutorial 通过不等于正式任务验证 |

契约入口：[task_contracts.yaml](docs/_starter_pack/config/task_contracts.yaml)；官方缓存与变化：[OFFICIAL_SYNC.md](reports/OFFICIAL_SYNC.md)。

## 2. 发育图谱、调控与通路资源

| 数据源 | 本地入口 | 当前状态/用途 | 其他 task 复用要求 |
|---|---|---|---|
| E-MTAB-6967 WT 胃胚图谱 | [EMTAB6967/](infra/external_data/sanitized/T3/B2-T3-A1/EMTAB6967/) | 已登记 T3 B2-T3-A1 的 WT 模型输入；108,857 细胞 | 有潜在 T1/T3 用途，但现有净化产物的许可是任务限定的；T2 需额外阶段窗口审查 |
| E-MTAB-11763 | [EMTAB11763/](infra/external_data/sanitized/T3/B2-T3-A1/EMTAB11763/) | 当前登记为 metadata-only；不是可训练表达矩阵 | 不把 metadata 收录当成矩阵已到位 |
| ExtendedMouseAtlas / exact E8.75 WT | [原始资料](infra/external_data/quarantine/T3-S1A-STATE-JOIN/ExtendedMouseAtlas/)；[v7 净化输入](artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data/) | T3 WT 状态背景；v7 输入 68,910 细胞、27,669 基因 | 优先看净化输入与原 permit；原始归档不直接接入新任务模型 |
| GSE52123 WT GATA4 ChIP | [GSE52123/](infra/external_data/sanitized/T3/B2-T3-A1/GSE52123/) | T3 promoter directness；两个 ChIP replicate 与 input | 是 WT binding，不是敲除响应；含 E12.5 材料，不自动跨任务使用 |
| NCBIM37/mm9 GTF | [MM9_GTF_RELEASE67/](infra/external_data/sanitized/T3/B2-T3-A1/MM9_GTF_RELEASE67/) | 技术坐标映射 | 核对基因组版本、许可与用途 |
| GO / Reactome | [GO/](infra/external_data/sanitized/T3/B2-T3-A1/GO/)；[REACTOME/](infra/external_data/sanitized/T3/B2-T3-A1/REACTOME/) | 已登记 T3 通路/模块背景 | 可考虑跨 task 的 ontology 用途；保留版本、来源和独立许可 |
| CellOracle mm10 promoter base-GRN | [promoter_base_GRN/](infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN/) | 固定版本 motif 拓扑资源，已有 T3 使用记录 | 拓扑不是扰动方向证据；核对物种、基因组与原始来源 |
| CollecTRI / OmniPath | [COLLECTRI/](infra/external_data/sanitized/T3-S1A-STATE-JOIN/COLLECTRI/)；[OMNIPATH/](infra/external_data/sanitized/T3-S1A-STATE-JOIN/OMNIPATH/) | 已审计 T3 外部知识组件；另有 panel 子集 | 不能把聚合知识、generic signaling 表当作已审查的完整 ligand–receptor–target 链 |
| 基因别名资料 | [panel_gene_aliases.json](infra/external_data/manifests/T3-S1A-STATE-JOIN/panel_gene_aliases.json) | T3 panel 标识映射 | 可复核后用于其他任务；别名映射不等于人鼠同源映射 |
| CellOracle / scTenifoldKnk 源码快照 | [B2-T3-A1/](infra/external_data/sanitized/T3/B2-T3-A1/) 中对应目录 | 方法 provenance | 源码许可与生物数据许可分别检查；源码不是预训练模型 |

历史审查入口：[AUDIT_COMPLETE.json](infra/external_data/AUDIT_COMPLETE.json)；更细的资源说明：[生信汇总](infra/bioinf-data-index/SUMMARY.md)。

## 3. 新收录的扰动与细胞通讯资源

本组全部为 **未批准训练 / model_input=false**。`quarantine` 内的资料仅可按规则做元数据检查、明确过滤和结构核验。

| 数据源 | 已收录内容与位置 | 任务关注点 | 当前限制 |
|---|---|---|---|
| GSE261783 小鼠心脏成纤维细胞 | [原始两个静息样本](infra/external_data/quarantine/T3-NEXT-R56-20260920/raw/)；[过滤后原始计数](infra/external_data/quarantine/T3-NEXT-R56-20260920/filtered/GSE261783_OP2_resting_provisional_raw.h5ad) | T3 R6 优先候选；5,454 细胞、26 个候选扰动，另含 220 对照细胞；32,287 基因，panel 500/500 | 8 周龄、非胚胎；逐扰动近似表型与用途审查未闭合；未经归一化/训练；其他 task 尚未审查 |
| ConnectomeDB2025 | [小鼠 JSON](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/connectomedb_mouse.json)；[引用卡片](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/lr_cards/) | T3 R5；也可作为跨 task 的关系资源候选；3,252 对，其中 panel 内 37 对 | 许可表述冲突；含物种推断和接触/黏附关系；没有完整下游 target；原文逐条审查未完成 |
| CellPhoneDB v5 | [相互作用表](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/cellphonedb_interactions.csv)；[受体—TF 表](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/cellphonedb_transcription_factor.csv) | T3 R5 / 通讯资源候选；2,911 条相互作用、212 条受体—TF | 人类来源；软件许可不能替代数据许可；TF 活性不能直接当作靶点表达响应 |
| Whole-brain CRISPR atlas | [基因表](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/brain_features.tsv.gz)；[UCSC 版本元数据](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/brain_ucsc_combined.json) | T3 R6 备选；当前核查版本 panel 483/500 | **只有 metadata**；逐细胞审查与大矩阵下载未做；脑与胚胎心脏上下文不同 |
| Replogle 2022 | [Figshare 文件/许可目录](infra/external_data/quarantine/T3-NEXT-R56-20260920/metadata/replogle_figshare.json) | 通用 Perturb-seq 备选 | **只有 metadata**；人鼠同源映射、条件过滤、panel 覆盖尚未完成；未下载单细胞矩阵 |

详细来源 URL、许可证、候选排名和缺口：[来源清单](reports/t3_data_intake_20260920/SOURCE_SHORTLIST.tsv)。实际下载/派生清单：[COLLECTION_MANIFEST.json](reports/t3_data_intake_20260920/COLLECTION_MANIFEST.json)。本组 permit：[TASK_DATA_PERMIT.json](reports/t3_data_intake_20260920/TASK_DATA_PERMIT.json)；收集报告：[REPORT.md](reports/t3_data_intake_20260920/REPORT.md)。

## 4. 其他项目本地数据：可查找，不等于本项目已接入

`/home/huyudi/006/data` 是已有原始库，本项目按只读来源处理；不复制整库或修改原文件。目录级盘点见其 `README.md`、`file_inventory.tsv` 与各 `*_detailed_report.md`，旧盘点的数量需以真实文件为准。

| 来源 | 本地位置 | 本项目当前核查/用途 |
|---|---|---|
| Dixit / GSE90063 | `/home/huyudi/006/data/perturb_seq/GSE90063/` | 已查小鼠 DC guide/基因/细胞 metadata；两个条件分别匹配 320/500、341/500 panel（别名审计前），不直接满足当前 R6 |
| Norman / GSE133344 | `/home/huyudi/006/data/perturb_seq/GSE133344/` | CRISPRa/组合干预；已读 guide metadata，未当作 KO 训练输入 |
| GSE193736 | `/home/huyudi/006/data/perturb_seq/GSE193736/` | ORF 过表达/OverCITE-seq；与当前 R6 干预类型不匹配 |
| GSE306429 | `/home/huyudi/006/data/perturb_seq/GSE306429/` | 药物扰动；不能直接当成单基因 KO |
| X-Atlas-Orion | `/home/huyudi/006/data/perturb_seq/XAtlas/` | 人类 HCT116/HEK293T；本项目已有只读技术链接；未读表达列或借用 response embedding |
| CellPhoneDB 本地副本 | `/home/huyudi/006/data/lr_interaction/cellphonedb-data/` | 已核查来源表结构；使用前与固定在线版本核对 |
| TF regulon / pathway 库 | `/home/huyudi/006/data/tf_regulon/`、`/home/huyudi/006/data/pathway/` | 目录已定位，具体资源尚未完成本项目准入；不标为可用模型输入 |
| 006 / 013 的空间数据辅助链接 | [data/external/INDEX.tsv](data/external/INDEX.tsv) | 7 个只读技术辅助链接：胎肝 Visium HD、人肝 MERFISH、XAtlas、ccRCC Visium、USZ TLS、CRC CMS、HTAN CRC；全部 model_input=false |

## 5. 保留但不可当作共享训练数据的材料

[T3-S1D 隔离目录](infra/external_data/quarantine/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE/) 中保留 GSE156307、GSE255237、GSE5298、GSE9652、GSE78125 及探针注释。其涉及 Gata4/Gata6/Ctnnb1 扰动的历史审查语境，**不得因为已经收录而加入新的训练、embedding、统计背景或共享 prior**。用途重新获准前保持隔离，历史科学 gate 不变。

## 6. 新任务复用与后续登记

1. 从本页找到资源，再核对文件索引和实际文件。区分原始数据、净化数据、metadata-only、技术辅助、隔离材料。
2. 为目标 task/board 写独立用途与 permit：阶段、物种、基因型、扰动组合、phenocopy、许可、预训练语料来源都要覆盖。原任务的 permit 不自动继承。
3. 需要不同过滤时，新建任务专属产物和过滤回执；共享不可变原始来源，不能通过软链接绕过许可。
4. 仅在准入完成后改变 `model_input`。未知用途标为“未审查”，不要写成“允许”，也不要把一个 task 的禁止条件泛化成所有 task 永久禁用。
5. 新增来源或状态变化时，更新本页对应资源行和 [文件索引/汇总](infra/bioinf-data-index/SUMMARY.md)；新增 task 使用另加 permit 指针。来源、许可、哈希、过滤回执不只留在某次对话中。

防火墙：[DATA_FIREWALL_SPEC.md](docs/batch2/compliance/DATA_FIREWALL_SPEC.md)；任务禁区：[规则快照](docs/batch2/03_COMPLIANCE_RULES_SNAPSHOT_20260829.md)；扰动黑名单：[target_leakage_blacklist.tsv](docs/batch2/compliance/target_leakage_blacklist.tsv)。

## 2026-09-20：T3 R5/R6 第二轮准备

[准备报告](reports/t3_r56_readiness_20260920/REPORT.md)：GSE261783新增4998×32287隔离派生文件，23候选扰动、220对照、500基因唯一映射。输入输出身份见该目录PREPARATION_RECEIPT.json和生信INDEX。旧5454细胞文件保留为历史隔离输入；新旧文件不是可合并的独立样本。R5完整批准链为0，R6逐扰动审查/书面用途确认未闭合，均不能作为其他task的自动许可。

## 2026-09-20：R5最小来源已获项目范围许可

SIGNOR 4.0（CC-BY4.0）缓存及原始论文/同源映射元数据已入索引。仅 `infra/external_data/sanitized/T3-R5-SIGNOR-MINIMAL-20260920/edges.tsv` 的1条LRT允许T3:gata4按通路结构使用；4条源边逐项审查，5节点一对一映射，外部方向/幅度/表达数值未进入模型。原始全网络仍隔离，不授予R6或其他任务许可。源证据与permit见 `reports/t3_r5_completion_20260920/SOURCE_MANIFEST.json`、`FILTER_RECEIPT.json`。R5已实际运行并生成两候选（未提交/未评分）。

## 2026-09-21：R6正式开工输入

按新生效T3政策完成26条件审查。GSE261783本次选中5454细胞/26扰动/220NTC；恢复Chd4/Smarca4/Yy1基于实际成人来源背景的重新审查，不是自动恢复或全基因全场景许可。新派生包 `infra/external_data/sanitized/T3-R6-OP2-20260921/` 含5454×500 lognorm表达、27×80 WT-only特征及27×27邻接矩阵。来源permit与哈希见 `reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json`；旧5454/4998隔离件均保留，彼此不是独立新增样本。仅T3:gata4范围获准，其他task需独立审查；R6预测器训练NOT_RUN。
