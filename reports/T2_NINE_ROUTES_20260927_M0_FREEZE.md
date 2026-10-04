# T2 九路线 M0 冻结文件（2026-09-27）

- **决策号**：`D-20260927-T2M0FREEZE-001`
- **依据**：用户 2026-09-27 授权「T2 三个 board × (2 新 + 1 迭代) = 9 条 lane」，裁定 5% 为量化阈值
- **性质**：任何训练/建模**之前**写死的口径。后续 M1–M6 不得回改本文件而不追加新决策。
- **状态**：`FROZEN`（口径已定；9 个 lane 槽位待 M1 填入）

---

## 1. 冻结的父版本（磁盘 SHA 已独立复算，与 `submissions/INDEX.tsv` 逐位一致）

| board | 用途 | 版本 / method | 服务器分 | SHA256 |
|---|---|---|---|---|
| `T2:embryo:val_interp` | 迭代父版本（= 当前 selection） | `v0010` `b4_t2_r2_l2_mean_mass_bridge` | **62.29**（board best） | `34caae70aff220b6a754dedea54bd27a5c4d0962305341994dd239f60f14364e` |
| `T2:heart:val_interp` | 迭代父版本（= 当前 selection） | `v0013` `b4_t2_r2_l2_mean_mass_bridge` | **62.04**（board best） | `9080cfc3adbed773ad57a601548e15427b25696461b68d083a45c522b85daf08` |
| `T2:heart:val_extrap` | **迭代父版本**（用户裁定，取现有服务器最高分） | `v0011` `g0_t2_r2_shrink` | **50.64**（已评分最高） | `38edc52e3a9af7cdf87085c0f87d12d630dcfec8d5bb55735b383e62017d44e9` |
| `T2:heart:val_extrap` | 当前 selection（**不改动**） | `v0001` `pseudobulk_shift`（baseline-001） | **50.53** | `f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504` |

**extrap 的 0.11 差异保持 OPEN**：v0011（50.64）服务器分高于 selection baseline（50.53），但服务器确认的 Total 156.06 用的是 50.53 组合。本轮**只把 v0011 当迭代起点，不改 selection**，待重读门户页面澄清。

**已评分 artifact 完整性**：`git status --porcelain submissions/` 输出 **0 行** —— 本轮开始前无任何已评分或候选产物被改动。

## 2. Board 契约（`artifacts/tool_integration/P0-LOCK/locks/BOARD_REGISTRY.yaml`，locked 2026-08-30，scorer `veckit-0.1.1@46d41e6`）

| board | target_label | n_genes | cells 区间 | truth_cells | reference_cells | required_obsm | floor_model |
|---|---|---:|---|---:|---:|---|---|
| `T2:embryo:val_interp` | E7.5 | 498 | 583–5000 | 583 | 1330 | `[spatial_3D]` | `copy_last` |
| `T2:heart:val_interp` | E8.5 | 500 | 1000–17616 | 1185 | 5872 | `[spatial_3D]` | `copy_last` |
| `T2:heart:val_extrap` | E10.5 | 500 | 1000–25179 | 8393 | 5374 | `[spatial_3D]` | `copy_last` |

三块 board 的**官方 target 都是隐藏集**，本地不可能真评。因此：

- **官方 scorer 在本地为 `NOT_RUN_NO_MATCHED_TRUTH`**，不是「跑不通」，是**没有真值**。
- 本地一律用**观测期 stage 充当 pseudo-target**（source-only，证据层级第 4 层），强制披露，不作 leaderboard 预览。
- 沿用既往口径以便与历史轮次可比：embryo 用 `E7.25`／ref `E6.75`；heart_interp 用 `E8.75`／ref `E8.25_late`（与 B4-T2-R2、T2-J1 一致）。extrap 的 pseudo-target 对在 M1 各 lane 设计中显式声明并写进冻结设计。

## 3. 5% 三分类判据（用户裁定，量化版）

### 3.1 主指标（5% 的计算基准）

**`neighborhood_mmd`**（lower-better）。选它的理由有实测支撑，不是拍脑袋：今日 L-001 中，同靶条件下官方锁定 scorer 的 parent 臂 `neighborhood_mmd` = 0.03124 与 J1 进程内镜像的 `nfs_parent` = 0.031240 **逐位吻合**——它是目前唯一被本地验证过能忠实复现官方 scorer 的 T2 指标，且在 veckit 中明确标注为 coupling-free（不依赖行-点配对，故不会重演 FGW 置换类路线的偏差）。

```
degradation% = (candidate - parent) / parent × 100     # neighborhood_mmd，lower-better
```

### 3.2 分布侧会签（记录 + 作为结构性失败判据的输入，不设独立阈值）

