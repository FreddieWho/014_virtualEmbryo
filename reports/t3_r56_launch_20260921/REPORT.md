# T3 R5/R6 规则修改与开工准备（2026-09-21）

本轮按用户授权修改生效政策和R6准入代码，并完成真实数据准备；不是仅提出方案。

## 生效改动

权威政策：docs/coordination/T3_EXTERNAL_DATA_POLICY_20260921.md。

- 取消外部Perturb-seq必须shape-only的合规限制；来源允许时可学习有符号响应。
- 取消普遍主办方书面确认门。具体未解决边界疑问仍为NEEDS_CLARIFICATION；已知禁止记录仍排除。
- 基因同通路/共同参与心脏发育不是phenocopy的充分条件；按实际年龄、组织、扰动和实验上下文审查。
- 保留来源/许可、任务范围、条件allowlist、输入与review哈希绑定。旧规则快照、旧permit、原始隔离件和已评分候选均未覆写。

## R5

已存在且重新核对身份的v0032/v0033（父v0009，信号off/on）contract PASS，仍未提交/未评分；无需为了开工准备重复生成相同候选。交付包 deliveries/r5sig__t3__upload__20260920.zip。当前仅1条最小SIGNOR LRT，不宣称全通路模型。源边跨背景组合的科学限制保留。

## R6

READY_FOR_R6_TRAINING。输入为GSE261783 GSM8151756/57，8周龄小鼠静息心脏成纤维细胞。26个单基因扰动＋220个显式NTC，共5454细胞；不含目标家族标签。每个条件至少20细胞。

逐条件重新审查并登记在CONDITION_REVIEW.tsv，SOURCE_REVIEW.json绑定新政策、来源和许可。原先排除Chd4/Smarca4/Yy1所用证据来自胚胎发育/共因子研究；不能证明本来源的成年成纤维细胞记录等价于受保护胚胎KO，故经重新审查恢复。这只授权本次具体样本范围，不授权这些基因在所有阶段/组织的所有数据，也不意味着整个公共数据集通过。

其余未纳入初始26条件子集的源记录不在本次许可内，不把它们全部定性为违规。本轮没有为判断准入而查看目标表达、推断目标方向或使用服务器反演。

已完成三件套：

- expression.h5ad：5454×500，先使用全部32287个基因计数计算每细胞library，再CP10K/log1p，最后提取全部500个唯一匹配panel基因。不是在500基因子面板内重新归一化。
- embedding.npz：27×80。26源扰动基因＋Gata4，使用已获准WT图谱全部68910细胞，在原有80个细胞类型分组内计算平均log表达特征；未使用扰动响应。
- adjacency.npz：27×27，与embedding基因顺序一致；正cosine top5邻居、对称化、自环。未使用源响应、held-out基因响应或预训练模型构图。

三文件已绑定SOURCE_MANIFEST.json并通过现有manifest接口。原始源文件留在原隔离位置；新RAW_PROCESSING_PERMIT仅授权已审查的所选记录转换成新的sanitized派生文件，不更改原隔离件的历史身份。标准化输出obs.reason保留历史初筛文字，当前资格以permit_status与SOURCE_REVIEW为准。

准备阶段没有训练响应预测器。固定seed的计划为20个训练gene、6个验证gene；名单在READINESS.json。目标Gata4仅提供WT特征，没有源响应标签。下一步比较no-change、ridge与GCN，未通过原gene-holdout门时不生成目标预测。成人→胚胎迁移未经验证；样本编号不证明独立供体；现有R6采用合并显式NTC基线，可能受样本效应影响。

## 开工命令与边界

见START.md。实际预测器训练、gene-holdout评估、目标推断均NOT_RUN，本轮没有新R6候选。数据准备成功不等于预测成功。R5已有候选的身份以submissions/INDEX.tsv为准，分数以reports/SERVER_SCORE_REGISTRY.md为准。
