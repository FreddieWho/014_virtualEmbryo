# TODO — 当前待办（用户与 agent 共读唯一入口）

按执行顺序排列，重要的在前。建立日期：2026-09-04。

- [ ] 用户读服务器页面，提供最新 Total/T2 读数（确认 derived T2≈55.97/Total≈149.8 是否成立）  ← 阻塞"当前真实总分"的确认
- [ ] 授权 commit + push 本轮改动（分数回填、HX 收口、本套文档）
- [ ] 决定 batch4 方向或宣布封板（选项见 ROADMAP N8 与 LEADS.md）

## 分支记录

- **当前执行分支**：无活跃 atom（batch3 全部执行完毕，等待授权）。
- **并行分支**：无。
- **暂缓分支**：
  - T2 embryo_interp v0008 `j1_fgw_assignment`：HOLD_AS_COMPONENT（缺同靶 parent scorer 参照，见 LEADS L-001）
  - T2-S3 L2 spateo v0007/v0008 与 heart_extrap v0006/v0007：本地 REJECT，不可变保留不上传
  - B2-T3-A1 v0006/v0007：HOLD_AS_COMPONENT，score_pending
- **停止分支（已关闭，不可变存档）**：
  - T1-S2 moscot decoder（服务器 44.9/44.8 REJECT）
  - HX MIOFlow 增长/死亡动力学（kill test REJECT）
  - T3-S1 prior 链（UNSATISFIABLE_UNDER_FIREWALL 收口）
  - B1-A2/A3/A4、T1 v0002/v0003/v0005/v0006 等历史淘汰候选（见 submissions/INDEX.tsv）

## 变更记录

- 2026-09-04：建立本文件（batch3 收口后）。初始内容：3 条待办 + 分支记录；此前待办散见于各 TRACKING 文档"下一步"节，现以本文件为唯一入口。
- 2026-09-04：新增"用户读服务器页面确认 derived 149.8 / 授权 push / 决定 batch4 或封板"三条为当前待办（由 batch3 收尾事件产生）；同日落盘 `reports/PHASE_REPORT_BATCH3_20260904.md` 与 `reports/RELEASE_CHANGELOG_BATCH3_20260904.md`，分支记录不变。
