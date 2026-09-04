# Batch 4 范围、追赶目标与架构切换阈值

## 1. 定位

Batch 4 是一次**修复性追赶**：

- 不以夺冠为本批验收；
- 不把某条小修路线封为长期主线；
- 不因一次 +0.2 就宣布方向成立；
- 不因一次失败就关闭比当前实现更大的方法空间；
- 最终必须决定哪些低容量资产值得带入下一代架构。

用户提供的当前第十名参考：

```text
T1 = 62
T2 = 62
T3 = 68
```

这是 Batch 4 的差距标尺，不是可直接优化的 target。

## 2. 当前起点

执行时由本地 registry 解析，静态参考如下：

| Task | 当前 best | 主要问题 |
|---|---:|---|
| T1 | 48.5 | 低于第十名 13.5；floor parity 未证明；表达 decoder 和新状态支持不足 |
| T2 | per-board 60.1 / 57.3 / 50.5；aggregate 约 56.0 | 插值组件有正信号；heart extrapolation 和表达/组成仍弱 |
| T3 | 45.3 floor best；v0006/7 已由用户标记失败 | 低于第十名 22.7；旧 signed-prior 族关闭；确定基因型事实尚未单独隔离 |

## 3. 成功分级

### S0 · 审计成功

必须全部完成：

- v0006/7 分数与状态在本地 registry / index / tracking 一致；
- current best 无 stale parent；
- floor builder 差异被逐项列出；
- Agent Team evidence 生成链可运行；
- 所有 Batch 4 run 有可复核 lock。

S0 不代表提分，但没有 S0，后续分数不可归因。

### S1 · 基线修复成功

T1 / T3 的严格 no-change 构造：

- 服务器达到 50.0 附近，建议容差 ±0.2；或
- 明确证明参赛者不能复制 reference floor 的具体 bundle 差异，并给出官方/项目构造差异。

未解决 floor parity 时，任何复杂候选都只可临时评分，不可成为最终 parent。

### S2 · 有效追赶

满足任一：

- 某 task 相对当前 best 提升 ≥1.0；
- 某 task 与第十名差距缩小 ≥15%；
- 某 board 提升 ≥1.0 且不靠其他 board 回退抵消；
- 一个此前混合失败的组件被隔离后产生服务器正信号。

### S3 · 理想的 Batch 4 结果

这不是承诺，只是本批 stretch：

| Task | Batch 4 stretch | 与第十名仍有差距 |
|---|---:|---:|
| T1 | 54–55 | 7–8 |
| T2 | 59–60 | 2–3 |
| T3 | 52–55 | 13–16 |

达到 S3 仍不能证明获奖潜力，但会提供更好的大型架构 parent。

## 4. 不应被视为成功

- 只产生新的 prior / coupling / field，没有 H5AD；
- 只增加测试数量和文档数量；
- 本地 pseudo-score 上升但服务器未测；
- 同一个小假设反复换名字；
- 通过 publication-grade gate，但没有 leaderboard candidate；
- 用服务器分数差分反推 target；
- +0.1 的单次波动被包装成路线胜利；
- T2 单 board 提分但 aggregate 不变且未说明。

## 5. 架构调整触发器

Batch 4 closeout 时，满足任一即输出 `ARCHITECTURE_RESET_REQUIRED`：

### 全局触发

- 没有任何 task 提升 ≥1.0；
- floor parity 仍未解决；
- local proxy 对服务器排序继续大面积反向；
- 所有增益只来自输出格式/抽样，建模能力没有改善；
- 当前 best 与第十名总差距缩小不足 10%。

### Task 触发

| Task | 触发条件 | 下一代架构必须新增的能力 |
|---|---|---|
| T1 | 完成 R1/R2 后仍 <52 | 开放集状态出生、外部时序预训练、非自主/分支生成、全转录组 decoder |
| T2 | 完成 R1/R2/R3 后 aggregate 仍 <58 | 表达—组成—几何—生态位联合生成；插值/外推专家分离 |
| T3 | 完成 R1/R2 后仍 ≤50 | 目标基因条件表征、多扰动预训练、阶段/谱系条件因果生成，而非继续手工 residual |
| T3 | validation 有提升但离 68 仍 >12 | 必须把 validation 修补与 β-catenin 泛化分开；启动新架构前置研究 |

## 6. 路线决策标签

### `PROMOTE_PARENT`

服务器提升达到预声明阈值，且没有 contract / protected failure。可成为下一 run parent。

### `KEEP_COMPONENT`

完整候选未胜，但某个独立组件有可重复正证据，接口清晰，可进入下一代架构。

### `REJECT_IMPLEMENTATION`

当前算法、参数族或离散化失败；不否定更大的科学方向。

### `CLOSE_ROUTE`

同一信息假设的多个合理实现均失败，且无独立正组件。Batch 4 不再追加。

### `BLOCKED_INPUT`

缺失的是 parent、合法数据、工具或官方契约；不得包装成科学失败。

### `ARCHITECTURE_RESET_REQUIRED`

低容量修复已耗尽，需要单独方案包和新的架构选择，不在 Batch 4 内继续扩张。

## 7. 服务器提升阈值

默认：

```text
clear promotion: +0.5 or more
weak positive: +0.2 to +0.4
tie/noise: -0.1 to +0.1
clear reject: -0.5 or worse
```

若同一候选涉及多个 board，以 task aggregate 和 per-board 一起判断。  
弱正只能 `KEEP_COMPONENT` 或 `PROVISIONAL_PARENT`，不能被称为获奖路线。
