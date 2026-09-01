# T2 官方 reference-row controls 审计

更新时间：2026-08-21

## 范围

本审计复现官网 Reference rows 页面定义的三个 T2 controls，并在本地
`veckit` scorer 上做 1,000-cell pseudo-target smoke。pseudo-target 来自已落盘的
starter-pack proxy，不是官方 hidden validation，因此结果只证明实现和 scorer
链路可运行，不证明 leaderboard 行为。

实现与测试：

- runner：[scripts/t2_controls.py](/home/huyudi/014_virtualEmbryo/scripts/t2_controls.py)
- regression tests：[tests/test_t2_controls.py](/home/huyudi/014_virtualEmbryo/tests/test_t2_controls.py)
- 输出目录：[outputs/t2_controls](/home/huyudi/014_virtualEmbryo/outputs/t2_controls)
- scorer：`third_party/veckit` commit `46d41e63f42a9aab815db20b742feeccd249cb17`

`ctrl_random_cube` 使用 pseudo-target 的真实坐标范围生成随机点云，并在
`uns["ve_control"]` 标记 `audit_only=true`；它没有进入任何模型选择或预测轨道。

## 实现核对

| Control | 表达 | 坐标 |
|---|---|---|
| `ctrl_scale_ref` | `reference.X * 2.0` | 原样保留 |
| `ctrl_random_cube` | 原样保留 | 各轴在 target min/max 之间独立均匀采样 |
| `ctrl_squashed_ref` | 原样保留 | 以 reference 质心为中心乘 `(4.0, 1.0, 0.25)`，再回到原质心 |

`PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib pytest -q
tests/test_t2_baseline.py tests/test_t2_controls.py`：`9 passed`。

## Local scorer smoke

数值为 `de_score / energy_distance / d2_shape / occupancy_dice /
neighborhood_mmd / pb_rel_err`；每个 board 的 floor 是同一 pseudo-target
slice 上的 `copy_last`。

| Board | Row | de | energy | d2 shape | occupancy | neighborhood | pb error |
|---|---|---:|---:|---:|---:|---:|---:|
| embryo interp | `copy_last` floor | 0.0000 | 7.29907 | 0.02764 | 0.7588 | 0.30066 | 1.1742 |
| embryo interp | `ctrl_scale_ref` | -2.4808 | 29.70725 | 0.10697 | 0.4962 | 0.47669 | 2.1556 |
| embryo interp | `ctrl_random_cube` | 0.0000 | 7.24842 | 0.04093 | 0.8421 | 0.40185 | 0.9417 |
| embryo interp | `ctrl_squashed_ref` | 0.0000 | 7.24842 | 0.21271 | 0.4035 | 0.23866 | 0.9417 |
| heart interp | `copy_last` floor | 0.0000 | 2.39492 | 0.04791 | 0.7704 | 0.16928 | 0.4973 |
| heart interp | `ctrl_scale_ref` | 0.0000 | 14.66590 | 0.08652 | 0.4407 | 0.31399 | 1.1342 |
| heart interp | `ctrl_random_cube` | 0.0000 | 3.31180 | 0.03977 | 0.7486 | 0.38744 | 0.5594 |
| heart interp | `ctrl_squashed_ref` | 0.0000 | 3.31180 | 0.11980 | 0.3750 | 0.25573 | 0.5594 |
| heart extrap | `copy_last` floor | 0.0000 | 2.39496 | 0.04811 | 0.7704 | 0.14081 | 0.5706 |
| heart extrap | `ctrl_scale_ref` | -0.6000 | 17.37602 | 0.08677 | 0.5763 | 0.39151 | 1.4707 |
| heart extrap | `ctrl_random_cube` | 0.0000 | 3.31178 | 0.04599 | 0.8431 | 0.37125 | 0.6140 |
| heart extrap | `ctrl_squashed_ref` | 0.0000 | 3.31178 | 0.15304 | 0.4096 | 0.20626 | 0.6140 |

这些行有意只破坏某一类性质，所以单个指标可能比 floor 好；例如 random
cube 的体积/占据指标较好，但 neighborhood 指标明显恶化。当前 scorer 输出
没有把本地 pseudo-target 映射成官网 leaderboard 总分，故不能据此宣称
“controls 均低于 floor”或完成官方 Gate 4。当前结论是：T2 controls 的定义、
边界和本地执行链路已通过，正式 hidden-board control audit 仍未完成。
