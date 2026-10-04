# Research: T2:heart:val_interp 空间-时间预测 — 3 条候选路线研究简报

## Summary

heart:val_interp 的 E8.5 目标是 E8.25_late 与 E8.75 之间**精确中点**的插值，因此任何"沿发育时间做量插值"都退化为两侧量的等权平均；现役 62.04 路线的本质是**秩-0 空间项**（逐细胞类型均值平移），它的经验变异函数（variogram）几乎处处接近 0，与"variogram 子分约 28 分是明确 headroom"的诊断完全吻合。因此本简报给出 3 条路线：**A 直接把二阶结构（变异结构/功率谱）作为被预测量做匹配式合成**（正对 variogram headroom）、**B 用可解释的解剖坐标基替代秩-0 均值项**（把"位置函数"而非"细胞类型常数"作为被预测量）、**C 对现役赢家做秩-k 空间特征模态迁移的迭代**（严格推广 L1/L2，可 k=0 优雅退化回现役结果）。

**证据等级声明（重要）**：本次运行环境只有 `web_search`，**无 `fetch_content` / `source_check`**，因此所有引用仅核验到"搜索结果中出现的标题 / 期刊 / 年份 / DOI-URL / 摘要片段"这一层，**未读全文**。凡涉及方法内部细节的表述均按摘要片段措辞转述，未做全文确认。另外**官方 variogram 子分的具体定义无法查证**（无契约/服务器访问权限），下文所有"对子分的预期影响"都是基于子分名称的假设，不是结论。

---

## Findings

### 0. 关键结构事实（决定了三条路线的设计空间）

1. **Claim:** E8.5 在 E8.25_late 与 E8.75 之间是精确中点（等间隔半胚胎日）。**Sources:** 任务书给定的阶段表（内部事实）。**Support:** direct evidence（题面）。**Confidence:** high。**推论（researcher inference）：** 任何沿发育时间的插值量（模态幅度、坐标回归系数、变异结构参数）都取两侧等权平均；唯一"非平均"的信息来自**形态/几何随时间的变化**（pycpd 位移场），这正是现役路线已经吃掉的部分。
2. **Claim:** 现役 62.04 路线的表达项是逐细胞类型均值平移（秩-0，常数于空间），L1→L2 的 +0.5 来自组成重采样（occupancy_dice 46.6→51.2），与"表达空间结构"无关。**Sources:** 任务书内部实测。**Support:** direct evidence。**Confidence:** high。**推论（researcher inference）：** 秩-0 项对任意滞后 h 的半方差贡献为 0，即预测场的经验 variogram 形状由"随细胞类型跳变的分类块"决定，块内无结构；这与 variogram 子分低分是同一件事的两种说法。
3. **Claim:** 心脏 E8.5 处于心管**环化（looping）**阶段，形态拓扑与 E8.25/E8.75 不同。**Sources:** 任务书阶段设定（E8.25/E8.5/E8.75 均为心脏形态剧变期）；发育生物学常识。**Support:** interpretation。**Confidence:** medium-high。**含义（researcher inference）：** 任何依赖"解剖坐标在目标阶段可直接从几何定义"的方案，坐标定义本身就是最大失败点（见路线 B 的风险）。
4. **Claim:** 板面规模为源阶段 24k–59k 细胞、目标 5872 细胞（官方真值 1185），500 基因，3D 坐标，行序与坐标不可改。**Support:** direct evidence（题面）。**Confidence:** high。**算力推论（researcher inference）：** 500 基因 × 3D FFT 场合成若用 128³ 网格需 ~8 GB（float64）/ 4 GB（float32），需按基因流式生成或按"归一化变异曲线聚类"降维到 ~20–50 个场；用 64³ 网格（262k 体素）则 500 基因 float32 仅 ~0.5 GB，完全 CPU 可行。

---

### 路线 A — VMS：变异结构匹配式合成（Variogram-Matched Surrogate field synthesis）

