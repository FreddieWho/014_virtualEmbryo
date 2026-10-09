> Publication note: this handoff preserves the earlier planning checkpoint; v0026 code/results are included in this synchronization. Its historical local-only observation does not describe the published commit. T2 experiments/submissions remain paused.

# T2 暂停交接｜2026-10-09

**状态：按用户要求暂停全部 T2 实验与提交，转向 T1。今日 8/8 已用完；明日额度、继续实验及上传预算须重新确认。下文是候选计划，不是开工授权。** 本次只整理交接，没有新训练、实验、门户操作或 GitHub 推送。

## 1. 接手先看什么

- 当前本地完整收口工作树：`artifact:repo`，基于 `7dfe148f5c55d2a066e6adf1e4e46b08c631d08b`
- 11:38 UTC 只读核查：GitHub main 仍为上述提交。最后 v26 的登记及本交接仅在本地；**不能误称已同步远端**
- 文件身份正本：`submissions/INDEX.tsv`；总分正本：`reports/SERVER_SCORE_REGISTRY.md`；全部子项正本：`reports/SERVER_SUBMETRIC_REGISTRY.tsv`
- 本轮细节：`reports/t2_final_slot_20261009/REPORT.md`；前轮三板迁移：`reports/t2_operator_transfers_20261009/REPORT.md`

## 2. 门户数值最高 ≠ 项目现役

以下为 10:49:34 UTC 官方 API 快照，非持续监控；项目沿用 ±0.1 带内不换现役规则。

| 子板 | 门户数值最高 | 内部现役 | 差异解释 |
|---|---|---|---|
| 胚胎插值 | v23，63.0185 | v21，63.0047 | +0.0138，带内 |
| 心脏插值 | v26，66.7846 | v25，66.7064 | +0.0782，带内 |
| 心脏外推 | v32，51.1388 | v30，51.12（历史 UI 精度） | 不能据两种精度虚构精确差；现役未换 |

门户 T2 最佳值均分 **60.3139666667**，Human 71/187；心插 Human 38/174。此前用户确认总体 Total 172.9 是较早快照，不能冒充 v26 后的新精确总分。API 提供分数、模型和评分时间；submission ID/文件对应来自登录门户详情，不混淆两种证据。

## 3. 今日八次预算完整结算

此表是交接摘要，权威账仍以上述 registry 为准。标“UI”的数值不可补出隐藏小数。

| 次序 | 子板/版本 | 单一主要改动 | 终态分数 | 结论 |
|---|---|---|---|---|
| 1 | 胚胎 v19 | exact E3 + state-Bures 几何 | 62.33 UI | REJECT |
| 2 | 胚胎 v20 | exact E3 + endpoint support mixture | 61.39 UI | REJECT |
| 3 | 胚胎 v21 | exact E3 + 外部胚胎 scRNA 条件 copula | 63.0047 API | 较原 v14 62.8930 +0.1117，晋级 |
| 4 | 胚胎 v22 | 保持 v21 X，重排几何耦合 | 62.65 UI | REJECT |
| 5 | 胚胎 v23 | exact E3 均值桥后恢复桥输入自身 library | 63.0185 API | 数值最高，带内不晋级 |
| 6 | 心插 v25 | exact H1 + 心脏自身重拟合 copula | 66.7064 API | 较 exact H1 65.0260 +1.6804，晋级 |
| 7 | 外推 v37 | exact X2 原 drift 仅作用非零项 | 48.86 UI | 较 exact X2 50.35 UI 下降，REJECT |
| 8 | 心插 v26 | 相同 H1/B，blend 0.5→0.75 | 66.7846 API | 较 v25 +0.0782，带内不晋级 |

八次均终态，未重复上传，无待回分。对应 ID：
- 胚胎 v19 `07d32ef4cdfc4682b5998e6ab88c03e6`；v20 `7486e84fb2934a38a72737c4cefa655f`
- 胚胎 v21 `1b4b7c94a7fa45b6bb77cd3e839b5b6e`；v22 `efe73e77283d4b9486c72b7c919e76c8`；v23 `866a8e68fecd4c89baacbef1e73dcd35`
- 心插 v25 `84e1cb88cbdd4dd8861488783a1002b9`；v26 `178b3ff4be5440e286f53cf6e96805af`
- 外推 v37 `01f2cb4b59794d63ac27dd0d84962cff`

## 4. 必须继承的技术事实

1. **迁移算子，不迁移不合法的拟合数据。** 胚胎 copula 转心插的成功版本完全在合法心脏训练数据重新拟合 B，没有搬胚胎 B。v25 最終 fit 是 E8.25_late + E8.75；开发折 E8.25_late + E9.5 → E8.75，目标阶段只进入评分。
2. **copula 保持逐 state/逐 gene 数值多重集、全局边缘、零与正值总数、存储标签数、行序和坐标。** 不保持单细胞 library、分类器推断的类型质量、联合依赖或表达—坐标关联。variogram 是基因对表达结构，不是空间距离 lag。
3. **library renorm 与 copula 不可交换。** 不可在 v21/v25 后直接 renorm，却仍声称逐基因边缘不变。v23 是独立 exact E3 一开关：恢复均值桥输入 XB 每行自身 library，而非原始 E7.25 或 endpoint 分位数。原始行约 1e4，XB 中位约 2.447e4。
4. **零保持不等于零比例不变。** v37 不激活原零，但负漂移截断产生新零；开发折有 2 行全部截断，既有 library 规则无法恢复，最终提交没有此问题。不得事后修补掩盖失败。
5. **身份必须靠字节。** exact E3≠原 v14；exact X2≠原 v30/v32。H1 与历史 hash 的首轮差异最终定位为新增的 `carrier` provenance 字段；仅恢复旧元数据后整文件精确命中。v30/v32 历史原件仍未恢复。
6. **单线程与稳定排序是复现要求。** 不搜索 seed、行序或门户取样行为。几何重排虽然保全坐标多重集，有限索引抽样仍可能变，不能将 v22 占据分变化直接解释成空间支持丢失。

