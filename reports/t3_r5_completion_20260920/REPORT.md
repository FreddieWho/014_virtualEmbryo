# T3 R5 最小信号链补齐（2026-09-20）

## 已完成的输入闭环

从SIGNOR 4.0明确CC-BY4.0许可的逐边记录中，筛出一条最小链：

Pdgfb → Pdgfrb → Src → Stat1 → S100a10

供现有R5接口消费的记录为 Pdgfb/Pdgfrb/S100a10，三个基因均在500 panel。Src/Stat1仅是文献层面的中介，不假装它们都在panel实测或本次独立拟合了每步机制。每个节点都有唯一的一对一人鼠同源映射。输入在 `infra/external_data/sanitized/T3-R5-SIGNOR-MINIMAL-20260920/edges.tsv`；许可、哈希与范围在本目录SOURCE_MANIFEST.json、FILTER_RECEIPT.json。

这是单条链的最小启动版，不是37条旧LR关系全部补齐，也不是全胚胎细胞通信模型。

## 逐边来源

| 边 | SIGNOR记录 | 原始论文 | 审查背景 |
|---|---|---|---|
| PDGFB→PDGFRB | SIGNOR-107400 | PMID11331882；另核对PMC2895058结构研究 | 蛋白配体/受体结合，非目标胚胎响应 |
| PDGFRB→SRC | SIGNOR-247979 | PMID15489898 | 人肺腺癌细胞失巢凋亡/脱附信号；beta亚型归属以SIGNOR策展为据，摘要只称PDGFR |
| SRC→STAT1 | SIGNOR-235696 | PMID14978237 | 人NCI-H292细胞IFN-gamma/TPA信号 |
| STAT1→S100A10 | SIGNOR-255237 | PMID12645529 | 人BEAS-2B/HeLa细胞；p11启动子GAS位点及STAT1显性负性实验，支持转录调控 |

主引用：https://pubmed.ncbi.nlm.nih.gov/15489898/ 、https://pubmed.ncbi.nlm.nih.gov/14978237/ 、https://pubmed.ncbi.nlm.nih.gov/12645529/ 。源记录及人工背景判断见EDGE_CONTEXT_REVIEW.tsv；同源映射见ORTHOLOGY.tsv。

## 许可与使用边界

SIGNOR数据许可为CC-BY4.0（https://signor.uniroma2.it/documentation/），不是套用软件许可。交付包提供ATTRIBUTION.md并说明筛选、删除字段、同源映射和压缩链的修改。原始论文只做来源审查，不复制论文正文、图、表达数值、正负方向、效应幅度或预训练参数到训练输入。全量SIGNOR及所有原文缓存仍隔离，只有1条LRT及其4条来源记录按所列用途放行。

本次放行针对“通用pathway知识＋WT拟合系数”；没有受保护Gata4/Gata6/Ctnnb1特异边，也没有外部实测表达训练集。内部规则关于conditional来源确认的条件不能自动扩大到所有通用知识。这里的项目审查不是主办方书面批准，亦不授权R6数据。R6内部shape-only及待确认限制保持不变。

## 科学限制

四条边来自不同细胞/刺激背景；连接成完整链是待检验假设，不能声称原文证明了PDGF→S100A10在E8.75胚胎成立。中间磷酸化不等于目标表达；只因末端有转录调控证据而进入LRT表。实际系数完全在官方允许WT上拟合，信号开关及发送端置换用于检查本实现是否产生非平凡影响，不能验证因果。human→mouse同源关系也不保证情境迁移有效。

## 未采用的补链

- Pdgfb/Pdgfrb/Col1a1：PMC8667318中PDGFR抑制未降低Col1A1；不据此构造确定链。
- Apln/Aplnr/Klf2或Nos3：成人/人PAEC原始证据存在，但2011原文版权不等于可按CC-BY再分发其内容；2024研究显示KLF2对A13不响应的条件依赖。此次不纳入，不能用单一方向覆盖背景差异。
- Pdgfrb/Ptk2/Yap1/Bmp4：中间文献PMID33498611是干细胞应激综述，不能冒充逐边原始实验。
- 原37条LR候选不是全部合格；仍保留逐行缺口记录。没有为凑数量纳入adhesion自配对、无下游target或受保护信号分支。

## 验证与执行

输入身份、四条源记录、原始PMID、五个唯一同源映射及3/3端点panel匹配由 `scripts/t3_data_intake/complete_r5.py` 实际检查。运行结果将记录在EXECUTION.json；运行目录为 `artifacts/t3_next/T3-R5-SIGNOR-MINIMAL-20260920-v1`。无匹配的Gata4实测目标，不能在本地证明预测质量；服务器未评分之前不宣称进步。

执行结果：CANDIDATES_READY，v0032(r5off)/v0033(r5on)，父版本v0009，contract及候选检查PASS；发送端置换差MSE=6.866e-8，signal RMS=2.311e-4，效应很小。候选身份/哈希仅以submissions/INDEX.tsv为准。包 `deliveries/r5sig__t3__upload__20260920.zip`，未提交/未评分；下一次提交前须提醒用户回填现有待评分候选分数。