`morans_I_agreement`（higher-better）、`variogram`、`mmd_u`、`energy_distance`、`pseudobulk_pearson`。依 T1-D3 事故确立的 doctrine：de/dir 类指标须分布侧会签，本文件沿用。

### 3.3 三分类

| 分类 | 判据 | 后果 |
|---|---|---|
| **严重劣势** | `neighborhood_mmd` 相对父版本退化 **> 5%**，**或**出现任一结构性失败（见 §4） | **关闭淘汰，不占该 board 的 3 个名额**；触发一条替补新路线（走完整 researcher 检索 + 设计冻结流程） |
| **轻微劣势** | 退化 **≤ 5%** 且无任何结构性失败 | **照常交付占名额并可提交**，标注「轻微劣势提交」 |
| **通过** | 优于或持平父版本 | 占名额并可提交 |
| 边界 | 恰在 5% 附近或判据冲突 | **一律按「轻微」从宽处理**——宁可交由用户上传裁决，也不自行抬高或压低门槛 |

### 3.4 重复测量离散度（佐证，非门槛）

`neighborhood_mmd` 含随机成分（`mmd_unbiased(n=2000, seed=0)` + `morans_I` 的 `n_genes=200, seed=0`）。**离散度定义**：同一输入、同一伪目标下，用 3 个不同 `--seed` 重跑 scorer，取 `neighborhood_mmd` 的极差 ÷ 均值作为相对离散度 `disp%`。

- 每条 lane 必须报告 `degradation%` 与 `disp%` 两者。
- **未报告 `disp%` 者不得声明「落在噪声内」**——这一条是硬要求，因为 G1-T2 那轮正是缺了它（见 §6）。
- 成本：每 lane 额外 6 次 scorer 调用（父 3 + 候选 3），单次约 20s，合计约 2 分钟/lane。

## 4. 结构性失败签名（一票否决，独立于 5%）

出现任一条即判「严重劣势」，无论数值多小：

1. 表达出现**负值**或非有限值
2. **方差坍缩**（`variance_ratio` 显著 < 1 且与候选机制不匹配）或**组成坍缩**（`composition_JSD` 异常）
3. **几何漂移**：坐标、父行索引、基因顺序、`obsm` 与父版本不再逐位一致（`coords_exact=false` 或 `coords_row_indexed_exact=false`）
4. **劣于强对照**：不如父版本、类型均值或随机置换中的任一基线
5. **门本身设计无效**（如出现 D5 那类死条件或恒不可过腿）——此时**先修门再判**，不得引用该门的结论

## 5. 设计先于训练（可检查，不靠自觉）

- 每条 lane 的**设计文档必须在该 lane 第一个训练/生成动作之前落盘**，并包含：researcher 检索出处、机制描述、预声明评价指标、pseudo-target 选择、2 臂设计、预期失败模式。
- **可核查方式**：设计文档 mtime 必须早于该 lane run 目录 mtime。M5 验收时逐一比对并把结果写进收口报告。
- 6 条新路线另需 researcher 独立审稿记录（含意见与逐条回应），审稿在设计冻结后、训练前完成。

## 6. 必须随附的反证：本地门在 extrap 上曾「判负而服务器判胜」

`G1-T2-R2-SHRINK`（即现在的 extrap 迭代父版本 v0011）：

| | 本地 | 服务器 |
|---|---|---|
| `de_score` | 0.2466（钉死） | — |
| `neighborhood_mmd` | 0.20506 | — |
| board 总分 | **本地门判定 NOT promoted** | **50.64，+0.11，board 最高** |

**这条证据的含义必须写清楚**：若当时把 5% 规则机械套用，这条**已晋级的最高分路线会被直接淘汰**。所以 5% 只能作为筛选器、不能作为证伪器——这正是 §3.3 把「结构性失败」与「数值退化」分开、§3.4 强制报告离散度、§3.3 边界从宽的三重原因。

同一 board 上还有反向的一条：G1-T2-R3/R4 空间平滑族（k=7/15/30）本地全胜、服务器 50.26–50.32 **全负**（`D-20260916-G0T2-001`）。**extrap 上本地门的两个方向都错过**，唯一可靠的方向是服务器本身。

## 7. 不得重提的已耗尽轴

