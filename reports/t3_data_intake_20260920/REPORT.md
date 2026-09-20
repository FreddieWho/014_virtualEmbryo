# T3 路线 5/6 数据收集与准入结果

日期：2026-09-20。路线 3/4 的优化已写入根目录 TODO，本次未执行修复或训练。

**已收集到路线六优先候选的真实矩阵，并完成隔离过滤；路线五已收集可追溯的关系资料，但两条路线目前均无正式训练许可。** 数据收集完成不等于合规准入完成。来源比较见 [SOURCE_SHORTLIST.tsv](SOURCE_SHORTLIST.tsv)，任务级限制见 [TASK_DATA_PERMIT.json](TASK_DATA_PERMIT.json)。

## 路线六：优先保留小鼠心脏成纤维细胞 Perturb-seq

原始研究：[Aguado-Alvaro et al., Nature Communications, DOI:10.1038/s41467-025-66597-9](https://doi.org/10.1038/s41467-025-66597-9)。总系列为 GSE261742，真正的单细胞子系列是 [GSE261783](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE261783)；不能把总系列的 ATAC、ChIP、人类材料一起导入。作者链接的 [Zenodo 数据记录](https://doi.org/10.5281/zenodo.14794723)标记 CC BY 4.0，实际 API 返回版本记录 17224677，已保存原始 JSON。

论文方法说明小鼠为 8 周龄。这里是成年心脏成纤维细胞，不是 E8.75 胚胎心脏，也不是 Gata4 敲除验证数据。相较小鼠树突细胞、脑或人类肿瘤细胞，它在物种与组织上更接近，但发育阶段、细胞类型和敲除条件仍有明显差异。不能据此宣称迁移有效。

本轮先审查十个样本的 metadata 和逐细胞 guide 表，预先选定 **OP2 静息组两个样本 GSM8151756/GSM8151757**，不混入 TGFβ/IL1β 刺激组或 OP1 批次。之后才下载这两个样本的原始矩阵。样本名中的重复不能替代供体层级审查，未把它们宣称为两个独立生物学单位。

| 项目 | 实际结果 |
|---|---|
| 下载 | 两个原始 10x H5，合计 59,852,089 bytes；独立 SHA256 已保存 |
| 原始细胞 | 4,537 + 5,225 = 9,762 |
| 隔离过滤后 | 2,622 + 2,832 = **5,454**，删除 4,308 |
| 干预与对照 | **26 个单基因扰动**，各 99–370 个细胞；**220 个 NTC 对照**包含在 5,454 内 |
| 表达基因 | **32,287** 个 Gene Expression 特征；移除 CRISPR Guide Capture 特征 |
| 比赛 panel | **500/500**，每个 panel symbol 对应唯一保留特征；没有补零或代填缺失基因 |
| 数据形式 | 原始计数；Ensembl ID 索引 + gene_symbol 列；38 个重复 symbol 保留独立 ID，不合并计数 |
| 尚未执行 | 归一化、embedding、图构建、聚类、pseudobulk、marker 分析、训练、评估、候选生成 |

过滤版本：[GSE261783_OP2_resting_provisional_raw.h5ad](../../infra/external_data/quarantine/T3-NEXT-R56-20260920/filtered/GSE261783_OP2_resting_provisional_raw.h5ad)。[FIBRO_FILTER_RECEIPT.json](FIBRO_FILTER_RECEIPT.json) 记录完整身份与条件计数，[FILTER_VALIDATION.json](FILTER_VALIDATION.json) 记录结构检查。文件明确标记 `QUARANTINE_NOT_APPROVED`、`model_input=false`。

过滤规则：逐组合成员检查项目 blacklist；本轮另外保守排除 **Tgfbr1、Smad2、Smad3、Smad4** 等发育信号风险项；排除多 guide/多基因条件；无 guide 标签不冒充正常对照；仅保留明确 NTC。26 个剩余扰动仍需逐基因近似表型审查，**不能把“固定黑名单命中为零”写成“全部不合规风险为零”**。规则额外排除项是保守筛查，不是证明这些扰动与 held-out condition 等价。

保留/剔除计划在 `fibro_planned_*_samples.tsv`，实际矩阵细胞保留/删除清单在 `fibro_actual_*_cells.tsv`。第一次过滤因重复 symbol 终止，失败记录保留；修正为 Ensembl ID 索引后完整重跑，没有丢弃重复基因或覆盖历史候选。

## 路线五：已收集关系资料，完整信号链仍未准入

1. **ConnectomeDB2025 小鼠版**：下载 CSV、JSON、许可页及对应引用卡片。共 3,252 对，数据库标记 894 Direct / 2,358 Inferred；比赛 panel 内有 37 对，其中 11 Direct。37 张来源卡片全部落盘并提取到 PubMed 引用链接。[原始下载页](https://connectomedb.org/downloads.html)，数据库论文 DOI：[10.1093/nar/gkaf1108](https://doi.org/10.1093/nar/gkaf1108)。这些计数不代表 37 条合规信号链：其中有接触/黏附关系，物种推断与下游表达靶点还需处理。
2. **CellPhoneDB v5 来源表**：线上取得 2,911 条相互作用和 212 条受体—TF 记录；其中 93 条受体—TF 记录含 PMID。也核对了 `/home/huyudi/006/data/lr_interaction/cellphonedb-data/` 的本地副本。[原始数据仓库](https://github.com/ventolab/cellphonedb-data)，方法标识 arXiv:2311.04567。
3. **目前批准的完整 ligand–receptor–target 输入仍为 0 条**。LR 表没有下游 target；受体激活某个 TF 也不等于改变该 TF 的表达，更不能直接当作 target 表达效应。没有用 NicheNet 预训练权重或来源不明的 ligand–target 矩阵补上这段缺口。

两项许可需要区分：ConnectomeDB 下载页写 MIT，但 [条款页](https://connectomedb.org/docs/policy.html)把数据库列为 CC BY-NC 4.0、软件列为 MIT；本轮保留冲突，不擅自采用较宽松解释。CellPhoneDB 软件的 MIT 不能当成数据库许可；[其网站条款](https://www.cellphonedb.org/legal.html)默认 CC BY-NC-ND 4.0，独立数据库仓库的适用授权尚待明确。因此未将关系表登记为可训练 prior。

`R5_PANEL_LR_REVIEW.tsv` 保留 37 对关系、物种证据、真实引用链接及审查状态。引用链接存在不等于原文逐条审查完成；数据库提供的 AI summary 链接没有被用作证据。[R5_RESOURCE_AUDIT.json](R5_RESOURCE_AUDIT.json) 记录缺口。

## 其他来源为何没有优先接入

| 来源 | 已核查范围与判断 |
|---|---|
| 本地 GSE90063 / Dixit 小鼠 DC | 两条件的 guide/基因/细胞 metadata 已逐行检查，各有 24 个达到 20 细胞的单基因扰动；但 panel literal overlap 仅 320/500、341/500（别名审计前），不能直接满足当前完整 panel 接口，未读表达矩阵。DOI:10.1016/j.cell.2016.11.038 |
| 2026 whole-brain CRISPR atlas | 作者链接的 UCSC feature/config 已下载；该过滤版本 6,348,631 细胞、panel 483/500，235.77 GB 表达矩阵未下载。HF 页面标记 CC BY 4.0；命令行下载遇到 SSL EOF，已保留失败。全脑上下文比心脏成纤维细胞更远，逐细胞审查未完成。不能把 UCSC 与 HF 7.72M 版本的分母混用。PMID:42039528 |
| Replogle 2022 | 原始 Figshare 文件目录和 CC BY 4.0 许可已保存；人类 K562/RPE1 需一对一同源映射和条件净化，8.7–65.8 GB 单细胞矩阵未下载，不用小 pseudobulk 文件冒充单细胞训练集。DOI:10.25452/figshare.plus.20029387 |
| 本地 Norman/GSE133344 | 111,445 行 guide metadata 已读；CRISPRa、组合干预，与当前单基因 loss-of-function 入口不匹配；未读表达矩阵 |
| 本地 GSE193736 | ORF 过表达/OverCITE-seq，未当成敲除数据 |
| 本地 GSE306429 | 药物扰动，不能直接标成单基因 KO；约 25.6 GB H5AD 未打开 |
| 本地 X-Atlas-Orion | HCT116/HEK293T 人类数据；卡片为 CC BY-NC-SA 4.0；保留备选，未读表达列，未借用任何已有 response embedding |

## 合规边界与下一步

本轮已读取官方缓存、任务契约、防火墙和 blacklist，并在线复核 [官方 Rules §10](https://virtualembryo.ai/challenge/rules)，原始网页已缓存。靶基因、其他 allele、近似表型以及已受污染预训练模型的禁用边界继续有效。隔离区只用于 metadata、立即过滤和结构核验。

项目 `docs/batch2/03_COMPLIANCE_RULES_SNAPSHOT_20260829.md` 还限定通用 Perturb-seq **用于响应形状而非方向**，且把该用途列为待书面确认。当前 R6 的带符号预测接口不能因本次找到矩阵就自动获准。需要先闭合用途边界和逐扰动审查；本轮用户授权的是收集，未启动训练，也未发消息给组织者。

- R3/R4：留在 TODO，优化参数化/传播与跨平台映射，不放宽旧门槛。
- R5：解决适用数据许可、逐原文/同源关系审查，并补齐可追溯的 receptor–target 关系；当前仅资料收集完成。
- R6：先完成逐扰动近似表型审查和用途许可，再做归一化及 WT/ontology-only 图输入准备。是否训练须以新的任务准入为依据；现有 26 个候选扰动不等于最终允许的 26 个。

生信索引已同步记录真实下载文件与隔离状态。未触碰 `/home/huyudi/006` 原始数据、未修改已评分候选、未上传或重新评分。完整数据仍非 READY_FOR_TRAINING，科学状态不因本次收集而改变。
