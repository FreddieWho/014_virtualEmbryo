# T1 任务追踪：single-cell temporal

更新时间：2026-08-28

分数以 [`reports/SERVER_SCORE_REGISTRY.md`](../../reports/SERVER_SCORE_REGISTRY.md) 为准，候选文件以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 为准。本文件只做简短解释和路线选择。

## 当前状态

- 当前最高服务器分数：**48.5**
- 当前最佳：`candidate/T1_val/v0004_strict_pseudobulk_shift`
- 当前状态：`active`；`v0002` 已评分 45.9（-1.1）淘汰；v0004 取得 48.5，B1-A3 两条均低于该 best，v0006 仅为 B1-A3 lane winner
- 任务阻塞：无；科学 promotion 阻塞不影响提交

## Top 3 路线

三条路线均已有服务器分数；B1-A3 两条均高于旧 baseline。

| 位次 | 路线 | 通俗说明 | 服务器分数 | 状态 |
|---|---|---|---:|---|
| 1 | `v0004_strict_pseudobulk_shift` | 去掉组成外推并采用严格的状态内 pseudobulk shift | **48.5** | 已评分，当前 best |
| 2 | `B1-A3 L2_E95_EXPRESSION_PROBE` | 用 source-only expression projection 分区，再从 T1 基线做完整父行 replay | **47.7** | 已评分，B1-A3 lane winner |
| 3 | `B1-A3 L1_SHARED_UNRESOLVED` | 用 shared label + unresolved 分区，再从 T1 基线做完整父行 replay | **47.5** | 已评分，B1-A3 scored backup |

## 变更记录

每次修改或分叉只写一句人话：改了什么、为什么、结果如何。

| 日期 | 版本/分叉 | 父版本 | 一句话变更 | 结果/决定 |
|---|---|---|---|---|
| 2026-08-21 | `baseline-001/T1_val/v0001` | 无 | 先用 `copy_last` 建立 T1 合法提交底线。 | 服务器 `47.0`；保留 |
| 2026-08-22 | 追踪文档建立 | `v0001` | 把 T1 的已评分基线和两个待评分方向固定下来。 | 不改变模型；等待下一候选 |
| 2026-08-22 | `candidate/T1_val/v0002_shrunk_pseudobulk_shift` | `v0001` | 从 `copy_last` 分叉出收缩版 `pseudobulk_shift`：per-type Δ 与全局 Δ 各半混合、E9.5 独有类型回退全局 Δ、共有类型组成按 E8.5→E9.5 线性外推后定向抽样，其余 contract 不变。 | 本地 contract pass；上传评分 |
| 2026-08-24 | `submission-003/T1_val/v0002` | `v0001` | 服务器返回 45.9，比基线低 1.1 分；最可疑的是组成外推太激进（Foregut/pSHF 被压到下限），动到了占 30% 的分布项。 | 淘汰 v0002；保留 `copy_last` 为 best；评分快照存于 `submissions/scored/submission-003/` |
| 2026-08-24 | `candidate/T1_val/v0003_no_comp_extrap` | `v0001` | 从 `v0001` 分叉保守版：去掉组成外推，保留 per-type Δ 与全局 Δ 混合（w=0.5）+ E9.5 独有类型回退全局 Δ，其余不变。 | 服务器 46.2（-0.8）；淘汰 |
| 2026-08-24 | `candidate/T1_val/v0004_strict_pseudobulk_shift` | `v0001` | 从 `v0001` 分叉严格官方复刻：per-type Δ 纯、缺失类型 Δ=0、无组成外推。 | 服务器 48.5（+1.5）；当前 T1 best |
| 2026-08-28 | `B1-A3/T1_val/v0005_b1_a3_shared_unresolved` | `v0001` | 采用 exact shared label + `UNRESOLVED_STAGE_SPECIFIC` 的 source-only partition，按状态质量外推并做完整父行 residual replay。 | contract pass；服务器 47.5（+0.5），低于 v0004=48.5；保留为 scored backup |
| 2026-08-28 | `B1-A3/T1_val/v0006_b1_a3_e95_expression_probe` | `v0001` | 采用 E9.5 固定词表和全 panel cosine expression projection 冻结 E8.5 state assignment，再做同一质量外推与 residual replay。 | contract pass；服务器 47.7（+0.7），低于 v0004=48.5；保留为 B1-A3 lane winner |
| 2026-08-28 | B1-A3 本地评分尝试 | `v0005/v0006` | 对两条正式候选执行锁定的 full-panel scorer；L1 在 900 秒超时，L2 无结果且进程异常消失后中断。 | 不使用缩减/替代 scorer；服务器已回填 47.5/47.7，官方结果优先 |

## 下一步

`B1-A3` 已完成服务器评分：L1=47.5，L2=47.7。L2 为 B1-A3 lane winner，但全局 T1 best 是先前 v0004=48.5；两条 B1-A3 均保留为不可变 scored candidates，在获得新授权 atom 前不追加 T1 调参。
