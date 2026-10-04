# T3 方向六数据任务：GSE261783 metadata-first 显式屏蔽审查（2026-10-02）

范围：纯元数据检查（perturbation 基因名 vs 黑名单），未读表达矩阵、未训练。
依据：方向六设计（`reports/T3_NEXT_ROUTES_20260920.md` §8）＋
`docs/batch2/compliance/target_leakage_blacklist.tsv`（8 类显式排除）＋
`reports/t3_data_intake_20260920/FIBRO_METADATA_AUDIT.json`（26 扰动基因表）。

## 方法

26 个扰动基因（Arid2/Brd7/Brd9/Chd4/Dmap1/Egr2/Hcfc1/Ino80/Kansl1/Kat5/Kat8/Kmt2a/
Paxip1/Pbrm1/Rest/Rnf40/Setd1b/Setdb1/Smarca4/Smarcd1/Srcap/Tfpt/Wdr82/Yeats4/Yy1/Znhit1，
大小写不敏感）逐一比对黑名单 31 项（GATA4/GATA6/CTNNB1/MESP1、canonical WNT 13、
cardiac 核心 TF 6、GATA 家族 4、SMAD/TGFBR 4）。

## 结果

- 显式命中：0/26，全部通过。组合命中：无（皆单基因 KO）。
- 本地文件存在：`infra/external_data/quarantine/T3-NEXT-R56-20260920/filtered/GSE261783_OP2_resting_provisional_raw.h5ad`（58MB，未动）。

## 未闭合（本审查不裁决）

1. 功能性 phenocopy 人工复核仍 open：Smarca4、Rest、Yy1 有已知心脏发育文献角色，
   是否构成 phenocopy 风险需人判（或 organizer 答复）；本报告只列为复核提示，不擅自扩黑名单。
2. 许可升级：文件仍 QUARANTINE_NOT_APPROVED、model_input=false；放行需合规 owner 决议，
   organizer clearance 缺席；边界邮件 Q2 相关但这 26 个非通路成员，不在三问范围内。
3. 技术就绪：raw normalization/graph 未做（训练前做）。

## 裁决

数据任务元数据屏蔽项 PASS（26 扰动全部可用作留出组，数量足够做 gene-held-out）；
release PENDING（待上述 1–2）。训练仍 BLOCKED_DATA_NOT_READY，不得提前。