**机制（3–5 句）**
1. 不动现役的 pycpd 配准与秩-0 均值桥（它已在服务器上被正向验证），只在它之上**再加一个零均值残差场**。
2. 在每个源阶段自身的坐标上，对每个基因计算 log 归一化表达去掉"逐细胞类型均值"后的**残差场**，估计其经验变异函数 γ_g(h) 与对应功率谱 S_g(k)（用矩估计/加权最小二乘拟合 Matern 或指数族 + nugget；并按 MERINGUE 的思路**对非均匀细胞密度做校正**，因为 MERFISH 面板的细胞密度在心肌/腔壁之间差异很大，直接估 variogram 会被密度项污染）。
3. 以估计到的 S_g(k) 为谱，在**目标细胞的 3D 网格**上生成 M 个零均值高斯场实现：对周期延拓后的谱乘高斯随机相位后逆 FFT（circulant embedding / 谱合成），再在 5872 个目标细胞坐标上采样；把实现按基因做秩变换/裁剪到非负，得到"纹理"项 T(x)。
4. 合成 λ 与逐基因幅度，使**预测场自身的经验 variogram 在一组固定滞后上匹配源阶段的 γ**（第二阶一致性标定，不看服务器分数）；E8.5 取两侧参数等权平均。
5. 最终提交 = 秩-0 均值桥（不变）⊕ λ·T(x)，λ=0 时精确退化为现役 62.04 结果。

**文献锚点**
- Miller BF, Bambah-Mukku D, Dulac C, Zhuang X, Fan J. *Characterizing spatial gene expression heterogeneity in spatially resolved single-cell transcriptomic data with nonuniform cellular densities.* Genome Res 31:1843–1855 (2021). https://pubmed.ncbi.nlm.nih.gov/34035045/ — 可迁移部分：其基于**空间自相关/互相关**的框架，以及在**非均匀细胞密度**下估计空间结构的校正方式，正是本路线第 2 步所需（摘要片段：MERINGUE 用 spatial autocorrelation 与 cross-correlation 分析来刻画空间表达异质性）。
- Dietrich CR, Newsam BJ. *Fast and Exact Simulation of Stationary Gaussian Processes through Circulant Embedding of the Covariance Matrix.* SIAM J Sci Comput 14:108–128 (1993). https://dl.acm.org/doi/10.1137/S1064827592240555 — 可迁移部分：把任意平稳协方差的光谱转成网格上的快速精确实现，本路线的 O(N log N) 生成算子直接来自此（研究推断：更简单的"频域乘随机相位"版本在数值上等价于 circulant embedding 的对角化实现，代码量更小）。
- 补充（结构参数估计范式）：Li Q, et al. *Bayesian modeling of spatial molecular profiling data via Gaussian random field*（GPoSM 类框架，2021）. https://pmc.ncbi.nlm.nih.gov/articles/PMC9502169/ — 可迁移部分：把表达当高斯随机场并估计空间范围参数的做法（未读全文，仅据摘要层面判断为该范式）。

**与已关闭 5 轴的距离**
- 非 FGW/OT：没有行-点配对、没有 pairwise cost 矩阵、没有传输计划；只在给定坐标上按协方差生成噪声。
- 非"空间平滑位移场"：本路线**增加**高频结构而非平均掉高频；被平滑的位移场完全未触碰。关键区别是它在"表达"上加结构，不在"位移"上去结构。
- 非位移幅度族：位移场逐字节沿用现役版本，λ 只作用于零均值纹理项。
- 非深度结构化时间外推模型：无生成模型、无 ODE/SDE/扩散，核心算子是 FFT。
- 非"均值位移"朴素变体：均值项完全不变，新项按构造零均值、跨细胞类型共享谱。

**可实现性判断**
- 可识别：滞后尺度（哪一档 h 上方差开始饱和）、各向异性方向、幅值随发育阶段的变化——只要这些在 E8.25→E8.75 之间近似连续。
- 不可识别（诚实声明）：**相位**。任何满足同一 γ 的场在统计上等价，本路线无法判断某个局部高表达斑块应该落在哪里；它只能给出"统计上正确"的纹理，不能改善逐位置精度。这也意味着它**在原理上不能提升 de_direction**（除非相位恰好由现役配准提供）。
- 额外不可识别：源阶段间纹理谱是否已发生形状变化（只能用两侧平均，无法验证）。

**预期失败模式**
- 最可能：以"加入的是噪声而非信号"失败——variogram 子分持平或略升，但 de_score / mmcd_u 下降。
- 特征签名：预测场经验 variogram 与目标匹配（自检可测），但 de_direction 转负；或 variogram 只在 h 极小档改善而在主滞后档偏离。
- 次要失败：谱估计被密度不均污染 → 纹理呈"贴在细胞密集区"的假象，自检中表现为预测纹理与目标细胞密度场强相关（可用一个"只置换密度的对照场"排除）。

