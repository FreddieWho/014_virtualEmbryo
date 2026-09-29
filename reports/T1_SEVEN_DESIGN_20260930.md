# T1 七路线设计冻结（2026-09-30）

用户要求3条新尝试、2条过去失败案例优化、2条过去成功案例优化；本轮属于行为变更，完整实现、全量执行和针对性验证，不上传。当前权威best v0035=53.43，v0036=53.36为±0.1内备份；旧T1全部回分。历史报告中的未评分/旧best为当时状态，以SERVER_SCORE_REGISTRY为准。

## 文献检索与迁移边界

检索日期2026-09-30，research-mcp端点不可用，转web查原文。未下载外部生信数据。

- Hainmueller (2012), *Entropy Balancing*, DOI [10.1093/pan/mpr025](https://doi.org/10.1093/pan/mpr025)，[作者原文](https://www.mit.edu/~jhainm/Paper/eb.pdf)。矩约束调整样本权重启发n1；本实现为惩罚对偶目标＋有界权重，不声称精确矩平衡或因果估计。
- Schiebinger et al. (2019), *Optimal-Transport Analysis of Single-Cell Gene Expression Identifies Developmental Trajectories in Reprogramming*, DOI 10.1016/j.cell.2019.01.006，[原文](https://www.broadinstitute.org/files/publications/2019/03/1-s2.0-S009286741930039X-main.pdf)。支持从不同时间点分布研究发育的建模方向，不提供本赛题配对真值。
- Bhatia, Jain, Lim, *On the Bures–Wasserstein distance between positive definite matrices*, [原始论文页面](https://www.sciencedirect.com/science/article/pii/S0723086918300021)。Gaussian协方差传输启发n2；网页摘要可检索、全文403，公式将用已知协方差运输恒等式测试。不是Waddington-OT完整复现。
- Zhou et al., *Learning with Local and Global Consistency*, NeurIPS 2003，[原文](https://papers.nips.cc/paper/2506-learning-with-local-and-global-consistency.pdf)。n3借鉴邻接平滑，本实现采用row-normalized图的正则解；不声称与其归一化算子完全相同。
- Huang et al., *Correcting Sample Selection Bias by Unlabeled Data*, NeurIPS 2006，[原文页面](https://papers.nips.cc/paper_files/paper/2006/hash/a2186aa7c086b46ad4e8bf81e2a3a19b-Abstract.html)，用于区分直接矩匹配与原logistic密度比。未实现或冒称完整kernel QP。
- 检索亦覆盖PRESCIENT DOI 10.1038/s41467-021-23518-w 与 TrajectoryNet arXiv:2002.04461；本轮不把缺少时间点支持的连续动力学网络当作七条实现之一。误打开的arXiv:1711.00766为无关物理论文，排除。

## 固定实现与对照

共用已评分v0035的mass整行库与类型配额，复用冻结训练模型是明确设计；新模型局部仅训练于旧60%训练细胞，最终全E8.5/E9.5。全基因SVD冻结表示32维，n1/n2使用前8维；所有输出和scorer输入保持32285基因。以下“新”指项目新增算子，不是学术原创。

| 类别 | 路线 | 核心变化及可证伪问题 |
|---|---|---|
| 新1 | n1moment | 标准化8PC的一二阶矩，阶段差半步形成目标；最小化logsumexp对偶＋0.1 ridge，theta∈[-2,2]；recipient logweight居中并clip±log2。替换logistic权重，按v0035类型配额一次整行采样。直接矩约束是否比分类密度比有效？ |
| 新2 | n2covot | 每类型8PC covariance加0.1对角收缩，Gaussian SPD最优运输矩阵；mean/cov位移强度0.5。将v0035 donor的latent坐标映射后投影到同类型recipient最近整行mass donor，不decode低维均值、不做伪谱系配对。协方差变化是否提供增益？ |
| 新3 | n3graph | 类型内训练stage图15NN，对称距离核后row normalize，解(I−0.8P)f=0.2y；query16近邻平均并排除相同行ID、校正阶段先验，logit居中clip±log2，按固定配额整行采样。阶段密度非线性边界是否有用？ |
| 失败优化1 | f1soft | v0031 n3states服务器50.51且局部五项差。硬KMeans改8个以内diag-GMM软责任，每组件10伪计数，阶段比例log增量×0.5；与原logistic logweight各半，再clip±log2，以mass＋composition骨架采样。软边界与平滑是否缓解碎片化？ |
| 失败优化2 | f2stable | v0033 o2shrinkmass=51.10，低于原mass组件v0027=51.38。原方案普遍按方差缩步；本轮把每阶段训练细胞固定分4份，零率变化、阳性均值变化分别需≥3份符号一致才保留对应原mass步长，否则乘0.25；qout仍投影非负单调。加入v0035同一joint采样。只惩罚方向不稳者能否保留有用幅度？ |
| 成功优化1 | s1growth | v0035联合组成＋密度成功：仅把组成log趋势强度0.5提高到0.75（倍率仍0.5–2，伪计数0.5），mass与密度不变。是否仍有组成增益空间？ |
| 成功优化2 | s2mix | v0035与v0036均获服务器支持；固定70/30分层整行混合，不平均表达。是否保留v0035方向与v0036 DE/共变取舍？ |

失败原因是待检验假设，不由旧总分唯一识别。f1/f2同时继承新成功骨架，故对旧版本总体改善不能单独归因于局部修复；必须同时报告相对v0035的结果，不声称消融证明。

## 执行、限制、停止规则

独占脚本/配置/tests/报告/不可变run路径，先登记lease。七条report与future模型均实际构建，保存训练参数和donor身份；对v0035/v0036进行report/future逐值复现。report沿既有60/20/20，3357早期recipient/3411晚期target；final全部16787/17057细胞，预测5118×32285。七次完整panel官方scorer必须执行，不以smoke、小panel或廉价指标替代。旧report反复探索过，不算独立胚胎或E10.5验证。

预先固定参数见configs/t1_seven/design_20260930.json；不根据本轮结果调参。优化器/线性求解必须收敛，工程门/no-op失败保留完整研究输出和真实状态，不降门救结果。候选通过contract后才入INDEX，score_pending，禁止冒称服务器改进。工程有效路线可打一个短名包，失败路线不进包；实现七条不等于保证七条科学成功。

目标KO无关，T1隐藏E10.5/E12.5真值均NOT_RUN_NO_TRUTH；所有科学阻塞blocks_submission:false。现best在服务器证据前不变，无新数据索引更新需求。完整单元测试只覆盖新增关键算子及泄漏/身份边界；独立进程重放和完整评分验收后收口。
