# T3 第二波六新路线设计（2026-10-07）

第一波（v0075–v0080，2026-10-07 回分）无一晋级：o1_dual 46.73、o2_gate 47.31、
o3_shrunk 47.43、n1_nmf 47.93（同分平局，现役留下）、n2_marker 47.40、
n3_switch 46.82。现役 v0048 `n2hurdle` = 47.93 不变。round2 组合栈
（n1stack H+rate 47.86 等）也低于现役，H+rate 已试。

晋级门槛：总分 > 48.03（±0.1 平局带外）。本波 6 条：既有优化/结合 3 条
（O1/O2/O3，参数全部沿用第一波冻结选中值，不再扫描；LOPO 仅作诊断），
全新机制 3 条（N1/N2/N3，按 v0071 冻结协议 LOPO 网格选择）。

统一框架：同第一波——GSE261783 OP2 冻结源 + 锁定 retained model +
官方 core_metrics 五分项；交付作用于母本 v0048 X，Gata4 列归零，
contract PASS、INDEX 登记。源侧 LOPO 不等于服务器分。

## O1 hnmf（结合：现役 v0048 ⊕ v0078 NMF 消融，等权平均）
第一波最好的两个：现役（47.93）与 v0078（47.93 同分，DE 42.6 六候选最高、
variogram 49.9）。新组合：out = 0.5·v0048_X + 0.5·nmf_matrix（log 空间等权
平均；nmf_matrix 按第一波冻结 recipe 重算：embryo WT NMF K=16 seed20261006、
程序按 corr(H[k], delta4) 对齐、s=0.25 消融）。round2 的 n1stack 是 H 后接
rate 的顺序组合；本条是算术平均且第二成分换成 NMF，均为新组合。
参数固定 0.5/0.5，不扫描（SYNTHESIS 禁混合系数重扫）。

## O2 pnmf（结合：v0076 hurdle 概率门 × v0078 NMF 消融）
v0078 的消融对所有细胞均匀执行；新：只对 hurdle 概率 p 认为响应的
细胞×基因消融：expm1 预测 = max(expm1(base) − s·p_ij·prog_ij, 0)，
s=0.25 沿用 N1 冻结值，p 用 v0048 锁定 hurdle 模型（同第一波 O2 交付门）。
参数不扫描。

## O3 psb（结合：o2 门 × o3 收缩 × v0071 乘法）
o2 与 o3 是第一波最好的两个 o 路线（47.31/47.43）；新组合同时执行
每细胞门与每基因收缩：delta_ij = 0.5·p_ij·r_j·beta_j，s=0.5（o2 冻结）、
k=2.0（o3 冻结）、r_j=|delta_j|/(|delta_j|+k·sd_j+1e-12)、sd_j 为 26 扰动
跨条件离散度。参数不扫描。

## N1 qtl（全新：分位数形状迁移）
既有路线都只动均值（加性平移/乘法倍率）或程序结构（NMF）；新：逐基因
正值分位数迁移——把源 ctrl 的正值分布形状映射到最 GO 相似供体条件的
KO 分布形状（five_ops.quantile_response，bound ±log2，零值与组内秩保持）。
LOPO 时供体取 train-minus-g 内最相似者（预测器不见留出扰动表达）；
交付时供体取 26 条件内对 Gata4 最相似者。强度 {.25,.5,1.0} LOPO 选择。

## N2 dsign（全新：供体符号一致性门）
新门控机制：逐基因二值门——供体条件 pseudobulk 位移符号与预测 delta
符号一致的基因才应用响应（其余保持母本值），幅度用 v0071 beta。
LOPO 供体同 N1 规则。强度 {.25,.5,1.0} LOPO 选择。
与 o3（幅度连续收缩）、n2_marker（WT marker 门）正交：这是外部供体
符号稳定性门。

## N3 pswap（全新：程序置换/质量再分配）
N1 消融直接删除对齐程序的质量；新：把对齐程序的质量置换到最反相关
程序上（每细胞质量比再分配）：expm1 预测 = expm1(base) − s·prog_k+ +
s·ratio_i·prog_k−，ratio_i = sum(prog_k+)/sum(prog_k-)（逐细胞标量）。
同时面向 DE（去掉对齐程序）与库比 bounds（质量守恒）。
强度 {.25,.5,1.0} LOPO 选择。

## 不做/边界
- 同基因（Gata4 其他阶段）数据继续隔离等主办方答复。
- O1/O2/O3 参数全部沿用第一波冻结值，不做网格重扫；LOPO 行仅诊断，
  不作 selected_before_test 声明。
- N1/N2 的供体选择规则（GO 相似度 argmax）与第一波 n3_donor 相同。
- 本地源侧指标不等于服务器分；未评分不晋级。
