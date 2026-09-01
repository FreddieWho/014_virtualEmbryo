# First evidence loop blocker

更新时间：2026-08-21

状态：`BLOCKED_FOR_SCIENTIFIC_PROMOTION_ONLY`；leaderboard 竞争路线不阻塞。
科学 blocker 只限制 biological claim、正式模型晋级和科学 Gate 关闭，不限制合规
候选生成、format check、scored submission 或服务器反馈循环。

## 阻塞点

当前只有 starter-pack proxy 和本地 pseudo-target，没有独立的、target-blind
inner stage/replicate 可用于选择 heart interpolation 的 expression/geometry
超参数，也没有官方 hidden validation 的本地 truth。若现在继续用 E8.75 proxy
挑选 `lambda`、`rho` 或 B1/B2 组合，就会把评估目标泄漏进科学模型选择；若依据
单个 proxy 分数推进，则不能支撑 biological superiority 结论。但这不妨碍把预先
固定、合规、可追溯的候选提交到 leaderboard 获取真实反馈。

因此当前不能诚实地：

- 关闭 Gate 3/4 为正式通过；
- 选择并晋级 expression shrinkage 或 geometry candidate；
- 关闭 Gate 5 T2-B1/B2；
- 把一次 scored submission 当成独立科学验证。

以上限制不等于不能提交；下一次 leaderboard 候选可以标记为
`competition_exploratory`，并以服务器分数判断是否保留。

## 已完成证据

- 官方数据、panels、scorer、两个 notebook 已核对并落盘；E8.25 的 225 MB
  人工确认已登记，未再作为资源阻塞。
- T2 `copy_last` 与 `pseudobulk_shift` 已按官方 notebook 规则实现。
- T2 `ctrl_scale_ref`、`ctrl_random_cube`、`ctrl_squashed_ref` 已实现；三个本地
  pseudo-target board 均完成 scorer smoke。
- `PYTHONPATH=. env LD_LIBRARY_PATH=/opt/anaconda3/lib pytest -q tests`：`14 passed`。
- 5-seed exploratory panel 与 source-only artifact audit 已完成，但不等于
  biological replication 或 hidden validation。

## 最小人工决策

科学路线保持冻结，直到出现以下任一条件；竞争路线不需要等待：

1. 提供/解锁不暴露评估 target 的独立 stage 或 biological replicate，用于内层
   选择；或
2. 明确批准使用一套预先声明的固定参数继续做“诊断性、不可晋级”的 B1/B2
   实验，并接受其结果不能支撑正式模型优越性结论。

在得到该决策或新数据前，仍可继续做目标盲、固定参数的竞赛候选并提交；只需保留
必要的 contract、合规和文件追溯。榜单分数可以用于竞争迭代，但不能写成
biological superiority 结论。候选和合同见 `reports/SUBMISSION_READINESS.md`。
