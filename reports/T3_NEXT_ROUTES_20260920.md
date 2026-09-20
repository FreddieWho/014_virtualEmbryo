# T3 下一轮路线提案：从统一位移转向条件响应与分布重建

日期：2026-09-20。依据：已登记至 R6–R8 的服务器结果、现有 run 报告、任务数据与防火墙。
提案发布时状态：PROPOSED / NOT_RUN。用户随后授权实现；当前执行结果见 [六路线执行交付](T3_NEXT_EXECUTION_20260920.md)，下文保留原设计。

## 1. 当前结果支持什么

当前 selection 仍为 v0009/v0010（46.95）；R6–R13 八候选的分数均已回填。精确分数与子项以 [SERVER_SCORE_REGISTRY.md](SERVER_SCORE_REGISTRY.md)、[SERVER_SUBMETRIC_REGISTRY.tsv](SERVER_SUBMETRIC_REGISTRY.tsv) 为准；候选身份以 [INDEX.tsv](../submissions/INDEX.tsv) 为准。

- R6 CIPHER=46.94、R7 SPLIT=46.95：级联幅度加全局/心脏门控，没有取得晋级；二者 de_score 仍为 39.2。
- R8 KNK=46.64：相对 R7，direction 增加 0.6，variogram 降低 5.7；把 unsigned 排名扩展成 498 基因的位移，没有解决整体表现。
- R10 GRAPH/R11 SIGNMAX 的 de_score 达到 39.6，但没有超过 incumbent；R13 空间平滑则明显退步。这提示有必要隔离“响应方向”和“表达分布被如何改写”的影响，尚不能证明 variogram 是唯一瓶颈。
- genotype zeroing 已有正信号；继续扫剂量、心脏/非心脏二分门、传播半径或 kNN 平滑，优先级低。
- 当前 Gata4 候选对 Mab21l2 pseudo-target 的打分，不是 unseen-Gata4 的有效验证；不再用该分数排序新方向。

旧路线执行边界：R10 是 PageRank/图传播构造，没有训练原版 GEARS；R12 是偏移去偏，没有运行 dbDiffusion 训练；R9 没有完成原提案的 LLM embedding。失败的是实际执行版本。旧“30 轮”提案不能作为 30 个独立训练实验已经完成的证据。

本提案提出 6 条与已实施版本不同的实验方向。它们均为预测假设，没有预期提分承诺，也不构成 Gata4/Ctnnb1 因果机制结论。

## 2. 优先级和资源

| 顺序 | 新方向 | 相对旧路线改变的关键因素 | 输入就绪度 | 首轮预算上限建议 |
|---|---|---|---|---|
| 1 | 保留边际分布、重建细胞间表达排序 | 只检验跨基因/空间依赖结构，不继续放大 shift | 本地已有候选与 WT | CPU 1 h；最多 2 候选 |
| 2 | WT 流形内的异质响应与状态占比变化 | 从所有细胞同向位移，改为部分细胞切换到有支持的表达状态 | 官方 WT 已有；响应仅能由假设估计 | CPU 4 h；最多 2 候选 |
| 3 | 保留细胞残差的稀疏条件机制 | 从聚合线性级联，改为每细胞条件方程和有界非线性响应 | WT 已有；拓扑须按新 run 确认许可 | CPU 4 h；最多 2 候选 |
| 4 | 全转录组隐藏中介到 500-gene panel 的映射 | 从 full-RNA 模拟后聚合，改为逐细胞映射、保留中介与状态差异 | v7 输入在盘；部分索引待修正 | CPU 8 h/64 GB；最多 2 候选 |
| 5 | 配体—受体约束的非细胞自主响应 | 建模“扰动信号传给邻居”，不平滑原始表达 | 拓扑覆盖与来源许可待确认 | CPU 4 h；最多 2 候选 |
| 6 | 用合规多扰动数据训练 gene-conditioned 模型 | 真正学习未见基因响应；加入监督线性基线和公开图模型 | BLOCKED_DATA_NOT_READY | 数据条件满足后 CPU 基线；GPU 单轮 ≤8 h |

预算是拟议的停止上限，不是实测耗时或完成保证；不得为了按时交付缩小已锁定的正式实验后仍声称全量完成。方向 1 若无非平凡变换，立即关闭诊断，不占上传名额。方向 4–6 不阻塞前面独立路线。

## 3. 方向一：保留边际分布、重建细胞间表达排序