| 轴 | 关闭依据 | 后果 |
|---|---|---|
| FGW ε 离散化微调 | `D-20260904-B4T2R1-001`（57.3/57.31 TIE）+ 今日 L-002（分散度可控但效应未在两 holdout 同时变强） | 不得作为新路线或迭代方向 |
| heart_extrap 空间平滑族 | `D-20260916-G0T2-001`（本地胜、服务器全负） | 不得作为新路线或迭代方向 |
| extrap 位移幅度族（damp/time/popmix/收缩） | B4-T2-R3 关闭不评分 + G1-T2-R2 诊断「the whole shift-magnitude family is exhausted on extrap」 | 不得作为新路线；**注意 v0011 本身属此族，仅作迭代起点，不再扩参数** |
| embryo 行-点配对（FGW assignment） | 今日 L-001 确证拒绝（`D-20260927-T2LEADS-001`） | embryo 若再做配对，须先修 M 参考构建（LEADS L-006），不得调 ε 或换离散规则 |
| moscot decoder / MIOFlow 动力学 / T2-S3 L2 spateo | 各自 lane FAIL/REJECT 记录 | 不得复活 |

## 8. 预算与槽位记账

- 每 board **3 个计划 lane**（2 新 + 1 迭代）＝ 9 个交付槽位。
- 替补上限：每 board 最多 **1 条**替补（合计 12 条上限）。替补同样须走 researcher 检索 + 设计冻结 + 审稿。
- 替补用尽仍无候选 → **停止并询问用户**（阻塞规则 a）。
- 记法：每个槽位在 §9 表格中占一行，状态流转 `PROPOSED → DESIGN_FROZEN → RUN_DONE → TRIAGED → PACKED`，被淘汰的 lane 保留行并标 `CLOSED_SEVERE`（不删行，保留审计线索）。

## 9. 9 个 lane 槽位（M1 填入）

| # | board | 类型 | 状态 | lane 名 | 父版本 |
|---|---|---|---|---|---|
| 1 | embryo_val_interp | 新 | `PROPOSED` | 待 M1 | v0010 |
| 2 | embryo_val_interp | 迭代 | `PROPOSED` | 待 M1 | v0010 |
| 3 | embryo_val_interp | 新 | `PROPOSED` | 待 M1 | v0010 |
| 4 | heart_val_interp | 新 | `PROPOSED` | 待 M1 | v0013 |
| 5 | heart_val_interp | 迭代 | `PROPOSED` | 待 M1 | v0013 |
| 6 | heart_val_interp | 新 | `PROPOSED` | 待 M1 | v0013 |
| 7 | heart_val_extrap | 新 | `PROPOSED` | 待 M1 | v0011 |
| 8 | heart_val_extrap | 迭代 | `PROPOSED` | 待 M1 | v0011 |
| 9 | heart_val_extrap | 新 | `PROPOSED` | 待 M1 | v0011 |

## 10. M0 未决与后续阻塞

- extrap 的 0.11 聚合差异（§1）仍 OPEN，需用户重读门户页面。
- 本文件的 5% 判据基于**单板单指标**。若 M1 某条 lane 的机制改动使 `neighborhood_mmd` 不再是有效表征（例如几何完全不改而只改表达），仍按本文件执行，但在该 lane 冻结设计中说明主指标选择理由。
- `outputs/t2_pseudo_holdouts/` 当前**未构建**（`ls` 为空）。extrap lane 若需要 `t2_pseudo_holdout.py` 的 proxy，将先构建并记录，属 M1 设计的前置动作，不计入 lane 预算。

## 11. 附录 A：对 §7 两行的证据更新（追加，不回改 §7）

- **依据**：`D-20260927-T2LEADS-003`（L-002 atom B，2026-09-27）。本节按 §0 的冻结规则**只追加、不修改 §7 原文**；§7 的判定与后果**均不变**，仅把两行的**关闭依据**从 atom v1 的表述更新为 atom B 的机制表述。
- **§7「FGW ε 离散化微调」行**：原写「分散度可控但效应未在两 holdout 同时变强」。该表述**正确但不完整**。atom B 的落点诊断测得：两个 ε 臂经预声明离散规则后**只有 46.05%（H1）/ 45.80%（H2）的位置选中同一行**（54% 落点不同），而两臂的 hard objective 仅差 2.4e-03 / 4.6e-03。因此关闭的真实理由不是「ε 不敏感」，而是**冻结 FGW 目标面在 ε 方向接近退化**——两个解很不一样，但目标函数分不出高下。**后果不变且更强**：不仅不得作为新路线或迭代方向，**任何「把同一目标解得更好」的方向（ε / max_iter / tol / 更强求解器）都不应被期待带来 board 增益**。这也是 `B4-T2-R1` 全量 heart 57.3 / 57.31 双 TIE 的机制。
- **§7「embryo 行-点配对」行**：原写「须先修 M 参考构建（LEADS L-006）」。**关闭判定不变**，但补一条前置约束：若新参考构建**仍以同一个 square-loss FGW 为优化目标**，它可能同样分不出高下——「只换参考数据」可能不足以让这条路复活。LEADS L-006 的最小验证已相应加问「新参考是否同时改变了被优化的目标」。这**不影响**本轮 9 条 lane 的任何一条：E-N1 SBL / E-N2 VGM / H-N1 VMS / X-N1 vario-continuation 均**不使用 FGW 目标、不做行-点配对**（E-N1 明示「完全不做细胞对应、不用 OT、不用位移场」），方向上与该约束一致，无需修改。
- **与 §3.1 的一致性确认**：§3.1 选 `neighborhood_mmd` 作主指标的理由（同靶下 parent 臂 0.03124 与 J1 镜像 0.031240 逐位吻合）来自 L-001，**未被本次更新触动**。
- 边界：纯文档口径更新，**未训练、未改任何已评分或候选产物、未改 selection**（`git status --porcelain submissions/` 仍为 0 行）；`blocks_submission: false`。

