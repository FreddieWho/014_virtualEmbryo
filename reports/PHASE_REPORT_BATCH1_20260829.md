# Batch 1 综合外部评审报告

报告日期：2026-08-29  
报告状态：`CLOSED_FOR_REVIEW`  
评审对象：Virtual Embryo Challenge Batch 1（B1-A1、B1-A2、B1-A3、B1-A4，以及条件性 B1-C1）

## 0. 阅读说明与结论边界

本报告不使用外部文献、网页或其他正式引用，也不把项目内部报告包装成外部依据。文中的文件路径、candidate ID 和指标名称只是项目内部的证据定位锚点；候选完整路径与 SHA256 仍以 `submissions/INDEX.tsv` 为准，服务器分数与 submission ID 仍以 `reports/SERVER_SCORE_REGISTRY.md` 为准。

本报告的目标是让外部评审能够判断：

1. Batch 1 原计划是否按约束执行；
2. 哪些结果属于真实服务器反馈，哪些只是本地诊断；
3. 没有晋级的路线更可能失败在哪里；
4. 后续路线应继续、重做还是暂缓。

结论保持克制：Batch 1 证明了若干候选可以合规生成并提交，也证明了 B1-A1 在两个 T2 插值 board 上有服务器层面的改进；它没有证明任何生物学机制、因果关系或跨任务泛化规律。

## 1. 执行摘要

### 1.1 总体结果

原计划的四个正式 atom 均已执行完毕，共形成并评分 16 个最终候选：

| Atom | 计划终点 | 实际完成 | 服务器结果概括 | 当前处理 |
|---|---:|---:|---|---|
| B1-A1 | 2 条 lane × 3 个 T2 board | 6 | 两个插值 board 改善；heart extrapolation 低于原 parent | 按 board 保留，作为 Batch 1 的主要正向结果 |
| B1-A2 | 2 条 T3 lane | 2 | 两条均低于 `wt_identity` baseline | 拒绝晋级，保留作失败诊断 |
| B1-A3 | 2 条 T1 lane | 2 | 均高于旧 baseline，但低于已有 T1 best | 不替换当前 best，保留为 scored backup |
| B1-A4 | 2 条 lane × 3 个 T2 board | 6 | heart interpolation 持平，其余 board 下降 | 不晋级，候选不可变保留 |

因此，Batch 1 的候选生成和评分循环已经结束；不存在尚未完成的必做正式候选路线。B1-C1 是条件性组合 atom，不是自动的第五条路线，本轮不满足执行条件，详见第 4 节。

### 1.2 当前竞争选择

当前服务器返回的 aggregate 为 **149.5**，任务分数为 T1 **48.5**、T2 **55.7**、T3 **45.3**。当前选择为：

- T1：`candidate/T1_val/v0004_strict_pseudobulk_shift`，48.5；
- T2：按 board 选择 B1-A1 L1 的 embryo interpolation 与 heart interpolation，保留 baseline 的 heart extrapolation；当前 T2 服务器返回值为 55.7；
- T3：`baseline-001/T3_gata4/v0001` 的 `wt_identity`，45.3。

B1-A2、B1-A3、B1-A4 都没有改变该选择。所有已经评分的候选均保持原路径和原内容，不以新报告替换或覆盖。

### 1.3 最重要的判断

1. **格式和提交链路不是 Batch 1 的主要失败点。** 16 个正式候选均有 contract/invariant 通过记录，索引中的 canonical 文件 SHA256 在本次收尾检查中全部匹配；所有候选均记录为 `target_used=false`。
2. **B1-A1 是混合结果，不是普适成功。** 统一空间尺度在两个插值 board 上有效，在 heart extrapolation 上无效且低于 parent；这更像 board/时间区间依赖的信号，而不是已验证的通用尺度规律。
3. **B1-A2 的失败线索最集中。** 两条路线共享 WT-only 弱方向先验和借用的 Mab21l2 绝对效应预算；两条均低于 baseline，且 target-matched self-check 的方向指标已经偏弱。现有证据支持“响应先验/幅度转移不可靠”这一工作假设，但不能把方向、幅度和状态 gate 的贡献单独分离出来。
4. **B1-A3 不是简单的全盘失败。** 两条路线相对最初 T1 baseline 有小幅提升，但相对更强的既有 v0004 仍下降；同时锁定的 full-panel local scorer 未完成，因此无法仅凭本批结果判定是状态划分、质量外推还是 residual replay 导致差距。
5. **B1-A4 更像目标函数未对齐或作用太弱，而非文件损坏。** 它只重排表达行，坐标、表达边缘和 15-NN 结构通过保护检查；服务器只给出持平或下降。现有证据不能推出“表达—坐标配对没有作用”，只能否定本次固定配对目标和一次性贪心实现的晋级资格。