## 5. 有效经验与不该重跑的方向

- v25 的主要收益是 MMD skill +10.7466；v26 再加 MMD +1.2511，却使 neighborhood −0.4699。继续扫描 blend 的边际价值已小，不能只盯 MMD。
- 本次固定三个挑战者：global 0.75 局部均分较 v25 +0.3144，global 1.0 +0.2224 且 library 尾更宽，within-state rank B/0.5 −0.0348。**不把后两者包装成明日“新路线”**。
- 选定 0.75 的匹配置乱对照均分 52.3303，真实 54.7717；选择冻结后才补该诊断，没有据此二次调参。
- E8.75 开发折已被反复使用；三种子仅是抽样重复，不是三个独立生物学验证。局部选择收益乐观。v23 局部下降但服务器略升，局部 composite 不应跨机制一刀切。
- 暂不重跑：胚胎此次 Bures/support mixture/几何重排、外推零保持 drift、纯强度细扫、已失败的“均值场+加性空间对比”。本次不支持这些具体实现，不等于否定所有几何或外推方法。

## 6. 明日最多两条优先实验（须新授权）

### A. 心插：交叉拟合的可靠度门控 copula
保留已成功的 pooled heart B，在 released endpoints 内做固定 out-of-fold 条件预测，用训练数据可靠度门控原0.5贡献；弱证据/低支持组回退原秩，而非重新拟合已失败的 within-state B。若确有 donor/specimen ID，优先按其分折；否则细胞折不是独立生物学验证。目标是假设性地保住 v25 的 MMD 收益、减轻 neighborhood 代价；v26 局部 neighborhood 改善未传到服务器，故不能承诺此门控会保护它。不是再扫 0.6/0.7/0.8。

允许输入：E8.25_late/E8.75 的合法心脏 500 panel；开发折仍只用 E8.25_late/E9.5 拟合，E8.75 仅评估。比较 exact H1 off、v25 analogue、固定 v26 analogue、保持权重分布与覆盖的可靠度打乱负控。冻结可靠度定义与弱/小样本状态回退；维持精确边缘/坐标，报告 MMD、neighborhood、variogram、library 尾及分类器变化。复用开发折的限制不会因此消失；先有局部证据再决定是否值得新上传预算。

### B. 外推：心脏自身重拟合 copula 的独立迁移
这是尚未做过的“copula→外推”，不同于已失败的零保持 drift。优先找回 exact v30/v32 原件/可重放配方；若做不到，只能以 exact X2 的 50.35 UI 为配对父本，明确不是在 51.1388 最佳上做单轴改进。

允许输入：released E8.75/E9.5 心脏数据与该板 500 panel；开发折 E8.25_late/E8.75 → E9.5，模型不得见开发目标。保留父本原 drift/library/几何链，只在其后施加预先固定0.5依赖重排；不再 post-renorm，不声称单细胞 library 仍守恒。比较 same-parent off/on、copy-last 与同强度 gene-shuffle；跨类型少量共享、归一差异及旧父本可恢复性是先决风险。不要把胚胎 B 或额外新终点搬来。

不列第三条填数。联合“精确逐基因边缘+逐行 library”约束仍是未经证明的可行性问题，暂不占明日优先提交名额。

## 7. 复现与交付

- v26 候选完整 SHA256：`10db96db40d9ffbfd22a5d54a76c70a27ceab1284535e0170391dfcb3086d5e4`
- v25 精确父候选：`efb0c7298be54493d3d540257daf1f9c9664d8e64fe14bba8dd349669ea977c2`
- H1 精确载体：`7cc2e31445613a7e9e13525ea3b3ce8bf386855f8df0b70d6ba47f1ae2a23a37`
- E3 精确载体：`e93d56f2130297f7c5b256e3e26fc072b8913766772b3ffcb2634f7a3fdbfdae`
- X2 精确父本：`b884e3b6d2abda1aa4a01e64a198080f30cbdac7e3310d80c2a4f3da3ac7917b`

Library 持久交付（全部 version 0）：
- [v26 可移植代码/完整报告](private artifact reference omitted)：`private-artifact-reference-omitted`，5.85 MB
- [v26 候选](private artifact reference omitted)：`private-artifact-reference-omitted`，12.25 MB
- [前轮三板代码报告](private artifact reference omitted)：`private-artifact-reference-omitted`
- [v25 现役候选](private artifact reference omitted)：`private-artifact-reference-omitted`
- 前轮完整生成时备份：`private-artifact-reference-omitted`，43.4 MB，超过常用聊天附件 20 MB 上限

v26 包的 `portable.py` 可重定位此前数据/父本目录，示例见包内 README；从该打包入口已实际重放，输出文件 SHA 完全一致。精确 panel、输入来源、依赖版本和全部对照在包内。文件不可覆盖；复现须新目录。交接并不授权现在执行这些命令。
