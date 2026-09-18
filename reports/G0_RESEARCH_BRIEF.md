# G0 Research Brief — 15 轮独立建模开工前（2026-09-16）

## 1. 本地打分工具（已部署、可运行）
`third_party/veckit/score_h5ad.py`（veckit 0.1.1@46d41e63，P0 11/11 哈希验证，`--help` 实测可用）。
本轮统一调用（SEED=20260916，结果进 `artifacts/g0_research_baseline/`）：

| Board | input（基线） | target（pseudo） | reference/wt |
|---|---|---|---|
| T1 | v0004 strict shift | data/E9.5_RNA.h5ad | data/E8.5_RNA.h5ad |
| T2 embryo | v0010 mean+mass | data/E7.25.h5ad | data/E6.75.h5ad |
| T2 heart | v0013 mean+mass | data/E8.75.h5ad | data/E8.25_late.h5ad |
| T3 | v0009 gata4 zero | data/E9.5_mab21l2_ko.h5ad | data/E9.5.h5ad |

**口径警告（写进每轮 gate）**：pseudo-target 取自训练数据，是比 held-out 更简单的问题（veckit 原话 "NOT a preview of your real score"）；T3 的 pseudo 还是**不同 KO**（Mab21l2≠Gata4），是最弱的一档 gate，只防灾难、不保排序（PROXY_VS_SERVER 教训：T1-R1 pseudo 最优→服务器全灭）。晋级=**同 target 同 seed 下超基线本地分**，不与 server 分直接比。

## 2. 已测试路线（T1/T3 优先）
- **T1**（best v0004=48.47）： composition 外推（45.9✗）、no-comp（46.2✗）、B1-A3（47.5/47.7✗）、moscot decoder（44.9/44.8✗）、MIOFlow killtest（✗，但 mioflow state-mass 臂本身优于 parent——失败在动力学外推不在 mass）、保守族 damp/popmix/massgraft（47.58–47.85✗，mass025 族内最优）。floor 47.0 vs 官方 50 未解。**未测**：late-program bridge（缺数据）、开放集状态出生、外部时序预训练、分支生成。
- **T3**（best v0009/v0010=46.95）：signed residual（44.7/44.0✗）、genotype zeroing（+0.15✓）、lineage gate（无增量）、developmental delay（46.45/46.47✗）、signed-prior 链（关闭）。de_score（38–39）全批最弱。Gata6 F/+ 未确认。**未测**：目标基因条件表征、多扰动预训练、阶段/谱系条件因果生成。
- **T2**（58.29；embryo 62.29 / heart 62.04 / extrap 50.53）：FGW 全局匹配（打平关闭）、mean+mass bridge（✓✓）、extrap 校准三 lane 已生成未评分。**最弱 board = heart_extrap**；heart variogram（28）是明确 headroom。

## 3. 外部方法短名单（联网检索，Tavily 8+8；两篇全文抓取失败 422，留待各轮细读）
- **scNODE**（PMC11373355）：temporal Neural-ODE，外推任务上 beating MIOFlow/PRESCIENT → **T1 首选新路线**（E8.5→E9.5 拟合、E10.5 预测；与被 kill 的 MIOFlow 直接对位）。
- **scPerturBench**（Nature Methods 2025， generalizable perturbation benchmark）：T3 方法排名待细读（抓取失败，T3-R1 前补读）。
- **scGen / CPA**：VAE 潜空间 WT→perturbed 向量算术 → **T3 对位**（Gata4 KO = WT + 方向向量；zeroing 已证方向有价值，CPA 给出幅度/状态特异性）。
- **PertDiffBench / diffusion**（2026 bioRxiv）：生成式扰动建模，T3 备选。
- **Gene-Chronos**：参数高效发育时间模型，T1 备选。
- Virtual Cell Challenge 2026（Arc）：只跟踪，不直接消费。

## 4. 路线短名单（不限死，每 task R1–R3 三选，R4–R5 优化最优轮）
- **T1**：(a) scNODE 式 neural-ODE 外推；(b) 开放集状态出生（E10.5 新状态 v0004 给不出）；(c) 校准版组成预测（v0002 过激进的温和版）／v0004 顶残差结构建模。
- **T3**：(a) scGen/CPA 式潜空间位移（含 CellOracle Gata4 真实模拟输出直接成候选——S1A 产物现成）；(b) 状态特异分级幅度（zeroing 的连续版）；(c) scPerturBench 高排名方法复刻（先补读）。
- **T2**（殿后，主攻 extrap）：interp/extrap 专家分离；variogram 导向的空间场；v0008–0010 已生成 lane 视情况纳入。

## 5. 资源与纪律（用户红线）
单 lane ≤16 核/128G/12h；重型全局并发≤2；intermediate 及时清（磁盘仅剩 1.6T/44T，比 CPU 更紧）。
沿用 batch4 禁令：不反推 target、不拿 proxy 当晋级结论、不覆盖 scored artifact。

## 6. 基线本地重测分（SEED=20260916，同口径 gate；本地量纲 0–1，不与 server 分比）
- T1 v0004（target E9.5_RNA / ref E8.5_RNA）：de_score **0.8868** / de_direction **0.8895** / energy_distance 0.09656 / mmd_u 0.00332 / variogram 0.000948 / pb_rel_err 0.0478 / library_size_ratio 1.0 / variance_ratio 1.016 / composition_JSD 0.0 / pseudobulk_pearson 0.9987。T1 晋级线 = 同 target 同 seed 下 de_score>0.8868 且 de_direction>0.8895（双 metric 同时超；variogram/mmd_u 作辅助，不单列门）。
- T2 embryo v0010 / T2 heart v0013 / T3 v0009：待后台任务完成后补记。
- T2 embryo v0010（target E7.25 / ref E6.75）：de_score **0.7241** / de_direction **0.6589** / mmd_u 0.0092 / variogram 0.088284 / occupancy_dice 0.8975 / neighborhood_mmd 0.03636 / energy_distance 0.55469。T2-embryo 晋级线 = 同口径下 de 双 metric 同时超。
- T2 heart v0013（target E8.75 / ref E8.25_late）：de_score **0.5435** / de_direction **0.7697** / energy_distance 1.06209 / mmd_u 0.02511 / variogram 0.082772 / occupancy_dice 0.7426 / neighborhood_mmd 0.04088。T2-heart 晋级线 = 同口径下 de 双 metric 同时超。注意本地 heart de（0.54）低于 embryo（0.72），且 occupancy_dice（0.74 vs 0.90）明显更弱——heart 的 headroom 在 DE + 组成两端。
- T3 v0009（target mab21l2_KO / wt E9.5）：de_score **0.1739** / de_direction **0.2444** / severity_slope **-0.5368** / mmd_u 0.05276 / energy_distance 2.44272。T3 晋级线 = 同口径下 de 双 metric 同时超 + severity_slope 转正。如预期这是最弱 gate（不同 KO 的 pseudo-target，绝对值极低）——T3 轮次只用它做相对排序与灾难检查，不解释绝对值。