## 2. 原始方案与执行范围

### 2.1 原始施工规则

原方案在 `docs/batch1/config/batch1_manifest.yaml` 和 `docs/batch1/00_START_HERE.md` 中规定：

- 一次只施工一个 atom；
- 每个双 lane atom 的终点是预先固定的 1+1 条最终路线；
- B1-A1、B1-A4 各覆盖三个 T2 board，因此各产生 6 个最终文件；
- 允许有限的 source-only 临时探索，但不能晋升为第三条最终 lane；
- 禁止读取 hidden target、排行榜反馈或目标阶段测量值来调参；
- 自动提交关闭，候选必须通过人工上传和服务器评分；
- 本地 pseudo-score 只作路线诊断，不能替代服务器分数；
- 已评分 artifact 不得覆盖、重命名或静默替换。

### 2.2 四个正式 atom 的技术路线

#### B1-A1：G1 组织尺度

目标是只改变 T2 点云相对质心的统一 RMS 尺度，不改变表达矩阵、点间相对结构、表达—坐标配对或 15-NN 图。

- L1：按相邻观测阶段的 `log(RMS)` 做插值，超出末端时使用末段斜率外推；
- L2：对组织的全部观测阶段做等权 `log(RMS)` OLS；
- 两条 lane 都只应用正的 uniform scaling；
- 三个 board 分别生成，不混用 embryo 与 heart 尺度曲线。

#### B1-A2：C1 signed response

目标是对 Gata4 KO 产生稀疏、有符号的表达 residual，主要改善 DES/DCS，同时保护 WT 背景。

- L1：细胞层面的 Spearman signed rank；
- L2：状态 pseudobulk 层面的 Spearman signed rank；
- 实际可用的响应先验为 WT-only 相关 fallback，登记为 `prior_strength=weak`；
- 非零数量和基础幅度借用了 Mab21l2 训练 KO 的解析统计，但没有把 Mab21l2 的方向直接复制到 Gata4；
- 状态 gate、非负截断、目标基因置零和非响应基因保护均按契约执行。

#### B1-A3：P2 状态质量与 C7 residual consistency

目标是在不训练新动力学模型、不开创新状态的情况下调整 T1 预测的状态质量，并用完整 residual bank 保持状态内异质性。

- L1：同名状态保留，阶段特异标签归入 `UNRESOLVED_STAGE_SPECIFIC`；
- L2：以 E9.5 词表和全 panel expression centroid 对 E8.5 做 source-only projection；
- 使用固定的状态比例 growth、固定收缩和 5%—95% 截断规则；
- 从不可变 T1 baseline 做完整行 replay，保持 5,118 个细胞和全表达向量；
- 不重新聚类、不做人工 label crosswalk、不读取目标数据。

#### B1-A4：J1 expression-coordinate pairing

目标是固定表达行集合和坐标，只改变表达行放置到坐标节点的排列，以改善局部邻域表达；不得改表达数值、坐标、细胞数或 gene order。

- L1：`LATENT_KNN10`，固定 30 维 randomized PCA 和 latent 近邻候选；
- L2：`STATE_HASH10`，在相同父本 celltype 内按固定 hash 顺序提出候选；
- 两条 lane 共享固定 seed、Ridge `alpha=1.0`、一轮 greedy swap 和最多 `10*N` proposals；
- 所有表达行对齐对象同步重排，坐标和 15-NN 结构保持不变。

#### B1-C1：G1 + J1 组合

该路线只允许机械地把已冻结的 A1 scale 和 A4 permutation 组合起来，不允许重新拟合或调参。契约明确规定：如果 A4 的 immediate parent 已经携带选定的 A1 scale，或本身就是 identity-scale baseline，则该 board 记为 `NOT_NEEDED_PRECOMPOSED`，不得重复生成。

本轮 A4 的 embryo/heart interpolation immediate parent 已经是 A1 scale，heart extrapolation 使用 identity-scale baseline。因此 B1-C1 没有独立未完成的组合工作；再次执行只会重复已有状态。

## 3. 过程审计

### 3.1 已确认的执行事实

