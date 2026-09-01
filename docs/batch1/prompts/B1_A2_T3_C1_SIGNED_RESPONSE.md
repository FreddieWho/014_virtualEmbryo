# B1-A2 — T3 C1：方向优先的有符号稀疏响应

## 唯一目标

以目标阶段匹配 WT 为锚，只构造小而稀疏、具有基因特异方向依据的 KO residual，首先改善 E1 差异基因集合/符号和 E2 全基因方向/排序，即 DES 与 DCS。PSS 本轮只记录，不专门调参。

## 原子边界

本轮必须同时处理 E1+E2，因为 gene set 与 signed rank 来自同一个 pseudobulk residual；同时用 K2 WT 背景保护约束非响应基因。不得升级为自由 KO 生成器或 conditional flow。

## 输入

自动定位：

1. 目标阶段匹配 WT；
2. Mab21l2 KO 与匹配 WT 训练对；
3. 目标 KO gene/board 定义；
4. 现有 state label、frozen latent 或现有 state classifier；
5. 项目中已经登记且允许使用的 signed GRN、directed gene graph、gene-function prior 或 gene embedding。

本原子不得新下载外部数据。优先级：

1. 阶段/状态特异 signed GRN；
2. 一般 signed directed GRN；
3. directed/unsigned graph，加 WT 内部相关符号；
4. 若以上均不存在，使用 WT 中 target gene 与其他基因的稳健相关作为明确标注的弱 fallback。

## 最小算法

### 1. 构建 signed rank prior

对目标 KO 基因 g，为每个基因 j 构建一个分数 `s_j`：

- signed GRN 中，g 激活 j，则 KO 倾向使 j 下调；g 抑制 j，则 KO 倾向使 j 上调；
- 允许最多两跳传播，但每一跳必须衰减；
- 用目标阶段 WT 中的 gene/module activity 对边做门控；目标阶段不活跃的边向 0 收缩；
- 若只能用相关 fallback，KO 方向取相关符号的相反方向，并在 MANIFEST 中标记 `prior_strength=weak`。

不得直接把 Mab21l2 的全局 delta 当成目标 KO 的方向。

### 2. 确定稀疏支持

- 上调和下调候选分别按 `|s_j|` 排序；
- 非零基因总数由 Mab21l2 训练 KO 的真实 DE gene 数或现有官方 baseline 的固定规则解析得到；不做 k sweep；
- 只有置信度超过该 prior 非零分布中位数的基因进入 residual；其余保持 WT。

### 3. 状态门控

- 对每个现有状态 c，计算 target gene 或其 module 在目标 WT 中的活性；
- 将全局 signed residual 乘以 `[0,1]` 的状态活性 gate；
- 不新建状态，不改变状态比例；本轮只让不同状态有不同的 residual 大小。

### 4. 幅度固定而非调优

本轮不优化 E3。使用唯一解析尺度：

- 以 Mab21l2 KO 的 DE genes 中位绝对效应作为基础幅度；
- 乘以目标 prior 的中位置信度与状态 gate；
- 对所有 residual 施加一个保守上界：任何基因的绝对 pseudobulk 变化不得超过训练 KO 相应分位数的上界；
- 不根据 Gata4/leaderboard 分数重新调幅度。

### 5. 生成细胞级提交

- 从目标 WT 细胞开始；
- 每个状态内给细胞加同一个有符号均值 residual，保留 WT 的细胞级 residual 与协方差；
- 负值截断为 0；
- 被敲除基因必须置 0；
- 坐标保持 WT，不优化 T3 形态。

## 唯一开发检查

用同一规则做一次 Mab21l2 自预测检查：构建 prior 时禁止读取 Mab21l2 KO delta 的方向，只允许用它确定 DE 数量与基础幅度；然后对真实 Mab21l2 KO 计算一次 DES/DCS。该检查只用于发现方向规则是否完全反了，不允许据此做参数 sweep。

## 验收

- contract 通过；
- `L1_CELL_LEVEL_SPEARMAN` 与 `L2_STATE_PSEUDOBULK_SPEARMAN` 各生成一个最终候选，形成固定 1+1 结果集；
- 目标 KO gene 为 0；
- residual 稀疏率、正负基因数、状态 gate 和 prior 来源写入 MANIFEST；
- 与 wt_identity 相比，至少产生非零、非共线于 WT expression 的 signed rank；
- 完成同一版本官方验证 scorer；
- 输出两个 `prediction.h5ad`、各自的 `signed_prior.tsv`、`state_gates.tsv`、指标、MANIFEST、RESULT 和 `FINAL_SET_MANIFEST`；
- 两条通过 contract/invariant 的 lane 都必须交给用户人工上传并分别评分；self-check 偏弱不取消第二条，服务器分数返回前保持 `score_pending`。

若 DES/DCS self-check 未改善，记录为风险但仍交付两条合规 lane；不得现场切换到 flow、GEARS 重训或其他大模型。

## 禁止

- 禁止复制 shift_transfer 的 Mab21l2 delta；
- 禁止用 target/leaderboard 反复选择 top-k 或 severity；
- 禁止新下载未审计 GRN；
- 禁止优化绝对 KO 表达 Pearson；
- 禁止自动线上提交。
