# Research Brief：在空间转录组预测中保持/修复基因间联合（协方差/共表达）结构

> **证据层级的硬限制（必须先读）**
> 本环境的 `fetch_content` / `get_search_content` / `source_check` 不存在（调用即中止运行），因此**所有引用只核实到「题名 / 期刊 / 年卷页 / DOI 出现在 `web_search` 返回结果里」这一层**。我**没有**抓取任何全文，**没有**核对原文图表、公式细节或具体实验数字。凡涉及某论文"具体做了什么"处，均标注为**间接证据（来自摘要片段/引用列表）**；凡属我自己的推断，一律标 **[推断]**。
> 未被搜索结果直接印证的 DOI / 卷页号，我一律不写（Symphony 的 DOI 就是这种情况，我写的是能印证的卷页 15: 343–346 (2018)）。
> 输出路径由运行时指定为 `subagent-artifacts/.../research.md`（任务书中的 `reports/t2_nine_routes_research/...` 路径已被运行时覆盖）；文件只写这一次。

---

## 0. 摘要（直接回答）

**方向是成立的，而且文献支撑比预期强**：`variogram` 子分本质上是 proper scoring rule 族里的 **variogram score**（Gneiting & Raftery 2007, JASA），公开文献明确记载它「proper 但非 strictly proper，且相对 energy score 在**预测的协方差结构**上更有判别力」——与你们实测的"唯一约束联合分布的子分"完全吻合。域适应/单细胞文献中确实存在**显式对齐二阶结构**而非只对齐边际的成熟做法（CORAL / Deep CORAL、Seurat anchors 在原始表达空间核验、scDesign3 用 copula 保住 gene–gene correlation、TIME-CoExpress 直接预测沿轨迹的 gene pair 相关变化），代价分别是"协方差只能外推、不能识别"和"重建矩阵的相关被 rank 截断"。

**4 条候选机制**（详见 §2）：R1 整细胞/整块重采样（不产生算术平均 → 不衰减条件内方差）；R2 低秩因子 + 逐基因匹配的结构化噪声（NB/Poisson 因子模型）；R3 因子空间内的协方差校准（CORAL / Bures–Wasserstein 闭式，仅换色不白化）；R4 图邻域块重采样 + 去偏距离协方差/KSD 作为**无目标数据**的可微代理目标。

**最关键的诚实结论**：目标阶段协方差在"只有源阶段观测"下**不可识别**；因此所有方案都**不能**声称"匹配目标协方差"，只能声称"把源阶段协方差按一个可检验的演化律搬到目标阶段"。任何用到目标表达矩阵的做法都是泄漏。

---

## 1. 先把指标本身算清楚（决定 4 条机制的优先级）

评分器实现（题面给定）：对随机基因对 (i, j)，
`va_ij = mean_c |A[c,i] − A[c,j]|^0.5`，总分 = `mean_{i,j} (va_ij − vb_ij)^2`。

**[推断 A｜这个量是联合分布泛函，不是边际泛函]** `A[:,i]` 与 `A[:,j]` 是**两个不同基因在同一个细胞上**的取值，所以 `mean_c |A[c,i] − A[c,j]|^p` 正是"基因 i 与基因 j 的联合分布"的泛函（pairwise-difference moment）。因此你们"置换基因列 → 恶化 4.35×"的对照是对的结论；而"置换行 → 不可分辨"其实是**恒等变换**（整行置换精确保持联合分布），它只证明了该指标对**细胞身份/空间对应**不敏感，与联合结构无关。**这两条对照不矛盾，但其中一条的信息量为零。**

**[推断 B｜一个重要且可修的机制：均值位移会收缩该泛函]** 若预测 = 按细胞类型的条件均值 `m_t`（无残差），则 `va_ij = Σ_t w_t |m_{t,i} − m_{t,j}|^0.5`，只剩**类型间**跨基因的几何散布；真值还有**类型内**残差散布。对近高斯的 Z，Stein 引理给 `E|Z|^p = σ^p E|N|^p`（p=0.5 时 ∝ σ^0.5），所以**类型内残差的丢失会把 va 系统性压低**，而 `(va − vb)^2` 与 `vb` 的差距就被放大。这正好给出「现役方法 2.49× / 1.44× 更差」的**定量方向性解释**。⚠️ 这只是推断，**必须先做一个 5 分钟的数值验证**：在同一伪目标上，算 `f(σ) = mean_pairs E|N(σ)|^{0.5}` 对真实 `vb` 的敏感度，看"仅把每个基因的条件内方差从 0 拉到真值"能把分数拉回多少。若能拉回 >50%，R1/R2 只需做"补回残差"，不用碰联合结构。