| 审计项 | 结果 | 说明 |
|---|---|---|
| Atom 范围 | PASS | 四个正式 atom 均有独立结果目录和 tracking 事件 |
| 最终候选数量 | PASS | 6 + 2 + 2 + 6 = 16 |
| 双 lane 规则 | PASS | 每个要求双 lane 的 atom 均保留两条最终路线 |
| hidden target 隔离 | PASS（按记录） | 四个 atom 的 manifest/result 均记录 `target_used=false` |
| contract/invariant | PASS | A1 6/6、A2 2/2、A3 2/2、A4 6/6 |
| canonical SHA256 | PASS | `submissions/INDEX.tsv` 的 16 个 B1 路径本次逐一重算，16/16 匹配 |
| A1 本地 public proxy | PASS | 6/6 完成；仅作诊断 |
| A2 self-check | COMPLETE_WITH_WARNING | 两条均完成；方向指标偏弱，不能视为服务器预测 |
| A3 本地 full-panel scorer | INCOMPLETE | L1 超时，L2 进程异常消失后中断；没有缩减或替代 scorer |
| A4 本地 public proxy | PASS | 6/6 完成；仅作诊断 |
| 服务器评分 | PASS | 16/16 有服务器分数登记 |
| 自动提交 | PASS | 未启用；走人工上传和用户回填分数流程 |
| 评分后不可变性 | PASS | 已评分候选保留原 canonical 路径和内容 |

### 3.2 过程中的限制与收尾修正

1. A3 的 local scorer 不完整是明确的验证缺口。没有用简化 scorer、替代指标或猜测结果填补，因此 A3 的服务器结果可以用于榜单决策，但不能被包装成“本地验证充分”。
2. 部分服务器记录没有用户提供的 submission ID。A4 的六条成绩按上传包内显式的 batch/task/board/lane/version 文件名映射，未根据不可靠的 portal Model 字段猜测 ID，也未伪造 ID。
3. 服务器返回的 T2 和 Total 是当前榜单的权威值；显示的 board 分数独立四舍五入，不能用手工相加替代服务器 aggregate。
4. 仓库尚无 initial Git commit。当前文件、候选和报告仍可按路径与 SHA256追溯，但缺少一个统一的提交锚点，降低了完整环境复现的便利性。
5. 收尾时发现并修正了 B1-A2 的两个状态过期项：其 `RESULT.md` 与 `FINAL_SET_MANIFEST.json` 已从 `score_pending` 对齐为已评分完成；这只改变记录，不改变候选文件。

## 4. 结果与证据解读

### 4.1 B1-A1：局部成功，外推失败

服务器结果显示，L1 在 embryo interpolation 和 heart interpolation 上分别超过其 parent；在 heart extrapolation 上低于原来的 50.5 baseline。L2 在三个 board 上都低于同 board 的 L1。当前保留的是 L1 的两个插值结果与 baseline 的 heart extrapolation，而不是无条件采用六个 A1 输出。

支持的判断：

- `log(RMS)` 尺度校准在两个插值 board 上具有可用的竞争信号；
- L1 在本次三 board 比较中优于 L2；
- heart extrapolation 的末段斜率对结果敏感，不能从插值结果外推成功推断到外推 board。

不能支持的判断：

- 不能说 uniform scaling 是真实发育尺度规律；
- 不能说 L1 公式在其他组织、阶段或 hidden board 上普遍更好；
- 不能用一次服务器评分区分真实信号与该 board 的具体评分特性。

### 4.2 B1-A2：最明确的算法级失败线索

两条候选都通过格式和保护检查，但服务器分数均低于 45.3 的 `wt_identity` baseline：L1 低 0.6，L2 低 1.3。两条 lane 的公开 Mab21l2 self-check 也有一致的风险信号：

- L1 的 self-check `de_score=-0.0143`、`de_direction=-0.112`；
- L2 的 self-check `de_score=-0.0286`、`de_direction=-0.058`；
- 两条路线共享 WT-only 弱 fallback，且其 target-matched public proxy 的 DES/DCS、部分分布指标和 variogram 方向均不理想；
- L2 使用了更大的状态 pseudobulk residual，并出现更多 clipping，未能带来补偿。

最保守的失败解释是：本路线把“WT 中的相关符号”转成“Gata4 KO 的 signed response”，再借用 Mab21l2 的幅度预算；这两个转移假设都缺乏足够的 Gata4-specific 支撑。因为两条 lane 共享这两个核心假设，结果支持共同算法假设不可靠，但不能单独估计方向先验、幅度预算、状态 gate 三者各自的损失。

这里没有证据表明失败来自 H5AD 封装、gene order、目标基因置零或人工上传映射；这些环节的硬性检查均通过。也没有证据支持更强的 Gata4 生物学结论。

### 4.3 B1-A3：相对旧 baseline 有信号，但没有超过当前 best

