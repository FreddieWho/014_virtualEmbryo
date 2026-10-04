# PLAN — Virtual Embryo Challenge

建立日期：2026-09-04（batch1–3 收口后补建；此前科学判断散见于 `docs/batch3/` 方案与 `docs/coordination/` 文档，本文件为唯一权威版本）。
修改规则：仅当科学判断改变时修改，需用户确认；agent 不得自行修改，只能报告偏离。

**修订记录**
- 2026-09-27：**科学问题节的 T2 三个 board 目标 stage 事实性订正**（用户授权）。原文写 embryo 插值 E7.75 / heart 插值 E9.0 / heart 外推 E10.25，与官方 panel 索引 `data/gene_panel/index.json`（`T2:embryo:val_interp` → E7.5、`T2:heart:val_interp` → E8.5、`T2:heart:val_extrap` → E10.5）**三处全错**，并与 `BOARD_REGISTRY.yaml`、`t2_s3_shape_field.py`、`t2_j1_pairing.py` 三个内部来源冲突。**定性：不是官方规则冲突，也不是我们把边界设窄——是我们自己的 PLAN 写错，且把 held-out test stage（E7.75 / E9.0 / E12.5）当成了 validation target。** 该错误已在设计层造成一次真实后果：`H-N2 A2C` 的初版设计按「E8.5/E8.75 中点」取源阶段，而 E8.5 正是本板的目标 stage，属 target 泄漏（`D-20260927-T2DESIGN-001` 已修正并加入泄漏断言）。同时把主判据的陈旧 Total 149.5 更新为 157.04。**假设 H1/H3/H4 未改动。**
- 2026-09-27：H2 假设陈述与「现状」经用户明确授权修订（`D-20260927-T2VALIDATE-001` ＋ `D-20260927-T2GATES-001` ＋ `D-20260927-T2M0APPXB-001`）。修订动因见该决策的 evidence 段与 `artifacts/gate/T2_VALIDATE_V1_LOCAL_VS_SERVER-20260927-v1/RESULT.md`。

## 科学问题

给定小鼠原肠运动期（E6.75–E9.5）单细胞与空间转录组实测数据，构建可评分的"虚拟胚胎"预测：

- **T1（single-cell temporal）**：从 E8.5 及以前预测 E10.5 全转录组状态——纯时间外推。
- **T2（spatial-temporal）**：预测空间表达场，三个 board（**validation target stage 依官方 panel 索引 `data/gene_panel/index.json`**）：embryo 插值（**E7.5**）、heart 插值（**E8.5**）、heart 外推（**E10.5**）。对应的 held-out **test** stage 分别为 E7.75 / E9.0 / E12.5，**不在本地、不公开分发**（`reports/OFFICIAL_SYNC.md` §2/§7）；PLAN 不得把 test stage 写成 validation target。
- **T3（perturbation）**：预测 Gata4 半剂量扰动在 E8.75 心脏中的下游响应。

## 假设

- **H1（结构化先验）**：显式编码发育结构的路线（阶段间位移场、冻结状态词表、最优传输耦合、组成守恒）优于同等预算的黑箱替换。
  - 现状：**部分支持**。T2 几何位移场（+0.4）与 FGW 配对（+0.6）为阳性；T1 moscot 结构化外推（44.9/44.8 vs 48.5）与 MIOFlow 增长/死亡动力学（kill test REJECT）为阴性。结论收敛为：结构化先验在**空间配对/几何**方向有效，在**时间外推的转录组内容**方向未胜出。
- **H2（证据分层）**：source-only holdout 可用于候选筛选，但**失效方向与幅度逐板而异，必须逐板实测校准后方可作筛选器**；任何改善须逐 board 经服务器仲裁作数。
  - 现状：**部分支持，且已修订**（2026-09-27，用户授权修订；依据 `D-20260927-T2VALIDATE-001` 全历史 31 条已评分 T2 候选的实测）。原表述「窄间隔 holdout 获益不保证 leaderboard 获益」**低估了失效程度**。实测：
    - `neighborhood_mmd` 与服务器 board 分的 Spearman：`T2:heart:val_interp` **−0.559**（有预测力）、`T2:heart:val_extrap` **−0.627**（有预测力）、`T2:embryo:val_interp` **+0.833（反向）**。
    - embryo 板按 5% 规则判 DEGRADE 最严重的 v0010（本地 +16.4%）**恰是服务器第一名 62.29**；本地唯一判 IMPROVE 的 v0004 排第 6。
    - **服务器存在本地完全看不见的杠杆**：embryo 板 v0001 与 v0002 表达矩阵字节相同、obs 顺序与组成相同，仅 3D 坐标整体 ×1.305 膨胀，服务器 56.70→60.10（+3.4），而本地七项指标全部零变化（`d2_distance` 尺度不变）。embryo 板历史追的 +0.30/+0.20/+0.30 全部落在这条 3.4 分带宽内。
    - 另有**官方指标语义误解**（`D-20260927-T2GATES-001`）：官方 `variogram` 经三臂对照确认为**基因间协方差、坐标无关**，与「空间变异函数」同名而完全不同物；三份检索简报独立踩中该坑。
  - 修订后的操作含义：**本地门在 T2 上已不可作为默认筛选器**。`embryo` 板 5% 三分类**停用**、改服务器仲裁优先（`D-20260927-T2M0APPXB-001`）；`heart_interp` / `heart_extrap` 维持但须连同 `mmd_u` 同向会签（`mmd_u` 跨族有效、**族内成对比较反向**）。
- **H3（组合收益）**：几何、表达、行-点配对三个可分解方向的局部改善，可在 per-board best 选择下累加为总分提升。
  - 现状：**支持**（selection = embryo 60.1 + heart_interp 57.3 + heart_extrap 50.5，derived T2≈55.97 待服务器确认）。
- **H4（扰动可迁移性）**：WT 上下文 + 公开先验足以构造 E8.75 state-specific 的 Gata4 扰动响应。
  - 现状：**冻结/证伪**。2026-09-02 判定 `UNSATISFIABLE_UNDER_FIREWALL`：E8.75 state-matched 扰动证据公开不可得，且 E8.5–E9.0 窗口数据属 target leakage。作为研究组件收口，重开条件见 `artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md` 第 6 节。

## 判据

- **主判据**：比赛服务器 per-board 分数与 Total（**最新服务器确认 Total 157.04**，2026-09-27；历史快照 156.06 / 153.7 / 151.2 依次见 `reports/SERVER_SCORE_REGISTRY.md`）。
- **辅判据**：source-only holdout 上预声明指标（NFS-like、state-mass L1 等）相对冻结基线与随机对照的方向一致性；只作筛选，不作宣称。
- **否定判据**：预声明 kill metric 未同时优于双臂 → 路线立即关闭（HX-KILLTEST 确立的先例）。

## 为什么值得做

比赛层面：三个 board 的 per-board best 选择机制奖励每个方向的独立改善，小步、可验证、不可变的候选迭代是分数累积的最优策略。
方法学层面：本项目在真实比赛约束下检验"结构化先验 vs 通用模型"的边界——哪些发育结构值得显式编码、哪些是徒劳——否定结果（T1-S2、HX、T3-S1）与阳性结果同等有价值，均已不可变存档可复核。
