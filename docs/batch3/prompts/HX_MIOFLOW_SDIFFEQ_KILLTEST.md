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