B1-A3 L1/L2 的服务器结果分别为 47.5 和 47.7。两者相对最初的 T1 baseline 47.0 有小幅改善，但相对先前已经存在的 v0004 best 48.5 分别低 1.0 和 0.8。L2 是 B1-A3 内部 winner，但不是 T1 全局 winner。

支持的判断：

- 状态质量/residual 路线没有在服务器上造成全面崩溃；
- E9.5 expression probe 在本 atom 内优于 shared-unresolved lane；
- 该路线没有足够证据替换 v0004。

主要不确定性：

- E8.5 与 E9.5 label vocabulary 未 harmonise；
- L2 的 expression projection 是 source-only 假设，不是已验证的状态同一性；
- 两个正式候选都从旧 baseline 生成，而非从当前 48.5 best 生成，父版本差异会影响直接比较；
- locked full-panel local scorer 未完成，不能用本地结果拆分 partition、mass forecast 和 residual bank 的贡献。

因此 B1-A3 更适合被描述为“有弱正向服务器信号但未晋级，验证不完整”，而不是“状态质量方法已被证伪”。

### 4.4 B1-A4：结构保持成功，但 server NFS 没有改善

B1-A4 的六个候选都完成了 permutation 双射、表达层同步重排、坐标 hash、15-NN hash、panel/order 和数值检查。服务器结果中，embryo interpolation 两条均低于 B1-A1 L1，heart interpolation 两条与当前分数持平，heart extrapolation 两条低于 baseline。

这排除了几类简单实现错误：

- 不是坐标被意外改写；
- 不是表达矩阵边缘被整体改变；
- 不是 gene order 或 cell order 的明显破坏；
- 不是候选文件和上传包之间的 SHA256 不一致。

仍然存在的主要解释是：固定的 latent-neighborhood Ridge 目标、候选集限制和单轮 greedy swap 与服务器 NFS 的有效目标不一致，或者在当前 parent 上可利用的配对信号太弱。由于没有重复 seed、独立 NFS 评估或多个公开场景，不能在这两个解释之间做强区分。

### 4.5 任务级失败/成功归因矩阵

| 问题 | 现有证据能支持什么 | 现有证据不能支持什么 | 判断强度 |
|---|---|---|---|
| T2 插值尺度 | B1-A1 在两个插值 board 改善 | 通用尺度规律、因果机制 | 中等 |
| T2 heart extrapolation | A1 两条 lane 均低于 parent | extrapolation 永远无效 | 中等 |
| T3 signed response | WT-only signed prior 路线不可靠的线索 | 精确失败组件或 Gata4 生物学方向 | 较强的工程假设，非机制结论 |
| T1 mass residual | 相对旧 baseline 有弱增益，未超过 current best | partition 或 residual bank 的单独贡献 | 中等偏弱 |
| T2 pairing | 本次 pairing 方案不值得晋级，结构不变量通过 | expression-coordinate pairing 一般无效 | 中等偏弱 |
| 提交链路 | 候选可合规生成、映射和评分 | 合规本身会带来分数提升 | 较强 |

## 5. 外部评审应采用的证据层级

为避免把诊断值和服务器结果混在一起，建议按以下顺序审查：

1. `reports/SERVER_SCORE_REGISTRY.md`：逐候选服务器分数、差值、映射和决定；
2. `submissions/INDEX.tsv`：逐候选 canonical path、SHA256、contract 状态和版本；
3. `artifacts/atomic_batch1/B1-A1/` 至 `B1-A4/`：最终集、manifest、protected checks、local proxy 和运行状态；
4. `docs/batch1/prompts/`：每个 atom 的预先固定目标、禁止事项和验收条件；
5. `docs/coordination/T1_TRACKING.md`、`T2_TRACKING.md`、`T3_TRACKING.md`：路线决策和失败解释；
6. `scripts/` 与 `tests/`：实现和开发期检查入口。

本次报告不新增截图、网页链接或独立 raw-evidence 环节。服务器结果以用户回填和现有登记为边界；没有提供的 submission ID 不作猜测。

## 6. 下一阶段方案评估

### 6.1 立即动作：冻结，而不是继续消耗 Batch 1

建议维持以下冻结规则：

- 不再重复 B1-A1 的 scale 拟合；
- 不启动 B1-C1 重复缩放或重复组合；
- 不在 B1-A2 上重新跑同一个 WT-only Spearman fallback；
- 不把 B1-A3 的内部 winner 直接替换为 T1 current best；
- 不因 A4 的心脏插值 tie 而称其为改进；
- 不基于本报告自动激活新 atom。

### 6.2 若授权下一批，建议优先级

