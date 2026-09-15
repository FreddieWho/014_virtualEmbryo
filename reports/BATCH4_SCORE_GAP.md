# Batch 4 Score Gap — vs 10th-place reference 62 / 62 / 68 (total 192)

| Task | Batch start | Batch end | Δ | Gap to 10th (end) | Gap reduction |
|---|---|---:|---:|---:|---|
| T1 | 48.47 | 48.47 | 0.00 | 13.53 | 0% |
| T2 | 55.98 | 58.29 | +2.31 | 3.71 | (6.02→3.71) 38% of task gap |
| T3 | 46.79 | 46.95 | +0.16 | 21.05 | ~1% of task gap |
| **Total** | **151.2** | **153.7** | **+2.5** | **38.3** | **6.1% (< 10%)** |

Board-level T2: embryo 60.15→62.29 (+2.14); heart_interp 57.25→62.04 (+4.79);
heart_extrap 50.53→50.53 (0.00, unscored R3 lanes pending future batch).

## 判定

- S2（某 task +1.0）：T2 +2.31，达成。
- S3 stretch（T2 59–60）：未达成（58.29，差 0.71）。
- 与第十名总差距缩小 6.1% < 10% → 全局 `ARCHITECTURE_RESET_REQUIRED` 触发器成立。

## 4. 架构调整触发器逐项

| 触发器 | 状态 |
|---|---|
| 没有任何 task 提升 ≥1.0 | 未成立（T2 +2.31） |
| floor parity 仍未解决 | **成立**（T1 47.0 / T3 46.8，未到 50±0.2） |
| local proxy 对服务器排序大面积反向 | 部分成立（见 PROXY_VS_SERVER；T2-R1 全优→打平，R2 担忧→大胜） |
| 所有增益只来自输出格式/抽样，建模能力无改善 | 未成立（mean+mass bridge 是表达-组成建模增益） |
| 总差距缩小不足 10% | **成立**（6.1%） |
| T1 <52 | **成立**（48.47） |
| T2 <58 | 未成立（58.29，裕度仅 0.29，如实记录为边缘） |
| T3 ≤50 | **成立**（46.95） |
| T3 validation 离 68 仍 >12 | **成立**（差 21.05） |

结论：触发器多项成立 → `ARCHITECTURE_RESET_REQUIRED`（T2 插值资产保留，见 brief）。
