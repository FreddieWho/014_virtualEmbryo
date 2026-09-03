# PLAN — Virtual Embryo Challenge

建立日期：2026-09-04（batch1–3 收口后补建；此前科学判断散见于 `docs/batch3/` 方案与 `docs/coordination/` 文档，本文件为唯一权威版本）。
修改规则：仅当科学判断改变时修改，需用户确认；agent 不得自行修改，只能报告偏离。

## 科学问题

给定小鼠原肠运动期（E6.75–E9.5）单细胞与空间转录组实测数据，构建可评分的"虚拟胚胎"预测：

- **T1（single-cell temporal）**：从 E8.5 及以前预测 E10.5 全转录组状态——纯时间外推。
- **T2（spatial-temporal）**：预测空间表达场——embryo 插值（E7.75）、heart 插值（E9.0）、heart 外推（E10.25 方向）三个 board。
- **T3（perturbation）**：预测 Gata4 半剂量扰动在 E8.75 心脏中的下游响应。

## 假设

- **H1（结构化先验）**：显式编码发育结构的路线（阶段间位移场、冻结状态词表、最优传输耦合、组成守恒）优于同等预算的黑箱替换。
  - 现状：**部分支持**。T2 几何位移场（+0.4）与 FGW 配对（+0.6）为阳性；T1 moscot 结构化外推（44.9/44.8 vs 48.5）与 MIOFlow 增长/死亡动力学（kill test REJECT）为阴性。结论收敛为：结构化先验在**空间配对/几何**方向有效，在**时间外推的转录组内容**方向未胜出。
- **H2（证据分层）**：source-only holdout 可用于候选筛选，但窄间隔 holdout 获益不保证 leaderboard 获益；任何改善须逐 board 经服务器仲裁作数。
  - 现状：**支持**（T2-S3 embryo H1 holdout 全胜但服务器 −0.4；J1 heart 本地混合证据经服务器正向仲裁 +0.6）。
- **H3（组合收益）**：几何、表达、行-点配对三个可分解方向的局部改善，可在 per-board best 选择下累加为总分提升。
  - 现状：**支持**（selection = embryo 60.1 + heart_interp 57.3 + heart_extrap 50.5，derived T2≈55.97 待服务器确认）。
- **H4（扰动可迁移性）**：WT 上下文 + 公开先验足以构造 E8.75 state-specific 的 Gata4 扰动响应。
  - 现状：**冻结/证伪**。2026-09-02 判定 `UNSATISFIABLE_UNDER_FIREWALL`：E8.75 state-matched 扰动证据公开不可得，且 E8.5–E9.0 窗口数据属 target leakage。作为研究组件收口，重开条件见 `artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md` 第 6 节。

## 判据

- **主判据**：比赛服务器 per-board 分数与 Total（当前服务器返回 Total 149.5）。
- **辅判据**：source-only holdout 上预声明指标（NFS-like、state-mass L1 等）相对冻结基线与随机对照的方向一致性；只作筛选，不作宣称。
- **否定判据**：预声明 kill metric 未同时优于双臂 → 路线立即关闭（HX-KILLTEST 确立的先例）。

## 为什么值得做

比赛层面：三个 board 的 per-board best 选择机制奖励每个方向的独立改善，小步、可验证、不可变的候选迭代是分数累积的最优策略。
方法学层面：本项目在真实比赛约束下检验"结构化先验 vs 通用模型"的边界——哪些发育结构值得显式编码、哪些是徒劳——否定结果（T1-S2、HX、T3-S1）与阳性结果同等有价值，均已不可变存档可复核。
