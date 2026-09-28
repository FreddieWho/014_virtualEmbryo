# T3 五路线实现、固定选三（2026-09-29）

授权：实现五条路线，交付含三个可提交 h5ad 的一个包；不上传。类别：behavioral / 跨模块，执行针对性算子测试与完整模型重放。当前 best v0048=47.93；v0049–v0056 未回分。不上调科学结论。

共享：冻结 v0048 hurdle H、v0046 source rate G、v0009 WT carrier，500 genes / 7449 cells；源角色与旧哈希重新审核。只用已有批准数据，无新增外部数据。G 为既有源模型，不重新声称训练。

1. r1active：H 后加入 0.5×G，按训练集每类型正 Gata4 中位数归一化活动量，clip(activity/median,0,1)。检验活动量依赖；零观测可能为 dropout。
2. r2gene：训练 WT 上 H 的零干预平均响应与 G 同号且两者绝对值>1e-8 的基因才加入 0.5×G。全目标细胞应用；区别于旧逐细胞同号 mask。
3. r3bag：四个固定 seed、按类型有放回 bootstrap 的实际 hurdle 拟合；每类型训练样本数保持，平均条件响应，再用强度0.25有界解码。
4. r4spline：linear hurdle 特征上加入正活动量25/50/75分位截断线性基函数及类型交互；knots/scale仅训练拟合。概率与阳性幅度分别 ridge100。不是旧图约束 spline。
5. r5local：hurdle 预测残差，在训练标准化 activity+xyz 空间按类型取64邻居均值，权重0.4修正条件均值（截零）；查询时排除相同原始行ID，再计算干预差和0.25有界解码。没有供体的类型残差为0。

所有配置先冻结于 configs/t3_five_select/design_20260929.json；不得见结果后修改强度/方法。五条保存实际完整输出和模型；未选两条保留研究 artifact，不注册 candidate。

## 选择与限制

沿既有 z 四分块，0+1训练，2开发，3审计。同类型训练>=80，训练活动 q25<q75，测试高低组各>=10，干预到训练低组中位数。对499非Gata4基因比较“高组经响应调整后的均值”与观测低组均值，按高组细胞数×499加权 group-mean MSE。列出覆盖/排除数；identity及训练H为参照。局部比较所有模型只用0+1拟合，包括两种来源组合的H和gene mask，避免全WT模型泄漏。

在开发结果上，来源族 r1active/r2gene 选一，学习族 r3bag/r4spline/r5local 选二，MSE升序，同分用上述顺序。无可测组则固定顺序并标 NOT_TESTABLE。SELECTED.json 写入且哈希后才执行审计，审计不得改变排名。按锁定排名，若最终工程失败/no-op/与已登记候选完全相同，使用同族下一合格项；禁止降低gate或改参数。必须有三个有效且互不相同的提交。

最后在全WT拟合 bootstrap/spline/local 并执行五条7449×500推断；两条来源模型复用已验证H和G，训练型gate/mask使用全WT。全输出contract/灾难边界/noop/唯一性检查，选三登记并打包。回放、行基因坐标身份、包成员SHA/CRC检查。

该切分是同一胚胎的空间块，非生物重复；全项目已多次探索WT，审计也不构成独立KO验证。不能把改善视为因果效应或服务器提分。Gata4 KO target不可用，官方匹配KO评分 NOT_RUN_NO_MATCHED_GATA4_TARGET，科学NOT_IDENTIFIABLE；blocks_submission:false。上传前需提醒回填待分候选原始证据。