**对官方子分的预期影响（假设性）**
- variogram：**唯一直接针对项**，预期 ↑（这是设计目标）。
- d2_shape：可能轻微 ↓（新增高频使场"更碎"，若 d2_shape 奖励粗尺度形状一致性）。需配套对 λ 做保守标定。
- occupancy_dice：中性（细胞类型标签完全不动；这是它相对 L2 安全的最大优点）。
- de_score / de_direction / mmcd_u：风险为负向，因为纹理相位不可识别。**建议以"仅当 variogram 升幅 > de 掉幅"为晋级门槛。**

---

### 路线 B — A2C：解剖坐标条件回归（Anatomical-Axis-Conditioned basis regression）

**机制（3–5 句）**
1. 从**纯几何 + 细胞类型标签**（不用表达）构造少数几个低维、可解释的解剖坐标：(a) 心肌细胞云的测地骨架化得到的"流出道/房室交 → 心尖"弧长坐标 u；(b) 到心外膜（外轮廓）的带符号距离 v（区分壁层心肌 vs 腔壁/小梁）；(c) 沿现役 pycpd 位移场方向的归一化位移深度 w。
2. 这些坐标在源阶段各自直接计算，再**通过现役 pycpd 流场搬运**到目标细胞上（复用已验证的配准，不改其任何参数），因此目标端坐标是由目标几何导出的，绝不触碰目标真值。
3. 对每个基因 g 与细胞类型 c，堆叠 E8.25 与 E8.75 两阶段细胞拟合张量积三次 B 样条基回归：log1p(expr) ~ B(u,v,w) + stage 因子项；E8.5 是精确中点，故系数取两侧等权平均。
4. 在目标细胞坐标上求值该基得到"平滑位置趋势"，用它**替代**秩-0 均值项作为表达场主体（可选叠加现役 L2 的组成重采样以保住 occupancy_dice）。
5. 约束：基阶固定为每轴 3–5 个节点（总维数 ~30–80），用岭回归；不做逐基因的服务器分数调参。

**文献锚点**
- Aviñó-Esteban L, Cardona-Blaya H, Sharpe J. *Spatio-temporal reconstruction of gene expression patterns in developing mice.* Development 152:DEV204313 (2025). https://journals.biologists.com/dev/article-pdf/152/4/DEV204313/3634871/dev204313_review_history.pdf — 可迁移部分：其核心做法是"**把问题拆成许多小的组织区域，在时间上对每个区域做插值**，从而得到平滑的时空表达轨迹"（摘要片段），并把多个静态阶段快照整合成连续的时空表达重建。与本路线共享一个关键主张：**空间结构应由局部组织区域/坐标承载，而不是由全局均值承载**。
- Wagner DE, Weinreb C, Collins ZM, Briggs JA, Megason SG, et al. *Single-cell mapping of gene expression landscapes and lineage in the zebrafish embryo.* Science 360:981–987 (2018). https://pubmed.ncbi.nlm.nih.gov/29700229/ — 可迁移部分：细胞状态在空间上是有结构的、可用少数"地标基因/解剖位置"来索引，支撑"表达 ≈ 位置的平滑函数"这一建模前提。
- 心脏侧的解剖-谱系对应（用于设计 u/v 坐标的生物学合理性）：Cui Y, et al. *Single-Cell Transcriptome Analysis Maps the Developmental Track of the Human Heart.* Cell Rep 26:1934–1950.e5 (2019/2020). https://pubmed.ncbi.nlm.nih.gov/30759401/ — 可迁移部分：以心脏发育轨迹的解剖顺序组织细胞状态；FHF/LVH 位置偏置可用作 u 方向的先验（相关证据：Galdos FX, et al. *Combined lineage tracing and scRNA-seq reveals the origin of…* eLife 2023, https://elifesciences.org/articles/80075 — 一心场 >90% 贡献左心室，提示位置与谱系强耦联）。

