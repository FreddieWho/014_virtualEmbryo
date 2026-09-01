# 本批明确不施工的路线

以下方向重要，但不是第一批：

1. T1 P1 open-set 新生状态与外部阶段原型；
2. T1 unbalanced multi-marginal/branch flow；
3. T2 G2/G3 点云形态生成、SE(3) 等变 flow、coarse-to-fine geometry；
4. T2 端到端 NicheFlow；
5. T3 E3 专门 severity calibration；
6. T3 conditional OT/flow、GEARS 重训、PerturbODE；
7. 三任务统一 foundation generator；
8. 多 seed 稳定性、完整 ablation 和大规模超参数搜索。

B1-A1 的边界例外：允许最多 4 次全局 source-only 临时尝试，每次完整覆盖三个 board。B1-A2 同样允许最多 4 次 source-only 临时尝试。临时尝试必须有独立 attempt 记录，但不得晋升为第三条最终 lane；B1-A1 最终保留 `L1_FORMAL_LOG_RMS` 与 `L2_ALL_STAGE_LOG_RMS_OLS`，B1-A2 最终保留两条预先锁定的 Spearman lane。

进入下一批的最低条件：本批至少有一个原子产生明确主指标增益，且我们知道它能否作为独立 submission 或 ensemble 组件保留。B1-A1 在六个服务器分数全部回填前不得宣称完成。
