# 官方与项目状态快照

快照日期：2026-09-04。官网可能更新；执行时必须刷新差异。

## 官方事实

### Score scale

- 每个 board 的 floor 为 50；
- ceiling 为同一真实 target 的 split-half；
- floor 不是硬编码常数，而是 bundle 构建时由同 scorer 实测后用于映射；
- T1/T2 的 no-change 是 `copy_last`；
- T3 的 no-change 是 `wt_identity`。

来源：`https://virtualembryo.ai/challenge/baselines`

### P2 submission budget

- 每 task 每 UTC 日 8 次 scored submissions；
- format checks unlimited；
- 单文件 ≤1200 MB；
- score 可以用于选择 prediction；
- 不得用于反演 hidden target。

来源：`https://virtualembryo.ai/challenge/rules`

### Agent Team

- run 从 configuration lock 开始；
- lock 后人不得根据中间结果 steer；
- 人可以选择多个已完成 run 中的提交；
- scored 前至少提交两种 distinct evidence；
- candidate 必须由 agent 写出，人不能修改。

来源：`https://virtualembryo.ai/challenge/rules`

### T1

- train E8.5/E9.5；
- validation E10.5；
- test E12.5；
- whole transcriptome；
- 评分：DE 25%、direction 25%、distribution 30%、co-variation 20%。

来源：`https://virtualembryo.ai/challenge/evaluation?task=1`

### T2

- expression + 3D coordinates；
- heart interpolation E8.5、extrapolation E10.5；
- embryo interpolation E7.5；
- molecular/cellular/tissue/local 四组各约 25%；
- rotation/translation invariant。

来源：`https://virtualembryo.ai/challenge/evaluation?task=2`

### T3

公开任务页将 validation 简写为 Gata4 KO。项目旧锁定材料进一步记录了 Mesp1 lineage 与 Gata6 F/+ 条件；Batch 4 不把旧描述自动当作当前官方事实，T3-R1 在运行前必须从本地 starter metadata / contract 再确认复合基因型。

- train Mab21l2 KO E9.5；
- validation Gata4 KO E8.75；
- test β-catenin KO E8.75；
- 评分关注 WT→KO effect；
- validation 比 test 更 specific，test effect 更 diffuse；
- T3 shape 在当前官方说明中不是主要 ranking 优化目标，Batch 4 冻结 coordinates。

来源：
- `https://virtualembryo.ai/challenge/tasks/perturbation`
- `https://virtualembryo.ai/challenge/evaluation?task=3`

## 用户提供的榜单目标

```text
第十名：T1 62 / T2 62 / T3 68
```

这不是官网抓取结果；必须在项目报告中标记为 `user-supplied leaderboard snapshot`。

## 项目公开仓库快照

公开 GitHub 在制作本包时最新可见 commit：

```text
804d9f46a909a493d120a2cb3f0928efe3911b99
```

其状态仍把 B2-T3-A1 v0006/7 记为 `score_pending`。用户说明本地已经更新分数并宣告旧方法失败，因此：

- 本包不硬编码 v0006/7 数值；
- P0 必须读取本地工作区；
- 若本地仍未同步，写 `BLOCKED_SCORE_SYNC`；
- 不得从公开旧 commit 覆盖本地新记录。

## 项目静态最佳参考

```text
T1: 48.5, v0004 strict pseudobulk shift
T2:
  embryo interpolation: 60.1, scale
  heart interpolation: 57.3, pycpd parent + FGW assignment
  heart extrapolation: 50.5, baseline
T3: 45.3, wt_identity
```

T2 aggregate 应由服务器当前值优先；按显示 board 分数直接平均只是 derived estimate。
