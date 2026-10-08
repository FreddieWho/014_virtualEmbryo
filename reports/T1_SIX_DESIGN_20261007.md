# T1 六路线设计冻结（2026-10-07）

用户经 /goal 授权：在 T1 设计并实现 **6 条新路线——3 条既有路线的优化/结合 + 3 条全新路线**，全部全量执行、完整 32285 基因官方本地 scorer、独立重放与 contract 检查；候选登记 INDEX（score_pending）并打一份 zip；不晋级现役（v0051=53.92 保持）、不代用户提交。用户两项确认取舍：(1) 混合只作载体、必须携带新组件，不重复 v0049–v0056 已试配比；(2) 全新路线以本轮文献检索优先，旧草案可作候补（注：调研后发现 2026-09-21 T1-NEXT R1–R5 实际均已执行并关闭，候补选项蒸发，3 条全新路线全部来自本轮检索新机制）。本设计属行为变更：完整实现、全量执行、针对性验证，不上传。

## 1. 当前事实（以 SERVER_SCORE_REGISTRY 与 ATOM_MAP 2026-10-05 为准）

- T1 val 现役：**v0051 `mix36x38a` = 53.92**（v0036×v0038 50/50 混合，+0.37 PROMOTED）；v0054=53.98 数值最高但在 ±0.1 TIE 带内不换人。混合族 v0049–v0056 饱和于 53.32–53.98。
- 最强单模型：**v0038 `n2covot` = 53.55**（协方差输运整行投影），是现役混合的关键成分；v0043 `s2mix`=53.55 精确同分备份。
- v0035=53.43 / v0036=53.36 为骨架参照（r2joint/r3mix，t1_three 冻结模型逐值复现）。
- 服务器子项结构（v0051）：de 47.2（最弱）/ dir 60.0（最强）/ mmd 56.7 / vario 50.6；历史规律：donor 重选抬分布项（mmd/vario），de 几乎不动，de↔variogram 互换封顶总分。

**已关闭轴（新路线必须避开，且不得重调参）：**
- 混合族旧配比（v0049–v0056 固定配比扫描）；扩散 D5/D5b/D5c；外部预训练 T1-EXTPRE；moscot decoder T1-S2；增长/死亡动力学（HX-KILLTEST）；均值平移 PBMEAN 四臂；patience 轴（D2-R3）；保守族（v0011–v0014）；CFM 场（D3 OTCFM v0022=45.3 REJECT）；**T1-NEXT R2 残差 decoder（09-21 诊断关闭）**；**R3 有界线性步（09-27 关闭：弱环是两点线性步本身）**；**R4 模块运输（09-27 关闭：模块限制救不了 OT）**；**R5 边际固定秩重分配（09-27 关闭：破坏细胞内聚，学习方向差于置乱）**；R6 数据源审查（BLOCKED_DATA_NOT_READY）；R1 尺度扫描（0.5x/1.5x 全败，1x 为 de 峰）；图平滑 n3graph（五项全劣）；矩约束 n1moment（1/0/4）；组成加力 s1growth（DE 变差）；逐值手术。

**温和存活**：f2stable（2/1/2 最均衡，Energy/Variogram 微优）；f1soft（方向微优 0.5859 vs 0.5852）；n2covot（MMD 微优）。

## 2. 文献检索记录（2026-10-07，tavily 后端）

| 锚点 | 来源 | 用途 |
|---|---|---|
| Wasserstein Flow Matching（WFM） | ICML 2025 poster 45541 | nwasser：分布族上的 Wasserstein 几何输运 |
| Latent Gaussian 时序建模 | ICML 2026 poster 65964 | 调研；判定与 n2covot 过近，不采用 |
| scNODE（生成式时序） | PMC 2024, PMC11373355 | 调研；「潜空间学动力学再解码」家族已死（D3/v0022、R2），不采用 |
| scTimeBench | Bioinformatics 2026, btag414 | 时序预测基准的任务分解（forecast accuracy） |
| STORIES | Nature Methods 2026, s41592-025-02855-4 | OT fate landscape 谱系（空间版，机制参考） |
| Conformal inference for scRNA-seq annotation | PMC 2025, PMC12506889 | nconf：分布无关校准 |
| TISSUE / Angelopoulos & Bates / Lei et al. | Nat Methods 2024 / 2021 / JASA 2018 | split-conformal 回归校准的形式化 |
| CellRank / CellRank 2 | Lange et al. Nat Methods 2022；Weiler et al. 2024 | nbidir：前向/后向转移的双向命运映射 |
| CellFlow / scDFM / STATE / MultiFlow | Klein 2025 / ICLR 2026 / 2025 / 2026 | 调研；均属流匹配/直接映射家族，避开 |