#### 优先级 1：T3 响应路线重设计

T3 是当前最清楚暴露出“候选算法低于 identity floor”的任务。下一条路线不应只是 Spearman 实现的小改版，而应先解决两个共同假设：

1. 可审计的 Gata4-specific signed response prior；
2. 不依赖另一个 KO 基因的绝对效应预算，或至少使用预先固定、强收缩的幅度规则。

如果没有可靠的新先验，identity baseline 应继续作为主基准，而不是强行生成新的 signed residual。若未来引入外部生信数据，必须先完成来源审计和 `infra/bioinf-data-index/` 更新；这不属于当前 Batch 1 的隐含许可。

建议的进入 gate：source-only self-check 中 DES/DCS 不再同时低于 WT floor；contract/invariant 通过；两条 lane 的差异在生成前固定；不得以服务器分数反调符号、top-k 或幅度。

#### 优先级 2：T1 验证链路和状态划分

在再次做 T1 候选前，先解决 full-panel local scorer 的运行问题，并对 E8.5/E9.5 state assignment 的稳定性作独立检查。若无法完成这一步，应把新 T1 route 标记为验证不足，而不是继续依赖单次服务器结果。新候选的 parent、状态划分和 residual 规则必须在生成前固定，不能沿用模糊的 label 对应关系。

#### 优先级 3：T2 暂缓通用 pairing，必要时做 board-specific 路线

当前 T2 已有 55.7 的服务器返回值和两个插值 board 的 A1 改善。若继续，应先证明新的 local objective 与 server NFS 有可重复的公开关联，并优先考虑 board-specific 的时间/空间问题；不建议再次做没有独立判别力的通用 permutation 或机械组合。

### 6.3 新 atom 的统一准入标准

每个下一 atom 仍应遵循：

1. 明确唯一主要指标、parent、两个最终 lane 和停止条件；
2. 先做一次小型功能检查，再做一次正式候选生成；
3. 两条最终 lane 都通过 contract/invariant 后再人工评分；
4. 服务器分数高于当前 board best 才考虑晋级，tie 只记录为 tie；
5. 不用手工 composite、不用显示分数反推 Total、不用 local proxy 冒充服务器结果；
6. 保留所有负结果和不可变 artifact；
7. 新授权以前不执行任何新计算。

## 7. 结论分级

### 已充分支持

- Batch 1 四个正式 atom 已完成其规定的最终候选生成和服务器评分；
- 共 16 个正式候选 artifact，canonical SHA256 与索引一致；
- 所有正式候选均通过记录中的硬性 contract/invariant；
- 当前 aggregate 和 per-task selection 仍为 149.5 / 48.5 / 55.7 / 45.3；
- B1-A2、B1-A3、B1-A4 不应替换当前 best；
- B1-C1 在本轮不需要生成。

### 暂时支持

- G1 uniform scale 对两个 T2 interpolation board 有竞争价值；
- B1-A2 的共同 WT-only signed prior/幅度转移是最值得优先修正的失败假设；
- B1-A4 的固定 pairing objective 与 server NFS 未显示出足够一致性；
- B1-A3 可能有弱正向信号，但当前证据不足以判断其方法组件贡献。

### 不应从 Batch 1 推出

- 任何 biological superiority、causal mechanism 或 perturbation truth；
- 任何方法在 hidden test、其他阶段、其他组织或其他 KO 上的普遍有效性；
- local pseudo-score 与 server score 的稳定映射；
- 单次服务器分数足以证明科学模型晋级。

## 8. 收尾状态与交付面

Batch 1 已设为 `CLOSED_FOR_REVIEW`，当前无 active atom；任何新计算需要新的明确授权。收尾交付包括：

- 本报告：`reports/PHASE_REPORT_BATCH1_20260829.md`；
- 收尾变更日志：`reports/RELEASE_CHANGELOG_20260829.md`；
- 当前状态：`STATUS.md`、`docs/coordination/STATUS.md`；
- 服务器登记：`reports/SERVER_SCORE_REGISTRY.md`；
- 候选登记：`submissions/INDEX.tsv`；
- 四个 atom 的不可变结果目录：`artifacts/atomic_batch1/B1-A1/` 至 `B1-A4/`；
- A4 人工上传包：`deliveries/B1-A4__T2__manual_upload__20260829.zip`。

最终建议：把 Batch 1 作为一次“提交链路已验证、A1 局部有效、A2 明确失败、A3 证据不完整、A4 未晋级”的竞争实验冻结。下一阶段应围绕可区分的失败假设重新设计，而不是把未晋级路线继续微调成更复杂的组合。
