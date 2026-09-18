# T3 Gata4 KO 调研报告：从 46.95 到 70+ 的路线图（纯调研，未实现任何新方法）

日期 2026-09-16。目标：`mu3xgdyf-yp76u9`。用户关键判断：头部 70+ 证明有解。约束：只调研不动手；不推测头部解法（按用户要求删除原 task-2）。

## 1. 我们已做的 T3 尝试与失败归因（task-1-retro）

| # | 路线 | 版本 | 服务器 | 结论 |
|---|---|---|---|---|
| 1 | wt_identity 基线 | v0001 | 45.3 | floor |
| 2 | signed-prior 下游 residual | v0004/v0005 | 44.7/44.0 | 有害（两实证之一） |
| 3 | signed prior committee（B2-T3-A1） | v0006/v0007 | 45.5/45.5 | 并列 best（当时），后被超 |
| 4 | exact floor（均匀抽样零变换） | v0008 | 46.79 | 新 best（当时）；旧 residual 有害第二实证 |
| 5 | Gata4 全细胞清零 | v0009 | 46.95 | **当前 best 并列**；唯一 +0.15 |
| 6 | Gata4 hard-lineage 清零 | v0010 | 46.95 | 与 v0009 不可区分 |
| 7 | 发育 delay α=0.25/0.50 | v0011/v0012 | 46.45/46.47 | 双败 → 架构重置触发 |
| 8 | 17 motif 靶点传导 | v0013 | 46.88 | -0.07 |
| 9 | 三分位剂量 | v0014 | 46.95 | 持平 |
| 10 | 谱系剂量 | v0015 | 46.95 | 持平 |
| 11 | 剂量+传导叠加 | v0016 | 46.88 | -0.07（上传 pick，机制最强） |
| 12 | 叠加 2× 幅度 | v0017 | 46.84 | -0.11 |

核心证据：
- **de_score 钉死 39.2**：v0009/v0010/v0013/v0014/v0015/v0016/v0017 七连同（另 v0008=38.8、v0011=38.1、v0012=38.5）。DE 幅度项在 Gata4 轴任何形状变化下不动。
- **本地 kit 盲性**：pseudo-target 是 Mab21l2 KO（不同基因），proxy de 0.1739 五连同——本地门只能防灾难，不能排序（已如实降级）。
- **T3 计分结构**（veckit T3/metrics_v2.py：de 三项 + 分布两项 mmd_u/variogram + shape 六项 + 约束四项）。70+ 约束反推（纯算术，不归因头部）：若 de/方向/slope 三项满分 100 且其余八项取我方当前均值 50.7，则总分 ≈ (300+405.6)/11 ≈ 64.1 < 70——**头部必须同时拿下 de 三项高分和分布/shape 项**（标注：算术下界，非头部解法分析）。

## 2. 已发表/开源方法 survey（task-2-survey；全部可验证来源，推测已标注）

| 方法 | 年份/出处 | 原理一句话 | 开源 | 与 T3 的差距 |
|---|---|---|---|---|
| scGen | 2019, VAE 潜空间向量算术 | WT→pert 潜位移 | scvi-tools | 需见过该扰动；Gata4 未见过 → 零样本失效 |
| CPA | 2021, VAE 解耦扰动/状态/剂量 | 组合扰动可加 | theislab/CPA | 同上零样本问题；in-silico benchmark 中方向接近随机 |
| GEARS | 2024 Nat Biotech, 双图 GNN（共表达+GO） | GO 图把未见基因放到功能近邻 | snap-stanford/GEARS | 需扰动训练数据；GO 图无胚胎心脏特异性 |
| scGPT/scFoundation | 2024, 大规模预训练 transformer | 微调做扰动预测 | bowang-lab/scGPT | benchmark 显示经常≈随机；微调需扰动数据 |
| scLAMBDA | 2024, LLM 辅助 embedding 生成模型 | 文献知识给未见基因 embedding | 论文+代码 | LLM 知识非胚胎特异；dbDiffusion 对比中被超 |
| dbDiffusion | 2026 PNAS, 潜扩散+分类器无关引导+**两步去偏** | 专打未见扰动均值效应+CI | ergan-shang/dbDiffusion | 最新 SOTA（Replogle 大效应强，Yao 小效应弱） |
| CellOracle | 2023 Nature, GRN+信号传导模拟 | TF KO 级联 | morris-lab/CellOracle | 零样本方向预测跨系全败（2024 benchmark）；我们 S1A 产物现成 |
| scTenifoldKnk | 2022, scGRN 流形对齐虚拟 KO | 零目标基因出边 | cailab-tamu | 只给扰动基因排序，不给全表达矩阵 |
| CIPHER | 2025, 线性响应 Δx=Σu | 统计物理解析解 | 论文（查代码） | 线性假设；但 Ahlmann-Eltze 证明线性≈深度 |
| scPerturBench | 2025 Nat Methods, 27 方法×29 数据集 | 选型依据：先验知识+细胞上下文 embedding 改善泛化 | bm2-lab | benchmark 本身，非方法 |
| VCC2025 冠军 xTrimoSCPerturb | 2025, 深度+手工统计特征 | 纯端到端不够，要叠统计特征 | 部分 | 与我们“T1 收缩胜”一致：统计收缩是通用增益 |