## 12. 附录 B：主指标与会签规则按板校准（追加，不回改 §3）

- **依据**：`D-20260927-T2VALIDATE-001`（验证 V1，全历史 31 条已评分 T2 候选）。本节按 §0 冻结规则**只追加、不修改 §3 原文**；§3 的默认值仍在，但**从本节起按板覆盖**。
- **触发证据**：`neighborhood_mmd` 与服务器 board 分的 Spearman 为 **embryo +0.833（反向）／heart_interp −0.559（有效）／extrap −0.627（有效）**。embryo 板上按 §3 的 5% 规则判 DEGRADE 最严重的 v0010（本地 +16.4%）**恰是服务器第一名 62.29**，而本地唯一判 IMPROVE 的 v0004 排第 6。
- **另一条不可忽略的证据**：embryo 板存在「本地全零信号、服务器 +3.4 分」的输入对——v0001 与 v0002 表达矩阵字节相同、obs 顺序与组成相同，仅 3D 坐标整体 ×1.305 膨胀，服务器 56.70→60.10，而本地七项指标全部零变化（`d2_distance` 尺度不变）。**embryo 板上我们历史追的 +0.30/+0.20/+0.30 全部落在这条 3.4 分带宽内。**

### B.1 逐板主指标裁决

| board | §3.1 主指标裁决 | 理由 |
|---|---|---|
| `T2:heart:val_interp` | **维持** `neighborhood_mmd`，5% 阈值维持 | Spearman −0.559，有预测力 |
| `T2:heart:val_extrap` | **维持** `neighborhood_mmd`，5% 阈值维持 | Spearman −0.627，三板中最强 |
| `T2:embryo:val_interp` | **5% 三分类停用**。改为**服务器仲裁优先**：本地 `neighborhood_mmd` 在该板**只作记录，不作否决**。允许本地判 IMPROVE/DEGRADE 与服务器同向的情形（本板已实测出现）。 | Spearman +0.833，反向 |

**不得**把 embryo 的 5% 规则「反转」使用——V1 只证明了它反向，未证明反向的它有预测力（n=8，置信区间宽）。**停用是本轮证据能支持的唯一动作。**

### B.2 分布侧会签（覆盖 §3.2）

- `mmd_u`：extrap −0.564、heart_interp −0.615，**跨族可用**；但**族内成对比较反向**（B4-T2-R2 的 L1/L2 对，见 `D-20260927-T2PROBED-001`），且 embryo 上 **+0.000 零信号**。
- **裁决**：会签在 **extrap / heart_interp** 上可用，须与主指标同向；在 **embryo** 上**无效，不得单独用于否决**。任何**族内成对**比较（两条相邻迭代 lane）**不得**单独依赖 `mmd_u`。
- `mmd_u` 种子噪声 9.0%，本身不支持 5% 量级判据（承 §5 噪声标定）。

### B.3 结构性失败签名复核（覆盖 §4 的一部分）

- `d2_shape` 在 embryo（+0.357）与 heart_interp（+0.629）**均为反向**：形状更差 ↔ 服务器更高。最尖锐一例是 heart_interp 板最佳 v0013（62.04），其 `d2_shape` 是 12 条中最差（0.07962），与 +4.79 跃升来自组成重采样一致。
- **裁决**：`d2_shape` **不得**单独作为结构性失败签名。§4 中若含形状恶化判据，从本节起在该两板**失效**；其余签名（表达崩塌、库大小、坐标非法、负值等）不受影响。

### B.4 仍需随附声明

- 上述校准基于 pseudo-target（观测期 stage）上的同目标同 seed 重算，**不预测未来服务器分**；服务器分数取自 registry 既有登记，**本轮未查询服务器**。
- 样本量小（8/12/11），Spearman 置信区间宽。embryo +0.833 是强信号但仅 8 个点。
- 本节**不构成**对任一 board 的机制性主张，只对「本地判据与服务器读数」的经验关系作裁决。
- 边界：零候选、零上传、`submissions/INDEX.tsv` 未改；`blocks_submission: false`。
