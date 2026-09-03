# HX-DYNAMICS-KILLTEST · 高风险动力学单假设测试

## 默认状态

`FROZEN`。只有结构化 T1/T2 主线完成、且用户显式授权后才能激活。

## 目标

不是“试试更大的模型”，而是只测试一个新归纳假设：

- MIOFlow 2.0：增长/死亡 + 随机动力学是否改善特定 T1 state-mass/branch 指标；或
- scDiffEq：随机扩散是否改善特定 P3 多模态指标。

一次只能选一个工具、一个 task/board、一个 kill metric、一个 candidate。

## 必须固定

- current structured parent；
- 唯一新假设；
- 唯一 kill metric；
- 计算预算；
- 不使用的能力；
- 失败即停止的阈值。

## 禁止

- 把新工具作为统一 backbone；
- 同时改 mass、state vocabulary、decoder 和 geometry；
- 多模型竞赛；
- 超参搜索；
- 用高容量掩盖 hidden-state/hidden-gene 信息缺口。

## 终点

一个 kill-test report；只有预定指标改善且错误与结构化主线互补时，才进入后续工程评估。

## 实例化（2026-09-04，coordinator 裁定，用户授权继续）

状态：`FROZEN` → `ACTIVE`（一次性实例化；本节后任何改动需新授权）。

- **工具**：MIOFlow 2.0（PyPI `mioflow`）。不选 scDiffEq：其目标"P3 多模态指标"在当前三 board 框架（T1/T2/T3）中无对应 board，不可实例化。
- **task/board**：T1:val 唯一 board。依据：T1-S2 moscot 双 lane 已被服务器 REJECT（44.9/44.8 vs best 48.5、baseline 47.0），结构化主线在 T1 state-mass 外推上的残差是当前最明确的未解释缺口；T2 已由 J1-FGW 晋级（57.3），T3 已收口。
- **唯一新假设**：moscot 静态传输无增长/死亡项，其残差集中在 state-mass 漂移；把传输耦合替换为 MIOFlow 带增长/死亡的随机动力学，能改善 held-out stage 的 state-mass 预测。
- **current structured parent**：`candidate/T1_val/v0004_strict_pseudobulk_shift`（48.5，只读）。候选构造 = T1-S2 管线其余组件冻结，仅将 moscot 耦合替换为 MIOFlow 动力学。
- **唯一 kill metric**：source-only leave-one-stage-out（留 E9.5，state 词表用 T1-PRE-HARMONIZE 已冻结的 28 union fine_state + crosswalk）上 per-state mass 分布误差（L1 距离，定义先于运行写死）。双臂对照：strict-shift parent 臂 + moscot-decoder 臂（T1-S2 冻结 alpha=1.0127 管线，两臂可复用已冻结 artifact 值，不得重复计算超预算）。
- **计算预算**：一次环境部署（新 venv `ve-hx-mioflow`，固定版本+SHA256+license 审计，照 T3-TOOLCHAIN 先例；网络仅用于此次 PyPI 部署，其后关闭）+ 一次 MIOFlow 训练（本机无 GPU，CPU 训练，预声明规模上限与 2 小时 wall-clock 上限，超限即 BLOCKED）+ 一次 holdout 评估。不生成正式 H5AD 候选，不上传服务器。
- **不使用的能力**：不作统一 backbone；不同时改 mass/state vocabulary/decoder/geometry；不多模型竞赛；不超参搜索；不用高容量掩盖 hidden-state/hidden-gene 信息缺口。
- **失败即停阈值**：MIOFlow 臂 mass 误差未同时优于双臂 → `REJECT`，出 kill-test report 后停止；互补性（误差与结构化主线是否互补）只在指标改善时评估。