## 3. 至少 2 个对已有发表/开源方法的优化（task-3-optimize；非我们旧路线重复）

**OPT-A：dbDiffusion 式两步去偏 + 数据驱动 embedding（基于 dbDiffusion, PNAS 2026）**
- 原方法：潜扩散 + classifier-free guidance + 两步去偏；embedding 决定精度（数据驱动聚类对齐时最强，AI embedding 弱时互补）。
- 改动（3 点）：(a) embedding 不用 LLM/GO 通用知识，改用我们 E8.75 WT + 心脏谱系 52% 约束的胚胎特异聚类；(b) 去偏第二步的目标从“均值效应”改为 veckit de 三项可导代理（de 才是 23 分差距的主战场）；(c) 用 severiy_slope 转正做早停门（我们 slope 恒 -0.54，最弱环）。
- 与旧路线对照：我们从未做过生成式潜扩散（R1 神经 ODE 是轨迹模型非扩散；T3 全是手工位移）→ 无重复。
- 预期/成本/风险/验证门：预期 de 39.2→45+（dbDiffusion 在大效应集上超 GEARS/scGPT；Gata4 是强 TF）；成本 GPU 扩散训练（>12h 红线，需申请或拆 batch）；风险：小效应弱（Yao 教训）、embedding 对齐未知；验证门：先在 Mab21l2 proxy 上验证去偏步骤有效再动 Gata4。

**OPT-B：CIPHER 线性响应 + 心脏谱系约束（基于 CIPHER 2025, Δx=Σu）**
- 原方法：统计物理线性响应解析解，无训练。
- 改动（3 点）：(a) 响应核只在心脏谱系52%细胞上估计（其余 Unknown 用全局回退——T1-R2 小样本教训的正面应用）；(b) u 向量不用单位 KO，改用 CellOracle 真实模拟的 Gata4 级联幅度（S1A-v7 产物现成）；(c) 加 T1-R4 式 t-收缩（w=|t|/(|t|+2)，已证通用增益）压噪声基因。
- 与旧路线对照：我们从未做过线性响应解析解（v0013 传导是固定幅度非响应核）→ 无重复。
- 预期/成本/风险/验证门：预期 direction 49.6→55+（线性在 benchmark 中≈深度，谱系约束去噪）；成本 CPU 分钟级；风险：线性欠拟合真实 KO 非线性；验证门：先复现 v0009 分数（恒等输入→恒等输出）再加核。

## 4. ≥8 个新尝试方向 + 30 轮预算规划（task-4-synthesize；计数：D1–D8 共 8 个，其中 OPT-A/OPT-B 占 2 个优化位）

