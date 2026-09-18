# T1 val 调研报告：从 48.47 到 70+ 的路线图（纯调研，未实现任何新方法）

日期 2026-09-17。目标：`mu4ked7e-tqcd36`。用户关键判断：头部 70+ 证明有解；调参不可能带来 30 分增益，要新架构/路线/组合。约束：只调研不动手；不推测头部解法；跨任务移植需单独论证新机制。

## 1. 我们已做的 T1 尝试与失败归因（task-1-retro；21 个版本全有服务器分数）

| # | 路线 | 版本 | 服务器 | 结论 |
|---|---|---|---|---|
| 1 | copy_last 基线 | v0001 | 47.0 | floor（分层版同分） |
| 2 | 收缩 pseudobulk＋组成外推 | v0002 | 45.9 | 有害：Foregut/pSHF 压到下限，动了 30% 分布项 |
| 3 | 去组成外推保守版 | v0003 | 46.2 | 仍负，组成项是雷区 |
| 4 | strict 收缩 pseudobulk shift | v0004 | **48.47** | **当前 best**（de 43.8/dir 55.9/mmd 51.5/vario 40.6） |
| 5 | mass residual 共享/lane | v0005/v0006 | 47.5/47.7 | B1-A3 双负 |
| 6 | moscot decoder 双 lane | v0007/v0008 | 44.9/44.8 | 结构化外推 −3.6，路线关闭 |
| 7 | MIOFlow 增长/死亡 kill test | — | 未达阈值 | 增长/死亡动力学关闭（mass 不是失败点） |
| 8 | exact floor | v0009 | 47.0 | 分层被排除 |
| 9 | n=1706 floor 探针 | v0010 | 46.8 | n_obs 被排除 |
| 10 | 保守族 damp/popmix/graft | v0011–v0014 | 47.58/47.77/47.85/46.90 | 全负，族内 L3 最优，路线关闭 |
| 11 | neural-ODE 潜动力学 | v0015 | 48.51 | +0.04 落 TIE 带 |
| 12 | substate 细分增量 | v0016 | 48.14 | −0.33 |
| 13 | maturity 分箱增量 | v0017 | 47.46 | −1.01 |
| 14 | t-收缩 sweep C=1/2/4 | v0018–v0021 | 48.48/48.54/48.48/48.34 | C1 最优 +0.07 仍落带；C 全程跨度 0.20，弱旋钮，关闭 |

核心证据：
- **天花板是 de↔variogram 互换**：收缩族拿 de（43.2–43.6 < 43.8）换 variogram（42–44 > 40.6），没有单项短板，是结构 trade。
- **T1 proxy 方向存活（三任务唯一正对照）**：本地 PROMOTED 的收缩族服务器全 ≥48.34，本地毙掉的三条全挂——与 T2-extrap 反转、T3 全盲形成对比。新机制可用本地门做第一道筛。
- **已关闭、不得重复**：moscot-family、MIOFlow/增长动力学、组成外推、保守族、收缩扫参（t-shrink 本人是 best 家族，任何“再调收缩”都是调参，按用户要求排除）。
- **T1 契约**（`docs/_starter_pack/config/task_contracts.yaml`）：heart，32285 全基因，train E8.5/E9.5 → val E10.5（test E12.5），无坐标要求；权重 de 0.25 / direction 0.25 / distribution 0.30 / covariation 0.20。E9.5 数据仅 counts/log1p 层，**无 spliced/unspliced——velocity 家族（scVelo/dynamo/DeepVelo/CellRank2-kinetics）无米下锅，直接排除**。
- **70+ 算术下界（不归因头部）**：当前加权 ≈ .25×43.8＋.25×55.9＋.30×46＋.20×50 ≈ 48.7 ✓。70 分要求每项 +20 量级（如 65/70/72/72 → 69.75），其中 **distribution 权重最高（0.30）是最大杠杆**——这是 D5/D6 存在的理由。

## 2. 已发表/开源方法 survey（task-2-survey；scTimeBench 2026 为主标尺，全文已索引）

scTimeBench（Bioinformatics 2026，10 方法×多数据集×插值/外推/联合三场景，结论：**联合训练 VAE＋神经微分方程的家族整体最强**）：