**与已关闭 5 轴的距离**
- 明确不是"空间 kNN 平滑"：本路线是**全局低阶、参数化、跨阶段共享的坐标基回归**（参数个数是几十，不是每点一个邻居），与 k=5 全胜但服务器全负的那个族在数学形式上相反（那族做局部平均，本路线做全局低秩展开）。
- 不是"均值位移"：均值位移的场在空间上是常数（秩-0）；本路线的被预测量随位置连续变化（秩-k，且支撑是 u,v,w 三个解剖轴）。"朴素变体"指的是换细胞类型编码方式，本路线换的是被预测量的**函数类**。
- 非 OT/FGW、非深度时间外推模型、非位移幅度调整。

**可实现性判断**
- 可识别：沿心尖-流出道轴、沿壁厚方向的**粗尺度梯度**及其在两侧阶段间的线性行为；这类梯度在心脏形态发生中是最保守的量。
- 不可识别（诚实声明）：E8.5 的真实解剖坐标。目标端的 u/v 完全继承 pycpd 的搬运结果，而 E8.5 恰是心管环化期，**"房室交→心尖"轴在 E8.5 可能根本不单调**；若坐标定义在此阶段退化，整条路线的梯度方向会系统性错误，且这类错误不会在源阶段的自检里暴露（因为自检也用同一套定义）。
- 不可识别：细胞组成在 E8.5 的变化（只能靠现役 L2 的重采样，属已知雷区）。

**预期失败模式**
- 最可能：**基函数阶数与真实变异结构错配**。低阶基（每轴 3 节点）给出的是极平滑场，会把短滞后纹理进一步抹平 → variogram 在小 h 档变得更差；高阶基则会把源阶段纹理过拟合搬运到目标，产生"看似有结构、实为阶段残留"的假结构。
- 特征签名：de_score 可能 ↑（粗结构位置对）但 variogram 持平或小幅 ↓；自检中若预测场在 h→0 处的 nugget ≈ 0，即为过平滑签名。
- 次要失败：骨架化/外轮廓提取在环化期不稳健 → 坐标场出现折返；自检指标：u 在目标细胞上的分布应单调可排序，若出现多峰/折返即判失败（这是廉价且必要的 fail-fast 检查）。

**对官方子分的预期影响（假设性）**
- d2_shape：**最可能受益**（场的主轴对齐器官解剖轴，而非仅几何搬运）。
- de_score / de_direction：中等概率小幅受益（粗梯度位置正确）。
- variogram：不确定；中长滞后可能 ↑，短滞后可能 ↓。这是本路线最需要先做的诊断（用源阶段自检画预测 vs 真实的 γ 曲线对比图）。
- occupancy_dice：中性（保留 L2 重采样即可）。

---

### 路线 C — RK：秩-k 空间特征模态迁移（现役路线的优化迭代）

**改什么、为什么这个板值得改**
现役 62.04 的表达项 = 秩-0（逐细胞类型均值平移）。本迭代**保留 pycpd 几何、保留 L2 组成重采样、保留均值作为截距**，只在其上把"去掉均值后的纹理"用 **k 个共享空间特征向量（空间模态）**表示，并把模态幅度沿发育时间插值。因为 L1 就是 k=0 的特例，本路线**结构上严格包含现役赢家**，k 选错时可用"逐 k 扫描 + 阶段留一法"在本地挑，且最坏可回退到现役结果——这是三条路线里唯一**下行风险有界**的。

**机制（3–5 句）**
1. 在现役 pycpd 配准后的**共同坐标框架**内，对每个源阶段构造"位置 × 基因"的场矩阵 F_s(x) ∈ R^{G}，先减去逐细胞类型均值（得到纹理），再在目标网格上用随机化 SVD 求前 k 个空间特征向量 φ_k(x)（k ≈ 5–20），得到跨阶段共享的空间基（"高表达沿 AP 轴 / 沿室间隔-壁侧轴"这类解剖轴）。
2. 对每个基因估计模态幅度 a_{g,k}(E8.25) 与 a_{g,k}(E8.75)；E8.5 为精确中点 → a_{g,k}(E8.5) = 两侧平均。
3. 在目标细胞上重构纹理 x ↦ Σ_k a_{g,k}(E8.5)·φ_k(x)，加回秩-0 均值项，输出 = 现役 62.04 场 + 模态纹理。
4. **k 的选择用阶段留一法**：用 E8.25 + E9.5 拟合、在 E8.75 上评估（E9.5 是本板可用的第三个阶段），而不是看服务器分数。
5. 幅度整体缩放按第二阶一致性标定：使重构场的 γ 在参考滞后上与源阶段一致（与路线 A 共享同一标定工具，但这里标定的是低频部分的幅度）。

