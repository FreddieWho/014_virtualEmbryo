# Batch 4 Error Signatures

## floor constructor
- T1 copy_last 47.0 vs official 50：项目 stratified/uniform/两种 n_obs（5118/1706）三探针 47.0/47.0/46.8，子集规则被排除；剩余 bundle 级差异本地不可见。签名：floor 缺口与抽样无关。
- T3 wt_identity 45.3→46.8（uniform draw）：旧分层构造本身 -1.5 有害。

## amplitude
- T1 damp050（-0.89）、heart_extrap 未测：v0004 damp=1.0 无 overshoot 证据。
- T2-R3 L2 time1.333 未评分：时间归一假设未验证。

## state mass
- moscot mass graft 25%（T1-R1 L3，47.85，族内最优但未晋级）vs 50%（46.90，跌破 floor）：mass 信号弱且剂量敏感。
- T2-R2 L2 组成重采样双 board 一致增益（+0.50 / +4.79 的 L2-L1 差）：mass 在插值 board 是真增量。

## expression direction
- T3 de_score 全批最弱（38–39 across floor/R1/R2）：任何手工 residual 都没动 DE 幅度；只有 genotype zeroing 把 board 从 45.3 抬到 46.95。
- T2-R2 heart L2 de_score 60.6：mean+mass bridge 同时修方向与幅度。

## covariance/residual
- T1 v0004 的 strict shift 仍是不可战胜的 parent：decoder（44.9）、damp、popmix、mass 全败。残差结构未知是 T1 核心缺口。

## geometry
- heart_interp FGW 全局匹配 vs greedy：服务器打平（57.3/57.31 vs 57.25）。几何离散化不是瓶颈。
- heart_extrap 几何路线全灭（沿用 batch3 结论），表达校准未测。

## assignment
- 同上：72–73% 冲突的 greedy→全局匹配，board 零收益。Assignment 已出清。

## stage conditioning
- T3 developmental delay（5/33 states 有方向）：46.45/46.47，双败。低容量 stage conditioning 不够。

## genotype conditioning
- Gata4 zeroing +0.15（tied, lineage gate 无额外收益）；Gata6 F/+ 未确认（L3 BLOCKED）。单基因型事实已榨干。

## proxy/server disagreement
- T2-R1：本地 NFS/Moran/objective 全优 → 服务器打平。
- T2-R2 heart：本地 60% clip 担忧 → 服务器 +4.79 大胜（担忧方向反了）。
- T1-R1：本地 pseudo 高分传统（pseudo-target 循环），服务器全灭。
- 教训：本地 proxy 只保灾难，不保排序；任何“本地全优”不得写入晋级结论（本批已执行）。