**假设。** 部分候选的单基因响应已经有微弱信号，但跨基因组合或表达与位置的对应关系受到破坏。可以固定响应的边际分布，只改变其如何分配给细胞，从而做可归因的诊断。

**最小实验。** 预先指定 v0022 GRAPH 和 v0023 SIGNMAX 为两个不可变供体，各生成一个新文件。对每个非 Gata4 基因，取供体该列排序后的数值，按照原始 WT 同基因在相同 7,449 个细胞上的排序重新分配；Gata4 延续 parent 的零值。细胞行、坐标、基因顺序不变。WT 原始值从既有 parent 行映射取得，不能从清零后的 Gata4 列恢复原始表达。

该操作精确保留供体每列的数值多重集，因此均值、方差和零比例不变；目标是恢复 WT 的秩依赖结构。若有大量并列值，只能固定以原行号打破并列；此时不声称精确保留 Spearman 相关。秩结构保留也不等于 Pearson 协方差或 variogram 保留。

**与旧路线区别。** 不引入新符号、幅度或传播图；不是新一轮收缩扫描，也不是 R13 的邻居表达均值。这里只有一个新的重建操作。

**检查与停止。** 先比较供体和新矩阵：若每列原先就是 WT 的单调变换，操作可能完全无变化，记录 NO_OP，不注册重复候选、不上传。若有变化，核对列多重集不变、每细胞 library size/细胞类型表达支持与空间结构无明显灾难。不能假定服务器 de_score 必然不变，因为完整服务器预处理未知。任一供体仅做一次；两者均不超过 incumbent+0.1，则本轮排序修复路线关闭。

这是本项目提出的算法消融，未宣称来自某篇论文，亦不主张 WT 的真实 KO 协方差应当完全不变。

## 4. 方向二：WT 流形内的异质响应与状态占比变化

**假设。** Gata4 缺失可能使一部分细胞改变状态，而不是同一谱系所有细胞都叠加同一基因位移。现有 cardiac-full/else-half、SPLIT 只改变剂量门，未检验这种分布变化。

**输入与学习。** 仅用官方 E8.75 WT，在粗细胞类型内建立亚状态和局部邻域。用交叉拟合的 Gata4 活性/状态指标定义低活性参考池；排除 Gata4 本身，调节 library size、细胞周期、成熟度和空间区域，避免把测序深度或谱系区别当成响应。指标选基因只用 WT 与合规 topology，不能使用隐藏 KO 的 marker 或从分数推断 marker。

**最小实验。** 在粗细胞类型、空间区域与成熟度有共同支持的条件下，给高响应概率的 recipient 选择一个完整 donor 表达向量，或采用受限的状态运输；其余细胞保留 parent。第一版不改变粗谱系、坐标或 n_obs，也不直接套外部 atlas 的细胞比例。每次抽取整行表达，避免对 donor 做均值而压扁方差。固定两个构造：响应概率自适应分配，与相同替换数量、同分层的随机分配对照；不是两个任意剂量。

**缺口。** WT 低活性不等于 KO，表达自然变异无法识别敲除效果。响应比例来自 WT 支持范围内的建模假设，不能命名为“真实细胞死亡率”或“真实 KO 组成”；如果校正混杂后没有可分辨参考池，就停止。

**检查与停止。** 用 source-only 分组留出检查 donor 支持和表达分布，不把 cell split 当独立胚胎。共同支持不足或只能跨粗谱系强行替换时，BLOCKED_NO_SUPPORT。若适应性分配不优于随机对照且均不晋级，则不继续扫比例。