## 3. 六条路线

共享骨架（同 t1_seven prepare 模式）：冻结 t1_three r2joint/r3mix 模型逐值复现 v0035/v0036（report/future 双 scope 审计）；公共 mass 库（per type per gene 的 psource/pout/qsource/qout 分位函数）、密度分类器权重、组合分配、SVD-32 潜空间全部由冻结模型产生并 SHA 锁定。所有路线在 10 个 common 类型内操作；输出行名是 synthetic slots；官方 T1 评分不读取写入的 celltype 标签。

### 优化/结合（3 条）

**O1 `ocovstab`——n2covot 优化：投影距离可靠性自适应强度 + k 近邻软化。**
n2covot 用 k=1 硬最近邻、全类型统一 cov_strength=0.5。升级：(a) 每类型可靠性由冻结的 t1_seven n2covot 投影距离决定，**per scope**（report scope 用 REPORT_OPERATOR.json 10 类型、中位 0.9491；final scope 用 FINAL_OPERATOR.json 11 类型含 NCC、中位 0.9498；≤中位保持 0.5，否则收缩 0.125）——修订（2026-10-07 运行前）：首次批次暴露 NCC 无 report-scope 距离（report 划分无 NCC train 细胞），改 per-scope 来源，不需要新扫描；(b) k=8 近邻逆距离加权 systematic 抽样替代 k=1 硬选择（类型不足 k 个时回退 k=1）。首比较臂：O1 vs n2covot（同一骨架、同一潜空间 32 维）。

**O2 `osoftcov`——f1soft 软责任 × n2covot 协方差输运结合。**
f1soft 的软责任联合权重（logw = 0.5·log(密度分类器权重) + 0.5·(GMM soft responsibility @ composition step)，冻结公式）作为 joint_donors 的权重，再做 covot k=1 重选（cov_strength=0.5 冻结）。两个既有机制首次组合：软责任给 donor 权重，协方差输运给 donor 重选。首比较臂：O2 vs f1soft（权重路径）与 n2covot（重选路径）。

**O3 `ostabmix`——f2stable 稳定性 × s2mix 混合载体结合：per-type 自适应混合比例。**
s2mix 用全局固定 70/30（v0049–v0056 用固定 50/50、30/70）。升级：每类型 best/backup 混合比例由 f2stable 的 4-part 稳定性证据决定（类型内阳性均值方向稳定基因占比 ≥0.5 → 0.7；否则 0.3；两级规则冻结，不扫配比）。混合只作载体、携带新组件（per-type 自适应比例），满足用户裁决。修订（2026-10-07 运行前）：无冻结比例的类型（阶段特有类型，如 EXEM，不在 common 集内）保留原骨架（side 0，identity row）——首次批次暴露此缺口，已修。首比较臂：O3 vs s2mix（70/30）与 v0051 配比结构。

### 全新（3 条，本轮检索新机制）

**N1 `nwasser`——Wasserstein 测地位移场（WFM系，非参数计划输运）。**
每 common type：早/晚 train 潜空间（32 维标准化）上的**精确离散 OT 计划**（POT ot.emd 0.9.7.post1，双侧均匀质量）。修订（2026-10-07 运行前）：原冻结 numpy Sinkhorn（ε=0.05）在原始平方距离尺度上发散（exp 溢出）且 LSE 每迭代 ~0.17s 太慢；环境修复（见 §4）后 POT 恢复可用，改用精确 LP——严格更优（无 ε 依赖、无收敛问题），验证：最大 common 类型 2405×871 边缘残差 ≤1e-16、~0.9s。早侧位移 d_i = 行质心投影 − z_i，晚侧 d_j = z_j − 列质心投影。查询：k=8 近邻距离加权位移均值 → target = q + d̄ → 类型池内最近 query cell 为 donor（实现注记：距离加权均值需显式 [:,:,None] 广播，首次批次已修）。与已试路线差异：非参数局部位移场（vs n2covot 全局高斯参数映射）；无神经场、无生成训练（vs D3）；非模块限制（vs R4）。