**[推断 C｜诊断阶梯（建议按此顺序做，阈值必须 >4.2% MC 噪声）** 该量沿"信息量从少到多"有三层匹配：
1. **逐基因散布**：每个基因的 `E|X−EX|^0.5`（只需一维统计，500 个数）；
2. **基因对相关**：`corr(A[:,i], A[:,j])` 或 Spearman（500×500，log1p 稀疏下很稳）；
3. **pairwise-difference moment 本身**（评分器实际用的量，天然有偏但可直接对齐）。
配 6-seed 极差做显著性；**任何"我改善了 3%"的说法都应丢弃**。

---

## 2. 四条候选机制

### R1｜整细胞/整块重采样（"不平均，只重抽"）

**机制描述。** 完全不解构表达矩阵。预测的第 c 行 = **源阶段某个已观测细胞的整行 log1p 向量**（连同它的 3D 坐标、类型标签一起搬），只按目标时刻的组成/状态权重 `w_t` 做**有放回整行抽样**。因为每行都是真实细胞，它的 500 维共表达模式被**逐字保留**；变化的只有"哪些细胞状态以什么比例出现"。关键机制点：算术平均 `mean_{c∈t} x_c` 把条件内协方差按 `1/n_t` 衰减并把残差压成零，而整行抽样**不产生任何新的行**，因此不存在方差衰减。实现成本：`O(N·G)`（N=24k–59k, G=500 ≈ 30M 次浮点，秒级 CPU）。权重 `w_t` 可复用现役方法的组成估计（这是唯一需要承认不可识别的部分，见 §3）。

**文献锚点（可迁移部分）。**
- **scCODA**（Büttner, Ostner, Müller, Theis, Schubert; *Nature Communications* 12:6876, 2021, doi 10.1038/s41467-021-27150-6, https://www.nature.com/articles/s41467-021-27150-6）——可迁移：**样本级（sample-level）计数层级建模**，把不确定性放在"组成比例"这一层而不是基因层，即"整块/整样本"重采样比"逐基因扰动"更接近文献里的安全做法。⚠️间接证据（来自摘要片段/引用列表）。
- **Milo**（Dann et al.; *Genome Biology* 2021, PMC7617075, https://pmc.ncbi.nlm.nih.gov/articles/PMC7617075）——可迁移：**在 kNN 图邻域层面做重采样/计数**，即重采样单位是"空间上连贯的一群细胞"而非单细胞/单基因；这是"块重采样"的直接单细胞先例（R4 会重用这一点）。
- **LIGER / iNMF**（Welch et al.; Cell 2019；在线教程 https://welch-lab.github.io/liger/articles/online_iNMF_tutorial.html；GitHub https://github.com/welch-lab/liger）——可迁移：**shared factors 承载基因程序、dataset-specific factors 承载差异**，说明"要搬的是一个低维程序组合，而不是每个基因各自的偏移"。⚠️ LIGER 的原 Cell 论文 DOI 我未在搜索结果中直接印到，**不写 DOI**；另见 Welch 2019 *Genome Research*（PMC6716797）https://pmc.ncbi.nlm.nih.gov/articles/PMC6716797 作为方法学综述锚点。
- **Symphony**（*Nature Methods* 15: 343–346, 2018；卷页号在 https://experiments.springernature.com/articles/10.1038/s41592-022-01687-w 的引用列表中被间接印证）——可迁移：**用"跨数据集保守存在的基因–基因相关结构"来定义细胞流形**，即参考映射/对齐里确实存在以共表达结构为锚的做法。⚠️纯间接证据。

**与 6 条已关闭轴的距离。** 关键区分点：已关闭的 #6 是"**按细胞类型做均值位移**"，R1 是"**按（类型 × 源阶段）抽整行**"。差别不是"同一个想法换了个写法"：均值位移**必然**把条件内残差压到 0（方差衰减 1/n_t），整行抽样**必然**不产生任何新分布形状。二者在 §1 推断 B 的预测上必然给出**相反**的分数方向。这条可以用一次对照实验证伪（把 R1 的行先求均值再抽 vs 直接抽），如果两者分数相同，则我的机制解释错了，R1 立刻降级。距离 #1（OT 行-点配对）：R1 是**离散重采样，不解算配对问题**，没有 ε 可调，数学对象完全不同。

**可识别性诚实陈述。** 可识别：源阶段每个细胞型的**完整联合分布**（经验分布，精确）；`w_t` 的可识别部分（若组成由坐标/形态决定，则坐标是可观测的）。**不可识别**：目标阶段的联合分布本身。R1 **不含任何"匹配目标协方差"的成分**——它把目标协方差当作 `w_t` 的函数，隐含假设 = "跨阶段共表达拓扑不变，只有组成权重变"。这是**假设**，不是从数据推出来的，必须在报告里这样写。若该假设在某个 board 上为假（例如某基因程序被真正关闭），R1 会系统性偏高，签名见下。

**预期失败模式与特征签名。**
- (a) 组成权重估错 → 边际子分（per-gene MSE）掉，但 variogram 反而变好（因为结构对、幅度错）→ **"variogram 好 + 边际差"的分离签名**。
- (b) 时间不连续 → 目标时刻的预测在类型层是**分段常数**的，per-gene 指标出现台阶状。
- (c) 极端不平衡型（占比 <1% 但生物学关键）→ 抽样噪声暴涨；签名是**同输入换 seed 的 variogram 极差 >> 4.2%**（若极差跳到 15%+，就是它）。
- (d) 源阶段数太少（只有 1–2 个源阶段）→ 联合分布的支撑集太小，重采样只是在放大源阶段的抽样误差。

**对 `occupancy_dice` / `d2_shape` 的影响：0（严格为 0）。** 因为行与坐标是一起搬的，抽出的行的 3D 坐标就是源阶段真实坐标。若重采样权重 `w_t` 与现役方法相同，两个纯坐标子分的**分布**不变，只是有限样本实现不同（抽样噪声）。**唯一例外**：若你为了消除 (c) 的噪声而改用"分层确定性抽取"（每型抽固定个数），则细胞数分布被人为拉平，`occupancy_dice` 会有轻微变化（方向取决于目标组成）——请在实现时保留"按 `w_t` 成比例抽样"而不是"等额抽样"。

---

### R2｜低秩因子 + 逐基因匹配的结构化噪声（"补回残差"而不是"重造结构"）

**机制描述。** 用 Poisson/负二项**因子模型**（`E[Y] = link(A·U + Z·G)`，`U`=低维程序得分，`Z`=基因-基因的偏移共表达项）拟合**源阶段**计数。预测时 `U_t` 由现役方法给出（可复用其均值位移结果），然后关键一步：**不输出 `Â = Â(U_t)`，而是从 NB 分布采样**，即 `Y_pred ~ NB(mean = Â(U_t), dispersion = θ_g)`，其中 `θ_g` 按每个基因在**源阶段的条件内**过散度标定后再沿时间线性搬运。这保证 (i) 条件内残差不再是 0（修 §1 推断 B），(ii) 逐基因的 `E|X−EX|^0.5` 落在源阶段标定的水平上，(iii) 跨基因的残差耦合由 `Z` 项承载而非被独立噪声抹平。实现成本：`O(N·G·K)` 采样 + 一次 `K≤30` 的因子拟合，CPU 分钟级。注意这是**生成式**的，输出可以仍然是稀疏 log1p 尺度的实数矩阵。

**文献锚点（可迁移部分）。**
- **GLM-PCA / fastglmpca**（Poisson 因子模型，R = A X' + Z G' + V U'，逐基因/逐细胞有专属参数；https://cran.r-project.org/web/packages/fastglmpca/vignettes/intro_fastglmpca.html）——可迁移：**逐基因过散度参数 + 低秩因子得分**，正是"匹配边际散布而不匹配联合结构"的最小可实现单元；也说明因子模型能在 24k–59k × 500 规模 CPU 跑通。⚠️间接证据（CRAN vignette 描述模型结构）。
- **NNSF**（Townes et al.; *Nature Methods* 2023, doi 10.1038/s41592-022-01687-w, https://experiments.springernature.com/articles/10.1038/s41592-022-01687-w）——可迁移：**"非负因子 + 逐基因/逐空间单元的异质噪声水平"**，即允许不同基因有不同噪声量级，避免用一个全局噪声参数把 500 个基因的散布抹平。⚠️间接证据。
- **FISHFactor**（Walter et al. 2023, PMC10176502, https://pmc.ncbi.nlm.nih.gov/articles/PMC10176502）——可迁移：**空间 + 非负因子分析的混合模型，显式建模基因特异噪声**，是"空间坐标 + 低秩 + 逐基因噪声"三者组合的现成模板。⚠️间接证据。
- **scDesign3**（Song et al. 2023, PMC11182337, https://pmc.ncbi.nlm.nih.gov/articles/PMC11182337；预印本 https://www.biorxiv.org/content/10.1101/2022.09.20.508796.full）——可迁移：**明确宣称在保持 gene–cell distances 和 gene–gene correlations 上优于前代模拟器**（"more realistic synthetic cells and in better preserving the gene- and cell-specific characteristics, especially cell–cell distances and gene–gene correlations"）。这是"边际 + 二阶同时匹配"在单细胞领域最直接的先例。
- **Copula modeling of gene coexpression**（Puritz & Braun, bioRxiv 2025, https://www.biorxiv.org/content/10.64898/2025.12.04.692380v1；PMC12710820）——可迁移：**六种 copula 在复现基因共表达上的精度/效率基准** = 现成的"哪一族联合结构更值得建模"的实验设计模板。⚠️预印本。

**与 6 条已关闭轴的距离。** 与 #5（结构化时间外推的深度模型：条件流匹配 / VAE+SDE / 扩散 / moscot / 生长-死亡动力学）**有实质距离但也有邻接风险**：R2 里的 `U_t` 若也由深度模型给出，就退化成 #5 + 一个噪声层。所以 R2 的正确用法是 **`U_t` 沿用现役方法的均值位移结果，只把输出层从"均值"改成"采样"**——这样改动被限制在最后一层，与 #5 的路径无关。与 #2（空间 kNN 平滑位移场）也有邻接风险：**不要**把 `θ_g` 或残差做成空间平滑场；残差应当只由 `U_t` 决定（因为 `U_t` 已含空间信息），否则就滑向已关闭的 #2。

**可识别性诚实陈述。** 可识别：源阶段的 `(Â, θ_g)`，精确。**不可识别**：目标阶段的 `(Â_t, θ_g,t)`。R2 的做法等价于假设 `θ_g` 沿时间**保守**（不变）——这比"目标协方差未知"更强，是一个**明确写下来的模型假设**。这里没有泄漏：R2 完全不接触目标表达矩阵。⚠️但要注意一个陷阱：如果有人提出"用目标阶段的无标签表达来标定 `θ_g`"，那**就是泄漏**（目标计数就是真值矩阵），本方向必须明令禁止。

**预期失败模式与特征签名。**
- (a) **rank 截断**：K=30 因子之外的真实相关（尤其负载低的基因对）无法表达 → 分数只从 2.49× 降到 ~1.2–1.5× 而无法接近 1.0；签名是**改善在少数高方差基因对上饱和，其他基因对不动**。
- (b) **采样噪声冒充结构**：过采样（`n_rep` 大）会人为压低 `E|X−EX|^0.5` 的估计（多重共线），导致"参数看起来对、分数反而变差"；签名是 **Monte Carlo 极差随 `n_rep` 增大而增大**。
- (c) **离散化伪影**：`Â(U_t)` 在 log1p 上做 NB 采样再取 log，引入 Jensen 偏倚；签名是低表达基因被系统性高估。
- (d) 逐基因 `θ_g` 搬运假设被破：`variogram` 改善但 per-gene MSE 同步恶化，且**恶化集中在高表达基因**。

**对 `occupancy_dice` / `d2_shape` 的影响：0。** R2 完全不动坐标。

---

### R3｜因子空间内的二阶校准（CORAL / Bures–Wasserstein 闭式；只"换色"不"白化"）

**机制描述。** 把表达矩阵分解为「条件均值部分（不动）」+「低秩因子得分部分（校准）」。对因子得分子空间 `Z`（维度 K≤30），构造一个闭式线性映射，使其**协方差**从源阶段的 `Σ_src` 变为**外推得到的** `Σ̂_tgt`：
- CORAL 形式：`A = Σ_src^{1/2} (Σ_src^{1/2} Σ̂_tgt Σ_src^{1/2})^{1/2} Σ_src^{−1/2}`，逐 Frobenius 距离最小（Sun & Saenko 2016）；
- Bures–Wasserstein 形式：直接用高斯间 2-Wasserstein 的闭式 `W² = ||μ_s−μ_t||² + tr(Σ_s + Σ_t − 2(Σ_s^{1/2}Σ_tΣ_s^{1/2})^{1/2})`（可微、处处可导，含退化协方差）。
**关键实现约束：把 `A` 只作用在因子得分上，条件均值部分原样保留。** 若把 `A` 作用在整行表达上，`A^{1/2}x` 会把类型谱几何一起扭曲，`d2_shape` 会受损。`Σ̂_tgt` 的构造必须是**跨时间的可检验外推**（例如在 SPD 锥 / log-Euclidean 度量下对源阶段序列做测地线外推，或对 `Σ` 的 log-特征值做线性外推），**绝不能**来自目标数据。500×500 的特征分解在 CPU 上 <1 秒。

**文献锚点（可迁移部分）。**
- **CORAL / Deep CORAL**（Sun & Saenko；CORAL: arXiv:1612.01939 https://ar5iv.labs.arxiv.org/html/1612.01939；Deep CORAL: arXiv:1607.01719 https://arxiv.org/abs/1607.01719）——可迁移：**"用协方差（correlation）作为显式可微损失"这件事本身**，正是本任务缺的那一维；且明确无需目标标签。间接证据：搜索片段确认 loss 定义为两域特征协方差的平方 Frobenius 距离。
- **Bures–Wasserstein**（*Geometric Dataset Distances via Optimal Transport*, NeurIPS 2020, https://papers.neurips.cc/paper_files/paper/2020/file/f52a7b2610fb4d3f74b4106fb80b233d-Paper.pdf；实现见 POT `ot.gaussian` https://pythonot.github.io/gen_modules/ot.gaussian.html）——可迁移：**高斯协方差间有可微闭式距离**，使"校准协方差"变成一次梯度步而非 OT 求解。
- **Bures–Wasserstein 域适应**（Jin et al., NeurIPS 2020；间接来源：NeurIPS 2020 poster "Entropic Optimal Transport between Unbalanced Gaussian..." https://neurips.cc/virtual/2020/public/poster_766e428d1e232bbdd58664b41346196c.html，间接提及 Wasserstein-Bures 距离用于 UDA）——可迁移：把 BW 当作**目标函数**而非配对求解器。

**⚠️ 与已关闭轴的距离——这是 4 条里距离最需要坦白的一条。** 已关闭 #1 是「最优传输 / FGW **行-点配对**（含 ε 微调）」。Bures–Wasserstein 在**数学上是 OT 家族**。我的判断：把它用作**对协方差参数的一步闭式/梯度更新**与 FGW 的**行-点配对求解**在算法对象上不同（前者只动两个 500×500 矩阵，后者解 24k×59k 的分配问题），但**若团队纪律上认为"任何 OT 家族都算已关闭"，则 R3 只能保留 CORAL 分支**（纯 Frobenius，不涉及任何传输/分配）。**建议按 CORAL 分支执行，BW 作为可选升级并显式记录它与 #1 的边界。**

**可识别性诚实陈述。** 这是 4 条里**识别性问题最尖锐**的一条。请逐字写进报告：
- 源阶段的 `Σ_src` 精确可识别。
- `Σ̂_tgt` **在无目标数据时不是估计量，是外推/先验**。SPD 锥上的测地线外推隐含假设"协方差沿发育时间沿最短路径演化"，这是一个**未经验证的模型假设**；若真实协方差演化中出现基因程序开关（loading 归零），外推必然失败。
- **因此：任何"我们匹配了目标协方差"的措辞都是错误的。** 正确措辞是"我们把源阶段协方差按一个可证伪的时间演化律外推到目标阶段，并检验该外推在**留一阶段**（leave-one-stage-out）下是否成立"。留一阶段检验是本路线**唯一**的合法内部验证，且它用的是**源阶段内部**的数据，不构成对目标阶段的泄漏。
- 泄漏红线：`Σ̂_tgt` 的构造若用到目标阶段的任何表达统计（哪怕是无标签的 PCA），即为泄漏。

**预期失败模式与特征签名。**
- (a) **协方差外推过冲**：leverage 较大的方向被放大 → 低表达基因对出现负相关/过相关，签名是**分数在 K=30 的前几个方向上明显改善、后几十个方向恶化**，总体净收益 <0。
- (b) **SPD 病态**：`Σ_src` 近奇异（500 基因、稀疏 log1p、n=1500 子采样）→ `Σ^{1/2}` 数值不稳；签名是**结果随 `n_cells` 采样量变化剧烈**。必须加 ridge / 用 `log-Euclidean` 度量。
- (c) **因子截断与校准冲突**：校准只在 K 维子空间进行，剩余 `500−K` 维的相关完全不动 → 签名是**改善在 top-loading 基因对上饱和**。
- (d) 若误把 `A` 作用到整行：`d2_shape` 下降（见下）。

**对 `occupancy_dice` / `d2_shape` 的影响：严格按上述实现为 0；若误把 `A` 作用到完整表达行则为非零**（`d2_shape` 会下降，方向不确定）。`occupancy_dice` 恒为 0（它只看点的占据，不看表达），除非把 `A` 当作坐标变换。

---

### R4｜图邻域块重采样 + 「无目标数据」的可微二阶代理目标

**机制描述。** 两部分。
**(a) 采样设计的部分。** 把重采样单位从"单细胞"换成"**kNN 图邻域**"（一组空间上连贯的细胞），整块一起抽走一起放入。这样抽出来的预测不仅保有行内共表达，还保有**局部细胞间**的相关结构（组成/程序在空间上成块出现）。实现：`make_nhoods` 式抽稀建图 → 邻域二值成员矩阵 → 按 `w_t` 加权抽块。成本：`O(N log N)` 建图 + `O(N·G)` 复制。
**(b) 代理目标的部分。** 因为**没有**目标真值来算 `variogram`，需要在**源阶段内部**造一个可微的、可优化的二阶目标：`L = (去偏距离协方差(Ẑ, Ẑ_ref))` 或 `L = KSD(Ẑ, ref)`，其中 `ref` 是**源阶段某个已观测阶段**或一个"协方差外推出的高斯参考"。这让重采样/混合权重 `w_t` 可以**在源阶段上被监督地优化**，从而不在目标阶段上调参——这是本方向绕开"目标协方差不可识别"的唯一干净做法。
⚠️ 高维警告（直接引文献）：在 `p, q → ∞` 而 n 固定时，**朴素样本距离协方差 `R_n → 1`**（即使真实独立），Székely & Rizzo 因此提出**去偏估计 `R*_n`**；高维距离协方差的渐近分布也专门被研究过。`500 维 × 1500 细胞` 正好落在这个病态区。**所以这里必须用去偏/线性时间版本，不能用朴素 `R_n`。**

**文献锚点（可迁移部分）。**
- **Milo**（Dann et al. 2021, Genome Biology, PMC7617075, https://pmc.ncbi.nlm.nih.gov/articles/PMC7617075）——可迁移：**部分重叠的 kNN 邻域 + 邻域级计数 + 显式纳入实验重复（donor/sample）设计**。这是"块重采样比逐基因扰动安全"在单细胞里最硬的先例。
- **scCODA**（Büttner et al. 2021, Nat Commun, doi 10.1038/s41467-021-27150-6）——可迁移：**把组成比例作为主要不确定性来源、把基因层留作条件**，与 R1 的"只动权重不动基因"同构。
- **Kernel Stein Discrepancy**（原始线性时间版 Jitkrittum et al., https://zoltansz.github.io/publications/jitkrittum17linear.pdf；**Learning the Stein Discrepancy**, Grathwohl et al., AISTATS 2021, https://proceedings.mlr.press/v119/grathwohl20a/grathwohl20a.pdf；**A Kernelised Stein Statistic for Assessing Implicit Generative Models**, NeurIPS 2022, https://openreview.net/forum?id=t4vTbQnhM8）——可迁移：**"不用目标样本、只用源样本的二阶/分布差异度量"** = 本任务需要的可微代理目标的形式。⚠️间接证据（确认题名/出处，未核原文）。
- **Székely & Rizzo 2013**（*JMVA* 117:193–213, https://pages.stat.wisc.edu/~wahba/stat860/pdf4/Energy/JMVA-t-test-2013.pdf）＋ **Asymptotic Distributions of High-Dimensional Distance Covariances**（https://faculty.marshall.usc.edu/jinchi-lv/publications/AOS-GFLS21.pdf）——可迁移：**去偏距离协方差 `R*_n`** 的构造与高维偏倚结论，决定 R4(b) 用哪个估计量。
- **TIME-CoExpress**（bioRxiv 2025, https://www.biorxiv.org/content/10.1101/2025.01.23.634392v1.full.pdf）——可迁移：**copula 框架直接建模并预测"沿拟时序变化的 gene pair 相关变化"，且允许协变依赖的零膨胀与相关变化**。这是"预测目标阶段共表达"最贴题的一篇，但**是预印本**。⚠️此组合无直接先例（发育阶段插值 + 空间坐标 + 该 copula 框架），组件先例即上列。
- **scTenifoldKnk / scTenifoldNet**（Osorio et al. 2022 Nat Commun, PMC9058914, https://pmc.ncbi.nlm.nih.gov/articles/PMC9058914）——可迁移：**用张量分解（CP/Parafac）从多份子样本去噪并平均出稳定的基因调控/共表达网络**，即"用重复子抽样得到稳定的相关结构"的工程套路。

**与 6 条已关闭轴的距离。** R4(a) 与 #6「朴素按细胞类型均值位移」距离最大（它连"均值"都不算），但要小心它与 #2「空间平滑」的重叠：**建 kNN 邻域**是用空间信息的。区别在于 R4(a) 用空间只是为了**定义采样块的大小**，不改变任何细胞的表达值；而 #2 是对表达/位移场本身做平滑。如果实现时用邻域平均去"平滑"块内表达，就跨界了——请写成"抽块"，不写"平滑"。

**可识别性诚实陈述。** 可识别：源阶段之间的 `w_t` 序列（可通过留一阶段的源-源插值来监督），以及源阶段的二阶结构。**不可识别**：目标阶段的二阶结构。R4 的正当性**完全**建立在"代理目标在源阶段的留一验证有效"上——即：**先用某个源阶段当伪目标，训练/选择流程，再去预测真目标**。这条留一阶段协议必须在交付物里写明它是唯一的内部验证。泄漏红线同上：`ref` 必须是源阶段构造的。

**预期失败模式与特征签名。**
- (a) **块太小或太大**：块太小 → 退化为单细胞重采样（≈R1）；块太大 → 空间组成被冻死，`occupancy_dice` 掉。签名：块大小扫描时 `occupancy_dice` 与 `variogram` **反向移动**。
- (b) **KSD/距离协方差在高维无信号**：500 维里只有前几维可辨识，梯度被少数基因主导 → **variogram 改善但 per-gene MSE 明显恶化，且恶化集中在同一小组基因上**（这是本路线最有辨识度的签名）。
- (c) **代理目标与真实指标不对齐**：代理目标（距离协方差）优化的量和 `E|Δ|^0.5` 的 pairwise-difference moment 不是同一个泛函 → 代理变好、真实分数不动。**这是最可能的失败，且必须先用**"同一伪目标上代理目标与真实 variogram 的秩相关"**来预检**；秩相关 <0.5 就不要往下做。
- (d) 单阶段/单胚胎的 board（无 donor 重复）→ 块重采样没有生物学重复锚，方块内部相关被高估。

**对 `occupancy_dice` / `d2_shape` 的影响：非 0，但是本方向里唯一可能非 0 的。** 块重采样会改变被占用位置集合 → `occupancy_dice` 会有小幅变化（通常在采样噪声量级，**若超过 4.2% 同类噪声需警惕**）；`d2_shape` 会因 3D 轮廓重采样噪声而轻微下降。若坐标子分不能承受任何损失，**优先用 R1（单细胞重采样，坐标严格不变）而不是 R4**。

---

## 3. 三个"欢迎回答"的问题，直接答

**Q1｜域适应 / 批次校正 / 参考映射里，显式保持或对齐共表达结构的做法有哪些？代价是什么？**

| 做法 | 显式对齐的是什么 | 代价（文献/直接证据层） |
|---|---|---|
| **MNN**（Haghverdi et al. 2018, doi 10.1038/nbt.4091, https://www.biorxiv.org/content/10.1101/165118v1.full-text） | **用基因子集相关的线性修正向量对齐两个域**；搜索片段显示它只对"与细胞类型变量相关的基因"构造修正（类似 Seurat 的 CCV/TopDimFeatures） | ⚠️[推断] 只对基因子集做修正 = 对其余基因的相关结构不做任何保护，**这正是本项目现役方法的失败机制在文献里的对应物**。间接证据：https://www.biorxiv.org/content/10.1101/165118v1.full-text |
| **Seurat anchors / 综合整合**（Hao et al. 2021, PMC6687398, https://pmc.ncbi.nlm.nih.gov/articles/PMC6687398） | **回到原始高维表达空间核验 anchor**（用 CCV 相关基因、L2 归一化空间做最近邻），而不是只在低维嵌入上对齐 | 代价：只有 anchor 被核验，非 anchor 细胞的共表达结构不受保护（[推断]）；且低维整合本身会重排基因-基因关系 |
| **Symphony**（Nat Methods 15:343–346, 2018） | **用保守的基因–基因相关结构定义流形**，再把新样本投到流形上 | 代价：需要"保守基因"可识别（[推断]）；卷页间接印证 |
| **LIGER / iNMF**（Welch et al. 2019, Cell） | **共享因子承载基因程序** → 共表达结构由因子载荷承载 | 代价：**NMF 重构天然截断相关秩**，且输出不是有效计数矩阵（[推断]） |
| **CORAL / Deep CORAL**（arXiv:1612.01939 / 1607.01719） | **直接把协方差当损失**（本方向最直接可迁移物） | 代价：**只能对齐二阶，对联合分布的更高阶无能为力**；且必须外推目标协方差（见 R3） |
| **CellANOVA**（Zhang et al. 2025, Nat Biotechnol, https://pubmed.ncbi.nlm.nih.gov/39592777） | 反向证据：**定量刻画"整合过程会擦掉生物信号"** | 代价提示：任何整合/对齐都要付"信号损失税"，这与本项目 2.49× 的观察方向一致（[推断]） |
| **scDesign3**（Song et al. 2023, PMC11182337） | **copula + 边际同时匹配**，明确以 gene–gene correlation 为设计目标 | 代价：需要足够的参考数据估 copula；是**生成式**的，不保证"预测正确"，只保证"结构像" |

**Q2｜"低秩 + 结构匹配噪声"式生成做法；有吗？proper scoring rule 文献怎么说？**
- **有，而且正是 scDesign3 / GLM-PCA / NNSF / FISHFactor 这一族**（详见 R2 锚点表）。它们的共同结构就是：低秩（或 copula）承载跨基因耦合，逐基因噪声参数承载边际散布。**这是本方向最成熟的组件。**
- **proper scoring rule 侧的关键事实：**
  1. **variogram score 是 proper 但非 strictly proper，且被认为对"预测的协方差结构"比 energy score 更有判别力**——Wikipedia "Scoring rule" 条目明确如此表述（https://en.wikipedia.org/wiki/Scoring_rule），原始出处为 Gneiting & Raftery 2007 *JASA*（https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf）。⚠️ Wikipedia 为二手来源，**但 JASA 原文的题名/期刊/年份已在搜索结果中直接印证**。
  2. **energy score 的弱点**：Ziel 2019（arXiv:1910.07325, https://arxiv.org/pdf/1910.07325）指出 energy score 是最广泛使用的多维 proper scoring rule，且在检测预报失配上表现相当好（间接证据：搜索片段）——即 **energy score 并不是"二阶结构"上更差的那个**。真正的高维弱点来自**估计量**而非规则：距离协方差类统计量在高维有严重偏倚（见 Q3/Q4 的 Székely–Rizzo 结论）。
  3. **CRPS 的多维推广 = energy score**（Gneiting & Raftery 2007；arXiv:2407.00650 综述 https://arxiv.org/html/2407.00650v1 重述了 ES_α 定义）——**没有**一个"显式只关心相关结构"的 proper scoring rule；variogram score 之所以被选中，正是因为它是这一族里最接近协方差敏感的成员（[推断]）。
- **[推断] 实践含义**：不要用 energy score 做你的内部判据（它会奖励"整体距离对"而放过结构错），用 **variogram 一族 + 去偏距离协方差**；并且**内部判据必须与公开评分器同一泛函**（pairwise-difference moment），否则代理与目标不对齐（= R4 的失败模式 c）。

**Q3｜整细胞/整块重采样、donor/cluster 级重采样，是否比逐基因扰动更安全？**
**是，且文献方向一致。** scCoda（Nat Commun 2021）与 Milo（Genome Biol 2021）都把**样本级/邻域级的计数与组成**作为不确定性的承载层，基因层只作条件；LIGER 用**共享因子**代替逐基因独立偏移。⚠️[推断] 逐基因扰动之所以更危险：它**条件独立地**改动每个基因，会在"同一行内"人为制造/破坏相关，而任何行内操作都会直接打到 variogram（你们实测的 4.35× 就是这个机制）。**重采样不创造新的行内组合，因此按构造无法破坏联合结构**——这是 R1 最强的论证。
**但有一个反例必须记下**：如果重采样单位是"单细胞"而源阶段的细胞本身来自**不同个体/不同化学版本**（你们 GSE206325 那次教训），那么块/细胞级的"真实联合结构"里混着技术批次。⚠️[推断] 这时应当把重采样单位提升为 **donor/胚胎级**（整块来自同一次采集），而不是"选质量最好的个体"。

---

## 4. 矛盾与需要注意的地方（Contradictions）

1. **"variogram 对协方差敏感"这一关键论断，我在搜索结果里只拿到了 Wikipedia 这一二手来源**（https://en.wikipedia.org/wiki/Scoring_rule），JASA 原文 PDF 出现在结果中但我无法抓取核对其原句。**建议人工打开 Gneiting & Raftery 2007 PDF 确认原句**再写进报告——这是本简报中唯一"重要且仅二手支撑"的论断。
2. **Ziel 2019（arXiv:1910.07325）显示 energy score 在检测预报失配上"表现相当好"**，这与"energy score 对协方差结构不敏感"这一流行说法**存在张力**。本简报不主张"energy score 测不到协方差"，只主张"**距离类统计量在高维的估计量有偏**"（Székely–Rizzo 2013 / AOS 2021，这条是直接印证的）。
3. **Bures–Wasserstein 是否算"已关闭的 OT 家族"**——这是**规则层面**的分歧，不是证据分歧。R3 的 CORAL 分支可以无争议执行；BW 分支需要一次明确的边界裁决（见 R3 的 ⚠️ 段）。
4. **TIME-CoExpress / scCopula 两篇都是预印本**（2025），不能作为"已验证"证据，只能作为"有人正在做"的方向性证据。

## 5. 缺失的证据（Missing evidence）

- **没有任何文献直接做过这件事**（"在发育阶段插值中保持基因间共表达结构并用 variogram 类评分验证"）。**该组合无直接先例**；组件先例为：scDesign3（copula 保持 gene–gene correlation）、GLM-PCA/NNSF/FISHFactor（低秩 + 逐基因噪声）、CORAL（协方差作为显式损失）、Milo/scCODA（块级/样本级重采样）。
- 我**没有**核实：各锚点论文的具体超参数、噪声水平的量级、其报告的相关系数恢复精度。
- 我**没有**核实：Gneiting & Raftery 2007 中关于 variogram score 判别力的**原句**（见 §4.1）。
- 我**没有**核实：`Σ̂_tgt` 沿发育时间的"测地线外推"在文献中是否已有直接应用（未找到；SPAnish/NeuralNMF/Townes NNSF 都是**空间**因子分解，不是**时间外推**的协方差）。
- 我**没有**核实：24k–59k × 500 的 NB 因子模型在纯 CPU 上的实测耗时（只推断为分钟级）。

## 6. 建议的最小实验序列（供排期，非本次交付）

1. **§1 推断 B 的数值验证**（5 分钟）：只补"条件内残差"能把分数拉回多少？——它决定 R1/R2 是"补残差"就够，还是要动联合结构。
2. **§1 推断 C 的三层诊断阶梯**：逐基因散布 → 基因对相关 → 目标量。逐层看哪一层能解释 2.49×。
3. **R1 留一阶段验证**：用源阶段做伪目标（`w_t` 由伪目标组成估计），测 `variogram` 相对**什么都不改的基线**的比值。这一步是本方向唯一合法的调参入口。
4. **代理目标可迁移性预检**：源阶段内算「代理目标 vs 真实 variogram」的秩相关；<0.5 则 R4 停。
5. **坐标子分护栏**：R1 全程锁 `occupancy_dice` / `d2_shape` 为 0 影响（数学保证 + 实测确认）；R4 才允许非 0。

## 7. 引用清单

**保留（题名/期刊/年份/DOI 均在搜索结果中直接印证）**
- Gneiting & Raftery 2007, *Strictly Proper Scoring Rules, Prediction, and Estimation*, JASA — https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf —— variogram score 的原始出处
- Wikipedia, *Scoring rule* — https://en.wikipedia.org/wiki/Scoring_rule —— **唯一直接说"variogram score 对协方差更有判别力"的来源（二手，需人工核原文）**
- Ziel 2019, *On Sensitive and Strictly Proper Scoring Rules* — https://arxiv.org/pdf/1910.07325 —— energy score 的表现
- arXiv:2407.00650, *Proper Scoring Rules for Multivariate Probabilistic Forecasts based on Aggregation and Transformation* — https://arxiv.org/html/2407.00650v1 —— ES_α 定义重述
- Székely & Rizzo 2013, *The distance correlation t-test of independence in high dimension*, JMVA 117:193–213 — https://pages.stat.wisc.edu/~wahba/stat860/pdf4/Energy/JMVA-t-test-2013.pdf —— 去偏 R*_n
- *Asymptotic Distributions of High-Dimensional Distance Covariances* — http://faculty.marshall.usc.edu/jinchi-lv/publications/AOS-GFLS21.pdf —— 高维距离协方差偏倚
- Sun & Saenko, *Correlation Alignment for Unsupervised Domain Adaptation* (CORAL) — https://ar5iv.labs.arxiv.org/html/1612.01939
- Sun & Saenko, *Deep CORAL* — https://arxiv.org/abs/1607.01719
- *Geometric Dataset Distances via Optimal Transport*, NeurIPS 2020 — https://papers.neurips.cc/paper_files/paper/2020/file/f52a7b2610fb4d3f74b4106fb80b233d-Paper.pdf —— Bures–Wasserstein 闭式
- POT `ot.gaussian` 文档 — https://pythonot.github.io/gen_modules/ot.gaussian.html —— BW 实现
- NeurIPS 2020 poster（unbalanced Gaussian OT / Wasserstein-Bures 用于 UDA）— https://neurips.cc/virtual/2020/public/poster_766e428d1e232bbdd58664b41346196c.html
- Büttner et al. 2021, *scCODA*, Nat Commun 12:6876, doi 10.1038/s41467-021-27150-6 — https://www.nature.com/articles/s41467-021-27150-6
- Dann et al. 2021, *Milo*, Genome Biology — https://pmc.ncbi.nlm.nih.gov/articles/PMC7617075
- Welch et al., LIGER — https://github.com/welch-lab/liger ；iNMF 教程 https://welch-lab.github.io/liger/articles/online_iNMF_tutorial.html ；Welch 2019 Genome Research https://pmc.ncbi.nlm.nih.gov/articles/PMC6716797
- Hao et al. 2021（Seurat 综合整合）— https://pmc.ncbi.nlm.nih.gov/articles/PMC6687398
- Haghverdi et al. 2018（MNN, doi 10.1038/nbt.4091）— https://www.biorxiv.org/content/10.1101/165118v1.full-text
- Song et al. 2023, *scDesign3* — https://pmc.ncbi.nlm.nih.gov/articles/PMC11182337 ；预印本 https://www.biorxiv.org/content/10.1101/2022.09.20.508796.full
- Puritz & Braun 2025, *Copula modeling of gene coexpression in single-cell RNA sequencing data*, bioRxiv — https://www.biorxiv.org/content/10.64898/2025.12.04.692380v1 （**预印本**）
- *TIME-CoExpress*, bioRxiv 2025 — https://www.biorxiv.org/content/10.1101/2025.01.23.634392v1.full.pdf （**预印本**）
- Townes et al. 2023, *Nonnegative spatial factorization applied to spatial genomics*, Nat Methods, doi 10.1038/s41592-022-01687-w — https://experiments.springernature.com/articles/10.1038/s41592-022-01687-w （同时是 Symphony 卷页 15:343–346 (2018) 的引用出处）
- Walter et al. 2023, *FISHFactor* — https://pmc.ncbi.nlm.nih.gov/articles/PMC10176502
- GLM-PCA / fastglmpca vignette — https://cran.r-project.org/web/packages/fastglmpca/vignettes/intro_fastglmpca.html
- Osorio et al. 2022, *scTenifoldKnk*, Nat Commun — https://pmc.ncbi.nlm.nih.gov/articles/PMC9058914
- Grathwohl et al., *Learning the Stein Discrepancy*, AISTATS 2021 — https://proceedings.mlr.press/v119/grathwohl20a/grathwohl20a.pdf
- Jitkrittum et al., *A Linear-Time Kernel Goodness-of-Fit Test* — https://zoltansz.github.io/publications/jitkrittum17linear.pdf
- *A Kernelised Stein Statistic for Assessing Implicit Generative Models*, NeurIPS 2022 — https://openreview.net/forum?id=t4vTbQnhM8
- Zhang et al. 2025, *CellANOVA*, Nat Biotechnol — https://pubmed.ncbi.nlm.nih.gov/39592777

**弃用 / 降权**
- metricgate 的 Szekely-Rizzo 计算器页、Scribd / Emergentmind / ResearchGate / X(Twitter) 摘要页 —— 二手/SEO 聚合，不可作证据
- `sc-best-practices.org`、各 blog、YouTube 讲稿 —— 教学材料，只作背景
- Zhou et al. 2024, *Distance-Preserving Generative Modeling of Spatial Transcriptomics* — https://arxiv.org/pdf/2408.00911 —— **保留但不引用**：题名"distance-preserving"极可能与已关闭的 OT 家族重叠，且我无法核实其是否真处理共表达
- COEXPRESSO / FOCUS / Phoenix 等只在工具聚合页出现的名字 —— 无原始出处，弃用

---

## PROVENANCE_LIMIT（coordinator 2026-09-27 补记）

- 本简报由 `researcher` 子代理产出，该环境**无网页抓取工具**（`fetch_content`/`get_search_content`/`source_check` 未注册，调用即中止运行——本次运行即因此在写完简报后标记为 failed，产物已由 coordinator 从 `subagent-artifacts/outputs/160eb41d.../research.md` 回收）。
- **所有引用仅核实到「题名/期刊/年份/DOI 出现在 web_search 结果」这一层，未抓全文。** 简报内已自行用 `[推断]` 与间接证据标注分层，这一点值得肯定。
- 依 `D-20260927-T2CITE-001`：**未核验的锚点不得在设计文档中承担机制论证**。本简报的 8 组锚点（Gneiting&Raftery 2007、Wahba/Lin 2013、CORAL、Deep CORAL、NNSF、FISHFactor、scDesign3、Milo、scCODA、以及最贴题的沿轨迹 gene-pair 相关预印本）在各 GJC lane 设计冻结前必须由 coordinator 逐条读原文核验。
- 其中 **Gneiting & Raftery 2007** 承载 R3「CORAL 只作用在 K≤30 因子得分上」的可识别性论断，属于**二手引用**，必须核原句。
- 本子代理未读取任何本地数据文件。