方法参考：[CellOT，DOI:10.1038/s41592-023-01969-x](https://www.nature.com/articles/s41592-023-01969-x)，[作者实现](https://github.com/bunnech/cellot)。CellOT 从已观察到的处理/对照分布学习运输，不直接解决本项目未见 Gata4 的零样本条件；这里是受其分布运输思想启发的 WT-only 假设，不能叫 CellOT 复现。

## 5. 方向三：保留细胞残差的稀疏条件机制

**假设。** 聚合级联把不同细胞的上下文和个体残差丢掉。改为学习稀疏条件方程，固定每个细胞的残差，再改变目标调控输入，可能减少同一 shift 强加给所有细胞造成的失配。

**最小模型。** 先限定在 500-gene panel 内。只用通过来源审计的有向拓扑；用层级收缩在不同细胞状态间共享系数，比较线性条件模型和有界非线性条件模型（如少量样条项），不先上大网络。固定有向无环近似，反馈边作为显式未建模部分登记，不把图环静默删掉后称全网络模拟。

对基因 g，拟合 `x_g = f_g(parents, context) + epsilon_g`；对原始 WT 行计算 `epsilon_g`，在该模型内执行 `Gata4 := 0` 后，按固定拓扑更新下游，并保留原 `epsilon_g`。末端只将预测响应加回 v0009 的对应行；零干预必须逐值复现 parent。非线性外推到 0 的行为须预先声明，不能把未观测到的 0 输入当已验证区域。

**对照与新颖性。** 同拓扑、同训练切分下的线性与非线性两版，仅改变条件机制。它不同于 R6 对 76 个状态聚合模拟量后生成统一幅度，也不同于按 Knk 排名指定幅度；不使用真实模拟输出作因果真值标签。

**检查与停止。** 观察性 held-out gene/WT 预测只能验证拟合，不能证明 KO 正确。若可为 Mab21l2 建立合法的相同模型入口，可在源 KO 做一次锁定的独立检查；若该基因无适用拓扑，明确 NOT_APPLICABLE，不能强行套 TF knockout 接口。无干预复现失败、响应完全由任意断环选择决定、零输入外推不稳定或大规模 clipping 时停。两个版本均不晋级时，关闭本轮条件机制，不继续加模型容量。

方法参考：[DoWhy 官方 counterfactual 文档](https://www.pywhy.org/dowhy/main/user_guide/causal_tasks/what_if/counterfactuals.html)：固定个体噪声的反事实计算需要比一般预测更强的模型假设。这里的 WT-only 结构无法据此获得因果可识别性，科学状态保持 NOT_IDENTIFIABLE。

## 6. 方向四：全转录组隐藏中介与逐细胞映射

**假设。** 500 genes 是输出约束，不一定是最佳内部表征。此前 S1A 已用过全转录组，因此“再跑全转录组 GRN”不算新方向。真正的新因素是保留 panel 外中介和逐细胞映射，替代跨状态平均后将结果投回 panel。

**输入。** `artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/data/` 的 `state_input_counts.mtx`、`state_input_genes.tsv`、`metadata_cells_sanitized.tsv` 当前存在。矩阵头实读为 27,669 genes × 68,910 cells；是 exact E8.75 sanitized WT。当前 bioinf 索引部分条目仍指向已清理的 v5：开工前修复引用、复核 v7 manifest 与任务许可；本提案未重哈希 3.9 GB 矩阵。

**最小实验。** 用 WT shared genes 建立空间细胞到 RNA 状态的映射；内部限制为 WT 选择的调控中介/模块，不密集拟合全 27,669² 网络。采用同一固定扰动算子，在“panel-only 表征”和“带 panel 外中介表征”之间做一对比较；后者把每个 recipient 的隐含调控状态响应映回完整 500 genes。保留原 MERFISH residual 和 platform scale，只传响应，不能以 scRNA 表达绝对值覆盖 MERFISH。

映射时预留部分 panel genes 做未参与对齐的验证，然后正式模型才用全部可用 WT panel；细胞/胚胎分组仍须独立。若任一响应中介的符号与幅度完全不可识别，报告该中介 unsupported，不把相关性包装成实测调控。

**检查与停止。** 同一扰动算子是识别“中介表征增量”的必要对照。留出基因预测不优于按细胞类型的简单基线、映射跨粗谱系、状态与符号映射丢失或全转录组资源无法按锁定方案完成时，停止；缩减基因集或细胞数需成为另一个明确的实验，不能声称全量完成。

方法参考：[Tangram，DOI:10.1038/s41592-021-01264-7](https://pmc.ncbi.nlm.nih.gov/articles/PMC8566243/)，[作者实现](https://github.com/broadinstitute/Tangram)。它支持 scRNA 与空间表达对齐；不提供 Gata4 KO 响应或 panel 外中介的因果验证。

## 7. 方向五：配体—受体约束的非细胞自主响应

**假设。** 某些 recipient 的响应由附近 sender 的信号变化决定。现有细胞自主位移和 R13 表达平滑均未检验这种模型。

**最小实验。** 在已观测的 WT 500 genes 内，先清点合规 ligand/receptor 覆盖。固定空间邻接与来源可追溯的拓扑；预测 sender 的配体变化，再通过 recipient 的受体表达与下游模块条件方程形成 `delta_neighbor`。最终 `X_new = X_parent + delta_intrinsic + delta_neighbor`。只传播响应信号，不能把 `X_parent` 乘邻接矩阵做均值。

同一 intrinsic 基线生成两个版本：signal-off 与 signal-on；空间距离尺度由 WT/source-only 拟合预先冻结。没有充分观测配体—受体时标记 BLOCKED_PANEL_COVERAGE；后续若借方向四补 panel 外信号，须另开组合实验，不隐式增加依赖。

**来源与风险。** 优先核对现有 OmniPath 资源，但“文件在盘”不等于所有边可用于新 run。缺许可、上游 evidence 或存在 target/phenocopy 来源的边不能进入。不能直接下载 NicheNet 默认 ligand-target 权重当成无污染真值。WT 空间共表达也可能反映同一谱系或解剖位置，不是通讯因果证据。

**检查与停止。** 本地 signal-on/off 加一个仅用于诊断的 sender-label permutation，对照邻接效应是否区别于一般平滑。标签打乱后不受影响、所有效果都来自 broad smoothing，或 signal-on 相对 off 无增量且不晋级时停。

方法参考：[NicheNet，DOI:10.1038/s41592-019-0667-5](https://www.nature.com/articles/s41592-019-0667-5)。论文提出 ligand 到 target 的信息整合；本提案只借其建模分解，不宣称复现了原模型或证实了胚胎通讯机制。

## 8. 方向六：真正训练多扰动的 gene-conditioned 模型

**假设。** 仅有 WT 和一个 Mab21l2 KO，无法提供充分的“改变哪个基因，会造成何种响应”的监督。引入合规、与目标无泄漏关系的多扰动训练，可能比手工 GO/PageRank 传播更适合预测未见基因。

**先完成数据任务。** 本轮没有发现已许可、可直接用于该训练的多扰动 processed 对象；7 个外部软链接不能视为模型输入许可。新 source 必须 metadata-first，排除 GATA4/GATA6/CTNNB1/MESP1、黑名单 GATA family、canonical WNT 与 cardiac phenocopy，且多基因组合中任一成员命中也应排除。随后冻结 source/过滤 mask/基因同源映射/训练与测试 perturbation 集。跨物种只保留明确的一对一同源关系，并保留丢失基因清单。

**最小实验。** 同一允许数据上先训练带 gene embedding 的 ridge/低秩监督模型，再比较真正训练的公开图条件模型。两者共享 WT basal representation，输出响应而非重建整个细胞；训练语料和知识图不允许含保护条件的响应真值。评估按整个 perturbation gene 留出，并在有数据时另留 cell context；随机拆同一基因的细胞不算 unseen-gene 验证。对 E8.75 的迁移仍只用合法 WT context。

**方法选择。** 可选公开 TxPert 架构或 GEARS。新方向是“可审计的多扰动监督 + gene-held-out 比较”，不是把 R10 图传播改一个名字。首轮只比较线性基线与一个神经模型，不同时装多个大型模型。

**门与停止。** 数据过滤后没有足够的非目标 perturbation 留出组，保持 BLOCKED_DATA_NOT_READY；不采用作者未知训练语料的 checkpoint 顶替。神经模型必须在同一 held-out genes 上超过 no-change 和监督线性基线，才值得继续投入；跨 cell context 无支持时只报告同域结果。不得由该验证直接宣称 beta-catenin hidden test 泛化。预算到期而训练未完成，记 NOT_RUN/INCOMPLETE 的具体部分，不改成手工位移后仍报训练成功。

来源：[GEARS，DOI:10.1038/s41587-023-01905-6](https://www.nature.com/articles/s41587-023-01905-6) 与 [作者代码](https://github.com/snap-stanford/GEARS)；[TxPert，DOI:10.1038/s41587-026-03113-4](https://doi.org/10.1038/s41587-026-03113-4) 与 [作者代码](https://github.com/valence-labs/TxPert)。TxPert 公开仓库只提供部分模型，论文部分高性能版本使用专有图，且代码采用非商业协议；不能把其论文最佳表现当成可直接复现的预期。

设置线性基线的依据：[Ahlmann-Eltze et al.，DOI:10.1038/s41592-025-02772-6，PMID:40759747](https://pubmed.ncbi.nlm.nih.gov/40759747/)。该比较支持认真设置简单基线，不证明所有神经方法无效，也不提供本比赛的提分保证。

## 9. 本轮共同执行设计

### 9.1 先冻结输入和评价口径

- incumbent 使用 `T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all`；v0010 保留现状。方向一的 lineage parent 是各供体 v0022/v0023，评价 incumbent 仍为 v0009；其他方向以 v0009 为 parent。完整路径、SHA 从 INDEX 读取，不另造版本身份表。
- 校验源 WT 行映射与 parent 恒等重建；正常路线固定 7,449 行、500 genes、顺序与 spatial_3D。当前 board 缓存范围为 1,000–7,449 行，固定 7,449 是本实验控制变量，不声称是官方唯一要求。
- 只读取 `docs/batch2/compliance/{DATA_FIREWALL_SPEC.md,protected_windows.yaml,target_leakage_blacklist.tsv,external_sources.tsv}` 的实际文件；旧规范中示意的 `infra/external_data/registry/` 当前不存在。
- 科学 S1 链仍关闭。任何复用只在新 prediction run 的许可与 contract 中明确，不能把旧 HOLD 组件重标为已验证 signed evidence。`blocks_submission: false`，不能为了不可达的科学门阻止其他合规预测路线。
- 本地官方缓存只展示 T3 的五个评分子项；旧调研“把 11 项平均推算 70+”的说法不作为本轮决策依据。不反推隐藏靶表达，也不把 rounded skill 算出的数替代服务器 board score。

### 9.2 处理 proxy 失配

分清三种检查：WT 留出只验证表示/重建；Mab21l2 的正确源 KO 实验只能检验该源扰动；Gata4 真实表现只能由服务器仲裁。若算法支持 Mab21l2，必须在 E9.5 输入上明确预测 Mab21l2，不能拿 E8.75 的 Gata4 候选直接对比 E9.5 Mab21l2 真值并称目标匹配验证。

任何用于拟合或调参的 KO 细胞不得又作独立验证。优先按真实 embryo/sample 分组；当前 WT 的独立 replicate 信息未就绪，不预设存在生物学重复。若只有同一样本的空间 block 留出，就如实报告为块外预测，并保留 batch/stage 与 perturbation 混杂的限制。

每路线必须覆盖完整正式 500 genes/锁定 recipient 范围；采样只能用于明确标注的 smoke。计算未跑、不能跑、核心被缩减，都写入结果，不由预检代替。

### 9.3 最小检查和服务器规则

仅检查候选 contract、身份、该路线应保持的不变量，以及 library/variance/空间结构的灾难性变化；不重跑全仓测试。对自身有预测意义的留出可以给路线比较证据，但不能取代 Gata4 评分；受 WT 假设限制的路线明确作为低置信度探索候选。

每路线最多首轮 2 个有明确对照意义的候选，完全相同的不上传。采用当前项目 ±0.1 TIE 规则：相对 incumbent 超过 +0.1 才晋级；区间内留任；低于 −0.1 淘汰。不得在看到分数后改门槛。子项变化用于解释，不按“de 必须增加”单项否决可能有整体增益的候选。

预算与上传配额沿用本地已记录的 8/task/day；实际提交前核对当日额度及规则是否变化。首批建议只做方向 1、2：合计最多 4 候选；如果方向 1 是 NO_OP，则只提交方向 2 的有效对照。第二批做方向 3，再依据输入就绪度决定方向 4/5；方向 6 独立处理数据准备。

每批一份 zip、短成员名与 MANIFEST/映射文件按 submissions/README.md。新 candidate ID 由执行时 INDEX 的 board 内版本分配，本提案不预占 v0026 等编号。评分后同步 INDEX、SERVER_SCORE_REGISTRY、15/相应数量子项、TRACKING、决策、LANE_VERDICTS 与 AUDIT；不能把打包、提交与服务器评分混为一项完成。

## 10. 本次交付与未执行项

- 交付 6 条新实验方向、与旧版本的区别、输入条件、成对对照、预算与停止条件。
- 查阅了官方论文页/作者仓库/官方方法文档；research-mcp 技能已读，但本会话未暴露 research_query/s2 工具，采用 web 检索补足。部分 Nature open 请求失败，使用检索到的原站正文、PMC 或作者仓库；未声称完整复刻论文。
- 仅核对本地文件存在、矩阵头和 manifest 引用，未重哈希大矩阵、未执行算法、未下载外部生信数据。因此本次不新增数据索引行；方向四指出的旧索引引用问题仍是执行前的具体修复项。
- 六条路线均为 PROPOSED / NOT_RUN。完整训练、full-panel scorer、新候选构建、上传全部 NOT_RUN，因为本次请求是路线提案。没有将缺数据路线静默替代为已有手工 shift。
