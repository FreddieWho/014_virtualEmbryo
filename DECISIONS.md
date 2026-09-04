# DECISIONS — 项目级决策入口

**权威详细存档：[`docs/coordination/DECISIONS.md`](docs/coordination/DECISIONS.md)**（只追加事件日志，含全部 evidence/boundary/next_action）。
本文件按 `~/AGENTS.md` 规范收录影响后续路线的选择摘要：选择、当时理由、复查触发条件。只追加，不覆盖。同一决策不双写——全文以 coordination 存档为准，此处只留索引式摘要。

## 已登记决策摘要

- **D-20260829-005｜batch1 收尾冻结**：4 atom 16 候选全部评分，B1-A1 局部有效，B1-C1 按条件不执行。理由：边际收益递减，转 batch2/3。复查：新数据或新假设出现时。
- **D-20260902-T3-S1C-001｜T3-S1 链收口**：UNSATISFIABLE_UNDER_FIREWALL，gate 结构性不可达。理由：matched 证据公开不可得 + leakage firewall。复查：官方新数据/organizer 书面许可。
- **D-20260903-T2-S3-001｜heart_interp 56.7 晋级**：位移场几何方向首个服务器验证的改善。复查：服务器聚合复核。
- **D-20260903-NAME-001｜上传命名规则固化**：成员名 ≤50 字符短码规则，防止长名不可读。复查：portal 约束变更时。
- **D-20260904-T2-J1-001｜heart_interp 57.3 晋级、embryo HOLD**：FGW 配对方向服务器验证 +0.6；embryo 本地证据不足不消耗提交。复查：embryo 补同靶 parent 参照后（LEADS L-001）。
- **D-20260904-HX-001｜增长/死亡动力学方向关闭**：kill test 预声明阈值未达成（0.7475 vs 0.6645）。复查：独立证据表明 T1 残差由 mass 漂移主导时。
- **D-20260904-T3-001｜T3 并列新 board best 45.5**：B2-T3-A1 v0006/v0007 双双 +0.2，首次超过 wt_identity；服务器无法区分 lane。复查：服务器聚合复核；科学 gate 不受影响。

## 最近一条

D-20260904-T3-001（2026-09-04）：T3 双候选并列晋级；derived Total≈149.7 待确认。
