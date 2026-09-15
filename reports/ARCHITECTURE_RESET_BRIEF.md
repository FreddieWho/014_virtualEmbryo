# ARCHITECTURE_RESET_BRIEF — Batch 4 closeout 2026-09-15

## 1. 正确 floor 是否复现
否。T1 47.0 / T3 46.8（三探针排除抽样/n_obs；bundle 级差异本地不可见）。

## 2. 当前 best 与 62/62/68 的差距
T1 48.47（差 13.53）/ T2 58.29（差 3.71）/ T3 46.95（差 21.05）；Total 153.7（差 38.3）。

## 3. 有服务器正信号的变换
T2 mean+mass bridge（embryo +2.14、heart +4.79）；T3 genotype zeroing（+0.15 tied）。

## 4. 只在 local proxy 有信号的组件
T2 FGW 全局匹配；T1 mass graft 25%（pseudo 最优，服务器 -0.62）；T1 late-program（未测）。

## 5. 失败归因
- 信息缺失：T1 开放集状态出生、T1 late program 数据、T3 β-catenin 泛化证据、floor bundle 构造。
- decoder：T1 全转录组 decoder（moscot/scDesign3 全灭）、T3 阶段/谱系条件因果生成缺失。
- 离散化：FGW greedy→全局已出清（非瓶颈）。

## 6. 已 sanitized 可直接训练的外部数据
T3-S1A exact E8.75 WT（68,910 行，firewalled）；CollecTRI/OmniPath panel-scoped snapshots；CellOracle mm10 base-GRN。T1-R2 要的 late-program processed 对象仍缺。

## 7. 仍缺 processed object 的数据
T1 late-program（E9.5 前体可连的 late programs，无 E10.5–E13.5、无 mutant）；T2-R3 extrap 校准（candidate 已生成未评分，可直接用）。

## 8. 计算预算
沿用本批实际：单 lane 分钟级–小时级 CPU；无 GPU 需求记录；服务器 8/task/day。

## 9. 下一代架构必须同时解决的能力
- T1：开放集状态出生、外部时序预训练、非自主/分支生成、全转录组 decoder。
- T2：表达—组成—几何—生态位联合生成；插值/外推专家分离；variogram（heart 28）是明确 headroom。
- T3：目标基因条件表征、多扰动预训练、阶段/谱系条件因果生成；validation 修补与 β-catenin 泛化分开立项。

## 10. 不能进入下一阶段的 Batch 4 规则
- 用服务器分数差分反推 target（一直禁止，继续禁止）。
- 把 local proxy 全优写成晋级结论。
- 把 validation success 当 test success（T3 β-catenin 未测，不得声称泛化）。
- scored artifact 覆盖/重命名/静默替换。

## 11. validation 与 hidden test 的分布转移
未知。floor 缺口（T1 -3.0 / T3 -3.2 vs 官方 50）本身就是未解释的分布/构造差异；任何新架构必须先复现或解释 floor，否则分数不可归因（S1 门）。

## 12. 待比较的大型架构家族（只留接口，不指定）
1. T1 开放集状态出生 + 外部多阶段预训练；
2. T1 非自主/分支 flow 或 diffusion；
3. T2 表达—组成—几何—生态位联合生成（含 interp/extrap MoE）；
4. T3 多扰动预训练 gene-conditioned model（含 gene/stage/lineage conditional flow）。
三任务共享 WT developmental representation、任务专属 decoder 仍是开放选项。
