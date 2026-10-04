# Task3 六项优先路线：完整执行与第一轮结论

回分更新（2026-10-01）：本批六件全部已评分并判 REJECT，现役不变、T3 待分清零。[回分复盘](../t3_score_review_20261001/REPORT.md)；[权威分数](../SERVER_SCORE_REGISTRY.md#t3-priority-six-score-return-20261001)。以下保留模型执行和交付时的状态与结论，不再代表当前提交状态。

开始：2026-09-30；交付：2026-10-01（北京时间）。批次标识与文件名保留开始日期。

**六项核心计算已实际执行，完整目标推断已完成。生成六个通过 contract 的候选，合成一份上传包；未提交、未评分。** 显式状态质量路线没有预测出比例变化，因此保留负结果，不把随机重采样制造的差异交成候选。现役 v0048 保持。

用户要求的“完整实现原报告”已经登记到 [LEADS.md 的 L-010](../../LEADS.md)：包括全部八个方向、六项优先实验、对照与限制。本轮完成的是六项优先核心执行；原报告后面的条件分布生成、增强子反馈、发育分支与通信耦合仍是后续线索，尚未运行。

## 1. 这轮实际做了什么

| 优先路线 | 实际计算 | 本轮结果 |
|---|---|---|
| 1 状态化 CellOracle | CellOracle 0.22.0；完整 68,910 个 E8.75 WT 细胞；固定选择 2,000 基因；状态 GRN、Gata4 原生模拟、3 步传播；保留完整逐细胞 factual/delta | v0060；目标完整 7,449×500 |
| 2 显式状态质量 | 将原生反事实投到 WT 状态流形，计算状态转移与质量；表达单独、质量单独、组合三个完整输出 | 原生 68,910 个细胞的硬状态跨越为 0，比例完全等于 WT；质量单独为 identity，组合等于表达单独；不登记重复/无效候选 |
| 3 独立活动特征 | 按状态用 Gata4 下游 regulon；每个输出基因从自己的活动特征中排除；状态内 WT 重构留出、完整拟合和反事实 | v0061；属于观察性假设，缺少 Gata4 实测 KO 验证 |
| 4 功能线性/双线性 | 缓存小鼠 GO 注释闭包→固定 128 维表示；整扰动留出；来源全部细胞用于均值估计，双线性加入 sample-control 上下文；最终全部 26 条件重拟合 | v0062 线性，v0063 双线性；二者完整目标推断 |
| 5 Scouter | 作者 compressor–generator、默认 2048/512/64→2048、原训练与损失；40 epoch 上限和 validation 早停；最终 26 epoch 全条件拟合；全部目标细胞推断 | v0064；**作者代码的 GO128 表示变体，不是论文 GenePT1536 配置完整复现** |
| 6 GEARS | 作者原版双图、网络、损失与训练；64 hidden、20 epoch；小鼠 GO 自定义基因集和训练条件共表达图；另训练无邻居图对照；最终 20 epoch 全条件重拟合和完整目标推断 | v0065；真实 GEARS，使用完整 500 基因输出 panel 的自定义小鼠图；不是旧均值小 GCN，也不是全转录组/默认人类图复现 |

原生 CellOracle 是 68,910×2,000 的实际算法输入，不能写成 27,669 基因全部参与 GRN。完整 atlas 原始矩阵 68,910×27,669 已读取，选择规则固定为 panel/关键基因加变量基因，与已有原生运行范围一致。细胞级 native 输出和系数保留，未用旧汇总表代替这次拟合。

所有目标路线都使用完整 7,449×500。没有用目标细胞子集、smoke、旧拟合、旧目标候选或 Mab21l2 真值冒充本次核心计算。

## 2. 输入和验证怎样隔开

来源表达复用已批准的 GSE261783 两个 OP2 resting sample：5,454 细胞，26 种单基因扰动及 220 对照，成人小鼠心脏成纤维细胞。任务来源许可、条件 allowlist、文件 hash 和当前政策先检查，再读取表达；没有读取或训练隔离区未批准的额外条件。

功能表示只用已有 GO ontology/module 注释，包含 is_a/part_of 闭包，没有用 KO 响应构图或拟合 embedding。新派生的 526×128 表示和 526 基因 GO sets 已登记到 [数据索引](../../infra/bioinf-data-index/INDEX.tsv) 和 [汇总](../../infra/bioinf-data-index/SUMMARY.md)。未下载新的 KO 表达或扰动训练权重。

后三项共用同一固定拆分：17 个训练扰动、3 个 validation 扰动、6 个 test 扰动。一个扰动的全部细胞和两个 sample 同时留出，不将同一基因的另一批细胞放回训练。test 为 Ino80、Wdr82、Smarca4、Paxip1、Hcfc1、Yeats4；validation 为 Brd7、Kat8、Kat5。先保存 test 结果，再全部 26 条件重拟合供预测；重拟合阶段的结果不再称独立验证。

双线性模型实际只有两个 sample，control-context PCA 有效维度为 1；不是八维独立组织覆盖。这两个 sample 也未证实为独立动物。Scouter 随机 control–perturbed 配对没有增加独立扰动数。

证据：[冻结配置](../../artifacts/t3_priority_six_20260930/CONFIG.json)、[输入锁](../../artifacts/t3_priority_six_20260930/INPUT_LOCK.json)、[本轮来源审查](SOURCE_REVIEW.json)。新输入及最终代码都有保存，源数据和旧评分文件只读。native 三个输入还在训练后逐项核对原始 WT manifest SHA，全部通过；[锁文件](../../artifacts/t3_priority_six_20260930/NATIVE_INPUT_LOCK.json) 明确这是事后验证，重放代码已前移检查。

## 3. 来源侧结果：复杂模型没有自动胜出

下面是共同 6 个整扰动留出的 **变化量 MSE**，越低越好。它是本轮来源域诊断，**不是比赛分数**；不把 500 输出基因当 500 个独立生物重复。

| 方法 | 变化量 MSE | 变化向量 cosine | 相对平均扰动基线 |
|---|---:|---:|---|
| WT 不变 | 0.008508 | 0.000 | 更差 |
| 训练扰动平均响应 | 0.006726 | 0.476 | 比较基线 |
| GO 功能线性 | 0.006645 | 0.490 | 略好，MSE 降约 1.2% |
| GO 功能双线性 | 0.006581 | 0.499 | 略好，MSE 降约 2.2% |
| 原版 Scouter + GO128 | 0.007351 | 0.416 | 更差 |
| 原版 GEARS + 小鼠 GO | 0.009032 | 0.263 | 更差，且差于 WT 不变 |
| GEARS 同结构、独立训练、仅自环 | 0.008253 | 0.263 | 更差；本来源没有证明邻居图带来增量 |

本次六个 test 条件不足以宣称这些小幅差别有统计显著性。保留 Scouter/GEARS 的负结果，没有翻转方向、删掉困难扰动、重选 test、追扫参数或通过最终全量重拟合改写留出结果。

功能线性还运行了训练 embedding 置乱对照（MSE 0.006812）。Scouter 的条件置乱和 GEARS 的删边推断对照分别保存；这些是推断消融，不能冒称另一个从头训练的模型。GEARS **另有**真正从头训练的无邻居图对照，表中使用的是后者。

这支持的结论很有限：**本来源中的通用平均效应很强，功能表示有小幅增量，两个神经网络尚未证明比强基线更好。** 它不能证明其他合法来源、GenePT 表示或更丰富扰动数据没有价值，更不能预测目标服务器结果。

原始留出证据：[功能线性](../../artifacts/t3_priority_six_20260930/r4_functional/HOLDOUT.json)、[双线性](../../artifacts/t3_priority_six_20260930/r4_functional/BILINEAR_HOLDOUT.json)、[Scouter](../../artifacts/t3_priority_six_20260930/r5_scouter/HOLDOUT.json)、[GEARS](../../artifacts/t3_priority_six_20260930/r6_gears/HOLDOUT.json)、[独立无图训练](../../artifacts/t3_priority_six_20260930/r6_gears/NO_GRAPH_TRAINED_HOLDOUT.json)。

## 4. 虚拟敲除这次修复了哪些问题

**保留状态与细胞差异。** CellOracle 新 native layer 有 1,932 个下游原生建模基因出现非零 delta；这个数包括 2,000 模型基因，不能等同 500 panel。目标端从匹配的 native WT 邻居得到逐细胞 count ratio；没有再跨状态平均，也没有 E9.5 IQR 乘数。旧 v0018/v0019 adapter 和当前 v0048 RNA hurdle 以哈希绑定的原 artifact 作为输出对照，未重新标注旧服务器结果。

新 CellOracle 候选改变 489 个下游 panel 基因；旧 v0018 为 119 个。下游最大群体 log-mean 位移约 0.0504，旧 v0018 约 0.00402。**这是响应保留更多的证据，不是预测变准或服务器提高的证据。** 还没有匹配 Gata4 KO 真值，不能将变化变大本身当成成功。

**检测率与阳性值分开处理。** 旧的 count-ratio 输出仍保存为对照。另用合规来源学习“均值强度变化→检测率 logit 变化”的 decoder：固定训练扰动留出 test 后，条件检测率拟合 MSE 0.1439，相比零变化 0.9899；最终全 26 条件拟合 slope 1.1000。随后在目标已有细胞状态内稀疏激活/关闭条目、从 WT 阳性值采样，并保持每状态原模型预测的 count 均值。全零、没有阳性支持的状态仍保持零，不向所有零条目加常数。

这段 decoder 的诊断是**给定来源实际强度变化后的条件校准**，并非未知扰动效应的端到端独立验证。adult scRNA→胚胎 MERFISH 的迁移未验证；方向和尺度错误仍会被保留。小来源基线与数值 pseudocount 也可能产生过大的跨平台比例，不能把“校准”理解成已经校准目标 KO。

**活动特征不偷看自己的输出。** CellOracle 系数行是调节源、列是受体，因此用 Gata4 行取下游 regulon；每个基因从自己的活动计算中删除，且状态分别拟合，避免再次跨状态抵消。59 个映射状态具有足够输入；21 个目标细胞所在状态缺少足够 regulon 或 WT 数量，保留零活动效应。活动模型 WT 重构加权 MSE 1.363，状态均值基线 1.380，只是重构诊断。参考“失活水平”为事前 WT 状态内第 1 百分位，尚未证明等于生物学 Gata4 功能归零。

**状态质量的负结果没有被藏起来。** 当前硬状态转换没有跨状态事件，质量分布与 WT 完全一致。初版随机重采样会在相同比例下制造抽样变化，这是实现错误：已改成整数配额，预测质量等于 WT 时精确保留原行；早期未登记研究输出单独隔离保存，未进入上传包。质量单独输出等于 WT，质量+表达输出等于表达单独；因此不登记两件。该结果只约束当前“硬状态转移”实例，不证明敲除不会影响生存、发育速度或连续命运概率。

证据：[完整 native receipt](../../artifacts/t3_priority_six_20260930/native/COMPLETE.json)、[旧/新输出比较](../../artifacts/t3_priority_six_20260930/TARGET_COMPARISON.json)、[检测率校准](../../artifacts/t3_priority_six_20260930/DETECTION_CALIBRATION.json)、[活动审计](../../artifacts/t3_priority_six_20260930/ACTIVITY_AUDIT.json)、[质量负结果](../../artifacts/t3_priority_six_20260930/STATE_MASS.json)。

## 5. 原工具、工程问题与验收范围

[Scouter 作者仓库](https://github.com/PancakeZoy/scouter)固定 commit `fe2a73bdda02c9ec639bd55dabe758da2f7ff335`；[GEARS 作者仓库](https://github.com/snap-stanford/GEARS)固定 commit `f374e43e197b295016d80395d7a54ddb81cc6769`，二者 MIT。GO 预备集合有 526 个基因，其中 12 个缺少注释，实际 GEARS perturbation 图为 514 节点；所有 26 个来源扰动与 Gata4 均有覆盖，输出与共表达侧仍保留完整 500 基因。没有把自制小网络改名为原方法。Scouter 是作者自定义表示接口的 GO 变体；本轮没有下载/审查 GenePT 向量，完整论文配置仍未复现。GEARS 的作者说明不将跨细胞类型迁移作为既有验证能力，本轮胚胎 adapter 是探索性预测。

Scouter 作者 trainer 的最佳 checkpoint 使用可变 `state_dict` 引用；调用层加 deepcopy 让保存的 validation 最优权重保持不变，未改架构、损失、优化器或配对方式。目标预测还使用 zero embedding 作为无干预参考，但作者 BalancedDataset 未直接监督该参考输出，这一结构假设保留为风险。

CellOracle 环境初次 import 遇到 libstdc++、numba/genomepy 缓存目录问题；已用既有 conda 动态库及任务内 runtime 目录解决，完整 native 重跑成功。GEARS 删边推断最初忘了同时清空边权，失败被日志保存；修正后从已锁的原模型 checkpoint 继续，无重选 test，后续独立无图训练与全条件拟合均完成。

5 项针对性测试通过：观测 decoder 零效应/非负、活动输出排除、变化量诊断、检测率改变且保持状态 count 均值、质量不变时采样精确保留原行。六个候选均通过正式 locked contract 检查；zip 的成员 hash 和 CRC 已核验。没有为本次路线跑无关全仓测试。

**未运行/未获得：** 目标匹配 Gata4 全面本地 scorer（缺少合法目标真值）、portal 上传、新服务器评分；也没有获得独立因果机制验证、GenePT 配置复现、全转录组 GEARS 或独立动物泛化结论。没有将上述缺项写成 PASS。来源留出与活动/decoder 条件诊断各自保留结论边界。科学限制 `blocks_submission: false`。

## 6. 交付与下一步

本批 [六成员上传包](../../deliveries/t3six__t3__upload__20261001.zip) 为 `READY_NOT_SUBMITTED`：

| candidate | 路线 | 父版本 |
|---|---|---|
| v0060 | 原生状态化 CellOracle + 共同 decoder | v0009 |
| v0061 | 状态独立活动 + 共同 decoder | v0009 |
| v0062 | 功能线性 + 共同 decoder | v0009 |
| v0063 | 功能双线性 + 共同 decoder | v0009 |
| v0064 | 作者 Scouter 的 GO 变体 + 共同 decoder | v0009 |
| v0065 | 作者 GEARS 的小鼠图变体 + 共同 decoder | v0009 |

candidate artifact、SHA256 和 contract 状态以 [submissions/INDEX.tsv](../../submissions/INDEX.tsv) 为准；contract 报告随 canonical candidate 保存。包内包含全体成员 MANIFEST/UPLOAD_MANIFEST/RUN_ID_MAP/EVIDENCE_MANIFEST_POINTERS 四张清单。[交付 receipt](../../artifacts/t3_priority_six_20260930/DELIVERY.json) 记录父版本和输入/结果入口。六件均为 **未提交/未评分**，并未排成已验证的高分路线。

建议下一步先取得这批服务器的真实回分，再判断原生状态化响应和活动特征是否值得扩大。来源侧优先保留功能线性作为强基线；Scouter/GEARS 的后续增量必须来自有据可查的数据/表示或设计改变，不能由这次负结果推出神经网络整体无效。状态质量若继续，应新立 continuous/soft mass 或带允许干预证据的版本，保留当前硬转换的负结果，不能静默覆盖。

**下一次提交前须提醒：这六件没有服务器分数；提交后需提供完整分数与原始证据供回填。** 本轮没有操作 portal，也没有更换现役选集。数据准备和核心计算均已完成，无工程 blocker；目标真值缺失与跨域识别属于明确科学限制。

重放入口：[实现目录](../../scripts/t3_priority_six/)、[测试](../../tests/test_t3_priority_six.py)、[代码 manifest](CODE_MANIFEST.json)、[工具来源](TOOL_SOURCES.json)、[交付验收](ACCEPTANCE.json)。本轮决策 `D-20260930-T3SIX-001`（启动）及 `D-20261001-T3SIX-002`（执行/交付与质量负结果）。