| 方法 | 年份/出处 | 原理一句话 | 开源 | 与 T1 的差距 |
|---|---|---|---|---|
| scIMF | 2025 arXiv:2505.16492（PLOS 2026） | Transformer＋McKean-Vlasov 神经 SDE，细胞间注意力学群体动力学；**benchmark 总第一** | QiJiang-QJ/scIMF | 我们 v0015 是解耦单细胞 ODE，无联合训练、无细胞间项 |
| scNODE | 2024 Bioinformatics | VAE＋neural ODE＋dynamic regularization，联合训练 | 论文（查代码） | 与 v0015 同族但联合训练＋分布漂移正则——正是我们的缺口 |
| OT-CFM | 2024（Tong 等） | minibatch-OT＋条件流匹配，simulation-free 训练 | 论文（查代码） | 无需 ODE 积分器；与 moscot 的 Sinkhorn 耦合不同用法 |
| CellMNN | 2025 arXiv:2510.02903 | 局部线性潜 ODE，端到端单阶段，**无 OT 预处理**，学出 TRRUST 一致的基因互作 | 论文（查代码） | 直击 moscot 失败点（OT 耦合＋多阶段）；PCA 预处理适配 32285 全基因 |
| PRESCIENT | 2021 | PCA＋势景观神经 SDE（Waddington 图景） | 论文＋代码 | 随机性天然打 distribution 项；我们全是确定性位移 |
| PI-SDE | 2024（Jiang & Wan） | 物理信息神经 SDE | 论文（查代码） | 物理约束正则，未验证于心脏发育 |
| SquidDiff | 2026（He 等） | 条件扩散，Gaussian-MMD 最强、其余最差 | siyuh/Squidiff | 分布拟合专精，de 弱——需与位移法组合 |
| TrajectoryNet | 2020（Tong 等） | DOT＋连续归一化流 | 论文＋代码 | CNF 鼻祖，被 OT-CFM 在训练效率上取代 |
| Sagittarius | 2025 | 可学习时间编码＋伪时间对齐 | 论文（查代码） | E7.75 background 从未被使用——新数据轴 |
| 自回归离散-token | 2026 bioRxiv | 因果掩码预测下一细胞表示 | 预印本 | 极新，细胞级离散化在 32285 基因上未经验证 |
| MIOFlow | 2022 | 测地 VAE＋Neural ODE | 已试/kill | **排除：已杀** |
| Moscot/WOT | 2019/2025 | OT 耦合/解码 | 已试 | **排除：已杀** |
| Velocity 家族 | — | 剪接动力学 | 不适用 | **排除：无 spliced 层** |

## 3. 两个对已发表/开源方法的优化（task-3-optimize；非我们旧路线重复）

**OPT-A：scIMF 式联合 VAE＋Transformer-MV-SDE（基于 scIMF, arXiv:2505.16492）**
- 原方法：Transformer 编码器近似交互平均场漂移（f_intra 2×256 全连接＋f_inter 单层 2 头注意力，扩散系数常数 0.1，Sinkhorn-W2 DOT 损失，batch 512）。
- 改动（3 点）：(a) 联合训练 VAE＋SDE（我们 v0015 是解耦两步，这是 scTimeBench 点名的家族共性缺口）；(b) 注意力只在心脏谱系内计算（跨谱系注意力在 T2 上已被证是噪声源；谱系门是我们的移植经验）；(c) 三点 DOT 损失 E8.5→E9.5→E10.5（原方法两点耦合；E7.75 background 作锚点正则）。
- 与旧路线对照：v0015 是单细胞独立 ODE、无 VAE、无细胞间项；moscot 是静态耦合无动力学 → 无重复。
- 预期/成本/风险/验证门：预期 distribution（0.30 权重）＋covariation 主攻，de 43.8→50+（群体动力学补分布）；成本 GPU（SDE＋Sinkhorn，>12h 需拆 batch）；风险：注意力在 32285 基因上爆炸（需 PCA 先降维，CellMNN 同款）；验证门：先做 E8.5→E9.5 回报预测（held-out），过了再碰 E10.5。

**OPT-B：CellMNN 式局部线性显式 ODE（基于 CellMNN, arXiv:2510.02903）**
- 原方法：编码-解码＋潜空间局部线性 ODE，端到端单阶段，除 PCA 外无预处理，学出基因互作（TRRUST 一致），多数据集联合训练可扩展。
- 改动（3 点）：(a) 直接以 E8.5→E9.5 心脏数据训练，抛弃一切 OT 耦合（moscot 的失败点就是耦合）；(b) 局部线性工作点按 cm 谱系分区（谱系内线性假设远强于全局）；(c) 学出的基因互作矩阵用 CollecTRI 快照做一致性审计（T3-S1B 现成审计链移植——跨任务移植论证：审计链与任务无关，是方法组件复用）。
- 与旧路线对照：moscot 用 OT 耦合＋解码（已杀）；v0015 用黑盒 ODE 无显式互作；保守族无动力学 → 无重复。
- 预期/成本/风险/验证门：预期 direction 55.9→60+（显式互作给方向）＋covariation（互作即协变）；成本 GPU 中等（单阶段，比 SDE 便宜）；风险：局部线性在 E9.5→E10.5 大跨度（1 天）欠拟合——scTimeBench 外推场景本就最难；验证门：互作矩阵先过 TRRUST/CollecTRI 富集，不过则停。