**N2 `nconf`——split-conformal donor 半径校准（分布无关推断，T1 未试过）。**
每类型：E8.5→E9.5 train 内 50/50 split（fit/校准，seed 20260921）；covot 高斯映射只在 fit 半拟合；校准半上 nonconformity 得分 = 映射 target 到最近晚侧 train 潜形的距离；R = 分位数(⌈(n_cal+1)(1−α)⌉/n_cal)，α=0.1，有限样本 split-conformal。查询：donor 候选 = 映射 target 半径 R 内的 query cells（类型池），逆距离加权 systematic 抽样；无候选时回退 k=1 最近。与已试路线差异：统计校准机制（置信半径过滤）首次进入 T1 donor 选择；不是 kNN/OT/矩约束的参数变体。

**N3 `nbidir`——前向/后向计划一致性权重（CellRank 双向谱系）。**
每类型：同一精确 OT 计划 γ（与 N1 同一计划，见 plan_solver 修订）的行/列双向读取：早侧细胞 i 的一致性 d = ‖主导 plan target 的列质心反向源 − z_i‖；晚侧对称。计划按 scope 缓存于 `shared/<scope>/plans.pkl`（首次批次暴露路径 bug，已修）。查询细胞权重 = 一致性 logw = −d²/(2σ²)，σ = 该类型 train 一致性距离中位（冻结规则）；替换密度分类器权重（n1moment/n3graph 先例），bounded_weights cap 2.0，joint_donors 重选 donor。与已试路线差异：双向一致性作为 donor 权重信号（vs 分类器密度权重、矩匹配、图平滑）；与 N1 的机制差异：N1 用计划做 donor 放置（位移场），N3 用计划做权重（一致性）——同族不同机制，如实披露。

## 4. 执行、限制、停止规则

- **环境修复（2026-10-07，运行前）**：自 09-30 后用户级 numpy 升至 2.4.6，与 anaconda 的 h5py 3.11/xarray 旧版 ABI 冲突（anndata 与 scorer 导入链全断）。修复：用户级安装 h5py 3.16.0 + xarray 2026.9.0；修复后 anndata 0.12.19 + veckit scorer 导入验证通过。冻结父模型拟合于 numpy 1.26.4/sklearn 1.5.1（2026-09 时期）；跨版本 SVD 潜形漂移 3.4e-05（相对 5.3e-07），验证未翻转 donor（0/3357）与 mass（0.0 diff），v0035 字节级复现成立；final-scope 同样以 array_equal 断言验证。scorer 参照：v0035/v0036/v0038 report 预测在本环境下重评作为同环境参照（另存冻结旧环境 SCORER.json 作语境）。
- 独占目录：`scripts/t1_six/`、`configs/t1_six/`、`tests/t1_six/`、`artifacts/t1_six/T1-SIX-20261007-v1/`、`reports/t1_six_20261007/`；共享登记串行（t1_three/t1_seven 冻结产物只读）。
- report 沿既有 60/20/20（3357 recipient/3411 target）；final 全部 16787/17057 细胞，预测 5118×32285。六次完整 panel 官方 scorer 必须执行，不以 smoke、小 panel 或廉价指标替代。旧 report 反复探索过，不算独立胚胎或 E10.5 验证。
- 参数事前冻结于 `configs/t1_six/design_20261007.json`；不根据本轮结果调参。优化器/线性求解必须收敛（GMM/Sinkhorn 收敛检查，no-op 失败保留完整研究输出和真实状态，不降门救结果）。
- 候选通过 contract 后才入 INDEX，score_pending，禁止冒称服务器改进。工程有效路线进一份 zip（standing rule 2026-09-11），失败路线不进包；实现六条不等于保证六条科学成功。
- 科学限制：相邻两个时间点不能唯一识别未来动力学；report 划分反复使用，细胞级分割不是独立胚胎验证；E10.5/E12.5 真值 NOT_RUN_NO_TRUTH；服务器评分 NOT_RUN。本地五项（DE/方向/Energy/MMD/Variogram）只作提交优先信号，不晋级现役、不承诺提分。blocks_submission: false。无新外部生信数据下载，无需新增数据索引条目。
- 停止规则：任一路线优化器不收敛、工程门失败、或退化为原骨架 NO_OP（逐值相同）→ 保留完整研究输出，路线冻结不救结果。N1/N3 的 Sinkhorn 若大面积不收敛（>2 个类型）→ 冻结该路线并报告。
