# Batch 1–3 失败审计与 Batch 4 路线处置

本文件定义 Batch 4 的起始立场。精确服务器分数以本地最新 registry 为准。

## 1. T1

| 既有路线 | 证据 | Batch 4 处置 | 允许的解释 |
|---|---|---|---|
| `copy_last` | 项目提交 47.0，官方 floor 定义为 50 | `REPAIR_BASELINE` | 项目构造与官方 floor 不同构，先修复 |
| strict per-celltype pseudobulk shift v0004 | 48.5，当前 best | `KEEP_PARENT` | 低容量表达方向有弱正信号 |
| global fallback + composition extrap | 45.9 | `CLOSE_ROUTE` | 当前组成外推与全局回退组合失败 |
| no composition + global/type shrink | 46.2 | `CLOSE_ROUTE` | 当前 shrinkage 形式失败，不等于所有幅度校准失败 |
| B1-A3 state mass/residual | 47.5/47.7 | `KEEP_DIAGNOSTIC` | 部分 mass 表达有弱信号，未胜 parent |
| moscot + raw state delta + empirical/scDesign3 decoder | 44.9/44.8 | `REJECT_IMPLEMENTATION` | 完整 decoder 失败 |
| moscot state-mass forecast | source-only mass 指标优于 strict parent | `KEEP_COMPONENT` | 可与 strict expression 独立拼接一次 |
| MIOFlow growth/death | 未胜 moscot mass | `CLOSE_BATCH4_ROUTE` | 当前 MIOFlow mass 实现不继续，不否定未来大型动力学架构 |
| late-program birth | Batch 2 规划，未真正端到端施工 | `CONDITIONAL_COMPLETE_GAP` | 只做最小版；数据不就绪快速停止 |

### T1 的 Batch 4 核心问题

```text
strict shift 的方向信号能否通过保守幅度、population mixture 和更好的 mass
在不破坏分布/共变的情况下转成 >50 的候选？
```

不是：

```text
再部署一个 trajectory 工具。
```

## 2. T2

| 既有路线 | 证据 | Batch 4 处置 |
|---|---|---|
| board-specific log-RMS scale | embryo +3.4，heart interp +2.7 | `KEEP_FROZEN` |
| heart pycpd shape field | +0.4 | `KEEP_FROZEN_COMPONENT` |
| embryo pycpd | -0.4 | `REJECT_BOARD_APPLICATION` |
| Spateo lane | 本地全负 / 拓扑灾难 | `CLOSE_ROUTE` |
| B1 hard greedy pairing | 持平或下降 | `CLOSE_IMPLEMENTATION` |
| FGW heart assignment | +0.6，当前 57.3 | `OPTIMIZE_PROMISING` |
| FGW soft→hard greedy | 72–73% 首选冲突 | `REPAIR_DISCRETIZATION` |
| embryo FGW | 未上传 / 本地混合 | `HOLD_NOT_PRIORITY` |
| heart extrap geometry | 无正证据 | `FREEZE_GEOMETRY` |
| interpolation expression bridge | 仅早期 midpoint norm 有 +0.6，未系统完成 | `COMPLETE_GAP` |
| heart extrap expression calibration | 当前主要 parent 近 floor，未系统校准 | `COMPLETE_GAP` |

### T2 的 Batch 4 核心问题

1. 是否能保留 FGW 的软计划信息，而不是被 greedy 双射破坏；
2. 是否能在已验证 geometry parent 上补上表达和状态组成；
3. 是否能先用表达校准撬动 heart extrapolation，而不是继续盲改形状。

## 3. T3

| 既有路线 | 证据 | Batch 4 处置 |
|---|---|---|
| `wt_identity` | 45.3，项目 best；官方 floor=50 | `REPAIR_BASELINE` |
| shift transfer | 45.2 / 43.8 | `CLOSE_ROUTE` |
| WT Spearman residual | 44.7 / 44.0 | `CLOSE_ROUTE` |
| B2 v0006/7 signed prior | 用户已更新服务器分数并宣告失败 | `CLOSE_ROUTE` |
| Batch 2 近似 CellOracle/scTenifold | 实现不等于计划的真实工具，但候选族已失败 | `DO_NOT_REOPEN_IN_BATCH4` |
| Batch 3 real-tool prior chain | 真实工具运行，但出版级 gate 阻止候选 | `ARCHIVE_COMPONENTS_ONLY` |
| target gene / lineage / Gata6 dosage 单独贡献 | 未被独立评分 | `REPAIR_BY_ABLATION` |
| 目标阶段 normal-development direction | 旧路线基本没有使用 | `REPAIR_STAGE_CONDITIONING` |
| T3 geometry | 当前官方排名以扰动响应和分布为主 | `FREEZE_COORDINATES` |

### T3 的旧方法关闭边界

Batch 4 不再：

- 改 v0006/7 top-k；
- 调旧 prior committee 权重；
- 换第三个 GRN 工具；
- 继续追求两个 evidence family unanimity；
- 从 Mab21l2 复制方向；
- 用 WT 相关性猜 KO 符号；
- 把 Batch 3 的研究 gate 重新跑一遍。

Batch 4 只做：

1. 严格 floor parity；
2. 去掉全部下游 residual，单独检验确定的基因型操作；
3. 用公开 WT 时间梯补上 stage conditioning，构造低容量 developmental-axis residual；
4. 若仍不胜 floor，T3 进入大型架构重构，而不是继续手工先验。

## 4. 原子任务地图的制度修正

此前的三层地图：

```text
信息原子 → 生成原子 → 可提交原子
```

保留。

但新增两条硬规则：

1. **信息原子不能以出版级证据 gate 阻断合规候选。**
2. **评分 task 的最小原子不是单个指标，而是一个完整候选族：**
   - 一个 parent；
   - 一个信息假设；
   - 一个端到端 transform；
   - 2–4 个预声明 calibration lanes；
   - protected checks；
   - H5AD；
   - 服务器结果。

## 5. 不得扩大解释的失败

- T1 moscot decoder 失败 ≠ state mass 无用；
- MIOFlow 未胜 moscot mass ≠ 所有 growth-aware dynamics 无用；
- embryo pycpd 失败 ≠ heart pycpd 无用；
- greedy pairing 失败 ≠ NFS / assignment 不可优化；
- v0006/7 失败 ≠ 基因条件 perturbation model 不可能；
- real-tool prior 未生成候选 ≠ real-tool 候选已被服务器否决；
- floor 低于 50 ≠ 官方 floor 弱；更可能是构造不一致。

## 6. Batch 4 结束后不得自动保留的东西

即使本地通过，也不自动带入下一代架构：

- 旧 hard-coded celltype whitelist；
- target-specific 手工 top-k；
- 单次服务器成功但没有 source-only 稳定性的参数；
- 与具体文件行序绑定的 coupling；
- 把 validation Gata4 经验硬编码进 β-catenin test 的规则；
- 为 Batch 4 临时写的 submission packaging 逻辑。

只有标准中间接口、合规数据、验证过的 parent 和可复现实验记录可以复用。