**文献锚点**
- Gingerich IK, et al. *Randomized Spatial PCA (RASP): a computationally efficient dimensionality reduction method tailored for spatial transcriptomics.* PLoS Comput Biol (2025). https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013759 — 可迁移部分：可扩展的**空间主成分/特征分解**实现，正是本路线在 3D、24k–59k 细胞上求 φ_k 的算子。
- Okochi Y, Sakaguchi S, Nakae K, Kondo T, Honda N. *Model-based prediction of spatial gene expression via generative linear mapping.* Nat Commun 12:3731 (2021). https://www.nature.com/articles/s41467-021-24014-x — 可迁移部分：**用生成式线性映射把空间表达场分解到一个低维隐变量上**并据此重建空间表达（摘要片段：以高斯混合 + EM 做生成式线性映射，在果蝇/斑马鱼胚胎、哺乳动物肝脏、小鼠视皮层上准确重建空间表达，且"重建的转录组不会过拟合 ISH 数据"）。本路线把它的隐基从"细胞状态 GMM"换成"空间特征模态"，并把幅度沿发育时间插值。
- 心血管侧的解剖轴先验：同路线 B 的 Cui et al. Cell Rep 与 Galdos et al. eLife（用于解释 φ_k 的主轴是否对应真实解剖轴，作为可解释性检查而非拟合先验）。

**与已关闭 5 轴的距离**
- 不含任何 OT/FGW 配对；不含深度生成模型；不含位移场平滑或位移幅度调整（pycpd 位移场逐字节不变）。
- 与"均值位移族"的关系要说清楚：均值项**保留不变**，新增项是显式零均值、按空间基底展开的 rank-k 项，因此这是"把秩-0 推广到秩-k"，不是"均值位移的朴素变体"（朴素变体不改变被预测量的函数类）。
- 与路线 A 的区别：A 生成**高频宽带**纹理（相位随机、统计匹配）；C 生成**低频平滑**结构（相位由现役配准携带、位置确定）。二者对 variogram 的作用方向相反，因此**不应同时全量上线**；建议 C 先上、A 作为其高频补充分层叠加。

**可实现性判断**
- 可识别：哪些空间方向上的表达幅度在两侧阶段之间是可线性外推的（低维、低频，通常比逐基因逐位置更稳定）。
- 不可识别（诚实声明）：E8.5 的纹理是否已经出现**源阶段没有的新空间结构**（新生 chamber/隔形成带来的新轴）。低秩展开按构造无法凭空产生新轴——这既是它的稳定性来源，也是它的天花板。
- 不可识别：同一 k 下幅度应缩放多少（只能靠第二阶一致性，不能靠真值）。

**预期失败模式**
- 最可能：**过平滑**。空间特征向量按构造是低频的，若把它们加到一个已经很平滑的秩-0 场上，预测场的短滞后方差进一步下降 → variogram 小 h 档**变得更差**。
- 特征签名：de_score 持平、variogram ↓。廉价诊断：比较 k 与 k+8 的预测场 γ 曲线，若 k 增大反而使小 h 段方差更低，则该方向应直接停。
- 次要失败：模态跨阶段不连续（E8.25→E8.75 期间主轴已旋转）→ 幅度平均后两个阶段的主轴互相抵消，纹理趋近于零；自检：比较两侧 φ_k 的主方向夹角，>~30° 即判该 k 不可用。

**对官方子分的预期影响（假设性）**
- de_score / de_direction：中等概率 ↑（低频结构位置由配准确定，比路线 A 的随机相位可靠）。
- d2_shape：较可能 ↑（场的主轴与解剖轴对齐）。
- variogram：**双向风险**，取决于 k；中长滞后 ↑，短滞后 ↓。必须先用 E9.5 留一法在本地画出 γ 曲线对比再决定是否上线。
- occupancy_dice：中性（组成重采样不动）。
- de 相对 L1 的可识别增量：这是本路线唯一真正的"迭代增益"假设——若 C 也拿不到增益，则说明 62.04 已接近该 backbone 的信息上限，应转向注册（registration）质量而非表达侧。

---

## Contradictions