| # | 方向 | 类型 | 原理 | 预期增益 | 成本 | 风险 | 验证门 |
|---|---|---|---|---|---|---|---|
| D1 | OPT-A：胚胎特异 dbDiffusion 去偏 | 发表方法优化 | 见 §3 | de 39→45+ | GPU，需拆 batch | 小效应弱 | proxy 去偏有效性 |
| D2 | OPT-B：谱系约束 CIPHER 线性响应 | 发表方法优化 | 见 §3 | dir 49.6→55+ | CPU 分钟级 | 线性欠拟合 | 恒等复现 v0009 |
| D3 | GEARS-GO 图胚胎化 | 发表方法应用 | GO 图换 E8.75 共表达+心脏谱系图；Gata4 未见→功能近邻给非零预测 | 非零 de（当前 39.2 是零附近） | GPU 中等 | GO 无胚胎边 | 先在 Mab21l2 上验证非零 |
| D4 | scLAMBDA-LLM 胚胎文献 embedding | 发表方法应用 | Gata4 心脏文献 embedding 代替 motif 0/1（v0013 的 17 靶点只有 3 个非零幅度是教训） | 靶点幅度全覆盖 | CPU+API | LLM 幻觉 | embedding 与 CellOracle 级联一致性 |
| D5 | scTenifoldKnk 全矩阵化 | 发表方法扩展 | Knk 只给排序；把扰动排序转成全 500 基因位移（排序分位数×WT 分散） | de 非零 | CPU | 排序→幅度映射随意 | 映射在 proxy 上单调性 |
| D6 | de 三项直优（可导代理） | 新目标 | 现有 lane 全在表达空间手工位移；直接以 de_score/de_direction/severity_slope 可导代理为损失，梯度搜位移场 | de 主战场直打 | GPU/CPU | 代理与真 de 错位 | 代理在历史 12 版本上 rank 一致 |
| D7 | 分布/shape 项 Miner（mmd_u 51.5→60） | 新目标 | 70+ 反推要求分布/shape 项也高；variogram/neighborhood_mmd 用 T2-R3 式空间平滑（已证 +0.014 de  spillover） | mmd_u/vario 各 +5 | CPU | server 空间项权重未知 | 本地 variogram 单调 |
| D8 | 状态特异 KO（52% 心脏 vs Unknown 分家） | 新机制 | 现有 lane 全细胞同规则；心脏谱系与 Unknown 分别估计响应（Unknown 用收缩回退） | dir +3 | CPU | Unknown 无信号 | 分家 vs 不分家本地对照 |

30 轮预算建议（8/task/day server 约束内）：D2(2) → D8(2) → D5(3) → D3(4) → D6(4) → D4(3) → D1(8) → D7(4)，合计 30。顺序原理：便宜 CPU 先行（D2/D8/D5），GEARS 与直优居中，扩散最贵最后（且以前面轮次的 embedding 结论为输入）。每 5 轮一个仲裁点：de 未动则砍该分支（de 钉死是唯一硬门）。

## 5. 需求逐项确认计数
- ≥8 个新方向：D1–D8 = 8 ✅
- ≥2 个对已发表/开源方法的优化：OPT-A（dbDiffusion）、OPT-B（CIPHER）= 2 ✅（对照旧路线无重复 ✅）
- 结合已做尝试：§1 十二条 + 失败归因 ✅
- 70+：仅作差距动机与算术下界，不归因头部 ✅
- 只调研未实现：本报告零新候选、零建模 ✅

## 6. 执行附录（2026-09-17，用户明确“继续完成所有工作，最后统一提交”）
- D2–D7 七 lane＋D2 首轮 v0018 共 8 候选（v0018–v0025）全部 contract PASS、无回归、本地全盲（de 0.1739 第 3–12 例），统包 `deliveries/g1t3__t3__upload__20260917.zip`。
- 更正：心脏谱系在 T3 行中实占 **20.75%**（§4 的 52% 作废）；D4＝HOP2 替代（motif 二值实锤＋无 API 已验证）、D6＝SIGNMAX 替代（直优门证伪）、D1＝DEBIAS 改编（无 GPU 训练已披露）、D7 lib-ratio 0.69 系 Jensen 效应（已验算非 bug）。
- D4 首跑维度 bug（hcol 多一维）修复重跑，失败 receipt 保留。30 轮预算实际消耗：构建 8 轮（D2–D7 各 1 构建轮），剩余预算＝服务器仲裁轮。
