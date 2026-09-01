# First cycle report

更新时间：2026-08-21

## 状态

`COMPLETE_FOR_COMPETITION`。本周期的关键交付是：官方数据、面板和 scorer 已落盘，
submission contract 可验证，并完成首个 baseline scored submission，服务器返回了
可用于后续比较的分数。

科学晋级状态单独记为 `BLOCKED_FOR_SCIENTIFIC_PROMOTION_ONLY`；这不阻断
leaderboard 路线。

## 服务器 baseline

| Score | Value |
|---|---:|
| Total | 145.7 |
| T1 · single-cell temporal | 47.0 |
| T2 | 53.4 |
| T2 · heart interpolation | 53.0 |
| T2 · heart extrapolation | 50.5 |
| T2 · embryo interpolation | 56.7 |
| T3 · Gata4 KO | 45.3 |

完整登记见 [`SERVER_SCORE_REGISTRY.md`](SERVER_SCORE_REGISTRY.md)。

## 当前最短竞争路线

下一次只尝试一个可归因变化：T2 heart interpolation 的中点表达插值。以 E8.25
为细胞和空间载体，使用已发布 E8.25/E8.75 的 celltype/global 混合表达 shift，
固定 `damp=0.5`、`celltype_weight=0.5`，并恢复 log1p library size 到 10,000；
不改 geometry。

候选文件：
`submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad`

该候选已通过本地 contract，`target_used=false`，并取得服务器 heart interpolation
分数 `53.6`，相对 baseline `53.0` 提升 `+0.6`。它现在是该 board 的当前 best；
服务器 submission ID 和原始证据仍待补录。

作为筛选依据的公开-stage proxy（E8.75 target、E8.25 reference）相对 E8.25
copy baseline 的变化为：`de_score 0.0000 → 0.0543`、`energy_distance
2.24542 → 1.88809`、`pb_rel_err 0.4876 → 0.4414`、`neighborhood_mmd
0.09719 → 0.08890`，`library_size_ratio` 保持 `1.000`。这只是候选筛选证据，
不是官网分数预测。

## 裁剪后的规则

- 服务器分数是竞争真值；local pseudo-score 只用于筛选和风险提示；
- 一次提交只改一个 board/一个主要变量；提交后立即登记分数和差值；
- 没有服务器结果时标记 `score_pending`；
- 不为关闭科学 Gate 而暂停有效 leaderboard 尝试；
- 暂不进入 diffusion、flow、ODE 或大规模外部数据路线。

## 不作的结论

当前结果不能证明 biological superiority、跨基因扰动泛化或 hidden test 性能。
这些是科学报告边界，不是竞赛提交阻塞条件。
