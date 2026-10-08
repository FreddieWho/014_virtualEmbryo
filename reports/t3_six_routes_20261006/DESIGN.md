# T3 六新路线设计（2026-10-06）

目标：在现役 v0048 `n2hurdle=47.93` 之上，新增 6 条路线并全部实现（源侧 LOPO
评测 + 胚胎交付契约）。既有优化/结合 3 条（O1/O2/O3），全新机制 3 条（N1/N2/N3）。

统一框架（继承 v0071 已批准的源侧冻结评测协议）：
- 来源：GSE261783 OP2，5454 细胞 × 500 基因，26 条件，ctrl 220 细胞；
  manifest `reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json`（SIGNED_RESPONSE）。
- 预测器：锁定 `scripts/t3_autoresearch/retained_model.py`（GO 嵌入 + 核 + Ridge 校正），
  仅用批准的 WT/GO 嵌入，不用 Gata4 目标 truth 做选择。
- 评测：`third_party/veckit/common/core_metrics.py` 五分项
  （de_score、de_direction、severity_abs、mmd_u、variogram），seed0；
  开发 17 基因 LOPO，加权秩 [.30,.25,.25,.12,.08]，缺失项重归一；
  历史 test 6 基因仅报告。
- 交付：选中方法的 operator 作用于母本 v0048 的 X（7449×500），Gata4 列归零，
  contract PASS、SHA 登记、INDEX/TRACKING 更新。

## O1 dual_form（结合：v0070 additive ⊕ v0071 乘法）
既有 v0070 只试加性残差（源 MSE 降但 H5AD 退步），v0071 只试乘法倍率。
新：单候选内同时执行乘法步与有界加性残差步（raw-intensity 空间混合），
out = log1p(max(expm1(emit_mult(base, s_m·beta)) + s_a·(expm1(add)-expm1(base)), 0))。
s_m、s_a ∈ {0, .25, .5, 1.0} 网格，按 LOPO 加权秩联合选择。

## O2 gate_mult（结合：v0048 hurdle 概率门 × v0071 乘法）
v0071 的 beta 对所有非零位置均匀缩放；v0048 的 Hurdle 给出每细胞×基因的
响应概率 p。新：delta_ij = s·p_ij·beta_j。
交付用 v0048 锁定 hurdle 模型 probability 列；源侧 LOPO 用
proxy 门 d_j=ctrl 基因 j 的阳性细胞比例（声明不对称），选 s。

## O3 shrunk_beta（优化：v0071 的 beta 按可靠性收缩）
v0071 给了统一 ±log2 上限与单一强度。新：每基因收缩因子
r_j = |delta_j| / (|delta_j| + k·sd_j)，sd_j 为留一扰动集内该基因
Y 的跨扰动离散度；beta_j ← r_j·beta_j。k ∈ {.5, 1, 2} 选。

## N1 nmf_ablation（全新：WT 程序分解消融）
在源侧 ctrl 上拟合 NMF(K=16, seed 固定)，取其基因空间载荷 H 与本查询的
预测 delta 相关性最高的程序 k*(g)，从 expm1(ctrl) 中扣除
s·W[:,k*]·H[k*,:]（非负截断）。交付：同法在胚胎 WT（E8.75，父行序）上
消融与 Gata4 预测 delta 最对齐的程序。
与“加性均值平移/乘法倍率/hurdle”正交——它按共表达程序重写分布而非按
均值偏移。注：源条件基因不在 500 基因面板内，故程序选择以预测 delta
对齐（不读 KO truth），而非以查询基因表达相关替代。

## N2 marker_gate（全新：谱系 marker 门控）
S1A 的 POSITIVE/NEGATIVE markers 定义一个 WT 细胞行系身份打分
w_i = clip((#pos 标记检出 − #neg 标记检出)/4, 0, 1)，
delta_ij = s·w_i·beta_j。机制假设：Gata4 缺失的响应应只出现在
Mesp1+ 心源谱系细胞；其余细胞群不改写。

## N3 switch_emit（全新：双向开关/零膨胀发射）
对每个条件 g 估计相对于 ctrl 的零转移率：
off_j = max(P_g(x_ij==0) − P_ctrl(x_ij==0), 0)，
on_j = max(P_ctrl(x_ij==0) − P_g(x_ij==0), 0)。
emit: out_ij = log1p(expm1(base)·(1−s·off_j))，且 base=0 处填入
s·on_j·mean_ctrl_j（有界）。直接面向 DE 子项最敏感的“有无表达翻转”，
而非平滑幅度缩放。s 选。

## 不做/边界
- 外部同基因（Gata4 在胚胎其他阶段）数据继续隔离，等主办方答复。
- N2 的源侧 LOPO 因来源无细胞类型维度，gate 以密度/marker 代理替代，
  不作源胚胎完全等价声明。
- 本地评测不等于服务器分；未评分候选不得宣称晋级。