1. **"variogram 是最大 headroom"与"低秩/平滑方案可能进一步恶化短滞后变异结构"存在方向性冲突。** 架构重置文件把 variogram 标为 headroom（题面事实），但路线 B/C 的机制（平滑基 / 低频模态）都倾向**降低**短滞后方差。本简报的处理是：A 直取该指标、B/C 只在中长滞后受益且必须先做 γ 曲线自检。**这是 researcher inference 对指标定义的猜测，若官方 variogram 实际奖励的是粗尺度一致性而非细粒度纹理，则 A 的收益估计会显著偏高。**
2. **文献中的"在未观测中间时间点做插值"主流做法落在本项目已关闭的族里。** 检索到两篇明确以"预测未观测中间时间点"为目标的工作：(a) *Generative Modeling of Mouse Embryogenesis for Fate Mapping*（bioRxiv 2026, https://www.biorxiv.org/content/10.64898/2026.06.18.733286v1）明确"评估模型在未观测中间时间点预测基因表达分布的能力"，但其核心是配对 + ODE 生成模型，**落在已关闭轴 4（结构化时间外推的深度模型）**；(b) Aviñó-Esteban et al. Development 2025 走组织区域插值路线，落在本简报路线 B。**因此"未观测阶段插值"这个方向有可靠先例，但本项目能安全迁移的只有非深度的那一支。**
3. **跨阶段 kNN 探针的失败与路线 B 的局部-坐标主张。** 项目历史：早期"跨阶段 kNN 表达探针"在心脏上 de 方向为正但传递到全基因无收益。路线 B 在"局部"这一点上与该失败实验共享直觉。**我的判断（researcher inference）：** 失败的原因被项目记录为"panel 成功未传导 / 组成是雷区"，而非"局部插值不可行"；但由于无法重读该实验记录，此处标记为未解冲突——建议路线 B 必须在协议里显式区分"局部平均"（已被否）与"参数化坐标基回归"（本提案新增），并以前者的对照组形式实现以示区分。

## Missing evidence

1. **官方 variogram 子分的定义未知**（无契约/服务器访问）。它究竟是 (a) 比较预测场与真值场的经验变异函数，(b) 比较两者的空间自相关，还是 (c) 二者差值的能量距离——三种定义下 A/B/C 的收益排序会完全不同。**这是本次研究最大的未验证前提。** 建议：优先从历史服务器回填记录或官方契约文件中把该子分的实现取出来读一眼，再决定 A 与 C 的先后。
2. **参考源阶段的自检是否能替代真值评估。** 三条路线都依赖"用 E8.25→E8.75 的留一法推断 E8.25→E8.5 的表现"。但 E8.5 距两侧的距离只有半个胚胎日（E8.25→E8.5→E8.75 等距），**留一法的外推跨度与真实插值跨度相同，这是少见的、留一法与真实任务同分布的场景**——但我无法确认 E9.5 在留一法中的角色（E8.25→E9.5 跨度远大于真实任务，会高估方法的插值能力）。
3. **本板的可细胞类型标注清单与中心 E8.5 的形态拓扑。** 路线 B 的坐标定义依赖"流出道/房室交→心尖"轴在 E8.5 是否单调；未读数据，无法判断（按硬约束本简报未读取任何本地数据文件）。
4. **未找到可靠先例的方向（如实声明）**：(a) 用变异函数/功率谱匹配直接做"发育中间阶段空间表达场"的预测——检索未发现空间组学中已有工作这样做（所有命中都是"用 variogram 描述已观测样本的空间模式"，如 MERINGUE / GPoSM / STANCE，而非用它做跨阶段预测）。路线 A 的**组件**都有先例，**组合**无先例。(b) 把 B 样条坐标基回归作为跨发育阶段的空间插值器——无可靠先例，最接近的是 Aviñó-Esteban 2025 的组织区域插值（不同粒度、不同方法）。
5. **文献核验深度限制**：如上文所声明，所有引用仅核验到标题/期刊/年份/DOI/摘要片段层，未读全文；MERINGUE 的自相关具体算法形式、GPoSM 的具体似然、RASP 的具体分解设定均未从原文确认。

## Sources