## 4. 至少 6 个新方向（task-4-synthesize；计数：D1–D7 共 7 个，其中 OPT-A/OPT-B 占 2 个优化位）

| # | 方向 | 类型 | 原理 | 预期 | 成本 | 风险 | 验证门 |
|---|---|---|---|---|---|---|---|
| D1 | OPT-A：联合 VAE＋Transformer-MV-SDE | 发表方法优化 | 见 §3 | dist/covar 主攻，de→50+ | GPU，需拆 batch | 注意力爆炸 | E8.5→E9.5 回报 |
| D2 | OPT-B：局部线性显式 ODE | 发表方法优化 | 见 §3 | dir→60+，covar | GPU 中等 | 大跨度欠拟合 | 互作富集审计 |
| D3 | OT-CFM 流匹配预测 | 发表方法应用 | minibatch-OT＋条件流匹配，simulation-free；耦合代价用 E8.5→E9.5 几何（静态耦合只做训练脚手架，不做预测——与 moscot 已杀用法的本质区别） | 训练效率＋分布 | GPU 中等 | 流匹配在 32285 基因上未验证 | 先 500 基因 panel 子集验证再全基因 |
| D4 | T2 表达桥移植 | 跨任务移植 | T2-R2 在 heart_interp 上 +4.79 的共享端点锚定几何，用来锚定 E10.5 组成＋per-type 位移。**新机制论证**：v0002 已杀的是“方向性线性组成外推”，桥是“共享端点数据锚定”，一杀一立不矛盾；且 T1 本地 proxy 存活，可做第一道筛（T3 移植无此条件） | 组成项止血＋分布 | CPU/GPU 小 | 外推锚定仍可能漂 | 本地 proxy 先行（T1 专属特权） |
| D5 | 条件扩散总体生成 | 发表方法应用/组合 | SquidDiff 式条件扩散直学生成 E10.5 总体（专打 0.30 的 distribution）＋v0004 位移法定 de 方向；两路按权重拼 | dist 大幅 | GPU 大 | de 弱，需组合 | 分布项本地先行 |
| D6 | 势景观 SDE | 发表方法应用 | PRESCIENT 式 Waddington 势＋随机动力学；我们 21 个版本全是确定性位移，随机性是全新轴 | dist/shape | GPU 中等 | 势函数难学 | 回报场景先行 |
| D7 | E7.75 background＋时间扭曲对齐 | 新数据轴 | 契约里的 background E7.75 从未被使用；Sagittarius 式可学习时间编码把 E7.75/E8.5/E9.5 对到统一伪时间轴，多锚点定 E10.5 | 方向/分布 | CPU/GPU 小 | 跨 batch 效应 | 对齐后 E8.5→E9.5 回报 |

检索-评估 30 轮使用建议（用户口径：检索-评估迭代，非提交轮次）：已用约 10 轮（契约＋INDEX＋追踪＋权重＋scTimeBench＋scIMF＋CellMNN/review＋SquidDiff＋层验证＋落盘）；剩余 ≈20 轮优先：OPT-A/B 的论文复现评估（8）→ D3/D5/D6 的代码可得性与规模评估（6）→ D4/D7 的本地数据评估（4）→ 综合仲裁（2）。

## 5. 需求逐项确认计数
- ≥6 个新方向：D1–D7 = 7 ✅
- ≥2 个对已发表/开源方法的优化：OPT-A（scIMF）、OPT-B（CellMNN）= 2 ✅（逐一对照旧路线无重复 ✅；跨任务移植 D4＋OPT-B(c) 已单独论证 ✅）
- 结合已做尝试：§1 二十一条＋失败归因 ✅
- 70+：仅差距动机与算术下界（69.75 测算），不归因头部 ✅
- 只调研未实现：零新候选、零建模 ✅
- 非调参：收缩/C/damp/popmix/graft 全族关闭，无一入选 ✅