- Kept: Miller et al., Genome Res 2021 (MERINGUE) — https://pubmed.ncbi.nlm.nih.gov/34035045/ — 空间自相关/互相关 + 非均匀密度校正，是路线 A 变异结构估计的直接方法学基础。
- Kept: Dietrich & Newsam, SIAM J Sci Comput 1993 — https://dl.acm.org/doi/10.1137/S1064827592240555 — 路线 A 的 O(N log N) 谱合成算子出处。
- Kept: Aviñó-Esteban, Cardona-Blaya, Sharpe, Development 2025 — https://journals.biologists.com/dev/article-pdf/152/4/DEV204313/3634871/dev204313_review_history.pdf — 路线 B 的核心先例（组织区域级时空插值，发育小鼠）。
- Kept: Wagner et al., Science 2018 — https://pubmed.ncbi.nlm.nih.gov/29700229/ — "表达是位置的平滑函数"这一前提的经典证据。
- Kept: Gingerich et al., PLoS Comput Biol 2025 (RASP) — https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013759 — 路线 C 的空间特征分解算子。
- Kept: Okochi et al., Nat Commun 12:3731 (2021) — https://www.nature.com/articles/s41467-021-24014-x — 低秩生成式线性重建空间表达场，路线 C 的建模范式。
- Kept: Cui et al., Cell Rep 26:1934–1950 — https://pubmed.ncbi.nlm.nih.gov/30759401/ — 心脏发育的解剖轴/谱系顺序，用于 B/C 的可解释性检查。
- Kept（仅作反例/边界标注）: *Generative Modeling of Mouse Embryogenesis for Fate Mapping*, bioRxiv 2026 — https://www.biorxiv.org/content/10.64898/2026.06.18.733286v1 — 证明"未观测中间时间点插值"是有先例的任务，但其机制落在本项目已关闭轴 4，故**不作为提案**。
- Kept（背景）: Su H, et al. STANCE, Nat Commun 16:1793 (2025) — https://www.nature.com/articles/s41467-025-57117-w — 线性混合效应 + 空间随机效应的 SVG 统计框架，可作为路线 B 系数岭惩罚选择的参照。
- Rejected: Hogg et al. 2014 SAGMB "Spatial transcriptomics: a genomic approach…" — 多次检索未取到可解析 DOI/URL，按"宁少勿滥"弃用（该文确实是 variogram 用于空间转录组的最早出处，但无法给出可解析引用）。
- Rejected: 各类 OT / FGW / moscot / CellOracle / MIOFlow / 扩散模型方法 — 全部落在已关闭轴，无检索价值。
- Rejected: 10x Genomics / 通用 ST 博客页、Sanger 博客、LinkedIn/Facebook/ResearchGate 摘要页 — 二手或营销来源，不作证据。

## Next steps

1. **先读官方 variogram 子分的实现**（从服务器回填记录或官方契约文件），因为 A/B/C 的收益排序完全取决于它的定义；这是唯一能显著改变结论的补充检索/取证。
2. **本地零成本判别实验（不需服务器）**：用 E8.25 + E9.5 拟合、E8.75 评估，画出三条路线预测场的经验 variogram 与 E8.75 真值场的 γ 曲线对比图。这是三条路线共用的、最便宜的 fail-fast 判据。
3. **对路线 B 加一个廉价坐标健康检查**：在目标细胞上统计 u 的单峰性；不单调即立刻停，不进服务器。
4. 若 variogram 定义确认是"细粒度纹理"型，则**优先 A（并把 C 的 k 压到极小或暂缓）**；若是"粗尺度一致性"型，则**优先 C，B 次之，A 可能无效**。

---

## PROVENANCE_LIMIT（由 coordinator 于 2026-09-27 补记）

本简报由 `researcher` 子代理产出，该环境**只有 web_search 可用**，无网页抓取工具。因此：

- 所有引用仅核实到「题名 / 期刊 / 卷页 / DOI 出现在检索结果中」这一层，**未读取全文**。
- 每条路线里描述的「可迁移部分」是 coordinator 与 researcher 基于**检索摘要与题名**的推断，**不是原文细节引用**。任何依赖具体公式、定理条件或实验结论的机制，必须先由 coordinator 用 `web_read` 核验原文后才可进入设计冻结。
- 本子代理未读取任何本地数据文件（无 bash 权限，且已明确禁止）；结论不涉及本地真值。
- 附带的 PROPOSED 路线均为**候选**，未经 coordinator 定稿与独立审稿，不得直接实施。
